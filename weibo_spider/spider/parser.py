#!/usr/bin/env python
# -*- coding: utf-8 -*-
u"""用于抓取结果和中间结果的解析的模块."""
import re
import json
import urlparse
import datetime

from functools import wraps

from bs4 import BeautifulSoup


def ensure_soup(func):
    u"""装饰器,如果soup本身是unicode或者str,将其转变成soup."""
    @wraps(func)
    def wrapper(self, soup, *args, **kwargs):
        if isinstance(soup, str) or isinstance(soup, unicode):
            soup = BeautifulSoup(soup, 'html.parser')
        return func(self=self, soup=soup, *args, **kwargs)
    return wrapper


class Parser(object):
    u"""新浪微博HTML解析类."""

    base62_base = '0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ'

    def __init__(self):
        u"""Constructer."""
        self._weibo_url_pattern = re.compile(r'\/(?P<user_id>\d+)\/(?P<mid>[0-9a-zA-Z]+)')
        self._embed_html_pattern = re.compile(r'\"html\":\"((?:[^"\\]|\\.)*)\"')

    @classmethod
    def base62_decode(cls, text):
        u"""将base62字符串转为10进制整数."""
        result = 0
        for c in text:
            result *= 62
            result += cls.base62_base.find(c)
            print result
        return result

    @classmethod
    def base62_encode(cls, num):
        u"""将10进制整数转为 base62 字符串."""
        assert(isinstance(num, int))
        result = ''
        while num:
            result = cls.base62_base[num % 62] + result
            num /= 62
        return result

    @classmethod
    def mid_decode(cls, text):
        u"""
        将微博连接 mid 转为整形形式.

        转换方式：从结尾开始4个字符一组,1e7进制
        e.g.:
        > mid_decode('z579Hz9Wr')
        3512191498379699
        """
        first = len(text) % 4
        result = cls.base62_decode(text[:first])
        for i in range(first, len(text), 4):
            result *= 10000000
            result += cls.base62_decode(text[i:i + 4])
        return result

    @classmethod
    def mid_encode(cls, mid):
        u"""将整形 mid 转为字符型."""
        assert(isinstance(mid, int))
        result = ''
        while mid:
            result = cls.base62_encode(mid % 10000000) + result
            mid /= 10000000
        return result

    def parse_weibo_url(self, text):
        u"""
        将微博url分解为 uid 和 mid 部分.

        e.g.:
        > parse_weibo_url('http://weibo.com/1696218363/DmB4uDgQB')
        ('1696218363', 'DmB4uDgQB')
        """
        groups = self._weibo_url_pattern.search(text)
        if groups:
            return groups.group('user_id'), groups.group('mid')
        else:
            return None, None

    def embed_html_iter(self, text):
        u"""
        在文件中抽出内嵌在JS中的HTML.

        {'xxx':'yyyy', 'html':'<embed_html>'}
        中的<embed_html>
        """
        for g in self._embed_html_pattern.finditer(text):
            yield json.loads('"' + g.group(1) + '"')

    @ensure_soup
    def parse_search_result(self, soup):
        u"""返回搜索页中的所有微博."""
        weibos = []
        for item in soup.findAll('div', attrs={'action-type': 'feed_list_item'}):
            weibo = {}
            comment_txt = item.find(class_='comment_txt')
            location = self.parse_location(comment_txt, decompose=True)
            weibo['location'] = location
            weibo['text'] = comment_txt.text

            # 链接,时间,设备
            feed_from = item.findAll(class_='feed_from')[-1]
            pageurl, timestamp, device = self.parse_time_url_device(feed_from)
            weibo['pageurl'] = pageurl
            user_id, mid = self.parse_weibo_url(pageurl)
            weibo['user_id'] = user_id
            weibo['mid'] = mid
            weibo['timestamp'] = timestamp

            # 转发,评论,赞
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
        u"""
        在时间和设备行返回微博链接,发布时间戳,发布设备.

        时间戳是整形毫秒值
        return pageurl, timestamp, device
        """
        time_and_url = soup.find(date=True)
        pageurl = time_and_url.attrs['href']
        timestamp = int(time_and_url.attrs['date'])
        links = soup.findAll('a')
        device = links[1].text if len(links) > 1 else None
        return pageurl, timestamp, device

    @ensure_soup
    def parse_share_comment_like(self, soup):
        u"""
        抽取转发数评论数和赞数.

        要求DOM树种只有li包含数据,而且最后三个li分别为转发,评论,赞

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
        u"""
        处理延迟加载的框(常见于话题页面).

        返回其中的 action-data 的字典
        """
        return {
            'action-data': urlparse.parse_qs(soup.attrs['action-data'])
        }

    @ensure_soup
    def extract_topic_weibo(self, soup):
        u"""
        处理从话题页面或者普通页面爬去的微博.

        return 微博的数组
        """
        weibos = []
        for item in soup.findAll('div', attrs={'action-type': 'feed_list_item'}):
            weibo = {}

            wb_text = item.find(class_='WB_text')
            location = self.parse_location(wb_text, decompose=True)
            weibo['location'] = location
            weibo['text'] = wb_text.text

            # 链接,时间,设备
            wb_from = item.find(class_='WB_from')
            pageurl, timestamp, device = self.parse_time_url_device(wb_from)
            user_id, mid = self.parse_weibo_url(pageurl)
            weibo.update({
                'pageurl': pageurl,
                'timestamp': timestamp,
                'device': device,
                'user_id': user_id,
                'mid': mid
            })
            wb_handle = item.findAll(class_='WB_handle')[-1]

            # 转发,评论,赞
            share, comment, like = self.parse_share_comment_like(wb_handle)
            weibo.update({
                'share': share,
                'comment': comment,
                'like': like
            })
            print self.pretty_weibo(weibo) + '\n'
            weibos.append(weibo)
        return weibos

    @ensure_soup
    def parse_location(self, soup, decompose=False):
        u"""
        抽取位置信息.

        如果 decompose=True, 则从soup中删除位置，避免打乱文本
        """
        icon = soup.find(class_='ficon_cd_place')
        if not icon:
            return None
        link = icon.parent
        location = link.attrs['title']
        if decompose:
            link.decompose()
        return location

    def parse_topic_result(self, text, is_json):
        u"""
        处理从topic 页面抓取的HTML，包括Ajax方法取得的部分.

        is_json = True 则认为是Ajax 数据，从其中data键中抽取HTML

        返回：weibos, lazyload, next_url
        weibos: 微博数组
        lazyload: lazyload 的 action-data 数据（如果有）
        next_url: 下一页的url （如果有）
        """
        lazyload = None
        next_url = None
        weibos = []
        if is_json:
            embed_html_iter = [json.loads(text)['data']]
        else:
            embed_html_iter = self.embed_html_iter(text)

        for embed_html in embed_html_iter:
            soup = BeautifulSoup(embed_html, 'html.parser')
            lazyload = soup.find('div', attrs={'node-type': 'lazyload'}) or lazyload
            _, _, next_page = self.split_pages_bar(soup)
            if next_page:
                next_url = next_page.attrs['href']
            weibos += self.extract_topic_weibo(soup)
        if lazyload:
            lazyload = self.parse_lazyload(lazyload)
        return weibos, lazyload, next_url

    @ensure_soup
    def split_pages_bar(self, soup):
        u"""拆分上一页, 页list, 下一页."""
        w_pages = soup.find('div', class_='W_pages')
        if not w_pages:
            return None, None, None
        prev_page = w_pages.find('a', class_='prev')
        page_list = w_pages.find('span', class_='list')
        next_page = w_pages.find('a', class_='next')
        return prev_page, page_list, next_page

    @classmethod
    def pretty_weibo(cls, weibo):
        u"""以人类可读格式格式化weibo数组."""
        r = u''
        r += datetime.datetime.fromtimestamp(weibo['timestamp'] / 1000).strftime("%Y-%m-%d %H:%M:%S")
        if weibo['location'] and len(weibo['location']):
            r += u' @{location}'.format(location=weibo['location'])
        if weibo['device'] and len(weibo['device']):
            r += u' By {device}'.format(device=weibo['device'])
        r += '\n'
        r += weibo['text']
        r += '\n'
        r += '{share} share | {comment} comment | {like} like'.format(
            share=weibo['share'], comment=weibo['comment'], like=weibo['like'])
        return r
