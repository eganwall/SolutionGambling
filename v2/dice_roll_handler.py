import json
import traceback
import pika
import praw
import time
import SG_Repository
import SG_Messages
import ConfigParser
from random import randint
import SG_Utils

config = ConfigParser.ConfigParser()
config.read("settings.config")
config_header = "DiceRoll"

username = config.get("General", "username")
version = config.get("General", "version")
starting_balance = int(config.get("General", "starting_balance"))
max_bet = int(config.get(config_header, "bet_limit"))
payout_factor = int(config.get(config_header, "payout_factor"))
game_type = '6-9 Dice'
logger_name = 'dice_roll_handler'

def format_wager_reply(username, wager_amount, roll_1, roll_2, total, outcome,
                       winnings, new_balance):
    return reply_messages.DICE_ROLL_SUCCESS_MSG.format(username,
                                                       wager_amount,
                                                       roll_1,
                                                       roll_2,
                                                       total,
                                                       outcome,
                                                       winnings,
                                                       new_balance)

def roll_die():
    roll = randint(1, 6)
    #print("Die roll result: {}".format(roll))
    return roll

def parse_post_for_wager(post_body, player_balance):
    body_tokens = post_body.strip().split(' ')

    if len(body_tokens) > 1 and str(body_tokens[0]) == 'wager' and (body_tokens[1].isnumeric() or body_tokens[1] == 'max'):
        if body_tokens[1] == 'max':
            return min(player_balance, max_bet)
        else:
            return int(body_tokens[1])

    return 0

def play_3_6_9(wager_amount):
    roll_1 = roll_die()
    roll_2 = roll_die()

    if (roll_1 + roll_2 == 6) or (roll_1 + roll_2 == 9) or (roll_1 + roll_2 == 3):
        outcome = SG_Repository.WagerOutcome.WIN
        winnings = wager_amount * payout_factor
    else:
        outcome = SG_Repository.WagerOutcome.LOSE
        winnings = 0

    wager_result = {'roll_1' : roll_1, 'roll_2' : roll_2, 'outcome' : outcome,
                    'winnings' : winnings, 'roll_total' : (roll_1 + roll_2)}

    # print("6-9 wager result:")
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
    # print("Received message : [body = {}]".format(body))

    # get the comment instance so we can reply to it
    comment = reddit.comment(message['comment_id'])

    # get the player from the DB so we can validate their wager
    # and update their balance
    player = sg_repo.GET_PLAYER_BY_USERNAME(message['username'])

    # create new player if this account hasn't played before
    if player is None:
        SG_Utils.add_new_player(comment.author.name, message['message_id'])
        player = sg_repo.GET_PLAYER_BY_USERNAME(comment.author.name)

    # process the comment for the wager amount
    wager_amount = parse_post_for_wager(message['comment_body'], player['balance'])
    logger.log_info_message(message['message_id'], SG_Utils.LogUtilityConstants.wager_validated_event,
                            logger_name, '[wager_amount={}] [game_type={}]'.format(wager_amount, game_type))

    if wager_amount <= 0:
        # print("Wager amount not valid")
        SG_Utils.post_comment_reply(comment, error_messages.DICE_ROLL_ERROR_MSG, message['message_id'])
        ch.basic_ack(delivery_tag=method.delivery_tag)
        logger.log_info_message(message['message_id'], SG_Utils.LogUtilityConstants.wager_rejected_event,
                                logger_name, '[rejected_reason={}] [comment_id={}] [elapsed_seconds={:.3f}]'.format(
                                    SG_Utils.LogUtilityConstants.incorrect_format_reason, message['comment_id'],
                                    SG_Utils.get_elapsed_secs(comment.created_utc, time.time())))
        return

    if wager_amount > player['balance']:
        # print("Player wagered more than their balance")
        SG_Utils.post_comment_reply(comment, error_messages.INSUFFICIENT_BALANCE_ERROR_MSG, message['message_id'])
        ch.basic_ack(delivery_tag=method.delivery_tag)
        logger.log_info_message(message['message_id'], SG_Utils.LogUtilityConstants.wager_rejected_event,
                                logger_name, '[rejected_reason={}] [comment_id={}] [elapsed_seconds={:.3f}]'.format(
                                    SG_Utils.LogUtilityConstants.insufficient_balance_reason, message['comment_id'],
                                    SG_Utils.get_elapsed_secs(comment.created_utc, time.time())))
        return

    if wager_amount > max_bet:
        # print("Player wagered more than this game's max bet")
        SG_Utils.post_comment_reply(comment, error_messages.OVER_MAX_BET_ERROR_MSG.format(max_bet), message['message_id'])
        ch.basic_ack(delivery_tag=method.delivery_tag)
        logger.log_info_message(message['message_id'], SG_Utils.LogUtilityConstants.wager_rejected_event,
                                logger_name, '[rejected_reason={}] [comment_id={}] [elapsed_seconds={:.3f}]'.format(
                                    SG_Utils.LogUtilityConstants.over_max_bet_reason, message['comment_id'],
                                    SG_Utils.get_elapsed_secs(comment.created_utc, time.time())))
        return

    wager_result = play_3_6_9(wager_amount)
    new_player_balance = player['balance'] - wager_amount + wager_result['winnings']

    sg_repo.INSERT_WAGER(player['username'], wager_result['outcome'],
                         wager_amount, wager_result['winnings'], new_player_balance, game_type)
    SG_Utils.update_player_after_wager(player['username'], new_player_balance, player['flair_css_class'], message['message_id'])

    reply = format_wager_reply(player['username'], wager_amount, wager_result['roll_1'],
                               wager_result['roll_2'], wager_result['roll_total'],
                               wager_result['outcome'], wager_result['winnings'],
                               new_player_balance)

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

channel.queue_declare(queue='dice_roll', durable=True)

channel.basic_consume(safe_handle,
                      queue='dice_roll')

log_msg = "DICE_ROLL handler started up - waiting for messages..."
logger.log_info_message('', SG_Utils.LogUtilityConstants.handler_startup_event,
                        logger_name, log_msg)

channel.start_consuming()