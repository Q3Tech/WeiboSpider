#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging
import asyncio
import time
import consul.aio
import uuid
from core.mq_connection import get_channel


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
        loop = asyncio.get_event_loop()
        loop.run_until_complete(self.init())

    async def init(self):
        self.consul = consul.aio.Consul()
        self.channel = await get_channel()

        # Register
        await self.channel.queue_declare(queue_name='spiderworker_register', durable=False)
        await self.channel.queue_bind(
            queue_name='spiderworker_register', exchange_name='amq.direct', routing_key='spiderworker_register')

        # exclusive
        self.exclusive = (await self.channel.queue_declare('', exclusive=True))['queue']
        self.logger.info('Exclusive queue: {0}'.format(self.exclusive))
        await self.channel.basic_consume(queue_name=self.exclusive, callback=self.handle_exclusive)
        
        tasks = [
            self.update_alive(),
        ]
        await asyncio.wait(tasks)

    async def update_alive(self):
        while True:
            await self.consul.kv.put(
                'WeiboSpider/SpiderWorker/{uuid}/last_alive'.format(uuid=self.id), str(time.time()))
            await self.channel.basic_publish(
                payload='register: {0}.'.format(self.id),
                exchange_name='amq.direct',
                routing_key='spiderworker_register',
                properties={'expiration': '5000'},  # must be string for rabbitmq
            )
            await asyncio.sleep(5)

    async def handle_exclusive(self, channel, body, envelope, properties):
        print(body)

    async def get_account(self):
        result = await self.channel.queue_declare(exclusive=True)
