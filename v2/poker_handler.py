import json
import traceback
import time
import deuces
import pika
import praw
import SG_Repository
import SG_Messages
import ConfigParser
import SG_Utils

config = ConfigParser.ConfigParser()
config.read("settings.config")
config_header = "Poker"

username = config.get("General", "username")
version = config.get("General", "version")
starting_balance = int(config.get("General", "starting_balance"))
max_bet = int(config.get(config_header, "bet_limit"))
payout_table = {
    0 : 45000,
    1 : 4000,
    2 : 600,
    3 : 55,
    4 : 25,
    5 : 10,
    6 : 5,
    7 : 2,
    8 : 0,
    9 : 0
}
game_type = 'High-hand Poker'
logger_name = 'poker_handler'

def format_wager_reply(username, wager_amount, hand_string, board_string, hand_type, outcome,
                       winnings, new_balance):
    return reply_messages.POKER_SUCCESS_MSG.format(username,
                                                   wager_amount,
                                                   hand_string,
                                                   board_string,
                                                   hand_type,
                                                   winnings,
                                                   new_balance)

def send_royal_message(comment_id):
    reddit.redditor('eganwall').message('ROYAL FLUSH BABY', 'SOMEONE HIT A ROYAL! Look here : {}'.format(str(comment_id)))

def deal_hand():
    deck = deuces.Deck()
    board = deck.draw(5)
    hand = deck.draw(2)
    # print("Dealing hand: ")
    # for current_card in hand:
    #     card.print_pretty_card(current_card)
    # print("Dealing board: ")
    # for current_card in board:
    #     card.print_pretty_card(current_card)
    return {'board' : board, 'hand' : hand}

def parse_post_for_wager(post_body, player_balance):
    body_tokens = post_body.strip().split(' ')

    if len(body_tokens) > 1 and str(body_tokens[0]) == 'wager' and (body_tokens[1].isnumeric() or body_tokens[1] == 'max'):
        if(body_tokens[1] == 'max'):
            return min(player_balance, max_bet)
        else:
            return int(body_tokens[1])

    return 0

def play_poker(wager_amount, comment_id):
    player_hand = deal_hand()
    hand_score = evaluator.evaluate(cards=player_hand['hand'], board=player_hand['board'])
    hand_class = evaluator.get_rank_class(hand_score)
    hand_class_string = evaluator.class_to_string(hand_class)
    #print("Player hand class : [raw = {}] [string = {}]".format(hand_class, hand_class_string))

    # if we don't have at least 2 pair, we lose
    if(hand_class > 7):
        outcome = SG_Repository.WagerOutcome.LOSE
        winnings = wager_amount * payout_table[hand_class]
    # if they hit a royal flush, pay out the special case big payday
    elif (hand_score == 1):
        outcome = SG_Repository.WagerOutcome.WIN
        winnings = wager_amount * payout_table[0]
        send_royal_message(comment_id)
    else:
        outcome = SG_Repository.WagerOutcome.WIN
        winnings = wager_amount * payout_table[hand_class]

    # build the pretty-printed cards into a string for the dealer reply comment
    full_hand_string = """"""
    for current_card in player_hand['hand']:
        full_hand_string += card.int_to_pretty_str(current_card) + """

"""
    full_board_string = """"""
    for current_card in player_hand['board']:
        full_board_string += card.int_to_pretty_str(current_card) + """

"""

    wager_result = {'hand_type' : hand_class_string, 'full_hand_string' : full_hand_string, 'outcome' : outcome,
                    'winnings' : winnings, 'full_board_string' : full_board_string}

    return wager_result

# create our Reddit instance
c_id = config.get(config_header, "client_id")
c_secret = config.get(config_header, "client_secret")
user = config.get(config_header, "plain_username")
pw = config.get(config_header, "password")

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

# initialize the classes we need to run the poker game
card = deuces.Card()
evaluator = deuces.Evaluator()

def handle_message(ch, method, properties, body):
    # get current time for elapsed time tracking
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

    # now process the comment
    wager_amount = parse_post_for_wager(message['comment_body'], player['balance'])
    logger.log_info_message(message['message_id'], SG_Utils.LogUtilityConstants.wager_validated_event,
                            logger_name, '[wager_amount={}] [game_type={}]'.format(wager_amount, game_type))

    if wager_amount <= 0:
        #print("Wager amount not valid")
        SG_Utils.post_comment_reply(comment, error_messages.POKER_ERROR_MSG, message['message_id'])
        ch.basic_ack(delivery_tag=method.delivery_tag)
        logger.log_info_message(message['message_id'], SG_Utils.LogUtilityConstants.wager_rejected_event,
                                logger_name, '[rejected_reason={}] [comment_id={}] [elapsed_seconds={:.3f}]'.format(
                                    SG_Utils.LogUtilityConstants.incorrect_format_reason, message['comment_id'],
                                    SG_Utils.get_elapsed_secs(comment.created_utc, time.time())))
        return

    if wager_amount > player['balance']:
        #print("Player wagered more than their balance")
        SG_Utils.post_comment_reply(comment, error_messages.INSUFFICIENT_BALANCE_ERROR_MSG, message['message_id'])
        ch.basic_ack(delivery_tag=method.delivery_tag)
        logger.log_info_message(message['message_id'], SG_Utils.LogUtilityConstants.wager_rejected_event,
                                logger_name, '[rejected_reason={}] [comment_id={}] [elapsed_seconds={:.3f}]'.format(
                                    SG_Utils.LogUtilityConstants.insufficient_balance_reason, message['comment_id'],
                                    SG_Utils.get_elapsed_secs(comment.created_utc, time.time())))
        return

    if wager_amount > max_bet:
        #print("Player wagered more than this game's max bet")
        SG_Utils.post_comment_reply(comment, error_messages.OVER_MAX_BET_ERROR_MSG.format(max_bet), message['message_id'])
        ch.basic_ack(delivery_tag=method.delivery_tag)
        logger.log_info_message(message['message_id'], SG_Utils.LogUtilityConstants.wager_rejected_event,
                                logger_name, '[rejected_reason={}] [comment_id={}] [elapsed_seconds={:.3f}]'.format(
                                    SG_Utils.LogUtilityConstants.over_max_bet_reason, message['comment_id'],
                                    SG_Utils.get_elapsed_secs(comment.created_utc, time.time())))
        return

    wager_result = play_poker(wager_amount, comment.id)
    new_player_balance = player['balance'] - wager_amount + wager_result['winnings']

    sg_repo.INSERT_WAGER(player['username'], wager_result['outcome'],
                         wager_amount, wager_result['winnings'], new_player_balance, game_type)
    SG_Utils.update_player_after_wager(player['username'], new_player_balance, player['flair_css_class'], message['message_id'])

    reply = format_wager_reply(player['username'], wager_amount, wager_result['full_hand_string'],
                               wager_result['full_board_string'],
                               wager_result['hand_type'], wager_result['outcome'], wager_result['winnings'],
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

channel.queue_declare(queue='poker', durable=True)

channel.basic_consume(safe_handle,
                      queue='poker')

log_msg = "POKER handler started up - waiting for messages..."
logger.log_info_message('', SG_Utils.LogUtilityConstants.handler_startup_event,
                        logger_name, log_msg)

channel.start_consuming()