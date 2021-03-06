#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""用于抓取结果和中间结果的解析的模块."""
import re
import json
import urllib.parse
import logging

from functools import wraps

from bs4 import BeautifulSoup

from .tweetp import TweetP


def ensure_soup(func):
    """装饰器,如果soup本身是unicode或者str,将其转变成soup."""
    @wraps(func)
    def wrapper(self, soup, *args, **kwargs):
        if isinstance(soup, str):
            soup = BeautifulSoup(soup, 'lxml')
        body = soup.find('body')
        if body:
            soup = next(body.children)
        try:
            return func(self=self, soup=soup, *args, **kwargs)
        except Exception:
            import os
            import settings
            import uuid
            uuid_filename = str(uuid.uuid4()) + '.txt.html'
            filename = os.path.join(settings.SAMPLES_DIR,  uuid_filename)
            with open(filename, 'w') as file:
                file.write(str(soup))
            logging.error('Sample saved to {filename}'.format(filename=uuid_filename))
            raise

    return wrapper


class Parser(object):
    """新浪微博HTML解析类."""

    base62_base = '0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ'

    def __init__(self):
        """Constructer."""
        self._weibo_url_pattern = re.compile(r'weibo\.com\/(?P<uid>\d*)\/(?P<mid>[0-9a-zA-Z]+)')  # 被删除的微博id为空
        self._embed_html_pattern = re.compile(r'\"html\":\"((?:[^"\\]|\\.)*)\"')

    @classmethod
    def base62_decode(cls, text):
        """将base62字符串转为10进制整数."""
        result = 0
        for c in text:
            result *= 62
            result += cls.base62_base.find(c)
        return result

    @classmethod
    def base62_encode(cls, num):
        """将10进制整数转为 base62 字符串."""
        assert(isinstance(num, int))
        result = ''
        while num:
            result = cls.base62_base[num % 62] + result
            num //= 62
        return result

    @classmethod
    def mid_decode(cls, text):
        """
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
        """将整形 mid 转为字符型."""
        assert(isinstance(mid, int))
        result = ''
        while mid:
            result = cls.base62_encode(mid % 10000000) + result
            mid //= 10000000
        return result

    @classmethod
    def get_soup(cls, text):
        return BeautifulSoup(text, 'lxml')

    def parse_weibo_url(self, text):
        """
        将微博url分解为 uid 和 mid 部分.

        e.g.:
        > parse_weibo_url('http://weibo.com/1696218363/DmB4uDgQB')
        ('1696218363', 'DmB4uDgQB')
        """
        groups = self._weibo_url_pattern.search(text)
        if groups:
            return groups.group('uid'), groups.group('mid')
        else:
            return None, None

    def embed_html_iter(self, text):
        """
        在文件中抽出内嵌在JS中的HTML.

        {'xxx':'yyyy', 'html':'<embed_html>'}
        中的<embed_html>
        """
        for g in self._embed_html_pattern.finditer(text):
            yield json.loads('"' + g.group(1) + '"')

    @ensure_soup
    def parse_time_url_device(self, soup):
        """
        在时间和设备行返回微博链接,发布时间戳,发布设备.

        时间戳是整形毫秒值
        return pageurl, timestamp, device
        """
        time_and_url = soup.find(date=True)
        pageurl = time_and_url.attrs['href']
        timestamp = int(time_and_url.attrs['date']) if time_and_url.attrs['date'] else None
        links = soup.findAll('a')
        device = links[1].text if len(links) > 1 else None
        return pageurl, timestamp, device

    @ensure_soup
    def parse_share_comment_like(self, soup):
        """
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
        """
        处理延迟加载的框(常见于话题页面).

        返回其中的 action-data 的字典
        """
        return {
            'action-data': urllib.parse.parse_qs(soup.attrs['action-data'])
        }

    @ensure_soup
    def extract_search_weibo(self, soup):
        """返回搜索页中的所有微博."""
        weibos = []
        for item in soup.findAll('div', attrs={'action-type': 'feed_list_item'}):
            weibo = self.parse_weibo(item)
            weibos.append(weibo)
        return weibos

    @ensure_soup
    def extract_topic_weibo(self, soup):
        """
        处理从话题页面或者普通页面爬取的微博.

        return 微博的数组
        """
        weibos = []
        for item in soup.findAll('div', attrs={'action-type': 'feed_list_item'}):
            weibo = self.parse_weibo(item)
            weibos.append(weibo)
        return weibos

    @ensure_soup
    def extract_forward_content(self, soup, decompose=False):
        """
        抽取微博中转发的原文信息.

        特征: node-type="feed_list_forwardContent"
        forwardContent 中不会再含有 forwardContent

        return weibo
        """
        if soup.attrs.get('node-type') != 'feed_list_forwardContent':
            soup = soup.find(attrs={'node-type': 'feed_list_forwardContent'})
        if not soup:
            return None

        # 搜索页中的情况
        if soup.parent and 'class' in soup.parent.attrs and \
           'comment_info' in soup.parent.attrs['class']:
            soup = soup.parent

        weibo = self.parse_weibo(soup=soup, parse_forward=False)  # 不再寻找 forward

        if decompose:
            soup.decompose()
        return weibo

    @ensure_soup
    def parse_weibo(self, soup, parse_forward=True, decompose=False):
        """
        统一的微博解析函数(单条).

        parse_forward: 是否进一步解析转发
        decompose: 是否销毁部分
        """
        weibo = TweetP()
        weibo.update(raw_html=str(soup))

        # 转发内容
        if parse_forward:
            forward_soup = soup.find(attrs={'node-type': 'feed_list_forwardContent'})
            if forward_soup:
                forward_weibo = self.extract_forward_content(soup=forward_soup, decompose=True)
                weibo.update(forward_tweet=forward_weibo)

        # 链接,时间,设备
        wb_from = soup.find(class_='WB_from') or soup.find(class_='feed_from')
        pageurl, timestamp, device = self.parse_time_url_device(wb_from)
        user_id, mid = self.parse_weibo_url(pageurl)
        if not user_id:  # 已删除
            weibo.update(uid=0, mid=mid)
            if decompose:
                soup.decompose()
            return weibo
        weibo.update(
            pageurl=pageurl,
            timestamp=timestamp,
            device=device,
            uid=user_id,
            mid=mid
        )

        # 昵称
        nickname = soup.find(**{'nick-name': True}).attrs['nick-name']
        weibo.update(nickname=nickname)

        # 转发,评论,赞
        wb_handle = soup.find(class_='WB_handle') or soup.find(class_='feed_action')
        share, comment, like = self.parse_share_comment_like(wb_handle)
        weibo.update(
            share=share,
            comment=comment,
            like=like
        )

        # 文本
        wb_text = soup.find(class_='WB_text') or soup.find(class_='comment_txt')
        location = self.parse_location(wb_text, decompose=True)  # 破坏性操作
        weibo.update(location=location, text=wb_text.text.strip())

        if decompose:
            soup.decompose()
        return weibo

    @ensure_soup
    def parse_location(self, soup, decompose=False):
        """
        抽取位置信息.

        如果 decompose=True, 则从soup中删除位置，避免打乱文本
        """
        icon = soup.find(class_=['ficon_cd_place', 'icon_cd_place'])
        if not icon:
            return None
        link = icon.parent
        if 'title' not in link.attrs:
            link = link.parent
        location = link.attrs['title']
        if decompose:
            link.decompose()
        return location

    @ensure_soup
    def split_pages_bar(self, soup):
        """拆分上一页, 页list, 下一页."""
        w_pages = soup.find('div', class_='W_pages')
        if not w_pages:
            return None, None, None
        prev_page = w_pages.find('a', class_='prev')
        page_list = w_pages.find('span', class_='list')
        next_page = w_pages.find('a', class_='next')
        return prev_page, page_list, next_page

    def parse_topic_result(self, text, is_json):
        """
        处理从topic 页面抓取的HTML，包括Ajax方法取得的部分.

        is_json = True 则认为是Ajax 数据，从其中data键中抽取HTML

        返回：weibos, lazyload, next_url
        weibos: 微博数组
        lazyload: lazyload 的 action-data 数据（如果有）
        next_url: 下一页的url （如果有）（url一般是相对路径）
        """
        lazyload = None
        next_url = None
        weibos = []
        if is_json:
            embed_html_iter = [json.loads(text)['data']]
        else:
            embed_html_iter = self.embed_html_iter(text)

        for embed_html in embed_html_iter:
            soup = BeautifulSoup(embed_html, 'lxml')
            lazyload = soup.find('div', attrs={'node-type': 'lazyload'}) or lazyload
            _, _, next_page = self.split_pages_bar(soup)
            if next_page:
                next_url = next_page.attrs['href']
            weibos += self.extract_topic_weibo(soup)
        if lazyload:
            lazyload = self.parse_lazyload(lazyload)
        return weibos, lazyload, next_url

    def parse_search_result(self, text):
        """
        解析search返回的html.

        返回：weibos, lazyload, next_url
        weibos: 微博数组
        lazyload: 固定为 None
        next_url: 下一页的url （如果有）（url一般是相对路径）
        """
        weibos = []
        next_url = None
        for embed_html in self.embed_html_iter(text):
            soup = BeautifulSoup(embed_html, 'lxml')
            _, _, next_page = self.split_pages_bar(soup)
            if next_page:
                next_url = next_page.attrs['href']
            weibos += self.extract_search_weibo(soup)
        return weibos, None, next_url
