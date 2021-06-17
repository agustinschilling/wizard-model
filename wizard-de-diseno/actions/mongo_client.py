from pymongo import MongoClient
mongo_url ='mongodb+srv://dbArquitectura:wizarddiseño@cluster0.owhd6.mongodb.net/ArquitecturaDataBase?retryWrites=true&w=majority'

client = MongoClient(mongo_url)
db = client.ArquitecturaDataBase

arquitecturas = db.arquitecturas

#insertar un solo doc
def save_arqui(user_id,arqui,color_idx=0):
    # TODO: guardar lista de arquis, poner vacia en el setOnInsert, y desp en el set agregarla a la lista
    result = arquitecturas.update_one(
        {'user_id':user_id},
        {
            '$setOnInsert': {'user_id':user_id},
            '$push': {'arquis': arqui},
            '$set':{'color_idx': color_idx}
        },
         upsert=True)
    return result.modified_count

# TODO: traer la lista y sacar la utima. Chequear si la lista esta vacia!! Devolver none
def load_arqui(user_id):
    #arquis = arquitecturas.find({'user_id':user_id},{'arquis':{'$exists':True,'$not':{'$size':0}}})
    arquis = arquitecturas.find_one({'user_id':user_id},{'arquis':{'$slice': -1},'color_idx':0,'user_id':0,'_id':0})
    if arquis: 
        return arquis['arquis'][0]

def load_color(user_id):
    arqui = arquitecturas.find_one({'user_id':user_id},{'color_idx':1,'arqui':0,'user_id':0,'_id':0})
    if arqui:
        return arqui['color_idx']

# TODO: consultar si el user_id tiene una lista de arquis y no esta vacia, sacar la ultima
def remove_arqui(user_id):
    arquis = arquitecturas.find({'user_id':user_id},{'arquis':{'$exists':True,'$not':{'$size':0}}})
    if arquis.count() > 0: 
        return arquitecturas.update_one({'user_id':user_id},{'$pop':{'arquis':1}}) #el pop elimina de la lista 1(ultimo), -1(primero)

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