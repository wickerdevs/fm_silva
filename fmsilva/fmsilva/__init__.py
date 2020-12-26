PERSISTENCE_DIR = 'fmsilva/config'
CONFIG_DIR = 'fmsilva/config/config.json'
CONFIG_FOLDER = 'fmsilva/config'

import os, logging

# Enable logging
# TODO REMOVE WHEN FINISHED DEBUGGING
debug = True
if debug:
    logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
else:
    logging.basicConfig(filename="logs.log", format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

applogger = logging.getLogger('applogger')
applogger.setLevel(logging.DEBUG)

instalogger = logging.getLogger('instaclient')
instalogger.setLevel(logging.DEBUG)

telelogger = logging.getLogger("telegram.bot")
telelogger.setLevel(logging.INFO)

def instaclient_error_callback(driver):
    from fmsilva import telegram_bot as bot
    driver.save_screenshot('error.png')
    bot.report_error('instaclient.__find_element() error.', send_screenshot=True, screenshot_name='error')
    os.remove('error.png')


LOCALHOST = True
queue = None
if os.environ.get('PORT') not in (None, ""):
    # Code running locally
    LOCALHOST = False    

# Initialize Bot
from fmsilva.config import config
BOT_TOKEN = config.get('BOT_TOKEN')
URL = config.get('SERVER_APP_DOMAIN')
PORT = int(os.environ.get('PORT', 5000))


        