from telebot import types


def start_markup():
    markup = types.InlineKeyboardMarkup()

    markup.add(types.InlineKeyboardButton(text='Мои турниры', callback_data='user'))
    markup.add(types.InlineKeyboardButton(text='Добавить бота в группу',
                                          url='https://t.me/TournamentManagebot?startgroup=botstart'))

    return markup


def back_markup():
    markup = types.InlineKeyboardMarkup()

    markup.add(types.InlineKeyboardButton(text='Назад ↩️', callback_data='back'))

    return markup


def my_back_markup():
    markup = types.InlineKeyboardMarkup()

    markup.add(types.InlineKeyboardButton(text='Назад ↩️', callback_data='user'))

    return markup


def my_markup(results):
    markup = types.InlineKeyboardMarkup()

    for i, k in enumerate(results, start=1):
        markup.add(types.InlineKeyboardButton(text=f'{i}. {k["title"]}', callback_data=f'my_{i - 1}'))

    return markup


def group_start_markup():
    markup = types.InlineKeyboardMarkup()

    markup.add(types.InlineKeyboardButton(text='Создать новый турнир ✍', callback_data='tourtype'))

    return markup


def tournament_type():
    markup = types.InlineKeyboardMarkup()

    markup.add(types.InlineKeyboardButton(text='Свободное расписание 🟢', callback_data=f'nw_free'))
    markup.add(types.InlineKeyboardButton(text='Фиксированное расписание 🔵', callback_data=f'nw_fix'))

    return markup


def new_tournament(game_id):
    markup = types.InlineKeyboardMarkup()

    markup.add(types.InlineKeyboardButton(text='Присоединиться к турниру 🏆',
                                          url=f'https://t.me/tournamentmanagebot?start={game_id}'))

    return markup


def confirm_markup(id):
    markup = types.InlineKeyboardMarkup()

    markup.add(types.InlineKeyboardButton(text='Подтвердить ✅', callback_data=f'cnf_y_{id}'))
    markup.add(types.InlineKeyboardButton(text='Отменить ❌', callback_data=f'cnf_n_{id}'))

    return markup
