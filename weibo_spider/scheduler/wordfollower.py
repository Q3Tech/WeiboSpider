#!/usr/bin/env python
# -*- coding: utf-8 -*-
import asyncio
import logging
import datetime
import json
import time
from asyncio import ensure_future

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
        self.newest_timestamp = self.wordfollow_dao.get_newest_timestamp(word=word)
        self.running = False
        self.fetch_interval = 30
        self.worker = None
        self.worker_response_future = None
        self.scheduler = scheduler

    async def start(self):
        if self.running:
            return
        self.running = True
        self.logger.debug('wordfollower {0}-{1} starting'.format(self.word, self.custom_url))
        self.worker = ensure_future(self.follow_worker())

    async def stop(self):
        if not self.running:
            return
        if self.worker:
            self.worker.cancel()
        self.running = False

    async def __update(self, custom_url=None, time_flag=None):
        result = None
        while result is None:
            payload = json.dumps({
                'type': 'update_word_follow',
                'keyword': self.word,
                'newest_ts': self.newest_timestamp,
                'custom_url': custom_url,
                'time_flag': time_flag,
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
        self.newest_timestamp = max(self.newest_timestamp, body['max_ts'])
        self.logger.info("Newest timestamp is {0}, aka {1}".format(
            self.newest_timestamp, datetime.datetime.fromtimestamp(self.newest_timestamp / 1000)))
        if not time_flag:
            self.wordfollow_dao.update_newest_timestamp(word=self.word, newest_timestamp=self.newest_timestamp)
        mids = self.wordfollowtweet_dao.add_wordfollow_mids(self.word, body['mids'])  # get diff mids
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
        word = self.word
        if self.custom_url and 'timescope' in self.custom_url:
            str_s_time = self.custom_url.split(':')[-2]
            str_e_time = self.custom_url.split(':')[-1]
            s_time = time.mktime(time.strptime(str_s_time, '%Y-%m-%d-%H'))
            e_time = time.mktime(time.strptime(str_e_time, '%Y-%m-%d-%H'))
            custom_flag = True
        else:
            custom_flag = False
        if custom_flag:
            c_time = s_time
            fetch_interval = 0
            while self.running:
                n_time = c_time + 3600 * fetch_interval
                n_time = min(n_time, e_time)
                str_c_time = time.strftime('%Y-%m-%d-%H', time.localtime(c_time))
                str_n_time = time.strftime('%Y-%m-%d-%H', time.localtime(n_time))
                custom_url = self.custom_url.split(':')
                custom_url[-1] = str_n_time
                custom_url[-2] = str_c_time
                custom_url = ':'.join(custom_url)
                self.logger.info('Try to update wordfollow {0}, custom_url: {1}.'.format(word, custom_url))
                num_new = await self.__update(custom_url, time_flag=True)
                self.logger.info('WordFollower {0}, custom_url: {1} got {2} new, and going to sleep {3} seconds.'.format(
                    word, custom_url, num_new, 10))
                if num_new < 200:
                    fetch_interval +=1
                elif num_new > 600:
                    fetch_interval -= 1
                fetch_interval = min(4, max(0, fetch_interval))
                c_time = n_time + 3600
                if c_time > e_time:
                    self.logger.info('Advanced search {0}-{1} has completed.'.format(self.word, self.custom_url))
                    self.running = False
                    break
                await asyncio.sleep(10)
        else:
            while self.running:
                self.logger.info('Try to update wordfollow {0}, custom_url: {1}.'.format(word, self.custom_url))
                num_new = await self.__update(self.custom_url, False)
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
