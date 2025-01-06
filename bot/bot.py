from config import bot
from telebot import types

import bot.handlers.inlines as inlines
import bot.handlers.messages as messages
import bot.handlers.callbacks as callbacks

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

inlines.register_inline_handlers(bot)
messages.register_message_handlers(bot)
callbacks.register_callback_handlers(bot)
