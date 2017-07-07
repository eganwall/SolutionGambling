import praw
import SG_Repository
import SG_Messages
import pprint
import time
import deuces
import ConfigParser

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

def format_wager_reply(username, wager_amount, hand_string, board_string, hand_type, outcome,
                       winnings, new_balance):
    return reply_messages.POKER_SUCCESS_MSG.format(username,
                                                   wager_amount,
                                                   hand_string,
                                                   board_string,
                                                   hand_type,
                                                   winnings,
                                                   new_balance)

def update_player_after_wager(username, new_balance, flair_class):
    sg_repo.UPDATE_PLAYER_BALANCE_BY_USERNAME(username, new_balance)
    update_player_flair(username, new_balance, flair_class)

def update_player_flair(player, flair, flair_class):
    print('Updating flair : [player = {}], [flair = {}], [class = {}]'.format(player, flair, flair_class))

    if(player == 'eganwall'):
        subreddit.flair.set(player, "Pit Boss : {:,}".format(flair), flair_class)
    else:
        subreddit.flair.set(player, "{}{:,}".format(constants.FLAIR_TIER_TITLES[flair_class], flair), flair_class)

def deal_hand():
    deck = deuces.Deck()
    board = deck.draw(5)
    hand = deck.draw(2)
    print("Dealing hand: ")
    for current_card in hand:
        card.print_pretty_card(current_card)
    print("Dealing board: ")
    for current_card in board:
        card.print_pretty_card(current_card)
    return {'board' : board, 'hand' : hand}

def parse_post_for_wager(post_body, player_balance):
    body_tokens = post_body.strip().split(' ')

    if str(body_tokens[0]) == 'wager' and (body_tokens[1].isnumeric() or body_tokens[1] == 'max'):
        if(body_tokens[1] == 'max'):
            return min(player_balance, max_bet)
        else:
            return int(body_tokens[1])

    return 0

def play_poker(wager_amount):
    player_hand = deal_hand()
    hand_score = evaluator.evaluate(cards=player_hand['hand'], board=player_hand['board'])
    hand_class = evaluator.get_rank_class(hand_score)
    hand_class_string = evaluator.class_to_string(hand_class)
    print("Player hand class : [raw = {}] [string = {}]".format(hand_class, hand_class_string))

    # if we don't have at least 2 pair, we lose
    if(hand_class > 7):
        outcome = SG_Repository.WagerOutcome.LOSE
        winnings = wager_amount * payout_table[hand_class]
    # if they hit a royal flush, pay out the special case big payday
    elif (hand_score == 1):
        outcome = SG_Repository.WagerOutcome.WIN
        winnings = wager_amount * payout_table[0]
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

    print("Poker wager result:")
    pprint.pprint(wager_result)

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

# initialize our repository
sg_repo = SG_Repository.Repository()

# get our messaging classes
error_messages = SG_Messages.ErrorMessages
reply_messages = SG_Messages.ReplyMessages
constants = SG_Messages.MiscConstants

# initialize the classes we need to run the poker game
card = deuces.Card()
evaluator = deuces.Evaluator()

# set our subreddit so that we can do mod stuff like edit flairs
subreddit = reddit.subreddit('solutiongambling')

def bot_loop():
    # get the Submission object for our poker thread
    submission = reddit.submission(id='6kcnvc')

    submission.comment_sort = 'new'
    # submission.comments.replace_more(limit=0)
    for comment in list(submission.comments):
        # if we haven't processed this comment yet, make a new record for it and
        # process it
        if sg_repo.GET_COMMENT_BY_ID(comment.id) is None:
            sg_repo.INSERT_COMMENT_ID(comment.id)

            # if this player hasn't commented on the sub yet, make sure we
            # create a record of them, update their flair, and send them the
            # welcome PM
            if sg_repo.GET_PLAYER_BY_USERNAME(comment.author.name) is None:
                sg_repo.INSERT_PLAYER(comment.author.name, starting_balance)
                update_player_flair(comment.author.name, starting_balance, '')
                reddit.redditor(comment.author.name).message('Welcome!',
                                                             reply_messages.NEW_PLAYER_WELCOME_MESSAGE.format(
                                                                 comment.author.name),
                                                             from_subreddit='/r/SolutionGambling')

            # get the player from the DB so we can validate their wager
            # and update their balance
            player = sg_repo.GET_PLAYER_BY_USERNAME(comment.author.name)

            # now process the comment - first we convert it to lower
            post_body_lower = comment.body.lower()
            print("Processing post body: ".format(post_body_lower))

            wager_amount = parse_post_for_wager(post_body_lower, player['balance'])
            print("Wager amount from post: {}".format(wager_amount))

            if wager_amount <= 0:
                print("Wager amount not valid")
                comment.reply(error_messages.POKER_ERROR_MSG)
                continue

            if wager_amount > player['balance']:
                print("Player wagered more than their balance")
                comment.reply(error_messages.INSUFFICIENT_BALANCE_ERROR_MSG)
                continue

            if wager_amount > max_bet:
                print("Player wagered more than this game's max bet")
                comment.reply(error_messages.OVER_MAX_BET_ERROR_MSG.format(max_bet))
                continue

            wager_result = play_poker(wager_amount)
            new_player_balance = player['balance'] - wager_amount + wager_result['winnings']

            sg_repo.INSERT_WAGER(player['username'], wager_result['outcome'],
                                 wager_amount, wager_result['winnings'], new_player_balance, game_type)
            update_player_after_wager(player['username'], new_player_balance, player['flair_css_class'])

            reply = format_wager_reply(player['username'], wager_amount, wager_result['full_hand_string'],
                                       wager_result['full_board_string'],
                                       wager_result['hand_type'], wager_result['outcome'], wager_result['winnings'],
                                       new_player_balance)

            # print("Reply formatted:\n{}".format(reply))
            comment.reply(reply)
        else:
            break

while True:
    bot_loop()

    print("---------------------- Processing finished - sleeping for 10 seconds...")
    time.sleep(10)