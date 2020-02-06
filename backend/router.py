import database

from sqlalchemy import text
from sqlalchemy.sql import func
from flask_restful import (Resource, reqparse)
from database import (User, Trade)

SESSION = database.db_connect('../db/money.db')


def intify(x): return x if x else 0


class Status(Resource):
    def get(self):
        return {'status': True}


class GetUser(Resource):
    def get(self):
        try:
            req_parser = reqparse.RequestParser()
            req_parser.add_argument('uid', type=str)
            req_args = req_parser.parse_args()

            uid = req_args['uid']

            session = SESSION()

            if uid is None:
                all_users = session.query(User).all()
                return [user.as_dict() for user in all_users]
            else:
                user = session.query(User).filter_by(uid=uid).first()
                return user.as_dict()
        except Exception as e:
            return {'error': str(e)}


class GetTrade(Resource):
    def get(self):
        try:
            req_parser = reqparse.RequestParser()
            req_parser.add_argument('tid', type=str)  # trade no.
            req_parser.add_argument('did', type=str)  # debtor
            req_parser.add_argument('cid', type=str)  # creditor
            req_parser.add_argument('rec', type=int)
            req_parser.add_argument('dead', type=bool)
            req_args = req_parser.parse_args()

            tid = req_args['tid']
            did = req_args['did']
            cid = req_args['cid']
            rec = req_args['rec']
            dead = req_args['dead']

            session = SESSION()

            if tid:
                trade = session.query(Trade).filter_by(no=tid).first()
                return trade.as_dict()
            elif did:
                trades = None
                if dead:
                    trades = session.query(Trade).filter_by(gab_uid=did)
                else:
                    trades = session.query(Trade).filter_by(
                        gab_uid=did, completed=False)
                return [trade.as_dict() for trade in trades]
            elif cid:
                trades = None
                if dead:
                    trades = session.query(Trade).filter_by(eul_uid=cid)
                else:
                    trades = session.query(Trade).filter_by(
                        eul_uid=cid, completed=False)
                return [trade.as_dict() for trade in trades]
            elif rec:
                trades = None
                if dead:
                    trades = session.query(Trade)\
                        .order_by(Trade.no.desc())\
                        .offset(rec - 5)\
                        .limit(5)
                else:
                    trades = session.query(Trade)\
                        .order_by(Trade.no.desc())\
                        .filter_by(completed=False)\
                        .offset(rec - 5)\
                        .limit(5)
                return [trade.as_dict() for trade in trades]
            else:
                summary = None
                if dead:
                    summary = session.query(func.sum(
                        Trade.reduce_price)).filter_by(completed=False)\
                        .first()[0]
                else:
                    summary = session.query(func.sum(Trade.price)).first()[0]
                return int(summary)
        except Exception as e:
            return {'error': str(e)}


class GetStats(Resource):
    def get(self):
        try:
            req_parser = reqparse.RequestParser()
            req_parser.add_argument('cnum', type=int)
            req_parser.add_argument('dnum', type=int)
            req_args = req_parser.parse_args()

            cnum = req_args['cnum']
            dnum = req_args['dnum']

            session = SESSION()

            if cnum:
                ranking = session.query(Trade.eul_uid,
                                        func.sum(Trade.reduce_price).label('sum'))\
                    .filter_by(completed=False)\
                    .group_by(Trade.eul_uid)\
                    .order_by(text('sum desc'))\
                    .limit(cnum)
                return [{'uid': rank[0], 'sum': rank[1]} for rank in ranking]
            elif dnum:
                ranking = session.query(Trade.gab_uid,
                                        func.sum(Trade.reduce_price).label('sum'))\
                    .filter_by(completed=False)\
                    .group_by(Trade.gab_uid)\
                    .order_by(text('sum desc'))\
                    .limit(dnum)
                return [{'uid': rank[0], 'sum': rank[1]} for rank in ranking]
        except Exception as e:
            return {'error': str(e)}
