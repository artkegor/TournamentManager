import re
import uuid
import datetime
from telebot import types

import bot.database.user_database as user_db
import bot.database.tournament_database as tr_db


# Обработчик команд встроенного бота
def register_inline_handlers(bot):
    @bot.inline_handler(func=lambda query: len(query.query) > 0)
    def query_text(query):
        result = None
        pattern = r"@\w+\s\d+:\d+"
        match = re.search(pattern, query.query)
        if match:
            username = query.query.split(' ')[0]
            score = query.query.split(' ')[1]

            author_id = query.from_user.id
            mentioned_id = user_db.get_user_document_by_username(username[1:])['userId']
            chat_id_a = user_db.get_user_document_by_username(query.from_user.username)['current_chat']
            chat_id_b = user_db.get_user_document_by_username(username[1:])['current_chat']

            if chat_id_b != chat_id_a:
                number = str(uuid.uuid4())
                title = 'Ошибка!'
                description = 'Один из игроков участвует в другом турнире, или не присоединился к игре.'
                result = types.InlineQueryResultArticle(
                    id=number,
                    title=title,
                    description=description,
                    input_message_content=types.InputTextMessageContent(description)
                )
            else:
                game = tr_db.find_game_by_users_and_chat(author_id, mentioned_id, chat_id_a)
                if not game:
                    if not tr_db.get_tournament_users_by_chat_id(chat_id_a):
                        number = str(uuid.uuid4())
                        title = 'Ошибка'
                        description = 'Никакой турнир сейчас не запущен.'
                        result = types.InlineQueryResultArticle(
                            id=number,
                            title=title,
                            description=description,
                            input_message_content=types.InputTextMessageContent(description)
                        )
                    else:
                        tourne = tr_db.get_tournament_type_by_chat_id(chat_id_a)
                        if tourne == 'free':
                            number = str(uuid.uuid4())
                            title = 'Внести игру'
                            description = f'@{query.from_user.username} {score} {username}'
                            command = f'/set {username} {score}'
                            result = types.InlineQueryResultArticle(
                                id=number,
                                title=title,
                                description=description,
                                input_message_content=types.InputTextMessageContent(command)
                            )
                        else:
                            number = str(uuid.uuid4())
                            title = 'Ошибка'
                            description = 'Никакой турнир сейчас не запущен.'
                            result = types.InlineQueryResultArticle(
                                id=number,
                                title=title,
                                description=description,
                                input_message_content=types.InputTextMessageContent(description)
                            )
                else:
                    tourne = tr_db.get_tournament_type_by_chat_id(chat_id_a)
                    if tourne == 'free':
                        if game['games_left'] > 0:
                            number = str(uuid.uuid4())
                            title = 'Внести игру'
                            description = f'@{query.from_user.username} {score} {username}'
                            command = f'/set {username} {score}'
                            result = types.InlineQueryResultArticle(
                                id=number,
                                title=title,
                                description=description,
                                input_message_content=types.InputTextMessageContent(command)
                            )
                        else:
                            number = str(uuid.uuid4())
                            title = 'Ошибка!'
                            description = 'Вы уже внесли две игры с этим пользователем.'

                            result = types.InlineQueryResultArticle(
                                id=number,
                                title=title,
                                description=description,
                                input_message_content=types.InputTextMessageContent(description)
                            )
                    elif tourne == 'fix':
                        game_date_str = game['date']
                        game_date = datetime.strptime(game_date_str, '%d/%m/%y')
                        today_date = datetime.now()

                        if game_date.date() == today_date.date():
                            if game['games_left'] > 0:
                                number = str(uuid.uuid4())
                                title = 'Внести игру'
                                description = f'@{query.from_user.username} {score} {username}'
                                command = f'/set {username} {score}'
                                result = types.InlineQueryResultArticle(
                                    id=number,
                                    title=title,
                                    description=description,
                                    input_message_content=types.InputTextMessageContent(command)
                                )
                            else:
                                number = str(uuid.uuid4())
                                title = 'Ошибка!'
                                description = 'Вы уже внесли две игры с этим пользователем.'

                                result = types.InlineQueryResultArticle(
                                    id=number,
                                    title=title,
                                    description=description,
                                    input_message_content=types.InputTextMessageContent(description)
                                )
                        else:
                            number = str(uuid.uuid4())
                            title = 'Ошибка!'
                            description = 'Сегодня вы играете с другим участником.'

                            result = types.InlineQueryResultArticle(
                                id=number,
                                title=title,
                                description=description,
                                input_message_content=types.InputTextMessageContent(description),
                            )

            bot.answer_inline_query(query.id, [result])
