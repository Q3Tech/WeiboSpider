# -*- coding: utf-8 -*-
"""提供数据库连接功能."""
from sqlalchemy import create_engine

from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.engine.url import URL


import settings

from core import Singleton

Base = declarative_base()


class DBEngine(Singleton):

    def __init__(self):
        self.connect_string = 'mysql+pymysql://{user}:{password}@{host}/{database}?charset=utf8mb4'.format(
            **settings.MYSQL_SETTINGS)
        print(self.connect_string)
        __engine = create_engine(self.connect_string, echo=False, isolation_level="READ COMMITTED")
        self.engine = __engine.connect()
        self.session = self.get_session()

    def create_db(self):
            """建立数据库."""
            Base.metadata.create_all(self.engine)

    def get_session(self):
        Session = sessionmaker(bind=self.engine)
        return Session()


if __name__ == '__main__':

    import IPython

    IPython.embed()
