# -*- coding: utf-8 -*-
"""提供数据库连接功能."""
import logging
from functools import wraps

from sqlalchemy import create_engine

from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from contextlib import contextmanager

import settings

from core import Singleton

Base = declarative_base()


class DBEngine(Singleton):

    def __init__(self):
        self.logger = logging.getLogger('DBEngine')
        self.connect_string = 'mysql+pymysql://{user}:{password}@{host}/{database}?charset=utf8mb4'.format(
            **settings.MYSQL_SETTINGS)
        self.logger.info('Connect String: {0}'.format(self.connect_string))
        __engine = create_engine(self.connect_string, echo=True)
        self.engine = __engine.connect()
        self.sessionmaker = sessionmaker(bind=self.engine)

    def create_db(self):
            """建立数据库."""
            Base.metadata.create_all(self.engine)

    def get_session(self):
        session = self.sessionmaker()
        self.logger.debug("Distribute a new SESSION. {0}".format(session))
        return session

    @contextmanager
    def Session(self):
        try:
            session = self.get_session()
            yield session
            session.commit()
        except Exception:
            print("SESSION ERROR", session)
            logging.exception("Session Exception.")
            session.rollback()
            raise
        finally:
            print('CLOSE', session)
            session.close()


def ensure_session(func):
    """确保DAO方法调用时有session."""

    @wraps(func)
    def wrapper(*args, **kwargs):
        if 'session' in kwargs:
            return func(*args, **kwargs)
        else:
            db_engine = DBEngine()
            with db_engine.Session() as session:
                kwargs['session'] = session
                return func(*args, **kwargs)
    return wrapper
