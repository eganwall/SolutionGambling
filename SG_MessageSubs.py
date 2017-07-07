import ConfigParser
import praw
import SG_Repository
import SG_Messages

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
message_subject = "Updates: Small Flair Changes and New High-Stakes Game!"
message_body = """Today I finished a couple of smaller things I had in the works: flair 
titles and a new, all-or-nothing game!

&nbsp;

If you go to the flair shop, you'll notice that each level/color of flair now has a title.
I added this because I was looking at the sub on my mobile Reddit app, and noticed that 
since CSS doesn't show up, nobody could see the flair colors! The titles add a little bit more
flavor, as well as allowing mobile users to see their flairs (and the flairs of others).

&nbsp;

I also noticed that there have been plenty of big hands that have been hit in poker, resulting 
in some pretty high balances. This is neat, but having a maximum of 50K per poker hand kind of 
makes it feel insignificant. For a little bit of added flavor, I've implemented a simple coin flip 
game. What makes it high-stakes, however, is that if you place a wager, it's for your entire bankroll!

I know this may not be appealing to some of you more risk-averse players with big stacks, and that's
OK - I figured I would get some feedback on this, while also planning to implement some other 
high-stakes alternatives; for instance, possibly high-limit roulette where you can choose between a small
bet of 1 million, and a large bet of 10 million. I'm going to be fiddling around with some design issues
around high stakes games, so stay tuned for more in the future!

&nbsp;

Coming up soon: gifting and more games!"""

# get all of our players
all_players = sg_repo.GET_ALL_PLAYERS()

for player in all_players:
    message = message_template.format(player['username'], message_body)
    reddit.redditor(player['username']).message(message_subject, message, from_subreddit='/r/SolutionGambling')
    print("Message sent to /u/{}".format(player['username']))