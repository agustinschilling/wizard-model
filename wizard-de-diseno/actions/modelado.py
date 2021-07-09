import itertools
from string import Template
from typing import List, Dict

import enchant.utils
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

    # Genera preguntas para un texto
    intent, entities = parse_req(text)
    print("Intent:" + intent)

    # tag entities
    entities_tagged = {"MODEL": [], "PROPERTY": [], "EVENT": [], "COMPONENT": []}
    for entity in entities:
        entities_tagged[entity.category].append(entity)

    preguntas = []
    for i, entity in enumerate(entities):
        if entity.category == "MODEL":
            preguntas.append(Question("Contame de donde surge $model o cuál te imaginas que es su función",
                                      {"model": entity}))
            # preguntas.append("Que propiedades estarían asociadas a " + entity.name)
            # preguntas.append("Cuál sería el proceso para obtener " + entity.name)
        elif entity.category == "EVENT":
            if i + 1 < len(entities) and entities[i + 1].category != "EVENT":
                preguntas.append(Question("Cómo implementarias el proceso que involucra $event $entity",
                                          {"event": entity, "entity": entities[i + 1]}))
            else:
                preguntas.append(Question("Con que elementos se relaciona el proceso de $event y cómo lo hace?",
                                          {"event": entity}))
        elif entity.category == "COMPONENT":
            preguntas.append(Question("Cómo se relaciona $component con las otras partes del sistema?",
                                      {"component": entity}))

    model_entities = [e for e in entities if e.category == "MODEL" or e.category == "COMPONENT"]
    if len(model_entities) > 1:
        for e1, e2 in itertools.combinations(model_entities, 2):
            preguntas.append(Question("Contame mas informacion de como se relacionan $e1 y $e2",
                                      {"e1": e1, "e2": e2}))
    print([x.get_filled_question() for x in preguntas])
    return remove_repeated_questions(preguntas, asked, remaining, 0.8)


def check_similar_words(word1, word2, ratio) -> bool:
    if word1 in word2 or word2 in word1:
        return True
    # TODO mas L-gante
    divider = word2
    if len(word1) < len(word2):
        divider = word1
    #pocos cambios dan una distancia baja
    if (1 - enchant.utils.levenshtein(word1, word2)/divider) > ratio:
        print(word1+" es similar a "+word2)
        return True

    return False


def check_similar_entities(old_q_ent: List[Entity], new_q_ent: List[Entity], ratio: float) -> bool:
    """
    check if two list of entities have a similarity, requires same category and @ratio similar name
    :param old_q_ent:
    :param new_q_ent:
    :param ratio: ratio of similarity to consider similar
    :return: true if similar, false otherwise
    """
    same_entities = 0
    for q_old in old_q_ent:
        for q_new in new_q_ent:
            if q_old.category is q_new.category and check_similar_words(q_old.name, q_new.name, ratio):
                same_entities += 1

    # compare ratio with smaller list
    if same_entities > 0:
        # less entities in old
        if len(old_q_ent) < len(new_q_ent):
            if len(old_q_ent) / same_entities >= ratio:
                return True
        # more or equal in old
        else:
            if len(new_q_ent) / same_entities >= ratio:
                return True

    return False


def remove_repeated_questions(new_q: List[Question],
                              asked: List[Question],
                              remaining: List[Question],
                              ratio: float) -> List[Question]:
    # TODO el metodo deberia solo recibir una lista que combine asked y remaining porque no se usan por separado
    """
    removes from a list a questions that are similar to asked and remaining with a ratio
    :param ratio: ratio of similarity
    :param new_q:
    :param asked:
    :param remaining:
    :return: questions of new_q that arent similar
    """
    cleared_q = []
    for q in new_q:
        new_q_ent = q.get_used_entities()
        for old_q in itertools.chain(asked, remaining):
            old_q_ent = old_q.get_used_entities()
            if not check_similar_entities(old_q_ent, new_q_ent, ratio):
                cleared_q.append(q)
            # TODO borrar print de debug
            else:
                print("detecto similar a: " + q.get_filled_question() + "y" + old_q.get_filled_question())
    print([x.get_filled_question() for x in cleared_q])
    return cleared_q


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
