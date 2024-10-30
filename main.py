import atexit

import pymongo
from datetime import datetime
from bot.bot import bot


# Подключаемся к БД для дампов
def connect_to_mongodb():
    client = pymongo.MongoClient('mongodb://localhost:27017/')
    db = client['Tournaments']
    tournaments_collection = db['tournaments']
    users_collection = db['users']
    return tournaments_collection, users_collection


# Приводим данные в порядок
def fetch_data(tournaments_collection, users_collection):
    tournaments_data = list(tournaments_collection.find())
    users_data = list(users_collection.find())
    return tournaments_data, users_data


# Сохраняем снимок БД в файл
def save_data_to_file(data, filename):
    with open(filename, 'w') as file:
        file.write("Tournaments Data:\n")
        for tournament in data[0]:
            file.write(str(tournament) + "\n")
        file.write("\nUsers Data:\n")
        for user in data[1]:
            file.write(str(user) + "\n")


# Создаем снимок
def exit_dump():
    tournaments_collection, users_collection = connect_to_mongodb()
    data = fetch_data(tournaments_collection, users_collection)
    filename = datetime.now().strftime("%d-%m-%y_%H-%M.txt")

    save_data_to_file(data, filename)


if __name__ == '__main__':
    # Запуск бота
    atexit.register(exit_dump)
    bot.infinity_polling()
