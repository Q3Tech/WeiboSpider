#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Weibo."""
from sqlalchemy import Column, Integer, String, BIGINT
from sqlalchemy import UniqueConstraint
from sqlalchemy import desc
from sqlalchemy.orm import load_only

from .db_engine import Base
from .db_engine import DBEngine
from .db_engine import ensure_session

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

    @ensure_session
    def get_wordfollow(self, word, session=None):
        return session.query(WordFollow).filter(
            WordFollow.word == word).one_or_none()

    @ensure_session
    def get_or_create(self, word, session=None):
        wordfollow = session.query(WordFollow).filter(
            WordFollow.word == word).one_or_none()
        print("This:", wordfollow)
        if not wordfollow:
            print("word {0} not found, create new.".format(word.encode('utf-8')))
            wordfollow = WordFollow(word=word, newest_timestamp=0)
            session.add(wordfollow)
        return wordfollow

    def all_iter(self):
        with self.engine.Session() as session:
            for wordfollow in session.query(WordFollow):
                yield wordfollow

    @ensure_session
    def get_newest_timestamp(self, word, session=None):
        wordfollow = self.get_or_create(word=word, session=session)
        newest_timestamp = wordfollow.newest_timestamp
        return newest_timestamp

    @ensure_session
    def update_newest_timestamp(self, word, newest_timestamp, session=None):
        wordfollow = self.get_or_create(word=word, session=session)
        # print(word, newest_timestamp, wordfollow.id)
        wordfollow.newest_timestamp = newest_timestamp
        session.commit()


class WordFollowTweetDAO(Singleton):

    @ensure_session
    def add_wordfollow_mids(self, word, mids, session=None):
        word_id = session.query(WordFollow).filter(
            WordFollow.word == word).one_or_none()
        if not word_id:
            return
        word_id = word_id.id
        exists_mid_query = session.query(WordFollowTweet).filter(
            WordFollowTweet.mid.in_(mids)).options(load_only("mid"))
        exists_mids = [x.mid for x in exists_mid_query]
        mids = set(mids) - set(exists_mids)
        data = []
        for mid in mids:
            data.append(dict(word_id=word_id, mid=mid))
        session.bulk_insert_mappings(WordFollowTweet, data)
        return mids

    @ensure_session
    def get_word_latest_mids(self, word, num=50, session=None):
        word_id = session.query(WordFollow).filter(
            WordFollow.word == word).one_or_none()
        if not word_id:
            return []
        word_id = word_id.id
        mids = []
        mids_query = session.query(WordFollowTweet).filter(
            WordFollowTweet.word_id == word_id).order_by(desc(WordFollowTweet.id)).limit(num)
        for mid in mids_query:
            mids.append(mid.mid)
        return mids
