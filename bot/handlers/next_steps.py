import bot.keyboards.inline as mk


# Функции с получением текста от пользователя
def get_name(bot, message):
    name = message.text
    with open(f'bot/cache/{message.chat.id}.txt', 'w') as f:
        f.write(name)
    bot.send_message(chat_id=message.chat.id,
                     text='Выберите тип турнира:', reply_markup=mk.tournament_type())
