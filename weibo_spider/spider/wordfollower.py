#!/usr/bin/env python
# -*- coding: utf-8 -*-

import thread
import time

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
        self.spider = Spider(account=self.account)
        self.running = True

    def start_follow(self):
        thread.start_new_thread(self.follow_worker)

    def __update(self):
        it = self.spider.fetch_search_iter(keyword=self.wordfollow.word)
        newest_ts = self.wordfollow.newest_timestamp
        max_ts = 0
        num_new = 0
        for weibos, page, _ in it:
            for weibo in weibos:
                if weibo.timestamp >= newest_ts:  # New
                    print weibo.pretty()
                    num_new += 1
                max_ts = max(max_ts, weibo.timestamp)
            if max_ts > newest_ts:
                break
            # if page % 10 == 0:
            #     time.sleep(10)
        self.wordfollow.newest_timestamp = max(self.wordfollow.newest_timestamp, max_ts)
        self.wordfollow_dao.commit()
        return num_new

    def follow_worker(self):
        while self.running:
            self.__update()
            time.sleep(30)
