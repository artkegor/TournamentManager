import pymongo

client = pymongo.MongoClient('mongodb://localhost:27017/')
db = client['Tournaments']
collection = db['tournaments']


# Вывод всех данных для дебага
def print_all_data():
    for document in collection:
        print(document)


# Вставляем в БД новый турнир
def insert_tournament(tournament_id, chat_id, name, status):
    new_tournament = {
        "id": tournament_id,
        "chat": chat_id,
        "name": name,
        "status": status,
        "users": []
    }

    collection.insert_one(new_tournament)


# Вставляем пользователя в турнир
def add_user_to_tournament(tournament_id, user_id):
    tournament_doc = collection.find_one({"id": tournament_id})

    if not tournament_doc:
        return 'no tour'

    if 'users' not in tournament_doc or tournament_doc['status'] != 'register':
        return 'status'

    if user_id in tournament_doc['users']:
        return 'reg'

    tournament_doc['users'].append(user_id)
    collection.update_one({"id": tournament_id}, {"$set": {"users": tournament_doc['users']}})
    return 'good'


# Обновляем статус турнира
def update_tournament_status(tournament_id, status):
    collection.update_one({'id': tournament_id}, {'$set': {'status': status}})


# Получаем статус турнира
def get_tournament_status_by_id(tournament_id):
    tournament_doc = collection.find_one({"id": tournament_id})

    if not tournament_doc:
        return None

    return tournament_doc.get('status', None)


def get_tournament_users_by_id(tournament_id):
    tournament_doc = collection.find_one({"id": tournament_id})

    if not tournament_doc:
        return None

    return tournament_doc.get('users', None)


# Получаем турнир по ID чата
def find_tournament_by_chat_id(chat_id):
    tournament_doc = collection.find_one({"chat": chat_id})
    try:
        return tournament_doc['id']
    except NotImplementedError:
        return None
