import pymongo
from datetime import timedelta, datetime
import locale
import datetime

client = pymongo.MongoClient('mongodb://localhost:27017/')
db = client['Tournaments']
collection = db['tournaments']


# Вывод всех данных для дебага
def print_all_data():
    for document in collection:
        print(document)


# Insert
# Вставляем в БД новый турнир
def insert_tournament(tournament_id, chat_id, status, type, name_entered):
    existing_tournament = collection.find_one({"chat": chat_id})

    if existing_tournament:
        collection.delete_one({"chat": chat_id})

    new_tournament = {
        "id": tournament_id,
        "chat": chat_id,
        "name_entered": name_entered,
        "status": status,
        "type": type,
        'current_game_number': 1,
        "users": [],
        "games": []
    }

    collection.insert_one(new_tournament)


# Update
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


# Вставляем игры в фиксированный турнир
def insert_schedule_to_tournament(schedule_list, tournament_id):
    tournament = collection.find_one({"id": tournament_id})

    if tournament:
        game_id_counter = len(tournament.get("games", [])) + 1
        start_date = datetime.datetime.now().date()

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
                    "games_left": 2,
                    "first_game_results": {},
                    "second_game_results": {},
                }

                tournament["games"].append(game_doc)
                game_id_counter += 1

        collection.update_one({"id": tournament_id}, {"$set": tournament})


# Вставляем игру в свободный турнир
def add_new_game(chat_id, first_player, second_player):
    doc = collection.find_one({'chat': chat_id})

    if doc:
        games_length = len(doc.get('games', []))
        new_game = {
            "game_id": games_length + 1,
            "first_player": first_player,
            "second_player": second_player,
            "games_left": 2,
            "first_game_results": {},
            "second_game_results": {}
        }

        doc['games'].append(new_game)

        collection.update_one({'_id': doc['_id']}, {'$set': {'games': doc['games']}})


# Вставлем результат игры
def insert_game_result(chat_id, game_id, score, games_left, user_id_1, user_id_2):
    game = find_game_by_id(chat_id, game_id)
    number = get_current_game(chat_id)
    if game:
        locale.setlocale(locale.LC_TIME, 'ru_RU.UTF-8')
        now = datetime.datetime.now()
        if games_left == 2:
            game['first_game_results'] = {
                'number': number,
                'first_player': user_id_1,
                'second_player': user_id_2,
                'score': score,
                'date': now.strftime('%a %d.%m.%Y').upper(),
                'time': now.strftime('%H:%M')
            }
            games_left -= 1
        elif games_left == 1:
            game['second_game_results'] = {
                'number': number,
                'first_player': user_id_1,
                'second_player': user_id_2,
                'score': score,
                'date': now.strftime('%a %d.%m.%Y').upper(),
                'time': now.strftime('%H:%M')
            }
            games_left -= 1
        collection.update_one({'chat': chat_id, 'games.game_id': game_id},
                              {'$set': {'games.$': game}})
        collection.update_one({'chat': chat_id, 'games.game_id': game_id},
                              {'$set': {'games.$.games_left': games_left}})
        return True
    else:
        return False


# Обновляем результат игры
def update_game_score(chat_id, game_number, new_score):
    document = collection.find_one({'chat': chat_id})

    if document:
        for game in document.get('games', []):
            if int(game.get('first_game_results', {}).get('number')) == int(game_number):
                game['first_game_results']['score'] = new_score
                break
            elif int(game.get('second_game_results', {}).get('number')) == int(game_number):
                game['second_game_results']['score'] = new_score
                break
        else:
            return False

        collection.update_one(
            {'chat': chat_id, 'games.game_id': game['game_id']},
            {'$set': {'games.$': game}}
        )

        return True

    return False


# Обновляем статус турнира
def update_tournament_status(tournament_id, status):
    collection.update_one({'id': tournament_id}, {'$set': {'status': status}})


# Обновляем статус турнира по ID чата
def update_tournament_status_by_chat(chat, status):
    collection.update_one({'chat': chat}, {'$set': {'status': status}})


# Обновляем тип расписания турнира
def update_tournament_schedule_type(tournament_id, status):
    collection.update_one({'id': tournament_id}, {'$set': {'type': status}})


# Find
# Получаем игру по ID-игры и турнира
def find_game_by_id(chat_id, game_id):
    document = collection.find_one({'chat': chat_id})
    if document:
        for game in document.get('games', []):
            if game.get('game_id') == game_id:
                return game
    return None


# Получаем статус турнира
def get_tournament_status_by_id(tournament_id):
    tournament_doc = collection.find_one({"id": tournament_id})

    if not tournament_doc:
        return None

    return tournament_doc.get('status', None)


# Получаем ID чата по ID турнирв
def get_tournament_chat_id_by_id(tournament_id):
    tournament_doc = collection.find_one({"id": tournament_id})

    if not tournament_doc:
        return None

    return int(tournament_doc.get('chat', None))


# Получаем и обновляем текущий номер игры
def get_current_game(chat_id):
    tournament_doc = collection.find_one({'chat': chat_id})

    if not tournament_doc:
        return None

    game_number = tournament_doc.get('current_game_number', None)
    collection.update_one({'chat': chat_id}, {'$set': {'current_game_number': game_number + 1}})

    return game_number


# Получаем статус турнира по ID чата
def get_tournament_status_by_chat_id(chat):
    tournament_doc = collection.find_one({"chat": chat})

    if not tournament_doc:
        return None

    return tournament_doc.get('status', None)


# Получаем имя турнира по ID чата
def get_tournament_name_by_chat_id(chat):
    tournament_doc = collection.find_one({"chat": chat})

    if not tournament_doc:
        return None

    return tournament_doc.get('name_entered', None)


# Получаем участников по ID турнира
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


# Получаем тип турнира по ID чата
def get_tournament_type_by_chat_id(chat):
    tournament_doc = collection.find_one({"chat": chat})

    if not tournament_doc:
        return None

    return tournament_doc.get('type', None)


# Получаем игры по ID чата
def get_tournament_games_by_chat_id(chat):
    tournament_doc = collection.find_one({"chat": chat})

    if not tournament_doc:
        return None

    return tournament_doc.get('games', None)


# Получаем сыгранные игры
def get_played_games_by_chat_id(chat):
    tournament_doc = collection.find_one({"chat": chat})

    if tournament_doc:
        game_results = []

        for game in tournament_doc.get('games', []):
            if game.get('first_game_results') and game.get('second_game_results'):
                game_results.append(game['first_game_results'])
                game_results.append(game['second_game_results'])
            elif game.get('first_game_results'):
                game_results.append(game['first_game_results'])
            elif game.get('second_game_results'):
                game_results.append(game['second_game_results'])

        return game_results
    else:
        return None


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


# Удаляем пользователя из турнира
def remove_user_from_tournament(chat_id, user_id):
    collection.update_one(
        {"chat": chat_id},
        {"$pull": {"users": user_id}}
    )


# Delete
# Удаляем турнир
def delete_tournament_by_chat_id(chat_id):
    collection.delete_one({"chat": chat_id})
