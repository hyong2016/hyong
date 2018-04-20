#! /usr/bin/env python
#coding=UTF-8
import logging,traceback,time
import simplejson as json
import config,tool,db_util

logger = logging.getLogger(__name__)

def msglist(sc,pv,v):
    try:
        res = {}
        if (str(pv) == 'android' and str(v) > '1.5'):
            sql = "select id, title from sysmsg where valid_date>now() and now()>start_date and (phone_version='%s' or phone_version='all') and id!='2' order by id desc" %pv
        else:
            sql = "select id, title from sysmsg where valid_date>now() and now()>start_date and (phone_version='%s' or phone_version='all') order by id desc" %pv
        row = db_util.query_db(sql,2)
        ctl  = long(sc) >> 20
        if pv == 'iphone':
            ctrl = 1
        #elif ctl >= 7:
        #   ctrl = 1
        else:
            ctrl = 0

        res['result'] = '0'
        res['service_phone'] = config.service_phone
        if (str(pv) == 'android' and str(v) == '1.5'):
            res['update_addr'] = ''
        else:
            res['update_addr'] = tool.check_update(pv,v)
        if not row:
            res['syslist'] = ''
        else:
            res['syslist'] = row
        res['sysctrl'] = str(ctrl)
        res['systime'] = time.strftime('%H', time.localtime())
        res = json.dumps(res)
        res = eval("u'%s'" % res)
        return res.encode('utf-8')
    except:
        logger.info('%s' %traceback.format_exc())
        return '{"result":"-1"}'

def getmsg(id,pv,v):
    try:
        res = {}
        if id != '':
            sql = "select content from sysmsg where id=%s" %id
        else:
            return '{"result":"-2"}'
        row = db_util.query_db(sql,1)
        if row:
            res['result'] = '0'
            res['content'] = row['content']
        res = json.dumps(res)
        res = eval("u'%s'" % res)
        return res.encode('utf-8')
    except:
        logger.info('%s' %traceback.format_exc())
        return '{"result":"-1"}'

