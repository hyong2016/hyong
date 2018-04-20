#coding=UTF-8
import MySQLdb
import config
import logging, traceback

logger = logging.getLogger(__name__)
DSN_DBCONN = dict({"host":"112.124.58.27","user":"xiaowei","passwd":"sz888888","db":"8601","charset":"utf8",'cursorclass':MySQLdb.cursors.DictCursor})
try:
    import MySQLdb
    from DBUtils.PooledDB import PooledDB
    db_pooled = PooledDB(MySQLdb, **DSN_DBCONN)
except ImportError, e:
    logger.info("DButil Eroor")
    print "DButil Eroor"
    import sys
    sys.exit(1)

def getDbcnn():
    return db_pooled.connection(shareable=False)

def query_db(sql, type=1):
    try:
        conn = getDbcnn()
        cursor = conn.cursor(cursorclass = MySQLdb.cursors.DictCursor)
        cursor.execute(sql.decode('UTF-8'))
        if type == 1:
            result = cursor.fetchone()
        else:
            result = cursor.fetchall()
        conn.close()
        cursor.close()
        return result
    except:
        logger.info('query_db execute %s fail \n  proc :%s \n' % (sql, traceback.format_exc()))
        return None

def modify_db(sql):
    try:
        conn = getDbcnn()
        cursor = conn.cursor()
        result = cursor.execute(sql)
        conn.commit()
        conn.close()
        cursor.close()
        return result
    except :
        logger.info('modify_db execute %s fail \n  proc :%s \n' % (sql, traceback.format_exc()))
        return None

#支持中文的插入，使用方式如下：
#sql = "insert into ewyu(gg, ff) values('china', %s)"
#para = ("北京")
def insert_db(sql,para):
    try:
        conn = getDbcnn()
        cursor = conn.cursor()
        result = cursor.execute(sql, para)
        conn.commit()
        conn.close()
        cursor.close()
        return result
    except :
        logger.info('insert_db execute %s fail \n  proc :%s \n' % (sql, traceback.format_exc()))
        return None
