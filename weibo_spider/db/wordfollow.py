#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Weibo."""
from sqlalchemy import Column, Integer, String, BIGINT

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

    def commit(self):
        self.session.commit()
