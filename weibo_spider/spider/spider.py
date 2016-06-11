#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json
import re
import requests
import logging
import random
import urllib.request
import urllib.parse
import urllib.error
import time

from db import Account
from db import AccountDAO
from db import RawDataDAO
from db import TweetDAO
from .parser import Parser
from .tweetp import TweetP
from .captcha import CaptchaDecoderFactory


class LoginFailedException(Exception):
    pass


class Spider(object):

    def __init__(self, account, rawdata_dao=None, tweet_dao=None):
        """
        爬虫类， 每个使用一个账户.

        account: Account 对象
        rawdata_dao: RawDataDAO
        tweet_dao: TweetDAO
        """
        self.logger = logging.getLogger('Spider')

        assert isinstance(account, Account)
        if rawdata_dao:
            if rawdata_dao is True:
                rawdata_dao = RawDataDAO()
            assert(isinstance(rawdata_dao, RawDataDAO))
        if tweet_dao:
            if tweet_dao is True:
                tweet_dao = TweetDAO()
            assert(isinstance(tweet_dao, TweetDAO))
        self.account = account
        self.rawdata_dao = rawdata_dao
        self.tweet_dao = tweet_dao
        self.s = requests.session()
        self.set_session_cookie(session=self.s,
                                cookies=account.cookies)
        self.s.headers['User-Agent'] = 'Mozilla/5.0 (Windows NT 10.0; WOW64) '\
            'AppleWebKit/537.36 \(KHTML, like Gecko) Chrome/49.0.2623.110 Safari/537.36'
        self.referer = ''
        self.parser = Parser()
        self.fetch('http://weibo.com/')
        self.capthca_decoder = CaptchaDecoderFactory('Ruokuai')()
        self.logger.info('Spider {0} initialize successful.'.format(self.account.email))

    def __del__(self):
        self.save_cookies()
        self.logger.info('Destory spider {email}.'.format(email=self.account.email))

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

    def get_cookies_json(self):
        return json.dumps(self.get_session_cookies(self.s))

    def save_cookies(self):
        self.account.cookies = json.dumps(self.get_session_cookies(self.s))
        account_dao = AccountDAO()
        account_dao.commit()

    def handle_login_failed(self):
        self.account.is_login = False
        account_dao = AccountDAO()
        account_dao.commit()
        raise LoginFailedException

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

    def handle_captcha(self, body, content_type):
        print("handle_captcha!")
        return self.capthca_decoder.decode(body, content_type)

    def check_captcha(self, resp):
        """检查验证码."""
        text = resp.text
        if text.find('yzm_submit') != -1 \
           and text.find('yzm_input') != -1:
            print("Got a captcha!")
            for html in self.parser.embed_html_iter(text):
                g = re.search(r'<img\ssrc=\"(?P<src>[^\"]*?)\"\snode-type=\"yzm_img\">', html)
                url = urllib.parse.urljoin(resp.url, g.group('src'))
                _type = urllib.parse.parse_qs(urllib.parse.urlsplit(url).query)['type']
                img_resp = self.s.get(url)
                code = self.handle_captcha(img_resp.content, img_resp.headers['Content-Type'])
                print('Captcha code is {0}'.format(code))
                post_url = urllib.parse.urljoin(resp.url,
                                                '/ajax/pincode/verified?__rnd={0}'.format(int(time.time() * 1000)))
                resp_n = self.s.post(
                    url=post_url,
                    headers={
                        'Content-Type': 'application/x-www-form-urlencoded',
                        'X-Requested-With': 'XMLHttpRequest',
                        'Referer': resp.url,
                    },
                    data={
                        'secode': code,
                        'type': _type,
                        'page_id': re.search(r"\$CONFIG\['pageid'\]\s*=\s*'(?P<pageid>.*?)';", text).group('pageid'),
                        '_t': 0,
                    }
                )
                # successful: u'{"code":"100000","msg":"","data":{"retcode":"9e27b221a5b6e577d40e45226442bd40"}}'
                if json.loads(resp_n.text)['code'] == '100000':
                    return True
                else:
                    return False
        return None

    def relogin(self, former_resp):
        """
        处理长时间未登录后登陆的流程.
        """
        def encodeURIComponent(s):
            return urllib.parse.quote(str(s))
        url = 'https://passport.weibo.com/visitor/visitor?a=restore&cb=restore_back&from=weibo&_rand='
        url += '%.15g' % random.random()
        self.logger.info('restore1 new_url: {url}'.format(url=url))
        resp = self.s.get(url=url, headers={
            'Referer': former_resp.url
        })
        if resp.status_code != 200:
            self.logger.info('restore failed! status_code != 200')
            return False
        try:
            groups = re.search(r'restore_back\((?P<json>.*?)\);', resp.text)
            json_resp = json.loads(groups.group('json'))
            assert(json_resp['retcode'] == 20000000)
            assert(json_resp['data'])
        except Exception:
            self.logger.exception('restore failed!')
            self.logger.info(resp.text)
            self.handle_login_failed()
            return False

        alt = json_resp['data']['alt']
        if alt != '':
            savestate = json_resp['data']['savestate']
            requrl = "&url=" + encodeURIComponent(r'http://weibo.com/?retcode=6102')
            params = "entry=sso&alt=" + encodeURIComponent(alt)
            params += "&returntype=META" + "&gateway=1&savestate=" + encodeURIComponent(savestate) + requrl
            url = r'http://login.sina.com.cn/sso/login.php?' + params
        else:  # cross_domain
            self.logger.info('cross_domain')
            self.handle_login_failed()
            return False
            url = "http://login.sina.com.cn/visitor/visitor?a=crossdomain&cb=return_back&s="
            url += encodeURIComponent(json_resp["data"]["sub"])
            url += "&sp=" + encodeURIComponent(json_resp["data"]["subp"])
            url += "&from=" + "weibo" + "&_rand=" + '%.15g' % random.random()

        self.logger.info('restore2 new_url: {url}'.format(url=url))
        resp = self.s.get(url, headers={'Referer': resp.url})
        try:
            groups = re.search(r'location.replace\(\'(?P<url>.*?)\'\);', resp.text)
            url = groups.group('url')
            assert(url)
        except Exception:
            self.logger.exception('restore failed!')
            self.logger.info(resp.text)

        self.logger.info('restore3 new_url: {url}'.format(url=url))
        resp = self.s.get(url, headers={'Referer': resp.url})
        return resp

    def fetch(self, url, referer=None):
        """
        抓取一个页面，处理各种需要的跳转和重登录
        """
        if referer is None:
            referer = self.referer
        resp = self.s.get(url=url, headers={'Referer': referer})
        while True:
            new_url, reason = self.check_redirect(resp)
            if new_url:  # redierct
                self.logger.info("Fetching encounter redirect:\nreason:{reason}\ntarget:{target}\n".format(
                    reason=reason, target=new_url))
                resp = self.s.get(url=new_url)
                continue
            if self.check_relogin(resp):
                self.logger.info("Fetching encounter relogin:\n")
                self.logger.info("URL: {0}\n".format(resp.url))
                resp = self.relogin(resp)
                if not resp:
                    self.logger.info('Fetch: relogin Failed')
                    break
                self.save_cookies()
                resp = self.s.get(url=url, headers={'Referer': referer})
                continue
            if self.check_captcha(resp) is not None:
                resp = self.s.get(url=url, headers={'Referer': referer})
                continue
            break
        self.referer = resp.url
        self.last_resp = resp
        return resp

    def fetch_weibo(self, user_id, weibo_id):
        pass

    def fetch_search(self, keyword, page=1):
        quote_keyword = urllib.parse.quote(urllib.parse.quote(keyword))  # quote 两次
        if page == 1:
            url = 'http://s.weibo.com/weibo/{quote}&nodup=1'.format(quote=quote_keyword)
            referer = 'http://s.weibo.com/weibo/{quote}?topnav=1&wvr=6'.format(quote=quote_keyword)
        else:
            url = 'http://s.weibo.com/weibo/{quote}&nodup=1&page={page}'.format(quote=quote_keyword, page=page)
            referer = 'http://s.weibo.com/weibo/{quote}&nodup=1&page={page}'.format(quote=quote_keyword, page=page - 1)
        resp = self.fetch(url=url, referer=referer)
        weibos, _, _ = self.parser.parse_search_result(resp.text)
        return weibos

    def fetch_search_iter(self, keyword, start_page=1):
        quote_keyword = urllib.parse.quote(urllib.parse.quote(keyword))  # quote 两次
        page = start_page - 1
        assert(page >= 0)
        next_url = None
        while True:
            page += 1
            weibos = []
            self.logger.info('Fetching search page {page}'.format(page=page))
            if page == 1:
                url = 'http://s.weibo.com/weibo/{quote}&nodup=1'.format(quote=quote_keyword)
                referer = 'http://s.weibo.com/weibo/{quote}?topnav=1&wvr=6'.format(quote=quote_keyword)
            else:
                url = 'http://s.weibo.com/weibo/{quote}&nodup=1&page={page}'.format(quote=quote_keyword, page=page)
                referer = 'http://s.weibo.com/weibo/{quote}&nodup=1&page={page}'.format(
                    quote=quote_keyword, page=page - 1)
            resp = self.fetch(url=url, referer=referer)
            _weibos, _, next_url = self.parser.parse_search_result(resp.text)
            weibos += _weibos
            self.save_weibo(weibos)
            yield weibos, page, next_url is not None
            print('next_url', next_url)
            if not next_url:
                break

    def fetch_topic_iter(self, keyword):
        def get_pl_name(text):
            max_len = 0
            target = None
            for item in self.parser.embed_html_iter(text):
                if len(item) > max_len:
                    max_len = len(item)
                    target = item
            return re.search(r'Pl_Third_App__\d+', target).group(0)

        if isinstance(keyword, str):
            keyword = keyword.encode('utf-8')
        url = 'http://huati.weibo.com/k/{quote}?from=501'.format(quote=urllib.parse.quote(keyword))
        page = 0
        referer = None
        pl_name = None
        while True:
            page += 1
            weibos = []
            self.logger.info('Topic: fetching page {page}'.format(page=page))
            if not referer:
                resp = self.fetch(url=url)
            else:
                resp = self.fetch(url=url, referer=referer)
            # extract params
            domain = re.search(r'\$CONFIG\[\'domain\'\]=\'(\d+)\';', resp.text).group(1)
            page_id = re.search(r'\$CONFIG\[\'page_id\'\]=\'(\w+)\';', resp.text).group(1)
            referer = resp.url
            main_url_parsed = urllib.parse.urlparse(str(resp.url))
            params_main = urllib.parse.parse_qs(main_url_parsed.query)
            params_main['script_uri'] = main_url_parsed.path

            resps = []
            resps.append(resp)
            resp_is_json = False
            pagebar = 0
            pl_name = pl_name or get_pl_name(resp.text)
            while True:
                _weibos, lazyload, next_url = self.parser.parse_topic_result(resp.text, is_json=resp_is_json)
                weibos += _weibos
                if lazyload is None:
                    break
                # fetch next (Ajax)
                url = 'http://weibo.com/p/aj/v6/mblog/mbloglist'
                params = {
                    'ajwvr': 6,
                    'domain': domain,
                    'id': page_id,
                    'pl_name': pl_name,
                    'pagebar': pagebar,  # 是否显示翻页
                    'domain_op': domain,
                    '__rnd': int(time.time() * 1000),
                    'feed_type': 1
                }
                params.update(params_main)
                params.update(lazyload['action-data'])
                params['page'] = params.get('page', 1)
                params['pre_page'] = params.get('pre_page', params['page'])
                self.logger.info('Topic lazyload:')
                resp = self.s.get(url=url, params=params, headers={
                    'X-Requested-With': 'XMLHttpRequest',
                    'Content-Type': 'application/x-www-form-urlencoded',
                    'Referer': referer
                })
                resp_is_json = True
                pagebar += 1
                resps.append(resp)
            self.save_weibo(weibos)
            yield weibos, page, next_url is not None
            if next_url:
                url = urllib.parse.urljoin(referer, next_url)
            else:
                break

    def save_to_file(self, resp=None, filename=None):
        if resp is None:
            resp = self.last_resp
        if filename is None:
            import os
            import settings
            import uuid
            filename = os.path.join(settings.SAMPLES_DIR, str(uuid.uuid4()) + '.html')
        with open(filename, 'wb') as file:
            file.write(resp.content)

    def save_weibo(self, weibos):
        if isinstance(weibos, TweetP):
            weibos = [weibos]
        for weibo in weibos:
            if self.rawdata_dao:
                self.rawdata_dao.set_raw_data(weibo.mid, weibo.raw_html)
                if weibo.forward_tweet:
                    self.rawdata_dao.set_raw_data(weibo.forward_tweet.mid, weibo.forward_tweet.raw_html)
            if self.tweet_dao:
                self.tweet_dao.update_or_create_tweetp(weibo)
                if weibo.forward_tweet:
                    self.tweet_dao.update_or_create_tweetp(weibo.forward_tweet)


def get_random_spider():
    account_dao = AccountDAO()
    account = account_dao.get_random_account()
    rawdata_dao = RawDataDAO()
    tweet_dao = TweetDAO()
    spider = Spider(account=account, rawdata_dao=rawdata_dao, tweet_dao=tweet_dao)
    return spider
