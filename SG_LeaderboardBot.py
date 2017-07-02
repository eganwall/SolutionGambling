import ConfigParser
import praw
import SG_Repository
import SG_Messages
import time

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

# initialize our repository
sg_repo = SG_Repository.Repository()

# get our messaging classes
error_messages = SG_Messages.ErrorMessages
reply_messages = SG_Messages.ReplyMessages

# set our subreddit so that we can do mod stuff like edit flairs
subreddit = reddit.subreddit('solutiongambling')

# get the Submission object for our leaderboard thread
submission = reddit.submission(id='6jya4t')

while True:
    full_post_message = reply_messages.LEADERBOARD_FULL_POST_TEMPLATE_MSG

    # get our top wealthiest players
    players = sg_repo.GET_WEALTHIEST_PLAYERS(10)

    player_leaderboard_message = reply_messages.PLAYER_LEADERBOARD_TEMPLATE_MSG

    player_tokens = list()
    for player in players:
        player_tokens.append(player['username'])
        player_tokens.append(player['balance'])

    player_leaderboard_message = player_leaderboard_message.format(*player_tokens)
    print("Updating player leaderboard:\n\n{}".format(player_leaderboard_message))


    # get our top wagers by win
    top_wins = sg_repo.GET_TOP_WIN_WAGERS_SORTED_BY_OUTCOME_AMT(10)

    win_leaderboard_message = reply_messages.WINS_LEADERBOARD_TEMPLATE_MSG

    win_tokens = list()
    for win in top_wins:
        win_tokens.append(win['username'])
        win_tokens.append(win['wager_amount'])
        win_tokens.append(win['outcome_amount'])
        win_tokens.append(win['game_type'])

    win_leaderboard_message = win_leaderboard_message.format(*win_tokens)
    print("Updating wins leaderboard:\n\n{}".format(win_leaderboard_message))

    # get our top wagers by loss
    top_losses = sg_repo.GET_TOP_LOSE_WAGERS_SORTED_BY_WAGER_AMT(10)

    loss_leaderboard_message = reply_messages.LOSSES_LEADERBOARD_TEMPLATE_MSG

    loss_tokens = list()
    for loss in top_losses:
        loss_tokens.append(loss['username'])
        loss_tokens.append(loss['wager_amount'])
        loss_tokens.append(loss['game_type'])

    loss_leaderboard_message = loss_leaderboard_message.format(*loss_tokens)
    print("Updating losses leaderboard:\n\n{}".format(loss_leaderboard_message))

    all_players_count = sg_repo.GET_ALL_PLAYERS().count()

    full_post_message = full_post_message.format(all_players_count, player_leaderboard_message, win_leaderboard_message, loss_leaderboard_message)
    submission.edit(full_post_message)

    print("---------------------- Processing finished - sleeping for 30 seconds...")
    time.sleep(30)