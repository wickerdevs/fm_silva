from functools import wraps
from telegram import update
from telegram.parsemode import ParseMode
from fmsilva.models.interaction import Interaction
from fmsilva.models.settings import Settings
from fmsilva.models.setting import Setting
from fmsilva.models.interactsession import InteractSession
from fmsilva.modules import config
from fmsilva.texts import *
from typing import List, Optional, Tuple
from fmsilva import CONFIG_DIR, CONFIG_FOLDER
from instaclient.client.instaclient import InstaClient
from instaclient.errors.common import FollowRequestSentError, InvaildPasswordError, InvalidUserError, PrivateAccountError, SuspisciousLoginAttemptError, VerificationCodeNecessary
from instaclient.instagram.post import Post
from fmsilva.models.instasession import InstaSession
from fmsilva import applogger, queue
import os, multiprocessing, logging

instalogger = logging.getLogger('instaclient')


def insta_error_callback(driver):
    driver.save_screenshot('error.png')
    from fmsilva import telegram_bot as bot, config # TODO
    users_str = config.get('DEVS')
    if isinstance(users_str, str):
        users_str = users_str.replace('[', '')
        users_str = users_str.replace(']', '')
        users_str = users_str.replace(' ', '')
        users = users_str.split(',')
        for index, user in enumerate(users):
            users[index] = int(user)
    else:
        users = users_str

    for dev in users:
        bot.send_photo(chat_id=dev, photo=open('{}.png'.format('error'), 'rb'), caption='There was an error with the bot. Check logs')

    
def update_message(obj: InteractSession, text:str):
    """
    process_update_callback sends an update message to the user, to inform of the status of the current process. This method can be used as a callback in another method.

    Args:
        obj (ScraperorForwarder): Object to get the `chat_id` and `message_id` from.
        message (str): The text to send via message
        message_id (int, optional): If this argument is defined, then the method will try to edit the message matching the `message_id` of the `obj`. Defaults to None.
    """
    from fmsilva import telegram_bot as bot
    message_id = config.get_message(obj.get_user_id())
    try:
        bot.delete_message(chat_id=obj.user_id, message_id=message_id)
    except Exception as error:
        applogger.error(f'Unable to delete message of id {message_id}', exc_info=error)
        pass         

    message_obj = bot.send_message(chat_id=obj.user_id, text=text, parse_mode=ParseMode.HTML)
    obj.set_message(message_obj.message_id)
    config.set_message(obj.user_id, message_obj.message_id)
    applogger.debug(f'Sent message of id {message_obj.message_id}')
    return   


def init_client():
    if os.environ.get('PORT') in (None, ""):
        client = InstaClient(driver_path=f'{CONFIG_FOLDER}chromedriver.exe', debug=True, error_callback=insta_error_callback, logger=instalogger, localhost_headless=True)
    else:
        client = InstaClient(host_type=InstaClient.WEB_SERVER, debug=True, error_callback=insta_error_callback, logger=instalogger, localhost_headless=True)
    return client


def error_proof(func):
    @wraps(func)
    def wrapper(session:InteractSession):
        result:Tuple[bool, InteractSession] = func(session)
        if result[1]:
            settings:Settings = config.get_settings(session.user_id)
            settings.add_interaction(result[1].interaction)
        return result
    return wrapper


def scrape_callback(scraped:List[str], session:InteractSession):
    session.set_scraped(scraped)
    session.save_scraped()
    update_message(session, scrape_followers_callback_text.format(len(scraped)))


def enqueue_scrape(session:InteractSession):
    queue.add_task(scrape_job, session=session)


@error_proof
def scrape_job(session:InteractSession) -> Tuple[bool, Optional[InteractSession]]:
    client = init_client()

    update_message(session, logging_in_text)
    try:
        client.login(session.username, session.password)
    except (InvalidUserError, InvaildPasswordError):
        client.disconnect()
        return (False, None)
    except VerificationCodeNecessary:
        client.disconnect()
        return (False, None)

    update_message(session, waiting_scrape_text)
    try:
        followers = client.get_followers(session.target, session.count)
        session.set_scraped(followers)
        session.save_scraped()
        client.disconnect()
        return (True, session)
    except Exception as error:
        applogger.error(f'Error in scraping <{session.target}>\'s followers: ', exc_info=error)
        client.disconnect()
        update_message(session, operation_error_text.format(len(session.get_followed())))
        return (False, None)


def enqueue_dm(session:InteractSession):
    update_message(session, 'ENQUEING DMs')


@error_proof
def interaction_job(session:InteractSession) -> Tuple[bool, Optional[InteractSession]]:
    settings:Settings = config.get_settings(session.user_id)
    setting:Setting = settings.get_setting(session.username)

    # TODO: Scrape Users
    if not session.get_scraped():
        result = scrape_job(session)
        if result[1]:
            followers = result[2].get_scraped()
        else:
            return (False, session)
    else:
        followers = session.get_scraped()

    client = init_client()

    update_message(session, logging_in_text)
    try:
        client.login(session.username, session.password)
    except (InvalidUserError, InvaildPasswordError):
        client.disconnect()
        return (False, None)
    except VerificationCodeNecessary:
        client.disconnect()
        return (False, None)
    
    session.set_interaction(Interaction(session.target))

    # FOR EACH USER
    for index, follower in enumerate(followers):
        # Send DM to User
        update_message(session, )
        try:
            client.send_dm(follower, session.get_text())
            session.add_messaged(follower)
        except Exception as error:
            applogger.error(f'Error in sending message to <{follower}>', exc_info=error)

    update_message(session, follow_successful_text.format(len(session.get_followed())))
    client.disconnect()
    return (True, session)

        