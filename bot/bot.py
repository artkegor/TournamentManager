import random
import threading
import time

from telebot import types
from config import bot
import bot.keyboards.inline as mk
import bot.database.user_database as user_db
import bot.database.tournament_database as tr_db
import bot.utilities.tournament_helper as helper

bot.set_my_commands(commands=[types.BotCommand('/start', 'Перезапустить бота'),
                              types.BotCommand('/help', 'Помощь'),
                              types.BotCommand('/launch', 'Запустить турнир')])


@bot.message_handler(commands=['start', 'help'])
def start_message(message):
    if message.chat.type in ['group', 'supergroup']:
        threading.Timer(1.0, lambda: bot.delete_message(message.chat.id, message.message_id)).start()
        bot.send_message(message.chat.id, f'Привет, {message.from_user.first_name}! 👋\n\n'
                                          f'Чтобы посмотреть статистику текущего турнира введи /table 🏆\n\n'
                                          f'Если хочешь ввести результат игры то отметь меня, '
                                          f'или напиши в личные сообщения. 👀', reply_markup=mk.group_start_markup())
    else:
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
    bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id,
                          text='Выберите тип турнира:', reply_markup=mk.tournament_type())


@bot.callback_query_handler(func=lambda call: call.data.startswith('newtour_'))
def callback_query(call):
    if call.message.chat.type in ['group', 'supergroup']:
        admins = bot.get_chat_administrators(call.message.chat.id)
        for admin in admins:
            if admin.user.id == call.from_user.id:
                tournament_type = call.data.split('_')[1]
                tournament_id = str(random.randint(100000, 999999))

                tr_db.insert_tournament(tournament_id, call.message.chat.id, bot.get_chat(call.message.chat.id).title,
                                        'register', tournament_type)

                bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id,
                                      text='Турнир создан.\n'
                                           'До конца регистрации 30 секунд.',
                                      reply_markup=mk.new_tournament(tournament_id))

                def starter_func():
                    for i in range(300):
                        time.sleep(3)
                        if tr_db.get_tournament_status_by_id(tournament_id) == 'going':
                            break
                        else:
                            users = tr_db.get_tournament_users_by_id(tournament_id)
                            try:
                                bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id,
                                                      text='Турнир создан.\n'
                                                           'До конца регистрации 30 секунд.\n\n'
                                                           f'Присоединились: {", ".join(str(bot.get_chat_member(call.message.chat.id, x).user.first_name) for x in users)}',
                                                      reply_markup=mk.new_tournament(tournament_id))
                            except:
                                pass

                    users = tr_db.get_tournament_users_by_id(tournament_id)
                    tr_db.update_tournament_status(tournament_id, 'going')
                    if tournament_type == 'free':
                        bot.delete_message(call.message.chat.id, call.message.message_id)
                        bot.send_message(call.message.chat.id, 'Регистрация окончена!\n\n'
                                                               f'🫂 На турнир зарегистрированы: {", ".join(str(bot.get_chat_member(call.message.chat.id, x).user.first_name) for x in users)}')

                    else:
                        bot.delete_message(call.message.chat.id, call.message.message_id)
                        bot.send_message(call.message.chat.id, 'Регистрация окончена!\n'
                                                               'Формирую расписание игр...\n\n'
                                                               f'🫂 На турнир зарегистрированы: {", ".join(str(bot.get_chat_member(call.message.chat.id, x).user.first_name) for x in users)}')

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
                                          caption='Расписание игр ☝')

                threading.Thread(target=starter_func()).start()
    else:
        pass


@bot.message_handler(commands=['launch'])
def launch_tournament(message):
    threading.Timer(1.0, lambda: bot.delete_message(message.chat.id, message.message_id)).start()
    if message.chat.type in ['group', 'supergroup']:
        tournament_id = tr_db.find_tournament_by_chat_id(message.chat.id)
        if tournament_id:
            tr_db.update_tournament_status(tournament_id, 'going')
        else:
            bot.send_message(message.chat.id, 'Никакой турнир сейчас не запущен.')


@bot.message_handler(commands=['delete'])
def launch_tournament(message):
    tr_db.delete_tournament_by_chat_id(message.chat.id)
    bot.send_message(message.chat.id, 'удалено')
