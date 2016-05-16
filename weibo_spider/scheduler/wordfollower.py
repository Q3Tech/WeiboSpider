#!/usr/bin/env python
# -*- coding: utf-8 -*-
import asyncio
import logging
import json
from asyncio import ensure_future

from db.wordfollow import WordFollowDAO
from db.wordfollow import WordFollowTweetDAO


class WordFollower(object):
    """用于跟踪某一关键词的任务封装."""

    def __init__(self, word, scheduler):
        self.logger = logging.getLogger('WordFollower')
        self.word = word
        self.wordfollow_dao = WordFollowDAO()
        self.wordfollowtweet_dao = WordFollowTweetDAO()
        self.wordfollow = self.wordfollow_dao.get_or_create(word=word)
        self.running = False
        self.fetch_interval = 30
        self.worker = None
        self.worker_response_future = None
        self.scheduler = scheduler

    async def start(self):
        if self.running:
            return
        self.running = True
        self.worker = ensure_future(self.follow_worker())

    async def stop(self):
        if not self.running:
            return
        if self.worker:
            self.worker.cancel()
        self.running = False

    async def __update(self):
        result = None
        while result is None:
            payload = json.dumps({
                'type': 'update_word_follow',
                'keyword': self.word,
                'newest_ts': self.wordfollow.newest_timestamp,
            })
            result = await self.scheduler.worker_rpc(
                payload=payload,
                properties={
                    'expiration': '300000',  # must be string for rabbitmq
                },
                timeout=5 * 60,
            )
            self.logger.info('Got response.')
            self.logger.info(result)
        body = json.loads(result['body'].decode('utf-8'))
        self.wordfollow.newest_timestamp = max(self.wordfollow.newest_timestamp, body['max_ts'])
        self.wordfollow_dao.commit()
        self.wordfollowtweet_dao.add_wordfollow_mids(self.word, body['mids'])
        self.wordfollowtweet_dao.commit()
        return body['num_new']

    async def follow_worker(self):
        word = self.wordfollow.word
        while self.running:
            self.logger.info('Try to update wordfollow {0}.'.format(word))
            num_new = await self.__update()
            self.logger.info('{0} Update complete.'.format(word))
            fetch_interval = self.fetch_interval
            if num_new >= 19:
                fetch_interval *= 0.618
            elif num_new < 10:
                fetch_interval *= 1.618
            fetch_interval = min(300, max(20, fetch_interval))
            self.fetch_interval = int(fetch_interval)
            self.logger.info('WordFollower {0} got {1} new, and going to sleep {2} seconds.'.format(
                word, num_new, self.fetch_interval))
            await asyncio.sleep(self.fetch_interval)
