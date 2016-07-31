#!/usr/bin/env python
# -*- coding: utf-8 -*-
import asyncio
import logging
import json
from asyncio import ensure_future
import time

from db.wordfollow import WordFollowDAO
from db.wordfollow import WordFollowTweetDAO


class WordFollower(object):
    """用于跟踪某一关键词的任务封装."""

    def __init__(self, word, scheduler, custom_url=None):
        self.logger = logging.getLogger('WordFollower')
        self.word = word
        self.custom_url = custom_url
        self.wordfollow_dao = WordFollowDAO()
        self.wordfollowtweet_dao = WordFollowTweetDAO()
        self.logger.debug('WordFollower creating...0')
        self.wordfollow = self.wordfollow_dao.get_or_create(word=word, custom_url=custom_url)
        self.logger.debug('WordFollower creating...0')
        self.running = False
        self.fetch_interval = 30
        self.worker = None
        self.worker_response_future = None
        self.scheduler = scheduler

    async def start(self):
        self.logger.debug('WordFolloer starting...')
        if self.running:
            self.logger.debug('WordFollower {0}-{1} has been running...'.format(self.word, self.custom_url))
            return
        self.running = True
        self.worker = ensure_future(self.follow_worker())

    async def stop(self):
        if not self.running:
            return
        if self.worker:
            self.worker.cancel()
        self.running = False
        self.logger.debug('WordFollower {0}-{1} is cancelled...'.format(self.word, self.custom_url))

    async def __update(self, custom_url=None, time_flag=None):
        result = None
        while result is None:
            payload = json.dumps({
                'type': 'update_word_follow',
                'keyword': self.word,
                'newest_ts': self.wordfollow.newest_timestamp,
                'custom_url': custom_url,
                'time_flag': time_flag,
            })
            self.logger.debug('%s : %s' % (self.word, payload))
            result = await self.scheduler.worker_rpc(
                payload=payload,
                properties={
                    'expiration': '300000',  # must be string for rabbitmq
                },
                timeout=5 * 60,
            )
            self.logger.info('%s : Got response.' % self.word)
            self.logger.info(result)
        body = json.loads(result['body'].decode('utf-8'))
        self.wordfollow.newest_timestamp = max(self.wordfollow.newest_timestamp, body['max_ts'])
        self.wordfollow_dao.commit()
        mids = self.wordfollowtweet_dao.add_wordfollow_mids(self.word, body['mids'])  # get diff mids
        self.wordfollowtweet_dao.commit()
        # 发布至 Exchange wordfollow_update, 动态展示
        await self.scheduler.channel.basic_publish(
            payload=json.dumps({
                'word': self.word,
                'mids': list(mids)
            }),
            exchange_name='wordfollow_update',
            routing_key='',
        )
        return body['num_new']

    async def follow_worker(self):
        self.logger.debug('I am in follow_worker')
        word = self.wordfollow.word
        custom_url = self.wordfollow.custom_url
        self.logger.debug('{0} {1}'.format(word, custom_url))
        self.logger.debug('s_time={0}; e_time={1}; c_time={2}.'.format(self.wordfollow.s_time, self.wordfollow.e_time, self.wordfollow.c_time))
        s_time = int(self.wordfollow.s_time) / 1000
        e_time = int(self.wordfollow.e_time) / 1000
        c_time = int(self.wordfollow.c_time) / 1000
        self.logger.debug('s_time={0}; e_time={1}; c_time={2}.'.format(self.wordfollow.s_time, self.wordfollow.e_time, self.wordfollow.c_time))
        self.logger.debug('follow_worker.{0} {1} {2} {3}'.format(word, custom_url, s_time, e_time))
        if s_time and e_time and c_time < e_time:
            if c_time <= s_time:
                c_time = s_time
            region = self.wordfollow.region
            w_type = self.wordfollow.w_type
            c_type = self.wordfollow.c_type
            fetch_interval = 0
            while self.running:
                n_time = c_time + 3600 * fetch_interval
                str_s_time = time.strftime('%Y-%m-%d-%H', time.localtime(c_time))
                str_n_time = time.strftime('%Y-%m-%d-%H', time.localtime(n_time))
                custom_url = region + w_type + c_type + '&timescope=custom:' + str_s_time + ':' + str_n_time
                self.logger.info('Try to update wordfollow {0}, custom_url: {1}.'.format(word, custom_url))
                num_new = await self.__update(custom_url, time_flag=True)
                self.logger.info('WordFollower {0} got {1} new, and going to sleep {2} seconds.'.format(
                    word, num_new, 10))
                if num_new < 200:
                    fetch_interval +=1
                if num_new > 600:
                    fetch_interval -= 1
                fetch_interval = min(4, max(0, fetch_interval))
                c_time = n_time + 3600
                self.wordfollow.c_time = str(int(c_time * 1000))
                self.wordfollow_dao.commit()
                if c_time > e_time:
                    break
                await asyncio.sleep(10)
        else:
            while self.running:
                self.logger.info('Try to update wordfollow {0}, custom_url: {1}.'.format(word, custom_url))
                num_new = await self.__update(custom_url, time_flag=False)
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
