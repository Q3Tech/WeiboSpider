#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""收集由RabbitMQ回传的微博数据."""
import logging
import asyncio
import json

from core.mq_connection import get_channel
from spider import TweetP
from db import RawDataDAO
from db import TweetDAO


class DataCollecter(object):
    """收集由RabbitMQ回传的微博数据."""
    def __init__(self):
        self.logger = logging.getLogger('DataCollecter')
        hdr = logging.StreamHandler()
        formatter = logging.Formatter('[%(asctime)s] %(name)s:%(levelname)s: %(message)s')
        hdr.setFormatter(formatter)
        self.logger.addHandler(hdr)
        self.logger.setLevel(logging.INFO)

        self.rawdata_dao = RawDataDAO()
        self.tweet_dao = TweetDAO()

        def start_loop():
            loop = asyncio.get_event_loop()
            loop.run_until_complete(self.init())
            loop.run_forever()
        start_loop()

    async def init(self):
        self.channel = await get_channel()
        await self.channel.basic_consume(queue_name='weibo_data', callback=self.handle_weibo_data)

    async def handle_weibo_data(self, channel, body, envelope, properties):
        weibos = json.loads(body.decode('utf-8'))

        def convert_generator():
            for weibo_dict in weibos:
                weibo = TweetP.from_json_dict(weibo_dict)
                # print(weibo.pretty())
                yield weibo
        self.logger.info("Got {0} weibo.".format(len(weibos)))
        self.save_weibo(convert_generator())
        await self.channel.basic_client_ack(delivery_tag=envelope.delivery_tag)
        self.logger.debug('Save {0} weibo successful.'.format(len(weibos)))

    def save_weibo(self, weibos):
        if isinstance(weibos, TweetP):
            weibos = [weibos]
        for weibo in weibos:
            if self.rawdata_dao:
                self.rawdata_dao.set_raw_data(weibo.mid, weibo.raw_html)
                if weibo.forward_tweet:
                    self.rawdata_dao.set_raw_data(weibo.forward_tweet.mid, weibo.forward_tweet.raw_html)
            if self.tweet_dao:
                self.tweet_dao.update_or_create_tweetp(weibo)
                if weibo.forward_tweet:
                    self.tweet_dao.update_or_create_tweetp(weibo.forward_tweet)
