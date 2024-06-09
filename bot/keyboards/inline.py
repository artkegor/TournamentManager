from telebot import types


def start_markup():
    markup = types.InlineKeyboardMarkup()

    markup.add(types.InlineKeyboardButton(text='Мои турниры', callback_data='user'))
    markup.add(types.InlineKeyboardButton(text='Добавить бота в группу',
                                          url='https://t.me/TournamentManagebot?startgroup=botstart'))

    return markup


def group_start_markup():
    markup = types.InlineKeyboardMarkup()

    markup.add(types.InlineKeyboardButton(text='Создать новый турнир ✍', callback_data='tourtype'))

    return markup


def tournament_type():
    markup = types.InlineKeyboardMarkup()

    markup.add(types.InlineKeyboardButton(text='Свободное расписание 🟢', callback_data='newtour_free'))
    markup.add(types.InlineKeyboardButton(text='Фиксированное расписание 🔵', callback_data='newtour_fix'))

    return markup


def new_tournament(game_id):
    markup = types.InlineKeyboardMarkup()

    markup.add(types.InlineKeyboardButton(text='Присоединиться к турниру 🏆',
                                          url=f'https://t.me/tournamentmanagebot?start={game_id}'))

    return markup
