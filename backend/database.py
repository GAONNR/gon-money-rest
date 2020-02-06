import argparse
import sqlalchemy as db

from logzero import logger
from sqlalchemy import (Column, Integer, String, Boolean, ForeignKey)
from sqlalchemy.sql import expression
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class User(Base):
    __tablename__ = 'user'

    no = Column(Integer, primary_key=True)
    uid = Column(String(40), unique=True, nullable=False)
    name = Column(String(80))
    nick = Column(String(80), nullable=False)
    account = Column(String(80))
    profile_image = Column(String(160))
    reduce_money = Column(Boolean, default=False,
                          server_default=expression.false())
    confirm = Column(Boolean, default=False, server_default=expression.false())
    notice = Column(Boolean, default=False, server_default=expression.false())

    def __init__(self,
                 uid,
                 nick,
                 name=None,
                 account=None,
                 profile_image=None,
                 reduce_money=None,
                 confirm=None,
                 notice=None):
        self.name = name
        self.uid = uid
        self.nick = nick
        self.account = account
        self.profile_image = profile_image
        self.reduce_money = reduce_money
        self.confirm = confirm
        self.notice = notice

    def as_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}


class Trade(Base):
    __tablename__ = 'trade'

    no = Column(Integer, primary_key=True)
    eul_uid = Column(String(40), ForeignKey('user.uid'))
    gab_uid = Column(String(40), ForeignKey('user.uid'))
    price = Column(Integer, nullable=False)
    reduce_price = Column(Integer)
    date = Column(String(10))
    content = Column(String(160))
    account = Column(String(80))
    completed = Column(Boolean, default=False,
                       server_default=expression.false())
    reduced = Column(Boolean, default=False, server_default=expression.false())
    confirmed = Column(Boolean, default=True, server_default=expression.true())

    def __init__(self,
                 eul_uid,
                 gab_uid,
                 price,
                 reduce_price=None,
                 date=None,
                 content=None,
                 account=None,
                 completed=None,
                 reduced=None,
                 confirmed=None
                 ):
        self.eul_uid = eul_uid
        self.gab_uid = gab_uid
        self.price = price
        self.reduce_price = reduce_price
        self.date = date
        self.content = content
        self.account = account
        self.completed = completed
        self.reduced = reduced
        self.confirmed = confirmed

    def as_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}


def get_engine(db_path):
    return db.create_engine('sqlite:///%s' % db_path, connect_args={'check_same_thread': False})


def db_connect(db_path):
    Session = sessionmaker(bind=get_engine(db_path))
    logger.info('Connected to database')
    return Session


def _main():
    parser = argparse.ArgumentParser()
    parser.add_argument('db_path', default='../db/money.db')
    parser.add_argument('--init_db', action='store_true')
    args = parser.parse_args()

    if args.init_db:
        engine = get_engine(args.db_path)
        Base.metadata.create_all(engine)
        logger.info('Initialized database')


if __name__ == '__main__':
    _main()
