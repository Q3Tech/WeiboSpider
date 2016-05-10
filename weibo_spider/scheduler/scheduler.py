#!/usr/bin/env python
# -*- coding: utf-8 -*-
import asyncio
import logging
import json
import consul.aio
import time
import random
from core.mq_connection import get_channel
from db import AccountDAO


class Scheduler(object):
    """
    爬虫调度器

    负责：
    - 爬虫上线账号分配
    - 爬虫处理Cookie
    """

    def __init__(self):
        self.logger = logging.getLogger('Scheduler')
        hdr = logging.StreamHandler()
        formatter = logging.Formatter('[%(asctime)s] %(name)s:%(levelname)s: %(message)s')
        hdr.setFormatter(formatter)
        self.logger.addHandler(hdr)
        self.logger.setLevel(logging.INFO)
        self.logger.info('Scheduler initializing.')
        self.workers = {}  # SpiderWorker
        self.accounts = {}   # 有效账户
        self.account_avail_set = set()
        self.account_dao = AccountDAO()

        loop = asyncio.get_event_loop()
        loop.run_until_complete(self.init())
        loop.run_forever()

    async def init(self):
        self.consul = consul.aio.Consul()
        self.channel = await get_channel()

        self.load_accounts()

        await self.channel.basic_consume(queue_name='worker_heartbeat', callback=self.handle_heartbeat, no_ack=True)
        await self.channel.basic_consume(queue_name='worker_report', callback=self.handle_report, no_ack=True)

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
        body = json.loads(body.decode('utf-8'))
        _type = body['type']
        if _type == 'loginfailed':
            self.logger.warn('Account {0} login failed.'.format(body['account']))
            self.accounts[body['account']]['is_login'] = False
            account = self.account_dao.get_or_create(email=body['account'])
            account.is_login = False
            self.account_dao.commit()

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
