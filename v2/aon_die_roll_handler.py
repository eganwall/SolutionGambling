import json
import pika
import praw
import SG_Repository
import SG_Messages
import time
import ConfigParser
import random
import SG_Utils
import traceback

config = ConfigParser.ConfigParser()
config.read("settings.config")

username = config.get("General", "username")
version = config.get("General", "version")
starting_balance = int(config.get("General", "starting_balance"))
game_type = 'AoN Die'
logger_name = 'aon_die_roll_handler'

pay_table = {
    3 : 2,
    4 : 3,
    5 : 4,
    6 : 5
}

def format_wager_reply(username, wager_amount, flip_result, outcome,
                       winnings, new_balance):
    if outcome == SG_Repository.WagerOutcome.WIN:
        return reply_messages.AON_DICE_ROLL_WIN_MSG.format(username, wager_amount, flip_result, new_balance)
    else:
        return reply_messages.AON_DICE_ROLL_LOSE_MSG.format(username, wager_amount, flip_result)

def roll_die():
    roll = random.randint(1, 6)
    # print("Die roll result: {}".format(roll))
    return roll

def parse_post_for_wager(post_body, player_balance):
    body_tokens = post_body.strip().split(' ')

    if str(body_tokens[0]) == 'wager':
        return player_balance

    return -1

def play_dice(wager_amount):
    die_result = roll_die()

    if (die_result > 2):
        outcome = SG_Repository.WagerOutcome.WIN
        winnings = wager_amount * pay_table[die_result]
    else:
        outcome = SG_Repository.WagerOutcome.LOSE
        winnings = 0

    wager_result = {'die_roll_result' : die_result, 'outcome' : outcome,
                    'winnings' : winnings}

    # print("All-or-nothing die roll wager result:")
    # pprint.pprint(wager_result)

    return wager_result

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

    # get the player from the DB so we can validate their wager
    # and update their balance
    player = sg_repo.GET_PLAYER_BY_USERNAME(comment.author.name)

    # create new player if this account hasn't played before
    if player is None:
        SG_Utils.add_new_player(comment.author.name, message['message_id'])
        player = sg_repo.GET_PLAYER_BY_USERNAME(comment.author.name)

    wager_amount = parse_post_for_wager(message['comment_body'], player['balance'])
    logger.log_info_message(message['message_id'], SG_Utils.LogUtilityConstants.wager_validated_event,
                            logger_name, '[wager_amount={}] [game_type={}]'.format(wager_amount, game_type))

    if wager_amount == 0:
        # print("Player has no balance")
        SG_Utils.post_comment_reply(comment, error_messages.AON_DICE_ROLL_NO_BALANCE_ERROR_MSG.format(player['username'], message['message_id']))
        ch.basic_ack(delivery_tag=method.delivery_tag)
        logger.log_info_message(message['message_id'], SG_Utils.LogUtilityConstants.wager_rejected_event,
                                logger_name, '[rejected_reason={}] [comment_id={}] [elapsed_seconds={:.3f}]'.format(
                                    SG_Utils.LogUtilityConstants.insufficient_balance_reason, message['comment_id'],
                                    SG_Utils.get_elapsed_secs(comment.created_utc, time.time())))
        return

    if wager_amount == -1:
        # print("Player triggered bot incorrectly")
        SG_Utils.post_comment_reply(comment, error_messages.AON_DICE_ROLL_ERROR_MSG.format(player['username'], message['message_id']))
        ch.basic_ack(delivery_tag=method.delivery_tag)
        logger.log_info_message(message['message_id'], SG_Utils.LogUtilityConstants.wager_rejected_event,
                                logger_name, '[rejected_reason={}] [comment_id={}] [elapsed_seconds={:.3f}]'.format(
                                    SG_Utils.LogUtilityConstants.incorrect_format_reason, message['comment_id'],
                                    SG_Utils.get_elapsed_secs(comment.created_utc, time.time())))
        return

    wager_result = play_dice(wager_amount)
    new_player_balance = player['balance'] - wager_amount + wager_result['winnings']

    sg_repo.INSERT_WAGER(player['username'], wager_result['outcome'],
                         wager_amount, wager_result['winnings'], new_player_balance, game_type)
    SG_Utils.update_player_after_wager(player['username'], new_player_balance, player['flair_css_class'], message['message_id'])

    reply = format_wager_reply(player['username'], wager_amount, wager_result['die_roll_result'],
                               wager_result['outcome'], wager_result['winnings'], new_player_balance)

    logger.log_info_message(message['message_id'], SG_Utils.LogUtilityConstants.wager_executed_event,
                            logger_name, '[outcome={}] [new_balance={}]'.format(wager_result['outcome'], new_player_balance))

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

channel.queue_declare(queue='aon_die', durable=True)

channel.basic_consume(safe_handle,
                      queue='aon_die')

log_msg = "ALL_OR_NOTHING_DICE handler started up - waiting for messages..."
logger.log_info_message('', SG_Utils.LogUtilityConstants.handler_startup_event,
                        logger_name, log_msg)
channel.start_consuming()