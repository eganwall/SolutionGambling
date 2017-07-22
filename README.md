# SolutionGambling

## http://reddit.com/r/SolutionGambling to see it in action!

### Next Steps:
Currently working on a v2.0 refactor/rewrite that will do away with having separate bots all watching the Reddit threads, and will implement a single monitor script with a subreddit comment stream open. This monitor will do the following:

* catch new comments as they come into the sub in real time
* check to see if the comment's parent ID matches any of our game thread ID's
* if so, drop a message in a RabbitMQ queue to be picked up by the appropriate game handler
* handle rate limit checking and declining wager requests if user is surpassing the allowed rate

This v2.0 code will (ideally) include rate limiting as mentioned above to help combat the spamming problem, as well as infrastructure changes and end-to-end logging via Splunk for monitoring purposes. 

At this point (as of 7.22.17) I've set up RabbitMQ and Splunk, implemented the monitor on a testing subreddit, and migrated about half of the bots over to handler scripts. After migration is complete, I'll clean up the code, commit it, and begin on the rate-limiting feature.

After that, it's back to adding games and features!
