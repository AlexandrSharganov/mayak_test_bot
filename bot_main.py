from dotenv import load_dotenv
import os
import sqlite3
import telegram
from telegram.ext import Updater, Filters, MessageHandler, CommandHandler
import pandas as pd


load_dotenv()

BOT_TOKEN = os.getenv('TOKEN')

bot = telegram.Bot(token=BOT_TOKEN)

updater = Updater(token=BOT_TOKEN)

con = sqlite3.connect('db.sqlite', check_same_thread=False)

FILES_DIR = 'uploaded_fiels'

START_TEXT = 'Привет! Прикрепи к сообщению excel файл и отправь его мне. \
И может что-то произойдет.'

if not os.path.exists(FILES_DIR):
    os.mkdir(FILES_DIR)
    
def open_file_with_pandas(file_path, chat_id, file_unique_id):
    """
    Открываем файл библиотекой pandas.
    Отправляем содержимое пользователю.
    Сохраняем содержимое в локальную бд sqlite.
    """
    opened_file = pd.read_excel(file_path)
    result_string = opened_file.to_string()
    bot.send_message(
        chat_id=chat_id,
        text=result_string
    )
    table_name = f'{chat_id}{file_unique_id}'
    opened_file.to_sql(name=table_name, con=con)

def download_file(uploaded_file, chat_id):
    """
    Скачиваем файл в подготовленную папку.
    """
    download_link = bot.get_file(file_id=uploaded_file.file_id)
    folder_path = f'{FILES_DIR}/{chat_id}'
    file_path = f'{FILES_DIR}/{chat_id}/{uploaded_file.file_name}'
    if not os.path.exists(folder_path):
        os.mkdir(f'{FILES_DIR}/{chat_id}')
    if os.path.exists(file_path):
        bot.send_message(
            chat_id=chat_id,
            text='Вы уже загружали файл с таким именем!'
        )
        return
    download_link.download(custom_path=file_path)
    open_file_with_pandas(file_path, chat_id, uploaded_file.file_unique_id)
    
def wake_up(update, context):
    """
    Функция приветствия после запуска бота командой /start.
    """
    chat = update.effective_chat
    context.bot.send_message(
        text=START_TEXT,
        chat_id=chat.id,
    )
    
def try_to_load(update, context):
    """
    Получение ссылки на загружаемый файл.
    """
    chat = update.effective_chat
    uploaded_file = update.message.document
    context.bot.send_message(
        chat_id=chat.id,
        text='Вы загружаете файл!'
    )
    download_file(uploaded_file, chat.id)


updater.dispatcher.add_handler(CommandHandler('start', wake_up))
updater.dispatcher.add_handler(
    MessageHandler(
        Filters.document.mime_type('application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'),
        try_to_load
    )
)


updater.start_polling(poll_interval=5.0)

updater.idle() 
