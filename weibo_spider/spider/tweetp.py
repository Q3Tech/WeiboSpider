#!/usr/bin/env python
# -*- coding: utf-8 -*-

u"""定义处理过的微博的数据结构."""

import datetime


class TweetP(object):
    u"""parsed Tweet."""

    def __init__(self):
        u"""构造函数."""
        self._dict = {}  # 存储数据
        self.uid = None  # 用户id
        self.mid = None  # Base62文本
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
        u"""更新操作, 对参数合法性进行检查."""
        for k, v in kwargs.iteritems():
            if v is None:
                continue
            if k in ('uid', 'timestamp', 'share', 'comment', 'like'):
                self.__setattr__(k, int(v))
            elif k in ('mid', 'pageurl', 'raw_html', 'text', 'location', 'device'):
                assert(isinstance(v, str) or isinstance(v, unicode))
                if isinstance(v, str):
                    v = v.decode('utf-8')
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
        u"""以人类可读格式格式化weibo数组."""
        r = u'{uid}/{mid} | '.format(uid=self.uid, mid=self.mid)
        r += datetime.datetime.fromtimestamp(self.timestamp / 1000).strftime("%Y-%m-%d %H:%M:%S")
        if self.location and len(self.location):
            r += u' @{location}'.format(location=self.location)
        if self.device and len(self.device):
            r += u' By {device}'.format(device=self.device)
        r += '\n'
        r += self.text
        r += '\n'
        if self.isforward:
            r += "Forward from {uid}/{mid}\n".format(uid=self.forward_tweet.uid, mid=self.forward_tweet.mid)
        r += '{share} share | {comment} comment | {like} like'.format(
            share=self.share, comment=self.comment, like=self.like)
        return r
