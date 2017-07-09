import ConfigParser
import praw
import SG_Repository
import SG_Messages

config = ConfigParser.ConfigParser()
config.read("settings.config")

version = config.get("General", "version")

# create our Reddit instance
c_id = config.get("General", "client_id")
c_secret = config.get("General", "client_secret")
user = config.get("General", "plain_username")
pw = config.get("General", "password")

reddit = praw.Reddit(
    client_id=c_id,
    client_secret=c_secret,
    username=user,
    password=pw,
    user_agent='Dealer bot v{} by /u/eganwall'.format(version)
)

# initialize our repository
sg_repo = SG_Repository.Repository()

subreddit = reddit.subreddit('solutiongambling')


def update_player_after_wager(username, new_balance, flair_class):
    if new_balance <= 0:
        print "Depositing 500 into bankrupt player's account [/u/{}]".format(username)
        new_balance = 500
        reddit.redditor(username).message('More points!',
                                                    SG_Messages.ReplyMessages.DEPOSIT_AFTER_BANKRUPTCY_MSG.format(
                                                        username), from_subreddit='/r/SolutionGambling')
    sg_repo.UPDATE_PLAYER_BALANCE_BY_USERNAME(username, new_balance)
    update_player_flair(username, new_balance, flair_class)

def update_player_flair(player, flair, flair_class):
    print('Updating flair : [player = {}], [flair = {}], [class = {}]'.format(player, flair, flair_class))

    if (player == 'eganwall'):
        subreddit.flair.set(player, "Pit Boss : {:,}".format(flair), flair_class)
    else:
        subreddit.flair.set(player, "{}{:,}".format(SG_Messages.MiscConstants.FLAIR_TIER_TITLES[flair_class], flair), flair_class)
