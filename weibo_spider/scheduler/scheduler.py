#!/usr/bin/env python
# -*- coding: utf-8 -*-
import asyncio
import logging
import json
import consul.aio
import time
import random
import uuid

from core.mq_connection import get_channel
from db import AccountDAO
from db import WordFollowDAO
from .wordfollower import WordFollower


from .webapi import install_web_api


class Scheduler(object):
    """
    爬虫调度器

    负责：
    - 爬虫上线账号分配
    - 爬虫处理Cookie
    """

    def __init__(self):
        self.logger = logging.getLogger('Scheduler')
        
        self.logger.info('Scheduler initializing.')
        self.workers = {}  # SpiderWorker
        self.accounts = {}   # 有效账户
        self.account_avail_set = set()
        self.account_dao = AccountDAO()
        self.wordfollow_dao = WordFollowDAO()
        self.worker_rpc_futures = {}
        self.word_follower = {}

        # WebApi
        self.web_api = install_web_api(self)

        loop = asyncio.get_event_loop()
        loop.run_until_complete(self.init())
        loop.run_forever()

    async def init(self):
        self.consul = consul.aio.Consul()
        self.channel = await get_channel()

        self.load_accounts()
        self.load_word_follow()

        await self.channel.basic_consume(queue_name='worker_heartbeat', callback=self.handle_heartbeat, no_ack=True)
        await self.channel.basic_consume(queue_name='worker_report', callback=self.handle_report)

        tasks = [
            self.recycle(),
        ]
        await asyncio.wait(tasks)

    def load_accounts(self):
        for account in self.account_dao.account_iter():
            self.accounts[account.email] = {
                'cookies': account.cookies,
                'is_login': account.is_login,
                'bind': None,
            }
            if account.is_login:
                self.account_avail_set.add(account.email)
        # await self.consul.kv.put('')

    def load_word_follow(self):
        wordfollow_dao = WordFollowDAO()
        for wordfollow in wordfollow_dao.all_iter():
            word = wordfollow.word
            self.logger.debug('initializing wordfollower {0}'.format(word))
            if word not in self.word_follower:
                self.word_follower[word] = WordFollower(word=word, scheduler=self)

    async def active_word_follow(self, word):
        if word not in self.word_follower:
            self.create_word_follow(word)
        await self.word_follower[word].start()

    async def deactive_word_follow(self, word):
        if word in self.word_follower:
            self.word_follower[word].stop()

    def create_word_follow(self, word):
        self.wordfollow_dao.get_or_create(word=word)
        self.word_follower[word] = WordFollower(word=word, scheduler=self)

    async def handle_heartbeat(self, channel, body, envelope, properties):
        body = json.loads(body.decode('utf-8'))
        worker_id = body['id']
        self.logger.info('Got heart beat from {0}.'.format(worker_id))
        if worker_id not in self.workers:
            self.logger.info('New worker online! {0}'.format(worker_id))
            self.workers[worker_id] = {
                'exclusive': properties.reply_to,
                'last_alive': time.time(),
                'account': body['account']
            }
        else:
            self.workers[worker_id]['last_alive'] = time.time()
        if body['account'] is None:
            self.logger.info('binding account.')
            await self.bind_account(worker_id=worker_id)

    async def handle_report(self, channel, body, envelope, properties):
        if properties.correlation_id:
            correlation_id = properties.correlation_id
            if correlation_id in self.worker_rpc_futures:
                self.worker_rpc_futures[correlation_id].set_result({
                    'channel': channel,
                    'body': body,
                    'envelope': envelope,
                    'properties': properties,
                })
            await channel.basic_client_ack(delivery_tag=envelope.delivery_tag)
            return
        print(body)
        body = json.loads(body.decode('utf-8'))
        _type = body['type']
        if _type == 'loginfailed':
            self.logger.warn('Account {0} login failed.'.format(body['account']))
            self.accounts[body['account']]['is_login'] = False
            account = self.account_dao.get_or_create(email=body['account'])
            account.is_login = False
            self.account_dao.commit()
        await channel.basic_client_ack(delivery_tag=envelope.delivery_tag)

    async def bind_account(self, worker_id):
        if len(self.account_avail_set) == 0:
            self.logger.warn('No account available to bind for {0}'.format(worker_id))
            return
        account,  = random.sample(self.account_avail_set, 1)
        self.account_avail_set.remove(account)
        self.accounts[account]['bind'] = worker_id
        self.workers[worker_id]['account'] = account
        payload = json.dumps({
            'type': 'bind_account',
            'account': account,
            'cookies': self.accounts[account]['cookies'],
        })
        await self.channel.basic_publish(
            payload=payload, exchange_name='', routing_key=self.workers[worker_id]['exclusive'])
        self.logger.info('Account bind sent. {0} {1}'.format(worker_id, account))

    async def recycle(self):
        while True:
            self.logger.info('Recycle')
            now = time.time()
            recycle_workers = [id for id in self.workers if now - self.workers[id]['last_alive'] > 60]
            for worker_id in recycle_workers:
                account = self.workers[worker_id]['account']
                self.logger.warn('recollect {0} {1}'.format(worker_id, account))
                if account:
                    self.accounts[account]['bind'] = None
                    if self.accounts[account]['is_login']:
                        self.account_avail_set.add(account)
                    self.logger.info('{0} recycled'.format(account))
                self.workers.pop(worker_id)
            await asyncio.sleep(5)

    async def worker_rpc(self, payload, properties=None, timeout=60):
        """
        向不特定Worker发布任务的RPC函数.

        kwargs 为basic_publish 的参数, correlation_id 务必保证正确
        如果在worker_report 中受到带有 correlation_id 的消息，则认为RPC调用成功
        本函数将创建一个feature, 并等待，如果成功则返回channel, body, envelope, properties 的字典，
        失败/超时则返回 None
        """
        if properties is None:
            properties = {}
        assert(isinstance(properties, dict) and 'correlation_id' not in properties)
        correlation_id = str(uuid.uuid4())
        properties['correlation_id'] = correlation_id
        self.logger.debug('Sending RPC.')
        await self.channel.basic_publish(
            payload=payload,
            exchange_name='amq.direct',
            routing_key='worker_task',
            properties=properties
        )
        self.worker_rpc_futures[correlation_id] = asyncio.Future()
        try:
            with asyncio.timeout(timeout):
                result = await self.worker_rpc_futures[correlation_id]
        except asyncio.TimeoutError:
            result = None
            self.worker_rpc_futures[correlation_id].cancel()
        finally:
            self.worker_rpc_futures.pop(correlation_id)

        return result
