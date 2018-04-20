#coding=UTF-8
import logging
import db_util,tool

logger = logging.getLogger(__name__)

def get_password(phone):
    sql = "select reg_pwd from user where long_name='%s' limit 1" %phone
    row = db_util.query_db(sql)
    if not row:
        return None
    return row['reg_pwd']

def find_password(phone):
    if not tool.number_deal(phone):
        return '{"result":"-3"}'
    if (phone[0] == '0' and phone[1] == '1'):
        phone = phone[1:]
    pwd = get_password(phone)
    if not pwd :
        return '{"result":"-2"}'
    return '{"result":"0","pwd":"%s"}' %(pwd)
