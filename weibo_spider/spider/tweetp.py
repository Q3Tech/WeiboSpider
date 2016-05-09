#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""定义处理过的微博的数据结构."""

import datetime
import time

from core import JsonSerializable


class TweetP(JsonSerializable):
    """parsed Tweet."""

    _keys = (
        'fetch_timestamp', 'uid', 'mid', 'nickname', 'pageurl',
        'pageurl', 'raw_html', 'timestamp', 'timestamp', 'device',
        'location', 'text', 'share', 'comment', 'like', 'isforward',
        'forward_tweet',
        )

    def __init__(self, fetch_time=None):
        """构造函数."""
        self._dict = {}  # 存储数据
        self.fetch_timestamp = int(time.time() * 1000)
        self.uid = None  # 用户id
        self.mid = None  # Base62文本
        self.nickname = None
        self.pageurl = None
        self.raw_html = None  # 原始 HTML 数据
        self.timestamp = None  # 发布时间戳 毫秒
        self.device = None  # 发布设备
        self.location = None
        self.text = None
        self.share = None
        self.comment = None
        self.like = None
        self.isforward = False
        self.forward_tweet = None  # TweetP 对象,转发的微博

    def update(self, **kwargs):
        """更新操作, 对参数合法性进行检查."""
        for k, v in kwargs.items():
            if v is None:
                continue
            if k in ('uid', 'timestamp', 'share', 'comment', 'like', 'fetch_timestamp'):
                self.__setattr__(k, int(v))
            elif k in ('mid', 'pageurl', 'raw_html', 'text', 'location', 'device', 'nickname'):
                assert(isinstance(v, str))
                self.__setattr__(k, v)
            elif k in ('isforward'):
                assert(isinstance(v, bool))
                self.__setattr__(k, v)
            elif k == 'forward_tweet':
                assert(isinstance(v, TweetP))
                self.forward_tweet = v
                self.isforward = True
            else:
                self._dict[k] = v

    def pretty(self):
        """以人类可读格式格式化weibo数组."""
        r = '{uid}/{mid}\n'.format(uid=self.uid, mid=self.mid)
        r += self.nickname + ' | '
        r += datetime.datetime.fromtimestamp(self.timestamp / 1000).strftime("%Y-%m-%d %H:%M:%S")
        if self.location and len(self.location):
            r += ' @{location}'.format(location=self.location)
        if self.device and len(self.device):
            r += ' By {device}'.format(device=self.device)
        r += '\n'
        r += self.text
        r += '\n'
        if self.isforward:
            r += "Forward from {uid}/{mid}\n".format(uid=self.forward_tweet.uid, mid=self.forward_tweet.mid)
        r += '{share} share | {comment} comment | {like} like'.format(
            share=self.share, comment=self.comment, like=self.like)
        return r

    def to_json_dict(self):
        json_dict = {}
        for key in self._keys:
            json_dict[key] = self.__getattribute__(key)
        return json_dict
