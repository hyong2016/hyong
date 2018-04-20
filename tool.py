#coding=UTF-8
import urllib2, md5
import logging, db_wap
import config, db_util

logger = logging.getLogger(__name__)

def cryptData(data):
    if(data==None or len(data)==0):
        return None
    dataLen=len(data)
    if(dataLen>512):
        dataLen=512
    ret = ''
    for i in range(dataLen):
        value = ord(data[i])
        if((value > 0x60) and (value < 0x7B)):
            value = value - 0x20
            value = 0x5A - value + 0x41
        elif((value > 0x40) and (value < 0x5B)):
            value = value + 0x20
            value = 0x7A - value + 0x61
        elif((value >= 0x30) and (value <= 0x34)):
            value = value + 0x05
        elif((value >= 0x35) and (value <= 0x39)):
            value = value - 0x05
        ret += chr(value)
    return ret

def check_phone_pwd(phone,pwd):
    sql = "SELECT user_name, reg_pwd FROM user WHERE long_name='%s'" % phone
    result = db_util.query_db(sql)
    if not result:
        return None
    try:
        if pwd != result['reg_pwd']:
            return -1
    except :
        logger.info('密码格式错误')
        return -1
    return result['user_name']

def get_status_data(uid):
    sql = "SELECT u.reg_pwd, u.enable_flag, u.long_name, v.agent_id FROM user u, v_field v WHERE u.field_id=v.field_id AND u.user_name='%s'" % uid
    result = db_util.query_db(sql)
    return result

def get_bind_uid(phone):
    if not str(phone).isdigit():
        return False
    sql = "SELECT user_name FROM user WHERE long_name='%s'" % phone
    result = db_util.query_db(sql)
    return result

def get_bind_mobile(uid):
    sql = "SELECT long_name FROM user WHERE user_name='%s'" % uid
    result = db_util.query_db(sql)
    return result

def get_bind_uid_and_pwd(phone):
    if not str(phone).isdigit():
        return False
    sql = "SELECT user_name, reg_pwd FROM user WHERE long_name='%s'" % phone
    result = db_util.query_db(sql)
    return result

def number_deal(called):
    called = called.replace(' ', '')
    called = called.replace('-', '')
    if called[:5] in ['12593','12580','17909','17951','17950','10193']:
        called = called[5:]

    if len(called)<5 or called[:3] == '000':
        return False
    number = called

    if called[:4] == '0086':
        if called[4] != '0':
            number = '0' + called[4:]
        else:
            number = called[4:]
    elif called[:3] == '+86' or called[:3] == '086':
        if called[3] != '0':
            number = '0' + called[3:]
        else:
            number = called[3:]
    elif called[:2] == '86':
        if called[2] != '0':
            number = '0' + called[2:]
        else:
            number = called[2:]
    elif called[0] == '+':
        if called[1:3] != '00':
            number = '00' + called[1:]
        else:
            number = called[1:]
    elif called[:3] == '400':
        if len(called) != 10:
            return False
    elif called[:2] == '95':
        if len(called)<5 or len(called)>8:
            return False
    elif called[:2] == '00':
        if len(called)<8 or len(called)>23:
            return False
    elif called[0] == '1':
        if len(called) != 11:
            return False
        number = '0' + called
    elif called[0] == '0' and called[1] != '0':
        if len(called)<6 or len(called)>13:
            return False
    else:
        return False

    pos = number.find('-')
    if pos>-1 and pos<len(number)/2:
        number=number[:pos]+number[pos+1:]
    if number.find('4000755181')>-1:
        return '075586105758'
    if number.isdigit():
        return number
    return False

def check_update(phone_version, version):
    if phone_version == 'java' and version < config.java:
        return config.java_update_add
    if phone_version == 'android' and (version < config.android and version != '1.5'):
        return config.android_update_add
    if phone_version == 'S60V3' and version < config.S60V3:
        return config.S60V3_update_add
    if phone_version == 'S60V5' and version < config.S60V5:
        return config.S60V5_update_add
    if phone_version == 'PC' and version < config.PC:
        return config.PC_update_add
    if phone_version == 'iphone' and version < config.iphone:
        return config.iphone_update_add
    return ''

def is_mobile(number):
    if len(number)==11 and number.startswith('1'):
        return True
    return False

def get_called_by_cornet(uid, cornet):
    sql = "SELECT mobile FROM contacts WHERE uid='%s' AND cornet='%s'" %(uid, cornet)
    res = db_wap.query_db(sql)
    if res and res['mobile']:
        return str(res['mobile'])
    else:
        return None
