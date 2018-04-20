#!/bin/sh
cd /home/mobile
ps -ef|grep mobile.py|grep -v grep|awk '{print$2}'|xargs kill -9
sleep 1
nohup python mobile.py > /dev/null 2>&1 &

#清除35天之前的call_log
ps -ef|grep clean_log.pyc|grep -v grep|awk '{print$2}'|xargs kill -9
sleep 1
python clean_log.pyc > /dev/null 2>&1 &
