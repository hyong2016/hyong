#! /usr/bin/env python
#coding=UTF-8
import os.path, cherrypy, md5
import logging, traceback
import config, reg, tool
import sysmsg, search_balance, find_password
import change, call, charge
import simplejson as json
import time, db_util, urllib2
from xml.dom import minidom

logger = logging.getLogger(__name__)
class mobile_server:
    @cherrypy.expose
    def reg(self, phone, pwd, agent_id, sign, pv, v, itype=1):
        far_ip = cherrypy.request.remote.ip
        if 'User-Agent' in cherrypy.request.headers.keys():
            ieinfo = cherrypy.request.headers['User-Agent']
            if ieinfo.find('Mozilla') > -1:
                logger.info('受到恶意攻击!!!IP=%s, User-Agent=%s' % (far_ip, ieinfo))
                return 'hehe'
        if (not phone) or (not pwd) or (not sign) or (not pv) or (not v):
            logger.info('传入参数错误!')
            return '{"result":"-3"}'
        if ((pwd.isalnum() == False) or (phone.isdigit() == False)):
            logger.info('传入参数错误!')
            return '{"result":"-2"}'
        if sign != md5.new(phone + config.key).hexdigest():
            return '{"result":"-6"}'
        try:
            result = reg.register(phone, pwd, agent_id, itype, far_ip)
            return str(result)
        except:
            logger.info("reg proc exception: %s " % traceback.format_exc())
            return '{"result":"-10"}'
    @cherrypy.expose
    def call(self, uid, pwd, called, sign, pv, v, echo='1'):
        far_ip = cherrypy.request.remote.ip
        if 'User-Agent' in cherrypy.request.headers.keys():
            ieinfo = cherrypy.request.headers['User-Agent']
            if ieinfo.find('Mozilla') > -1:
                logger.info('受到恶意攻击!!!IP=%s, User-Agent=%s' % (far_ip, ieinfo))
                return 'hehe'
        if (not uid) or (not called) or (not pwd) or (not sign) or (not pv) or (not v):
            logger.info('传入参数错误!')
            return '{"result":"-10"}'
        called = called.replace(' ', '')
        called = called.replace('-', '')
        if (called[0] == '+'):
            called = called[1:]
        if ((called.isdigit() == False) or (uid.isdigit() == False) or (echo != '0' and echo != '1')):
            logger.info('传入参数错误!')
            return '{"result":"-10"}'
        if sign != md5.new(uid + config.key).hexdigest():
            return '{"result":"-6"}'
        try:
            ln = len(called)
            if ((ln >= 2) and (ln <= 4)):
                called = tool.get_called_by_cornet(uid, called)
            if called:
                result = call.call(uid, pwd, called, echo, far_ip)
                logger.info("pv=%s, v=%s, uid=%s, called=%s, echo=%s" % (pv, v, uid, called, echo))
                return str(result)
            else:
                logger.info("%s呼叫%s，短号相应的号码获取失败" % (uid,called))
                return '{"result":"-3"}'
        except:
            logger.info("call proc exception: %s " % traceback.format_exc())
            return '{"result":"-11"}'
    @cherrypy.expose
    def free_call(self, caller, callee, pwd, agent_id, agent_name, sign):
        far_ip = cherrypy.request.remote.ip
        try:
            if (not caller) or (not callee) or (not pwd) or (not agent_id) or (not agent_name):
                logger.info('传入参数错误!')
                return '-1'
            if ((pwd.isalnum() == False) or (callee.isdigit() == False) or (caller.isdigit() == False)):
                logger.info('传入参数错误!')
                return '-1'
            if sign != md5.new(caller + config.key).hexdigest():
                return '{"result":"-12"}'
            logger.info('free call: caller:%s,callee:%s,agent_id:%s,agent_name:%s' % (caller,callee,agent_id,agent_name.decode('gbk')))
            passwd = tool.cryptData(pwd)
            result = reg.register(caller, passwd, agent_id, 1, far_ip)
            tmp = json.loads(result)
            res = tmp['result']
            if callee == caller:
                return res
            else:
                if res != '0':
                    return res
                result = call.call(str(tmp['uid']), passwd, callee, '1', far_ip)
                tmp = json.loads(result)
                return tmp['result']
        except:
            logger.info("reg proc exception: %s " % traceback.format_exc())
            return '-1'
    @cherrypy.expose
    def change_phone(self, old_phone, pwd, new_phone, sign):
        if sign != md5.new(old_phone + config.key).hexdigest():
            return '{"result":"-6"}'
        try:
            result = change.change_phone(old_phone, pwd, new_phone)
            return str(result)
        except:
            logger.info("change_phone proc exception: %s " % traceback.format_exc())
            return '{"result":"-10"}'
    @cherrypy.expose
    def find_password(self, phone, sign):
        if sign != md5.new(phone + config.key).hexdigest():
            return '{"result":"-6"}'
        if not str(phone).isdigit():
            return '{"result":"-5"}'
        try:
            result = find_password.find_password(phone)
            return str(result)
        except:
            logger.info("find_password proc exception: %s " % traceback.format_exc())
            return '{"result":"-10"}'
    @cherrypy.expose
    def change_pwd(self, phone, old_pwd, new_pwd, sign):
        if sign != md5.new(phone + config.key).hexdigest():
            return '{"result":"-6"}'
        try:
            result = change.change_pwd(phone, old_pwd, new_pwd)
            return str(result)
        except:
            logger.info("change_pwd proc exception: %s " % traceback.format_exc())
            return '{"result":"-10"}'
    @cherrypy.expose
    def search_balance(self, uid, pwd, sign):
        if sign != md5.new(uid + config.key).hexdigest():
            return '{"result":"-6"}'
        try:
            result = search_balance.can_call(uid)
            result = result.replace('-8',  '0')
            result = result.replace('-9',  '0')
            result = result.replace('-10', '0')
            return str(result)
        except:
            logger.info("search_balance proc exception: %s " % traceback.format_exc())
            return '{"result":"-11"}'
    @cherrypy.expose()
    def msglist(self, sc, pv, v):
        try:
            if (not sc) or (not pv) or (not v) or (sc.isdigit() == False):
                logger.info('传入参数错误!')
                return '{"result":"-10"}'
            result = sysmsg.msglist(sc, pv, v)
            return str(result)
        except:
            logger.info("msglist proc exception: %s " % traceback.format_exc())
            return '{"result":"-10"}'
    @cherrypy.expose()
    def getmsg(self, id, pv, v):
        try:
            if (not id) or (not pv) or (not v) or (id.isdigit() == False):
                logger.info('传入参数错误!')
                return '{"result":"-10"}'
            result = sysmsg.getmsg(id, pv, v)
            return str(result)
        except:
            logger.info("getmsg proc exception: %s " % traceback.format_exc())
            return '{"result":"-10"}'
    @cherrypy.expose()
    def charge(self, uid, paytype, goodstype, money, cardno, cardpwd, sign, pv, v):
        if sign != md5.new(uid + config.key).hexdigest():
            return '{"result":"-6"}'
        try:
            result = charge.pay(uid, paytype, goodstype, money, cardno, cardpwd, pv, v)
            return str(result)
        except:
            logger.info("charge proc exception: %s " % traceback.format_exc())
            return '{"result":"-10"}'
    @cherrypy.expose()
    def add_money(self, uid, actual, virtual, order, paytype, sign, web='0'):
        if sign != md5.new(uid + config.key + actual).hexdigest():
            return '{"result":"-6"}'
        try:
            result = charge.add_money(uid, actual, virtual, order, paytype, web)
            return str(result)
        except:
            logger.info("add_money proc exception: %s " % traceback.format_exc())
            return '{"result":"-10"}'
    @cherrypy.expose()
    def package(self, uid, packageid, no, orderno, sign, web='0', paytype=''):
        if sign != md5.new(uid + orderno + config.key).hexdigest():
            return '{"result":"-6"}'
        try:
            result = charge.package(uid, packageid, no, orderno, web, paytype)
            return str(result)
        except:
            logger.info("package proc exception: %s " % traceback.format_exc())
            return '{"result":"-10"}'
    @cherrypy.expose()
    def findphone_req(self, uid, sign):
        if sign != md5.new(uid + config.key).hexdigest():
            return '{"result":"-6"}'
        try:
            phone = tool.get_bind_mobile(uid)
            if phone:
                return '{"result":"0","phone":"%s"}' %phone['long_name']
            else:
                return '{"result":"-4"}'
        except:
            logger.info("findphone_req proc exception: %s " % traceback.format_exc())
            return '{"result":"-10"}'
    @cherrypy.expose()
    def getinfo(self, phone, sign):
        if sign != md5.new(phone + config.key).hexdigest():
            return '{"result":"-6"}'
        try:
            result = tool.get_bind_uid_and_pwd(phone)
            if result:
                return '{"result":"0","uid":"%s","pwd":"%s"}' % (result['user_name'], result['reg_pwd'])
            else:
                return '{"result":"-4"}'
        except:
            logger.info("getinfo proc exception: %s " % traceback.format_exc())
            return '{"result":"-10"}'
    @cherrypy.expose()
    def user_type(self, phone, sign):
        if sign != md5.new(phone + config.key).hexdigest():
            return '{"result":"-6"}'
        if not str(phone).isdigit():
            return '{"result":"-5"}'
        try:
            sql = "SELECT field_id FROM user WHERE long_name='%s'" % phone
            ret = db_util.query_db(sql)
            if ret and ret['field_id']:
                sql = "SELECT SUM(money) AS money FROM charge_log WHERE chargee_id='%s' AND (operate_type='充值' OR operate_type='划账')" %(ret['field_id'])
                hos = db_util.query_db(sql) #累计充值
                if hos and hos['money'] and hos['money'] >= 10000000:
                    return '{"result":"0","type":"1"}'
                elif hos['money'] == None or hos['money'] < 10000000:
                    return '{"result":"0","type":"0"}'
                else:
                    return '{"result":"-4"}'
            else:
                return '{"result":"-3"}'
        except:
            logger.info("user_type proc exception: %s " % traceback.format_exc())
            return '{"result":"-10"}'
    @cherrypy.expose()
    def is_free(self, field_id, balance):
        if not str(field_id).isdigit():
            return '-5'
        if not str(balance).isdigit():
            return '-4'
        try:
            ret = call.is_free(field_id, int(balance)/100.0)
            if ret == True:
                return '1'
            else:
                return '0'
        except:
            logger.info("is_free proc exception: %s " % traceback.format_exc())
            return '-10'
    @cherrypy.expose()
    def send_sms(self, phone, message, sign):
        if sign != md5.new(phone + config.key).hexdigest():
            return '{"result":"-6"}'
        if (not str(phone).isdigit()) or (not message):
            logger.info('传入参数错误!')
            return '{"result":"-5"}'
        try:
            url = config.SMS_parameter %(phone,message)
            f = urllib2.urlopen(url)
            xmlstr = str(f.read())
            xmlstr = xmlstr.replace('\r', '')
            xmlstr = xmlstr.replace('\n', '')
            xmlstr = xmlstr.replace('\t', '')
            doc    = minidom.parseString(xmlstr)
            root   = doc.documentElement
            nodes  = root.getElementsByTagName('error')
            value  = nodes[0].childNodes[0].nodeValue
            result = value.encode('utf-8','ignore')
            return '{"result":"%s"}' %result
        except:
            logger.info("send_sms proc exception: %s " % traceback.format_exc())
            return '{"result":"-10"}'


conf = os.path.join(os.path.dirname(__file__), 'http.conf')
if __name__ == '__main__':
    config.initLog()
    cherrypy.tree.mount(mobile_server(), '/')
    cherrypy.quickstart(config=conf)
    if hasattr(cherrypy.engine, 'block'):
        cherrypy.engine.start()
        cherrypy.engine.block()
    else:
        cherrypy.server.quickstart()
        cherrypy.engine.start()
