from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton

admin_kbs = [[KeyboardButton(text = '🗄 Каналы')],
             [KeyboardButton(text = '💬 Рассылка'), KeyboardButton(text = '📈 Статистика')]]
admin_kbs = ReplyKeyboardMarkup(resize_keyboard=True, keyboard=admin_kbs)

manag_kbs = [[KeyboardButton(text = '🗄 Каналы')],
             [KeyboardButton(text = '💬 Рассылка'), KeyboardButton(text = '📈 Статистика')]]
manag_kbs = ReplyKeyboardMarkup(resize_keyboard=True, keyboard=manag_kbs)