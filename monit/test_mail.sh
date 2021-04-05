#!/bin/bash
#https://www.tecmint.com/send-email-attachment-from-linux-commandline/

echo 'test sending email. email are sent on camera node. blynk_monit and sendpushover (motion detect) send mail'


dest='your@gmail.com'
echo 'test email' $dest


echo 'ssmtp deprecated in buster. use msmtp'
# install msmtp msmtp-mta bsd-mailx
# install sharutils    (uuencode)


echo 'simple, no subject'
echo 'TEST. delete' | mail $dest


echo 'with subject'
printf "Subject:TEST. delete\nLe corp du message" | msmtp $dest

echo 'with uuencode'
uuencode -m ./test_mail.sh /dev/stdout | msmtp $dest

# with file attachement
echo 'with file attachement'
mpack -s "TEST. with file. delete" /etc/rc.local $dest

#log defined in /etc/msmtprc
tail /home/pi/ramdisk/msmtp.log
