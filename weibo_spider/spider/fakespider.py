#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""用于在离线环境下调试爬虫其他部件的替身爬虫."""
import logging
import time

from .tweetp import TweetP
from .parser import Parser


class FakeSpider(object):

    def __init__(self, account):
        self.logger = logging.getLogger('FakeSpider')
        self.account = account
        self.logger.info("Fake Spider initialized, account: {0}".format(account.email))

    def get_cookies_json(self):
        return self.account.cookies

    def fetch_search_iter(self, keyword, start_page=1):

        for page in range(start_page, start_page + 2):
            weibos = []
            for i in range(20):
                weibo = TweetP()
                weibo.update(**{
                    'mid': Parser.mid_encode(page * 100 + i),
                    'uid': 10086,
                    'text': 'keyword {0}, i = {1}'.format(keyword, i),
                    'nickname': '测试用稻草娃娃',
                    'timestamp': int(time.time() * 1000),
                    'share': 0,
                    'comment': 1,
                    'like': 2,
                    'raw_html': '<div></div>',
                    'device': '稻草娃娃',
                })
                weibos.append(weibo)
            yield weibos, page, False
