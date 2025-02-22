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


@router.callback_query(F.data == 'back_to_start')
async def back_to_start_func(callback: CallbackQuery, state: FSMContext):
    if len(cur2.execute('select * from data where id == ?', (callback.from_user.id,)).fetchall()) != 0 or callback.from_user.id in admin_ids:
        await state.clear()
        await callback.message.edit_text(
            f'👋 <b>Приветствую, {callback.from_user.first_name}!</b>\n\nДобро пожаловать в админ панель бота приёма заявок.',
            parse_mode='HTML')

#
@router.message(F.text == '🗄 Каналы')
async def channels_func(message: Message, state: FSMContext):
    if len(cur2.execute('select * from data where id == ?', (message.from_user.id,)).fetchall()) != 0 or message.from_user.id in admin_ids:
        await state.clear()
        kbs = await functions.generate_channels()
        await message.answer('Здесь ты можешь управлять подключёнными каналами', reply_markup=kbs)

@router.message(F.text == '💬 Рассылка')
async def spam_func(message: Message, state: FSMContext):
    if len(cur2.execute('select * from data where id == ?', (message.from_user.id,)).fetchall()) != 0 or message.from_user.id in admin_ids:
        await state.clear()
        kbs = [[InlineKeyboardButton(text = '← Назад', callback_data='back_to_start')]]
        kbs = InlineKeyboardMarkup(inline_keyboard=kbs)
        await message.answer('Пришли мне пост для рассылки', reply_markup=kbs)
        await state.set_state(aForm.spam_post)

@router.message(F.text == '📈 Статистика')
async def stat_func(message: Message, state: FSMContext):
    if len(cur2.execute('select * from data where id == ?', (message.from_user.id,)).fetchall()) != 0 or message.from_user.id in admin_ids:
        await state.clear()
        text = await functions.get_stat_func()
        await message.answer(text, parse_mode='HTML')

@router.message(F.text == '👤 Админы')
async def admins_func(message: Message, state: FSMContext):
    if message.from_user.id in admin_ids:
        await state.clear()
        kbs = await functions.generate_admins()
        await message.answer('Здесь ты можешь управлять админами бота', reply_markup=kbs)

