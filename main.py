import os
import json
import requests
import schedule
import logging 
import datetime
import time as t
from pyowm.owm import OWM
import logging
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler

chat_ids = []

load_dotenv()
tl_key = os.getenv('TELEGRAM_KEY')

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

#Console print of error
def error(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    logging.error(f'Update "{update}" caused error {ctx.error}')

#Needed for dolar value report
data = (requests.get('https://api.bluelytics.com.ar/v2/latest')).json()
actual_value = data['blue']['value_sell']

def send_msg(bot_message):
    for chat_id in chat_ids:
        send_text = 'https://api.telegram.org/bot' + tl_key + '/sendMessage?chat_id=' + chat_id + '&parse_mode=Markdown&text=' + bot_message
        response = requests.get(send_text)
        return response.json()

def dolar_close(): #should send the message to every chat
    close = ((requests.get('https://api.bluelytics.com.ar/v2/latest')).json())['blue']['value_sell']
    send_msg(f'The dollar has closed at ${close}💸')

def proof():
    send_msg('This is a proof message')

def check_dollar_update(): #should send the message to every chat
    global actual_value
    new_value = ((requests.get('https://api.bluelytics.com.ar/v2/latest')).json())['blue']['value_sell']

    if new_value > actual_value:
        send_msg(f'The dollar value rose to {new_value}📈') 
    elif new_value < actual_value:
        send_msg(f'The dollar value fell to {new_value}📉') 
    elif new_value == actual_value:
        send_msg(f'The value of the dollar is still at {new_value}💹') #see how to send it to every chat, at X time
    
    actual_value = new_value

def weather():
    owm = OWM(os.getenv('OWM'))
    mgr = owm.weather_manager()
    weather_now = (mgr.weather_at_place('Buenos Aires')).weather
    fl = weather_now.temperature('celsius')['feels_like']
    max = weather_now.temperature('celsius')['temp_max']
    min = weather_now.temperature('celsius')['temp_min']

    return f'It is {weather_now.detailed_status}, with a minimun of {round(min)}°, a max of {round(max)}°, and a feels like of {round(fl)}° 🌥'

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.message.chat_id
    if chat_id not in chat_ids:
        chat_ids.append(chat_id)
    await context.bot.send_message(chat_id=update.effective_chat.id, text="Hello Sir, welcome! I can serve you the weather, the dolar value and your favourites cryptocurrencies values.")
    logging.info(f'User ({update.message.chat.first_name}) executed: start_command, chat_id: {chat_id}')


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("You picked out the help command, how can i help u?\nHere are all my commands for now:\nstart - Find out what this bot can do🐍\nhelp - Get assistance for this bot⛑\ndolar - Get the value of dolar to Pesos argentinos💸\ncryptos - Get the actual value of my favourites cryptos🔥\nweather - Get what's the weather like right now🌥")
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

    await update.message.reply_text(f'\tActual Value 💹\n🔥 BTC:   {consultaBTC}\n🔗 ETH:   {consultaETH}\n💲 DAI:   {consultaDAI}')
    logging.info(f'User ({update.message.chat.first_name}) executed: cryptos_command')

if __name__ == '__main__':

    app = ApplicationBuilder().token(tl_key).build()
    
    app.add_handler(CommandHandler('start', start))
    app.add_handler(CommandHandler('dollar', dollar_command))    
    app.add_handler(CommandHandler('help', help_command))    
    app.add_handler(CommandHandler('weather', weather_command))    
    app.add_handler(CommandHandler('crypto', crypto_command))    

    app.add_error_handler(error)
    app.run_polling(poll_interval=5.0)

    schedule.every().hour.do(check_dollar_update)
    schedule.every(1).minutes.do(proof) #not working too2

    schedule.run_pending()
    t.sleep(1)


"""
#Auto-reply
def handle_message(update, ctx):
    text = str(update.message.text)
    update.message.reply_text(text)
    logging.info(f'User ({update.message.chat.first_name}) says: {text}')
"""

#TODO: Fix schedule and the time of the messages 
#Is chait_ids implemented right?