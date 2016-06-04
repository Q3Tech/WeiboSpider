#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Weibo."""
from sqlalchemy import Column, Integer, String, Boolean, TEXT, BIGINT
from sqlalchemy import desc

from .db_engine import Base
from .db_engine import DBEngine

from core import Singleton


class Tweet(Base):
    """
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
    uid = Column(BIGINT, index=True)
    mid = Column(String(12), unique=True)
    nickname = Column(String(61))
    isforward = Column(Boolean)
    text = Column(TEXT)
    timestamp = Column(BIGINT)
    device = Column(String(50))
    location = Column(String(100))
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
        if not tweetp.uid:
            return None
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
            like=tweetp.like,
        )
        if tweetp.isforward:
            tweet.forward_uid = tweetp.forward_tweet.uid
            tweet.forward_mid = tweetp.forward_tweet.mid
        self.session.add(tweet)
        self.session.commit()
        return tweet

    def update_or_create_tweetp(self, tweetp):
        created = False
        if not tweetp.uid:
            return created, None
        tweet = self.session.query(Tweet).filter(
            Tweet.mid == tweetp.mid).one_or_none()
        if tweet:
            tweet.fetch_timestamp = tweetp.fetch_timestamp
            tweet.share = tweetp.share
            tweet.comment = tweetp.comment
            tweet.like = tweetp.like
            self.session.commit()
        else:
            tweet = self.save_tweetp(tweetp)
            created = True

        return created, tweet

    def get_many_tweet(self, mids):
        tweets = self.session.query(Tweet).filter(Tweet.mid.in_(mids)).order_by(desc(Tweet.timestamp))
        return tweets

    @classmethod
    def get_tweetp_from_tweet(cls, tweet):
        from spider import TweetP
        tweetp = TweetP()
        tweetp.update(
            fetch_timestamp=tweet.fetch_timestamp,
            uid=tweet.uid,
            mid=tweet.mid,
            nickname=tweet.nickname,
            isforward=tweet.isforward,
            text=tweet.text,
            timestamp=tweet.timestamp,
            device=tweet.device,
            location=tweet.location,
            share=tweet.share,
            comment=tweet.comment,
            like=tweet.like,
        )
        return tweetp

    def get_tweetp_from_mids(self, mids):
        tweets = self.session.query(Tweet).filter(Tweet.mid.in_(mids)).order_by(desc(Tweet.timestamp))
        forward_mids = []
        for tweet in tweets:
            if tweet.forward_mid:
                forward_mids.append(tweet.forward_mid)
        forward_tweets = {tweet.mid: tweet for tweet in self.session.query(Tweet).filter(Tweet.mid.in_(forward_mids))}
        forward_tweetps = {mid: self.get_tweetp_from_tweet(tweet) for mid, tweet in forward_tweets.items()}
        tweetps = []
        for tweet in tweets:
            tweetp = self.get_tweetp_from_tweet(tweet)
            if tweet.forward_mid:
                tweetp.update(forward_tweet=forward_tweetps.get(tweet.forward_mid, None))
            tweetps.append(tweetp)
        return tweetps
