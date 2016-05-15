#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Use to re-proxy for other API."""

import tornado.web
from tornado.httpclient import HTTPRequest
from tornado.httpclient import AsyncHTTPClient
from settings import SCHEDULER_API_URL


class WordFollowerHandler(tornado.web.RequestHandler):
    """re-proxy for scheduler /api/wordfollow/ ."""

    async def get(self):
        http_client = AsyncHTTPClient()
        response = await http_client.fetch(SCHEDULER_API_URL + "wordfollow/")
        self.set_header('Content-Type', 'application/javascript')
        self.write(response.body)

    async def post(self):
        http_client = AsyncHTTPClient()
        request = HTTPRequest(
            url=SCHEDULER_API_URL + "wordfollow/",
            method='POST',
            body=self.request.body,
            headers=self.request.headers,
        )
        response = await http_client.fetch(request)
        self.set_header('Content-Type', 'application/javascript')
        self.write(response.body)
