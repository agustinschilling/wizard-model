
from actions.architecture_graph import GraphManager
from actions.entities import Entity

class Pattern:
    """
    Clase para definir patrones de arquitectura y 
    que busca facilitar la identificacion de patrones 
    y las recomendaciones de implementacion
    """
    def __init__(self, name:str, keywords: list, entities_weight) -> None:
        # Nombre de patrón
        self.name = name
        # Palabras clave que nos ayudan a identificarlo
        self.keywords = keywords
        # Pesos que tienen las entidades para este patrón (Ej:microservicios le da mucha bola a componentes)
        self.entities_weight = entities_weight
        
    def match_score_entities(self, entities):
        """
        Dado un diccionario de entidades agrupadas por su categoria
        calculo un valor de matching respecto al valor que le da este patron 
        a cada conjunto
        """
        categories = ["MODEL","EVENT","COMPONENT","PROPERTY"]
        score = 0
        total_ents = 0
        # Para cada categoria
        for cat in categories:
            # Sumo al score el valor de cant de entidades, promediado por el peso que le da este patrón
            score += len(entities[cat]) * self.entities_weight[cat] 
            # Calculo iterativamente el valor total de entidades
            total_ents += len(entities[cat])
    
        # Normalizo el score entre 0 y 1 dividiendolo por el total de entidades
        return score/total_ents
        
    def match_score_keywords(self, target_words):
        """
        Dada la lista de palabras que tiene una solucion
        devuelve un valor de matching de acuerdo a cuantas de las palabras 
        relevantes para el patron matchean. se normaliza entre 0 y 1
        """
        matches = 0
        # Para cada par de palabras entre lasd el patron y las de la solucion
        for keyword in self.keywords:
            keyword = keyword.lower()
            for target in target_words:
                target = target.lower()
                # Sumo uno si matchean
                if Pattern.keyword_match(keyword, target):
                    matches += 1
        
        # Normalizo diviendo por el maximo numero de matches posibles
        return matches/(len(self.keywords)*len(target))

    def match_score(self, target_words, entities_grouped):
        # Devuelve el promedio entre todos los scores que definamos
        keywords_score = self.match_score_keywords(target_words) 
        entities_score = self.match_score_entities(entities_grouped)
        return (keywords_score + entities_score)/2

    @staticmethod
    def keyword_match(word1, word2):
        if word1 == word2 or word1 in word2 or word2 in word1:
            return True
        return False
        
# Defino unos patrones de prueba, aca se pueden agregar muchos mas con 
# distintas palabras claves y pesos. HAy que analizarlos para hacerlo mejor
patterns = [
    Pattern("MVC",["interfaz","web","aplicación web"],{"MODEL":1,"EVENT":1,"COMPONENT":0,"PROPERTY":1}),
    Pattern("Microservicios",["servicio","api"],{"MODEL":0,"EVENT":1,"COMPONENT":1,"PROPERTY":0})
]

# Dado un grafo, determinar que patron se puede asignar
def get_pattern(keywords, entities_grouped):
    # Obtengo las keywords y el diccionario de entities agrupadas

    # Itero por todos los patrones y me quedo con el que mas score da
    max_score = -1
    max_patt = None
    for patt in patterns:
        score = patt.match_score(keywords, entities_grouped)  
        if score > max_score:
            max_patt = patt
            max_score = score

    return max_patt

def get_sugerencia_implementacion(graph_manager:GraphManager):
    # Calculo las keywords y el grupo de entidadees para calcular el patron
    graph = graph_manager.graph
    keywords = [node.name for node in graph.nodes()]
    entities_grouped = graph_manager.get_entities_grouped()

    # Tengo mi patron :D
    pattern = get_pattern(keywords,entities_grouped)
    
    if pattern.name == "MVC":
        text = "Analizando el problema, recomiendo implementar una arquitectura con el patrón Model-View-Controller."
        text += ". \nEl hecho de que tengas una interfaz en la que interactuan usuarios y que ademas tengas que almacenar informacion para algunos objetos importantes me hace pensar que es la mejor decision."
        text += ". \nSi necesitas más información sobre este patrón o cualquier otro preguntale al profe de diseño."

        text +=". \nAdaptando tus features a este patrón, te sugiero implementar los siguientes modelos: "       

        for model in entities_grouped["MODEL"]:
            # Nombre del modelo
            text += "\nModelo: " + model
            # Propiedades
            salidas = graph_manager.graph.out_neighbors(model)
            propiedades = [s.name for s in salidas if Entity.get_category_by_shape(s.attr['shape']) == "PROPERTY"] # Sacar propiedadees para este modelo
            if propiedades:
                text += "\nPropiedades del modelo: " + " ,".join(propiedades)
            # Eventos / funciones

            eventos = [e.attr['label'] + " " +e[1] for e in graph_manager.graph.out_edges(model) if len(e.attr['label']) > 0]
            if eventos:
                text += "\nFunciones/responsabilidades (se pueden implementar en su controlador): " + " ,".join(eventos)

            componentes = [s.name for s in salidas if Entity.get_category_by_shape(s.attr['shape']) == "COMPONENT"] 
            if componentes:
                text += "\n El controlador de este modelo ademas debe tener soporte para conectarse con " + " y ".join(componentes)
        
        return text
        
    return "Ni idea como implementarlo"
         