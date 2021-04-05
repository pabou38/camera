#!/bin/bash

echo 'test rpc to validate certificates. use sudo to be root'

echo 'I am' $LOGNAME

cmd='/home/pi/monit/rpc.sh'


echo ' '
remote='192.168.1.227'
echo 'remote' $remote

rsh $LOGNAME@$remote $cmd read_timelapse
ssh $LOGNAME@$remote $cmd read_threshold
ssh $LOGNAME@$remote $cmd read_snapshot


echo ' '
remote='192.168.1.228'
echo 'remote' $remote

rsh $LOGNAME@$remote $cmd  read_timelapse
ssh $LOGNAME@$remote $cmd  read_threshold
ssh $LOGNAME@$remote $cmd  read_snapshot

