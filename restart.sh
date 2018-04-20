#!/bin/sh
cd /home/mobile


ps -ef|grep vice.sh|grep -v grep|awk '{print$2}'|xargs kill -9
ps -ef|grep itf.py |grep -v grep|awk '{print$2}'|xargs kill -9

PID=`ps -ef|grep cb|grep -v grep|awk '{print$2}'`
if [ -n "$PID" ]; then
    kill $PID

    #cb退出时话单传送需10秒,再延5秒让端口完全关闭
    sleep 15
fi

PID=`ps -ef|grep cb|grep -v grep|awk '{print$2}'`
if [ ! -n "$PID" ]; then
    PID=`ps -ef|grep tps|grep -v grep|awk '{print$2}'`
    kill $PID
    sleep 5

    rm -f /var/lock/subsys/cb
    rm -f /var/lock/subsys/tps

    /etc/rc.d/init.d/cbmon start
    sleep 3
    /etc/rc.d/init.d/tpsmon start

    #延迟1秒让cb内部模块全部启动完成
    sleep 3
    ./start.sh &
    ./vice.sh &
fi


PID=`ps -ef|grep cb|grep -v grep|awk '{print$2}'`
if [ ! -n "$PID" ]; then
    echo "cb pid is not exist"
    rm -f /var/lock/subsys/cb
    rm -f /var/lock/subsys/tps
    reboot
fi

PID=`ps -ef|grep tps|grep -v grep|awk '{print$2}'`
if [ ! -n "$PID" ]; then
    echo "tps pid is not exist"
    rm -f /var/lock/subsys/cb
    rm -f /var/lock/subsys/tps
    reboot
fi
