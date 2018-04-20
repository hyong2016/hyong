#coding=UTF-8
import logging
import db_util,tool

logger = logging.getLogger(__name__)

def change_phone(old_phone, pwd, new_phone):
    try:
        new_phone = tool.number_deal(new_phone)
        if not new_phone:
            logger.info("手机格式错误:old_phone:%s,new_phone:%s" % (old_phone,new_phone))
            return '{"result":"-3"}'
        if (old_phone[0] == '0' and old_phone[1] == '1'):
            old_phone = old_phone[1:]
        if (new_phone[0] == '0' and new_phone[1] == '1'):
            new_phone = new_phone[1:]
        sql = "SELECT field_id, user_name, reg_pwd FROM user WHERE long_name='%s'" % old_phone
        ret = db_util.query_db(sql)
        if not ret or pwd != ret['reg_pwd']:
            logger.info("手机对应帐号或密码错误:%s" % old_phone)
            return '{"result":"-2"}'
        new_uid = tool.get_bind_uid(new_phone)
        if new_uid:
            logger.info("新手机已存在,old_phone:%s,new_phone:%s" %(old_phone,new_phone))
            return '{"result":"-4"}'
        sql = "SELECT balance FROM field_account WHERE field_id='%s'" %ret['field_id']
        rec = db_util.query_db(sql)
        if not rec:
            logger.info("余额查询失败,old_phone:%s,field_id:%s" %(old_phone,ret['field_id']))
            return '{"result":"-10"}'
        elif rec and long(rec['balance']) < 30000000:
            logger.info("改绑失败:%s余额小于30元,不允许改绑" %old_phone)
            return '{"result":"-5"}'
        sql = "update user set long_name='%s' where long_name='%s'" %(new_phone,old_phone)
        res = db_util.modify_db(sql)
        if not res:
            logger.info("改绑失败:%s" %old_phone)
            return '{"result":"-6"}'
        logger.info("改绑成功:%s-->%s " % (old_phone,new_phone))
        return '{"result":"0","uid":"%s"}' %ret['user_name']
    except :
        logger.info('密码格式错误')
        return '{"result":"-2"}'

def change_pwd(phone, old_pwd, new_pwd):
    try:
        phone = tool.number_deal(phone)
        if not phone:
            logger.info("手机格式错误:phone:%s" % (phone))
            return '{"result":"-3"}'
        if (phone[0] == '0' and phone[1] == '1'):
            phone = phone[1:]
        sql = "SELECT reg_pwd FROM user WHERE long_name='%s'" % phone
        ret = db_util.query_db(sql)
        if not ret or old_pwd != ret['reg_pwd']:
            logger.info("原密码错误:%s" % old_pwd)
            return '{"result":"-2"}'
        sql = "update user set reg_pwd='%s' where long_name='%s'" %(new_pwd,phone)
        res = db_util.modify_db(sql)
        if not res:
            logger.info("密码修改失败,phone:%s,new_pwd:%s" %(phone,new_pwd))
            return '{"result":"-4"}'
        logger.info("密码修改成功:phone=%s,%s-->%s " % (phone,old_pwd,new_pwd))
        return '{"result":"0"}'
    except :
        logger.info('传入参数错误')
        return '{"result":"-10"}'
