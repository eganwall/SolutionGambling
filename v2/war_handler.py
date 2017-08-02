import json
import traceback
import deuces
import math
import pika
import praw
import time
import SG_Repository
import SG_Messages
import ConfigParser
import SG_Utils

config = ConfigParser.ConfigParser()
config.read("settings.config")
config_header = "CasinoWar"

username = config.get("General", "username")
version = config.get("General", "version")
starting_balance = int(config.get("General", "starting_balance"))
small_bet = int(config.get(config_header, "small_bet"))
mid_bet = int(config.get(config_header, "mid_bet"))
big_bet = int(config.get(config_header, "big_bet"))

game_type = 'Casino War'
logger_name = 'war_handler'

def format_wager_reply(username, wager_amount, player_card, player_war_card,
                       dealer_card, dealer_war_card, outcome, winnings, new_balance):
    reply_template = SG_Messages.ReplyMessages.CASINO_WAR_REPLY_WRAPPER_TEMPLATE_MSG
    reply_body = ""

    first_draw_results = SG_Messages.ReplyMessages.CASINO_WAR_BODY_TEMPLATE.format(player_card, dealer_card)
    reply_body += first_draw_results

    if player_war_card != '':
        # if we went to war, include the war results
        reply_body += """

&nbsp;

***Going to war!***

"""
        war_results = SG_Messages.ReplyMessages.CASINO_WAR_BODY_TEMPLATE.format(player_war_card, dealer_war_card)
        reply_body += war_results

    return reply_template.format(username, wager_amount, reply_body, outcome, winnings, winnings - wager_amount, new_balance)

def parse_post_for_wager(post_body, player_balance):
    body_tokens = post_body.strip().split(' ')

    if len(body_tokens) > 1 and str(body_tokens[0]) == 'wager':
        if body_tokens[1] == 'big':
            return big_bet
        elif body_tokens[1] == 'mid':
            return mid_bet
        elif body_tokens[1] == 'small':
            return small_bet

    return 0

def evaluate_win(player_card, dealer_card):
    return card.get_rank_int(player_card) - card.get_rank_int(dealer_card)

def calculate_winnings(result_diff, wager_amount, war = False):
    if war:
        if result_diff > 0:
            value = math.trunc(wager_amount * 1.5)
            return value
        elif result_diff < 0:
            return 0
        else:
            return wager_amount * 3
    else:
        if result_diff > 0:
            return wager_amount * 2
        else:
            return 0

def play_war(wager_amount):
    deck = deuces.Deck()

    player_card = deck.draw(1)
    dealer_card = deck.draw(1)

    player_war_card = ''
    dealer_war_card = ''

    # evaluate the difference of the player and dealer cards
    result = evaluate_win(player_card, dealer_card)
    if result > 0:
        winnings = calculate_winnings(result, wager_amount, False)
        outcome = SG_Repository.WagerOutcome.WIN
    elif result < 0:
        winnings = calculate_winnings(result, wager_amount, False)
        outcome = SG_Repository.WagerOutcome.LOSE
    else:
        player_war_card = deck.draw(1)
        dealer_war_card = deck.draw(1)

        war_result = evaluate_win(player_war_card, dealer_war_card)
        if war_result > 0:
            winnings = calculate_winnings(war_result, wager_amount, True)
            outcome = SG_Repository.WagerOutcome.WIN
        elif war_result < 0:
            winnings = calculate_winnings(war_result, wager_amount, True)
            outcome = SG_Repository.WagerOutcome.LOSE
        else:
            winnings = calculate_winnings(war_result, wager_amount, True)
            outcome = SG_Repository.WagerOutcome.WIN

        player_war_card = card.int_to_pretty_str(player_war_card)
        dealer_war_card = card.int_to_pretty_str(dealer_war_card)

    wager_result = {'player_card' : card.int_to_pretty_str(player_card), 'dealer_card' : card.int_to_pretty_str(dealer_card), 'outcome' : outcome,
                    'winnings' : winnings, 'player_war_card' : player_war_card, 'dealer_war_card' : dealer_war_card}

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

card = deuces.Card()

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

    if wager_amount <= 0:
        # print("Wager amount not valid")
        SG_Utils.post_comment_reply(comment, error_messages.WAR_ERROR_MSG.format(player['username']), message['message_id'])
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

    wager_result = play_war(wager_amount)
    new_player_balance = player['balance'] - wager_amount + wager_result['winnings']

    sg_repo.INSERT_WAGER(player['username'], wager_result['outcome'],
                         wager_amount, wager_result['winnings'], new_player_balance, game_type)
    SG_Utils.update_player_after_wager(player['username'], new_player_balance, player['flair_css_class'], message['message_id'])

    reply = format_wager_reply(player['username'], wager_amount, wager_result['player_card'],
                               wager_result['player_war_card'], wager_result['dealer_card'],
                               wager_result['dealer_war_card'], wager_result['outcome'],
                               wager_result['winnings'], new_player_balance)

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

channel.queue_declare(queue='war', durable=True)

channel.basic_consume(safe_handle,
                      queue='war')

log_msg = "WAR handler started up - waiting for messages..."
logger.log_info_message('', SG_Utils.LogUtilityConstants.handler_startup_event,
                        logger_name, log_msg)

channel.start_consuming()