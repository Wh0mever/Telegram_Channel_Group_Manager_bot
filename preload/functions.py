from preload.databases import *
from preload.config import *
from preload.states import *
from preload.keyboard import *
from preload.logger_config import setup_logger

from aiogram import Bot
from aiogram.types import FSInputFile
from secrets import token_hex
import json
import logging
import sys

bot = Bot(TOKEN)
logger = setup_logger()

# Настройка логирования
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Создаем форматтер для логов
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(name)s - %(message)s')

# Хендлер для записи в файл
file_handler = logging.FileHandler("logs/functions.log", mode="w", encoding='utf-8')
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

# Хендлер для вывода в консоль
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)

#id integer, info text, message text, turn integer
async def generate_channels():
    select = cur3.execute('select * from data').fetchall()
    kbs = []
    for row in select:
        info = json.loads(row[1])
        text = f'✔ {info["title"]}' if row[3] == 1 else f'✖ {info["title"]}'
        kbs.append([InlineKeyboardButton(text = text, callback_data=f'select_channel_{row[0]}')])
    kbs.append([InlineKeyboardButton(text = '➕ Добавить канал', callback_data='add_channel')])
    kbs = InlineKeyboardMarkup(inline_keyboard=kbs)
    return kbs


async def generate_one_channel(id):
    select = cur3.execute('select * from data where id == ?', (id, )).fetchone()
    info = json.loads(select[1])
    kbs = [[InlineKeyboardButton(text = '🖋 Изменить сообщение', callback_data=f'edit_message_{id}')],
           [InlineKeyboardButton(text = '👁 Показать сообщение', callback_data=f'show_message_{id}')],
           [InlineKeyboardButton(text = 'Включить автоприём' if select[3] == 0 else 'Выключить автоприём', callback_data=f'turn_channel_{id}')],
           [InlineKeyboardButton(text = '🗑 Удалить канал', callback_data=f'delete_channel_{id}')],
           [InlineKeyboardButton(text = '← Назад', callback_data='back_to_channels')]]
    kbs = InlineKeyboardMarkup(inline_keyboard=kbs)
    colvo = len(cur.execute('select * from data where channel == ?', (id, )).fetchall())
    text = f'Управление каналом <a href="{info["link"]}">{info["title"]}</a>' if info['link'] else f'Управление каналом <b>{info["title"]}</b>'
    text += '\n\nАвтоприём: <b>включен</b>' if select[3] == 1 else '\n\nАвтоприём: <b>выключен</b>'
    text += f'\nЛюдей в базе: <b>{colvo}чел.</b>'
    return kbs, text



async def check_admin(message):
    """Проверяет права администратора бота в канале/чате"""
    logger.info(f"Начало проверки админских прав для сообщения: {message.message_id}")
    
    async def verify_admin_status(chat_id):
        """Проверяет статус администратора и получает информацию о канале"""
        try:
            bot_info = await bot.get_me()
            member = await bot.get_chat_member(chat_id, bot_info.id)
            chat = await bot.get_chat(chat_id)
            
            required_rights = {
                'can_invite_users': True,
                'can_manage_chat': True,
            }
            
            # Проверяем необходимые права
            if member.status != 'administrator':
                logger.warning(f"Бот не является администратором в чате {chat_id}")
                return False
            
            # Проверяем наличие необходимых прав
            for right, required in required_rights.items():
                if not getattr(member, right, False):
                    logger.warning(f"У бота отсутствует право {right} в чате {chat_id}")
                    return False
            
            channel_info = {
                'id': chat.id,
                'title': chat.title,
                'link': chat.invite_link
            }
            logger.info(f"Успешно получена информация о канале: {channel_info}")
            return channel_info
            
        except Exception as err:
            logger.error(f"Ошибка при проверке прав администратора: {err}")
            return False
    
    if message.forward_from_chat:
        logger.info(f"Проверка форварда из чата {message.forward_from_chat.id}")
        return await verify_admin_status(message.forward_from_chat.id)
    else:
        try:
            chat_id = int(message.text)
            chat_id = chat_id * -1 if chat_id > 0 else chat_id
            logger.info(f"Проверка чата по ID: {chat_id}")
            return await verify_admin_status(chat_id)
        except ValueError:
            logger.error("Некорректный формат ID канала")
            return None
        except Exception as err:
            logger.error(f"Ошибка при обработке ID чата: {err}")
            return None


async def generate_spam_channels(data):
    select_channels = data['select_channels']
    kbs = []
    chans = cur3.execute('select * from data').fetchall()
    for row in chans:
        info = json.loads(row[1])
        text = f'{info["title"]}' if row[0] not in select_channels else f'✔️ {info["title"]}'
        kbs.append([InlineKeyboardButton(text = text, callback_data=f'select_spamchan_{row[0]}')])
    kbs.append([InlineKeyboardButton(text = 'Начать рассылку', callback_data='start_spam')])
    kbs.append([InlineKeyboardButton(text = '← Назад', callback_data='back_to_start')])
    kbs = InlineKeyboardMarkup(inline_keyboard=kbs)
    return kbs

async def get_stat_func():
    all_users = len(cur.execute('select * from data').fetchall())
    life_users = len(cur.execute('select * from data where life == ?', (1, )).fetchall())
    block_users = all_users-life_users
    text = f'<b>📈 Статистика бота</b>\n\nВсего пользователей: <b>{all_users} чел.</b>\nИз них:\n Живые: <b>{life_users} чел.</b>\n Заблокировали бота: <b>{block_users} чел.</b>'
    channels = cur3.execute('select * from data').fetchall()
    if len(channels) != 0:
        text += '\n\n\n<b>Статистика по каналам</b>'
        for row in channels:
            info = json.loads(row[1])
            all_users = len(cur.execute('select * from data where channel == ?', (row[0], )).fetchall())
            life_users = len(cur.execute('select * from data where life == ? and channel == ?', (1, row[0])).fetchall())
            block_users = all_users - life_users
            text += f'\n\n<b>{info["title"]}</b>\nВсего пользователей: <b>{all_users} чел.</b>\nИз них:\n Живые: <b>{life_users} чел.</b>\n Заблокировали бота: <b>{block_users} чел.</b>'
    return text
#id integer, info text
async def generate_admins():
    select = cur2.execute('select * from data').fetchall()
    kbs = []
    for row in select:
        info = json.loads(row[1])
        text = f'ID: {row[0]}' if info == None else f'{info["first_name"]}'
        kbs.append([InlineKeyboardButton(text = text, callback_data=f'select_admin_{row[0]}')])
    kbs.append([InlineKeyboardButton(text = '➕ Добавить админа', callback_data='add_admin')])
    kbs = InlineKeyboardMarkup(inline_keyboard=kbs)
    return kbs