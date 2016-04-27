# -*- coding: utf-8 -*-
# @Author: Comzyh
# @Date:   2016-03-30 18:43:24
# @Last Modified by:   Comzyh
# @Last Modified time: 2016-04-15 17:44:40
u"""Weibo Spider配置模块."""
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

MYSQL_SETTINGS = {
    'host': '192.168.50.1',
    'user': 'root',
    'password': 'comzyh',
    'database': 'weibo_spider'
}

RAW_DATA_STORGE = {
    'type': 'LevelDB',
    'path': os.path.join(BASE_DIR, 'rawdata'),
}

SAMPLES_DIR  = os.path.join(BASE_DIR, 'samples')
