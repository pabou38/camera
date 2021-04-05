#!/bin/bash

cd /home/pi/monit

sudo cp monitrc monitrc.bak

echo 'check /home/pi/monit/monitrc config file'
sudo monit -t -c ./monitrc

echo 'copy monitrc to run time location /etc/monit'
sudo cp monitrc /etc/monit
sudo monit -t

echo 'restart monit'
sudo systemctl restart monit
sudo systemctl status monit

sudo monit summary

