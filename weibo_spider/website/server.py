#!/usr/bin/env python
# -*- coding: utf-8 -*-
import tornado
import tornado.web
import os

import settings

from .api_bridge import WordFollowerHandler
from .weibo import WordUpdateHandler

__frontend_path = os.path.join(settings.BASE_DIR, 'frontend')
__static_path = os.path.join(__frontend_path, 'static')
__template_path = os.path.join(__frontend_path, 'template')


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


    ])
    return application


def start_server():
    app = get_app()
    app.listen(settings.WEB_PORT)
    tornado.ioloop.IOLoop.current().start()
