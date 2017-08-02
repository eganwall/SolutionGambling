import json
import traceback
import pika
import praw
import time
import SG_Repository
import SG_Messages
import ConfigParser
import SG_Utils

flair_table = {
    1 : {'cost' : 50000, 'css_class' : 'lvl1'},
    2 : {'cost' : 500000, 'css_class' : 'lvl2'},
    3 : {'cost' : 1000000, 'css_class' : 'lvl3'},
    4 : {'cost' : 2000000, 'css_class' : 'lvl4'},
    5 : {'cost' : 10000000, 'css_class' : 'lvl5'},
    6 : {'cost' : 50000000, 'css_class' : 'lvl6'},
    7 : {'cost' : 100000000, 'css_class' : 'lvl7'},
    8 : {'cost' : 500000000, 'css_class' : 'lvl8'},
    9 : {'cost' : 1000000000, 'css_class' : 'lvl9'},
    10 : {'cost' : 5000000000, 'css_class' : 'lvl10'},
    11 : {'cost' : 10000000000, 'css_class' : 'lvl11'},
    12 : {'cost' : 25000000000, 'css_class' : 'lvl12'},
    13 : {'cost' : 50000000000, 'css_class' : 'lvl13'},
    14 : {'cost' : 75000000000, 'css_class' : 'lvl14'},
    15 : {'cost' : 100000000000, 'css_class' : 'lvl15'},
    16 : {'cost' : 250000000000, 'css_class' : 'lvl16'},
    17 : {'cost' : 500000000000, 'css_class' : 'lvl17'},
    18 : {'cost' : 1000000000000, 'css_class' : 'lvl18'},
    19 : {'cost' : 5000000000000, 'css_class' : 'lvl19'},
    20 : {'cost' : 10000000000000, 'css_class' : 'lvl20'},
    21 : {'cost' : 100000000000000, 'css_class' : 'lvl21'},
    22 : {'cost' : 0, 'css_class' : ''}
}

config = ConfigParser.ConfigParser()
config.read("settings.config")

username = config.get("General", "username")
version = config.get("General", "version")
starting_balance = int(config.get("General", "starting_balance"))
logger_name = 'flair_shop_handler'

def is_requesting_purchase(post_body):
    body_tokens = post_body.strip().split(' ')

    if str(body_tokens[0]) == 'upgrade':
        return True

    return False

def update_player_after_purchase(username, new_balance, flair_level, flair_class):
    sg_repo.UPDATE_PLAYER_FLAIR_BY_USERNAME(username, flair_level, flair_class)
    SG_Utils.update_player_after_wager(username, new_balance, flair_class)

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
constants = SG_Messages.MiscConstants

def handle_message(ch, method, properties, body):
    start_time = time.time()

    message = json.loads(body)

    # get the comment instance so we can reply to it
    comment = reddit.comment(message['comment_id'])

    # get the player from the DB so we can validate their purchase and update them
    player = sg_repo.GET_PLAYER_BY_USERNAME(comment.author.name)

    # create new player if this account hasn't played before
    if player is None:
        SG_Utils.add_new_player(comment.author.name, message['message_id'])
        player = sg_repo.GET_PLAYER_BY_USERNAME(comment.author.name)

    # now process the comment - first we convert it to lower
    post_body_lower = comment.body.lower()

    if (is_requesting_purchase(post_body_lower)):
        target_flair_level = player['flair_level'] + 1
        log_msg = "/u/{} is requesting upgrade to level {}".format(player['username'], target_flair_level)

        logger.log_info_message(message['message_id'], SG_Utils.LogUtilityConstants.flair_req_event,
                                logger_name, log_msg)

        target_flair = flair_table[target_flair_level]

        if target_flair_level == len(flair_table):
            logger.log_info_message(message['message_id'], SG_Utils.LogUtilityConstants.flair_rejected_event,
                                    logger_name, '[rejected_reason={}] [comment_id={}] [elapsed_seconds={:.3f}]'.format(
                                    SG_Utils.LogUtilityConstants.max_flair_level_reason, message['comment_id'],
                                    SG_Utils.get_elapsed_secs(comment.created_utc, time.time())))
            reply = error_messages.FLAIR_SHOP_ALREADY_MAX_LEVEL.format(player['username'])
        elif player['balance'] < target_flair['cost']:
            cost_str = "[flair_cost={}]".format(target_flair['cost'])

            logger.log_info_message(message['message_id'], SG_Utils.LogUtilityConstants.flair_rejected_event,
                                    logger_name, '[rejected_reason={}] [comment_id={}] [elapsed_seconds={:.3f}] {}'.format(
                                    SG_Utils.LogUtilityConstants.insufficient_balance_reason, message['comment_id'],
                                    SG_Utils.get_elapsed_secs(comment.created_utc, time.time()), cost_str))

            reply = error_messages.FLAIR_SHOP_INSUFFICIENT_BALANCE_ERROR_MSG.format(player['username'],
                                                                                    target_flair_level,
                                                                                    target_flair['cost'],
                                                                                    player['balance'])
        else:
            new_flair_css_class = target_flair['css_class']
            new_player_balance = player['balance'] - target_flair['cost']

            logger.log_info_message(message['message_id'], SG_Utils.LogUtilityConstants.flair_executed_event,
                                    logger_name, '[new_balance={}]'.format(new_player_balance))

            update_player_after_purchase(player['username'], new_player_balance, target_flair_level,
                                         new_flair_css_class)
            reply = reply_messages.FLAIR_SHOP_SUCCESS_MSG.format(player['username'], target_flair_level,
                                                                 target_flair['cost'], new_player_balance)

        SG_Utils.post_comment_reply(comment, reply, message['message_id'])


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

channel.queue_declare(queue='flair_shop', durable=True)

channel.basic_consume(safe_handle,
                      queue='flair_shop')

log_msg = "FLAIR_SHOP handler started up - waiting for messages..."
logger.log_info_message('', SG_Utils.LogUtilityConstants.handler_startup_event, logger_name, log_msg)

channel.start_consuming()