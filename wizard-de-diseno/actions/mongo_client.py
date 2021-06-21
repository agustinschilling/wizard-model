from pymongo import MongoClient

# Conexión a MongoDB
mongo_url ='mongodb+srv://dbArquitectura:wizarddiseño@cluster0.owhd6.mongodb.net/ArquitecturaDataBase?retryWrites=true&w=majority'
client = MongoClient(mongo_url)
db = client.ArquitecturaDataBase

# Bases
arquitecturas = db.arquitecturas
conocimiento = db.conocimiento

def save_conocimiento(nombre, descripcion, tipo):
    """
    Almacena algun tipo de conocimiento nuevo para una palabra asociada
    """
    return conocimiento.update_one(
        { 'nombre':nombre },
        {   
            '$setOnInsert': {'sinonimos':[]},
            '$set': {'descripcion': descripcion,'tipo':tipo}
        }
    , upsert=True).modified_count

def update_sinonimos(nombre, sinonimos):
    """
    Actualiza la lista de sinonimos de un objeto de conocimiento x
    """
    return conocimiento.update_one(
        {'nombre': nombre },
        { '$push': {'sinonimos':{'$each': sinonimos}}}
    ).modified_count

def get_conocimiento(nombre):
    return conocimiento.find_one({'nombre':nombre})

def save_arqui(user_id,arqui,color_idx=0):
    """
    Guarda para un usuario determinado la arquitectura actualizada 
    y el índice de color que esta utilizando para el requerimiento actual
    """ 
    result = arquitecturas.update_one(
        {'user_id':user_id},
        {
            '$setOnInsert': {'user_id':user_id},
            '$push': {'arquis': arqui},
            '$set':{'color_idx': color_idx}
        },
         upsert=True)
    return result.modified_count

def load_arqui(user_id):
    """
    Devuelve la ultima version disponible de la
    arquitectura para un usuario determinado
    """
    arquis = arquitecturas.find_one({'user_id':user_id},{'arquis':{'$slice': -1},'color_idx':0,'user_id':0,'_id':0})
    if arquis: 
        return arquis['arquis'][0]

def load_color(user_id):
    """
    Devuelve el índice de color utilizado por última vez por esta arqui
    """
    arqui = arquitecturas.find_one({'user_id':user_id},{'color_idx':1,'_id':0})
    if arqui:
        return arqui['color_idx']

def remove_arqui(user_id):
    """
    Elimina la ultima arquitectura guardada
    """
    arquis = arquitecturas.find({'user_id':user_id},{'arquis':{'$exists':True,'$not':{'$size':0}}})
    if arquis.count() > 0: 
        return arquitecturas.update_one({'user_id':user_id},{'$pop':{'arquis':1}}) #el pop elimina de la lista 1(ultimo), -1(primero)


#  TEST
if __name__=="__main__":
    arqui1 = {"x":1}
    arqui2 = {"y":2}

    user_id = 124214

    # Guarda la primera
    save_arqui(user_id, arqui1)
    # Deberia imprimir la de x=1
    print(load_arqui(user_id))
    # Guarda la segunda
    save_arqui(user_id, arqui2)
    # Deberia imporimir la de y=2
    print(load_arqui(user_id))
    # sacamos la ultima que tiene
    remove_arqui(user_id)
    # imprime x=1
    print(load_arqui(user_id))