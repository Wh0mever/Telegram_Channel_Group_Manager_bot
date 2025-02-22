from aiogram.fsm.storage.memory import MemoryStorage
from aiogram import Bot, Dispatcher

from secrets import token_hex
import asyncio

from handlers import main_handler
from admin_handlers import admin_handler, channels, spam, admins
from preload.config import *
from preload.databases import *
from preload.logger_config import setup_logger

# Настройка логирования
logger = setup_logger()
logger.info("Бот запущен")

async def get_stat_func(bot):
    while True:
        try:
            select = cur.execute('select * from data where life != ?', (2, )).fetchall()
            for row in select:
                try:
                    await bot.send_chat_action(chat_id=row[0], action='typing')
                    cur.execute('update data set life == ? where id == ?', (1, row[0]))
                    base.commit()
                except Exception as e:
                    logger.debug(f"Пользователь {row[0]} заблокировал бота: {e}")
                    cur.execute('update data set life == ? where id == ?', (0, row[0]))
                    base.commit()
            await asyncio.sleep(3)
        except Exception as e:
            logger.error(f"Ошибка в get_stat_func: {e}")
            await asyncio.sleep(3)


async def main():
    dp = Dispatcher(storage=MemoryStorage())
    bot = Bot(TOKEN)

    dp.include_router(admin_handler.router)
    dp.include_router(channels.router)
    dp.include_router(spam.router)
    dp.include_router(admins.router)

    dp.include_router(main_handler.router)


    loop = asyncio.get_event_loop()
    loop.create_task(get_stat_func(bot))

    await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())


if __name__ == '__main__':
    asyncio.run(main())