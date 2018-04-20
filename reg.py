#coding=UTF-8
import logging, traceback
import time, md5, random
import datetime
import MySQLdb
import simplejson as json
import config, db_util, tool

logger = logging.getLogger(__name__)
_g_uid = 0

def do_add_user(phone,uid,reg_pwd,agentId,expireDate,itype):
    if (itype == 0):
        atype = 0        #0:分钟数帐户  
    else:
        atype = 1        #1:正常预付费帐户
    try:
        sql = "insert into v_field(field_name, pstn_num, field_desc, agent_id, fee_table_id, enable_flag, create_time, active_time) values ('%s','','',%d,%d,'1',now(),now())" %(uid, agentId, 2)
        ret = db_util.modify_db(sql)
        if not ret:
            logger.info("插入v_field表失败:%s" %phone)
            return False
        sql = "select field_id from v_field where field_name='%s' limit 1" % uid
        row = db_util.query_db(sql)
        if not row:
            logger.warning("v_field中不存在field_id,查询失败, please contact the system admin")
            return False
        fieldId = int(row['field_id'])

        if (itype != 1): #不是正常的终端用户注册均不赠送
            sql = "insert into field_account(field_id,balance,discount,account_type,quota,money_id) values (%d,%d,100,%d,0,1)" % (fieldId, 0, atype)
        else:
            sql = "insert into field_account(field_id,balance,discount,account_type,quota,money_id) values (%d,%d,100,%d,0,1)" % (fieldId, config.given, atype)
        ret = db_util.modify_db(sql)
        if not ret:
            logger.info("插入field_account表失败:%s" %phone)
            return False
        sql = "select field_account_id from field_account where field_id='%s' limit 1" % fieldId
        row = db_util.query_db(sql)
        if not row:
            logger.warning("field_account中不存在field_account_id,查询失败, please contact the system admin")
            return False

        sql = "insert into user(user_type,user_name,reg_pwd,long_name,rep_name,email,phone,address,field_id,enable_flag,user_desc,create_time,active_time,valid_date) values('%s','%s','%s','%s','','','','',%d,'1','',NOW(),NOW(),'%s')" % (itype, uid, reg_pwd, phone, fieldId, expireDate)
        ret = db_util.modify_db(sql)
        if not ret:
            logger.info("插入user表失败:%s" %phone)
            return False
        sql = "select user_id from user where field_id='%s' limit 1" % fieldId
        row = db_util.query_db(sql)
        if not row:
            logger.warning("user中不存在user_id,查询失败, please contact the system admin")
            return False
        sql = "UPDATE agent SET customer=customer+1 WHERE agent_id='%s'" %agentId
        db_util.modify_db(sql)
        return fieldId
    except:
        logger.info("do_add_user proc exception: %s" % traceback.format_exc())
        return False

def get_uid(itype):
    try:
        if itype == 0: #1255577注册绑定，注意：如果注册用户超过5万，此查找将非常慢
            limit = [2,3,4,5]
            imin = [10,100,1000,10000]
            imax = [99,999,9999,99999]
            while True:
                for i in limit:
                    fld = str(i) + str(random.randint(imin[i-2], imax[i-2]))
                    sql = "SELECT field_name FROM v_field WHERE field_name = '%s' LIMIT 1" %fld
                    row = db_util.query_db(sql, 1)
                    if (not row) or (not row['field_name']):
                        break
                return fld

        global _g_uid
        if _g_uid:
            _g_uid = _g_uid + 1
        else:
            sql = "SELECT field_name FROM v_field WHERE field_name >= '600000' ORDER BY field_id DESC LIMIT 1"
            row = db_util.query_db(sql, 1)
            if (not row) or (not row['field_name']):
                _g_uid = 600000
            else:
                _g_uid = int(row['field_name'])+1
        return _g_uid
    except :
        logger.info("get_uid proc exception: %s" % traceback.format_exc())
        return None

def register(phone,password,agentid,itype,ip=''):
    try:
        agent_id = int(agentid)
    except :
        logger.info("注册agentid=%s格式错误,用默认1" %agentid)
        agent_id = 1
    if agent_id != -1:
        sql = "SELECT 1 FROM agent WHERE agent_id=%d LIMIT 1" %agent_id
        row = db_util.query_db(sql, 1)
        if not row:
            agent_id = 1
    if (phone[0] >= '2' and phone[0] <= '9') or (not tool.number_deal(phone)):
        logger.info("注册手机号码格式错误")
        return '{"result":"-3"}'
    if (phone[0] == '0' and phone[1] == '1'):
        phone = phone[1:]
    uid = tool.check_phone_pwd(phone,password)
    if uid == -1:
        logger.info("密码错误:%s" %phone)
        return '{"result":"-2"}'
    elif uid:
        logger.info("登录请求成功:phone=%s pwd=%s uid=%s ip=%s" % (phone,password,str(uid),ip))
        return '{"result":"0","uid":"%s"}' %(uid)
    elif agent_id == -1:
        logger.info("登录失败,账户未注册")
        return '{"result":"-1"}'
    itype = int(itype)   #0:1255577业务之移动直拨  1:终端用户  2:代理商用户
    uid = get_uid(itype)
    if not uid:
        logger.info("取UID异常:%s" %phone)
        return '{"result":"-13"}'

    expireDate = (datetime.datetime.now() + datetime.timedelta(days=30)).strftime('%Y-%m-%d %H:%M:%S')
    if ((agent_id == 236 or agent_id == 544 or agent_id == 534 or agent_id == 332 or agent_id == 764 or agent_id == 546 or agent_id == 215 or agent_id == 121) and (uid%3 == 0)):
        logger.info("agent_id:%s-->1" %agent_id)
        agent_id = 1
    res = do_add_user(phone,uid,password,agent_id,expireDate,itype)
    if not res:
        #logger.info("添加用户信息失败:%s" %phone)
        return '{"result":"-1"}'
    logger.info("注册请求成功:phone=%s pwd=%s uid=%s ip=%s" % (phone,password,uid,ip))
    return '{"result":"0","uid":"%s","field_id":"%s"}' %(uid, res)
