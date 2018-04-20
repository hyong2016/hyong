#coding=UTF-8
import logging, logging.handlers
import MySQLdb, MySQLdb.cursors

__LOG_FILE = "./log/run.log"

java = '2.0'
java_update_add = 'http://wap.aicall800.com/download/aicall_java.jar'

android = '2.2.0'
android_update_add = 'http://wap.aicall800.com/download/aicall_android.apk'

iphone = '2.1.8'
iphone_update_add = 'http://wap.aicall800.com/download/aicall_apple.ipa'

S60V3 = '1.0'
S60V3_update_add = 'http://wap.aicall800.com/download/aicall_S60V3.sisx'

S60V5 = '1.0'
S60V5_update_add = 'http://wap.aicall800.com/download/aicall_S60V5.sisx'

PC = '1.8'
PC_update_add = 'http://wap.aicall800.com/download/update.zip'

MIN_BALANCE = 150000

APS = {"host":"localhost","user":"python","passwd":"888python888","db":"aps","charset":"utf8",'cursorclass':MySQLdb.cursors.DictCursor}
WAP = {"host":"localhost","user":"wap","passwd":"wap","db":"wap","charset":"utf8",'cursorclass':MySQLdb.cursors.DictCursor}

given = 6000000

service_phone = "0204000755181"
key = "&%&aicall$#$"

prefix = "0086"
nights = "00083"
CB_KEY = "*aicall#"

"""配置回拨分流服务器IP"""
#ADDR1 = 127.0.0.1
#ADDR2 = 211.154.154.231
#ADDR3 = 211.154.154.232
#ADDR4 = 183.61.244.6
CB_ADD = {
    '0'   : 'http://127.0.0.1:9999/',#绑定固话呼叫
    '000' : 'http://127.0.0.1:9999/',#夜间免费呼叫
    '134' : 'http://127.0.0.1:9999/',
    '135' : 'http://127.0.0.1:9999/',
    '136' : 'http://127.0.0.1:9999/',
    '137' : 'http://127.0.0.1:9999/',
    '138' : 'http://127.0.0.1:9999/',
    '139' : 'http://127.0.0.1:9999/',
    '13' : 'http://127.0.0.1:9999/',
    '14' : 'http://127.0.0.1:9999/',
    '15' : 'http://127.0.0.1:9999/',
    '16' : 'http://127.0.0.1:9999/',
    '17' : 'http://127.0.0.1:9999/',
    '18' : 'http://127.0.0.1:9999/',
    '19' : 'http://127.0.0.1:9999/',
    }

CB_parameter = "callback?sn=%s&uid=%s&caller=%s&called=%s&echo=%s&ref=%s&resv=%s&sign=%s"
SMS_parameter = "http://sdkhttp.eucp.b2m.cn/sdkproxy/sendsms.action?cdkey=3SDK-EMY-0130-OKRSN&password=214124&phone=%s&message=%s&addserial="

charge_KEY  = "123456"
Charge_ADDR = "http://127.0.0.1/pay.php?src=%s&ordersn=%s&uid=%s&paytype=%s&goodstype=%s&money=%s&cardno=%s&cardpwd=%s&sign=%s"

def initLog():
    logger = logging.getLogger()
    hdlr = logging.handlers.TimedRotatingFileHandler(__LOG_FILE, when='midnight', backupCount=30)
    formatter = logging.Formatter("[%(asctime)s]: %(module)s %(message)s ")
    hdlr.setFormatter(formatter)
    logger.addHandler(hdlr)
    logger.setLevel(logging.DEBUG)
