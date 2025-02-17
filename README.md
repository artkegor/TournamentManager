# Tournament Manager 🏆
Бот создан для организации и проведения спортивных и киберспортивных мероприятий. 

Чтобы организовать турнир - соберите всех участников в одну группу и нажмите `/start`.

## Особенности 

- Бот написан на Python, с использованием библиотеки Telebot
- База данных реализована с помощью MongoDB, на сервере работает через Docker
- Для работы системы мы сохраняем в базу данных две таблицы: с пользователями и турнирами

## Установка

- Чтобы запустить бота, необходимо в исходный код скачанного проекта добавить файл .env, куда будут добавлены токены для работы с API Telegram
- Все требования по библиотекам находятся в файле [requirements.txt](https://github.com/artkegor/tournament_manager/blob/master/requirements.txt):
  ```sh
  $ pip install -r requirements.txt
  ```
- Для работы на сервере нужно запустить базу данных Mongo в Docker-контейнере с помощью следующих команд:
  ```sh
  $ docker pull mongo:latest
  $ docker run -d -p 27017:27017 --name mongodb mongo:latest
  ```
- Чтобы запустить бота можно использовать [Nohup](https://ru.wikipedia.org/wiki/Nohup):
  ```sh
  $ nohup python main.py &
  ```
