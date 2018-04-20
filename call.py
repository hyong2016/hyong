#coding=UTF-8
import time, urllib2, random
import simplejson as json
import logging,md5,traceback
import tool,config,db_util,search_balance

logger = logging.getLogger(__name__)
sn = 0


def get_cb_url(caller,mydict):
    key_list = mydict.keys()
    key_list.sort()
    for i in key_list:
        if caller[:3] == i:
            return mydict[i]+config.CB_parameter
    for i in key_list:
        if caller[:2] == i:
            return mydict[i]+config.CB_parameter
    for i in key_list:
        if caller[:1] == i:
            return mydict[i]+config.CB_parameter
    return None

#号码加前缀
def phone_add(prefix,number):
    add_number = prefix + number
    return add_number

def is_free(field_id,balance,package=''):
    no_fee = False
    now = int(time.strftime('%H',time.localtime()))
    if now >= 2 and now < 6:
        no_fee = True
    else:
        stg = time.strftime('%H:%M:00',time.localtime())
        if ((stg>='06:00:00' and stg<'11:30:00') or (stg>='14:00:00' and stg<'17:30:00')):
            beg = time.strftime('%Y-%m-%d 00:00:00',time.localtime())
            end = time.strftime('%Y-%m-%d 17:30:00',time.localtime())
            sql = "SELECT SUM(money) AS money FROM charge_log WHERE chargee_id='%s' AND (time>='%s' AND time<'%s') AND (operate_type='充值' OR operate_type='划账')" %(field_id, beg, end)
            cur = db_util.query_db(sql)  #当天累计充值
            if (cur and cur['money'] and (cur['money'] >= 50000000) and (float(balance)*1000000 > float(cur['money']))):  #并且没有扣款
                no_fee = True
            else:
                beg = time.strftime('%Y-%m-%d 00:00:00',time.localtime(time.time()-86400))
                end = time.strftime('%Y-%m-%d 17:30:00',time.localtime())
                sql = "SELECT SUM(money) AS money FROM charge_log WHERE chargee_id='%s' AND (time>='%s' AND time<'%s') AND (operate_type='充值' OR operate_type='划账')" %(field_id, beg, end)
                two = db_util.query_db(sql)  #两天累计充值
                if (two and two['money'] and (two['money'] >= 100000000) and (float(balance)*1000000 > float(two['money']))):  #并且没有扣款
                    no_fee = True
                else:
                    day = int(time.strftime('%w',time.localtime()))
                    if (day==0):
                        ydate = time.strftime('%Y-01-01 00:00:00',time.localtime())
                        sql = "SELECT SUM(money) AS money FROM charge_log WHERE chargee_id='%s' AND (time>='%s' AND time<NOW()) AND (operate_type='充值' OR operate_type='划账')" %(field_id, ydate)
                        hos = db_util.query_db(sql)
                        sql = "SELECT SUM(money) AS money FROM charge_log WHERE chargee_id='%s' AND (time>='%s' AND time<NOW()) AND (operate_type='扣款')" %(field_id, ydate)
                        drp = db_util.query_db(sql)
                        if drp and hos and drp['money'] > 0 and hos['money'] > 0:
                            hos['money'] = hos['money'] - drp['money']
                        pkg = ((package!=None) and (package!='') and (int(package[0]['month_left_time'])>100))
                        if ((hos['money'] >= 10000000) and ((float(balance)*1000000 > 15000000) or (pkg == True))):  #本年度累计充值
                            no_fee = True
                            if ((float(balance)*1000000 <= 0) and (pkg == True)):  #包月用户如果账户余额不足，自动追加余额5分钱
                                sql = "UPDATE field_account SET balance=balance+50000 WHERE field_id='%s' LIMIT 1" %field_id
                                if not (db_util.modify_db(sql)):
                                    logger.info("包月用户余额不足，自动追加5分钱失败: field_id=%s" %field_id)
    return no_fee

def call(uid,pwd,called,echo,ip=''):
    logger.info("收到回拨请求: uid:%s;被叫号码:%s" % (uid,called))
    called  = tool.number_deal(called)
    if not called:
        logger.info("%s呼叫%s被叫号码格式验证失败" % (uid,called))
        return '{"result":"-3"}'
    data = tool.get_status_data(uid)
    if data:
        caller = str(data['long_name'])
        if pwd != data['reg_pwd']:
            logger.info("%s呼叫%s密码验证失败" % (caller,called))
            return '{"result":"-2"}'
        elif '1' != data['enable_flag']:
            logger.info("%s呼叫%s账户已被冻结" % (caller,called))
            return '{"result":"-10"}'

        if called[0] == '0':
            tmp_called = called[1:]
        else:
            tmp_called = called
        if ((caller == tmp_called) or (caller[:2] == '00')):
            logger.info("%s呼叫%s呼叫失败" % (caller,called))
            return '{"result":"-3"}'

        can_call = search_balance.can_call(uid)
        can_call = json.loads(can_call)
        if can_call['result'] != '0':
            return json.dumps(can_call)
        stg = time.strftime('%H:%M:00',time.localtime())
        package = can_call['package']
        if (float(can_call['balance']) <= 6.0) and (package==None or package==''):
            if (stg>='17:30:00' and stg<'23:50:00'):
                cnt = 10
            elif (stg>='00:00:00' and stg<'06:30:00'):
                cnt = 3
            else:
                cnt = 5
        else:
            if (stg>='17:30:00' and stg<'23:50:00'):
                cnt = 25
            elif (stg>='00:00:00' and stg<'06:30:00'):
                cnt = 10
            else:
                cnt = 25

        #A号码不停的呼叫号码
        limited_time = time.strftime('%Y-%m-%d %H:%M:%S',time.localtime(time.time()-3600))
        sql = "SELECT COUNT(*) AS count FROM call_log WHERE field_name='%s' AND to_number='0%s' AND start_time>'%s' AND start_time<=NOW()" %(uid,caller,limited_time)
        res = db_util.query_db(sql)
        if (res and res['count'] >= cnt and caller.find('13172388331') <= -1 and caller.find('15015759543') <= -1 and caller.find('15502010898') <= -1):
            sql = "UPDATE user SET enable_flag=0 WHERE user_name='%s'" %uid
            db_util.modify_db(sql)
            logger.info("%s呼叫过于频繁,冻结账户" %caller)
            return '{"result":"-10"}'

        #B号码不停的被呼叫
        sql = "SELECT COUNT(*) AS count FROM call_log WHERE to_number LIKE '%%%s' AND start_time>'%s' AND start_time<=NOW()" %(called,limited_time)
        ret = db_util.query_db(sql)
        if (ret and ret['count'] >= 8 and called.find('13172388331') <= -1 and called.find('15015759543') <= -1 and called != '075586105758' and called.find('15502010898') <= -1):
            logger.info("%s被过于频繁呼叫" %called)
            return '{"result":"-5"}'

        is_old = True
        if called[:2] != '00':
            sql = "SELECT count(*) AS nums FROM charge_log WHERE chargee_id='%s' AND (operate_type='充值' OR operate_type='划账')" %(can_call['field_id'])
            res = db_util.query_db(sql)
            #新老用户判断，并加以前缀
            if res and res['nums'] == 0 and float(can_call['balance']) <= 6.0:
                if tool.is_mobile(called):
                    called = phone_add(config.prefix+'0',called)
                else:
                    called = phone_add(config.prefix,called)
                is_old = False
                logger.info("新用户呼叫:caller=%s called=%s ip=%s" %(caller, called, ip))
            elif not res:
                logger.info("查询用户充值记录失败:UID=%s" %uid)
            elif is_free(can_call['field_id'],can_call['balance'], package):  #老用户免费活动
                if tool.is_mobile(called):
                    called = phone_add(config.nights+'0',called)
                else:
                    called = phone_add(config.nights,called)
                caller = phone_add(config.nights+'00',caller)
                logger.info("免费呼叫:caller=%s called=%s" %(caller, called))
#        elif 190 == data['agent_id']:
#            logger.info('新疆用户禁止打国外电话')
#            return '{"result":"-10"}'
#
#        #jmdw_2008此代理特殊处理
#        if 1098 == data['agent_id'] and called[:2] == '00':
#            sql = "SELECT count(*) AS nums FROM charge_log WHERE chargee_id='%s' AND (operate_type='充值' OR operate_type='划账')" %(can_call['field_id'])
#            res = db_util.query_db(sql)
#            #新老用户判断，并加以前缀
#            if res and res['nums'] == 0 and float(can_call['balance']) <= 6.0:
#                is_old = False
#                logger.info("新用户呼叫:caller=%s called=%s" %(caller, called))
#            elif not res:
#                logger.info("查询用户充值记录失败:UID=%s" %uid)
#        if 1098 == data['agent_id'] and is_old:
#            if called[:2] != '00':
#                #国内回拨1角,被叫号码加前缀0010以示区别
#                called = '0010' + called
#            elif called[:4] == '0084':
#                called = '0070' + called[4:]
#            elif called[:4] == '0081':
#                called = '0071' + called[4:]
#            elif called[:4] == '0082':
#                called = '0072' + called[4:]

        global sn
        sn = sn + 1
        cburl = get_cb_url(caller,config.CB_ADD)
        if cburl:
            try:
                sign = md5.new('uid=%s&key=%s' % (uid,config.CB_KEY)).hexdigest()
                url = cburl %(str(sn)+str(random.randint(10,99)),uid,caller,called,echo,'2','',sign)
                logger.info(url)
                f = urllib2.urlopen(url)
                result = f.read()
            except:
                logger.info("callback_itf Error: %s" %traceback.format_exc())
                return '{"result":"-11"}'
        else:
            logger.info("%s没有配置回拨分流服务器IP" %caller)
            return '{"result":"-11"}'
        if result == '0':
            return '{"result":"0","balance":"%s"}' %(can_call['balance'])
        elif result == '1' or result == '2':
            logger.info('ERROR,result:%s' %result)
            return '{"result":"-12"}'
        else:
            logger.info('ERROR,result:%s' %result)
            return '{"result":"-13"}'
    else:
        logger.info("%s呼叫%s捆绑手机号查找失败" % (uid,called))
        return '{"result":"-4"}'

