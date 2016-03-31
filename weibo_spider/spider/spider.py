#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json
import re
import requests
from db.db_engine import Account
from db.db_engine import AccountDAO


class Spider(object):

    def __init__(self, account):
        assert isinstance(account, Account)
        self.account = account
        self.s = requests.session()
        self.session_set_cookie(session=self.s,
                                cookies=account.cookies)

    def __repr__(self):
        return "<Spider: %s>" % self.account.email

    @classmethod
    def session_set_cookie(cls, session, cookies):
        cookies = json.loads(cookies)
        for cookie in cookies:
            # domain expiry httpOnly name path secure
            session.cookies.set(
                name=cookie['name'],
                value=cookie['value'],
                path=cookie['path'],
                domain=cookie['domain'])

    @classmethod
    def embed_html_iter(cls, resp):
        html_in_js_pattern = re.compile(r'\"html\":\"((?:[^"\\]|\\.)*)\"')
        for g in html_in_js_pattern.finditer(resp.text):
            yield json.loads('"' + g.group(1) + '"')

    @classmethod
    def check_avail(cls, resp):
        return True

    def fetch(self, url, referer=None):
        resp = self.s.get(url=url)
        return resp

    def fetch_weibo(self, user_id, weibo_id):
        pass

    def fetch_serach(self, keyword):
        pass

    @classmethod
    def save_to_file(cls, resp, filename):
        with open(filename, 'w') as file:
            file.write(resp.content)


def get_random_spider():
    account = AccountDAO.get_random_account()
    spider = Spider(account=account)
    return spider
