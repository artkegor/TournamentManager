import pymongo
from datetime import timedelta, datetime

client = pymongo.MongoClient('mongodb://localhost:27017/')
db = client['Tournaments']
collection = db['tournaments']


# Вывод всех данных для дебага
def print_all_data():
    for document in collection:
        print(document)


# Вставляем в БД новый турнир
def insert_tournament(tournament_id, chat_id, name, status, type):
    existing_tournament = collection.find_one({"chat": chat_id})

    if existing_tournament:
        collection.delete_one({"chat": chat_id})

    new_tournament = {
        "id": tournament_id,
        "chat": chat_id,
        "name": name,
        "status": status,
        "type": type,
        "users": [],
        "games": []
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


# Вставляем расписание в игру
def insert_schedule_to_tournament(schedule_list, tournament_id):
    tournament = collection.find_one({"id": tournament_id})

    if tournament:
        game_id_counter = len(tournament.get("games", [])) + 1
        start_date = datetime.now().date()

        for game_set_index, game_set in enumerate(schedule_list):
            if game_set_index == 0:
                game_set_date = start_date
            else:
                game_set_date = start_date + timedelta(days=(game_set_index * 2))

            for game in game_set:
                game_doc = {
                    "game_id": game_id_counter,
                    "date": game_set_date.strftime("%d/%m/%y"),
                    "first_player": game[0],
                    "second_player": game[1],
                    "games_left": 2
                }

                tournament["games"].append(game_doc)
                game_id_counter += 1

        collection.update_one({"id": tournament_id}, {"$set": tournament})


# Обновляем статус турнира
def update_tournament_status(tournament_id, status):
    collection.update_one({'id': tournament_id}, {'$set': {'status': status}})


# Обновляем тип расписания турнира
def update_tournament_schedule_type(tournament_id, status):
    collection.update_one({'id': tournament_id}, {'$set': {'type': status}})


# Получаем статус турнира
def get_tournament_status_by_id(tournament_id):
    tournament_doc = collection.find_one({"id": tournament_id})

    if not tournament_doc:
        return None

    return tournament_doc.get('status', None)


# Получаем участников по ID
def get_tournament_users_by_id(tournament_id):
    tournament_doc = collection.find_one({"id": tournament_id})

    if not tournament_doc:
        return None

    return tournament_doc.get('users', None)


# Получаем участников по ID чата
def get_tournament_users_by_chat_id(chat):
    tournament_doc = collection.find_one({"chat": chat})

    if not tournament_doc:
        return None

    return tournament_doc.get('users', None)


# Получаем турнир по ID чата
def find_tournament_by_chat_id(chat_id):
    tournament_doc = collection.find_one({"chat": chat_id})
    if tournament_doc:
        return tournament_doc['id']
    else:
        return None


# Получаем игру по турниру и двум пользователям
def find_game_by_users_and_chat(user_id_1, user_id_2, chat_id):
    document = collection.find_one({'chat': chat_id})

    if document:
        for game in document.get('games', []):
            if game.get('first_player') == user_id_1 and game.get('second_player') == user_id_2:
                return game
            elif game.get('first_player') == user_id_2 and game.get('second_player') == user_id_1:
                return game
    else:
        return None


# Удаляем турнир
def delete_tournament_by_chat_id(chat_id):
    collection.delete_one({"chat": chat_id})
