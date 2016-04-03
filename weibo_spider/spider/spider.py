#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json
import re
import requests
import logging
import random
import urllib
from db.db_engine import Account
from db.db_engine import AccountDAO


class Spider(object):

    def __init__(self, account):
        assert isinstance(account, Account)
        self.account = account
        self.s = requests.session()
        self.set_session_cookie(session=self.s,
                                cookies=account.cookies)
        self.s.headers['User-Agent'] = 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/49.0.2623.110 Safari/537.36'
        self.referer = ''

     def __del__(self):
        slef.save_cookies()

    def __repr__(self):
        return "<Spider: %s>" % self.account.email

    @classmethod
    def set_session_cookie(cls, session, cookies):
        cookies = json.loads(cookies)
        for cookie in cookies:
            # domain expiry httpOnly name path secure
            session.cookies.set(
                name=cookie['name'],
                value=cookie['value'],
                path=cookie['path'],
                domain=cookie['domain'],
                expires=cookie.get('expires') or cookie.get('expiry')
            )

    @classmethod
    def get_session_cookies(cls, session):
        cookies = []
        for cookie in session.cookies:
            cookies.append(dict(
                name=cookie.name,
                value=cookie.value,
                path=cookie.path,
                domain=cookie.domain,
                expires=cookie.expires
            ))
        return cookies

    def save_cookies(slef):
        slef.account.cookies = json.dumps(slef.get_session_cookies(slef.s))
        AccountDAO.commit()

    @classmethod
    def embed_html_iter(cls, resp):
        html_in_js_pattern = re.compile(r'\"html\":\"((?:[^"\\]|\\.)*)\"')
        for g in html_in_js_pattern.finditer(resp.text):
            yield json.loads('"' + g.group(1) + '"')

    @classmethod
    def check_avail(cls, resp):
        return True

    @classmethod
    def check_redirect(cls, resp):
        if resp.status_code in [301, 302]:
            return resp.headers['Location'], str(resp.status_code)
        groups = re.search(r'<meta\shttp-equiv=\"refresh"\s*content=\"0;\s*url=&#39;(?P<url>.*?)&#39;\"\/>', resp.text)
        if groups:
            return groups.group('url'), 'meta-refreash'
        return None, None

    @classmethod
    def check_relogin(cls, resp):
        """
        检查是否是重新登陆页面
        """

        cond1 = re.search(r'<title>Sina Visitor System</title>', resp.text)
        cond2 = re.search(r'var restore_back = function \(response\)', resp.text)
        return cond1 is not None and cond2 is not None

    def relogin(self, former_resp):
        """
        """
        def encodeURIComponent(s):
            return urllib.quote(str(s))

        url = 'https://passport.weibo.com/visitor/visitor?a=restore&cb=restore_back&from=weibo&_rand='
        url += '%.16f' % random.random()
        logging.info('restore1 new_url: {url}'.format(url=url))
        resp = self.s.get(url=url, headers={
            'Referer': former_resp.url
        })
        if resp.status_code != 200:
            logging.info('restore failed! status_code != 200')
            return False
        try:
            groups = re.search(r'restore_back\((?P<json>.*?)\);', resp.text)
            json_resp = json.loads(groups.group('json'))
            assert(json_resp['retcode'] == 20000000)
            assert(json_resp['data'])
        except Exception:
            logging.exception('restore failed!')
            logging.info(resp.text)
            return False
        alt = json_resp['data']['alt']
        if alt != '':
            savestate = json_resp['data']['savestate']
            requrl = "&url=" + encodeURIComponent(r'http://weibo.com/?retcode=6102')
            params = "entry=sso&alt=" + encodeURIComponent(alt)
            params += "&returntype=META" + "&gateway=1&savestate=" + encodeURIComponent(savestate) + requrl
            url = r'http://login.sina.com.cn/sso/login.php?' + params
        else:  # cross_domain
            return False
            logging.info('cross_domain')
            url = "http://login.sina.com.cn/visitor/visitor?a=crossdomain&cb=return_back&s="
            url += encodeURIComponent(json_resp["data"]["sub"])
            url += "&sp=" + encodeURIComponent(json_resp["data"]["subp"])
            url += "&from=" + "weibo" + "&_rand=" + '%.16f' % random.random()

        logging.info('restore2 new_url: {url}'.format(url=url))
        resp = self.s.get(url, headers={'Referer': resp.url})
        try:
            groups = re.search(r'location.replace\(\'(?P<url>.*?)\'\);', resp.text)
            url = groups.group('url')
            assert(url)
        except Exception:
            logging.exception('restore failed!')
            logging.info(resp.text)

        logging.info('restore3 new_url: {url}'.format(url=url))
        resp = self.s.get(url, headers={'Referer': resp.url})
        return resp

    def fetch(self, url, referer=None):
        if referer is None:
            referer = self.referer
        resp = self.s.get(url=url, headers={'Referer': referer})
        while True:
            new_url, reason = self.check_redirect(resp)
            if new_url:  # redierct
                logging.info("Fetching encounter redirect:\nreason:{reason}\ntarget:{target}\n".format(
                    reason=reason, target=new_url))
                resp = self.s.get(url=new_url)
                continue
            if self.check_relogin(resp):
                logging.info("Fetching encounter relogin:\n")
                resp = self.relogin(resp)
                if not resp:
                    logging.info('Fetch: elogin Failed')
                continue
            break
        self.referer = resp.url
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
