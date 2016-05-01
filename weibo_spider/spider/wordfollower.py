#!/usr/bin/env python
# -*- coding: utf-8 -*-

import thread
import time
import logging

from spider import Spider
from db.wordfollow import WordFollowDAO
from db.account import AccountDAO


class WordFollower(object):
    u"""用于跟踪某一关键词的爬虫封装."""

    def __init__(self, word, account=None):
        self.wordfollow_dao = WordFollowDAO()
        self.wordfollow = self.wordfollow_dao.get_or_create(word=word)
        if not account:
            account_dao = AccountDAO()
            account = account_dao.get_random_account()
        print account
        self.account = account
        self.spider = Spider(account=self.account, rawdata_dao=True, tweet_dao=True)
        self.running = True
        self.fetch_interval = 30

    def start_follow(self):
        thread.start_new_thread(self.follow_worker, ())

    def __update(self):
        it = self.spider.fetch_search_iter(keyword=self.wordfollow.word)
        newest_ts = self.wordfollow.newest_timestamp
        min_ts = int((time.time() + 3600) * 1000)
        max_ts = 0
        num_new = 0
        logging.info('start __update loop.')
        for weibos, page, _ in it:
            logging.info('__update page {0}.'.format(page))
            for weibo in weibos:
                if weibo.timestamp >= newest_ts:  # New
                    print weibo.pretty()
                    num_new += 1
                max_ts = max(max_ts, weibo.timestamp)
                min_ts = min(min_ts, weibo.timestamp)
            logging.info("min_ts={min_ts}, max_ts={max_ts}, newest_ts={newest_ts}.".format(
                min_ts=min_ts, max_ts=max_ts, newest_ts=newest_ts))
            if min_ts < newest_ts:
                logging.info('break __update.')
                break
            # if page % 10 == 0:
            #     time.sleep(10)
        self.wordfollow.newest_timestamp = max(self.wordfollow.newest_timestamp, max_ts)
        self.wordfollow_dao.commit()
        return num_new

    def follow_worker(self):
        while self.running:
            num_new = self.__update()
            fetch_interval = self.fetch_interval
            if num_new > 30:
                fetch_interval *= 0.618
            elif num_new < 10:
                fetch_interval *= 1.618
            fetch_interval = min(300, max(20, fetch_interval))
            self.fetch_interval = int(fetch_interval)
            word = self.wordfollow.word
            word = word.encode('utf-8') if isinstance(word, unicode) else word
            logging.info('WordFollower {0} got {1} new, and going to sleep {2} seconds.'.format(
                word, num_new, self.fetch_interval))
            time.sleep(self.fetch_interval)
