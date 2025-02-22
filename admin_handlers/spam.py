import asyncio
import json

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


router = Router()
bot = Bot(TOKEN)


import logging
logging.basicConfig(level=logging.INFO, filename="logs/handlers.log",filemode="w")


async def spam(chat_id, message_id, kbs, channels):
    select = cur.execute('select * from data').fetchall()
    data = {}
    for c in channels:
        data[c] = {
            'yes': 0,
            'no': 0
        }
    for row in select:
        if row[1] in channels:
            try:
                await bot.copy_message(row[0], chat_id, message_id, parse_mode='HTML', reply_markup=kbs)
                data[row[1]]['yes'] += 1
            except:
                data[row[1]]['no'] += 1
    text = '✔️ <b>Рассылка успешно завершена!</b>'
    for row in data:
        info = cur3.execute('select info from data where id == ?', (row, )).fetchone()[0]
        info = json.loads(info)
        text += f'\n\n<b>{info["title"]}</b>\nУспешно отправлено: {data[row]["yes"]}\nНе отправлено: {data[row]["no"]}'

    await bot.send_message(chat_id, text, parse_mode='HTML')



@router.message(F.content_type.in_(any), aForm.spam_post)
async def spam_post_func(message: Message, state: FSMContext):
    if len(cur2.execute('select * from data where id == ?', (message.from_user.id,)).fetchall()) != 0 or message.from_user.id in admin_ids:
        await state.update_data(chat_id=message.from_user.id, message_id=message.message_id)
        kbs = [[InlineKeyboardButton(text='Продолжить без кнопок →', callback_data='skip_buttons')],
               [InlineKeyboardButton(text='← Назад', callback_data=f'back_to_start')]]
        kbs = InlineKeyboardMarkup(inline_keyboard=kbs)
        await message.answer('''Отправьте боту список URL-кнопок в следующем формате:

<code>Кнопка 1 - http://example1.com
Кнопка 2 - http://example2.com</code>

Используйте разделитель "|", чтобы добавить до трех кнопок в один ряд (допустимо 15 рядов):

<code>Кнопка 1 - http://example1.com | Кнопка 2 - http://example2.com
Кнопка 3 - http://example3.com | Кнопка 4 - http://example4.com</code>''', reply_markup=kbs, parse_mode='HTML')
        await state.set_state(aForm.spam_kbs)
        await state.update_data(select_channels = [])


@router.callback_query(F.data == 'skip_buttons', aForm.spam_kbs)
async def skip_kbs_func(callback: CallbackQuery, state: FSMContext):
    if len(cur2.execute('select * from data where id == ?', (callback.from_user.id,)).fetchall()) != 0 or callback.from_user.id in admin_ids:
        kbs = [[]]
        kbs = InlineKeyboardMarkup(inline_keyboard=kbs)
        await state.update_data(kbs = kbs)
        data = await state.get_data()
        kbs = await functions.generate_spam_channels(data)
        await callback.message.edit_text('Выбери, по каким каналам будет производиться рассылка:', reply_markup=kbs)
        await state.set_state(aForm.spam_channels)


@router.message(F.text, aForm.spam_kbs)
async def spam_kbs_func(message: Message, state: FSMContext):
    if len(cur2.execute('select * from data where id == ?', (message.from_user.id,)).fetchall()) != 0 or message.from_user.id in admin_ids:
        try:
            message_kbs = []
            for row in message.text.split('\n'):
                k = []
                for row2 in row.split(' | '):
                    k.append(InlineKeyboardButton(text=row2.split(' - ')[0], url=row2.split(' - ')[1]))
                message_kbs.append(k)
            kbs = InlineKeyboardMarkup(inline_keyboard=message_kbs)
            await state.update_data(kbs = kbs)
            a = await bot.send_message(message.from_user.id, 'test', reply_markup=kbs)
            await bot.delete_message(message.from_user.id, a.message_id)
            data = await state.get_data()
            kbs = await functions.generate_spam_channels(data)
            await message.answer('Выбери, по каким каналам будет производиться рассылка:', reply_markup=kbs)
            await state.set_state(aForm.spam_channels)
        except Exception as err:
            await message.answer('''Кнопки, которые ты прислал, не соответствуют формату:

<code>Кнопка 1 - http://example1.com
Кнопка 2 - http://example2.com</code>

Используйте разделитель "|", чтобы добавить до трех кнопок в один ряд (допустимо 15 рядов):

<code>Кнопка 1 - http://example1.com | Кнопка 2 - http://example2.com
Кнопка 3 - http://example3.com | Кнопка 4 - http://example4.com</code>''', parse_mode='HTML')


@router.callback_query(F.data.startswith('select_spamchan_'), aForm.spam_channels)
async def spam_channels_func(callback: CallbackQuery, state: FSMContext):
    if len(cur2.execute('select * from data where id == ?', (callback.from_user.id,)).fetchall()) != 0 or callback.from_user.id in admin_ids:
        data = await state.get_data()
        select_channels = data['select_channels']
        select = int(callback.data.split('_')[-1])
        if select in select_channels:
            select_channels.remove(select)
        else:
            select_channels.append(select)
        await state.update_data(select_channels = select_channels)
        data = await state.get_data()
        kbs = await functions.generate_spam_channels(data)
        await callback.message.edit_reply_markup(reply_markup=kbs)

#chat_id, message_id, kbs, channels
@router.callback_query(F.data == 'start_spam', aForm.spam_channels)
async def start_spam_func(callback: CallbackQuery, state: FSMContext):
    if len(cur2.execute('select * from data where id == ?', (callback.from_user.id,)).fetchall()) != 0 or callback.from_user.id in admin_ids:
        data = await state.get_data()
        select_channels = data['select_channels']
        if len(select_channels) != 0:
            chat_id = data['chat_id']
            message_id = data['message_id']
            kbs = data['kbs']
            n = 0
            for row in select_channels:
                n += len(cur.execute('select * from data where channel == ?', (row, )).fetchall())
            loop = asyncio.get_event_loop()
            loop.create_task(spam(chat_id, message_id, kbs, select_channels))
            await callback.message.edit_text(f'Рассылка на {n}чел. запущена!')
            await state.clear()
        else:
            await callback.answer('Ты должен выбрать хотя бы один канал!', show_alert=True)
