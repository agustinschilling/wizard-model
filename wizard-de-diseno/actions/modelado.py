from rasa.nlu.model import Interpreter
from .entities import Entity
from .architecture_graph import GraphManager
import os
import random


# path of your model
rasa_model_path = "actions/models/modelado/nlu"

# create an interpreter object
interpreter = Interpreter.load(rasa_model_path)

from actions import mongo_client

def rasa_output(text):
    """
    Analisis NLU del texto para clasificar categorias de patrones:
    usa modelo de -> (https://github.com/joacosaralegui/analisis-de-patrones)
    """
    message = str(text).strip()
    result = interpreter.parse(message)
    return result

def update_graph(id,text):
    # Get analisis
    intent,entities = parse_req(text)
    print_summary(entities)

    # Update graph
    graph_manager = GraphManager(id)
    graph_manager.update_graph_with_new_entities(entities,intent)
    graph_manager.save()

    # Image
    graph_image_file = graph_manager.get_image_file()
    return "Qué te parece esto?",os.path.abspath(graph_image_file)


def remove_graph(id):
    # Remove last graph
    graph_manager = GraphManager(id)
    graph_manager.remove_last()

    # Image
    graph_image_file = graph_manager.get_image_file()
    return "Ahí lo corregí. Cómo avanzamos ahora?",os.path.abspath(graph_image_file)
    
def parse_req(text):
    rasa_parsing = rasa_output(text)
    intent = rasa_parsing['intent']['name']
    entities = parse_entities(rasa_parsing['entities'])

    return intent, entities

def get_pregunta(text):
    # Get analisis
    intent,entities = parse_req(text)
    print_summary(entities)
    relevant_entities = [e for e in entities if e.category == "MODEL" or e.category == "COMPONENT"]

    for entity in relevant_entities:
        if not mongo_client.get_conocimiento(entity.name):
            options = [ "Contame que entendés por " + entity.name, 
            "A qué te referís con " + entity.name +"?",
            "Que significa " + entity.name + " en este contexto?"]
            return random.choice(options)
        
    if len(relevant_entities) >= 2:
        return "Explicame un poco la relacion entre " + relevant_entities[0].name + " y " + relevant_entities[1].name + " y cómo interactuan entre sí"
    
def save_conocimiento(text):
    intent,entities = parse_req(text)
    print_summary(entities)
    relevant_entities = [e for e in entities if e.category == "MODEL" or e.category == "COMPONENT"]

    for entity in relevant_entities:
        if not mongo_client.get_conocimiento(entity.name):
            mongo_client.save_conocimiento(entity.name, text,entity.category)
            return 
        

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
