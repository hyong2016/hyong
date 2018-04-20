#!/bin/sh

mkdir -p /dev/mqueue
mount -t mqueue none /dev/mqueue
cd /dev/mqueue

DATE=`date +%m-%d`
ls -lt | grep -v $DATE | awk '{print$8}' | xargs rm -f

cd /
umount -t mqueue /dev/mqueue
