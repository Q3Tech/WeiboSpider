#!/usr/bin/env python
# -*- coding: utf-8 -*-
import tornado
import tornado.web
import os

import settings

from .api_bridge import WordFollowerHandler

__static_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static')
__template_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'template')


class MainHandler(tornado.web.RequestHandler):
    def get(self):
        self.write("Hello, world")


def get_app():
    application = tornado.web.Application([
        (r"/()", tornado.web.StaticFileHandler, {
            "path": __template_path,
            "default_filename": "index.html"
        }),
        (r"/static/(.*)", tornado.web.StaticFileHandler, {"path": __static_path}),
        (r"/api/wordfollow/", WordFollowerHandler),


    ])
    return application


def start_server():
    app = get_app()
    app.listen(settings.WEB_PORT)
    tornado.ioloop.IOLoop.current().start()
