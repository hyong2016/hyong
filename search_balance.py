#coding=UTF-8
import MySQLdb, db_1255577
import logging, traceback
from datetime import datetime
import simplejson as json
import config,db_util

logger = logging.getLogger(__name__)


#org = do_query_balance(uid)
#row = json.loads(org)
#result = row['result']

def can_call(uid):
    try:
        sql = "SELECT b.balance, a.valid_date, a.field_id, a.enable_flag, a.user_type, a.long_name FROM user a, field_account b WHERE a.field_id=b.field_id AND a.user_name='%s' LIMIT 1" % uid
        row = db_util.query_db(sql)
        if not row:
            logger.info("can not call: 账户不存在:%s" % uid)
            return '{"result":"-2"}'
        res = {}
        res['result'] = '0'
        res['balance']  = "%.3f" %(long(row['balance']) / 1000000.0)
        res['validate'] = row['valid_date'].strftime('%Y-%m-%d')
        res['field_id'] = row['field_id']
        itype = int(row['user_type'])
        iname = str(row['long_name'])
        if res['validate'] < datetime.now().strftime('%Y-%m-%d'):
            sql = "SELECT field_type FROM v_field WHERE field_id='%s' LIMIT 1" %row['field_id']
            tmp = db_util.query_db(sql)
            if tmp and tmp['field_type'] == '0':
                sql = "UPDATE v_field SET field_type='1' WHERE field_id='%s' LIMIT 1" %row['field_id']
                ret = db_util.modify_db(sql)
                if not ret:
                    logger.info("修改field_type失败:%s" %iname)
                    return '{"result":"-8", "validate":"%s", "balance":"%s"}' % (res['validate'], res['balance'])
                sql = "UPDATE user SET valid_date=DATE_ADD(NOW(),INTERVAL 24 MONTH) WHERE field_id='%s' LIMIT 1" %row['field_id']
                ret = db_util.modify_db(sql)
                if not ret:
                    logger.info("修改valid_date失败:%s" %iname)
                    return '{"result":"-8", "validate":"%s", "balance":"%s"}' % (res['validate'], res['balance'])
            else:
                logger.info("can not call: 账户过有效期:%s" % uid)
                return '{"result":"-8", "validate":"%s", "balance":"%s"}' % (res['validate'], res['balance'])
        if row['enable_flag'] != '1':
            logger.info("can not call: 账户已被冻结:%s" % uid)
            return '{"result":"-10", "validate":"%s", "balance":"%s"}' % (res['validate'], res['balance'])
        sql = "SELECT product, eff_time, exp_time FROM time_acct WHERE user_name = '%s' AND NOW() <= exp_time ORDER BY exp_time DESC LIMIT 1" %uid
        row = db_util.query_db(sql)
        if not row:
            if (float(res['balance'])*1000000 < config.MIN_BALANCE):
                logger.info("can not call: 余额不足:%s" % uid)
                return '{"result":"-9", "validate":"%s", "balance":"%s"}' % (res['validate'], res['balance'])
            res['package'] = ''
        else:
            if itype == 0:
                fen = 0
                sql = "SELECT balance FROM phone WHERE phone ='%s' LIMIT 1" %iname
                tmp = db_1255577.query_db(sql)
                if tmp and tmp['balance']:
                    fen = int(tmp['balance'])
                    sql = "UPDATE time_acct SET month_left_time = %d WHERE user_name = '%s' AND NOW() <= exp_time ORDER BY exp_time DESC LIMIT 1" %(fen, uid)
                    db_util.modify_db(sql)
            else:
                sql = "SELECT SUM(month_left_time) AS month_left_time FROM time_acct WHERE user_name = '%s' AND NOW() <= exp_time" %uid
                tmp = db_util.query_db(sql)
                fen = tmp['month_left_time']
            if ((fen <= 0) and (float(res['balance'])*1000000 < config.MIN_BALANCE)):
                logger.info("can not call: 余额不足并且包月分钟数也已用完:%s" % uid)
                return '{"result":"-9", "validate":"%s", "balance":"%s"}' % (res['validate'], res['balance'])
            row['month_left_time'] = str(fen)
            row['eff_time'] = row['eff_time'].strftime('%Y-%m-%d')
            row['exp_time'] = row['exp_time'].strftime('%Y-%m-%d')
            res['package'] = [row]
        res = json.dumps(res)
        res = eval("u'%s'" % res)
        return res.encode('utf-8')
    except:
        logger.info("can_call异常%s" % traceback.format_exc())
        return '{"result":"-11"}'
