# This files contains your custom actions which can be used to run
# custom Python code.
#
# See this guide on how to implement these action:
# https://rasa.com/docs/rasa/custom-actions

from typing import Any, Text, Dict, List, Optional

from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.events import FollowupAction, EventType
from rasa_sdk.forms import FormValidationAction
from rasa_sdk.events import SlotSet


from . import modelado

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

    def name(self) -> Text:
        return "action_modelado"

    def run(
            self,
            dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any],
        ) -> List[Dict[Text, Any]]:

        text =  tracker.latest_message['text']
        utter, image = modelado.update_graph(tracker.sender_id, text)
        dispatcher.utter_message(text=utter)
        dispatcher.utter_message(image=image)        
        return[]

class ActionModeladoRechazo(Action):

    def name(self) -> Text:
        return "action_modelado_rechazo"

    def run(
            self,
            dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any],
        ) -> List[Dict[Text, Any]]:

        utter, image = modelado.remove_graph(tracker.sender_id)
        dispatcher.utter_message(text=utter)
        dispatcher.utter_message(image=image)
        return[]


class ActionPreguntaContestada(Action):

    def name(self) -> Text:
        return "action_pregunta_contestada"

    def run(
            self,
            dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any],
        ) -> List[Dict[Text, Any]]:

        text = tracker.latest_message['text']
        modelado.save_conocimiento(text)
        dispatcher.utter_message(text="Claro comprendo... ")        
        dispatcher.utter_message(text=modelado.get_pregunta(text))    
        return[]

class ActionPregunta(Action):

    def name(self) -> Text:
        return "action_pregunta"

    def run(
            self,
            dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any],
        ) -> List[Dict[Text, Any]]:

        text =  tracker.latest_message['text']
        dispatcher.utter_message(text=modelado.get_pregunta(text))
        return[]

class AskForRespuestaEntradaAction(Action):
    def name(self) -> Text:
        return "action_ask_respuesta_entrada"

    def run(
        self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict
    ) -> List[EventType]:
        """
        Se fija la pregunta que tiene que hacer de acuerdo a la Queue de preguntas que tenemos
        para las entidades reconocidas como entradas 
        """
        preguntas_entrada = tracker.get_slot("preguntas_entrada")
        if preguntas_entrada and len(preguntas_entrada) > 0:
            dispatcher.utter_message(text=preguntas_entrada.pop(0))
            if len(preguntas_entrada) == 0:
                return [SlotSet('termino_entradas',True)]

        return []

class AskForRespuestaSalidaAction(Action):
    def name(self) -> Text:
        return "action_ask_respuesta_salida"

    def run(
        self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict
    ) -> List[EventType]:
        """
        Se fija la pregunta que tiene que hacer de acuerdo a la Queue de preguntas que tenemos
        para las entidades reconocidas como salida 
        """
        preguntas_salida = tracker.get_slot("preguntas_salida")
        if preguntas_salida and len(preguntas_salida) > 0:
            dispatcher.utter_message(text=preguntas_salida.pop(0))
            if len(preguntas_salida) == 0:
                return [SlotSet('termino_salidas',True)]
                
        return []


class ActionAnalizarEntradas(Action):

    def name(self) -> Text:
        return "action_analizar_entradas"

    def run(
            self,
            dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any],
        ) -> List[Dict[Text, Any]]:

        text =  tracker.latest_message['text']
        # TODO: ANALISIS
        # Generar preguntas automagicamente para la entrada
        return [SlotSet('termino_entradas',False),SlotSet('preguntas_entrada',["De que color es el caballo blanco de San Martín a la ENTRADA del baile?"])]

class ActionAnalizarSalidas(Action):

    def name(self) -> Text:
        return "action_analizar_salidas"

    def run(
            self,
            dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any],
        ) -> List[Dict[Text, Any]]:

        text =  tracker.latest_message['text']
        # TODO: ANALISIS
        # Generar preguntas automagicamente para la salida
        return [SlotSet('termino_salidas',False),SlotSet('preguntas_salida',["De que color es el caballo blanco de San Martín a la SALIDA del baile?"])]


class ActionGuardarEntrada(Action):

    def name(self) -> Text:
        return "action_guardar_entrada"

    def run(
            self,
            dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any],
        ) -> List[Dict[Text, Any]]:

        text =  tracker.latest_message['text']
        features = tracker.get_slot('features')
        if not features:
            features = [text]
        else:
            features.append(text)
        
        # TODO: unificar en unica accion action_guardar y usarlapara ambos casos
        # Generar preguntas automagicamente
        return [SlotSet('features',features)]

class ActionGuardarSalida(Action):

    def name(self) -> Text:
        return "action_guardar_salida"

    def run(
            self,
            dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any],
        ) -> List[Dict[Text, Any]]:

        text =  tracker.latest_message['text']
        features = tracker.get_slot('features')
        if not features:
            features = [text]
        else:
            features.append(text)
        
        # Generar preguntas automagicamente
        return [SlotSet('features',features)]