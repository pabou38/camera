#!/usr/bin/python3

import time
import datetime
import subprocess
import _thread
import sys
import smtplib
from email.mime.text import MIMEText
import json
import re
import logging

"""
Blynk token

in android app
stop running
hexagon
send va email

"""



#https://github.com/vshymanskyy/blynk-library-python
#pip install blynk-library-python
import BlynkLib

# where is this lib ?  sudo find / -name"BlynkLib.py" 
# pijuice is in /usr/lib/python3.5
# BlynkLib is in /usr/local/lib/python2.7
# pi@juice:/usr/local/lib/python2.7/dist-packages $ sudo cp BlynkLib.py /usr/lib/python3.5/dist-packages/
# pi@juice:/usr/local/lib/python2.7/dist-packages $ sudo cp BlynkLib.py /usr/lib/python3.7


# debug, info, warning, error, critical
log_file = "/home/pi/ramdisk/blynk.log"

print ("logging to:  " , log_file)
logging.basicConfig(filename=log_file,level=logging.INFO)

logging.info(str(datetime.datetime.now())+ ' ---- send_blynk starting ----')


####### CUSTO
# to store output of monit summary
monit_output= '/home/pi/ramdisk/monit.output'
#############

fp = open('/home/pi/monit/cam_config.txt', 'r')
data = json.load(fp)
fp.close()

print(data)

ip = data['ip']
dest_email = data['email']
bterminal = int(data['terminal'])

print('update blynk with monit status on vpin %d'% bterminal)

"""
do not use thread
File "./blynk_monit.py", line 71, in blynk_thread
    blynk.on_connect(blynk_connected)
AttributeError: 'Blynk' object has no attribute 'on_connect'
"""


# create blynk there so that it is available in main thread as well
blynk = BlynkLib.Blynk(data['blynk_token'])

# use lf on android app
blynk.virtual_write(bterminal, datetime.datetime.now())

# test is monit web server running 
# shell = True to use pipe

result = subprocess.run(['/bin/nc', '-z' , ip , '2812'], stdout=subprocess.DEVNULL) # 0 if found
# ret code is an objet
print('nc ret code ',result.returncode) # 1 if not found, 0 is found
if result.returncode != 0:
	# monit http server not running
	print('port 2812 not there. reloading monit')
	subprocess.run(['/usr/bin/monit', 'reload'])
	time.sleep(3)

else:
	print('port 2812 already open')


# run monit summary
try:
	result = subprocess.run(['/usr/bin/monit', 'summary'], stdout=subprocess.PIPE)
	s = result.stdout.decode('utf-8')

except Exception as e: # monit summary command failed
	print('Exception monit summary command failed: %s' %(str(e)))
	logging.error(str(datetime.datetime.now())+ ' exception monit summary command failed %s' %str(e))

else:
	# replace multiple space to fit in blynk terminal 
	with open(monit_output, 'wb') as fp:
		fp.write(s.encode('utf-8'))

	s = re.sub('\s+', '  ', s)

	# header of monit summary
	s = re.sub('Service', '\nService', s)
	s = re.sub('Type', 'Type\n', s)

	# add new line
	s = re.sub('System', 'System\n', s)
	s = re.sub('Process', 'Process\n', s)
	s = re.sub('Filesystem', 'Filesystem\n', s)
	s = re.sub('Host', 'Host\n', s)
	s = re.sub('Network', 'Network\n', s)

	print(s)
	logging.info(str(datetime.datetime.now())+ ' monit summary %s' %s)


	# send email if some string are found in output of monit summary
	# ISSUE motion connection failed. FIXED in monitrc 

	if s.find('NOK',0,len(s)) != -1 or s.find('limit', 0, len(s)) != -1 or s.find('failed',0,len(s)) != -1: # ie found, means error
	#if s.find('NOK',0,len(s)) != -1 or s.find('limit', 0, len(s)) != -1 : # ie found
		print('monit summary returned error . will send email')
		logging.error(str(datetime.datetime.now())+ ' monit summary returned error. sending email')
		# sending email
		try:
			

			with open (monit_output, 'w+' ) as fp:
				fp.write(s)

			# send email using script


			result = subprocess.run(['/home/pi/monit/send_mail.sh', monit_output, dest_email], stdout=subprocess.PIPE)
			# script output. echo
			stdout = result.stdout.decode('utf-8')
			if result.returncode != 0:
				print('error while sending email')
				logging.error(str(datetime.datetime.now())+ ' error while sending email. stdout %s' %stdout)
			else:
				print('email sent ok. stdout: ', stdout)
				logging.info(str(datetime.datetime.now())+ ' email sent OK. stdout: %s' %stdout)

		except Exception as e: # could not send email 
			print('Exception in email script %s' %(str(e)))
			logging.error(str(datetime.datetime.now())+ ' email failed stdout: %s' %stdout)


	else:
		print('motion summary ok. did not send email')


# output to terminal
print('send to Blynk terminal')
blynk.virtual_write(bterminal, s)

print('blynk run')
try:
	blynk.run()
except Exception as e:
	print ("exception in Blynk.run") , e
	logging.error(str(datetime.datetime.now())+ ' exception Blynk.run %s' %str(e))

print('sleep in main')
time.sleep(20)

logging.info(str(datetime.datetime.now())+ ' ---- send_blynk ends ----')

print('exit in main')
sys.exit(0)
