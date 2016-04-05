#!/usr/bin/env python
# -*- coding: utf-8 -*-
import re
import json
import urlparse

from functools import wraps

from bs4 import BeautifulSoup


def ensure_soup(func):
    """
    装饰器，如果soup本身是unicode或者str，将其转变成soup
    """
    @wraps(func)
    def wrapper(self, soup, *args, **kwargs):
        if isinstance(soup, str) or isinstance(soup, unicode):
            soup = BeautifulSoup(soup, 'html.parser')
        return func(self=self, soup=soup, *args, **kwargs)
    return wrapper


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

    @ensure_soup
    def parse_search_result(self, soup):
        weibos = []
        for item in soup.findAll('div', attrs={'action-type': 'feed_list_item'}):
            weibo = {}
            comment_txt = item.find(class_='comment_txt')
            weibo['comment_txt'] = comment_txt.text

            # 时间，链接，设备
            feed_from = item.findAll(class_='feed_from')[-1]
            pageurl, timestamp, device = self.parse_time_url_device(feed_from)
            weibo['pageurl'] = pageurl
            user_id, mid = self.parse_weibo_url(pageurl)
            weibo['user_id'] = user_id
            weibo['mid'] = mid
            weibo['timestamp'] = timestamp

            # 转发，评论，赞
            feed_action = item.findAll(class_='feed_action')[-1]
            share, comment, like = self.parse_share_comment_like(feed_action)
            weibo['share'] = share
            weibo['comment'] = comment
            weibo['like'] = like

            weibos.append(weibo)
            self.last_text = soup

        return weibos

    @ensure_soup
    def parse_time_url_device(self, soup):
        """
        return timestamp, url, device
        """
        time_and_url = soup.find(date=True)
        pageurl = time_and_url.attrs['href']
        timestamp = int(time_and_url.attrs['date'])
        device = soup.findAll('a')[1].text
        return pageurl, timestamp, device

    @ensure_soup
    def parse_share_comment_like(self, soup):
        """
        ensure: contain 3 or li
        return share, comment, like
        """
        def soup_to_num(element):
            element = re.search('\d+', element.text)
            return 0 if not element else int(element.group(0))
        lis = soup.findAll('li')
        if len(lis) > 3:
            lis = lis[-3:]
        return soup_to_num(lis[0]), soup_to_num(lis[1]), soup_to_num(lis[2])

    @ensure_soup
    def parse_lazyload(self, soup):
        """
        """
        return {
            'action-data': urlparse.parse_qs(soup.attrs['action-data'])
        }
    def parse_topic_result(self, text):
        """
        return weibos, lazyload
        """
        lazyload = None
        for embed_html in self.embed_html_iter(text):
            soup = BeautifulSoup(embed_html, 'html.parser')
            lazyload = soup.find('div', attrs={'node-type': 'lazyload'}) or lazyload
        weibos = []
        lazyload = self.parse_lazyload(lazyload)
        return weibos, lazyload