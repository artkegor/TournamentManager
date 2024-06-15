import re
import time
import uuid
import random
import threading

from config import bot
from telebot import types
from datetime import datetime
import bot.keyboards.inline as mk
import bot.database.user_database as user_db
import bot.database.tournament_database as tr_db
import bot.utilities.tournament_helper as helper

bot.set_my_commands(commands=[types.BotCommand('/set', 'Внести игру'),
                              types.BotCommand('/start', 'Перезапустить бота'),
                              types.BotCommand('/launch', 'Запустить турнир'),
                              types.BotCommand('/delete', 'Удалить текущий турнир')])


@bot.message_handler(commands=['start'])
def start_message(message):
    threading.Timer(1.0, lambda: bot.delete_message(message.chat.id, message.message_id)).start()
    if message.chat.type in ['group', 'supergroup']:
        bot.send_message(message.chat.id, f'Привет, {message.from_user.first_name}! 👋\n\n'
                                          f'Чтобы посмотреть статистику текущего турнира введи /table 🏆\n\n'
                                          f'Если хочешь ввести результат игры то отметь меня, '
                                          f'или используй команду\n /set. 👀', reply_markup=mk.group_start_markup())
    else:
        if message.from_user.username:
            if ' ' in message.text:
                if not user_db.get_user_document_by_userid(message.chat.id):
                    user_db.insert_user(message.chat.id, message.from_user.username)
                args = message.text.split()[1]
                reg = tr_db.add_user_to_tournament(str(args), message.chat.id)

                if reg == 'no tour':
                    bot.send_message(message.chat.id, 'Турнир не найден.')
                elif reg == 'status':
                    bot.send_message(message.chat.id, 'Регистрация скорее всего кончилась.\n'
                                                      'Ждем тебя на следующем состязании.')
                elif reg == 'reg':
                    bot.send_message(message.chat.id, 'Ты уже зарегистрирован на турнире.')
                elif reg == 'good':
                    bot.send_message(message.chat.id, 'Ты присоединился к турниру.\n'
                                                      'Ожидай жеребьевки.')
            else:
                if not user_db.get_user_document_by_userid(message.chat.id):
                    user_db.insert_user(message.chat.id, message.from_user.username)
                bot.send_message(message.chat.id, text='Добрый день!\n'
                                                       'Готовы к новым победам? 🏆', reply_markup=mk.start_markup())
        else:
            bot.send_message(message.chat.id, 'Чтобы использовать бота установите себе юзернейм.')


@bot.message_handler(content_types=['new_chat_members'])
def start_group(message):
    if message.new_chat_members[0].username == 'TournamentManagebot':
        bot.send_message(message.chat.id, "Привет!\n"
                                          "Я здесь новенький.\n\n"
                                          "Нажми на кнопку снизу чтобы начать турнир.",
                         reply_markup=mk.group_start_markup())


@bot.callback_query_handler(func=lambda call: call.data.startswith('user'))
def callback_query(call):
    if not user_db.check_tournaments(call.message.chat.id):
        bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id,
                              text='Кажется, вы еще не участвовали в турнирах!')


@bot.callback_query_handler(func=lambda call: call.data.startswith('tourtype'))
def callback_query(call):
    admins = bot.get_chat_administrators(call.message.chat.id)
    for admin in admins:
        if admin.user.id == call.from_user.id:
            tournament_id = tr_db.find_tournament_by_chat_id(call.message.chat.id)
            if tournament_id:
                bot.answer_callback_query(call.id, text='Турнир уже запущен!')
            else:
                bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id,
                                      text='Выберите тип турнира:', reply_markup=mk.tournament_type())


@bot.callback_query_handler(func=lambda call: call.data.startswith('newtour_'))
def callback_query(call):
    admins = bot.get_chat_administrators(call.message.chat.id)
    for admin in admins:
        if admin.user.id == call.from_user.id:
            tournament_type = call.data.split('_')[1]
            tournament_id = str(random.randint(100000, 999999))

            tr_db.insert_tournament(tournament_id, call.message.chat.id, bot.get_chat(call.message.chat.id).title,
                                    'register', tournament_type)

            bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id,
                                  text=f'Турнир создан.\n'
                                       'До конца регистрации 30 секунд.',
                                  reply_markup=mk.new_tournament(tournament_id))

            def starter_func(tournament_type):
                for i in range(300):
                    time.sleep(5)
                    if tr_db.get_tournament_status_by_id(tournament_id) == 'going':
                        break
                    else:
                        users = tr_db.get_tournament_users_by_id(tournament_id)
                        try:
                            bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id,
                                                  text=f'Турнир создан.\n'
                                                       'До конца регистрации 30 секунд.\n\n'
                                                       f'Присоединились: {", ".join(str(bot.get_chat_member(call.message.chat.id, x).user.first_name) for x in users)}',
                                                  reply_markup=mk.new_tournament(tournament_id))
                        except:
                            if not tr_db.get_tournament_users_by_id(tournament_id):
                                bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id,
                                                      text='Турнир был удален.')
                                return
                            else:
                                pass

                users = tr_db.get_tournament_users_by_id(tournament_id)
                user_db.update_users_with_current_tournament(call.message.chat.id, users)
                tr_db.update_tournament_status(tournament_id, 'going')

                if len(users) % 2 == 1:
                    tournament_type = 'free'
                    tr_db.update_tournament_schedule_type(tournament_id, tournament_type)

                if tournament_type == 'free':
                    bot.delete_message(call.message.chat.id, call.message.message_id)
                    bot.send_message(call.message.chat.id, 'Турнир объявляется открытым!\n\n'
                                                           f'🫂 Зарегистрированы: {", ".join(str(bot.get_chat_member(call.message.chat.id, x).user.first_name) for x in users)}\n\n'
                                                           f'❕ Турнир проводится в свободном расписании, '
                                                           f'играйте с кем угодно и когда угодно.')

                else:
                    bot.delete_message(call.message.chat.id, call.message.message_id)
                    bot.send_message(call.message.chat.id, 'Регистрация окончена!\n'
                                                           'Формирую расписание игр...\n\n'
                                                           f'🫂 На турнир зарегистрированы: {", ".join(str(bot.get_chat_member(call.message.chat.id, x).user.first_name) for x in users)}\n\n'
                                     )

                    games = helper.round_robin(tr_db.get_tournament_users_by_id(tournament_id))
                    tr_db.insert_schedule_to_tournament(games, tournament_id)

                    for item in games:
                        if isinstance(item, list):
                            new_item = []
                            for subitem in item:
                                if isinstance(subitem, tuple):
                                    new_subitem = (
                                        bot.get_chat_member(call.message.chat.id, subitem[0]).user.first_name,
                                        bot.get_chat_member(call.message.chat.id, subitem[1]).user.first_name)
                                    new_item.append(new_subitem)
                            item[:] = new_item

                    helper.generate_and_save_tables(games, tournament_id, bot.get_chat(call.message.chat.id).title)

                    bot.send_document(call.message.chat.id,
                                      document=open(f'bot/utilities/data/{tournament_id}.png', 'rb'),
                                      caption='Расписание ☝\n\n'
                                              'Турнир объявляется открытым!\n'
                                              f'❕ Игры проводится по фиксированным датам.')

            threading.Thread(target=starter_func(tournament_type)).start()


@bot.message_handler(commands=['launch'])
def launch_tournament(message):
    threading.Timer(1.0, lambda: bot.delete_message(message.chat.id, message.message_id)).start()
    if message.chat.type in ['group', 'supergroup']:
        admins = bot.get_chat_administrators(message.chat.id)
        for admin in admins:
            if admin.user.id == message.from_user.id:
                tournament_id = tr_db.find_tournament_by_chat_id(message.chat.id)
                if tournament_id:
                    tr_db.update_tournament_status(tournament_id, 'going')
                else:
                    bot.send_message(message.chat.id, 'Никакой турнир сейчас не запущен.')
    else:
        bot.send_message(message.chat.id, 'Команда применима только в группе.')


@bot.message_handler(commands=['delete'])
def launch_tournament(message):
    threading.Timer(1.0, lambda: bot.delete_message(message.chat.id, message.message_id)).start()
    if message.chat.type in ['group', 'supergroup']:
        admins = bot.get_chat_administrators(message.chat.id)
        for admin in admins:
            if admin.user.id == message.from_user.id:
                status = tr_db.find_tournament_by_chat_id(message.chat.id)
                if not status:
                    bot.send_message(message.chat.id, 'Никакой турнир не запущен')
                else:
                    users = tr_db.get_tournament_users_by_chat_id(message.chat.id)
                    user_db.update_users_with_current_tournament(False, users)
                    tr_db.delete_tournament_by_chat_id(message.chat.id)
                    bot.send_message(message.chat.id, 'Текущий турнир удален')
    else:
        bot.send_message(message.chat.id, 'Команда применима только в группе.')


@bot.message_handler(commands=['set'])
def set_message(message):
    threading.Timer(1.0, lambda: bot.delete_message(message.chat.id, message.message_id)).start()
    if ' ' in message.text:
        if len(message.text.split()) != 3:
            bot.send_message(message.chat.id, 'Чтобы внести игру, введите ник оппонента и счет.')
        else:
            cmd, username, score = message.text.split()
            first_player = message.from_user.id
            second_player = user_db.get_user_document_by_username(username[1:])['userId']
            chat_id_1 = user_db.get_user_document_by_username(message.from_user.username)['current_chat']
            chat_id_2 = user_db.get_user_document_by_username(username[1:])['current_chat']

            if chat_id_1 != chat_id_2:
                bot.send_message(message.chat.id,
                                 'Вы участвуете в разных турнирах, или игрок не присоединился к соревнованиям.')
            else:
                game = tr_db.find_game_by_users_and_chat(first_player, second_player, chat_id_1)
                if not game:
                    if not tr_db.get_tournament_users_by_chat_id(chat_id_1):
                        bot.send_message(message.chat.id, 'Никакой турнир сейчас не запущен.')
                    else:
                        tourne = tr_db.get_tournament_type_by_chat_id(chat_id_1)
                        if tourne == 'free':
                            tr_db.add_new_game(chat_id_1, first_player, second_player)
                            game = tr_db.find_game_by_users_and_chat(first_player, second_player, chat_id_1)
                            game_id = game['game_id']
                            games_left = game['games_left']
                            if tr_db.insert_game_result(chat_id_1, game_id, score, games_left, first_player,
                                                        second_player):
                                bot.send_message(message.chat.id, 'Игра внесена.\n\n'
                                                                  f'@{message.from_user.username} {score} {username}')
                        else:
                            bot.send_message(message.chat.id, 'Никакой турнир сейчас не запущен.')
                else:
                    tourne = tr_db.get_tournament_type_by_chat_id(chat_id_1)
                    if tourne == 'free':
                        if game['games_left'] > 0:
                            game_id = game['game_id']
                            games_left = game['games_left']
                            if tr_db.insert_game_result(chat_id_1, game_id, score, games_left, first_player,
                                                        second_player):
                                bot.send_message(message.chat.id, 'Игра внесена.\n\n'
                                                                  f'@{message.from_user.username} {score} {username}')
                        else:
                            bot.send_message(message.chat.id, 'Вы уже внесли две игры с этим пользователем.')
                    elif game['type'] == 'fix':
                        game_date_str = game['date']
                        game_date = datetime.strptime(game_date_str, '%d/%m/%y')
                        today_date = datetime.now()

                        if game_date.date() == today_date.date():
                            games_left = game['games_left']
                            if games_left > 0:
                                game_id = game['game_id']
                                if tr_db.insert_game_result(chat_id_1, game_id, score, games_left, first_player,
                                                            second_player):
                                    bot.send_message(message.chat.id, 'Игра внесена.\n\n'
                                                                      f'@{message.from_user.username} {score} {username}')
                                else:
                                    bot.send_message(message.chat.id, 'Ошибка!')

                            else:
                                bot.send_message(message.chat.id, 'Вы уже внесли две игры с этим пользователем.')
                        else:
                            bot.send_message(message.chat.id, 'Сегодня вы играете с другим игроком.')

    else:
        bot.send_message(message.chat.id, 'ℹ️ Чтобы внести игру, введите сообщение в формате\n\n'
                                          '<code>/set [@ник соперника] [счет (свой:соперника)]</code>', parse_mode='html')


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
                elif game['type'] == 'fix':
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
