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


load_dotenv()
tl_key = os.getenv('TELEGRAM_KEY')

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

#Console print of error
def error(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    logging.error(f'Update "{update}" caused error {ctx.error}')

#Needed for dolar value report
data = (requests.get('https://api.bluelytics.com.ar/v2/latest')).json()
actual_value = data['blue']['value_sell']

def check_dollar_update():
    global actual_value
    new_value = ((requests.get('https://api.bluelytics.com.ar/v2/latest')).json())['blue']['value_sell']

    if new_value > actual_value:
        print(f'The dollar value rose to {new_value}📈') 
    elif new_value < actual_value:
        print(f'The dollar value fell to {new_value}📉') 
    elif new_value == actual_value:
        print(f'The value of the dollar is still at {new_value}💹') #see how to send it to every chat, at X time
    
    actual_value = new_value

def dolar_close():
    close = ((requests.get('https://api.bluelytics.com.ar/v2/latest')).json())['blue']['value_sell']
    return(f'The dollar has closed at ${close}💸')

def weather():
    owm = os.getenv('OWM')
    mgr = owm.weather_manager()
    weather_now = (mgr.weather_at_place('Buenos Aires')).weather #not working on this line, revise
    fl = weather_now.temperature('celsius')['feels_like']
    max = weather_now.temperature('celsius')['temp_max']
    min = weather_now.temperature('celsius')['temp_min']

    return f'It is {weather_now.detailed_status}, with a minimun of {min}°, a max of {max}°, and a feels like of {fl}° 🌥'


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(chat_id=update.effective_chat.id, text="I'm a bot, please talk to me!")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("You picked out the help command, how can i help u?\nHere are all my commands for now:\nstart - Find out what this bot can do🐍\nhelp - Get assistance for this bot⛑\ndolar - Get the value of dolar to Pesos argentinos💸\ncryptos - Get the actual value of my favourites cryptos🔥\nweather - Get what's the weather like right now🌥")
    logging.info(f'User ({update.message.chat.first_name}) executed: help_command')

async def dollar_command(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    actual_value = ((requests.get('https://api.bluelytics.com.ar/v2/latest')).json())['blue']['value_sell']
    await update.message.reply_text(f'The actual value of dollar blue in Argentina is of {actual_value} pesos argentinos.💸')
    logging.info(f'User ({update.message.chat.first_name}) executed: dolar_command')

async def weather_command(update, ctx):
    await update.message.reply_text(f'{weather()}')
    logging.info(f'User ({update.message.chat.first_name}) executed: weather_command')

if __name__ == '__main__':

    app = ApplicationBuilder().token(tl_key).build()
    
    app.add_handler(CommandHandler('start', start))
    app.add_handler(CommandHandler('dollar', dollar_command))    
    app.add_handler(CommandHandler('help', help_command))    
    app.add_handler(CommandHandler('weather', weather_command))    

    app.add_error_handler(error)
    app.run_polling(poll_interval=3.0)

    schedule.every().hour.do(check_dollar_update)
    schedule.every().minute.do(check_dollar_update)

    while True:
        schedule.run_pending()
        t.sleep(10)
