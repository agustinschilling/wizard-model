from string import Template
from typing import List, Dict

from rasa.nlu.model import Interpreter
from .entities import Entity
from .architecture_graph import GraphManager
import os
import json

import sys

sys.path.append('../')

# path of your model
rasa_model_path = "actions/models/modelado/nlu"

# create an interpreter object
interpreter = Interpreter.load(rasa_model_path)


def rasa_output(text):
    """
    Analisis NLU del texto para clasificar categorias de patrones:
    usa modelo de -> (https://github.com/joacosaralegui/analisis-de-patrones)
    """
    message = str(text).strip()
    result = interpreter.parse(message)
    return result


def update_graph(id, text):
    """
    Actualizar el grafo con un texto nuevo, 
    primero sacando entidades y requerimientos
    """
    # Get analisis
    intent, entities = parse_req(text)

    # Update graph
    graph_manager = GraphManager(id)
    graph_manager.update_graph_with_new_entities(entities, intent)
    graph_manager.save()

    # Actualizar el dump/info
    # guardar_prediccion(text, entities, intent)

    # Image
    graph_image_file = graph_manager.get_image_file()
    return "Qué te parece esto?", os.path.abspath(graph_image_file)


def remove_graph(id):
    """
    Elimina la ultima version del grafo
    """
    # Remove last graph
    graph_manager = GraphManager(id)
    graph_manager.remove_last()

    # Image
    graph_image_file = graph_manager.get_image_file()
    return "Ahí lo corregí. Cómo avanzamos ahora?", os.path.abspath(graph_image_file)


def parse_req(text):
    """
    Dado un requerimiento lo analiza y extrae entidades e intencion
    """
    # Genera el output de rasa para un texto
    rasa_parsing = rasa_output(text)
    intent = rasa_parsing['intent']['name']
    entities = parse_entities(rasa_parsing['entities'])
    print_summary(entities)
    return intent, entities


def guardar_prediccion(text, entities, intent, preguntas=[]):
    # Almacena informacion para luego mejorar el entrenamiento
    prediccion = {
        "preguntas": preguntas,
        "texto": text,
        "entidades": [(e.name, e.category) for e in entities],
        "intent": intent
    }

    # Opening JSON file
    with open('data.json', 'r') as openfile:
        # Reading from json file
        data = json.load(openfile)

    if data:
        data.append(prediccion)
    else:
        data = [prediccion]

    with open("data.json", 'w') as file:
        json.dump(data, file)


class Question:
    def __init__(self, text_template: str, fill: Dict[str, Entity]):
        """
        create a question with a template and a dict with the name of template var and her entity data
        :param text_template: Template of the question. Example: "Hello my name is $name and today is $day"
        :param fill: parameters to fill template. Example: {"name": Entity, "day": Entity}
        """
        self.template = Template(text_template)
        self.fill_dict = fill

    def get_filled_question(self) -> str:
        """
        fills the template with entity NAME
        :return: filled template
        """
        fill_vars = {}
        for entity_arg_name in self.fill_dict.keys():
            fill_vars[entity_arg_name] = self.fill_dict[entity_arg_name].name
        a = self.template.substitute(fill_vars)
        print(a)
        return a

    def get_used_entities(self) -> List[Entity]:
        """
        :return: list of entities that are used to fill the templates
        """
        return [x for x in self.fill_dict.values()]


class QuestionsData:
    """
    Class to store questions
    @asked_questions work as history
    """
    remaining_questions = []
    asked_questions = []

    def add_question(self, question: Question):
        """
        add a question to a struct without criteria
        :param question: question to add
        """
        self.remaining_questions.append(question)

    def get_question(self) -> Question:
        """
        move returned question to asked to maintain history
        :return: next question without criteria
        """
        next_q = self.remaining_questions.pop()
        self.asked_questions.append(next)
        return next_q

    def remaining_size(self) -> int:
        return len(self.remaining_questions)


def get_questions(text: str, asked: List[Question], remaining: List[Question]) -> List[Question]:
    """
    Generate a list of questions based on the entities(MODEL, COMPONENT, ..) of a text
    and a context based on asked questions and remaining questions
    :param remaining: questions not asked
    :param text: text to search entities
    :param asked: questions that were asked
    :return: list of NEW questions
    """

    #TODO use asked and remaining

    # Genera preguntas para un texto
    intent, entities = parse_req(text)
    print("Intent:" + intent)

    # tag entities
    entities_tagged = {"MODEL": [], "PROPERTY": [], "EVENT": [], "COMPONENT": []}
    for entity in entities:
        entities_tagged[entity.category].append(entity)

    preguntas = []
    if len(entities_tagged["EVENT"]) is 1:
        # simple chain
        if len(entities_tagged["MODEL"]) is 2:
            preguntas.append(Question("Contame de donde surge $model1 o cuál te imaginas que es su función",
                                      {"model1": entities_tagged["MODEL"][0]}))
            preguntas.append(Question("Contame de donde surge $model2 o cuál te imaginas que es su función",
                                      {"model2": entities_tagged["MODEL"][1]}))
        if len(entities_tagged["MODEL"]) is 1 and len(entities_tagged["COMPONENT"]) is 1:
            preguntas.append(Question("Contame de donde surge $model1 o cuál te imaginas que es su función",
                                      {"model1": entities_tagged["MODEL"][0]}))
            preguntas.append(Question("Es necesario hacer algun otro uso del $component1",
                                      {"component1": entities_tagged["COMPONENT"][0]}))

        # falta un elemento para cadena simple
        if (len(entities_tagged["MODEL"]) is 1) and (len(entities_tagged["COMPONENT"]) is 0):
            preguntas.append(Question("El $event1 de $model1 de donde o con que debe hacerse?",
                                      {"event1": entities_tagged["EVENT"][0],
                                       "model1": entities_tagged["MODEL"][0]}))
        if (len(entities_tagged["MODEL"]) is 0) and (len(entities_tagged["COMPONENT"]) is 1):
            preguntas.append(Question("El $event1 que interactua con $component1 que debe resultado genera?",
                                      {"event1": entities_tagged["EVENT"][0],
                                       "component1": entities_tagged["COMPONENT"][0]}))
    return preguntas

#Codigo de joaco
"""
    preguntas_de_entidades = {}
    preguntas = []
    for i, entity in enumerate(entities):
        if entity.category == "MODEL":
            preguntas_de_entidades[entity.name] = i
            preguntas.append("Contame de donde surge " + entity.name + " o cuál te imaginas que es su función")
            # preguntas.append("Que propiedades estarían asociadas a " + entity.name)
            # preguntas.append("Cuál sería el proceso para obtener " + entity.name)
        elif entity.category == "EVENT":
            if i + 1 < len(entities) and entities[i + 1].category != "EVENT":
                preguntas.append(
                    "Cómo implementarias el proceso que involucra " + entity.name + " " + entities[i + 1].name)
            else:
                preguntas.append("Con que elementos se relaciona el proceso de " + entity.name + " y cómo lo hace?")
        elif entity.category == "COMPONENT":
            preguntas.append("Cómo se relaciona " + entity.name + " con las otras partes del sistema?")

    model_entities = [e.name for e in entities if e.category == "MODEL"]
    if len(model_entities) > 1:
        if "chain" in intent:
            preguntas.append(
                "Explicame la relación entre " + model_entities[-2] + " y " + model_entities[-1] + " si existe")
        else:
            preguntas.append("Cómo explicarías la relación entre a " + model_entities[0] + " y " + model_entities[1])

    guardar_prediccion(text, entities, intent, preguntas)
"""


#
# Helper functions  
#
def parse_entities(entities_list):
    entities = [Entity(e) for e in entities_list]
    return get_valid_entities(entities)


def get_valid_entities(entities):
    return [e for e in entities if e.is_valid()]


def print_summary(entities):
    print("***  New requirement  ****")
    print("Entities: ")
    for e in entities:
        print(f" - {e.category}: {e.name}")
    print("*************************")
