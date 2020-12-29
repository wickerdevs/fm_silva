PERSISTENCE_DIR = 'config/'
CONFIG_DIR = 'config/config.json'
CONFIG_FOLDER = 'config/'
LOCALHEADLESS = False

import os, logging
from telegram.ext.updater import Updater
from telegram.ext.defaults import Defaults
from telegram.utils.request import Request
from fmsilva.models.mq_bot import MQBot
import telegram
from telegram import ParseMode
from telegram.ext import messagequeue as mq

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
if os.environ.get('PORT') not in (None, ""):
    # Code running locally
    LOCALHOST = False    

from fmsilva.models.worker import TaskQueue
queue = TaskQueue(num_workers=6)

# Initialize Bot
from fmsilva.modules import config
BOT_TOKEN = config.get('BOT_TOKEN')
URL = config.get('SERVER_APP_DOMAIN')
PORT = int(os.environ.get('PORT', 5000))

# set connection pool size for bot 
request = Request(con_pool_size=8)
defaults = Defaults(parse_mode=ParseMode.HTML, run_async=True)
q = mq.MessageQueue(all_burst_limit=3, all_time_limit_ms=3000)
telegram_bot = MQBot(BOT_TOKEN, request=request, mqueue=q, defaults=defaults)
updater = Updater(bot=telegram_bot, use_context=True)

# SET UP BOT COMMAND HANDLERS
applogger.debug(f'Initiate setup')
from fmsilva.bot import setup
setup.setup(updater)


        