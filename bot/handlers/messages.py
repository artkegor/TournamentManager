import os
import threading

from telebot import TeleBot
from datetime import datetime
import bot.keyboards.inline as mk
import bot.utils.tournament_helper as helper
import bot.database.user_database as user_db
import bot.database.tournament_database as tr_db


# Обработчик всех команд
def register_message_handlers(bot: TeleBot):
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
                    if not user_db.get_user_document_by_username(message.from_user.username):
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

                            chat_id = tr_db.get_tournament_chat_id_by_id(str(args))
                            bot.send_message(chat_id, f'@{message.from_user.username} присоединился к турниру!')
                    else:
                        bot.send_message(message.chat.id, 'Вы уже участвуете в другом турнире.')
                else:
                    if not user_db.get_user_document_by_userid(message.chat.id):
                        user_db.insert_user(message.chat.id, message.from_user.username)
                    bot.send_message(message.chat.id, text='Добрый день!\n'
                                                           'Готовы к новым победам? 🏆', reply_markup=mk.start_markup())
            else:
                bot.send_message(message.chat.id, 'Чтобы использовать бота установите себе юзернейм.')

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
                bot.send_message(message.chat.id,
                                 'Вы не состоите в турнире этой группы, или регистрация уже кончилась.')
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
                                 f'В турнире участвуют:\n{f"{sepa}".join(str(bot.get_chat_member(message.chat.id, x).user.first_name) for x in users)}.')
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
        if message.chat.type in ['group', 'supergroup']:
            admins = bot.get_chat_administrators(message.chat.id)
            for admin in admins:
                if admin.user.id == message.from_user.id:
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
                                            game = tr_db.find_game_by_users_and_chat(first_player, second_player,
                                                                                     chat_id_1)
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
                                            bot.send_message(message.chat.id,
                                                             'Вы уже внесли две игры с этим пользователями.')
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
                                                bot.send_message(message.chat.id,
                                                                 'Вы уже внесли две игры с этими пользователями.')
                                        else:
                                            bot.send_message(message.chat.id, 'Сегодня вы играете с другим игроком.')

                    else:
                        bot.send_message(message.chat.id, 'ℹ️ Чтобы внести игру, введите сообщение в формате\n\n'
                                                          '<code>/set [@ник соперника1] '
                                                          '[@ник соперника2] [счет (соперник1:соперник2)]</code>',
                                         parse_mode='html')
        else:
            bot.send_message(message.chat.id, 'Команда применима только в группе.')

    @bot.message_handler(commands=['edit'])
    def set_message(message):
        threading.Timer(1.0, lambda: bot.delete_message(message.chat.id, message.message_id)).start()
        if message.chat.type in ['group', 'supergroup']:
            admins = bot.get_chat_administrators(message.chat.id)
            for admin in admins:
                if admin.user.id == message.from_user.id:
                    if ' ' in message.text:
                        if len(message.text.split()) != 3:
                            bot.send_message(message.chat.id, 'Введите номер игры и новый счет.')
                        else:
                            cmd, number, score = message.text.split()
                            if tr_db.update_game_score(message.chat.id, number, score):
                                bot.send_message(message.chat.id, 'Результат игры обновлен')
                            else:
                                bot.send_message(message.chat.id, 'Произошла ошибка.')
                    else:
                        bot.send_message(message.chat.id, 'ℹ️ Чтобы изменить счет игры, введите сообщение в формате\n\n'
                                                          '<code>/edit [номер игры] [новый счет]</code>\n\n'
                                                          'Найти номер игры можно в /games.', parse_mode='html')
        else:
            bot.send_message(message.chat.id, 'Команда применима только в группе.')

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
                                  document=open(f'bot/utils/data/res_{tournament_id}.png', 'rb'),
                                  caption='Текущие результаты ☝\n\nВ - Н - П',
                                  visible_file_name=f'Результаты турнира {curr}.png')
                os.remove(f'bot/utils/data/res_{tournament_id}.png')
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
                                  document=open(f'bot/utils/data/played_{tournament_id}.png', 'rb'),
                                  caption='Сыгранные игры ☝',
                                  visible_file_name=f'Результаты игр {curr}.png')
                os.remove(f'bot/utils/data/played_{tournament_id}.png')
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

                bot.send_document(message.chat.id, open(f'bot/utils/data/res_{tournament_id}.png', 'rb'),
                                  visible_file_name='Результаты.png')
                bot.send_photo(message.chat.id,
                               photo=open(f'bot/utils/data/finish.jpg', 'rb'),
                               caption='Турнир завершен!\n\n'
                                       f'{top_players_string}')

                tr_db.delete_tournament_by_chat_id(message.chat.id)
                os.remove(f'bot/utils/data/res_{tournament_id}.png')
            else:
                bot.send_message(message.chat.id, 'Никакой турнир сейчас не запущен.')
        else:
            bot.send_message(message.chat.id, 'Команда применима только в группе.')
