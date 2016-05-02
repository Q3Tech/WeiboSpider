#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json
import datetime

from celery import Celery
from celery import bootsteps
from kombu import Consumer, Exchange, Queue

from .manul_login_app import LoginExecuter
from db.db_engine import AccountDAO

my_queue = Queue('weibo_login', Exchange('weibo_login'), 'weibo_login')

# app = Celery(broker='amqp://guest:guest@localhost:5672/')

app = Celery(broker='amqp://192.168.50.4/')


class LoginTaskHandler(bootsteps.ConsumerStep):
    """amqp Consumer for login task"""

    def __init__(self):
        self.login_executer = LoginExecuter()

    def get_consumers(self, channel):
        return [Consumer(channel,
                         queues=[my_queue],
                         callbacks=[self.handle_message],
                         accept=['json'])]

    def handle_message(self, body, message):
        body = json.loads(body)
        assert 'username' in body
        assert 'password' in body
        print(body)
        resp = self.login_executer.login(body['username'], body['password'])
        if not resp:
            return
        with open('cookies.json', 'w') as cookies_file:
            cookies_file.write(json.dumps(resp))
        AccountDAO.update_or_create(email=body['username'],
                                    password=body['password'],
                                    is_login=True,
                                    login_time=datetime.datetime.now(),
                                    cookies=json.dumps(resp))
        print ("Database Updated")
        message.ack()

app.steps['consumer'].add(LoginTaskHandler)
