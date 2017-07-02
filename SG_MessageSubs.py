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
message_subject = "Updates: Reset Coming!"
message_body = """Last night, I reset everyone's balances and cleaned up some of the games in the sub (I'm sure most of you noticed). However, it still seems that progression is less about any sort of luck and more of a function of betting volume and frequency (looking at you /u/vnoice!), which isn't particularly in line with my vision. Like I said in earlier posts, this sub shouldn't necessarily operate like a casino - I want players to win in the long run. It's just... maybe not quite so easily. Playing poker at the moment is basically printing money, and after a few big payouts you can start betting huge amounts with pretty much 0 risk of ruin. 

Currently when playing poker, you have roughly a 17% chance to lose (no pair), ~43% chance to get your bet back (pair), and about a 40% chance to **at least** double your money. I think that this is, combined with the fact that there is no maximum bet, is pretty unhealthy and makes the game less meaningful. It's not really gambling if there's no chance of losing, is it? And if poker is basically free money, what reason is there to play any of the other games? As we can see, there is none. 

That being said, here are the steps I'm going to take in order to make this a little more stimulating:

* Further adjust the payout scale in poker. After the changes, a hand must be **at least 2 pair** in order to qualify as a win. This makes poker more of a gamble, as wins will be less frequent, but it will still pay out better than pretty much any other game
* Institute a maximum bet. Just like casinos have at their tables, this sub will have a **maximum bet** of something along the lines of 100K (this may vary across the game type). This will eliminate some of the experience issues with having to type in huge numbers, and will help make progression less snowbally and a bit more realistic. If player balances eventually get high enough that this is a fairly insignificant max bet, I'll open up some high-limit threads. After these changes, though, it should take a lot longer to get to the point where we have balances in the billions and trillions

Along with these changes will come another reset (sorry to those who have been grinding after this current reset!) but I think it's important that there are fewer safe bets - after all, this is about gambling!"""

# get all of our players
all_players = sg_repo.GET_ALL_PLAYERS()

for player in all_players:
    message = message_template.format(player['username'], message_body)
    reddit.redditor(player['username']).message(message_subject, message, from_subreddit='/r/SolutionGambling')
    print("Message sent to /u/{}".format(player['username']))