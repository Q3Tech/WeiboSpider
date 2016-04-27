#!/usr/bin/env python
# -*- coding: utf-8 -*-

u"""Weibo."""
from sqlalchemy import Column, Integer, String, Boolean, TEXT, BIGINT

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
    fetch_timestamp = Column(BIGINT)
    uid = Column(BIGINT)
    mid = Column(String(12))
    nickname = Column(String(61))
    isforward = Column(Boolean)
    text = Column(TEXT)
    timestamp = Column(BIGINT)
    device = Column(String(50))
    location = Column(String(50))
    share = Column(Integer)
    comment = Column(Integer)
    like = Column(Integer)
    forward_uid = Column(BIGINT, nullable=True)
    forward_mid = Column(String(12), nullable=True)


class TweetDAO(Singleton):

    def __init__(self):
        self.engine = DBEngine()
        self.session = self.engine.session

    def save_tweetp(self, tweetp):
        tweet = Tweet(
            fetch_timestamp=tweetp.fetch_timestamp,
            uid=tweetp.uid,
            mid=tweetp.mid,
            nickname=tweetp.nickname,
            isforward=tweetp.isforward,
            text=tweetp.text,
            timestamp=tweetp.timestamp,
            device=tweetp.device,
            location=tweetp.location,
            share=tweetp.share,
            comment=tweetp.comment,
            like=tweetp.comment,
        )
        if tweetp.isforward:
            tweet.forward_uid = tweetp.forward_tweet.uid
            tweet.forward_mid = tweetp.forward_tweet.mid
        self.session.add(tweet)
        self.session.commit()
