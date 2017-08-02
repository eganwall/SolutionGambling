import ConfigParser
import pika
import praw
import SG_Repository
from SG_Utils import LogUtilityConstants, LogUtility
import json
import uuid

# this maps handler queue name to the submission ID's it processes
# store lists of submission id's just in case we need multiple ever
handler_map = {
    'dice_roll' : ['6nyckd'],
    'poker' : ['6o18s9'],
    'aon_die' : ['6o1enj'],
    'roulette' : ['6o1ekr'],
    'keno' : ['6o1eor'],
    'war' : ['6o1epo'],
    'flair_shop' : ['6o1er0']
}

admin_usernames = ['eganwall']

def publish_message(queue_name, message):
    message_body = json.dumps(message)
    message_id = message['message_id']

    connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))

    channel = connection.channel()
    channel.queue_declare(queue=queue_name, durable=True)
    channel.basic_publish(exchange='',
                          routing_key=queue_name,
                          body=message_body,
                          properties=pika.BasicProperties(
                              delivery_mode=2,  # make message persistent
                          )
    )
    log_msg = "Published : [queue_name={}] [comment_id={}] [username={}] [comment_body={}]".format(
        queue_name, message['comment_id'], message['username'], message['comment_body'])
    logger.log_info_message(message_id, LogUtilityConstants.message_published_event,
                            'sub_monitor', log_msg)

    connection.close()

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

# get our repository and logging utility
sg_repo = SG_Repository.Repository()
logger = LogUtility()

# get our subreddit
subreddit = reddit.subreddit('sg_playground')

logger.log_info_message('', LogUtilityConstants.monitor_startup_event,
                        'sub_monitor', 'Monitor started up - opening comment stream...')

for comment in subreddit.stream.comments(pause_after=0):
    if comment is None:
        continue

    # if we have already seen this comment, skip execution
    if sg_repo.GET_COMMENT_BY_ID(comment.id) is not None:
        continue

    # if it's an admin command, send it to the appropriate queue
    if (comment.author.name in admin_usernames) and (comment.body.strip().startswith('!')):
        message_id = str(uuid.uuid4())
        message = {'username': comment.author.name, 'comment_body': comment.body.lower(),
                   'message_id': message_id, 'comment_id': comment.id}

        # publish the message to the queue
        publish_message('admin', message)

        # flag the comment as having been processed
        sg_repo.INSERT_COMMENT_ID(comment.id)
        continue

    # see if we have a handler for this comment's parent ID
    parent_id = comment.parent().id
    #print("Comment's parent ID is {}".format(parent_id))

    handler_names_list = [k for k, v in handler_map.iteritems() if parent_id in v]
    if len(handler_names_list) > 0:
        # build our message object and dispatch message to handler
        handler_name = handler_names_list[0]
        message_id = str(uuid.uuid4())
        message = {'username' : comment.author.name, 'comment_body' : comment.body.lower(),
                   'message_id' : message_id, 'comment_id' : comment.id}

        # publish the message to the queue
        publish_message(handler_name, message)

    # flag the comment as having been processed
    sg_repo.INSERT_COMMENT_ID(comment.id)