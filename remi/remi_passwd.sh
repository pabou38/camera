#!/bin/bash

# $1  change or view
# $2  new password

cd /home/pi/remi

# would go back to rpc caller
#echo $1 $2

case $1 in

'change')

########################
# change  REMI password
########################

#https://stackoverflow.com/questions/4870253/sed-replace-single-double-quoted-text


# get current password
pass=$(sudo grep passwd remi_config.txt | cut -f4 -d '"')

sudo cp remi_config.txt remi_config.txt.bak

# inside " $pass is expended as $, and \ has special meaning
# inside ' it is not. no special char inside '


sudo cat remi_config.txt | sed "s/: \"$pass\",/: \"$2\",/g" > /home/pi/ramdisk/a
sudo cp /home/pi/ramdisk/a remi_config.txt

# read current value
pass=$(sudo grep passwd remi_config.txt | cut -f4 -d '"')
echo 'GUI: '$pass

# restart remi to read new json config
# not reload
#sudo systemctl restart remi.service > /dev/null
# rather ask user to restart gui

;;

'view')

#############################
# view remi password
############################
cd /home/pi/remi
pass=$(sudo grep passwd remi_config.txt | cut -f4 -d '"')
echo 'GUI: '$pass

;;

*)
echo 'wrong command'
;;
esac
