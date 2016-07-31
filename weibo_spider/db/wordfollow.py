#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Weibo."""
import logging

from sqlalchemy import Column, Integer, String, BIGINT
from sqlalchemy import UniqueConstraint
from sqlalchemy import desc
from sqlalchemy.orm import load_only


from .db_engine import Base
from .db_engine import DBEngine

from core import Singleton


class WordFollow(Base):
    """
    表示对一个搜索关键词的跟踪

    """
    __tablename__ = 'wordfollow'

    id = Column(Integer, primary_key=True)
    word = Column(String(50), unique=True)
    newest_timestamp = Column(BIGINT)
    custom_url = Column(String(100))
    region = Column(String(20)) # 地点
    w_type = Column(String(20)) # 微博类型：全部、精选、原创、关注人、认证用户、名人、媒体
    c_type = Column(String(20)) # 包含类型：全部、含图片、含视频、含音乐、含短链
    s_time = Column(String(20)) # 起始时间
    e_time = Column(String(20)) # 结束时间
    c_time = Column(String(20), default='0') # 当前抓取完成时间


class WordFollowTweet(Base):
    __tablename__ = 'wordfollowtweet'
    id = Column(Integer, primary_key=True)
    word_id = Column(Integer)
    mid = Column(String(12))

    __table_args__ = (UniqueConstraint('word_id', 'mid', name='wordfollow_tweet'),)


class WordFollowDAO(Singleton):

    def __init__(self):
        self.engine = DBEngine()
        self.session = self.engine.session

    def get_wordfollow(self, word):
        return self.session.query(WordFollow).filter(
            WordFollow.word == word).one_or_none()

    def get_or_create(self, word, custom_url, region=None, w_type=None,
            c_type=None, s_time=None, e_time=None):
        wordfollow = self.session.query(WordFollow).filter(
            WordFollow.word == word,
            WordFollow.custom_url == custom_url).one_or_none()
        if not wordfollow:
            wordfollow = self.session.query(WordFollow).filter(
                    WordFollow.word == word).one_or_none()
            if wordfollow:
                wordfollow.custom_url = custom_url
                wordfollow.region = region
                wordfollow.w_type = w_type
                wordfollow.c_type = c_type
                wordfollow.s_time = s_time
                wordfollow.e_time = e_time
                self.session.commit()
            else:
                wordfollow = WordFollow(
                        word=word,
                        newest_timestamp=0,
                        custom_url=custom_url,
                        region=region,
                        w_type=w_type,
                        c_type=c_type,
                        s_time=s_time,
                        e_time=e_time,
                )
                self.session.add(wordfollow)
                self.session.commit()
        return wordfollow

    def all_iter(self):
        for wordfollow in self.session.query(WordFollow):
            yield wordfollow

    def commit(self):
        self.session.commit()


class WordFollowTweetDAO(Singleton):

    def __init__(self):
        self.engine = DBEngine()
        self.session = self.engine.session
        self.logger = logging.getLogger('WordFollower')

    def add_wordfollow_mids(self, word, mids):
        word_id = self.session.query(WordFollow).filter(
            WordFollow.word == word).one_or_none()
        if not word_id:
            return
        word_id = word_id.id
        exists_mid_query = self.session.query(WordFollowTweet).filter(
            WordFollowTweet.mid.in_(mids)).options(load_only("mid"))
        exists_mids = [x.mid for x in exists_mid_query]
        mids = set(mids) - set(exists_mids)
        self.logger.debug('mids prepare to write to mysql: %s' % mids)
        data = []
        for mid in mids:
            data.append(dict(word_id=word_id, mid=mid))
        try:
            self.session.bulk_insert_mappings(WordFollowTweet, data)
            self.session.commit()
        except Exception as e:
            self.logger.error('bulk_insert_mappings error: %s' % e)
        return mids

    def get_word_latest_mids(self, word, num=50):
        word_id = self.session.query(WordFollow).filter(
            WordFollow.word == word).one_or_none()
        if not word_id:
            return []
        word_id = word_id.id
        mids = []
        mids_query = self.session.query(WordFollowTweet).filter(
            WordFollowTweet.word_id == word_id).order_by(desc(WordFollowTweet.id)).limit(num)
        for mid in mids_query:
            mids.append(mid.mid)
        return mids

    def commit(self):
        self.session.commit()
