import praw
import SG_Repository
import SG_Messages
import time
import ConfigParser

flair_table = {
    1 : {'cost' : 50000, 'css_class' : 'lvl1'},
    2 : {'cost' : 500000, 'css_class' : 'lvl2'},
    3 : {'cost' : 2000000, 'css_class' : 'lvl3'},
    4 : {'cost' : 10000000, 'css_class' : 'lvl4'},
    5 : {'cost' : 100000000, 'css_class' : 'lvl5'},
    6 : {'cost' : 1000000000, 'css_class' : 'lvl6'},
    7 : {'cost' : 10000000000, 'css_class' : 'lvl7'},
    8 : {'cost' : 0, 'css_class' : ''}
}

config = ConfigParser.ConfigParser()
config.read("settings.config")

username = config.get("General", "username")
version = config.get("General", "version")
starting_balance = int(config.get("General", "starting_balance"))

def is_requesting_purchase(post_body):
    body_tokens = post_body.strip().split(' ')

    if str(body_tokens[0]) == 'upgrade':
        return True

    return False

def update_player_after_purchase(username, new_balance, flair_level, flair_class):
    sg_repo.UPDATE_PLAYER_BALANCE_BY_USERNAME(username, new_balance)
    sg_repo.UPDATE_PLAYER_FLAIR_BY_USERNAME(username, flair_level, flair_class)
    update_player_flair(username, new_balance, flair_class)

def update_player_flair(player, flair, flair_class):
    print('Updating flair : [player = {}], [flair = {}], [class = {}]'.format(player, flair, flair_class))

    if(player == 'eganwall'):
        subreddit.flair.set(player, "Pit Boss : {:,}".format(flair), flair_class)
    else:
        subreddit.flair.set(player, "{}{:,}".format(constants.FLAIR_TIER_TITLES[flair_class], flair), flair_class)

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

# set our subreddit
subreddit = reddit.subreddit('solutiongambling')

while True:
    # get the Submission object for our thread
    submission = reddit.submission(id='6l2lsk')

    submission.comment_sort = 'new'
    submission.comments.replace_more(limit = 0)
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
                                                             reply_messages.NEW_PLAYER_WELCOME_MESSAGE.format(comment.author.name),
                                                             from_subreddit='/r/SolutionGambling')

            # get the player from the DB so we can validate their purchase and update them
            player = sg_repo.GET_PLAYER_BY_USERNAME(comment.author.name)

            # now process the comment - first we convert it to lower
            post_body_lower = comment.body.lower()
            print("Processing post body: ".format(post_body_lower))

            if(is_requesting_purchase(post_body_lower)):
                target_flair_level = player['flair_level'] + 1
                print("/u/{} is requesting upgrade to level {}".format(player['username'], target_flair_level))

                target_flair = flair_table[target_flair_level]

                if target_flair_level > 7:
                    print("Player already at highest level")
                    reply = error_messages.FLAIR_SHOP_ALREADY_MAX_LEVEL.format(player['username'])
                elif player['balance'] < target_flair['cost']:
                    print("Player balance [{}] is less than cost [{}] - upgrade denied".format(player['balance'], target_flair['cost']))
                    # REPLY WITH ERROR MESSAGE
                    reply = error_messages.FLAIR_SHOP_INSUFFICIENT_BALANCE_ERROR_MSG.format(player['username'], target_flair_level,
                                                                                            target_flair['cost'], player['balance'])
                else:
                    new_flair_css_class = target_flair['css_class']
                    new_player_balance = player['balance'] - target_flair['cost']
                    print("/u/{}'s purchase was successful : [new_balance = {}]".format(player['username'], new_player_balance))

                    update_player_after_purchase(player['username'], new_player_balance, target_flair_level, new_flair_css_class)
                    reply = reply_messages.FLAIR_SHOP_SUCCESS_MSG.format(player['username'], target_flair_level,
                                                                         target_flair['cost'], new_player_balance)

                print("Reply formatted:\n{}".format(reply))
                comment.reply(reply)

    print("---------------------- Processing finished - sleeping for 10 seconds...")
    time.sleep(10)

# players = sg_repo.GET_ALL_PLAYERS()
# for player in players:
#     pprint.pprint(player)
#     sg_repo.DELETE_PLAYER_BY_USERNAME(player['username'])