import pprint
import math
import praw
import SG_Repository
import SG_Messages
import random
import time
import ConfigParser

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

def format_wager_reply(username, wager_amount, hand_string, hand_type, outcome,
                       winnings, new_balance):
    return reply_messages.POKER_SUCCESS_MSG.format(username,
                                                   wager_amount,
                                                   hand_string,
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

def spin_roulette():
    print("Spinning roulette wheel...")
    result = random.choice(roulette_list)
    print("Result : ")
    pprint.pprint(result)
    return result

def parse_individual_wager(wager_text, current_balance):
    base_result = {'wager_amount' : 0, 'wager_type' : '', 'wager_value' : '', 'balance_after' : current_balance, 'error_msg' : ''}

    split_text = wager_text.strip().split(' ')

    if len(split_text) != 3 or split_text[0] != 'wager' or not split_text[1].isnumeric():
        print("Comment format is wrong")
        base_result['error_msg'] = error_messages.ROULETTE_WAGER_FORMAT_ERROR_MSG.format(wager_text.strip())
        return base_result

    if int(split_text[1]) > current_balance:
        print("Player has wagered too much : [wager = {}], [current_balance = {}]".format(int(split_text[1]), current_balance))
        base_result['error_msg'] = error_messages.ROULETTE_WAGER_INSUFFICIENT_BALANCE_ERROR_MSG.format(wager_text.strip())
        return base_result

    if int(split_text[1]) > max_bet:
        print("Player has wagered more than the max : [wager = {}], [max_bet = {}]".format(int(split_text[1]), max_bet))
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
        print("Player entered an unknown wager value : [wager_value = {}]".format(split_text[2]))
        base_result['error_msg'] = error_messages.ROULETTE_WAGER_FORMAT_ERROR_MSG.format(wager_text.strip())
        return base_result

    result = base_result
    result['wager_amount'] = int(split_text[1])
    result['wager_type'] = wager_type
    result['wager_value'] = wager_value
    result['balance_after'] = current_balance - int(split_text[1])

    print("Result of wager parsing:")
    pprint.pprint(result)
    print("\n")

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

def bot_loop():
    # get the Submission object for our poker thread
    submission = reddit.submission(id='6k6vbj')

    submission.comment_sort = 'new'
    submission.comments.replace_more(limit=0)
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
            print("Processing post body: \n{}".format(post_body_lower))

            print("Analyzing line by line:")
            for line in post_body_lower.splitlines():
                print(line)

            # parse the post for wagers
            remaining_balance = player['balance']
            player_wagers = list()
            for line in post_body_lower.splitlines():
                new_wager = parse_individual_wager(line, remaining_balance)
                player_wagers.append(new_wager)
                remaining_balance = new_wager['balance_after']

            print("\n\nParsed wager list:")
            pprint.pprint(player_wagers)

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
                elif outcome == SG_Repository.WagerOutcome.LOSE:
                    wager_winnings = 0
                    wager_string = SG_Messages.ReplyMessages.ROULETTE_INDIVIDUAL_WAGER_TEMPLATE_MSG.format(
                        index + 1, wager['wager_amount'], wager['wager_value'], outcome, wager_winnings
                    )

                    new_player_balance = player['balance'] - wager['wager_amount'] + wager_winnings
                    sg_repo.INSERT_WAGER(player['username'], outcome, wager['wager_amount'], wager_winnings,
                                         new_player_balance, game_type)
                    total_wagered += wager['wager_amount']
                else:
                    wager_winnings = 0
                    wager_string = """Wager {}: """.format(index + 1) + wager['error_msg'] + """

&nbsp;

"""
                total_winnings += wager_winnings
                wager_results_string += wager_string

            # calculate the new balance after all of the bets are executed
            new_player_balance = player['balance'] - total_wagered + total_winnings

            # update the player's balance
            update_player_after_wager(player['username'], new_player_balance, player['flair_css_class'])
            updated_player = sg_repo.GET_PLAYER_BY_USERNAME(player['username'])

            # format and send the reply
            reply = SG_Messages.ReplyMessages.ROULETTE_REPLY_WRAPPER_TEMPLATE_MSG.format(
                updated_player['username'], roulette_result['value'], roulette_result['color'].upper(),
                wager_results_string, total_wagered, total_winnings, (total_winnings - total_wagered),
                updated_player['balance']
            )

            print("Reply formatted:\n{}".format(reply))
            comment.reply(reply)

        else:
            break

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

# set our subreddit so that we can do mod stuff like edit flairs
subreddit = reddit.subreddit('solutiongambling')

while True:
    bot_loop()

    print("---------------------- Processing finished - sleeping for 10 seconds...")
    time.sleep(10)