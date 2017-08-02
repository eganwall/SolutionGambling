import ConfigParser
import praw
import time

import SG_Repository
import SG_Messages

config = ConfigParser.ConfigParser()
config.read("settings.config")

base_balance = int(config.get("General", "starting_balance"))

version = config.get("General", "version")
logger_name = "sg_utils"

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

subreddit = reddit.subreddit('sg_playground')

def add_new_player(username, message_id):
    sg_repo.INSERT_PLAYER(username, base_balance)
    update_player_flair(username, base_balance, '')

    log_msg = "Adding new player : [username={}] [new_balance={}]".format(username, base_balance)
    LogUtility().log_info_message(message_id, LogUtilityConstants.player_added_event,
                                  logger_name, log_msg)

    reddit.redditor(username).message('Welcome!',
                                      SG_Messages.ReplyMessages.NEW_PLAYER_WELCOME_MESSAGE.format(username),
                                      from_subreddit='/r/SolutionGambling')

def update_player_after_wager(username, new_balance, flair_class, message_id=''):
    if new_balance <= 0:
        new_balance = base_balance + (SG_Messages.MiscConstants.FLAIR_CSS_LIST.index(flair_class) * 2500)

        log_msg = "Reloading player : [username={}] [new_balance={}]".format(username, new_balance)
        LogUtility().log_info_message(message_id, LogUtilityConstants.player_reloaded_event,
                                      logger_name, log_msg)

        reddit.redditor(username).message('More points!',
                                          SG_Messages.ReplyMessages.DEPOSIT_AFTER_BANKRUPTCY_MSG.format(username),
                                          from_subreddit='/r/SolutionGambling')

    sg_repo.UPDATE_PLAYER_BALANCE_BY_USERNAME(username, new_balance)
    update_player_flair(username, new_balance, flair_class, message_id)

def update_player_flair(player, flair, flair_class, message_id=''):
    start_time = time.time()

    if (player == 'eganwall'):
        subreddit.flair.set(player, "Pit Boss : {:,}".format(flair), flair_class)
    else:
        subreddit.flair.set(player, "{}{:,}".format(SG_Messages.MiscConstants.FLAIR_TIER_TITLES[flair_class], flair), flair_class)

    end_time = time.time()

    log_msg = "[username=/u/{}] [flair_update_time={:.3f}] [auth_limits={} : {}]".format(player, get_elapsed_secs(start_time, end_time), reddit.user.me(), reddit.auth.limits)
    LogUtility().log_info_message(message_id, LogUtilityConstants.flair_updated_event, logger_name, log_msg)

def get_elapsed_secs(start_tstamp, end_tstamp):
    return end_tstamp - start_tstamp

def post_comment_reply(comment, comment_body, message_id):
    start_time = time.time()
    comment.reply(comment_body)
    end_time = time.time()

    log_msg = "[comment_id={}] [reply_time={:.3f}] [auth_limits={} : {}]".format(comment.id, get_elapsed_secs(start_time, end_time), reddit.user.me(), reddit.auth.limits)
    LogUtility().log_info_message(message_id, LogUtilityConstants.reply_posted_event,
                                  logger_name, log_msg)

# ===========================================
#       Logging Utility
# ===========================================


class LogUtilityConstants:
    error_loglevel = "ERROR"
    warn_loglevel = "WARN"
    info_loglevel = "INFO"

    insufficient_balance_reason = "INSUFFICIENT_BALANCE"
    incorrect_format_reason = "INCORRECT_FORMAT"
    over_max_bet_reason = "OVER_MAX_BET"
    max_flair_level_reason = "MAX_FLAIR_LEVEL"

    monitor_startup_event = "MONITOR_STARTUP"
    handler_startup_event = "HANDLER_STARTUP"
    message_published_event = "MESSAGE_PUBLISHED"
    deposit_success_event = "ADMIN_DEPOSIT_SUCCESS"
    flair_req_event = "FLAIR_UPGRADE_REQUEST"
    wager_rejected_event = "WAGER_REJECTED"
    flair_rejected_event = "FLAIR_UPGRADE_REJECTED"
    wager_validated_event = "WAGER_VALIDATED"
    wager_executed_event = "WAGER_EXECUTED"
    flair_executed_event = "FLAIR_UPGRADE_EXECUTED"
    handler_finished_event = "HANDLER_FINISHED"
    exception_event = "EXCEPTION"
    player_reloaded_event = "PLAYER_RELOADED"
    player_added_event = "PLAYER_ADDED"
    reply_posted_event = "REPLY_POSTED"
    flair_updated_event = "FLAIR_UPDATED"

class LogUtility:
    def log_message(self, loglevel, message_id, event_type, logger, log_msg):
        loglevel_key = "LOGLEVEL={}".format(loglevel)
        message_id_key = "MESSAGE_ID={}".format(message_id)
        event_type_key = "EVENT_TYPE={}".format(event_type)
        logger_key = "LOGGER={}".format(logger)
        log_msg_key = "LOGMSG=[{}]".format(log_msg)

        log_string = "{} {} {} {} {}".format(loglevel_key, message_id_key,
                                             event_type_key, logger_key, log_msg_key)

        print(log_string)

    def log_info_message(self, message_id, event_type, logger, log_msg):
        self.log_message(LogUtilityConstants.info_loglevel, message_id, event_type,
                         logger, log_msg)

    def log_warn_message(self, message_id, event_type, logger, log_msg):
        self.log_message(LogUtilityConstants.warn_loglevel, message_id, event_type,
                         logger, log_msg)

    def log_error_message(self, message_id, event_type, logger, log_msg):
        self.log_message(LogUtilityConstants.error_loglevel, message_id, event_type,
                         logger, log_msg)
