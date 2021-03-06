# -*- coding: utf-8 -*-
# @Author: Comzyh
# @Date:   2016-04-20 01:53:03
# @Last Modified by:   Comzyh
# @Last Modified time: 2016-04-20 02:08:57
"""Weibo Account."""
from sqlalchemy import Column, Integer, String, Boolean, DATETIME, TEXT
from sqlalchemy.sql.expression import false, true
from sqlalchemy.sql.expression import func

from .db_engine import Base
from .db_engine import DBEngine
from .db_engine import ensure_session


from core import Singleton


class Account(Base):
    """
    表示爬虫账户.

    id:
    email:
    password:
    is_login:
    login_time:
    cookies:
    """

    __tablename__ = 'account'

    id = Column(Integer, primary_key=True)
    email = Column(String(50), nullable=False, unique=True)
    password = Column(String(50))
    is_login = Column(Boolean(50), default=False)
    login_time = Column(DATETIME)
    cookies = Column(TEXT)

    def __repr__(self):
        """__repr__."""
        return "<Account: %s>" % self.email


class AccountDAO(Singleton):
    """用于操纵Account数据的类."""

    def __init__(self):
        self.engine = DBEngine()

    def not_login_iter(self):
        with self.engine.Session() as session:
            for account in session.query(Account).filter(Account.is_login == false()):
                yield account

    def account_iter(self):
        with self.engine.Session() as session:
            for account in session.query(Account):
                yield account

    @ensure_session
    def get_or_create(self, *args, **kwargs):
        session = kwargs.pop('session')
        assert 'id' in kwargs or 'email' in kwargs
        if 'id' in kwargs:
            account = session.query(Account).filter(
                Account.id == kwargs['id']).one_or_none()
        elif 'email' in kwargs:
            account = session.query(Account).filter(
                Account.email == kwargs['email']).one_or_none()
        return account

    @ensure_session
    def update_or_create(self, *args, **kwargs):
        """
        ex:
        AccountDAO.update_or_create(email='shuntuov38964@163.com', password='a123456')
        """
        session = kwargs.pop('session')
        created = False
        assert 'id' in kwargs or 'email' in kwargs
        if 'id' in kwargs:
            account = session.query(Account).filter(
                Account.id == kwargs['id']).one_or_none()
        elif 'email' in kwargs:
            account = session.query(Account).filter(
                Account.email == kwargs['email']).one_or_none()

        if account:
            print(kwargs)
            for k, v in kwargs.items():
                setattr(account, k, v)
        else:
            created = True
            account = Account(**kwargs)
            session.add(account)
        return account, created

    @ensure_session
    def get_random_account(self, session):
        q = session.query(Account).filter(Account.is_login == true())
        return q.order_by(func.rand()).first()
