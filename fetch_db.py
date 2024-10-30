import pymongo

if __name__ == '__main__':
    # Подключение к БД
    client = pymongo.MongoClient('mongodb://localhost:27017/')
    db = client['Tournaments']

    # Вывод всех турниров
    collection = db['tournaments']
    cursor = collection.find({})
    for row in cursor:
        print(row)

    # Вывод всех пользователей
    collection = db['users']
    cursor = collection.find({})
    for row in cursor:
        print(row)
