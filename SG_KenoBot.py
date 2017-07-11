import praw
import SG_Repository
import SG_Messages
import pprint
import time
import ConfigParser
import random
import SG_Utils

config = ConfigParser.ConfigParser()
config.read("settings.config")
config_header = "Keno"

username = config.get("General", "username")
version = config.get("General", "version")
starting_balance = int(config.get("General", "starting_balance"))
max_bet = int(config.get(config_header, "bet_limit"))
game_type = 'Keno'

def format_wager_reply(username, wager_amount, num_catches, outcome,
                       winnings, result_string, new_balance):
    return reply_messages.KENO_REPLY_WRAPPER_TEMPLATE_MSG.format(username, wager_amount, result_string, outcome,
                                                                 winnings, (winnings - wager_amount), new_balance)

def parse_post_for_wager(post_body, player_balance):
    body_tokens = post_body.strip().split(' ')

    if str(body_tokens[0]) == 'wager' and (body_tokens[1].isnumeric() or body_tokens[1] == 'max'):
        if(body_tokens[1] == 'max'):
            return min(player_balance, max_bet)
        else:
            return int(body_tokens[1])

    return 0

def play_keno(wager_amount):
    payout_table = {
        0: 0,
        1: 0,
        2: 2,
        3: 5,
        4: 10,
        5: 20,
        6: 75,
        7: 2000,
        8: 25000
    }

    number_range = range(1, 61) # list of numbers 1-60
    # get player's picks
    player_numbers = random.sample(number_range, 7)
    # print("Player picks: " + str(player_numbers))

    # get dealer's picks
    dealer_numbers = random.sample(number_range, 15)
    # print("Dealer picks: " + str(dealer_numbers))

    result_string = """***Your numbers*** : {}\n\n***Dealer numbers*** : [""".format(str(player_numbers))

    # get the number of catches
    num_catches = 0
    for number in dealer_numbers:
        if number in player_numbers:
            print("Catch! [{}]".format(number))
            num_catches += 1
            result_string += """***{}***, """.format(number)
        else:
            result_string += """{}, """.format(number)

    # remove the trailing ', ' and add the end bracket and newlines
    result_string = result_string[:-2] + "]\n\n"

    print("Found {} catches\n".format(num_catches))
    # print("Your payout is {} : 1".format(str(payout_table[num_catches])))

    result_string += """Total catches : ***{}***\n\n""".format((num_catches))

    winnings = wager_amount * payout_table[num_catches]
    print("Total winnings : {}".format(str(winnings)))

    if winnings > 0:
        outcome = SG_Repository.WagerOutcome.WIN
    else:
        outcome = SG_Repository.WagerOutcome.LOSE

    wager_result = {'num_catches' : num_catches, 'outcome': outcome, 'winnings': winnings,
                    'full_result_string' : result_string}

    print("Keno wager result:")
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

# set our subreddit so that we can do mod stuff like edit flairs
subreddit = reddit.subreddit('solutiongambling')

def bot_loop():
    # get the Submission object for our keno thread
    submission = reddit.submission(id='6mk17b')

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
                SG_Utils.update_player_flair(comment.author.name, starting_balance, '')
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
                comment.reply(error_messages.KENO_ERROR_MSG)
                continue

            if wager_amount > player['balance']:
                print("Player wagered more than their balance")
                comment.reply(error_messages.INSUFFICIENT_BALANCE_ERROR_MSG)
                continue

            if wager_amount > max_bet:
                print("Player wagered more than this game's max bet")
                comment.reply(error_messages.OVER_MAX_BET_ERROR_MSG.format(max_bet))
                continue

            wager_result = play_keno(wager_amount)
            new_player_balance = player['balance'] - wager_amount + wager_result['winnings']

            sg_repo.INSERT_WAGER(player['username'], wager_result['outcome'],
                                 wager_amount, wager_result['winnings'], new_player_balance, game_type)
            SG_Utils.update_player_after_wager(player['username'], new_player_balance, player['flair_css_class'])

            reply = format_wager_reply(player['username'], wager_amount, wager_result['num_catches'], wager_result['outcome'],
                                       wager_result['winnings'], wager_result['full_result_string'], new_player_balance)

            print("Reply formatted:\n{}".format(reply))
            comment.reply(reply)
        else:
            break

while True:
    bot_loop()

    print("---------------------- Processing finished - sleeping for 10 seconds...")
    time.sleep(10)

# players = sg_repo.GET_ALL_PLAYERS()
# for player in players:
#     pprint.pprint(player)
#     sg_repo.DELETE_PLAYER_BY_USERNAME(player['username'])