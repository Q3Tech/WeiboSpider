#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
import json
import asyncio

import tornado
import tornado.web
from tornado.platform.asyncio import AsyncIOMainLoop

import settings
from core.mq_connection import get_channel
from .api_bridge import WordFollowerHandler
from .weibo import WordUpdateHandler
from .weibo import WordFollowUpdateHandler

__frontend_path = os.path.join(settings.BASE_DIR, 'frontend')
__static_path = os.path.join(__frontend_path, 'bin', 'static')


class MainHandler(tornado.web.RequestHandler):
    def get(self):
        self.write("Hello, world")


def get_app():
    application = tornado.web.Application([
        (r"/()", tornado.web.StaticFileHandler, {
            "path": __frontend_path,
            "default_filename": "index.html"
        }),
        (r"/static/(.*)", tornado.web.StaticFileHandler, {"path": __static_path}),
        (r"/api/wordfollow/", WordFollowerHandler),
        (r"/api/wordupdate/", WordUpdateHandler),
        (r"/ws/wordfollow_update/", WordFollowUpdateHandler),


    ])
    return application


async def init():
    async def handle_update(channel, body, envelope, properties):
        body = json.loads(body.decode('utf-8'))
        print(body)
        await channel.basic_client_ack(delivery_tag=envelope.delivery_tag)
        await asyncio.sleep(1)
        WordFollowUpdateHandler.update(word=body['word'], mids=body['mids'])

    channel = await get_channel()
    queue_name = (await channel.queue_declare('', exclusive=True))['queue']
    await channel.queue_bind(queue_name=queue_name, exchange_name='wordfollow_update', routing_key='')
    await channel.basic_consume(queue_name=queue_name, callback=handle_update)


def start_server():
    AsyncIOMainLoop().install()
    app = get_app()
    app.listen(settings.WEB_PORT)
    loop = asyncio.get_event_loop()
    loop.run_until_complete(init())
    loop.run_forever()
