import pymongo

client = pymongo.MongoClient('mongodb://localhost:27017/')
db = client['Tournaments']
collection = db['users']


# Вывод всех данных (для дебага)
def print_all_data(collection):
    for document in collection.find:
        print(document)


# Update
# Вставляем в БД нового пользователя
def insert_user(userid, username):
    filter = {'userId': userid}
    update = {'$set': {'username': username, 'current_chat': False}}

    collection.update_one(filter, update, upsert=True)


# Вставляем оконченный турнир в документ пользователя
def insert_tournament_to_user(user_id, tournament_data):
    user = collection.find_one({"userId": user_id})
    if user:
        if "tournaments" not in user:
            user["tournaments"] = []

        user["tournaments"].append(tournament_data)
        collection.update_one({"_id": user["_id"]}, {"$set": user})


# Обновляем пользователям текущий турнир
def update_users_with_current_tournament(current_chat, users):
    for i in users:
        user_document = collection.find_one({'userId': i})
        if user_document:
            collection.update_one({"userId": i}, {"$set": {'current_chat': current_chat}}, upsert=False)


# Find
# Получаем пользователя по ID
def get_user_document_by_userid(userid):
    user_document = collection.find_one({'userId': userid})

    return user_document


# Получаем пользователя по нику
def get_user_document_by_username(username):
    user_document = collection.find_one({'username': username})

    return user_document


# Получаем турниры пользователя
def get_user_tournaments_by_userid(userid):
    user_document = collection.find_one({'userId': userid})

    if 'tournaments' in user_document:
        return user_document['tournaments']
    else:
        return None
