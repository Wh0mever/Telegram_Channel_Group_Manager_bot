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


@router.callback_query(F.data == 'back_to_admins')
async def back_to_admins_func(callback: CallbackQuery, state: FSMContext):
    if callback.from_user.id in admin_ids:
        await state.clear()
        kbs = await functions.generate_admins()
        await callback.message.edit_text('Здесь ты можешь управлять админами бота', reply_markup=kbs)

@router.callback_query(F.data == 'add_admin')
async def add_admin_func(callback: CallbackQuery, state: FSMContext):
    if callback.from_user.id in admin_ids:
        kbs = [[InlineKeyboardButton(text = '← Назад', callback_data='back_to_admins')]]
        kbs = InlineKeyboardMarkup(inline_keyboard=kbs)
        await callback.message.edit_text('Перешли мне сообщение от админа или пришли его айди.', reply_markup=kbs)
        await state.set_state(aForm.admin_message)

@router.message(F.content_type.in_(any), aForm.admin_message)
async def admin_message_func(message: Message, state: FSMContext):
    if message.from_user.id in admin_ids:
        if message.forward_from:
            admin_id = message.forward_from.id
        else:
            try:
                admin_id = int(message.text)
            except:
                admin_id = 0
        if admin_id != 0:
            if len(cur2.execute('select * from data where id == ?', (admin_id,)).fetchall()) == 0:
                cur2.execute('insert into data values (?, ?)', (admin_id, json.dumps(None)))
                base2.commit()
                await message.answer('Админ успешно добавлен!\n\n<i>Для того, чтобы он смог перейти в панель, он должен прописать /start в бота</i>',
                                     parse_mode='HTML')
                await state.clear()
                kbs = await functions.generate_admins()
                await bot.send_message(message.from_user.id, 'Здесь ты можешь управлять админами бота', reply_markup=kbs)
            else:
                await message.answer('Админ с этим айди уже есть в базе!')
        else:
            await message.answer('Это не похоже на сообщение от админа или его айди..')


@router.callback_query(F.data.startswith('select_admin_'))
async def select_admin_func(callback: CallbackQuery, state: FSMContext):
    if callback.from_user.id in admin_ids:
        admin_id = int(callback.data.split('_')[-1])
        select = cur2.execute('select * from data where id == ?', (admin_id, )).fetchone()
        info = json.loads(select[1])
        if info != None:
            text = f'Админ <a href="tg://user?id={admin_id}>{info["first_name"]}</a>\n\nАйди: <code>{admin_id}</code>\nЮзернейм: {"@"+info["username"] if info["username"] else "нет"}'
        else:
            text = f'Админ с ID <code>{admin_id}</code>\n\n<i>Его информация не отображается, значит он ещё не прописал команду /start в бота.</i>'
        kbs = [[InlineKeyboardButton(text = '🗑 Удалить админа', callback_data=f'delete_admin_{admin_id}')],
               [InlineKeyboardButton(text = '← Назад', callback_data='back_to_admins')]]
        kbs = InlineKeyboardMarkup(inline_keyboard=kbs)
        await callback.message.edit_text(text, parse_mode='HTML', reply_markup=kbs)


@router.callback_query(F.data.startswith('delete_admin'))
async def delete_admin_func(callback: CallbackQuery, state: FSMContext):
    if callback.from_user.id in admin_ids:
        admin_id = int(callback.data.split('_')[-1])
        kbs = [[InlineKeyboardButton(text = 'Да, удалить', callback_data=f'yes_admindel_{admin_id}')],
               [InlineKeyboardButton(text = 'Нет, отмена', callback_data=f'select_admin_{admin_id}')]]
        kbs = InlineKeyboardMarkup(inline_keyboard=kbs)
        await callback.message.edit_text('Ты уверен, что хочешь удалить админа?', reply_markup=kbs)

@router.callback_query(F.data.startswith('yes_admindel'))
async def yes_admindel_func(callback: CallbackQuery, state: FSMContext):
    if callback.from_user.id in admin_ids:
        admin_id = int(callback.data.split('_')[-1])
        cur2.execute('delete from data where id == ?', (admin_id, ))
        base2.commit()
        cur2.execute('vacuum')
        await callback.answer('Админ успешно удалён!', show_alert=True)
        kbs = await functions.generate_admins()
        await callback.message.edit_text('Здесь ты можешь управлять админами бота', reply_markup=kbs)
