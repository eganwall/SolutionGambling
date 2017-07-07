<<<<<<< HEAD
import ConfigParser
import praw

import SG_Messages
import SG_Repository

config = ConfigParser.ConfigParser()
config.read("settings.config")

username = config.get("General", "username")
version = config.get("General", "version")

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

admin_usernames = ['eganwall']

def update_player_flair(player, flair, flair_class):
    print('Updating flair : [player = {}], [flair = {}], [class = {}]'.format(player, flair, flair_class))

    if(player == 'eganwall'):
        subreddit.flair.set(player, "Pit Boss : {:,}".format(flair), flair_class)
    else:
        subreddit.flair.set(player, "{}{:,}".format(constants.FLAIR_TIER_TITLES[flair_class], flair), flair_class)

# initialize our repository
sg_repo = SG_Repository.Repository()

constants = SG_Messages.MiscConstants

# get our subreddit
subreddit = reddit.subreddit('solutiongambling')

print('Streaming comments...')

for comment in subreddit.stream.comments():
    if (comment.author.name in admin_usernames) and sg_repo.GET_COMMENT_BY_ID(comment.id + '_admin') is None:
        sg_repo.INSERT_COMMENT_ID(comment.id + '_admin')
        comment_tokens = comment.body.strip().split(' ')
        if comment_tokens[0].lower() == '!deposit' and comment_tokens[1].isnumeric():
            player_username = comment.parent().author.name
            add_amount = int(comment_tokens[1])
            print('Adding {} points to /u/{}\'s account...'.format(add_amount, player_username))

            player_dto = sg_repo.GET_PLAYER_BY_USERNAME(player_username)
            new_balance = player_dto['balance'] + add_amount

            print('/u/{}\'s new balance is {}\n\n'.format(player_username, new_balance))
            sg_repo.UPDATE_PLAYER_BALANCE_BY_USERNAME(player_username, new_balance)

            update_player_flair(player_username, new_balance, player_dto['flair_css_class'])

=======
import ConfigParser
import praw
import SG_Repository

config = ConfigParser.ConfigParser()
config.read("settings.config")

username = config.get("General", "username")
version = config.get("General", "version")

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

admin_usernames = ['eganwall']

def update_player_flair(player, flair):
    print('Updating flair : [player = {}], [flair = {}]'.format(player, flair))

    if(player == 'eganwall'):
        subreddit.flair.set(player, "Pit Boss : {:,}".format(flair))
    else:
        subreddit.flair.set(player, "{:,}".format(flair))

# initialize our repository
sg_repo = SG_Repository.Repository()

# get our subreddit
subreddit = reddit.subreddit('solutiongambling')

print('Streaming comments...')

for comment in subreddit.stream.comments():
    if (comment.author.name in admin_usernames) and sg_repo.GET_COMMENT_BY_ID(comment.id + '_admin') is None:
        sg_repo.INSERT_COMMENT_ID(comment.id + '_admin')
        comment_tokens = comment.body.strip().split(' ')
        if comment_tokens[0].lower() == '!deposit' and comment_tokens[1].isnumeric():
            player_username = comment.parent().author.name
            add_amount = int(comment_tokens[1])
            print('Adding {} points to /u/{}\'s account...'.format(add_amount, player_username))

            player_dto = sg_repo.GET_PLAYER_BY_USERNAME(player_username)
            new_balance = player_dto['balance'] + add_amount

            print('/u/{}\'s new balance is {}\n\n'.format(player_username, new_balance))
            sg_repo.UPDATE_PLAYER_BALANCE_BY_USERNAME(player_username, new_balance)

            update_player_flair(player_username, new_balance)

>>>>>>> ec22b73e27c4152e5c55ba2a5911129c18070c26
            reddit.redditor('eganwall').message('Deposit successful', 'Successfully deposited {} for /u/{}'.format(add_amount, player_username))