#coding=UTF-8
import urllib2, logging, md5
from xml.dom import minidom
from datetime import datetime
import traceback, calendar
import config, db_util

logger = logging.getLogger(__name__)

def add_money(uid, actual, virtual, order_id, paytype, web):
    logger.info("charge: uid: %s, actual: %s, virtual: %s, order id: %s" % (uid, actual, virtual, order_id))
    money = int(virtual)
    if str(paytype) == 'card':
        base = int(actual)/3
    else:
        base = int(actual)

    try:
        #取出终端用户的余额等信息
        sql = "SELECT u.long_name, u.field_id, u.valid_date, NOW() AS now_date, f.balance, f.account_type, v.agent_id, v.field_type FROM v_field AS v, user AS u LEFT JOIN field_account AS f ON u.field_id=f.field_id WHERE u.field_id=v.field_id AND u.user_name='%s'" % uid
        user = db_util.query_db(sql)
        if not user:
            logger.info("查询用户余额等信息失败:UID=%s" %uid)
            return '{"result":"-2"}'
        chargee_name = str(user['long_name'])
        chargee_field_id = int(user['field_id'])
        chargee_money_before = int(user['balance'])

        if int(user['account_type']) == 0:
            logger.info("1255577业务充分钟数=>充包月: UID=%s" %uid)
            if actual == '10000':
                packageid = 12
            elif actual == '5000':
                packageid = 18
            elif actual == '3000':
                packageid = 1
            else:
                return '{"result":"-1"}'
            result = package(uid, packageid, 1, order_id, web, 0)
            return str(result)

        sql = "SELECT 1 FROM charge_log WHERE order_id = '%s'" % order_id
        if db_util.query_db(sql):
            logger.info("订单号已存在:UID=%s, orderId=%s" %(uid, order_id))
            return '{"result":"-3"}'

        #修改终端用户帐户的有效期
        if int(user['field_type']) == 1:
            if base < 10000:
                month = 2 * 12#base/500
            else:
                month = 5 * 12
            if user['valid_date'] < user['now_date']:
                sql = "UPDATE user SET valid_date=DATE_ADD(NOW(),INTERVAL %d MONTH) WHERE user_name='%s' LIMIT 1" % (month, uid)
            else:
                sql = "UPDATE user SET valid_date=DATE_ADD(valid_date,INTERVAL %d MONTH) WHERE user_name='%s' LIMIT 1" % (month, uid)
            ret = db_util.modify_db(sql)
            if not ret and month:
                logger.info("修改用户有效期失败:%s" %chargee_name)
                return '{"result":"-1"}'

        #修改终端用户的余额
        balance = money * 10000 #操作金额,数据库里的格式
        sql = "UPDATE field_account SET balance=balance+%d WHERE field_id='%s' LIMIT 1" %(balance, chargee_field_id)
        ret = db_util.modify_db(sql)
        if not ret:
            logger.info("修改用户余额失败:%s" %chargee_name)
            return '{"result":"-1"}'

        if web != '1':
            #充值日志
            sql = "INSERT INTO charge_log SET money=%d, given=%d, time=NOW(), chargee_id=%d, " %(base*10000, balance-base*10000, chargee_field_id)
            sql = sql+"chargee_money_before=%d, chargee_money_after=%d, agent_id='%s', " %(chargee_money_before, chargee_money_before+balance, user['agent_id'])
            sql = sql+"chargee_name='%s', order_id='%s', operate_type=%%s" %(chargee_name, str(order_id))
            db_util.insert_db(sql, "充值")
            logger.info("charege for account: balance = %d long_name = %s" %(balance, chargee_name))

        if int(user['agent_id']) == 1 or str(paytype) == 'card' or str(paytype) == 'none':
            logger.info("自己的终端用户或不返点")
            return '{"result":"0"}'

        #代理商返点,一直往上找到顶级代理
        info = []
        running = True
        while running:
            list = {}
            #下级
            sql = "SELECT a.good_type, a.good_dot, a.agent_name, a.link_man, a.agent_id FROM agent a, v_field v WHERE v.agent_id=a.agent_id AND v.field_name='%s'" %uid
            agent2 = db_util.query_db(sql)
            #上级
            sql = "SELECT a.agent_name, a.link_man, a.agent_id FROM agent a, v_field v WHERE v.agent_id=a.agent_id AND v.field_name='%s'" %agent2['agent_name']
            agent1 = db_util.query_db(sql)
            if agent2 and agent1:
                if (int(agent1['agent_id']) == 0):
                    running = False
                    break
                #取出上级的余额
                sql = "SELECT f.balance, v.field_id FROM field_account f, v_field v WHERE v.field_id=f.field_id AND field_name='%s'" %agent1['agent_name']
                bf1 = db_util.query_db(sql)
                #取出下级的余额
                sql = "SELECT f.balance, v.field_id FROM field_account f, v_field v WHERE v.field_id=f.field_id AND field_name='%s'" %agent2['agent_name']
                bf2 = db_util.query_db(sql)
                if bf1 and bf2:
                    list['chargee_money_before'] = int(bf2['balance'])
                    list['charger_money_before'] = int(bf1['balance'])
                    list['chargee_field_id'] = int(bf2['field_id'])
                    list['charger_field_id'] = int(bf1['field_id'])
                else:
                    logger.info("查询代理商余额失败:agent1=%s,agent2=%s" %(agent1['link_man'], agent2['link_man']))
                    return '{"result":"-1"}'
                list['chargee_name'] = str(agent2['link_man'])
                list['charger_name'] = str(agent1['link_man'])
                list['chargee_agent_id'] = int(agent2['agent_id'])
                list['charger_agent_id'] = int(agent1['agent_id'])
            else:
                logger.info("查找上级代理商失败:UID=%s" %uid)
                return '{"result":"-1"}'

            uid = str(agent2['agent_name'])
            if int(agent2['good_type']) == 1:
                sql = "SELECT count(*) AS nums FROM charge_log WHERE chargee_id='%s'" %chargee_field_id
                res = db_util.query_db(sql)
                if res and res['nums'] != 1:
                    continue
                elif not res:
                    logger.info("查询用户充值记录失败:name=%s" %chargee_name)
                    return '{"result":"-4"}'
            #操作金额,数据库里的格式
            list['balance'] = base * int(agent2['good_dot']) / 1000
            info.insert(0,list)

        #从顶级代理开始逐级返点
        for list in info:
            if (list['charger_money_before'] < list['balance']):
                logger.info("返点失败：%s余额不足" %list['charger_name'])
                break
            else:
                #上级代理扣款
                sql = "UPDATE field_account SET balance=balance-%d WHERE field_id='%s' AND balance >= %d LIMIT 1" %(list['balance'], list['charger_field_id'], list['balance'])
                ret = db_util.modify_db(sql)
                if not ret:
                    logger.info("上级代理扣款失败:%s" %list['chargee_name'])
                    return '{"result":"-1"}'
                else:
                    #下级代理加钱
                    sql = "UPDATE field_account SET balance=balance+%d WHERE field_id='%s' LIMIT 1" %(list['balance'], list['chargee_field_id'])
                    ret = db_util.modify_db(sql)
                    if not ret:
                        logger.info("下级代理返点失败:%s" %list['chargee_name'])
                        return '{"result":"-1"}'
            #充值日志
            sql = "INSERT INTO charge_log SET money=%d, given=%d, time=NOW(), " %(base*10000, list['balance'])
            sql = sql+"chargee_money_before=%d, chargee_money_after=%d, " %(list['chargee_money_before'], list['chargee_money_before']+list['balance'])
            sql = sql+"charger_money_before=%d, charger_money_after=%d, " %(list['charger_money_before'], list['charger_money_before']-list['balance'])
            sql = sql+"chargee_level=%d, chargee_id=%d, charger_level=%d, charger_id=%d, " %(list['chargee_agent_id'], list['chargee_field_id'], list['charger_agent_id'], list['charger_field_id'])
            sql = sql+"chargee_name='%s', charger_name='%s', order_id='%s', operate_type=%%s" %(list['chargee_name'], list['charger_name'], str(order_id))
            db_util.insert_db(sql, "返点")
        return '{"result":"0"}'
    except:
        logger.info("充值时异常：%s" % traceback.format_exc())
        conn.rollback()
        return '{"result":"-1"}'

#paytype：只有在WEB后台划帐时才带有过来，其它渠道充包月没有此参数
def package(uid, packageid, no, orderno, web, paytype, convert=1):
    logger.info("收到包月充值请求: uid: %s, packageid: %s, num: %s, orderno: %s" % (uid, packageid, no, orderno))
    productid = int(packageid)
    cnt = int(no)#购买包月套餐的个数

    #取出终端用户的余额等信息
    sql = "SELECT u.long_name, u.field_id, u.valid_date, u.user_type, NOW() AS now_date, f.balance, f.account_type, v.agent_id, v.field_type FROM v_field AS v, user AS u LEFT JOIN field_account AS f ON u.field_id=f.field_id WHERE u.field_id=v.field_id AND u.user_name='%s'" % uid
    user = db_util.query_db(sql)
    if not user:
        logger.info("查询用户余额等信息失败:UID=%s" %uid)
        return '{"result":"-2"}'
    packs_type = '1'    #1：计时账户、代理商正常返点
    chargee_name = str(user['long_name'])
    chargee_field_id = int(user['field_id'])
    chargee_money_before = int(user['balance'])

    if convert == 1:
        if int(user['account_type'] == 0):      #1255577业务充包月
            if productid == 12:#100元包30天
                base = 10000
                days_per_month = 30
                days = days_per_month * cnt
                month_left_time = 30000 * cnt
            elif productid == 14:#10元包2天
                base = 1000
                days_per_month = 2
                days = days_per_month * cnt
                month_left_time = 1000 * cnt
            else:
                return '{"result":"-1"}'
        else:                                   #普通回拨业务充包月
            if productid == 1:#30元包月[回拨]
                base = 3000
                days_per_month = 30
                days = days_per_month * cnt
                month_left_time = 500 * cnt
            elif productid == 18:#50元包月[回拨]
                base = 5000
                days_per_month = 30
                days = days_per_month * cnt
                month_left_time = 1000 * cnt
            elif productid == 12:#100元包月[回拨]
                base = 10000
                days_per_month = 30
                days = days_per_month * cnt
                month_left_time = 2500 * cnt
            elif productid == 13:#300元包月[回拨]
                base = 30000
                days_per_month = 30
                days = days_per_month * cnt
                month_left_time = 100000 * cnt
            elif productid == 14:#无限打开通半年+包30天
                mday = 180
                base = 15000
                days_per_month = 30
                days = days_per_month * cnt
                month_left_time = 30000 * cnt
            elif productid == 15:#无限打开通半年+包99天
                mday = 180
                base = 22000
                days_per_month = 99
                days = days_per_month * cnt
                month_left_time = 50000 * cnt
            elif productid == 16:#无限打开通一年+包30天
                mday = 360
                base = 23000
                days_per_month = 30
                days = days_per_month * cnt
                month_left_time = 30000 * cnt
            elif productid == 17:#无限打开通一年+包99天
                mday = 360
                base = 30000
                days_per_month = 99
                days = days_per_month * cnt
                month_left_time = 50000 * cnt
            else:
                return '{"result":"-1"}'

        if int(user['account_type']) == 1:
            sql = "SELECT order_id FROM card WHERE order_id='%s' AND is_actived=1" %orderno
            car = db_util.query_db(sql)
            if car:
                logger.info("自发卡充包月=>充账户余额: UID=%s" %uid)
                result = add_money(uid, base, base, orderno, 'card', web)
                return str(result)

        sql = "SELECT 1 FROM charge_log WHERE order_id = '%s'" % orderno
        if db_util.query_db(sql):
            logger.info("订单号已存在:UID=%s, orderId=%s" %(uid, orderno))
            return '{"result":"-3"}'

        if int(user['field_type']) == 0:
            if ((productid == 1) or (productid == 18)):#30元包月=>无限打
                days_per_month = 30
                days = days_per_month * cnt
                month_left_time = 30000 * cnt
            elif productid == 12:#100元包月=>无限打
                days_per_month = 99
                days = days_per_month * cnt
                month_left_time = 50000 * cnt
            packs_type = '2'    #2：充值包月无限打不修改帐户有效期并且代理商不返点

        if ((productid == 14) or (productid == 15) or (productid == 16) or (productid == 17)):
            sql = "UPDATE v_field SET field_type='0' WHERE field_id='%s' LIMIT 1" %chargee_field_id
            ret = db_util.modify_db(sql)
            if not ret:
                logger.info("修改field_type失败:%s" %chargee_name)
                #return '{"result":"-1"}'
            if ((productid == 14) or (productid == 16)):
                productid = 1
            else:
                productid = 12
            packs_type = '0'    #0：开通包月无限打修改帐户有效期至半年或一年并且代理商固定返40元人民币
    else:        #1255577业务充分钟数=>充包月
        iyear  = int(datetime.now().strftime('%Y'))
        imonth = int(datetime.now().strftime('%m'))
        iday   = int(datetime.now().strftime('%d'))
        days   = calendar.monthrange(iyear, imonth)[1] - iday
        if productid == 1:#30元包300分钟
            base = 3000
            days_per_month = days + 30
            days = days_per_month * cnt
            month_left_time = 300 * cnt
        elif productid == 18:#50元包600分钟
            base = 5000
            days_per_month = days + 30
            days = days_per_month * cnt
            month_left_time = 600 * cnt
        elif productid == 12:#100元包1600分钟
            base = 10000
            days_per_month = days + 60
            days = days_per_month * cnt
            month_left_time = 1600 * cnt
        else:
            return '{"result":"-1"}'

    try:
        #修改终端用户帐户的有效期
        if packs_type == '0':
            sql = "UPDATE user SET valid_date=DATE_ADD(NOW(),INTERVAL %d DAY) WHERE user_name='%s' LIMIT 1" % (mday, uid)
            ret = db_util.modify_db(sql)
            if not ret:
                logger.info("修改用户有效期失败:%s" %chargee_name)
                return '{"result":"-1"}'
        elif packs_type == '1':
            month = 24#base/500
            if user['valid_date'] < user['now_date']:
                sql = "UPDATE user SET valid_date=DATE_ADD(NOW(),INTERVAL %d MONTH) WHERE user_name='%s' LIMIT 1" % (month, uid)
            else:
                sql = "UPDATE user SET valid_date=DATE_ADD(valid_date,INTERVAL %d MONTH) WHERE user_name='%s' LIMIT 1" % (month, uid)
            ret = db_util.modify_db(sql)
            if not ret and month:
                logger.info("修改用户有效期失败:%s" %chargee_name)
                return '{"result":"-1"}'

        #添加包月
        sql = "INSERT INTO time_acct SET user_name='%s', product='%s', prefix='0086', " %(uid, productid)
        sql = sql+"month_left_time=%d, day_total_time=%d, day_left_time=%d, " %(month_left_time, month_left_time/days, month_left_time/days)
        sql = sql+"last_call_time=NOW(), eff_time=NOW(), exp_time=DATE_ADD(NOW(),INTERVAL %d DAY)" %days
        db_util.modify_db(sql)

        if web != '1':
            #充值日志
            sql = "INSERT INTO charge_log SET money=%d, given=%d, time=NOW(), chargee_id=%d, " %(base*10000, 0, chargee_field_id)
            sql = sql+"chargee_money_before=%d, chargee_money_after=%d, agent_id='%s', " %(chargee_money_before, chargee_money_before, user['agent_id'])
            sql = sql+"chargee_name='%s', order_id='%s', operate_type=%%s" %(chargee_name, str(orderno))
            db_util.insert_db(sql, "充值")
            logger.info("package for account: balance = %d long_name = %s" %(base, chargee_name))

        if int(user['agent_id']) == 1 or str(paytype) == 'none' or int(packs_type) == 2:
            logger.info("自己的终端用户或不返点")
            return '{"result":"0"}'
        elif int(packs_type) == 0:
            logger.info("无限打开通代理暂未现实返点")
            return '{"result":"0"}'

        #代理商返点,一直往上找到顶级代理
        info = []
        running = True
        while running:
            list = {}
            #下级
            sql = "SELECT a.good_type, a.good_dot, a.agent_name, a.link_man, a.agent_id FROM agent a, v_field v WHERE v.agent_id=a.agent_id AND v.field_name='%s'" %uid
            agent2 = db_util.query_db(sql)
            #上级
            sql = "SELECT a.agent_name, a.link_man, a.agent_id FROM agent a, v_field v WHERE v.agent_id=a.agent_id AND v.field_name='%s'" %agent2['agent_name']
            agent1 = db_util.query_db(sql)
            if agent2 and agent1:
                if (int(agent1['agent_id']) == 0):
                    running = False
                    break
                #取出上级的余额
                sql = "SELECT f.balance, v.field_id FROM field_account f, v_field v WHERE v.field_id=f.field_id AND field_name='%s'" %agent1['agent_name']
                bf1 = db_util.query_db(sql)
                #取出下级的余额
                sql = "SELECT f.balance, v.field_id FROM field_account f, v_field v WHERE v.field_id=f.field_id AND field_name='%s'" %agent2['agent_name']
                bf2 = db_util.query_db(sql)
                if bf1 and bf2:
                    list['chargee_money_before'] = int(bf2['balance'])
                    list['charger_money_before'] = int(bf1['balance'])
                    list['chargee_field_id'] = int(bf2['field_id'])
                    list['charger_field_id'] = int(bf1['field_id'])
                else:
                    logger.info("查询代理商余额失败:agent1=%s,agent2=%s" %(agent1['link_man'], agent2['link_man']))
                    return '{"result":"-1"}'
                list['chargee_name'] = str(agent2['link_man'])
                list['charger_name'] = str(agent1['link_man'])
                list['chargee_agent_id'] = int(agent2['agent_id'])
                list['charger_agent_id'] = int(agent1['agent_id'])
            else:
                logger.info("查找上级代理商失败:UID=%s" %uid)
                return '{"result":"-1"}'

            uid = str(agent2['agent_name'])
            if int(agent2['good_type']) == 1:
                sql = "SELECT count(*) AS nums FROM charge_log WHERE chargee_id='%s'" %chargee_field_id
                res = db_util.query_db(sql)
                if res and res['nums'] != 1:
                    continue
                elif not res:
                    logger.info("查询用户充值记录失败:name=%s" %chargee_name)
                    return '{"result":"-4"}'
            #操作金额,数据库里的格式
            list['balance'] = base * int(agent2['good_dot']) / 1000
            info.insert(0,list)

        #从顶级代理开始逐级返点
        for list in info:
            if (list['charger_money_before'] < list['balance']):
                logger.info("返点失败：%s余额不足" %list['charger_name'])
                break
            else:
                #上级代理扣款
                sql = "UPDATE field_account SET balance=balance-%d WHERE field_id='%s' AND balance >= %d LIMIT 1" %(list['balance'], list['charger_field_id'], list['balance'])
                ret = db_util.modify_db(sql)
                if not ret:
                    logger.info("上级代理扣款失败:%s" %list['chargee_name'])
                    return '{"result":"-1"}'
                else:
                    #下级代理加钱
                    sql = "UPDATE field_account SET balance=balance+%d WHERE field_id='%s' LIMIT 1" %(list['balance'], list['chargee_field_id'])
                    ret = db_util.modify_db(sql)
                    if not ret:
                        logger.info("下级代理返点失败:%s" %list['chargee_name'])
                        return '{"result":"-1"}'
            #充值日志
            sql = "INSERT INTO charge_log SET money=%d, given=%d, time=NOW(), " %(base*10000, list['balance'])
            sql = sql+"chargee_money_before=%d, chargee_money_after=%d, " %(list['chargee_money_before'], list['chargee_money_before']+list['balance'])
            sql = sql+"charger_money_before=%d, charger_money_after=%d, " %(list['charger_money_before'], list['charger_money_before']-list['balance'])
            sql = sql+"chargee_level=%d, chargee_id=%d, charger_level=%d, charger_id=%d, " %(list['chargee_agent_id'], list['chargee_field_id'], list['charger_agent_id'], list['charger_field_id'])
            sql = sql+"chargee_name='%s', charger_name='%s', order_id='%s', operate_type=%%s" %(list['chargee_name'], list['charger_name'], str(orderno))
            db_util.insert_db(sql, "返点")

        if int(user['user_type']) == 0:
            url = "http://112.124.58.27/index.php/iface/addcharge/{%s}/{%s}/kzcz13544225433/52c69e3a57331081823331c4e69d3f2e" %(chargee_name, base/100)
            f = urllib2.urlopen(url)
            xmlstr = str(f.read())
            #xmlstr = xmlstr.replace('\r', '')
            #xmlstr = xmlstr.replace('\n', '')
            #xmlstr = xmlstr.replace('\t', '')
            #doc    = minidom.parseString(xmlstr)
            #root   = doc.documentElement
            #nodes  = root.getElementsByTagName('error')
            #value  = nodes[0].childNodes[0].nodeValue
            #result = value.encode('utf-8','ignore')
            #return '{"result":"%s"}' %result
        return '{"result":"0"}'

    except:
        logger.info("充值时异常：%s" % traceback.format_exc())
        conn.rollback()
        return '{"result":"-1"}'

def pay(uid, paytype, goodstype, money, cardno, cardpwd, pv, v):
    logger.info("收到充值请求:uid:%s,金额:%s,卡号:%s,密码:%s,版本:%s,版本号:%s" %(uid, money, cardno, cardpwd, pv, v))
    src = ''
    if (pv == 'java'):
        src = '20'
    elif (pv == 'S602'):
        src = '10'
    elif ((pv == 'S60v3') or (pv == 'S60v5')):
        src = '11'
    ordersn = datetime.now().strftime('%Y%m%d%H%M%S') + uid
    sign = md5.new('src=%s&ordersn=%s&uid=%s&key=%s' % (src, ordersn, uid, config.charge_KEY)).hexdigest()
    url = config.Charge_ADDR % (src, ordersn, uid, paytype, goodstype, money, cardno, cardpwd, sign)
    f = urllib2.urlopen(url)
    res = f.read()
    logger.info("调充值接口:%s,返回结果:%s" %(url,res))
    return res

if __name__=='__main__':
    print add_money('10006',5000,'123456789')
