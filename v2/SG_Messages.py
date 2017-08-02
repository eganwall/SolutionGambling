class ErrorMessages:
    DICE_ROLL_ERROR_MSG = """Hello! Please place your wager in the form of a 
top-level comment:

`wager {NUMBER}`

where 0 < {NUMBER} <= your balance.

Thanks, and good luck!

^^If ^^you ^^have ^^any ^^issues, ^^please ^^PM ^^/u/eganwall ^^or ^^post ^^on ^^this ^^sub!*"""

    POKER_ERROR_MSG = """Hello! Please place your wager in the form of a 
top-level comment:

`wager {NUMBER}`

where 0 < {NUMBER} <= your balance.

Thanks, and good luck!

^^If ^^you ^^have ^^any ^^issues, ^^please ^^PM ^^/u/eganwall ^^or ^^post ^^on ^^this ^^sub!*"""

    KENO_ERROR_MSG = """Hello! Please place your wager in the form of a 
top-level comment:

`wager {NUMBER}`

where 0 < {NUMBER} <= your balance.

Thanks, and good luck!

^^If ^^you ^^have ^^any ^^issues, ^^please ^^PM ^^/u/eganwall ^^or ^^post ^^on ^^this ^^sub!*"""

    ROULETTE_WAGER_FORMAT_ERROR_MSG = """Wager could not be made: [*{}*] Reason: __invalid format__.
Please refer to the body of the OP for more info."""

    ROULETTE_WAGER_INSUFFICIENT_BALANCE_ERROR_MSG = """Wager could not be made: [*{}*] Reason:
__Insufficient balance__. Please refer to the body of the OP for more info."""

    ROULETTE_WAGER_OVER_MAX_ERROR_MSG = """Wager could not be made: [*{}*] Reason:
    __Wager was over maximum__. Please refer to the body of the OP for more info."""

    INSUFFICIENT_BALANCE_ERROR_MSG = """Hello! It looks like you're trying to place
a wager for an amount greater than your balance. Please make a more reasonable bet!

^^If ^^you ^^have ^^any ^^issues, ^^please ^^PM ^^/u/eganwall ^^or ^^post ^^on ^^this ^^sub!*"""

    OVER_MAX_BET_ERROR_MSG = """Hello! It looks like you're trying to place
a wager for an amount greater than the maximum bet for this game (__{:,}__).
Please adjust your wager amount!

^^If ^^you ^^have ^^any ^^issues, ^^please ^^PM ^^/u/eganwall ^^or ^^post ^^on ^^this ^^sub!*"""

    FLAIR_SHOP_INSUFFICIENT_BALANCE_ERROR_MSG = """/u/{},

It appears that you are attempting to purchase a __Level {}__ flair, which costs {:,}.

Your current balance is {:,}, which is insufficient for this purchase. Please try again when you have the points!"""

    FLAIR_SHOP_ALREADY_MAX_LEVEL = """/u/{},

It appears you are already at the highest flair level! Congratulations!"""

    AON_DICE_ROLL_NO_BALANCE_ERROR_MSG = """/u/{},

It appears that you have no points with which to wager! Please message the moderators
and they will deposit the starting amount into your bankroll so you can get back on 
your feet.

Thanks, and good luck!"""

    AON_DICE_ROLL_ERROR_MSG = """/u/{},

Please place your bet by posting a comment like this: 

    wager

Thanks, and good luck!"""

    WAR_ERROR_MSG = """/u/{},

Please place your bet by selecting either the 'small' or 'big' bet:

    wager small
    wager mid
    wager big

Thanks, and good luck!"""

class ReplyMessages:
    NEW_PLAYER_WELCOME_MESSAGE = """Hello, /u/{}! Welcome to /r/SolutionGambling -
where you can build a meaningless fortune of imaginary points one wager at a time!
It seems that you are a new player with us, so we've gone ahead and made an initial 
deposit of 500 points. Knock yourself out, kid!"""

    DICE_ROLL_SUCCESS_MSG = """/u/{},

Thanks for placing your bet of {:,}! Here are your results:

* Roll 1: {}

* Roll 2: {}

* **Total: {}**

**Your outcome is: {}**

Your winnings are {:,}, and your new balance is {:,}.

Thank you for playing - please come see us again!"""

    POKER_SUCCESS_MSG = """/u/{},

Thanks for placing your bet of {:,}! Here are your results:

Your 2-card poker hand is

{}

&nbsp;

The 5 cards on the board are

{}

&nbsp;

**Your outcome is: {}**

Your winnings are {:,}, and your new balance is {:,}.

Thank you for playing - please come see us again!"""

    PLAYER_LEADERBOARD_TEMPLATE_MSG = """**Here is the overall balance leaderboard:**
    
Rank|Player| Balance 
---------|---------|---------:
1|/u/{} | __{:,}__
2|/u/{} | __{:,}__
3|/u/{} | __{:,}__
4|/u/{} | __{:,}__
5|/u/{} | __{:,}__
6|/u/{} | __{:,}__
7|/u/{} | __{:,}__
8|/u/{} | __{:,}__
9|/u/{} | __{:,}__
10|/u/{} | __{:,}__"""

    WINS_LEADERBOARD_TEMPLATE_MSG = """**Here is the WINS leaderboard:**
    
Rank|Player|Wager Amount|Winnings|Game Type
---------|---------|----------|----------|----------
1|/u/{} | {:,} | __{:,}__ | {}
2|/u/{} | {:,} | __{:,}__ | {}
3|/u/{} | {:,} | __{:,}__ | {}
4|/u/{} | {:,} | __{:,}__ | {}
5|/u/{} | {:,} | __{:,}__ | {}
6|/u/{} | {:,} | __{:,}__ | {}
7|/u/{} | {:,} | __{:,}__ | {}
8|/u/{} | {:,} | __{:,}__ | {}
9|/u/{} | {:,} | __{:,}__ | {}
10|/u/{} | {:,} | __{:,}__ | {}"""

    LOSSES_LEADERBOARD_TEMPLATE_MSG = """**Here is the LOSSES leaderboard:**

    Rank|Player|Amount Lost|Game Type
    ---------|---------|----------|----------
    1|/u/{} | __{:,}__ | {}
    2|/u/{} | __{:,}__ | {}
    3|/u/{} | __{:,}__ | {}
    4|/u/{} | __{:,}__ | {}
    5|/u/{} | __{:,}__ | {}
    6|/u/{} | __{:,}__ | {}
    7|/u/{} | __{:,}__ | {}
    8|/u/{} | __{:,}__ | {}
    9|/u/{} | __{:,}__ | {}
    10|/u/{} | __{:,}__ | {}"""

    LEADERBOARD_FULL_POST_TEMPLATE_MSG = """# Here are the leaderboards for /r/SolutionGambling!

*There are {} players in total.*

{}

&nbsp;

&nbsp;

{}

&nbsp;

&nbsp;

{}

Good luck, all!"""

    ROULETTE_INDIVIDUAL_WAGER_TEMPLATE_MSG = """Wager {}: {:,} on {}

Your outcome is : **{}**

Your winnings for this bet are {:,}

&nbsp;

"""

    ROULETTE_REPLY_WRAPPER_TEMPLATE_MSG = """/u/{},

## The roulette spin results are : ***{} {}***!

Here are your wager results:

&nbsp;

{}

&nbsp;

Your __wagers__ total {:,}

Your __winnings__  total {:,}

Your __overall profit__ is {:,}, and your __new balance__ is {:,}.

Thanks for your wager - good luck!"""

    FLAIR_SHOP_SUCCESS_MSG = """/u/{},

Your purchase of __Level {}__ flair for {:,} was successful! 

Your new balance is __{:,}__.

Enjoy!"""

    AON_DICE_ROLL_WIN_MSG = """/u/{},

You've risked your whole balance ({:,}) on this die roll, and the result is...

#__{}__!

Congratulations! Your new balance is {:,}. Good luck!"""

    AON_DICE_ROLL_LOSE_MSG = """/u/{},

You've risked your whole balance ({:,}) on this die roll, and the result is...

#__{}__!

Unfortunately, you've lost your bankroll. You'll have some points automatically deposited in just a minute!
Thanks for playing, and good luck!"""

    CASINO_WAR_REPLY_WRAPPER_TEMPLATE_MSG = """/u/{},

Thank you for your wager of {:,}! Here are your war results:

&nbsp;

{}

Your outcome is : **{}**

&nbsp;

Your __winnings__ are __{:,}__

Your __profit__ is __{:,}__

Your __new balance__ is ***{:,}***

Thanks for playing, and good luck!
"""

    CASINO_WAR_BODY_TEMPLATE = """Your card : 

    {}

Dealer's card: 

    {}"""

    DEPOSIT_AFTER_BANKRUPTCY_MSG = """/u/{},

It looks like you've lost all of your points! Don't worry - we've added some more to 
your balance. Get back out there and have fun!"""

    KENO_REPLY_WRAPPER_TEMPLATE_MSG = """/u/{},

Thank you for your wager of {:,}! Here are your keno results:

&nbsp;

{}

Your outcome is : **{}**

&nbsp;

Your __winnings__ are __{:,}__

Your __profit__ is __{:,}__

Your __new balance__ is ***{:,}***

Thanks for playing, and good luck!"""

class MiscMessages:
    SUBSCRIBER_ANNOUNCEMENT_MSG_TEMPLATE = """Hello, /u/{}!

{}

Thanks for reading and playing - good luck!"""

class MiscConstants:
    FLAIR_TIER_TITLES = {
        "" : "",
        "lvl1" : "Novice: ",
        "lvl2" : "Social Gambler: ",
        "lvl3" : "Weekend Warrior: ",
        "lvl4" : "Addict: ",
        "lvl5" : "Grinder: ",
        "lvl6" : "Advantage Player: ",
        "lvl7" : "Professional: ",
        "lvl8" : "Shark: ",
        "lvl9" : "High Roller: ",
        "lvl10": "Whale: ",
        "lvl11": "Wizard of Odds: ",
        "lvl12": "Fatcat: ",
        "lvl13": "Kingpin: ",
        "lvl14": "Moneybags: ",
        "lvl15": "Soldier of Fortune: ",
        "lvl16": "Born Lucky, I Guess: ",
        "lvl17": "Budgetary Daredevil: ",
        "lvl18": "Variance? What Variance?: ",
        "lvl19": "Filthy, Stinking Rich: ",
        "lvl20": "King Midas 2.0: ",
        "lvl21": "Disciple of RNGesus: "
    }

    FLAIR_CSS_LIST = ["", "lvl1", "lvl2", "lvl3", "lvl4", "lvl5",
                      "lvl6", "lvl7", "lvl8", "lvl9", "lvl10", "lvl11",
                      "lvl12", "lvl13", "lvl14", "lvl15", "lvl16",
                      "lvl17", "lvl18", "lvl19", "lvl20", "lvl21", ]