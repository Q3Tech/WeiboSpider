#!/usr/bin/env python
# -*- coding: utf-8 -*-
import tornado.web
import json

from core import JsonSerializableEncoder
from db import WordFollowTweetDAO
from db import TweetDAO


class WordUpdateHandler(tornado.web.RequestHandler):
    """返回关键字下最近50条微博"""
    def get(self):
        wordfollowtweet_dao = WordFollowTweetDAO()
        tweet_dao = TweetDAO()
        word = self.get_query_argument('word')
        mids = wordfollowtweet_dao.get_word_latest_mids(word)
        print(mids)
        tweets = tweet_dao.get_tweetp_from_mids(mids=mids)
        self.set_header('Content-Type', 'application/javascript')
        self.write(json.dumps(tweets, cls=JsonSerializableEncoder))
