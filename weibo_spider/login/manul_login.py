#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Author: Comzyh
# @Date:   2016-01-23 22:02:48
# @Last Modified by:   Comzyh
# @Last Modified time: 2016-04-04 02:54:20

import datetime
import json

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions


from db.db_engine import AccountDAO


class LoginExecuter(object):
    """docstring for LoginExecuter"""

    def __init__(self):
        super(LoginExecuter, self).__init__()
        self.browser = webdriver.Chrome()

    def login(self, username, password):
        # 整体操作太容易出错了
        try:
            self.browser.delete_all_cookies()
            self.browser.get("http://weibo.com")
            normal_tab = WebDriverWait(self.browser, 10).until(
                expected_conditions.presence_of_element_located((By.XPATH, "//a[@node-type='normal_tab']")))
            normal_tab.click()  # 点击'账号登陆'
            username_input = WebDriverWait(self.browser, 1).until(
                expected_conditions.presence_of_element_located((By.NAME, "username")))
            # username_input = self.browser.find_element_by_name('username')
            password_input = self.browser.find_element_by_name('password')
            submit_btn = self.browser.find_element_by_xpath(
                "//a[@action-type='btn_submit']")
            username_input.clear()
            username_input.send_keys(username)
            password_input.clear()
            password_input.send_keys(password)
            submit_btn.click()

            # 检测登陆成功
            normal_tab = WebDriverWait(self.browser, 40).until(
                expected_conditions.presence_of_element_located((By.CLASS_NAME, "gn_name")))
            print('login successful')
            cookies = self.browser.get_cookies()
            # self.browser.get("http://passport.weibo.com/js/visitor/mini.js")
            self.browser.get("https://passport.weibo.com/visitor/")
            for cookie in self.browser.get_cookies():
                print cookie['domain']
                if cookie['domain'].find('passport.weibo.com') != -1:
                    cookies.append(cookie)
        except Exception, e:
            # raise e
            print e
            return None
        else:
            return cookies


def import_account_from_file(filename):
    account_file = open(filename, 'r')
    line_num = 0
    create_num = 0
    for line in account_file.readlines():
        print (line)
        line_num += 1
        email, password = line.split('----')[:2]
        _, created = AccountDAO.update_or_create(email=email, password=password)
        if created:
            create_num += 1
    print ('{line} lines, {created} created.'.format(line=line_num, created=create_num))


def login(login_executer, email, password):
    resp = login_executer.login(email, password)
    if not resp:
        return False
    AccountDAO.update_or_create(email=email,
                                password=password,
                                is_login=True,
                                login_time=datetime.datetime.now(),
                                cookies=json.dumps(resp))
    return True


def start_login():
    login_executer = LoginExecuter()
    for account in AccountDAO.not_login_iter():
        login(login_executer=login_executer, email=account.email, password=account.password)