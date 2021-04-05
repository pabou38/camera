#!/bin/bash
###############################################
# executed on remote camera
##############################################

command=$1
param=$2
# param = ' ' for read, slider value for set
# string for password
# none for halt, reboot
# echo will be sent to caller, and displayed on remi widget


tmp=/dev/null
tmp='/home/pi/ramdisk/rpc_remi.log'


# echo will be displayed on GUI

#echo 'input command '$1

echo '=== RPC camera v1.1 ===' >> $tmp

echo $(date)  >> $tmp
echo 'input: '$command $param >> $tmp


# read_timelapse space
# set_timelapse 30
# halt
# reboot
# password string


case $command in

'test')
echo 'testing'
;;

####################################
# SYSTEM
####################################


'halt')
echo 'will halt' >> $tmp
echo 'will halt'

sudo halt
;;

'reboot')
echo 'will reboot' >> $tmp
echo 'will reboot'
sudo reboot
;;

# change password
'password')

echo 'will change password to: ' $2  >> $tmp

##############
# change gallery password
#############

echo 'gallery' >> $tmp

cd /var/www/html/motion
sudo cp index.php index.php.old
# read password line get rid of all undeeded char


pass=$(grep define index.php | grep PASS | cut -f2 -d ' ' | sed "s/[),;,\r']//g")
#echo 'old password' $pass
# WTF. there is a CR LF at the end. no wonder why sed did not work
# not sure is this is echo who adds it

# remove trailinh lf in case
p=$(echo $pass | tr -d '\n')

# plain password
#echo $p | hexdump -c


sudo touch /home/pi/ramdisk/a
sudo chmod 777 /home/pi/ramdisk/a

cat index.php | sed "s/'$p');/'$2');/g" > /home/pi/ramdisk/a
sudo cp /home/pi/ramdisk/a index.php

# send new password to calling widget
pass_gal=`grep define index.php | grep PASS | cut -f2 -d ' ' | sed "s/[),;,']//g"`

echo 'OK GALLERY: '$pass_gal >> $tmp

##############
# change MOTION password
#############

echo 'motion' >> $tmp

cd /home/pi/monit

pass=$(grep 'stream_authentication camera38'  motion.conf | cut -f2 -d ':')

# modify value in motion.conf
sudo cp motion.conf motion.conf.bak
# no ' around stream_authentication camera38
# camera38 hardcoded in motion.conf
sudo cat motion.conf | sed "s/stream_authentication camera38:$pass/stream_authentication camera38:$2/g" > /home/pi/ramdisk/a

pass=$(grep 'webcontrol_authentication camera38'  /home/pi/ramdisk/a | cut -f2 -d ':')

sudo cat /home/pi/ramdisk/a | sed "s/webcontrol_authentication camera38:$pass/webcontrol_authentication camera38:$2/g" > /home/pi/ramdisk/a1

sudo cp /home/pi/ramdisk/a1 motion.conf

# restart
echo 'install motion' >> $tmp
sudo cp motion.conf /etc/motion

echo 'restart motion' >> $tmp
sudo systemctl restart motion &

# get new value from live configuration
echo 'get new value' >> $tmp
motion_p1=$(grep 'stream_authentication camera38'  /etc/motion/motion.conf | cut -f2 -d ':')
motion_p2=$(grep 'webcontrol_authentication camera38' /etc/motion/motion.conf  | cut -f2 -d ':')
echo 'OK MOTION: stream '$motion_p1 'web '$motion_p2 >> $tmp



##############
# change MONIT password
#############

echo 'monit' >> $tmp

cd /home/pi/monit

monit_pass=$(sudo grep 'allow camera38' monitrc | cut -f2 -d ':')

sudo cp monitrc monitrc.bak

sudo cat monitrc | sed "s/allow camera38:$pass/allow camera38:$2/g" > /home/pi/ramdisk/a

sudo cp /home/pi/ramdisk/a monitrc

echo 'install monit' >> $tmp
sudo ./install_monit.sh > /dev/null

# read from live config
monit_pass=$(sudo grep 'allow camera38' /etc/monit/monitrc | cut -f2 -d ':')


echo 'OK MONIT: '$monit_pass >> $tmp


# echo to send back to caller
echo 'send back to caller ' >> $tmp
echo 'GALLERY: ' $pass_gal
echo 'MOTION: stream: ' $motion_p1
echo 'MOTION: web: ' $motion_p2
echo 'MONIT: ' $monit_pass

;;



'view_password')

echo 'will view password' >> $tmp

# gallery
cd /var/www/html/motion
p3=$(grep define index.php | grep PASS | cut -f2 -d ' ' | sed "s/[),;,\r']//g")

# motion
p1=$(grep 'stream_authentication camera38'  /etc/motion/motion.conf | cut -f2 -d ':')
p2=$(grep 'webcontrol_authentication camera38' /etc/motion/motion.conf  | cut -f2 -d ':')

# monit
p4=$(sudo grep 'allow camera38' /etc/monit/monitrc | cut -f2 -d ':')

# remi
#cd /home/pi/remi
#p5=$(sudo grep passwd remi_config.txt | cut -f4 -d '"')

# -e interpret \n
#echo 'gallery '$p3 "stream "$p1 "admin "$p2 "monit "$p4 "GUI "$p5 >> $tmp
#echo -e "\n" 'gallery: '$p3 'stream: '$p1 "\n" 'admin: '$p2 'monit: '$p4 "\n"  'GUI: '$p5 


echo 'gallery '$p3 "stream "$p1 "admin "$p2 "monit "$p4  >> $tmp
echo -e "\n" 'gallery: '$p3 'stream: '$p1 "\n" 'admin: '$p2 'monit: '$p4 "\n"

# stdout
;;

####################################
# READ
####################################


'read_timelapse')

a=`grep timelapse_interval /etc/motion/motion.conf | tail -n1`
# send result. echo is send by rshell to caller
echo $a
echo $a >> $tmp
;;

'read_snapshot')

# if multiple instance, take last one. assume custo is at the end
a=`grep snapshot_interval /etc/motion/motion.conf | tail -n1`

# take only  words
#a1=$(echo $a| cut -f3 -d ' ')
#a2=$(echo $a| cut -f4 -d ' ')
#echo $a1 $a2
echo $a
echo $a >> $tmp
;;

'read_threshold')

a=`grep threshold /etc/motion/motion.conf | tail -n1`
echo $a
echo $a >> $tmp
;;


####################################
# SET
# $2 is parameter
####################################


'set_timelapse')

# update motion.conf in monit directory
cd /home/pi/monit

# first read current line
a=`grep timelapse_interval motion.conf | tail -n1`
# get value
current=$(echo $a | cut -d ' ' -f 2)
echo 'set new timelapse ' $current $2 >> $tmp

# modify value in motion.conf
sudo cp motion.conf motion.conf.bak
sudo cat motion.conf | sed "s/timelapse_interval $current/timelapse_interval $2/g" > /home/pi/ramdisk/a
# 2 step because permission non accordee
sudo cp /home/pi/ramdisk/a motion.conf

# restart motion with new config file
sudo /home/pi/monit/install_motion.sh > /dev/null

# read value from live config file

a=`grep timelapse_interval /etc/motion/motion.conf | tail -n1`
echo 'updated value:'  $a
echo 'live value ' $a >> $tmp
;;


'set_snapshot')
cd /home/pi/monit
# first read current line
a=`grep snapshot_interval motion.conf | tail -n1`
# get value
current=$(echo $a | cut -d ' ' -f 2)
echo 'set new snapshot ' $current $2 >> $tmp

sudo cp motion.conf motion.conf.bak
sudo cat motion.conf | sed "s/snapshot_interval $current/#RPC\nsnapshot_interval $2/g" > /home/pi/ramdisk/a 
# 2 step because permission non accordee
sudo cp /home/pi/ramdisk/a motion.conf
sudo ./install_motion.conf.sh

a=`grep snapshot_interval /etc/motion/motion.conf | tail -n1`
echo 'updated value:'  $a
echo 'live value '  $a >> $tmp
;;

'set_threshold')
cd /home/pi/monit
# first read current line
a=`grep threshold motion.conf | tail -n1`
# get value
current=$(echo $a | cut -d ' ' -f 2)
echo 'set new threshold ' $current $2 >> $tmp

sudo cp motion.conf motion.conf.bak
sudo cat motion.conf | sed "s/threshold $current/#RPC\nthreshold $2/g" > /home/pi/ramdisk/a 
# 2 step because permission non accordee
sudo cp /home/pi/ramdisk/a motion.conf
sudo ./install_motion.sh > /dev/null

a=`grep threshold /etc/motion/motion.conf | tail -n1`
echo 'updated value:'  $a
echo 'live value '  $a >> $tmp
;;


*)
echo 'rpc server: wrong command '$1
echo 'rpc wrong command '$1 >> $tmp
;;

esac
