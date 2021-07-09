# This files contains your custom actions which can be used to run
# custom Python code.
#
# See this guide on how to implement these action:
# https://rasa.com/docs/rasa/custom-actions
import sys
sys.path.append('../')

from typing import Any, Text, Dict, List
from difflib import SequenceMatcher
from actions import modelado

from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.events import FollowupAction
from rasa_sdk.events import SlotSet

# Setup wikipedia
import wikipedia

wikipedia.set_lang("es")


class ActionDefaultFallback(Action):
    """Ejecuta una accion de fallback que busca en wikipedia lo que no entiende el bot"""

    def name(self) -> Text:
        return "action_default_fallback"

    def run(
            self,
            dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any],
    ) -> List[Dict[Text, Any]]:

        text = tracker.latest_message['text']

        try:
            summary = wikipedia.summary(text, sentences=1)
        except:
            # TODO: add otras opciones!! (UTTER??)
            summary = "La verdad que no sé... porqué no hablamos de otra cosa?"
        dispatcher.utter_message(summary)

        return [FollowupAction("action_listen")]


class ActionModelado(Action):
    questions = modelado.QuestionsData()

    """
    Action que toma las features y genera una secuencia de 
    grafos a partir de cada feature.
    """

    def name(self) -> Text:
        return "action_modelado"

    def run(
            self,
            dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any],
    ) -> List[Dict[Text, Any]]:
        # Traigo el ultimo mensaje
        features = tracker.get_slot('features')
        for feat in features:
            # Actualizar una nueva versión del gráfico
            sugerencia, image = modelado.update_graph(tracker.sender_id, feat)
            
        # Mostrar mensaje e imagen
        dispatcher.utter_message(text=sugerencia)
        dispatcher.utter_message(image=image)
        return []


class ActionModeladoRechazo(Action):
    """
    Elimina la ultima entrada de la lista de arquitecturas de este usuario
    Es decir, vuelve a la versión interior
    """

    def name(self) -> Text:
        return "action_modelado_rechazo"

    def run(
            self,
            dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any],
    ) -> List[Dict[Text, Any]]:
        # Elimino ultima versión del gráfico
        utter, image = modelado.remove_graph(tracker.sender_id)
        # Muestro como queda
        dispatcher.utter_message(text=utter)
        dispatcher.utter_message(image=image)
        return []


def get_questions(text: str, asked: List, remaining: List) -> List[str]:
    """ 
    Funcion que trae preguntas para una especificacion
    """
    # Tambien quita las repetidas en la lista
    return remove_similars(modelado.get_questions(text, preguntas, preguntas))


def remove_similars(str_list):
    """
    Funcion que saca las frases repetidas
    (no tienen que ser matches exactos, usan un algo de proxmidad)
    """
    # Tengo que tener al menos dos items
    if len(list) > 1:
        # El primero siempre se carga xq no puede estar repetido
        clean_list = [str_list[0]]
        # Para cada uno de los que queda me fijo si ya esta
        for item in list[1:]:
            has_similar = False
            for clean_item in clean_list:
                if similar(item, clean_item) > 0.8:
                    has_similar = True
                    break
            if not has_similar:
                clean_list.append(item)
        return clean_list
    else:
        return list


def similar(a, b):
    """
    Calcula un valor de similaridad para un par de frases
    """
    return SequenceMatcher(None, a, b).ratio()


class ActionAnalizarEspecificaciones(Action):

    """
    Dada una especificacion inicial genera un conjunto de preguntas iniciales
    """

    def name(self) -> Text:
        return "action_analizar_especificaciones"

    def run(
            self,
            dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any],
    ) -> List[Dict[Text, Any]]:
        # Obtengo el ultimo mensaje
        text = tracker.latest_message['text']

        # obtengo las preguntas para esta especificacion, dando el contexto actual
        questions = modelado.get_questions(text, modelado.QuestionsData.asked_questions,
                                           modelado.QuestionsData.remaining_questions)

        for q in questions:
            ActionModelado.questions.add_question(q)
        # actualizo las features. Me fijo, si no existen creo la primera entrada
        features = tracker.get_slot('features')
        if features is None:
            features = [text]
        else:
            features.append(text)

        # Muestro una al usuario
        if ActionModelado.questions.remaining_size() is not 0:
            dispatcher.utter_message(ActionModelado.questions.get_question().get_filled_question())
            return [SlotSet('features', features)]
        else:
            return [SlotSet('features', features), SlotSet('termino_preguntas', True)]


class ActionGuardarFeature(Action):
    """
    Dada una nueva respuesta a preguntas anteriores, 
    la guardamos como feature y chequeamos si nos quedan preguntas pendientes
    """

    def name(self) -> Text:
        return "action_guardar_feature"

    def run(
            self,
            dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any],
    ) -> List[Dict[Text, Any]]:
        # Obtengo el texto de respuesta
        text = tracker.latest_message['text']

        # actualizo las features. Me fijo, si no existen creo la primera entrada
        features = tracker.get_slot('features')
        if not features:
            features = [text]
        else:
            features.append(text)

        # Chequeo si termino. Si no termino hago la siguiente pregunta
        # en caso de tener pocas features hago una ronda mas de preguntas
        termino = None
        if ActionModelado.questions.remaining_size() is not 0:
            dispatcher.utter_message(ActionModelado.questions.get_question().get_filled_question())
        else:
            termino = True
        # Generar preguntas automagicamente
        return [SlotSet('features', features), SlotSet('termino_preguntas', termino)]


class ActionRechazarFeature(Action):
    """
    Para cuando no entiende, no responde o responde que no,
    hacemos otra pregunta o cortamos la secuencia si ya no quedan
    """

    def name(self) -> Text:
        return "action_rechazar_feature"

    def run(
            self,
            dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any],
    ) -> List[Dict[Text, Any]]:
        dispatcher.utter_message("No hay problema.")
        # Chequeo si termino, sino le hago la que sigue
        if ActionModelado.questions.remaining_size() is not 0:
            dispatcher.utter_message("Sigamos con otra pregunta..")
            dispatcher.utter_message(ActionModelado.questions.get_question().get_filled_question())
            termino = None
        else:
            termino = True
        return [SlotSet('termino_preguntas', termino)]
