import os
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

bot.set_my_commands(commands=[types.BotCommand('/rules', 'Правила пользования'),
                              types.BotCommand('/set', 'Внести игру'),
                              types.BotCommand('/table', 'Текущие результаты'),
                              types.BotCommand('/games', 'Сыгранные игры'),
                              types.BotCommand('/quit', 'Покинуть турнир'),
                              types.BotCommand('/start', 'Перезапустить бота'),
                              types.BotCommand('/members', 'Участники турнира'),
                              types.BotCommand('/add', 'Добавить игроков в турнир'),
                              types.BotCommand('/admin_set', 'Админ вносит игру'),
                              types.BotCommand('/launch', 'Запустить турнир'),
                              types.BotCommand('/finish', 'Завершить турнир'),
                              types.BotCommand('/delete', 'Удалить текущий турнир')])


@bot.message_handler(content_types=['new_chat_members'])
def start_group(message):
    if message.new_chat_members[0].username == 'TournamentManagebot':
        bot.send_message(message.chat.id, "Привет!\n"
                                          "Я здесь новенький.\n\n"
                                          "Нажми на кнопку снизу чтобы начать турнир.",
                         reply_markup=mk.group_start_markup())


@bot.message_handler(commands=['rules'])
def start_message(message):
    threading.Timer(1.0, lambda: bot.delete_message(message.chat.id, message.message_id)).start()
    bot.send_message(message.chat.id, 'Инструкция по использованию бота:\n\n'
                                      'https://grabovsky.notion.site/0885db94e2c84e6e9c42150826b814ca?pvs=4')


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
                if not user_db.get_user_document_by_userid(message.chat.id)['current_chat']:
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
                    bot.send_message(message.chat.id, 'Вы уже участвуете в другом турнире.')
            else:
                if not user_db.get_user_document_by_userid(message.chat.id):
                    user_db.insert_user(message.chat.id, message.from_user.username)
                bot.send_message(message.chat.id, text='Добрый день!\n'
                                                       'Готовы к новым победам? 🏆', reply_markup=mk.start_markup())
        else:
            bot.send_message(message.chat.id, 'Чтобы использовать бота установите себе юзернейм.')


@bot.callback_query_handler(func=lambda call: call.data.startswith('user'))
def callback_query(call):
    results = user_db.get_user_tournaments_by_userid(call.message.chat.id)
    if not results:
        bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id,
                              text='Кажется, вы еще не участвовали в турнирах.', reply_markup=mk.back_markup())
    else:
        bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id,
                              text='ℹ️ Все турниры, в которых вы участвовали:', reply_markup=mk.my_markup(results))


@bot.callback_query_handler(func=lambda call: call.data.startswith('back'))
def callback_query(call):
    bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id,
                          text='Добрый день!\n'
                               'Готовы к новым победам? 🏆',
                          reply_markup=mk.start_markup())


@bot.callback_query_handler(func=lambda call: call.data.startswith('my'))
def callback_query(call):
    index = int(call.data.split('_')[1])
    tourne_profile = user_db.get_user_tournaments_by_userid(call.message.chat.id)[index]
    bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id,
                          text=f'{tourne_profile["title"]}\n\n'
                               f'{tourne_profile["place"]}-е место 🏆\n'
                               f'Очки: {tourne_profile["score"]}\n'
                               f'Статистика: '
                               f'{tourne_profile["games_results"]["wins"]} - {tourne_profile["games_results"]["draws"]}'
                               f' - {tourne_profile["games_results"]["losses"]}',
                          reply_markup=mk.my_back_markup())


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
                                      text='Введите название турнира:')
                bot.register_next_step_handler(call.message, lambda message: get_name(message))


def get_name(message):
    name = message.text
    with open(f'bot/cache/{message.chat.id}.txt', 'w') as f:
        f.write(name)
    bot.send_message(chat_id=message.chat.id,
                     text='Выберите тип турнира:', reply_markup=mk.tournament_type())


@bot.callback_query_handler(func=lambda call: call.data.startswith('nw_'))
def callback_query(call):
    admins = bot.get_chat_administrators(call.message.chat.id)
    for admin in admins:
        if admin.user.id == call.from_user.id:
            tournament_type = call.data.split('_')[1]
            with open(f'bot/cache/{call.message.chat.id}.txt', 'r') as f:
                name = f.readline().strip()
            os.remove(f'bot/cache/{call.message.chat.id}.txt')

            tournament_id = str(random.randint(100000, 999999))

            tr_db.insert_tournament(tournament_id, call.message.chat.id,
                                    'register', tournament_type, name)

            bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id,
                                  text=f'Турнир создан.\n'
                                       'До конца регистрации 24 часа.',
                                  reply_markup=mk.new_tournament(tournament_id))

            def starter_func(tournament_type, entered_name):
                for i in range(7200):
                    time.sleep(5)
                    if tr_db.get_tournament_status_by_id(tournament_id) == 'going':
                        break

                users = tr_db.get_tournament_users_by_id(tournament_id)
                user_db.update_users_with_current_tournament(call.message.chat.id, users)
                tr_db.update_tournament_status(tournament_id, 'going')

                if len(users) % 2 == 1:
                    tournament_type = 'free'
                    tr_db.update_tournament_schedule_type(tournament_id, tournament_type)

                if tournament_type == 'free':
                    bot.delete_message(call.message.chat.id, call.message.message_id)
                    bot.send_photo(call.message.chat.id, photo=open(f'bot/utilities/data/start.jpg', 'rb'),
                                   caption='Турнир объявляется открытым!\n\n'
                                           f'🫂 Зарегистрированы: {", ".join(str(bot.get_chat_member(call.message.chat.id, x).user.first_name) for x in users)}\n\n'
                                           f'❕ Турнир проводится в свободном расписании, '
                                           f'играйте с кем угодно и когда угодно по две игры.')

                    bot.send_message(call.message.chat.id,
                                     'ℹ️ Чтобы внести результат игры, введите сообщение в формате\n\n'
                                     '<code>/set [@ник соперника] [счет (свой:соперника)]</code>',
                                     parse_mode='html')

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

                    helper.generate_and_save_tables(games, tournament_id, entered_name)

                    bot.send_document(call.message.chat.id,
                                      document=open(f'bot/utilities/data/{tournament_id}.png', 'rb'),
                                      visible_file_name='Расписание.png')
                    bot.send_photo(call.message.chat.id,
                                   photo=open(f'bot/utilities/data/start.jpg', 'rb'),
                                   caption='Расписание ☝\n\n'
                                           'Турнир объявляется открытым!\n'
                                           f'❕Игры проводится по фиксированным датам.',
                                   )

                    bot.send_message(call.message.chat.id,
                                     'ℹ️ Чтобы внести результат игры, введите сообщение в формате\n\n'
                                     '<code>/set [@ник соперника] [счет (свой:соперника)]</code>',
                                     parse_mode='html')

                    os.remove(f'bot/utilities/data/{tournament_id}.png')

            threading.Thread(target=starter_func(tournament_type, name)).start()


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
def delete_tournament(message):
    threading.Timer(1.0, lambda: bot.delete_message(message.chat.id, message.message_id)).start()
    if message.chat.type in ['group', 'supergroup']:
        admins = bot.get_chat_administrators(message.chat.id)
        for admin in admins:
            if admin.user.id == message.from_user.id:
                status = tr_db.find_tournament_by_chat_id(message.chat.id)
                if not status:
                    bot.send_message(message.chat.id, 'Никакой турнир сейчас не запущен.')
                else:
                    users = tr_db.get_tournament_users_by_chat_id(message.chat.id)
                    user_db.update_users_with_current_tournament(False, users)
                    tr_db.delete_tournament_by_chat_id(message.chat.id)
                    bot.send_message(message.chat.id, 'Текущий турнир удален.')
    else:
        bot.send_message(message.chat.id, 'Команда применима только в группе.')


@bot.message_handler(commands=['quit'])
def launch_tournament(message):
    threading.Timer(1.0, lambda: bot.delete_message(message.chat.id, message.message_id)).start()
    if message.chat.type in ['group', 'supergroup']:
        if tr_db.get_tournament_status_by_chat_id(
                message.chat.id) == 'register' and message.from_user.id in tr_db.get_tournament_users_by_chat_id(
            message.chat.id):
            tr_db.remove_user_from_tournament(message.chat.id, message.from_user.id)
            bot.send_message(message.chat.id, f'{message.from_user.first_name} покинул турнир.')
        else:
            bot.send_message(message.chat.id, 'Вы не состоите в турнире этой группы, или регистрация уже кончилась.')
    else:
        bot.send_message(message.chat.id, 'Команда применима только в группе.')


@bot.message_handler(commands=['members'])
def members_tournament(message):
    threading.Timer(1.0, lambda: bot.delete_message(message.chat.id, message.message_id)).start()
    if message.chat.type in ['group', 'supergroup']:
        users = tr_db.get_tournament_users_by_chat_id(message.chat.id)
        if not users:
            bot.send_message(message.chat.id, 'Турнир не запущен или никто пока не присоединился.')
        else:
            sepa = '\n'
            bot.send_message(message.chat.id,
                             f'В турнире участвуют: {f"{sepa}".join(str(bot.get_chat_member(message.chat.id, x).user.first_name) for x in users)}.')
    else:
        bot.send_message(message.chat.id, 'Команда применима только в группе.')


@bot.message_handler(commands=['add'])
def delete_tournament(message):
    threading.Timer(1.0, lambda: bot.delete_message(message.chat.id, message.message_id)).start()
    if message.chat.type in ['group', 'supergroup']:
        admins = bot.get_chat_administrators(message.chat.id)
        for admin in admins:
            if admin.user.id == message.from_user.id:
                if ' ' in message.text:
                    tournament_id = tr_db.find_tournament_by_chat_id(message.chat.id)
                    users = message.text.split()[1:]
                    in_user = []
                    out_user = []
                    for i in users:
                        try:
                            if user_db.get_user_document_by_username(i[1:]) and not \
                                    user_db.get_user_document_by_userid(
                                        ['current_chat']) and tr_db.get_tournament_status_by_chat_id(
                                message.chat.id) == 'register':
                                in_user.append(i)

                                id = user_db.get_user_document_by_username(i[1:])['userId']
                                tr_db.add_user_to_tournament(tournament_id, id)
                            else:
                                out_user.append(i)
                        except:
                            out_user.append(i)
                    bot.send_message(message.chat.id, f'Добавлены:\n{", ".join(in_user)}\n\n'
                                                      f'Не удалось добавить: {", ".join(out_user)}')
                else:
                    bot.send_message(message.chat.id,
                                     'Введите через пробел игроков, которых вы хотите добавить в турнир.')
    else:
        bot.send_message(message.chat.id, 'Команда применима только в группе.')


@bot.callback_query_handler(func=lambda call: call.data.startswith('cnf_'))
def callback_query(call):
    ans = call.data.split('_')[1]
    id = int(call.data.split('_')[2])
    if id == call.from_user.id:
        if ans == 'y':
            with open(f'bot/cache/{id}.txt') as f:
                data = f.readline().strip()
            chat_id_1 = int(data.split('^')[0])
            game_id = int(data.split('^')[1])
            score = data.split('^')[2]
            games_left = int(data.split('^')[3])
            first_player = int(data.split('^')[4])
            second_player = int(data.split('^')[5])

            if tr_db.insert_game_result(chat_id_1, game_id, score, games_left, first_player,
                                        second_player):
                bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id,
                                      text='Игра сыграна.\n\n'
                                           f'@{user_db.get_user_document_by_userid(first_player)["username"]} '
                                           f'{score} @{user_db.get_user_document_by_userid(second_player)["username"]}')
                os.remove(f'bot/cache/{id}.txt')
            else:
                bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text='Ошибка!')
        elif ans == 'n':
            bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id,
                                  text='Внесение результатов отменено.')


@bot.message_handler(commands=['set'])
def set_message(message):
    threading.Timer(1.0, lambda: bot.delete_message(message.chat.id, message.message_id)).start()
    if ' ' in message.text:
        if len(message.text.split()) != 3:
            bot.send_message(message.chat.id, 'Чтобы внести игру, введите ник оппонента и счет.')
        else:
            cmd, username, score = message.text.split()
            score = score.replace('-', ':')
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
                            games_left = game['games_left']
                            game_id = game['game_id']
                            with open(f'bot/cache/{first_player}.txt', 'w') as f:
                                f.write(
                                    f'{chat_id_1}^{game_id}^{score}^{games_left}^{first_player}^{second_player}')

                            bot.send_message(message.chat.id, 'Вы хотите внести игру?\n\n'
                                                              f'@{message.from_user.username} '
                                                              f'{score} {username}',
                                             reply_markup=mk.confirm_markup(first_player))
                        else:
                            bot.send_message(message.chat.id, 'Никакой турнир сейчас не запущен.')
                else:
                    tourne = tr_db.get_tournament_type_by_chat_id(chat_id_1)
                    if tourne == 'free':
                        if game['games_left'] > 0:
                            games_left = game['games_left']
                            game_id = game['game_id']
                            with open(f'bot/cache/{first_player}.txt', 'w') as f:
                                f.write(
                                    f'{chat_id_1}^{game_id}^{score}^{games_left}^{first_player}^{second_player}')

                            bot.send_message(message.chat.id, 'Вы хотите внести игру?\n\n'
                                                              f'@{message.from_user.username} '
                                                              f'{score} {username}',
                                             reply_markup=mk.confirm_markup(first_player))
                        else:
                            bot.send_message(message.chat.id, 'Вы уже внесли две игры с этим пользователем.')
                    elif tourne == 'fix':
                        game_date_str = game['date']
                        game_date = datetime.strptime(game_date_str, '%d/%m/%y')
                        today_date = datetime.now()

                        if game_date.date() == today_date.date():
                            games_left = game['games_left']
                            if games_left > 0:
                                game_id = game['game_id']
                                with open(f'bot/cache/{first_player}.txt', 'w') as f:
                                    f.write(
                                        f'{chat_id_1}^{game_id}^{score}^{games_left}^{first_player}^{second_player}')

                                bot.send_message(message.chat.id, 'Вы хотите внести игру?\n\n'
                                                                  f'@{message.from_user.username} '
                                                                  f'{score} {username}',
                                                 reply_markup=mk.confirm_markup(first_player))

                            else:
                                bot.send_message(message.chat.id, 'Вы уже внесли две игры с этим пользователем.')
                        else:
                            bot.send_message(message.chat.id, 'Сегодня вы играете с другим игроком.')

    else:
        bot.send_message(message.chat.id, 'ℹ️ Чтобы внести игру, введите сообщение в формате\n\n'
                                          '<code>/set [@ник соперника] [счет (свой:соперника)]</code>',
                         parse_mode='html')


@bot.message_handler(commands=['admin_set'])
def set_message(message):
    threading.Timer(1.0, lambda: bot.delete_message(message.chat.id, message.message_id)).start()
    if ' ' in message.text:
        if len(message.text.split()) != 4:
            bot.send_message(message.chat.id, 'Чтобы внести игру, введите ники оппонентов и счет.')
        else:
            cmd, username1, username2, score = message.text.split()
            first_player = user_db.get_user_document_by_username(username1[1:])['userId']
            second_player = user_db.get_user_document_by_username(username2[1:])['userId']
            chat_id_1 = user_db.get_user_document_by_username(username1[1:])['current_chat']
            chat_id_2 = user_db.get_user_document_by_username(username2[1:])['current_chat']

            if chat_id_1 != chat_id_2:
                bot.send_message(message.chat.id,
                                 'Игроки участвуют в разных турнирах, или '
                                 'один из игроков не присоединился к соревнованиям.')
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
                            games_left = game['games_left']
                            game_id = game['game_id']
                            with open(f'bot/cache/{message.from_user.id}.txt', 'w') as f:
                                f.write(
                                    f'{chat_id_1}^{game_id}^{score}^{games_left}^{first_player}^{second_player}')

                            bot.send_message(message.chat.id, 'Вы хотите внести игру?\n\n'
                                                              f'{username1} '
                                                              f'{score} {username2}',
                                             reply_markup=mk.confirm_markup(message.from_user.id))
                        else:
                            bot.send_message(message.chat.id, 'Никакой турнир сейчас не запущен.')
                else:
                    tourne = tr_db.get_tournament_type_by_chat_id(chat_id_1)
                    if tourne == 'free':
                        if game['games_left'] > 0:
                            games_left = game['games_left']
                            game_id = game['game_id']
                            with open(f'bot/cache/{message.from_user.id}.txt', 'w') as f:
                                f.write(
                                    f'{chat_id_1}^{game_id}^{score}^{games_left}^{first_player}^{second_player}')

                            bot.send_message(message.chat.id, 'Вы хотите внести игру?\n\n'
                                                              f'{username1} '
                                                              f'{score} {username2}',
                                             reply_markup=mk.confirm_markup(message.from_user.id))
                        else:
                            bot.send_message(message.chat.id, 'Вы уже внесли две игры с этим пользователями.')
                    elif tourne == 'fix':
                        game_date_str = game['date']
                        game_date = datetime.strptime(game_date_str, '%d/%m/%y')
                        today_date = datetime.now()

                        if game_date.date() == today_date.date():
                            games_left = game['games_left']
                            if games_left > 0:
                                game_id = game['game_id']
                                with open(f'bot/cache/{message.from_user.id}.txt', 'w') as f:
                                    f.write(
                                        f'{chat_id_1}^{game_id}^{score}^{games_left}^{first_player}^{second_player}')

                                bot.send_message(message.chat.id, 'Вы хотите внести игру?\n\n'
                                                                  f'{username1} '
                                                                  f'{score} {username2}',
                                                 reply_markup=mk.confirm_markup(message.from_user.id))

                            else:
                                bot.send_message(message.chat.id, 'Вы уже внесли две игры с этими пользователями.')
                        else:
                            bot.send_message(message.chat.id, 'Сегодня вы играете с другим игроком.')

    else:
        bot.send_message(message.chat.id, 'ℹ️ Чтобы внести игру, введите сообщение в формате\n\n'
                                          '<code>/set [@ник соперника1] '
                                          '[@ник соперника2] [счет (соперник1:соперник2)]</code>',
                         parse_mode='html')


@bot.message_handler(commands=['table'])
def table_tournament(message):
    threading.Timer(1.0, lambda: bot.delete_message(message.chat.id, message.message_id)).start()
    if message.chat.type in ['group', 'supergroup']:
        if tr_db.get_tournament_status_by_chat_id(message.chat.id) == 'going':
            games = tr_db.get_tournament_games_by_chat_id(message.chat.id)
            users = tr_db.get_tournament_users_by_chat_id(message.chat.id)
            name = tr_db.get_tournament_name_by_chat_id(message.chat.id)

            raw_dict = helper.calculate_scores(games, users)
            new_dict = {}
            for key in raw_dict.keys():
                new_dict[bot.get_chat_member(message.chat.id, key).user.first_name] = raw_dict[key]
            tournament_id = tr_db.find_tournament_by_chat_id(message.chat.id)

            helper.save_tournament_results(tournament_id, name, new_dict)
            curr = str(datetime.now().strftime("%d-%m-%y_%H-%M"))
            bot.send_document(message.chat.id,
                              document=open(f'bot/utilities/data/res_{tournament_id}.png', 'rb'),
                              caption='Текущие результаты ☝\n\nВ - Н - П',
                              visible_file_name=f'Результаты турнира {curr}.png')
            os.remove(f'bot/utilities/data/res_{tournament_id}.png')
        else:
            bot.send_message(message.chat.id, 'Никакой турнир сейчас не запущен.')
    else:
        bot.send_message(message.chat.id, 'Команда применима только в группе.')


@bot.message_handler(commands=['games'])
def played_tournament(message):
    threading.Timer(1.0, lambda: bot.delete_message(message.chat.id, message.message_id)).start()
    if message.chat.type in ['group', 'supergroup']:
        if tr_db.get_tournament_status_by_chat_id(message.chat.id) == 'going':
            name = tr_db.get_tournament_name_by_chat_id(message.chat.id)
            tournament_id = tr_db.find_tournament_by_chat_id(message.chat.id)

            data = tr_db.get_played_games_by_chat_id(message.chat.id)
            for i in data:
                i['first_player'] = bot.get_chat_member(message.chat.id, i['first_player']).user.first_name
                i['second_player'] = bot.get_chat_member(message.chat.id, i['second_player']).user.first_name

            helper.save_match_table(data, tournament_id, name)
            curr = str(datetime.now().strftime("%d-%m-%y_%H-%M"))
            bot.send_document(message.chat.id,
                              document=open(f'bot/utilities/data/played_{tournament_id}.png', 'rb'),
                              caption='Сыгранные игры ☝',
                              visible_file_name=f'Результаты игр {curr}.png')
            os.remove(f'bot/utilities/data/played_{tournament_id}.png')
    else:
        bot.send_message(message.chat.id, 'Команда применима только в группе.')


@bot.message_handler(commands=['finish'])
def table_tournament(message):
    threading.Timer(1.0, lambda: bot.delete_message(message.chat.id, message.message_id)).start()
    if message.chat.type in ['group', 'supergroup']:
        if tr_db.get_tournament_status_by_chat_id(message.chat.id) == 'going':
            users = tr_db.get_tournament_users_by_chat_id(message.chat.id)
            games = tr_db.get_tournament_games_by_chat_id(message.chat.id)
            name = tr_db.get_tournament_name_by_chat_id(message.chat.id)
            tournament_id = tr_db.find_tournament_by_chat_id(message.chat.id)

            tr_db.update_tournament_status_by_chat(message.chat.id, 'end')
            user_db.update_users_with_current_tournament(False, users)

            bot.send_message(message.chat.id, 'Подводим итоги ⌛')

            raw_dict = helper.calculate_scores(games, users)
            for key, value in raw_dict.items():
                raw_dict[key]['title'] = name
                user_db.insert_tournament_to_user(key, value)

            new_dict = {}
            for key in raw_dict.keys():
                new_dict[bot.get_chat_member(message.chat.id, key).user.first_name] = raw_dict[key]

            helper.save_tournament_results(tournament_id, name, new_dict)
            top_players = list(new_dict.items())[:3]
            top_players_string = ""
            medal_emojis = ["🥇", "🥈", "🥉"]
            for i, (name, score) in enumerate(top_players):
                if i < len(medal_emojis):
                    top_players_string += f"{medal_emojis[i]} {name} - {score['score']} очков\n\n"

            bot.delete_message(message.chat.id, message.message_id + 1)

            bot.send_document(message.chat.id, open(f'bot/utilities/data/res_{tournament_id}.png', 'rb'),
                              visible_file_name='Результаты.png')
            bot.send_photo(message.chat.id,
                           photo=open(f'bot/utilities/data/finish.jpg', 'rb'),
                           caption='Турнир завершен!\n\n'
                                   f'{top_players_string}')

            tr_db.delete_tournament_by_chat_id(message.chat.id)
            os.remove(f'bot/utilities/data/res_{tournament_id}.png')
        else:
            bot.send_message(message.chat.id, 'Никакой турнир сейчас не запущен.')
    else:
        bot.send_message(message.chat.id, 'Команда применима только в группе.')


# Обработчик команд встроенного бота
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
