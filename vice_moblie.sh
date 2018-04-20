#!/bin/sh
cd /home/mobile

while [ 1 ]
do
    j=`/bin/ps -ef | grep mobile.py | grep -v grep | wc -l`
    DATE=`/bin/date +%m%d-%H:%M`

    if [ $j -eq 0 ]; then
        echo "$DATE     Alert: mobile.py is restarting ... " >> ./restart.log
        sh ./start.sh
    fi

    #必须大于每天正常重启所需的时间
    sleep 8
done

#定时任务,注意修改vos默认值为09:02(原为03:30)
#crontab -e
#0 9 * * * /home/sendFax/restart.sh

