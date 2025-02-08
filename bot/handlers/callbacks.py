import os
import time
import random
import threading

from telebot import TeleBot
import bot.keyboards.inline as mk
import bot.handlers.next_steps as next_steps
import bot.utils.tournament_helper as helper
import bot.database.user_database as user_db
import bot.database.tournament_database as tr_db


# Огромный обработчик всех нажатий кнопок
def register_callback_handlers(bot: TeleBot):
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
                    bot.register_next_step_handler(call.message, lambda message: next_steps.get_name(bot, message))

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
                        bot.send_photo(call.message.chat.id, photo=open(f'bot/utils/data/start.jpg', 'rb'),
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
                                          document=open(f'bot/utils/data/{tournament_id}.png', 'rb'),
                                          visible_file_name='Расписание.png')
                        bot.send_photo(call.message.chat.id,
                                       photo=open(f'bot/utils/data/start.jpg', 'rb'),
                                       caption='Расписание ☝\n\n'
                                               'Турнир объявляется открытым!\n'
                                               f'❕Игры проводится по фиксированным датам.',
                                       )

                        bot.send_message(call.message.chat.id,
                                         'ℹ️ Чтобы внести результат игры, введите сообщение в формате\n\n'
                                         '<code>/set [@ник соперника] [счет (свой:соперника)]</code>',
                                         parse_mode='html')

                        os.remove(f'bot/utils/data/{tournament_id}.png')

                threading.Thread(target=starter_func(tournament_type, name)).start()

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
                    bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id,
                                          text='Ошибка!')
            elif ans == 'n':
                bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id,
                                      text='Внесение результатов отменено.')
