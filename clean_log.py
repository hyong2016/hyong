#! /usr/bin/env python
#coding=utf-8
import time, os, logging, call_log_proc, config
import MySQLdb, datetime, db_util, db_wap


def domain():
    cnt = 0
    while True:
        time.sleep(900)

        #每间隔30分钟处理一次国际资费：54秒一分钟来扣费
        cnt = cnt + 1
        if (cnt % 2 == 0):
            call_log_proc.bill_by_54s()

        #8:00-24:00、0:00-4:30白天处理"帐户自动解冻"
        stg = time.strftime('%H:%M',time.localtime())
        now = datetime.date.today()
        if ((stg > '08:00') or (stg < '04:30')):
            hr = time.strftime('%H',time.localtime())
            if (int(hr)%2==0):
                dat = now - datetime.timedelta(days = 3)
                sql = "UPDATE user SET enable_flag='1' WHERE enable_flag='0' AND create_time<'%s 00:00:00'" %dat
                ret = db_util.modify_db(sql)

                sql = "update wap_disable set disable_call='1' where disable_call='0'"
                ret &= db_wap.modify_db(sql)
                print "ret = %s   sql = %s" %(ret, sql)
            continue

        #删除多余的垃圾记录
        sql = "delete from field_account where field_id not in (select field_id from user)"
        ret = db_util.modify_db(sql)
        print "ret = %s   sql = %s" %(ret, sql)
        time.sleep(15)
        sql = "delete from v_field where field_id not in (select field_id from user)"
        ret = db_util.modify_db(sql)
        print "ret = %s   sql = %s" %(ret, sql)
        time.sleep(15)

        #4:30-8:00零晨处理"清理话单"
        dat = now - datetime.timedelta(days = 35)
        for h in range(0,24):     #00-23点
            for m in range(0,20): #每间隔3分钟
                sql = "DELETE FROM call_log WHERE start_time<='%s %02d:%02d:59'" %(dat, h, m*3)
                ret = db_util.modify_db(sql)
                print "ret = %s   sql = %s" %(ret, sql)
                time.sleep(5)
        print "%s 的通话记录清理完成" %dat

        #4:30-8:00零晨处理"清理未使用的6元帐户"
        dat = now - datetime.timedelta(days = 66)
        sql = "SELECT field_id FROM v_field WHERE create_time>='%s 00:00:00' LIMIT 1" %dat
        fd1 = db_util.query_db(sql)
        dat = now - datetime.timedelta(days = 65)
        sql = "SELECT field_id FROM v_field WHERE create_time>='%s 00:00:00' LIMIT 1" %dat
        fd2 = db_util.query_db(sql)
        if fd1 and fd2 and fd1['field_id'] and fd2['field_id']:
            print "开始清理 %s 之前注册了未使用的垃圾数据" %dat
            os.system("ps -ef|grep itf.py|grep -v grep|awk '{print$2}'|xargs kill -9")
            sql = "DELETE FROM field_account WHERE balance='%s' AND (field_id>='%s' and field_id<'%s')" %(config.given, fd1['field_id'], fd2['field_id'])
            ret = db_util.modify_db(sql)
            print "ret = %s   sql = %s" %(ret, sql)
            time.sleep(15)
            sql = "DELETE FROM user WHERE field_id NOT IN (SELECT field_id FROM field_account)"
            ret = db_util.modify_db(sql)
            print "ret = %s   sql = %s" %(ret, sql)
            time.sleep(15)
            sql = "DELETE FROM v_field WHERE field_id NOT IN (SELECT field_id FROM field_account)"
            ret = db_util.modify_db(sql)
            print "ret = %s   sql = %s" %(ret, sql)
            os.system("cd /home/itf/; nohup python itf.py > /dev/null 2>&1 &")
        continue

#"""
#delete field_account AS f from field_account AS f, (select chargee_id from charge_log) AS c 
#where f.balance=6000000 and f.field_id>266865 and f.field_id<303540 and f.field_id!=c.chargee_id;
#"""

def main():
    domain()

def start():
    domain()

if __name__=='__main__':
    domain()

