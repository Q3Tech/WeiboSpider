#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging
import asyncio
import time
import consul.aio
import uuid
import json
from core.mq_connection import get_channel
from db import Account
from .spider import Spider
from .spider import LoginFailedException


class SpiderWorker(object):

    def __init__(self):
        # logger
        self.logger = logging.getLogger('SpiderWorker')
        hdr = logging.StreamHandler()
        formatter = logging.Formatter('[%(asctime)s] %(name)s:%(levelname)s: %(message)s')
        hdr.setFormatter(formatter)
        self.logger.addHandler(hdr)
        self.logger.setLevel(logging.INFO)

        self.logger.info('SpiderWorker initializing.')
        self.id = str(uuid.uuid4())
        self.logger.info('Worker id: {0}'.format(self.id))
        self.account = None
        loop = asyncio.get_event_loop()
        loop.run_until_complete(self.init())
        loop.run_forever()

    async def init(self):
        self.consul = consul.aio.Consul()
        self.channel = await get_channel()

        # Register
        await self.channel.queue_declare(queue_name='worker_heartbeat', durable=False)
        await self.channel.queue_bind(
            queue_name='worker_heartbeat', exchange_name='amq.direct', routing_key='worker_heartbeat')

        # worker_report
        await self.channel.queue_declare(queue_name='worker_report', durable=False)
        await self.channel.queue_bind(
            queue_name='worker_report', exchange_name='amq.direct', routing_key='worker_report')

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
