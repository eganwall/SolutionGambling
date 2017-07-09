import math
import praw
import SG_Repository
import SG_Messages
import pprint
import time
import deuces
import ConfigParser

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

def update_player_after_wager(username, new_balance, flair_class):
    sg_repo.UPDATE_PLAYER_BALANCE_BY_USERNAME(username, new_balance)
    update_player_flair(username, new_balance, flair_class)

def update_player_flair(player, flair, flair_class):
    print('Updating flair : [player = {}], [flair = {}], [class = {}]'.format(player, flair, flair_class))

    if(player == 'eganwall'):
        subreddit.flair.set(player, "Pit Boss : {:,}".format(flair), flair_class)
    else:
        subreddit.flair.set(player, "{}{:,}".format(constants.FLAIR_TIER_TITLES[flair_class], flair), flair_class)


def parse_post_for_wager(post_body, player_balance):
    body_tokens = post_body.strip().split(' ')

    if str(body_tokens[0]) == 'wager':
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
    print "Player: {} {}".format(card.int_to_pretty_str(player_card), card.get_rank_int(player_card))
    print "Dealer: {} {}".format(card.int_to_pretty_str(dealer_card), card.get_rank_int(dealer_card))

    player_war_card = ''
    dealer_war_card = ''

    # evaluate the difference of the player and dealer cards
    result = evaluate_win(player_card, dealer_card)
    if result > 0:
        winnings = calculate_winnings(result, wager_amount, False)
        print "Player wins - winnings = {}!".format(winnings)
        outcome = SG_Repository.WagerOutcome.WIN
    elif result < 0:
        winnings = calculate_winnings(result, wager_amount, False)
        print "Player loses - winnings = {}!".format(winnings)
        outcome = SG_Repository.WagerOutcome.LOSE
    else:
        print "Tie! Going to war...\n\n"

        player_war_card = deck.draw(1)
        dealer_war_card = deck.draw(1)
        print "Player: {} {}".format(card.int_to_pretty_str(player_war_card), card.get_rank_int(player_war_card))
        print "Dealer: {} {}".format(card.int_to_pretty_str(dealer_war_card), card.get_rank_int(dealer_war_card))

        war_result = evaluate_win(player_war_card, dealer_war_card)
        if war_result > 0:
            winnings = calculate_winnings(war_result, wager_amount, True)
            print "Player wins - winnings = {}!".format(winnings)
            outcome = SG_Repository.WagerOutcome.WIN
        elif war_result < 0:
            winnings = calculate_winnings(war_result, wager_amount, True)
            print "Player loses - winnings = {}!".format(winnings)
            outcome = SG_Repository.WagerOutcome.LOSE
        else:
            winnings = calculate_winnings(war_result, wager_amount, True)
            print "Player wins war tie - winnings = {}!".format(winnings)
            outcome = SG_Repository.WagerOutcome.WIN

        player_war_card = card.int_to_pretty_str(player_war_card)
        dealer_war_card = card.int_to_pretty_str(dealer_war_card)

    wager_result = {'player_card' : card.int_to_pretty_str(player_card), 'dealer_card' : card.int_to_pretty_str(dealer_card), 'outcome' : outcome,
                    'winnings' : winnings, 'player_war_card' : player_war_card, 'dealer_war_card' : dealer_war_card}

    print("War wager result:")
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

card = deuces.Card()

# set our subreddit so that we can do mod stuff like edit flairs
subreddit = reddit.subreddit('solutiongambling')

def bot_loop():
    # get the Submission object for our war thread
    submission = reddit.submission('6m5yhm')

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
                comment.reply(error_messages.WAR_ERROR_MSG.format(player['username']))
                continue

            if wager_amount > player['balance']:
                print("Player wagered more than their balance")
                comment.reply(error_messages.INSUFFICIENT_BALANCE_ERROR_MSG)
                continue

            wager_result = play_war(wager_amount)
            new_player_balance = player['balance'] - wager_amount + wager_result['winnings']

            sg_repo.INSERT_WAGER(player['username'], wager_result['outcome'],
                                 wager_amount, wager_result['winnings'], new_player_balance, game_type)
            update_player_after_wager(player['username'], new_player_balance, player['flair_css_class'])

            reply = format_wager_reply(player['username'], wager_amount, wager_result['player_card'],
                                       wager_result['player_war_card'], wager_result['dealer_card'],
                                       wager_result['dealer_war_card'], wager_result['outcome'],
                                       wager_result['winnings'], new_player_balance)

            print("Reply formatted:\n{}".format(reply))
            comment.reply(reply)
        else:
            break

while True:
    bot_loop()

    print("---------------------- Processing finished - sleeping for 10 seconds...")
    time.sleep(10)