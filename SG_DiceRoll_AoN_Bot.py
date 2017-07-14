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

username = config.get("General", "username")
version = config.get("General", "version")
starting_balance = int(config.get("General", "starting_balance"))
game_type = 'AoN Die'

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
    print("Die roll result: {}".format(roll))
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

    print("All-or-nothing die roll wager result:")
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
    # get the Submission object for our dice roll thread
    submission = reddit.submission(id='6n76ve')

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

            if wager_amount == 0:
                print("Player has no balance")
                comment.reply(error_messages.AON_DICE_ROLL_NO_BALANCE_ERROR_MSG.format(player['username']))
                continue

            if wager_amount == -1:
                print("Player triggered bot incorrectly")
                comment.reply(error_messages.AON_DICE_ROLL_ERROR_MSG.format(player['username']))
                continue

            wager_result = play_dice(wager_amount)
            new_player_balance = player['balance'] - wager_amount + wager_result['winnings']

            sg_repo.INSERT_WAGER(player['username'], wager_result['outcome'],
                                 wager_amount, wager_result['winnings'], new_player_balance, game_type)
            SG_Utils.update_player_after_wager(player['username'], new_player_balance, player['flair_css_class'])

            reply = format_wager_reply(player['username'], wager_amount, wager_result['die_roll_result'], wager_result['outcome'],
                                       wager_result['winnings'], new_player_balance)

            print("Reply formatted:\n{}".format(reply))
            comment.reply(reply)
        else:
            break

while True:
    bot_loop()

    print("---------------------- Processing finished - sleeping for 10 seconds...")
    time.sleep(10)