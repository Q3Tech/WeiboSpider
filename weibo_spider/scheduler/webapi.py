#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Scheduler的WebAPI."""

import json
import tornado.web
from tornado.platform.asyncio import AsyncIOMainLoop
import settings

scheduler = None


class MainHandler(tornado.web.RequestHandler):
    def get(self):
        self.write("WeiboSpider Scheduler!")


class WordFollowHandler(tornado.web.RequestHandler):
    async def get(self):
        result = []
        for word, follower in scheduler.word_follower.items():
            result.append({
                'word': word,
                'running': follower.running,
                'newest_timestamp': follower.wordfollow.newest_timestamp,
                'interval': follower.fetch_interval,
            })
        self.set_header('Content-Type', 'application/javascript')
        self.write(json.dumps(result))

    async def post(self):
        action = self.get_argument('action')
        if action == 'active':
            word = self.get_argument('word')
            await scheduler.active_word_follow(word)
        elif action == 'deactive':
            word = self.get_argument('word')
            await scheduler.deactive_word_follow(word)


def install_web_api(_scheduler):
    """make_app."""
    global scheduler
    scheduler = _scheduler
    AsyncIOMainLoop().install()
    app = tornado.web.Application([
        ("/", MainHandler),
        ("/api/wordfollow/", WordFollowHandler)
    ])
    app.listen(settings.SCHEDULER_API_PORT)
