import asyncio
import json
import logging
import sys

from aiogram.types import Message, CallbackQuery
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
from preload.logger_config import setup_logger


router = Router()
bot = Bot(TOKEN)
logger = setup_logger()

# Настройка логирования
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


@router.callback_query(F.data == 'back_to_channels')
async def back_to_channels_func(callback: CallbackQuery, state: FSMContext):
    if len(cur2.execute('select * from data where id == ?', (callback.from_user.id,)).fetchall()) != 0 or callback.from_user.id in admin_ids:
        await state.clear()
        kbs = await functions.generate_channels()
        await callback.message.edit_text('Здесь ты можешь управлять подключёнными каналами', reply_markup=kbs)


@router.callback_query(F.data == 'add_channel')
async def add_channel_func(callback: CallbackQuery, state: FSMContext):
    if len(cur2.execute('select * from data where id == ?', (callback.from_user.id,)).fetchall()) != 0 or callback.from_user.id in admin_ids:
        await state.clear()
        kbs = [[InlineKeyboardButton(text = '← Назад', callback_data='back_to_channels')]]
        kbs = InlineKeyboardMarkup(inline_keyboard=kbs)
        await callback.message.edit_text(f'Добавь бота (<code>@{bot_username}</code>) в админы канала/чата и перешли мне сообщение оттуда или пришли его айди.',
                                         reply_markup=kbs, parse_mode='HTML')
        await state.set_state(aForm.channel_message)


@router.message(F.content_type.in_(any), aForm.channel_message)
async def channel_message_func(message: Message, state: FSMContext):
    await state.clear()
    if len(cur2.execute('select * from data where id == ?', (message.from_user.id,)).fetchall()) != 0 or message.from_user.id in admin_ids:
        logger.info(f"Попытка добавления канала пользователем {message.from_user.id}")
        result = await functions.check_admin(message)
        
        if result is None:
            await message.answer('Пожалуйста, перешлите сообщение из канала или отправьте корректный ID канала (например: -100...).')
            await state.set_state(aForm.channel_message)
            return
            
        if result is False:
            error_text = (
                "❌ Бот не может быть добавлен в канал.\n\n"
                "Для корректной работы бота необходимо:\n"
                "1️⃣ Добавить бота в администраторы канала\n"
                "2️⃣ Предоставить следующие права:\n"
                "   • Управление каналом\n"
                "   • Приглашение пользователей\n\n"
                "После настройки прав, попробуйте снова."
            )
            await message.answer(error_text, parse_mode='HTML')
            await state.set_state(aForm.channel_message)
            return
            
        if len(cur3.execute('select * from data where id == ?', (result['id'], )).fetchall()) == 0:
            try:
                cur3.execute('insert into data values (?, ?, ?, ?)', (result['id'], json.dumps(result), 'hi!', 0))
                base3.commit()
                logger.info(f"Канал {result['title']} успешно добавлен в базу")
                
                success_text = (
                    f'✅ Канал <b>"{result["title"]}"</b> успешно добавлен!\n\n'
                    f'ℹ️ Не забудьте:\n'
                    f'1️⃣ Настроить приветственное сообщение\n'
                    f'2️⃣ Включить автоприём заявок'
                )
                await message.answer(success_text, parse_mode='HTML')
                
                kbs = await functions.generate_channels()
                await bot.send_message(message.from_user.id, 'Здесь вы можете управлять подключёнными каналами:', reply_markup=kbs)
            except Exception as e:
                logger.error(f"Ошибка при добавлении канала в базу: {e}")
                await message.answer("❌ Произошла ошибка при добавлении канала. Пожалуйста, попробуйте позже.")
        else:
            logger.warning(f"Попытка добавить существующий канал {result['id']}")
            await message.answer('❌ Этот канал уже добавлен в базу!')
            await asyncio.sleep(0.3)
            await state.set_state(aForm.channel_message)


@router.callback_query(F.data.startswith('select_channel_'))
async def select_channel_func(callback: CallbackQuery, state: FSMContext):
    if len(cur2.execute('select * from data where id == ?', (callback.from_user.id,)).fetchall()) != 0 or callback.from_user.id in admin_ids:
        await state.clear()
        id = int(callback.data.split('_')[-1])
        kbs, text = await functions.generate_one_channel(id)
        await callback.message.edit_text(text, reply_markup=kbs, parse_mode='HTML', disable_web_page_preview=True)


@router.callback_query(F.data.startswith('show_message_'))
async def show_message_func(callback: CallbackQuery, state: FSMContext):
    if len(cur2.execute('select * from data where id == ?', (callback.from_user.id,)).fetchall()) != 0 or callback.from_user.id in admin_ids:
        await callback.answer()
        id = int(callback.data.split('_')[-1])
        select = cur3.execute('select * from data where id == ?', (id,)).fetchone()
        if select[2] == 'hi!':
            kbs = [[InlineKeyboardButton(text = '✖️ Скрыть', callback_data='hide_message')]]
            kbs = InlineKeyboardMarkup(inline_keyboard=kbs)
            await callback.message.answer('hi!', reply_markup=kbs)
        else:
            post = json.loads(select[2])
            kbs = post['kbs']
            message_kbs = []
            for row in kbs:
                k = []
                for row2 in row:
                    k.append(InlineKeyboardButton(text = row2['text'], url = row2['url']))
                message_kbs.append(k)
            message_kbs.append([InlineKeyboardButton(text = '✖️ Скрыть', callback_data='hide_message')])
            kbs = InlineKeyboardMarkup(inline_keyboard=message_kbs)
            await bot.copy_message(callback.from_user.id, post['chat_id'], post['message_id'], reply_markup=kbs, parse_mode='HTML')


@router.callback_query(F.data == 'hide_message')
async def hide_message_func(callback: CallbackQuery, state: FSMContext):
    if len(cur2.execute('select * from data where id == ?', (callback.from_user.id,)).fetchall()) != 0 or callback.from_user.id in admin_ids:
        await callback.message.delete()


@router.callback_query(F.data.startswith('edit_message_'))
async def edit_message_func(callback: CallbackQuery, state: FSMContext):
    if len(cur2.execute('select * from data where id == ?', (callback.from_user.id,)).fetchall()) != 0 or callback.from_user.id in admin_ids:
        id = int(callback.data.split('_')[-1])
        kbs = [[InlineKeyboardButton(text = '← Назад', callback_data=f'select_channel_{id}')]]
        kbs = InlineKeyboardMarkup(inline_keyboard=kbs)
        await callback.message.edit_text('Пришли мне сообщение', reply_markup=kbs)
        await state.set_state(aForm.edit_message)
        await state.update_data(id = id)

@router.message(F.content_type.in_(any), aForm.edit_message)
async def edit_message_func(message: Message, state: FSMContext):
    if len(cur2.execute('select * from data where id == ?', (message.from_user.id,)).fetchall()) != 0 or message.from_user.id in admin_ids:
        data = await state.get_data()
        id = data['id']
        await state.update_data(chat_id = message.from_user.id, message_id = message.message_id)
        kbs = [[InlineKeyboardButton(text = 'Продолжить без кнопок →', callback_data='skip_buttons')],
               [InlineKeyboardButton(text = '← Назад', callback_data=f'select_channel_{id}')]]
        kbs = InlineKeyboardMarkup(inline_keyboard=kbs)
        await message.answer('''Отправьте боту список URL-кнопок в следующем формате:

<code>Кнопка 1 - http://example1.com
Кнопка 2 - http://example2.com</code>

Используйте разделитель "|", чтобы добавить до трех кнопок в один ряд (допустимо 15 рядов):

<code>Кнопка 1 - http://example1.com | Кнопка 2 - http://example2.com
Кнопка 3 - http://example3.com | Кнопка 4 - http://example4.com</code>''', reply_markup=kbs, parse_mode='HTML')
        await state.set_state(aForm.edit_kbs)

@router.callback_query(F.data == 'skip_buttons', aForm.edit_kbs)
async def skip_buttons_func(callback: CallbackQuery, state: FSMContext):
    if len(cur2.execute('select * from data where id == ?', (callback.from_user.id,)).fetchall()) != 0 or callback.from_user.id in admin_ids:
        data = await state.get_data()
        id = data['id']
        mes = {
            'chat_id': data['chat_id'],
            'message_id': data['message_id'],
            'kbs': []
        }
        cur3.execute('update data set message == ? where id == ?', (json.dumps(mes), id))
        base3.commit()
        await callback.message.edit_text('Сообщение успешно изменено!')
        kbs, text = await functions.generate_one_channel(id)
        await bot.send_message(callback.from_user.id, text, reply_markup=kbs, parse_mode='HTML', disable_web_page_preview=True)
        await state.clear()

@router.message(F.text, aForm.edit_kbs)
async def edit_kbs_func(message: Message, state: FSMContext):
    if len(cur2.execute('select * from data where id == ?', (message.from_user.id,)).fetchall()) != 0 or message.from_user.id in admin_ids:
        try:
            message_kbs = []
            data_kbs = []
            for row in message.text.split('\n'):
                k = []
                data_k = []
                for row2 in row.split(' | '):
                    data_k.append({'text': row2.split(' - ')[0], 'url': row2.split(' - ')[1]})
                    k.append(InlineKeyboardButton(text = row2.split(' - ')[0], url=row2.split(' - ')[1]))
                data_kbs.append(data_k)
                message_kbs.append(k)
            kbs = InlineKeyboardMarkup(inline_keyboard=message_kbs)
            a = await bot.send_message(message.from_user.id, 'test', reply_markup=kbs)
            await bot.delete_message(message.from_user.id, a.message_id)
            data = await state.get_data()
            id = data['id']
            mes = {
                'chat_id': data['chat_id'],
                'message_id': data['message_id'],
                'kbs': data_kbs
            }
            cur3.execute('update data set message == ? where id == ?', (json.dumps(mes), id))
            base3.commit()
            await message.answer('Сообщение успешно изменено!')
            kbs, text = await functions.generate_one_channel(id)
            await bot.send_message(message.from_user.id, text, reply_markup=kbs, parse_mode='HTML', disable_web_page_preview=True)
            await state.clear()
        except Exception as err:
            print(err)
            await message.answer('''Кнопки, которые ты прислал, не соответствуют формату:
        
<code>Кнопка 1 - http://example1.com
Кнопка 2 - http://example2.com</code>

Используйте разделитель "|", чтобы добавить до трех кнопок в один ряд (допустимо 15 рядов):

<code>Кнопка 1 - http://example1.com | Кнопка 2 - http://example2.com
Кнопка 3 - http://example3.com | Кнопка 4 - http://example4.com</code>''', parse_mode='HTML')


@router.callback_query(F.data.startswith('turn_channel_'))
async def turn_channel_func(callback: CallbackQuery, state: FSMContext):
    if len(cur2.execute('select * from data where id == ?', (callback.from_user.id,)).fetchall()) != 0 or callback.from_user.id in admin_ids:
        id = int(callback.data.split('_')[-1])
        turn = cur3.execute('select turn from data where id == ?', (id, )).fetchone()[0]
        turn = 1 if turn == 0 else 0
        cur3.execute('update data set turn == ? where id == ?', (turn, id))
        base3.commit()
        kbs, text = await functions.generate_one_channel(id)
        await callback.message.edit_text(text, reply_markup=kbs, parse_mode='HTML', disable_web_page_preview=True)


@router.callback_query(F.data.startswith('delete_channel_'))
async def delete_channel_func(callback: CallbackQuery, state: FSMContext):
    if len(cur2.execute('select * from data where id == ?', (callback.from_user.id,)).fetchall()) != 0 or callback.from_user.id in admin_ids:
        id = int(callback.data.split('_')[-1])
        select = cur3.execute('select * from data where id == ?', (id, )).fetchone()
        info = json.loads(select[1])
        kbs = [[InlineKeyboardButton(text = '✔️ Да, удалить', callback_data=f'yes_del_{id}')],
               [InlineKeyboardButton(text = '✖️ Нет, отмена', callback_data=f'select_channel_{id}')]]
        kbs = InlineKeyboardMarkup(inline_keyboard=kbs)
        await callback.message.edit_text(f'Ты уверен, что хочешь удалить канал <b>"{info["title"]}"</b>?',
                                         parse_mode='HTML', reply_markup=kbs)

@router.callback_query(F.data.startswith('yes_del'))
async def yes_del_func(callback: CallbackQuery, state: FSMContext):
    if len(cur2.execute('select * from data where id == ?', (callback.from_user.id,)).fetchall()) != 0 or callback.from_user.id in admin_ids:
        id = int(callback.data.split('_')[-1])
        select = cur3.execute('select * from data where id == ?', (id, )).fetchone()
        info = json.loads(select[1])
        cur3.execute('delete from data where id == ?', (id, ))
        base3.commit()
        cur3.execute('vacuum')
        await callback.answer(f'Канал "{info["title"]}" успешно удалён!')
        kbs = await functions.generate_channels()
        await callback.message.edit_text('Здесь ты можешь управлять подключёнными каналами', reply_markup=kbs)

