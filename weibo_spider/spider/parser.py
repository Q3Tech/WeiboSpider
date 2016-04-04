#!/usr/bin/env python
# -*- coding: utf-8 -*-
import re
import json
from bs4 import BeautifulSoup


class Parser(object):
    """
    新浪微博HTML解析的工具
    """
    base62_base = '0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ'

    def __init__(self):
        self._weibo_url_pattern = re.compile(r'\/(?P<user_id>\d+)\/(?P<mid>[0-9a-zA-Z]+)')
        self._embed_html_pattern = re.compile(r'\"html\":\"((?:[^"\\]|\\.)*)\"')

    @classmethod
    def base62_decode(cls, text):
        result = 0
        for c in text:
            result *= 62
            result += cls.base62_base.find(c)
            print result
        return result

    @classmethod
    def base62_encode(cls, num):
        assert(isinstance(num, int))
        result = ''
        while num:
            result = cls.base62_base[num % 62] + result
            num /= 62
        return result

    @classmethod
    def mid_decode(cls, text):
        first = len(text) % 4
        result = cls.base62_decode(text[:first])
        for i in range(first, len(text), 4):
            result *= 10000000
            result += cls.base62_decode(text[i:i + 4])
        return result

    @classmethod
    def mid_encode(cls, mid):
        assert(isinstance(mid, int))
        result = ''
        while mid:
            result = cls.base62_encode(mid % 10000000) + result
            mid /= 10000000
        return result

    def parse_weibo_url(self, text):
        groups = self._weibo_url_pattern.search(text)
        if groups:
            return groups.group('user_id'), groups.group('mid')
        else:
            return None, None

    def embed_html_iter(self, text):
        for g in self._embed_html_pattern.finditer(text):
            yield json.loads('"' + g.group(1) + '"')

    def parse_weibo(self, text):
        weibos = []
        soup = BeautifulSoup(text, 'html.parser')
        for item in soup.findAll('div', attrs={'action-type': 'feed_list_item'}):
            weibo = {}
            comment_txt = item.find(class_='comment_txt')
            weibo['comment_txt'] = comment_txt.text
            feed_from = item.findAll(class_='feed_from')[-1]
            time_and_url = feed_from.find(date=True)
            pageurl = time_and_url.attrs['href']
            weibo['pageurl'] = pageurl
            user_id, mid = self.parse_weibo_url(pageurl)
            weibo['user_id'] = user_id
            weibo['mid'] = mid
            weibo['timestamp'] = int(time_and_url.attrs['date'])
            print comment_txt.text.encode('utf-8')
            print weibo
            weibos.append(weibo)
        return weibos
