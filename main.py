import os
import json
import pytz
import logging
import requests
from pyowm.owm import OWM
from telegram import Update
from dotenv import load_dotenv
from datetime import time, datetime, date
from telegram.ext import Application, CommandHandler, ContextTypes, CallbackContext

load_dotenv()
tl_key = os.getenv('TELEGRAM_KEY')
chat_id = os.getenv('CHAT_ID')

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

#Console print of error
def error(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    logging.error(f'Update "{update}" caused error {ctx.error}')

data = (requests.get('https://api.bluelytics.com.ar/v2/latest')).json()
actual_value = data['blue']['value_sell']

#FUNCTIONS

def weather():
    owm = OWM(os.getenv('OWM'))
    mgr = owm.weather_manager()
    weather_now = (mgr.weather_at_place('Buenos Aires')).weather
    fl = weather_now.temperature('celsius')['feels_like']
    max = weather_now.temperature('celsius')['temp_max']
    min = weather_now.temperature('celsius')['temp_min']

    return f'It is {weather_now.detailed_status}, with a minimun of {round(min)}°, a max of {round(max)}°, and a feels like of {round(fl)}° 🌥'

#SCHEDULED MESSAGES

async def check_dollar_update(context: ContextTypes.DEFAULT_TYPE): #should send the message to every chat
    global actual_value
    new_value = ((requests.get('https://api.bluelytics.com.ar/v2/latest')).json())['blue']['value_sell']
    yesterday_close = ((requests.get('https://api.bluelytics.com.ar/v2/evolution.json')).json())[3]['value_sell']

    diff = ((new_value - yesterday_close) / yesterday_close) * 100

    if new_value > actual_value:
        await context.bot.send_message(chat_id=chat_id, text=f'The dollar value is up to {new_value}, ({round(diff,2)}) 24hs📈')
    elif new_value < actual_value:
        await context.bot.send_message(chat_id=chat_id, text=f'The dollar value is down to {new_value}, ({round(diff,2)}) 24hs📉')

    actual_value = new_value

async def dolar_close(context: CallbackContext):
    close = ((requests.get('https://api.bluelytics.com.ar/v2/latest')).json())['blue']['value_sell']
    await context.bot.send_message(chat_id=chat_id, text=f'The dollar has closed at {close}💸')

async def good_morning(context: CallbackContext):
    dollar = ((requests.get('https://api.bluelytics.com.ar/v2/latest')).json())['blue']['value_sell']
    today = (date.today()).strftime("%B %d, %Y")
    await context.bot.send_message(chat_id=chat_id, text=f"""
                                   \nGood Morning Sir.
                                   \nToday is {today}📅
                                   \n{weather()}
                                   \nThe dollar value is of ${dollar} 💸
                                   \nHave a nice day 🤖
                                   """)

#COMMANDS
async def start_command(update: Update,context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(chat_id=update.effective_chat.id, text="Hello Sir, welcome! I can serve you the weather, the dolar value and your favourites cryptocurrencies values.")
    logging.info(f'User: ({update.message.chat.first_name}) executed: start_command.')

async def check_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(chat_id=context._user_id ,text='Im alive, check command')
    logging.info(f'User: ({update.message.chat.first_name}) executed: check_command.')

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("You picked out the help command, how can i help u?\nHere are all my commands for now:\nstart - Find out what this bot can do🐍\nhelp - Get assistance for this bot⛑\ndolar - Get the value of dolar to Pesos argentinos💸\ncryptos - Get the actual value of my favourites cryptos🪙\nweather - Get what's the weather like right now🌥")
    logging.info(f'User ({update.message.chat.first_name}) executed: help_command')

async def dollar_command(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    actual_value = ((requests.get('https://api.bluelytics.com.ar/v2/latest')).json())['blue']['value_sell']
    await update.message.reply_text(f'The actual value of dollar blue in Argentina is of {actual_value} pesos argentinos.💸')
    logging.info(f'User ({update.message.chat.first_name}) executed: dollar_command')

async def weather_command(update, ctx):
    await update.message.reply_text(f'{weather()}')
    logging.info(f'User ({update.message.chat.first_name}) executed: weather_command')

async def crypto_command(update, ctx):
    consultaBTC = json.loads(requests.get(f'https://min-api.cryptocompare.com/data/price?fsym=BTC&tsyms=USD').text)["USD"]
    consultaETH = json.loads(requests.get(f'https://min-api.cryptocompare.com/data/price?fsym=ETH&tsyms=USD').text)["USD"]
    consultaDAI = (requests.get('https://criptoya.com/api/lemoncash/DAI').json())['ask']

    await update.message.reply_text(f'\tActual prices👇🏼\n⚡️ BTC/USD: {consultaBTC}\n⛓ ETH/USD: {consultaETH}\n💵 DAI/ARS: {consultaDAI}')
    logging.info(f'User ({update.message.chat.first_name}) executed: cryptos_command')

application = Application.builder().token(tl_key).build()
job_queue = application.job_queue

application.add_handler(CommandHandler('start', start_command))
application.add_handler(CommandHandler('check', check_command))
application.add_handler(CommandHandler('help', help_command))
application.add_handler(CommandHandler('dollar', dollar_command))
application.add_handler(CommandHandler('weather', weather_command))
application.add_handler(CommandHandler('crypto', crypto_command))

application.add_error_handler(error)

job_minute = job_queue.run_repeating(check_dollar_update, interval=1800, first=10)

buenos_aires_tz = pytz.timezone('America/Argentina/Buenos_Aires')

job_daily = job_queue.run_daily(dolar_close, time=(time(17,00, tzinfo=buenos_aires_tz)), days=(1, 2, 3, 4, 5))
job_daily = job_queue.run_daily(good_morning, time=(time(9,15, tzinfo=buenos_aires_tz)))

application.run_polling(poll_interval=10.0)