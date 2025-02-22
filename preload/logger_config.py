import logging
import sys
from logging.handlers import RotatingFileHandler

def setup_logger():
    # Создаем основной логгер
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    
    # Очищаем существующие хендлеры
    logger.handlers.clear()
    
    # Создаем форматтер
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(name)s - %(message)s')
    
    # Хендлер для файла с ротацией (максимум 5 файлов по 10MB)
    file_handler = RotatingFileHandler(
        "logs/bot.log",
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5,
        encoding='utf-8',
        mode='a'
    )
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    
    # Хендлер для консоли
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # Отключаем логи от aiogram ниже WARNING
    logging.getLogger('aiogram').setLevel(logging.WARNING)
    
    return logger 