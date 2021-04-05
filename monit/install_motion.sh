#!/bin/bash

echo 'copy motion.conf'
sudo cp ./motion.conf /etc/motion
echo 'restart motion'
sudo systemctl restart motion

sudo systemctl status motion


