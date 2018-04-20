#! /usr/bin/env python
#coding=utf-8
import MySQLdb
import time, logging
import db_util




"""
cryptDataByPwd ---- 加／解密数据通用API
输入参数:
    data       ---- 加／解密的数据
返回值：
    加／解密后的数据(加／解密前后长度保持不变)
备注：
    对原始数据调用一次为加密，对加密后的数据再调用一次为解密
"""
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

def get_sleep_time(time,mydict):
    key_list = mydict.keys()
    key_list.sort()
    for i in key_list:
        key1 = i.split('-')[0]
        key2 = i.split('-')[1]
        if mydict[i] == 0:
            print 40.0
            return 40.0
        elif time >= int(key1) and time < int(key2):
            print mydict[i]
            return mydict[i]
    i = key_list[-1]
    print "mydict"
    print key_list
    return mydict[i]

# 注意需要把db_opr.py里配置的python用户改成root用户
def create_group_number():
    for i in range(0,200):
        sql = """CREATE TABLE IF NOT EXISTS group_number%03d(row_id int(11) NOT NULL auto_increment,stat_id int(11) NOT NULL,user_name int(11) NOT NULL default '0',int_filename varchar(25) NOT NULL,priority int(3) NOT NULL default '1',send_time datetime NOT NULL,send_status tinyint(3) default '0',link_man varchar(15) default NULL,corp_name varchar(50) default NULL,fax_num varchar(32) NOT NULL,tel_num varchar(32) default NULL,address varchar(80) default NULL,PRIMARY KEY (row_id),UNIQUE KEY fax_num (fax_num)) ENGINE=MyISAM AUTO_INCREMENT=0 DEFAULT CHARSET=utf8""" %i
        dat = db_opr.modify_db(sql)
        print "sql=%s" %sql
        print dat
        if i >=200:
            sql = "INSERT INTO group_table_status() VALUES()"
            dat = db_opr.modify_db(sql)
            print "sql=%s" %sql
            print dat
        time.sleep(0.3)

def domain():
    create_group_number()
    return True

    tmp ="root"
    tmp1=cryptData(tmp)
    tmp2=cryptData(tmp1)
    print "加密前是：%s" %tmp
    print "加密后是：%s" %tmp1
    print "解密后是：%s" %tmp2
    return True

    respond="RESP:123423;thruput:400;"
    respLen = len(respond)
    pos = respond.find('thruput:')
    if pos>-1 and pos<respLen:
        thruput=respond[pos+8:respLen-1]
    else:
        thruput="test"
    print "respond=%s" %respond
    print "thruput=%s" %thruput
    return True

    sql = "select f.balance, u.enable_flag, u.valid_date, NOW() as now_data from field_account f,user u where u.field_id=f.field_id and u.user_name=10001"
    #res1 = db_opr.query_db(sql,1)
    res2  = db_opr.query_db(sql,2)
    res1  = res2[0]

    print res2

    if res1['enable_flag'] > '0':
        print "balance=%d enable_flag=%s valid_date=%s now_data=%s" %(res1['balance'], res1['enable_flag'], res1['valid_date'], res1['now_data'])
    if res2[0]['valid_date'] > res2[0]['now_data']:
        print "balance=%d enable_flag=%s valid_date=%s now_data=%s" %(res2[0]['balance'], res2[0]['enable_flag'], res2[0]['valid_date'], res2[0]['now_data'])


def main():
    domain()

def start():
    domain()

if __name__=='__main__':
    domain()

