#!/usr/bin/env python
# -*- coding: utf-8 -*-

u"""Weibo."""
from sqlalchemy import Column, Integer, String, Boolean, TEXT

from db_engine import Base
from db_engine import DBEngine

from core import Singleton


class Tweet(Base):
    u"""
    表示一条新浪微博.

    id: 主键
    uid: 用户id
    mid: 微博id,整形
    isforward: 是否为转发
    content: 内容
    timestamp: 时间戳,毫秒
    device: 设备
    location： 位置
    share: 转发数
    comment: 评论数
    like: 赞数
    forward_uid: 转发的uid
    forward_mid: 转发的mid,整形
    """
    __tablename__ = 'tweet'

    id = Column(Integer, primary_key=True)
    uid = Column(Integer)
    mid = Column(Integer)
    isforward = Column(Boolean)
    content = Column(TEXT)
    timestamp = Column(Integer)
    device = Column(String(50))
    location = Column(String(50))
    share = Column(Integer)
    comment = Column(Integer)
    like = Column(Integer)
    forward_uid = Column(Integer, nullable=True)
    forward_mid = Column(Integer, nullable=True)


class TweetDAO(Singleton):

    def __init__(self):
        self.engine = DBEngine()
        self.session = self.engine.session
