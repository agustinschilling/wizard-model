from rasa.nlu.model import Interpreter
from actions.entities import Entity
from actions.architecture_graph import GraphManager
from actions.implementacion import get_sugerencia_implementacion
import os
import random
import json

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

def update_graph(id,text):
    """
    Actualizar el grafo con un texto nuevo, 
    primero sacando entidades y requerimientos
    """
    # Get analisis
    intent,entities = parse_req(text)

    # Update graph
    graph_manager = GraphManager(id)
    graph_manager.update_graph_with_new_entities(entities,intent)
    graph_manager.save()

    # Actualizar el dump/info
    guardar_prediccion(text, entities, intent)

    # Image
    graph_image_file = graph_manager.get_image_file()
    implementacion = get_sugerencia_implementacion(graph_manager)
    return implementacion,os.path.abspath(graph_image_file)


def remove_graph(id):
    """
    Elimina la ultima version del grafo
    """
    # Remove last graph
    graph_manager = GraphManager(id)
    graph_manager.remove_last()

    # Image
    graph_image_file = graph_manager.get_image_file()
    return "Ahí lo corregí. Cómo avanzamos ahora?",os.path.abspath(graph_image_file)
    
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

def guardar_prediccion(text, entities, intent, preguntas =[]):
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

def get_questions(text):
    # Genera preguntas para un texto
    intent, entities = parse_req(text)
    print("Intent:" + intent)

    preguntas = []
    for i, entity in enumerate(entities):
        if entity.category == "MODEL":
            preguntas.append("Contame de donde surge " + entity.name + " o cuál te imaginas que es su función")
            #preguntas.append("Que propiedades estarían asociadas a " + entity.name)
            #preguntas.append("Cuál sería el proceso para obtener " + entity.name)
        elif entity.category == "EVENT":
            if i+1 < len(entities) and entities[i+1].category != "EVENT":
                preguntas.append("Cómo implementarias el proceso que involucra " + entity.name + " " + entities[i+1].name)
            else:
                preguntas.append("Con que elementos se relaciona el proceso de " + entity.name + " y cómo lo hace?")
        elif entity.category == "COMPONENT":
            preguntas.append("Cómo se relaciona " + entity.name + " con las otras partes del sistema?")

    model_entities = [e.name for e in entities if e.category == "MODEL"]
    if len(model_entities) > 1:
        if "chain" in intent:
            preguntas.append("Explicame la relación entre " + model_entities[-2] + " y "+ model_entities[-1] + " si existe")
        else:
            preguntas.append("Cómo explicarías la relación entre a " + model_entities[0] + " y "+ model_entities[1])

    guardar_prediccion(text, entities, intent, preguntas)

    return preguntas

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

if __name__=="__main__":
    text = "La interfaz web se conecta con la base para mostrar las frases chequeables que tienen una calificacion"
    id = "joaco_test3"
    # Get analisis
    intent,entities = parse_req(text)

    # Update graph
    graph_manager = GraphManager(id)
    graph_manager.update_graph_with_new_entities(entities,intent)
    graph_manager.save()

    pattern = get_sugerencia_implementacion(graph_manager)
    import pdb; pdb.set_trace()