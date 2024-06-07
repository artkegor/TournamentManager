import pymongo

client = pymongo.MongoClient('mongodb://localhost:27017/')
db = client['Tournaments']
collection = db['users']


# Вывод всех данных (для дебага)
def print_all_data(collection):
    for document in collection.find:
        print(document)


# Вставляем в БД нового пользователя
def insert_user(userid, username):
    filter = {'userId': userid}
    update = {'$set': {'username': username}}

    collection.update_one(filter, update, upsert=True)


# Получаем пользователя
def get_user_document_by_userid(userid):
    user_document = collection.find_one({'userId': userid})

    return user_document


# Проверяем участвовал ли пользователь в турнирах
def check_tournaments(userid):
    filter = {'userId': userid}

    result = collection.find_one(filter, {"tournaments": 1})

    if result is None:
        return None
    else:
        return result.get('tournaments', None)
