#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Scheduler的WebAPI."""

import json
import time
import tornado.web
from tornado.platform.asyncio import AsyncIOMainLoop
import settings

scheduler = None
location_data = json.loads(open('location.json').read())

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
            region = self.get_argument('region', default='')
            s_time = self.get_argument('s_time', default='0')
            e_time = self.get_argument('e_time', default='0')
            w_type = self.get_argument('w_type', default='&typeall=1')
            c_type = self.get_argument('c_type', default='&suball=1')
            custom_url = w_type + c_type
            if region:
                region = region.split(';')
                num0 = location_data[region[0]]
                num1 = location_data[''.join(region)]
                region = '&region=custom:' + num0 + ':' + num1
                custom_url = region + custom_url
            if s_time and e_time:
                str_s_time = time.strftime('%Y-%m-%d-%H', time.localtime(int(s_time) / 1000))
                str_e_time = time.strftime('%Y-%m-%d-%H', time.localtime(int(e_time) / 1000))
                str_time = '&timescope=custom:' + str_s_time + ':' + str_e_time
                custom_url += str_time
            await scheduler.active_word_follow(word, custom_url, region, w_type, c_type, s_time, e_time)
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
