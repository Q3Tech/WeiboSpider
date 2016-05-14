#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging
import asyncio
import time
import consul.aio
import uuid
import json
from core.mq_connection import get_channel
from core import JsonSerializableEncoder
from db import Account
from .spider import Spider
from .spider import LoginFailedException


class SpiderWorker(object):

    def __init__(self):
        # logger
        self.logger = logging.getLogger('SpiderWorker')

        self.logger.info('SpiderWorker initializing.')
        self.id = str(uuid.uuid4())
        self.logger.info('Worker id: {0}'.format(self.id))
        self.account = None
        self.spider = None
        self.task_consume_tag = None
        loop = asyncio.get_event_loop()
        loop.run_until_complete(self.init())
        loop.run_forever()

    async def init(self):
        self.consul = consul.aio.Consul()
        self.channel = await get_channel()

        # exclusive
        self.exclusive = (await self.channel.queue_declare('', exclusive=True))['queue']
        self.logger.info('Exclusive queue: {0}'.format(self.exclusive))
        await self.channel.basic_consume(queue_name=self.exclusive, callback=self.handle_exclusive)

        # tasks
        tasks = [
            self.update_alive(),
        ]
        await asyncio.wait(tasks)

    async def update_alive(self):
        while True:
            await self.consul.kv.put(
                'WeiboSpider/SpiderWorker/{uuid}/last_alive'.format(uuid=self.id), str(time.time()))
            await self.consul.kv.put(
                'WeiboSpider/SpiderWorker/{uuid}/reply_to'.format(uuid=self.id), self.exclusive)
            playload = json.dumps({
                'type': 'heartbeat',
                'id': self.id,
                'account': self.account,
                'cookies': self.spider.get_cookies_json() if self.spider else None,
            })
            await self.channel.basic_publish(
                payload=playload,
                exchange_name='amq.direct',
                routing_key='worker_heartbeat',
                properties={
                    'expiration': '5000',  # must be string for rabbitmq
                    'reply_to': self.exclusive,
                },
            )
            await asyncio.sleep(5)

    async def handle_exclusive(self, channel, body, envelope, properties):
        body = json.loads(body.decode('utf-8'))
        if body['type'] == 'bind_account':
            await self.bind_account(account=body['account'], cookies=body['cookies'])
            await channel.basic_client_ack(delivery_tag=envelope.delivery_tag)

    async def handle_task(self, channel, body, envelope, properties):
        self.logger.info(body)
        body = json.loads(body.decode('utf-8'))
        self.logger.info('Got a task of type {0}'.format(body['type']))
        if body['type'] == 'update_word_follow':
            self.logger.info('Got a update_word_follow task!')
            result = await self.update_word_follow(body['keyword'], body['newest_ts'])
            await self.channel.basic_publish(
                payload=json.dumps(result),
                exchange_name='amq.direct',
                routing_key='worker_report',
                properties={
                    'correlation_id': properties.correlation_id
                },
            )
            await channel.basic_client_ack(delivery_tag=envelope.delivery_tag)

    async def update_word_follow(self, keyword, newest_ts):
        """更新至指定时间, 返回新微博数量和他们的mid."""
        it = self.spider.fetch_search_iter(keyword=keyword)
        min_ts = int((time.time() + 3600) * 1000)
        max_ts = 0
        num_new = 0
        mids = []
        self.logger.info('start __update loop.')
        for weibos, page, _ in it:
            self.logger.info('__update page {0}.'.format(page))
            for weibo in weibos:
                if weibo.timestamp >= newest_ts:  # New
                    print(weibo.pretty())
                    num_new += 1
                    mids.append(weibo.mid)
                max_ts = max(max_ts, weibo.timestamp)
                min_ts = min(min_ts, weibo.timestamp)
            self.logger.info("min_ts={min_ts}, max_ts={max_ts}, newest_ts={newest_ts}.".format(
                min_ts=min_ts, max_ts=max_ts, newest_ts=newest_ts))
            await self.save_weibo_data(weibos)
            if min_ts < newest_ts:
                self.logger.info('break __update.')
                break
            # if page % 10 == 0:
            #     time.sleep(10)
        self.logger.info('{0} got {1} new.'.format(keyword, num_new))
        return {
            'num_new': num_new,
            'mids': mids,
            'max_ts': max_ts,
        }

    async def save_weibo_data(self, weibos):
        playload = json.dumps(weibos, cls=JsonSerializableEncoder)
        self.logger.debug('sending weibo to queue weibo_data')
        await self.channel.basic_publish(
            payload=playload,
            exchange_name='amq.direct',
            routing_key='weibo_data',
            properties={
                'delivery_mode': 2,
            },
        )

    async def bind_account(self, account, cookies):
        _account = Account()
        _account.email = account
        _account.cookies = cookies
        try:
            self.spider = Spider(account=_account)
        except LoginFailedException:
            self.spider = None
            await self.report_login_failed(account)
            self.logger.error('Login Failed')
        else:
            self.account = account
            self.task_consume_tag = await self.channel.basic_consume(
                queue_name='worker_task', callback=self.handle_task, no_wait=True)
            self.logger.info('Bind account successful. {}'.format(account))

    async def report_login_failed(self, account):
        playload = json.dumps({
            'type': 'loginfailed',
            'account': account,
        })
        await self.channel.basic_publish(
            payload=playload,
            exchange_name='amq.direct',
            routing_key='worker_report',
            properties={
                'expiration': '60000',  # must be string for rabbitmq
            },
        )
