#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Weibo."""
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

    def get_or_create(self, word):
        wordfollow = self.session.query(WordFollow).filter(
            WordFollow.word == word).one_or_none()

        if not wordfollow:
            wordfollow = WordFollow(word=word, newest_timestamp=0)
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
        data = []
        for mid in mids:
            data.append(dict(word_id=word_id, mid=mid))
        self.session.bulk_insert_mappings(WordFollowTweet, data)

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
            print(mid.id)
            mids.append(mid.mid)
        return mids

    def commit(self):
        self.session.commit()
