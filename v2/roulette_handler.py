import json
import math
import traceback

import pika
import praw
import time

import SG_Repository
import SG_Messages
import pprint
import ConfigParser
import random
import SG_Utils

config = ConfigParser.ConfigParser()
config.read("settings.config")
config_header = "Roulette"

username = config.get("General", "username")
version = config.get("General", "version")
starting_balance = int(config.get("General", "starting_balance"))
max_bet = int(config.get(config_header, "bet_limit"))

payout_table = {
    'parity' : 2,
    'color' : 2,
    'number' : 37,
    'dozen' : 3
}

roulette_list = [
    {'value' : 1, 'color' : 'red'},
    {'value' : 2, 'color' : 'black'},
    {'value' : 3, 'color' : 'red'},
    {'value' : 4, 'color' : 'black'},
    {'value' : 5, 'color' : 'red'},
    {'value' : 6, 'color' : 'black'},
    {'value' : 7, 'color' : 'red'},
    {'value' : 8, 'color' : 'black'},
    {'value' : 9, 'color' : 'red'},
    {'value' : 10, 'color' : 'black'},
    {'value' : 11, 'color' : 'black'},
    {'value' : 12, 'color' : 'red'},
    {'value' : 13, 'color' : 'black'},
    {'value' : 14, 'color' : 'red'},
    {'value' : 15, 'color' : 'black'},
    {'value' : 16, 'color' : 'red'},
    {'value' : 17, 'color' : 'black'},
    {'value' : 18, 'color' : 'red'},
    {'value' : 19, 'color' : 'red'},
    {'value' : 20, 'color' : 'black'},
    {'value' : 21, 'color' : 'red'},
    {'value' : 22, 'color' : 'black'},
    {'value' : 23, 'color' : 'red'},
    {'value' : 24, 'color' : 'black'},
    {'value' : 25, 'color' : 'red'},
    {'value' : 26, 'color' : 'black'},
    {'value' : 27, 'color' : 'red'},
    {'value' : 28, 'color' : 'black'},
    {'value' : 29, 'color' : 'black'},
    {'value' : 30, 'color' : 'red'},
    {'value' : 31, 'color' : 'black'},
    {'value' : 32, 'color' : 'red'},
    {'value' : 33, 'color' : 'black'},
    {'value' : 34, 'color' : 'red'},
    {'value' : 35, 'color' : 'black'},
    {'value' : 36, 'color' : 'red'},
    {'value' : 0, 'color' : 'green'},
]

game_type = 'Roulette'
logger_name = 'roulette_handler'

def spin_roulette():
    result = random.choice(roulette_list)
    return result

def parse_individual_wager(wager_text, current_balance):
    base_result = {'wager_amount' : 0, 'wager_type' : '', 'wager_value' : '', 'balance_after' : current_balance, 'error_msg' : ''}

    split_text = wager_text.strip().split(' ')

    if len(split_text) != 3 or split_text[0] != 'wager' or not split_text[1].isnumeric():
        base_result['error_msg'] = error_messages.ROULETTE_WAGER_FORMAT_ERROR_MSG.format(wager_text.strip())
        return base_result

    if int(split_text[1]) > current_balance:
        base_result['error_msg'] = error_messages.ROULETTE_WAGER_INSUFFICIENT_BALANCE_ERROR_MSG.format(wager_text.strip())
        return base_result

    if int(split_text[1]) > max_bet:
        base_result['error_msg'] = error_messages.ROULETTE_WAGER_OVER_MAX_ERROR_MSG.format(wager_text.strip())
        return base_result

    # determine what the player is actually betting on
    if split_text[2].isnumeric() and int(split_text[2]) <= 36 and int(split_text[2]) >= 0:
        wager_type = 'number'
        wager_value = int(split_text[2])
    elif split_text[2] == 'even' or split_text[2] == 'odd':
        wager_type = 'parity'
        wager_value = split_text[2]
    elif split_text[2] == 'red' or split_text[2] == 'black':
        wager_type = 'color'
        wager_value = split_text[2]
    else:
        base_result['error_msg'] = error_messages.ROULETTE_WAGER_FORMAT_ERROR_MSG.format(wager_text.strip())
        return base_result

    result = base_result
    result['wager_amount'] = int(split_text[1])
    result['wager_type'] = wager_type
    result['wager_value'] = wager_value
    result['balance_after'] = current_balance - int(split_text[1])

    return result

def determine_outcome(wager, roulette_result):
    # if there was something wrong parsing this wager, return the error
    if wager['error_msg'] != '':
        return wager['error_msg']

    if wager['wager_type'] == 'parity':
        if wager['wager_value'] == 'even' and roulette_result['value'] is not 0 and (
                roulette_result['value'] % 2 == 0):  # ewwww
            return SG_Repository.WagerOutcome.WIN
        elif wager['wager_value'] == 'odd' and roulette_result['value'] is not 0 and (
                roulette_result['value'] % 2 == 1):  # ewwww again
            return SG_Repository.WagerOutcome.WIN
        else:
            return SG_Repository.WagerOutcome.LOSE

    if wager['wager_type'] == 'color':
        if wager['wager_value'] == roulette_result['color']:
            return SG_Repository.WagerOutcome.WIN
        else:
            return SG_Repository.WagerOutcome.LOSE

    if wager['wager_type'] == 'number':
        if wager['wager_value'] == roulette_result['value']:
            return SG_Repository.WagerOutcome.WIN
        else:
            return SG_Repository.WagerOutcome.LOSE

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

    # now process the comment - first we convert it to lower
    post_body_lower = comment.body.lower()

    # parse the post for wagers
    remaining_balance = player['balance']
    player_wagers = list()
    for line in post_body_lower.splitlines():
        new_wager = parse_individual_wager(line, remaining_balance)
        player_wagers.append(new_wager)
        remaining_balance = new_wager['balance_after']

        logger.log_info_message(message['message_id'], SG_Utils.LogUtilityConstants.wager_validated_event,
                            logger_name, '[wager_type={}] [wager_value={}] [wager_amount={}] [game_type={}]'.format(
                                new_wager['wager_type'], new_wager['wager_value'], new_wager['wager_amount'], game_type))

    # execute the ADVANCED ROULETTE SIMULATION
    roulette_result = spin_roulette()

    # analyze the results
    total_winnings = 0
    total_wagered = 0
    wager_results_string = """"""
    for index, wager in enumerate(player_wagers):
        outcome = determine_outcome(wager, roulette_result)

        if outcome == SG_Repository.WagerOutcome.WIN:
            wager_winnings = math.trunc(wager['wager_amount'] * payout_table[wager['wager_type']])
            wager_string = SG_Messages.ReplyMessages.ROULETTE_INDIVIDUAL_WAGER_TEMPLATE_MSG.format(
                index + 1, wager['wager_amount'], wager['wager_value'], outcome, wager_winnings
            )

            new_player_balance = player['balance'] - wager['wager_amount'] + wager_winnings
            sg_repo.INSERT_WAGER(player['username'], outcome, wager['wager_amount'], wager_winnings,
                                 new_player_balance, game_type)
            total_wagered += wager['wager_amount']

            logger.log_info_message(message['message_id'], SG_Utils.LogUtilityConstants.wager_executed_event,
                                    logger_name, '[outcome={}] [new_balance={}]'.format(outcome, new_player_balance))
        elif outcome == SG_Repository.WagerOutcome.LOSE:
            wager_winnings = 0
            wager_string = SG_Messages.ReplyMessages.ROULETTE_INDIVIDUAL_WAGER_TEMPLATE_MSG.format(
                index + 1, wager['wager_amount'], wager['wager_value'], outcome, wager_winnings
            )

            new_player_balance = player['balance'] - wager['wager_amount'] + wager_winnings
            sg_repo.INSERT_WAGER(player['username'], outcome, wager['wager_amount'], wager_winnings,
                                 new_player_balance, game_type)
            total_wagered += wager['wager_amount']

            logger.log_info_message(message['message_id'], SG_Utils.LogUtilityConstants.wager_executed_event,
                                    logger_name, '[outcome={}] [new_balance={}]'.format(outcome, new_player_balance))
        else:
            wager_winnings = 0
            wager_string = """Wager {}: """.format(index + 1) + wager['error_msg'] + """

&nbsp;

"""
            logger.log_info_message(message['message_id'], SG_Utils.LogUtilityConstants.wager_rejected_event,
                                    logger_name, '[rejected_reason={}] [comment_id={}] [elapsed_seconds={:.3f}]'.format(
                                        wager['error_msg'], message['comment_id'],
                                        SG_Utils.get_elapsed_secs(comment.created_utc, time.time())))
        total_winnings += wager_winnings
        wager_results_string += wager_string

    # calculate the new balance after all of the bets are executed
    new_player_balance = player['balance'] - total_wagered + total_winnings

    # update the player's balance
    SG_Utils.update_player_after_wager(player['username'], new_player_balance, player['flair_css_class'], message['message_id'])
    updated_player = sg_repo.GET_PLAYER_BY_USERNAME(player['username'])

    # format and send the reply
    reply = SG_Messages.ReplyMessages.ROULETTE_REPLY_WRAPPER_TEMPLATE_MSG.format(
        updated_player['username'], roulette_result['value'], roulette_result['color'].upper(),
        wager_results_string, total_wagered, total_winnings, (total_winnings - total_wagered),
        updated_player['balance']
    )

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

channel.queue_declare(queue='roulette', durable=True)

channel.basic_consume(safe_handle,
                      queue='roulette')

log_msg = "ROULETTE handler started up - waiting for messages..."
logger.log_info_message('', SG_Utils.LogUtilityConstants.handler_startup_event,
                        logger_name, log_msg)

channel.start_consuming()