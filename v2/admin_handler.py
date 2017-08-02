import json
import traceback

import pika
import praw
import time

import SG_Repository
import SG_Messages
import ConfigParser
import SG_Utils

config = ConfigParser.ConfigParser()
config.read("settings.config")

username = config.get("General", "username")
version = config.get("General", "version")

logger_name = 'admin_handler'

# create our Reddit instance
c_id = config.get("General", "client_id")
c_secret = config.get("General", "client_secret")
user = config.get("General", "plain_username")
pw = config.get("General", "password")

reddit = praw.Reddit(
    client_id = c_id,
    client_secret = c_secret,
    username = user,
    password = pw,
    user_agent = 'Dealer bot v{} by /u/eganwall'.format(version)
)

# initialize our repository and logger
sg_repo = SG_Repository.Repository()
logger = SG_Utils.LogUtility()

# get our messaging classes
error_messages = SG_Messages.ErrorMessages
reply_messages = SG_Messages.ReplyMessages

def handle_message(ch, method, properties, body):
    start_time = time.time()

    message = json.loads(body)

    # get the comment instance so we can reply to it
    comment = reddit.comment(message['comment_id'])

    comment_tokens = comment.body.strip().split(' ')
    if comment_tokens[0].lower() == '!deposit' and comment_tokens[1].isnumeric():
        player_username = comment.parent().author.name
        add_amount = int(comment_tokens[1])
        #print('Adding {} points to /u/{}\'s account...'.format(add_amount, player_username))

        player_dto = sg_repo.GET_PLAYER_BY_USERNAME(player_username)
        new_balance = player_dto['balance'] + add_amount

        #print('/u/{}\'s new balance is {}\n\n'.format(player_username, new_balance))
        sg_repo.UPDATE_PLAYER_BALANCE_BY_USERNAME(player_username, new_balance)

        SG_Utils.update_player_flair(player_username, new_balance, player_dto['flair_css_class'])

        reddit.redditor('eganwall').message('Deposit successful',
                                            'Successfully deposited {} for /u/{}'.format(add_amount, player_username))
        logger.log_info_message(message['message_id'], SG_Utils.LogUtilityConstants.deposit_success_event,
                                logger_name, '[new_balance={}]'.format(new_balance))

    ch.basic_ack(delivery_tag=method.delivery_tag)
    logger.log_info_message(message['message_id'], SG_Utils.LogUtilityConstants.handler_finished_event,
                            logger_name, 'Handler finished fulfilling request : [comment_id={}] [elapsed_seconds={:.3f}] [processing_time={:.3f}]'.format(
                                message['comment_id'],
                                SG_Utils.get_elapsed_secs(comment.created_utc, time.time()),
                                SG_Utils.get_elapsed_secs(start_time, time.time())))

def safe_handle(ch, method, properties, body):
    try:
        handle_message(ch, method, properties, body)
    except Exception as e:
        message = json.loads(body)
        logger.log_error_message(message['message_id'], SG_Utils.LogUtilityConstants.exception_event,
                                 logger_name, traceback.format_exc() + "=== END OF STACK TRACE")
        ch.basic_ack(delivery_tag=method.delivery_tag)

connection = pika.BlockingConnection(pika.ConnectionParameters('localhost', heartbeat_interval=0))
channel = connection.channel()

channel.queue_declare(queue='admin', durable=True)

channel.basic_consume(safe_handle,
                      queue='admin')

log_msg = "ADMIN_TOOL handler started up - waiting for messages..."
logger.log_info_message('', SG_Utils.LogUtilityConstants.handler_startup_event, logger_name, log_msg)

channel.start_consuming()