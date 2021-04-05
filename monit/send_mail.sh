#!/bin/bash
# $1 file $2 dest email
# used by blynk_monit.py to send mail in case of monit summary error
# send_pushover send email using mpack, to include file attachement
echo 'send mail' $1 $2
cat $1 | mail -s 'monit detected an error' $2
