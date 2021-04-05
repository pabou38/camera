#!/usr/bin/python3

# use https://pushover.net/ to send notification from desktop

#import httplib Python 2
# httplib is http.client or ? httplib2 for Python3

#import httplib2

#https://support.pushover.net/i44-example-code-and-pushover-libraries#python

"""
pushover key

go to https://pushover.net/
user key is for all application
To receive notifications from a Pushover-powered application, service, or website, just supply your user key:


go in your application
pick an app (eg PI tinkering)
To begin using our API to send notifications, use this application's API token:

"""



import http.client, urllib
import sys
import os
import logging, datetime
import json
import subprocess

"""
urllib has been split up in Python 3.
The urllib.urlencode() function is now urllib.parse.urlencode(),
the urllib.urlopen() function is now urllib.request.urlopen().
"""


# debug, info, warning, error, critical
log_file = "/home/pi/ramdisk/send_pushover.log"

# read json config for single camera
with open('/home/pi/monit/cam_config.txt','r') as fp:
	data = json.load(fp)

# destination email
email = data["email"]

# prevent issue rw r r owned by motion
os.system('sudo touch ' + log_file)
os.system('sudo chmod 666 ' + log_file)

print ("logging to:  " , log_file)
logging.basicConfig(filename=log_file,level=logging.INFO)

logging.info(str(datetime.datetime.now())+ ' ---- send_pushover starting ----' )

print('python: ', sys.version)
#logging.info(str(datetime.datetime.now())+ ' Python: ' + sys.version )

# motion pass file name as /var/www/html/motion/01-2020- ...
import re
file1 = sys.argv[1] # keep file system name for sending as email attachement
cam = sys.argv[2] # cam1 from motion.conf. not yet dynamic

logging.info(str(datetime.datetime.now())+ ' arguments: %s %s' %(sys.argv[1], sys.argv[2]) )


# convert file name from file system to web access
file = re.sub('/var/www/html/motion/', '', file1)
mkv = re.sub('jpg', 'mkv', file) # associated mkv file

# NAT for web server w/ gallery 1


url= cam + \
"\n" + data['dns'] + ':' + data['cam_web_port'] + "/motion/" + file +\
"\n\n" + "http://" + data['ip'] + "/motion/" + file +\
"\n\n" + data['dns'] + ':' + data['cam_web_port'] + "/motion/" + mkv

print(url)
logging.info(str(datetime.datetime.now())+ ' urls: ' + url )


##########################
# send notification pushover
##########################

"""
 Alternatively, a number of 3rd party packages are available:  pushnotify package written by Jeffrey Goettsch, pushover Python 3 package written by Wyatt Johnson, Chump Python package written by Karan Lyons, and python-pushover Python package written by Thibaut Horel.
"""


# python 3
#For Python 3, httplib has been replaced with http.client and urlencode has moved to urllib.parse.
try:
	conn = http.client.HTTPSConnection("api.pushover.net:443") 

except Exception as e:
	print('cannot create pushover connection ',str(e))
	logging.error(str(datetime.datetime.now())+ ' cannot create push connection ' + str(e) )

try:
	# python 3
	conn.request("POST", "/1/messages.json",
    urllib.parse.urlencode({
    "token": data['push_token'],
    "user": data['push_user'],
    "sound": "echo",
    "priority": 1,
    "title": "motion control",
    "message": url,
  }), { "Content-type": "application/x-www-form-urlencoded" })

	r=conn.getresponse() # returns HTTPResponse object
	print('pushover http status code: ' ,r.status, type(r.status))
	logging.info(str(datetime.datetime.now())+ ' pushover http status code: ' + str(r.status) )

	if r.status != 200:
		logging.error(str(datetime.datetime.now())+ ' http status code error: ' + str(r.status) )

except Exception as e:
	print('con request error: ', str(e))
	logging.error(str(datetime.datetime.now())+ ' con request error: ' + str(e) )



##############################################
# send email
# mpack -s "Subject here" file user@example.com
#############################################


# use original file name, file system path
#sendmail: impossible d'écrire dans le journal /home/pi/ramdisk/msmtp.log : erreur d'ouverture de fichier: Permission non accordée

# not a string but list

# using sudo here creates problem when run from motion. not a problem if ran from shell 
s = [ '/usr/bin/mpack' , '-s' , 'notification_camera' , file1,  email]
logging.info(str(datetime.datetime.now())+ ' send email with: ' + str(s) )
print ('send email with ', s)

result = subprocess.run(s , stdout=subprocess.PIPE)
print('subprocess result ', result)
logging.info(str(datetime.datetime.now())+ ' subprocess result %s' %(result) )

# script output. echo in script
stdout = result.stdout.decode('utf-8')
if result.returncode != 0:
	print('error sending email' )
	logging.error(str(datetime.datetime.now())+ ' error sending email. stdout %s %s' %(stdout,result.returncode) )

else:
	print('email sent OK' )
	logging.info(str(datetime.datetime.now())+ ' email sent OK')



logging.info(str(datetime.datetime.now())+ ' ---- send_pushover ends ----' )
