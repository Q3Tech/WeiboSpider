#!/usr/bin/env python
# -*- coding: utf-8 -*-
import requests
import settings
import hashlib
import mimetypes
import os


class CaptchaDecoder(object):
    """验证码识别基类."""

    def __init__(self):
        self._sample_path = os.path.join(settings.SAMPLES_DIR, 'captcha')
        if not os.path.exists(self._sample_path):
            os.makedirs(self._sample_path)

    def decode(self, captcha, content_type):
        assert(isinstance(captcha, bytes))
        extension = mimetypes.guess_extension(content_type)
        filename = 'captcha' + extension
        sha1 = hashlib.sha1(captcha).hexdigest()

        with open(os.path.join(self._sample_path, sha1 + extension), 'wb') as f:
            f.write(captcha)
        result = self._decode(captcha, content_type, filename)
        return result

    def _decode(self, captcha, content_type, filename):
        raise NotImplementedError()


class VerifyBotAdapter(CaptchaDecoder):
    """VerifyBOT Adapter."""

    def __init__(self, url=None):
        super(VerifyBotAdapter, self).__init__()
        if not url:
            url = settings.VERIFY_BOT_URL
        self.bot_url = url
        self.s = requests.session()

    def _decode(self, captcha, content_type, filename):
        resp = self.s.post(self.bot_url, files={
            'captcha': (filename, captcha, content_type)
        })
        return resp.text


class RuokuaiAdapter(CaptchaDecoder):
    """若快答题适配器"""
    def __init__(self, ruokuai_settings=None):
        super(RuokuaiAdapter, self).__init__()
        if not ruokuai_settings:
            ruokuai_settings = settings.RUOKUAI_SETTINGS
        self.settings = ruokuai_settings
        self.base_params = {
            'username': self.settings['username'],
            'password': self.settings['password'],
            'softid': self.settings['softid'],
            'softkey': self.settings['softkey'],
        }
        self.headers = {
            'Connection': 'Keep-Alive',
            'Expect': '100-continue',
            'User-Agent': 'ben',
        }
        self.url = 'http://api.ruokuai.com/create.json'

    def _decode(self, captcha, content_type, filename):
        params = {
            'typeid': 3040
        }
        params.update(self.base_params)
        files = {'image': (filename, captcha)}
        r = requests.post(self.url, data=params, files=files, headers=self.headers)
        return r.json()['Result']


def CaptchaDecoderFactory(name):
    if name == 'VerifyBOT':
        return VerifyBotAdapter
    elif name == 'Ruokuai':
        return RuokuaiAdapter
    else:
        raise Exception('Captcha decoder doesn\'t exists')
