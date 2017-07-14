import ConfigParser
import praw
import SG_Repository
import SG_Messages
import pprint

config = ConfigParser.ConfigParser()
config.read("settings.config")
config_header = "Roulette"

username = config.get("General", "username")
version = config.get("General", "version")
starting_balance = int(config.get("General", "starting_balance"))
max_bet = int(config.get(config_header, "bet_limit"))

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

# load our message template
message_template = SG_Messages.MiscMessages.SUBSCRIBER_ANNOUNCEMENT_MSG_TEMPLATE

# here's the subject and body of the message we want to send to the subs
message_subject = "Updates: New All-in game, replacing coin toss"
message_body = """Earlier today I was looking at the state of some of the games, and realized that 
I needed to change at least a couple things. One of the problems, I think, is that we need more high-limit 
games. However, the all-or-nothing coin flip was obviously not an attractive option for someone with a 
bankroll of several million (or several hundred million). 

Because of this, I've done away with the coin flip and replaced it with something that's still
risky, but less so - and with a potentially much higher payout. Instead of a coin flip, a die will 
be rolled. You'll still have to risk your whole balance, but it pays out a bit differently. If the 
result is 1 or 2, you will lose your wager. However, a die roll of 3 pays out 2 to 1, with the payouts
increasing until a roll of 6 (paying out 5 to 1!). 

The idea here is that taking a well-placed shot at this 
game (and getting a bit lucky) could cause your balance to skyrocket, and might let you afford a 
new flair or two :)

Give it a try, and stay tuned for more updates after the weekend!"""

# get all of our players
all_players = sg_repo.GET_ALL_PLAYERS()

not_received = []

for player in all_players:
    # if player['username'] not in not_received:
    #     continue
    try:
        message = message_template.format(player['username'], message_body)
        reddit.redditor(player['username']).message(message_subject, message, from_subreddit='/r/SolutionGambling')
        print("Message sent to /u/{}".format(player['username']))
    except Exception as e:
        print("Exception {}".format(e))