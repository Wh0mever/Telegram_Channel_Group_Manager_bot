import asyncio
import json
import logging
import sys

from aiogram.types import Message, CallbackQuery, ChatJoinRequest
from aiogram.fsm.context import FSMContext
from aiogram.types import FSInputFile
from aiogram.filters import Command
from aiogram import Router, F, Bot

from secrets import token_hex

from preload import functions
from preload.databases import *
from preload.config import *
from preload.states import *
from preload.keyboard import *


router = Router()
bot = Bot(TOKEN)

# Настройка логирования
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Создаем форматтер для логов
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(name)s - %(message)s')

# Хендлер для записи в файл
file_handler = logging.FileHandler("logs/handlers.log", mode="w", encoding='utf-8')
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

# Хендлер для вывода в консоль
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)


@router.message(Command(commands=['start']))
async def start_func(message: Message, state: FSMContext):
    if message.from_user.id in admin_ids:
        await message.answer(f'👋 <b>Приветствую, {message.from_user.first_name}!</b>\n\nДобро пожаловать в админ панель бота приёма заявок.',
                             parse_mode='HTML', reply_markup=admin_kbs)
    else:
        if len(cur2.execute('select * from data where id == ?', (message.from_user.id, )).fetchall()) != 0:
            info = {
                'id': message.from_user.id,
                'first_name': message.from_user.first_name,
                'username': message.from_user.username
            }
            cur2.execute('update data set info == ? where id == ?', (json.dumps(info), message.from_user.id))
            base2.commit()
            await message.answer(
                f'👋 <b>Приветствую, {message.from_user.first_name}!</b>\n\nДобро пожаловать в админ панель бота приёма заявок.',
                parse_mode='HTML', reply_markup=manag_kbs)
        pass

@router.message(F.text)
async def text_hand_func(message: Message, state: FSMContext):
    if message.from_user.id not in admin_ids and len(cur2.execute('select * from data where id == ?', (message.from_user.id, )).fetchall()) == 0:
        if len(cur.execute('select * from data where id == ?', (message.from_user.id, )).fetchall()) == 0:
            info = {
                'id': message.from_user.id,
                'first_name': message.from_user.first_name,
                'last_name': message.from_user.last_name,
                'username': message.from_user.username,
                'language': message.from_user.language_code
            }
            cur.execute('insert into data values (?, ?, ?, ?)', (message.from_user.id, 0, json.dumps(info), 1))
            base.commit()
        await message.answer('''Спасибо, вы подтвердили, что вы не робот. 
Ваша заявка на вступление будет одобрена модераторами.''')


@router.chat_join_request()
async def start1(update: ChatJoinRequest):
    logger.info(f"Получена заявка на вступление от пользователя {update.from_user.id} в чат {update.chat.id}")
    try:
        if len(cur3.execute('select * from data where id == ?', (update.chat.id, )).fetchall()) != 0:
            select = cur3.execute('select * from data where id == ?', (update.chat.id, )).fetchone()
            post = select[2]
            turn = select[3]
            if turn == 1:
                info = {
                    'id': update.from_user.id,
                    'first_name': update.from_user.first_name,
                    'last_name': update.from_user.last_name,
                    'username': update.from_user.username,
                    'language': update.from_user.language_code
                }
                try:
                    if len(cur.execute('select * from data where id == ?', (update.from_user.id, )).fetchall()) == 0:
                        cur.execute('insert into data values (?, ?, ?, ?)', (update.from_user.id, update.chat.id, json.dumps(info), 1))
                        base.commit()
                        logger.info(f"Добавлен новый пользователь {update.from_user.id} для канала {update.chat.id}")
                    else:
                        cur.execute('update data set channel == ? where id == ?', (update.chat.id, update.from_user.id))
                        base.commit()
                        logger.info(f"Обновлен канал для пользователя {update.from_user.id}")

                    keys = [[KeyboardButton(text='🤷‍♂️ Я человек')]]
                    keys = ReplyKeyboardMarkup(resize_keyboard=True, keyboard=keys)
                    await bot.send_message(update.from_user.id, f'''{update.from_user.first_name}, спасибо за подписку на канал.
Я анти-спам бот.
Для подтверждения того, что вы живой человек, нажмите кнопку
<b>«Я человек»</b>
или напишите мне.''', parse_mode='HTML', reply_markup=keys)

                    await asyncio.sleep(60)

                    try:
                        if post != 'hi!':
                            post = json.loads(post)
                            kbs = post['kbs']
                            message_kbs = []
                            for row in kbs:
                                k = []
                                for row2 in row:
                                    k.append(InlineKeyboardButton(text=row2['text'], url=row2['url']))
                                message_kbs.append(k)
                            kbs = InlineKeyboardMarkup(inline_keyboard=message_kbs)
                            await bot.copy_message(update.from_user.id, post['chat_id'], post['message_id'], reply_markup=kbs,
                                               parse_mode='HTML')
                            logger.info(f"Отправлено приветственное сообщение пользователю {update.from_user.id}")
                        else:
                            await bot.send_message(update.from_user.id, post)
                            logger.info(f"Отправлено стандартное приветствие пользователю {update.from_user.id}")

                        await update.approve()
                        logger.info(f"Заявка пользователя {update.from_user.id} одобрена")
                    except Exception as e:
                        logger.error(f"Ошибка при отправке сообщения пользователю {update.from_user.id}: {e}")
                except Exception as e:
                    logger.error(f"Ошибка при обработке данных пользователя {update.from_user.id}: {e}")
    except Exception as e:
        logger.error(f"Критическая ошибка при обработке заявки: {e}")
