# -*- coding: utf-8 -*-
# @Author: Comzyh
# @Date:   2016-03-06 20:25:20
# @Last Modified by:   Comzyh
# @Last Modified time: 2016-04-20 01:57:29
from sqlalchemy import create_engine

from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

import settings

from core import Singleton

Base = declarative_base()


class DBEngine(Singleton):

    def __init__(self):
        self.connect_string = 'mysql://{user}:{password}@{host}/{database}?charset=utf8mb4'.format(
            **settings.MYSQL_SETTINGS)
        print self.connect_string
        __engine = create_engine(self.connect_string, echo=True)
        self.engine = __engine.connect()
        Session = sessionmaker(bind=self.engine)
        self.session = Session()

    def create_db(self):
            u"""建立数据库."""
            Base.metadata.create_all(self.engine)

if __name__ == '__main__':

    import IPython

    IPython.embed()
