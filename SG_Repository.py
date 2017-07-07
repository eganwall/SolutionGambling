import ConfigParser

import pymongo
import datetime

class Repository:
    def __init__(self):
        config = ConfigParser.ConfigParser()
        config.read("settings.config")

        username = config.get("Mongo", "username")
        password = config.get("Mongo", "password")

        self.client = pymongo.MongoClient(
            "mongodb://{}:{}@solutiongambling-shard-00-00-vcw5b.mongodb.net:27017,"
            "solutiongambling-shard-00-01-vcw5b.mongodb.net:27017,"
            "solutiongambling-shard-00-02-vcw5b.mongodb.net:27017/admin?ssl=true&replicaSet=SolutionGambling-shard-0"
            "&authSource=admin".format(username, password))
        self.db = self.client.sg_db

        print('Connected to SG_DB database')

        self.playerdb = self.db.players
        self.wagerdb = self.db.wagers
        self.commentdb = self.db.comments

    '''''''''''''''''''''''''''''''''''''''''''''
	PLAYER DB QUERIES
	'''''''''''''''''''''''''''''''''''''''''''''

    def GET_PLAYER_BY_USERNAME(self, username):
        player = self.playerdb.find_one({'username': username})
        print("GET_PLAYER_BY_USERNAME returned : [player = {}]".format(str(player)))
        return player

    def GET_ALL_PLAYERS(self):
        players = self.playerdb.find()
        print("GET_ALL_PLAYERS returned {} players".format(str(players.count())))
        return players

    def GET_WEALTHIEST_PLAYERS(self, limit):
        return self.playerdb.find(limit=limit).sort('balance', pymongo.DESCENDING)

    def UPDATE_PLAYER_BALANCE_BY_USERNAME(self, username, new_balance):
        return self.playerdb.update_one({'username': username}, {'$set': {'balance': new_balance}})

    def UPDATE_PLAYER_FLAIR_BY_USERNAME(self, username, new_level, new_class):
        return self.playerdb.update_one({'username': username}, {'$set': {'flair_level': new_level, 'flair_css_class' : new_class}})

    def UPDATE_PLAYER_BALANCE_BY_ID(self, id, new_balance):
        return self.playerdb.update_one({'_id': id}, {'$set': {'balance': new_balance}})

    def DELETE_PLAYER_BY_ID(self, id):
        return self.playerdb.delete_one({'_id': id}).deleted_count

    def DELETE_PLAYER_BY_USERNAME(self, username):
        print("DELETE_PLAYER_BY_USERNAME : [username = {}]".format(username))
        delete_count = self.playerdb.delete_one({'username': username}).deleted_count
        print("DELETE_PLAYER_BY_USERNAME deleted {} user(s)".format(str(delete_count)))
        return delete_count


    def INSERT_PLAYER(self, username, balance):
        print("INSERT_PLAYER : [username = {}], [balance = {}]".format(username, balance))
        newplayer_id = self.playerdb.insert_one({'username': username, 'balance': balance,
                                                 'flair_css_class' : '', 'flair_level' : 0}).inserted_id
        print("INSERT_PLAYER returned : [ID = {}]".format(str(newplayer_id)))
        return newplayer_id

    '''''''''''''''''''''''''''''''''''''''''''''
	WAGER DB QUERIES
	'''''''''''''''''''''''''''''''''''''''''''''

    def INSERT_WAGER(self, username, outcome, wager_amt, outcome_amt, remaining_balance, game_type):
        wager_object = {'username': username, 'outcome': outcome, 'wager_amount': wager_amt,
                        'outcome_amount': outcome_amt, 'remaining_balance': remaining_balance,
                        'game_type' : game_type, 'time_created' : datetime.datetime.now()}
        return self.wagerdb.insert_one(wager_object).inserted_id

    def GET_ALL_WAGERS(self):
        wagers =  self.wagerdb.find()
        print("GET_ALL_WAGERS returned {} wagers".format(str(wagers.count())))
        return wagers

    def GET_WAGERS_BY_USERNAME(self, username):
        wagers = self.wagerdb.find({'username': username})
        print("GET_WAGERS_BY_USERNAME returned {} wagers : [username = {}]".format(
            str(wagers.count()), username
        ))
        return wagers

    def GET_TOP_WIN_WAGERS_SORTED_BY_OUTCOME_AMT(self, limit):
        return self.wagerdb.find({'outcome': WagerOutcome.WIN}, limit=limit).sort('outcome_amount', pymongo.DESCENDING)

    def GET_TOP_LOSE_WAGERS_SORTED_BY_WAGER_AMT(self, limit):
        return self.wagerdb.find({'outcome': WagerOutcome.LOSE}, limit=limit).sort('wager_amount', pymongo.DESCENDING)

    def DELETE_WAGER_BY_ID(self, id):
        return self.wagerdb.delete_one({'_id': id}).deleted_count

    '''''''''''''''''''''''''''''''''''''''''''''
        COMMENT DB QUERIES
    '''''''''''''''''''''''''''''''''''''''''''''

    def INSERT_COMMENT_ID(self, id):
        comment_id = self.commentdb.insert_one({'_id' : id}).inserted_id
        print("INSERT_COMMENT_ID returned : [ID = {}]".format(str(comment_id)))
        return comment_id

    def GET_COMMENT_BY_ID(self, id):
        comment = self.commentdb.find_one({'_id' : id})
        #print("GET_COMMENT_BY_ID returned : [comment = {}]".format(str(comment)))
        return comment


class WagerOutcome:
    WIN = 'WIN'
    LOSE = 'LOSE'