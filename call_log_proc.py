#coding=UTF-8
import time,tool,db_util


#VOS上计费了CB里没有计到费处理，将VOS里的话单导入到call_log_temp表，然涿条进行处理
def no_bill_and_not_logs():
    sql = "SELECT * FROM call_log_temp"
    list = db_util.query_db(sql, 2)
    for row in list:
        t = row['field_units']%60
        if t > 0:
            t = 1
        field_units = row['field_units']/60 + t
        field_fee   = field_units*150000

        sql = "SELECT user_name,field_id FROM user WHERE long_name='%s'" %row['mobile'][1:]
        tmp = db_util.query_db(sql)
        if not tmp:
            print "%s in user table not found!!!" %(row['mobile'])
            continue

        from_number = tmp['user_name']


        sql = "UPDATE field_account SET balance = balance - %s WHERE field_id = '%s'" %(field_fee, tmp['field_id'])
        db_util.modify_db(sql)
        sql = "SELECT balance FROM field_account WHERE field_id = '%s'" %(tmp['field_id'])
        bln = db_util.query_db(sql)
        print "%s after:%s\tdrop:%s" %(row['mobile'], bln['balance'], field_fee)

        if row['to_number'][:2] == '00' and row['to_number'][:4] != '0086':
            call_type = 4
        else:
            call_type = 2

        sql = """INSERT INTO call_log(session_id, from_number, to_number, raw_from_number, raw_to_number, from_ip, to_ip, start_time, end_time, call_type, call_time, pkg_call_time, billing_time, agent_id, field_id, field_name, field_rate, field_units, field_fee, long_name) VALUES (floor(rand()*10000000), '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%d', %d, %d, %d, %d, %d, '%s', '%s', %d, %d, '%s')""" %(row['mobile'],row['to_number'],from_number,row['to_number'],row['from_ip'],row['to_ip'],row['start_time'],row['end_time'],call_type,row['call_time'],0,row['call_time'],1,tmp['field_id'],from_number,'0.150/60',field_units,field_fee,from_number+' :CB')
        db_util.modify_db(sql)
        time.sleep(1)

#jmdw2008的用户0070、0071、0071此三个国家按54秒一分钟来计费扣款
def bill_by_54s():
    return True
