from slacker import Slacker
from requests.sessions import Session
from sqlalchemy import create_engine, text
from sqlalchemy.pool import NullPool
from functools import wraps
import collections
import logging
import asyncio
import aiofiles
import websockets
import re
import json
import pickle
import time

import config

# TODO:
# task ordering: end
# change user data: end
# message sender coroutine: end
# notice function: end
# make log
# make response message: end
# ddddddddddddeeeeeeeeebbbbbbbbbbbbuuuuuuuuuuuuuuuuuuuuuuuuuuuggggg : maybe end

# channels
# money : C02QQKZ9N
# test_for : C02PM7XQ1

log_task = None


def message(msg, channel='C02QQKZ9N', dm=None):
    if dm:
        opening = slack.im.open(dm).body
        if opening['ok']:
            channel = opening['channel']['id']
    msg_dict = {'id': 1, 'type': 'message', 'channel': channel, 'text': msg}
    asyncio.async(ws.send(json.dumps(msg_dict)))


def ordering(manage_task):
    def set_decorator(func):
        @asyncio.coroutine
        def wrapper(*args, **kwargs):
            nonlocal manage_task
            old_task = manage_task
            @asyncio.coroutine
            def manager():
                nonlocal func
                coros = func(*args, **kwargs)
                tasks = [asyncio.async(coro) for coro in coros]
                return (yield from asyncio.gather(*tasks))
            task = manage_task = asyncio.async(manager())
            if old_task:
                yield from asyncio.wait_for(old_task, None)
            return (yield from asyncio.gather(task))[0]
        return wrapper
    return set_decorator


def exe(sts):
    if not isinstance(sts, list):
        sts = [sts]
    global engine
    result = []
    for st, param in sts:
        result.append(engine.execute(text(st), param))
    return result


@asyncio.coroutine
def money(uid, match):
    debt = match.group('m_debt')
    content = match.group('content')
    account = match.group('m_account')
    res = exe(
        ('select account, confirm, reduce_money from User where uid=:uid', {'uid': uid}))
    (base_account, confirm, reduce_money) = res[0].fetchone()
    if not account:
        if not base_account:
            message('no account')
            return
        account = base_account
    it = pat_m.finditer(debt)
    sts = []
    entire = 0
    for m in it:
        try:
            ricecake = pat_mm.findall(m.group('members'))
            entire += len(ricecake)
            price = int(eval(m.group('price')))
            if price <= 0 or price > 5000000:
                continue
            for u in ricecake:
                if u == uid:
                    continue
                sts.append(('insert into Trade (eul_uid,gab_uid,price,reduce_price,date,content,account,confirmed) values (:uid,:u,:price,:price,date("now","localtime"),:content,:account,:confirmed)', {
                           'uid': uid, 'u': u, 'price': price, 'content': content, 'account': account, 'confirmed': not confirm}))
        except:
            continue
    result = exe(sts)
    sucess = len(result)
    if sucess == entire:
        message('Whole %d trade registered' % entire)
    else:
        message('*%d of %d trade failed*' % (entire-sucess, entire))
    if reduce_money:
        for rsp in result:
            no = rsp.lastrowid
            res = exe(
                ('select gab_uid, eul_uid, reduce_price from Trade where (select reduce_money from User where uid=gab_uid)=1 and no=:no', {'no': no}))
            tup = res[0].fetchone()
            if tup:
                (gab_uid, eul_uid, reduce_price) = tup
                yield from eliminator(eul_uid, gab_uid, reduce_price, no)


@asyncio.coroutine
def eliminator(giver, reciever, price, fix_no=None):
    is_reduce = (lambda x: 1 if x else 0)(fix_no)
    res = exe(('select no,reduce_price from Trade where gab_uid=:giver and eul_uid=:reciever and completed=0', {
              'giver': giver, 'reciever': reciever}))[0]
    sts = []
    flag = False
    for no, rprice in res.fetchall():
        if not price:
            break
        old_price = price
        old_rprice = rprice
        if rprice <= price:
            price -= rprice
            rprice = 0
            sts.append(('update Trade set reduce_price=:rprice, completed=1, reduced=:is_reduce where no=:no', {
                       'is_reduce': is_reduce, 'no': no, 'rprice': rprice}))
        else:
            rprice -= price
            price = 0
            sts.append(('update Trade set reduce_price=:rprice, reduced=:is_reduce where no=:no', {
                       'rprice': rprice, 'is_reduce': is_reduce, 'no': no}))
        if is_reduce:
            flag = True
            asyncio.async(reduce_log_write('%d : %d \u2192 %d, %d : %d \u2192 %d, %d reduced' % (
                fix_no, old_price, price, no, old_rprice, rprice, old_price-price)))
    if flag:
        if price == 0:
            sts.append(('update Trade set reduce_price=0, reduced=:is_reduce, completed=1 where no=:no', {
                       'is_reduce': is_reduce, 'no': fix_no}))
        else:
            sts.append(('update Trade set reduce_price=:price, reduced=:is_reduce where no=:no', {
                       'price': price, 'is_reduce': is_reduce, 'no': fix_no}))
    if not is_reduce:
        if price > 0:
            message('you send over %d' % price)
    exe(sts)


@asyncio.coroutine
def send_money(gab_uid, eul_uid, price):
    try:
        price = int(eval(price))
        if price > 0 and price <= 5000000:
            yield from eliminator(gab_uid, eul_uid, price)
    except:
        pass


@asyncio.coroutine
def send(uid, match):
    debt = match.group('s_debt')
    it = pat_s.finditer(debt)
    for m in it:
        if m.group('member'):
            yield from send_money(uid, m.group('member'), m.group('price'))
        else:
            no = int(m.group('num'))
            st = [('update Trade set completed=1 where no=:no and gab_uid=:uid', {
                   'no': no, 'uid': uid})]
            st.append(('select eul_uid from Trade where no=:no and gab_uid=:uid', {
                      'no': no, 'uid': uid}))
            res = exe(st)
            eul_uid = res[1].fetchone()
            if eul_uid:
                eul_uid = eul_uid[0]
                res = exe(
                    ('select notice from User where uid=:eul_uid', {'eul_uid': eul_uid}))
                if (res[0].fetchone())[0]:
                    message('Trade number %d was paid' % no, dm=eul_uid)


@asyncio.coroutine
def remove(uid, match):
    numbers = match.group('d_num').split()
    sts = []
    for num in numbers:
        print(num)
        sts.append(('delete from Trade where no=:num and eul_uid=:uid and reduced=0', {
                   'num': int(num), 'uid': uid}))
    res = exe(sts)


def onoff(choco):
    if choco in ['켬', '킴', '켜기', '키기', 'on']:
        return True
    else:
        return False


@asyncio.coroutine
def eliminate(uid, match):
    mode = onoff(match.group('e_mode'))
    exe(('update User set reduce_money=:mode where uid=:uid',
         {'mode': mode, 'uid': uid}))
    if mode:
        res = exe(
            ('select gab_uid,reduce_price,no from Trade where (select reduce_money from User where uid=gab_uid)=1 and eul_uid=:uid and completed=0', {'uid': uid}))
        for gab_uid, reduce_price, no in res.fetchall():
            yield from eliminator(uid, gab_uid, reduce_price, no)


def help_msg():
    message('''1. *!보내요* ~내용~  @member1 @member2 1000 ~원~ @member3 500 ~원~ ~계좌~
2. *!보냄* 142 143 @member 1000 ~원~
3. *!삭제* 144 145
4. *!소거* 켬 _or_ 끔
5. *!도움*
6. *!받음* 켬 _or_ 끔 / 146 147
7. *!설정*
8. *!계좌* 우리 1002-123-456789
9. *!알림* 켬 _or_ 끔''')


@asyncio.coroutine
def recv(uid, match):
    numbers = match.group('r_num')
    if numbers:
        numbers = numbers.split()
        sts = []
        for num in numbers:
            sts.append(('update Trade set confirmed=1, completed=1 where no=:num and eul_uid=:uid', {
                       'num': int(num), 'uid': uid}))
        exe(sts)
    else:
        mode = onoff(match.group('r_mode'))
        exe(('update User set confirm=:mode where uid=:uid',
             {'mode': mode, 'uid': uid}))


@asyncio.coroutine
def config_msg(uid):
    res = exe(
        ('select reduce_money, account, confirm, notice from User where uid=:uid', {'uid': uid}))
    (reduce_money, account, confirm, notice) = res[0].fetchone()
    def convert(x): return 'on' if x else 'off'
    message('''계좌 : %s\n소거 : %s\n받음 : %s\n알림 : %s''' %
            (account, convert(reduce_money), convert(confirm), convert(notice)))


@asyncio.coroutine
def set_account(uid, match):
    exe(('update User set account=:account where uid=:uid',
         {'account': match.group('account'), 'uid': uid}))


@asyncio.coroutine
def notice(uid, match):
    mode = onoff(match.group('n_mode'))
    exe(('update User set notice=:mode where uid=:uid',
         {'mode': mode, 'uid': uid}))


@asyncio.coroutine
def change_user_data(user_info):
    res = exe(('update User set name=:name, nick=:nick, profile_image=:profile_image where uid=:uid', {'name': user_info.get(
        'real_name', 'no name'), 'nick': user_info['name'], 'profile_image': user_info['profile'].get('image_original'), 'uid': user_info['id']}))
    if res[0].rowcount != 1:
        res = exe(('insert into User (name,nick,profile_image,uid) values (:name,:nick,:profile_image,:uid)', {'name': user_info.get(
            'real_name', 'no name'), 'nick': user_info['name'], 'profile_image': user_info['profile'].get('image_original'), 'uid': user_info['id']}))
    return res[0].rowcount


@asyncio.coroutine
def update_member():
    success = 0
    fail = 0
    for user_info in response.body['users']:
        res = (yield from change_user_data(user_info))
        success += res
        fail += (1-res)
    return (success, fail)


@asyncio.coroutine
def msg_parser(msg):
    global start
    msg = json.loads(msg)
    # 1. !(보내요|주세요|돈|sendme|giveme|money|show me the money|smtm|m)
    # 2. !(보냄|send|remit|s)
    # 3. !(삭제|del|delete|d)
    # 4. !(소거|reduce|eliminate|e)
    # 5. !(도움|help|h)
    # 6. !(받음|확인|check|recieve|recv|r)
    # 7. !(설정|set|setting|config|c)
    # 8. !(계좌|account|a)
    # 9. !(알림|notice|n)
    print(msg)
    if msg.get('type') == 'hello':
        start = True
        return
    if not start:
        return
    if msg.get('subtype', True) and msg.get('type') == 'message':
        text = msg.get('text')
        if text:
            mat = pat.search(text)
            if not mat:
                mat = pat_c.search(text)
                if mat:
                    message('invalid syntax')
            else:
                asyncio.async(user_log_write(msg['user']+' : '+text+'\n'))
                if mat.group('m'):
                    yield from money(msg['user'], mat)
                elif mat.group('s'):
                    yield from send(msg['user'], mat)
                elif mat.group('d'):
                    yield from remove(msg['user'], mat)
                elif mat.group('e'):
                    yield from eliminate(msg['user'], mat)
                elif mat.group('h'):
                    help_msg()
                elif mat.group('r'):
                    yield from recv(msg['user'], mat)
                elif mat.group('c'):
                    yield from config_msg(msg['user'])
                elif mat.group('a'):
                    yield from set_account(msg['user'], mat)
                elif mat.group('n'):
                    yield from notice(msg['user'], mat)
    elif msg.get('type') == 'user_change':
        yield from change_user_data(msg['user'])
    elif msg.get('type') == 'team_join':
        yield from change_user_data(msg['user'])
    elif msg.get('type') == 'goodbye':
        return 'goodbye'


def revive_main(future):
    start = False
    for task in asyncio.Task.all_tasks():
        task.cancel()
    main_task = asyncio.async(main(slack, False))
    main_task.add_done_callback(revive_main)


@asyncio.coroutine
def main(slack, is_update=True):
    global ws, response, engine
    while True:
        response = slack.rtm.start()
        if response.body['ok']:
            break
    url = response.body['url']
    ws = (yield from websockets.connect(url))
    if is_update:
        yield from update_member()
    try:
        while True:
            message = (yield from ws.recv())
            if message:
                if (yield from msg_parser(message)) == 'goodbye':
                    break
    except KeyboardInterrupt as e:
        raise e
    except Exception:
        logging.exception('error in message processing!')
    finally:
        yield from ws.close()


@asyncio.coroutine
def user_log_write(msg):
    log = (yield from aiofiles.open('db/user.log', 'a'))
    yield from log.write(time.asctime(time.localtime())+' | '+msg)
    yield from log.close()


@asyncio.coroutine
def reduce_log_write(msg):
    log = (yield from aiofiles.open('db/reduce.log', 'a'))
    yield from log.write(time.asctime(time.localtime())+' | '+msg)
    yield from log.close()


def re_pattern_init():
    global pat, pat_c, pat_m, pat_mm, pat_s
    pat = re.compile(r'''^\s*!(
    (?P<m>보내요|주세요|돈|(send|give)me|show\sme\sthe\smoney|smtm|m(oney)?)
    (\s+(?P<content>\w|\w[\w\s]*\w))?
    \s+(?P<m_debt>(<@U[0-9A-Z]{8}>\s+)+[0-9acdefbox+\-*/]+원?(\s+(<@U[0-9A-Z]{8}>\s+)+[0-9acdefbox+\-*/]+원?)*)
    (\s+(?P<m_account>[-\w]+(\s+[-\w]+)*))?
    |
    (?P<s>보냄|s(end)?|remit)
    (?P<s_debt>\s+([0-9]{1,9}|<@U[0-9A-Z]{8}>\s+[0-9acdefbox+\-*/]+원?)(\s+([0-9]{1,9}|<@U[0-9A-Z]{8}>\s+[0-9acdefbox+\-*/]+원?))*)
    |
    (?P<d>삭제|d(el(ete)?)?)
    \s+(?P<d_num>[0-9]{1,9}(\s+[0-9]{1,9})*)
    |
    (?P<e>소거|reduce|e(liminate)?)
    \s+(?P<e_mode>켬|킴|끔|(켜|끄|키)기|o(n|ff))
    |
    (?P<h>도움|h(elp)?)
    |
    (?P<r>받음|확인|r(ec(v|ieve))?|check)
    \s+((?P<r_num>[0-9]{1,9}(\s+[0-9]{1,9})*)|(?P<r_mode>켬|킴|끔|(켜|끄|키)기|o(n|ff)))
    |
    (?P<c>설정|set(ting)?|c(onfig)?)
    |
    (?P<a>계좌|a(ccount)?)
    \s+(?P<account>[-\w]+(\s+[-\w]+)*)
    |
    (?P<n>알림|n(otice)?)
    \s+(?P<n_mode>켬|킴|끔|(켜|끄|키)기|o(n|ff))
    )\s*$''', re.I | re.X)
    pat_c = re.compile(r'''
    !(보내요|주세요|돈|(send|give)me|show\sme\sthe\smoney|smtm|m(oney)?)
    |
    !(보냄|s(end)?|remit)
    |
    !(삭제|d(el(ete)?)?)
    \s+(?P<d_num>[0-9]{1,9}(\s+[0-9]{1,9})*)
    |
    !(소거|reduce|e(liminate)?)
    |
    !(도움|h(elp)?)
    |
    !(받음|확인|r(ec(v|ieve))?|check)
    |
    !(설정|set(ting)?|c(onfig)?)
    |
    !(계좌|a(ccount)?)
    |
    !(알림|n(otice)?)
    ''', re.I | re.X)
    pat_m = re.compile(
        r'(?P<members>(<@U[0-9A-Z]{8}>\s+)+)(?P<price>[0-9acdefbox+\-*/]+)원?', re.I)
    pat_mm = re.compile(r'U[0-9A-Z]{8}', re.I)
    pat_s = re.compile(
        r'<@(?P<member>U[0-9A-Z]{8})>\s+(?P<price>[0-9acdefbox+\-*/]+)원?|(?<!<@U[0-9A-Z]{8}>)\s+(?P<num>[0-9]{1,9})', re.I)


@asyncio.coroutine
def loop_executer(loop):
    task = asyncio.async(main(slack))
    while loop.is_running():
        yield from asyncio.wait_for(task, None)
        start = False
        task = asyncio.async(main(slack, False))


if __name__ == '__main__':
    global start, slack
    start = False
    token = config.TOKEN
    re_pattern_init()
    engine = create_engine('sqlite:///db/money.db')
    try:
        with Session() as session:
            slack = Slacker(token, session=session)
            loop = asyncio.get_event_loop()
            task = asyncio.async(loop_executer(loop))
            loop.run_until_complete(task)
    except KeyboardInterrupt:
        pass
    except Exception as e:
        logging.exception('The cake is a lie!')
    finally:
        loop.close()
        if ws:
            ws.close()
