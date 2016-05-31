#!/usr/bin/env python
# -*- coding: utf-8 -*-
import logging
import tornado.web
import tornado.websocket
import json
from collections import defaultdict

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
        tweets = tweet_dao.get_tweetp_from_mids(mids=mids)
        self.set_header('Content-Type', 'application/javascript')
        self.write(json.dumps(tweets, cls=JsonSerializableEncoder))


class WordFollowUpdateHandler(tornado.websocket.WebSocketHandler):

    connections = {}
    max_connection_id = 0
    word_connection = defaultdict(lambda: set())
    connection_word = defaultdict(lambda: set())

    @classmethod
    def get_new_connection_id(cls):
        cls.max_connection_id += 1
        return cls.max_connection_id

    def open(self):
        self.connection_id = self.get_new_connection_id()
        self.connections[self.connection_id] = self
        self.logger = logging.getLogger('WordFollowUpdateHandler')
        self.logger.debug('New connection, id = {0}'.format(self.connection_id))

    def on_message(self, message):
        message = json.loads(message)
        action = message['action']
        word = message['word']
        self.logger.debug('connection {0} on message, action = {1}, word = {2}'.format(
            self.connection_id, action, word))
        if action == 'bind':
            self.word_connection[word].add(self.connection_id)
            self.connection_word[self.connection_id].add(word)
        elif action == 'unbind':
            if self.connection_id in self.word_connection[word]:
                self.word_connection[word].remove(self.connection_id)
            if word in self.connection_word[self.connection_id]:
                self.connection_word[self.connection_id].remove(word)

    def on_close(self):
        for word in self.connection_word[self.connection_id]:
            if self.connection_id in self.word_connection[word]:
                self.word_connection[word].remove(self.connection_id)
            if self.connection_id in self.connection_word:
                self.connection_word.pop(self.connection_id)

    @classmethod
    def update(cls, word, mids):
        if len(cls.word_connection[word]) == 0:
            return
        tweet_dao = TweetDAO()
        tweets = tweet_dao.get_tweetp_from_mids(mids=mids)
        body = json.dumps({
                'word': word,
                'tweets': tweets,
                'mids': list(mids)
            },
            cls=JsonSerializableEncoder
        )
        for connection_id in cls.word_connection[word]:
            cls.connections[connection_id].write_message(body)
