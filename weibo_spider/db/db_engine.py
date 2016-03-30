# -*- coding: utf-8 -*-
# @Author: Comzyh
# @Date:   2016-03-06 20:25:20
# @Last Modified by:   Comzyh
# @Last Modified time: 2016-03-30 18:58:17
from sqlalchemy import create_engine
from sqlalchemy import Column, Integer, String, Boolean, DATETIME, TEXT
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.sql.expression import false

import settings

connect_string = 'mysql://{user}:{password}@{host}/{database}'.format(**settings.MYSQL_SETTINGS)
print connect_string
__engine = create_engine(connect_string, convert_unicode=True, echo=True)


Base = declarative_base()


class Account(Base):
    """
    表示爬虫账户
    """
    __tablename__ = 'account'

    id = Column(Integer, primary_key=True)
    email = Column(String(50), nullable=False, unique=True)
    password = Column(String(50))
    is_login = Column(Boolean(50), default=False)
    login_time = Column(DATETIME)
    cookies = Column(TEXT)

    def __repr__(self):
        return "<Account: %s>" % self.email


engine = __engine.connect()
Session = sessionmaker(bind=engine)
session = Session()


class AccountDAO(object):

    def __init__(self, arg):
        super(AccountDAO, self).__init__()
        self.arg = arg

    @classmethod
    def not_login_iter(cls):
        for account in session.query(Account).filter(Account.is_login == false()):
            yield account

    @classmethod
    def get_or_create(cls, *args, **kwargs):
        pass

    @classmethod
    def update_or_create(cls, *args, **kwargs):
        """
        ex:
        AccountDAO.update_or_create(email='shuntuov38964@163.com', password='a123456')
        """
        created = False
        assert 'id' in kwargs or 'email' in kwargs
        if 'id' in kwargs:
            account = session.query(Account).filter(
                Account.id == kwargs['id']).one_or_none()
        elif 'email' in kwargs:
            account = session.query(Account).filter(
                Account.email == kwargs['email']).one_or_none()

        if account:
            print kwargs
            for k, v in kwargs.iteritems():
                setattr(account, k, v)
        else:
            created = True
            account = Account(**kwargs)
            session.add(account)
        session.commit()
        return account, created


def create_db():
    Base.metadata.create_all(engine)

if __name__ == '__main__':

    import IPython

    IPython.embed()
