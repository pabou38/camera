#!/usr/bin/python3

#############################################
# 02 avril 2021
# rpc hangs if not reachable
# added: gui password does not use rpc
#############################################



version = 'Meaudre Robotics. version 2.1'

#https://remi.readthedocs.io/en/latest/remi.html

# sudo pip3 install remi
# sudo pip3 install fabric. rshell over ssh. uses paramiko for low level

# permit root ssh. /etc/ssh/sshd_config  PermitRootLogin yes sudo service sshd restart

import remi.gui as gui
from remi import start, App
import time
import os
from fabric2 import Connection
#Fabric is a high level Python (2.7, 3.4+) library designed to execute shell commands remotely over SSH, yielding useful Python objects in return. It builds on top of Invoke (subprocess command execution and command-line features) and Paramiko (SSH protocol implementation), extending their APIs to complement one another and provide additional functionality.
#https://www.fabfile.org/



# MAKE SURE logging directory and file writable 
import logging
import datetime
import json
import sys
import subprocess


# debug, info, warning, error, critical
log_file = "/home/pi/ramdisk/remi.log"
print ("logging to:  " , log_file)
logging.basicConfig(filename=log_file,level=logging.INFO)
logging.error(str(datetime.datetime.now())+ ' ---- remi starting ----' )

print('import path: ', sys.path)

# source in /usr/local/lib/python3.7/dist-pacakges/remi
#pi@gadget:/usr/local/lib/python3.7/dist-packages/remi $ ls
#gui.py  __init__.py  __pycache__  res  server.py

# ADD set_url for Link in gui.py, to be able to change url when cam drop down changes

"""
    def get_url(self):
        return self.attributes['href']

    # PABOU
    def set_url(self,url):
        print('PABOU IN REMI ', url)
        self.attributes['href'] = url
        return self.attributes['href']
"""



title= 'motion control: '

# size of root container, ie the screen
# try and error. does not resize with mouse
w=320
h=600

"""
you can define the size of widgets as percentage instead of pixels.
widget = gui.Widget (width="50%", height ="20%")
This allows to auto size widget
to make the position change also you should use VBox or HBox as containers, and the contained widget must have the style parameter position as relative
"""

# read config file. data dict
with open('/home/pi/remi/remi_config.txt' ,'r') as fp:
	data = json.load(fp)



#all_cam = {'cam1':'192.168.1.227' , 'future1': '192.168.1.228'}

all_cam = {} # dict mapping cam name with local IP
all_cam_wan = {} # dict mapping cam name with dns name

"""
"all_cam" :
 {
  "1" : ["talloires" , ["192.168.1.227", "camera_talloires.ddns.net"]],
  "2" : ["future1", ["192.168.1.228", 'dns']] ,
  "3" : ["future2", ["192.168.1.228", 'dns']]
 }
"""


i=1
while True:
	try:
		x = data["all_cam"] [str(i)] # a list
		key = x[0]  # cam name

		local_ip = x[1]
		all_cam[key] = local_ip # update dict

		dns_name = x[2]
		all_cam_wan[key] = dns_name

		i = i + 1

	except Exception as e:
		break

print('dict of all cam, local IP ', all_cam)
print('dict of all cam, DNS ', all_cam_wan)

# build dynamic tuple of cam names, used for drop down, and key to all_cam dict
#		self.dropDown = gui.DropDown.new_from_list(('cam1', 'cam2', 'camc', 'came'), margin='10px', width=w/3)

# !!!!!!  .keys() does not return a list but a dict_keys object
#print(all_cam.keys(), type(all_cam.keys()))
l = []
for k in all_cam.keys():
	l.append(k)

first_cam = l[0]
all_keys = tuple(l) # tuple for drop down. keys() is NOT a list
print('all keys for drop down', all_keys)


# fabric2 rshell over ssh


#  only for camera, ie monit, motion and gallery
def do_rpc (rpc,remote):

	logging.info(str(datetime.datetime.now())+ ' rpc: %s remote: %s' %(rpc,remote) )

	print('	do_rpc %s on remote %s' %(rpc,remote))

	#c = Connection(host=remote, connect_timeout=5)
	c = Connection(host=remote)
	print('	connection created ', c) # does not fail even if remote not reachable
	# can also specify user, port


	# timeout is rpc execution, not ssh connection, 
	result= c.run(rpc, timeout=30) # seems will print stdout
	print('	rpc ran ')

	if result.ok:
		print('	rpc ok. stdout:\n', result.stdout)
		logging.info(str(datetime.datetime.now())+ ' RPC OK: %s' %(result.stdout) )
		return(True, result.stdout)
	else:
		print('	remote exec failed for %s. exited: %d' %(result.command, result.exited))
		logging.error(str(datetime.datetime.now())+ ' RPC ERROR: %s %d' %(result.command) )
		return(False, result.exited)


class remi_app(App):
	def __init__(self, *args):
		# custom style for app
		#res_path = os.path.join(os.path.dirname(__file__), 'res')
		#super(remi_app, self).__init__(*args, static_file_path={'res':res_path})
		super(remi_app, self).__init__(*args)
		# remi_app is a sub class of App

	# entry point
	def main(self):
		global cam, command, action
		global slider1_value, slider2_value

		self.colors = {'white' : '#ffffff', 'black' : '#000000', 'gray' : '#919191', 'x' : '#ff0000'}


		# default value
		cam = first_cam
		command = 'threshold'
		action = 'read'
		slider2_value = 0 # timelapse in sec
		slider1_value = 200 # threshold in pixels

		#container = gui.VBox(width=300, height=300, margin='10px')

		"""
		vertical = menu + label + dropdown + horizontal + slider
		horizontal = left + right
		"""

		# define all containers
		verticalContainer = gui.Container(width=w, height=h, margin='0px auto', style={'display': 'block', 'overflow': 'hidden', 'text-align':'center'})
		horizontalContainer = gui.Container(width=w, layout_orientation=gui.Container.LAYOUT_HORIZONTAL, margin='0px', style={'display': 'block', 'overflow': 'auto', 'text-align':'center'})

		subContainerLeft = gui.Container(width=w/2,  style={'display': 'block', 'overflow': 'auto', 'text-align': 'center'})
		subContainerRight = gui.Container(width=w/2, style={'display': 'block', 'overflow': 'auto', 'text-align': 'center'})

		# widgets for vertical

 		#menu
		self.menu = gui.Menu(width='100%', height='30px')
		self.m3 = gui.MenuItem('system', width=w/3, height=30)
		self.m2 = gui.MenuItem('guide', width=w/3, height=30)
		self.m1 = gui.MenuItem('about', width=w/3, height=30)

		self.m1.onclick.do(self.on_about)
		self.m2.onclick.do(self.on_guide)

		# sub menu

		ww = w/2 # width, enough space. WARNING. does not seem possible to extend beyond top widget, ie w/3
		ss = {"text-align":"left"}
		hh=20

		self.m31 = gui.MenuItem('halt camera', width=ww, height=hh, style=ss)
		self.m32 = gui.MenuItem('reboot camera', width=ww, height=hh, style=ss)
		self.m33 = gui.MenuItem('restart gui', width=ww, height=hh,style=ss)
		self.m34 = gui.MenuItem('change cam passwd', width=ww, height=hh, style=ss)
		self.m35 = gui.MenuItem('view cam passwd', width=ww, height=hh, style=ss)
		self.m36 = gui.MenuItem('change gui passwd', width=ww, height=hh, style=ss)

		self.m31.onclick.do(self.on_halt)
		self.m32.onclick.do(self.on_reboot)
		self.m33.onclick.do(self.on_gui) # restart gui
		self.m34.onclick.do(self.on_passwd) # change , monit, motion, gallery
		self.m35.onclick.do(self.on_view_passwd) # monit, motion, gallery
		self.m36.onclick.do(self.on_gui_passwd) # change password remi only

		# attach sub menu
		self.m3.append([self.m31, self.m32, self.m33, self.m34, self.m35, self.m36])

		self.menu.append([self.m1, self.m2, self.m3])

		self.menubar = gui.MenuBar(width='100%', height='30px')
		self.menubar.append([self.menu])


		# title
		self.label = gui.Label(title + first_cam, height=30, \
		style = { 'color' : self.colors['x'], 'font-weight' : 'bold', 'text-align' : 'center', 'font-size' : '20px'} \
		)

		# cam selection
#		self.dropDown = gui.DropDown.new_from_list(('cam1', 'cam2', 'camc', 'came'), margin='10px', width=w/3)
		self.dropDown = gui.DropDown.new_from_list(all_keys, margin='20px', width=w/2, \
			style = {'text-align':'center', "font-size":"30px"})
		self.dropDown.select_by_value('cam1')
		self.dropDown.attributes['title'] = 'select camera' # hover
		# pass label as parameter
		self.dropDown.onchange.do(self.on_drop, self.label)

		# command selection
		# left and rigth, combined in horizontal
		items = ('threshold' , 'timelapse', 'snapshot')
		self.listView1 = gui.ListView.new_from_list(items, width=w/3, margin='10px')
		self.listView1.attributes['title'] = 'select command'
		self.listView1.onselection.do(self.on_listview_command)
		subContainerLeft.append([self.listView1])

		items = ('read' , 'set')
		self.listView2 = gui.ListView.new_from_list(items, width=w/3, margin='10px')
		self.listView2.attributes['title'] = 'select action'
		self.listView2.onselection.do(self.on_listview_action)
		subContainerRight.append([self.listView2])


		horizontalContainer.append([subContainerLeft, subContainerRight])

		# slider for setting parameter
		# threshold. V1 cam is 5mega pixels, v2 is 8
		# default, min, max, steps  data in Kpixels
		# use a horizontal container to display label, then slider
		self.slider1_label = gui.Label('threshold (pixels)', width = w/3, margin = '10px', style={'text-align': 'left'})

		# if margin 10px and width =w, does not see it all
		self.slider1= gui.Slider(5000,0,100000,100, width = w, height=10, margin='0px')
		self.slider1.onchange.do(self.on_slider1)

		# pb if container is horizontal !!!! next widget is directly after, instead of new line
		self.t=gui.Container()
		self.t.append([self.slider1_label, self.slider1])

		# slider 2 is timelapse in sec
		self.slider2_label = gui.Label('timelapse (sec)', wigth = w/3, margin = '10px', style={'text-align': 'left'})

		self.slider2= gui.Slider(0,0,3600,1, width = w, height=10, margin='0px')
		self.slider2.onchange.do(self.on_slider2)

		self.l=gui.Container()
		self.l.append([self.slider2_label, self.slider2])


		# links
		# WARNING. not dynamic. change of cam with drop down does not change

		color = '#0000ff'
		wl = w/4

		# wan address must start with http, else will be front ended with local ip, port
		stream_url = all_cam_wan[cam] + ':' + data["cam_stream_port"]
		print ('link ', stream_url) 
		self.link1 = gui.Link(stream_url, "stream", open_new_window=True, width=wl, height=30, margin='10px', \
		style = { 'color' : color, 'font-weight' : 'bold', 'text-align' : 'center', 'font-size' : '20px'} )

		# modif in library
		print('updated library')

		self.link1.set_url('titi')
		print('get url ', self.link1.get_url())

		self.link1.set_url(stream_url)
		print('get url ', self.link1.get_url())

		web_url = all_cam_wan[cam] + ':' + data["cam_web_port"] + '/motion'
		print ('link ', web_url) 
		self.link2 = gui.Link(web_url, "gallery", width=wl, height=30, margin='10px', \
		style = { 'color' : color, 'font-weight' : 'bold', 'text-align' : 'center', 'font-size' : '20px'} )

		admin_url = all_cam_wan[cam] + ':' + data["cam_admin_port"]
		print ('link ', admin_url)
		self.link3 = gui.Link(admin_url, "admin", width=wl, height=30, margin='10px', \
		style = { 'color' : color, 'font-weight' : 'bold', 'text-align' : 'center', 'font-size' : '20px'} )

		monit_url = all_cam_wan[cam] + ':' + data["monit_admin_port"]
		print ('link ', monit_url)
		self.link4 = gui.Link(monit_url, "monit", width=wl, height=30, margin='10px', \
		style = { 'color' : color, 'font-weight' : 'bold', 'text-align' : 'center', 'font-size' : '20px'} )

		self.links=gui.Container()
		self.links.append([self.link1, self.link2, self.link3, self.link4])


		# label to print output
		self.label_output = gui.Label('output area', margin='10px', height=30, \
			style = { 'color' : self.colors['gray'], 'font-weight' : 'bold', 'text-align' : 'center', 'font-size' : '20px'} \
			)


		"""
		# use TextInput to get multiline. write with set_text or set_value
		# extensible
		# margin 0px text area is aligned with top widget. if w = 100% and margin 10px, text is cut on the rigth
		self.label_output = gui.TextInput(single_line=False, margin='0px', width = '100%', height = '20', \
		style = { 'color' : self.colors['gray'], 'text-align' : 'left', 'font-size' : '20px'} )
		"""


		############################################
		#  create top widget, vertical
		############################################

		# output not left align if placed after hrizontal. dont know why
		verticalContainer.append([\
			self.menubar, \
			self.label, \
			self.label_output, \
			self.dropDown, \
			horizontalContainer, \
			self.t, \
			self.l, \
			self.links, \
			self.label_output
			])

		# vertical is what is returned, root widget 



		"""
		self.button = gui.Button('Press!')
		# html
		self.button.attributes['title'] = 'please press me'
		self.button.style['color'] = 'red'
		# call back
		self.button.onclick.do(self.on_button,'you pressed')

		self.spin= gui.SpinBox(1,0,100, width = 50, height=50, margin='5px')
		self.spin.onchange.do(self.on_spin)
		"""

		# root widget
		return(verticalContainer)



	###################################
	# end of widget definition
	# call backs
	##################################


	def on_about(self,widget):
		self.label_output.set_text(version)



	def on_guide(self,widget):

		guide = "\
		\n- Use top drop-down menu to select camera.\
		\n- You can set or read 3 camera parameters.\
		\n- Threshold defines how many pixels need to change from one frame to the next to detect mouvement.\
		\n- Timelapse (in sec) defines how often pictures will be taken. Everyday a movie clip will be created with all those pictures.\
		\n- Snapshot (in sec) defines how often pictures will be taken. Pictures are available for your processing.\
		\n \
		\n- To read a parameter, select parameter on the left of the screen, and read on the rigth .\
		\n- To set a parameter, select parameter on the left of the screen, set one slider to desired value and select set on the rigth.\
		\n \
		\n- Select system menu to halt or reboot selected camera\
		\n- Select system menu to change password, or view existing password on selected camera\
		\n- Select system menu to restart GUI\
		\n\n\
		"

		# method 1 display on output widget
		#self.label_output.set_value(guide)



		"""
		# method 2 use InputDialog
		# issue, single line displayed, whatever the height 
		print('display guide. create InputDialog')
		# create InputDialog
		# 100% is entiere screen, not widget
		self.inputDialog = gui.InputDialog('quick guide', 'click', initial_value=guide, \
		width='100%', height = 400)
		self.inputDialog.confirm_value.do(self.guide)
		self.inputDialog.show(self)
		"""


		# method 3, generic dialog
		# display only using a label, but could get data from widgets created there

		# WARNING. seems cannoyt use NON input widget there, dialog will not show

		print('display guide. create GenericDialog')

		self.dialog = gui.GenericDialog(title= 'quick guide', message = 'click OK or cancel to return', \
		width=w, height = h)

		"""
		# can create input widgets
		self.dtextinput = gui.TextInput(width=200, height=30)
		self.dtextinput.set_value('Initial Text')
		# label is used in call back to get data
		self.dialog.add_field_with_label('dtextinput', 'Text Input', self.dtextinput)

		self.dcheck = gui.CheckBox(False, width=200, height=30)
		self.dialog.add_field_with_label('dcheck', 'Label Checkbox', self.dcheck)
		"""


		"""
		self.dlabel = gui.Label('test', width = 100, height = 100, \
		style = { 'color' : self.colors['x'], 'font-weight' : 'italic', 'text-align' : 'left', 'font-size' : '15px'})
		self.dialog.add_field_with_label('dlabel', 'Label', self.dlabel)
		"""

		# multiple lines to get nl
		self.dtextinput = gui.TextInput(width=w, height=300, single_line=False)
		# write guide
		self.dtextinput.set_value(guide)

		# 1st label is used in call back, 2nd is label displayed on the left
		#self.dialog.add_field_with_label('dtextinput', ' ', self.dtextinput)

		# I suspect only input widget can be used there
		# add without label to get more space
		self.dialog.add_field('dtextinput', self.dtextinput)


		# call back
		self.dialog.confirm_dialog.do(self.guide_confirm)

		print('show generic dialog')
		self.dialog.show(self)


	# get value from GenericDialog
	def guide_confirm(self, widget):
		print('guide input dialog confirmed')
		# just return to main, after displaying guide
		"""
		result = self.dialog.get_field('dtextinput').get_value()
		print(result)
		result = self.dialog.get_field('dcheck').get_value()
		print(result)
		"""

	def on_halt(self,widget):
		print('HALT')
		logging.info(str(datetime.datetime.now())+ ' HALT' )
		self.label_output.set_text('halting camera ' + cam)
		time.sleep(2)

		rpc='/home/pi/monit/rpc.sh ' + 'halt'
		print('rpc: ', rpc)
		remote = all_cam[cam]
		print('remote: ', remote)

		(_,_)=do_rpc(rpc,remote)


	def on_reboot(self,widget):
		print('REBOOT')
		logging.info(str(datetime.datetime.now())+ ' REBOOT' )
		self.label_output.set_text('rebooting camera ' + cam)
		time.sleep(2)

		rpc='/home/pi/monit/rpc.sh ' + 'reboot'
		print('rpc: ', rpc)
		remote = all_cam[cam]
		print('remote: ', remote)

		(_,_)=do_rpc(rpc,remote)

	# restart gui
	def on_gui(self,widget):
		print('GUI')
		logging.info(str(datetime.datetime.now())+ ' RESTART GUI' )
		self.label_output.set_text('restarting gui')
		time.sleep(2)

		print('restart GUI')
		os.system('sudo systemctl restart remi.service')

	# called by menu
	# change password for camera, ie for monit, motion and gallery
	def on_passwd(self,widget):
		print('change camera password. create InputDialog')
		# create InputDialog
		self.inputDialog = gui.InputDialog('change current camera password', 'new password?', initial_value='type here',width=w)
		self.inputDialog.confirm_value.do(self.passwd)
		self.inputDialog.show(self)

	# called by menu
	# change password for GUI
	# run locally where GUI runs
	def on_gui_passwd(self,widget):
		print('change GUI password. create InputDialog')
		# create InputDialog
		self.inputDialog = gui.InputDialog('change gui password', 'new password?', initial_value='type here',width=w)
		self.inputDialog.confirm_value.do(self.passwd1)
		self.inputDialog.show(self)


	# call back when password input dialog completed
	# for remi only
	def passwd1(self, widget, value):
		print('gui passwd input dialog confirmed ', value)
		logging.info(str(datetime.datetime.now())+ ' remi change password %s' %value)
		self.label_output.set_text('setting new gui password to %s ' %(value))

		# execute local script /home/pi/remi/remi_passwd.sh change titi
		process = subprocess.run(["/home/pi/remi/remi_passwd.sh", "change", value], check=True, stdout=subprocess.PIPE)

		print('subprocess has ran ', process.returncode, process.stdout)

		#subprocess has ran  0 b'GUI: titi\n'
		s = process.stdout.decode(encoding='UTF-8')

		# do not use + to build string for set_text !!!!!!

		if process.returncode == 0:
			print('updating label. OK')
			self.label_output.set_text("%s. now restart gui" %s)
		else:
			print('updating label. NOK')
			self.label_output.set_text('error %s: ' % process.stderr)


	# call back when password input dialog completed
	# for monit, motion and gallery
	def passwd(self, widget, value):
		print('camera passwd input dialog confirmed ', value)
		logging.info(str(datetime.datetime.now())+ ' RPC camera change password %s' %value)
		self.label_output.set_text('setting new camera password for %s to %s ' %(cam, value))

		if value == 'camera38':
			# mess sed
			self.label_output.set_text('cannot use camera38 as password')
			print('cannot use camera38 as password')
			return

		# update password on current camera
		# only for monit, motion and gallery
		rpc='/home/pi/monit/rpc.sh ' + 'password' + ' ' + value
		print('rpc: ', rpc)
		remote = all_cam[cam] # local IP
		print('remote local IP : ', remote)

		# stdout is echo from rpc.sh
		(result, stdout) = do_rpc(rpc,remote)

		print('RPC returned ', result)
		if result:
			self.label_output.set_text('OK: ' + stdout )
			print('changed passwd OK')
			logging.info(str(datetime.datetime.now())+ ' RPC change password OK')
		else:
			self.label_output.set_text('error changing password')
			print('changed passwd NOK')
			logging.error(str(datetime.datetime.now())+ ' RPC change password NOK')

		time.sleep(5)


	# only for monit, motion and gallery
	def on_view_passwd(self,widget):
		rpc='/home/pi/monit/rpc.sh ' + 'view_password'
		print('rpc: ', rpc)
		remote = all_cam[cam] # local IP
		print('remote local IP : ', remote)
		logging.info(str(datetime.datetime.now())+ ' RPC view password')


		# stdout is echo from rpc.sh
		(result, stdout) = do_rpc(rpc,remote)

		print('RPC returned ', result)
		if result:
			self.label_output.set_text('OK: ' + stdout)
			print('view passwd OK')
			logging.info(str(datetime.datetime.now())+ ' RPC view  password OK')
		else:
			self.label_output.set_text('error viewing password')
			print('view passwd NOK')
			logging.error(str(datetime.datetime.now())+ ' RPC view password NOK')

	"""
	def on_button(self, widget, param1 = ''): self.button.set_text('ok')
		self.label_output.set_value(guide)		# widget is button pressed

	def on_spin(self, widget, value):
		print('spin: ', value)
	"""

	def on_drop(self, widget, value, label):
		global cam
		print('camera selection drop down: ', value)
		cam = value # set global value, key in dict
		label.set_text(title + value) # update title

		# update url links
		# WARNING: need updated gui.py with new set_url
		print('update link url'
)
		stream_url = all_cam_wan[cam] + ':' + data["cam_stream_port"]
		self.link1.set_url(stream_url)

		web_url = all_cam_wan[cam] + ':' + data["cam_web_port"] + '/motion'
		self.link2.set_url(web_url)

		admin_url = all_cam_wan[cam] + ':' + data["cam_admin_port"]
		self.link3.set_url(admin_url)

		monit_url = all_cam_wan[cam] + ':' + data["monit_admin_port"]
		self.link4.set_url(monit_url)


	# set global values

	def on_slider1(self, widget, value):
		global slider1_value
		print('slider1: ' , str(value))
		slider1_value = int(value)
		# is a % of 10% of 5 Mega pixles
		slider1_value = int(slider1_value)
		self.label_output.set_text('pixels (of 5 mega): ' + str(slider1_value))

	def on_slider2(self, widget, value):
		global slider2_value
		print('slider2: ' , str(value))
		slider2_value = int(value)
		self.label_output.set_text('second: ' + str(slider2_value))


	def on_listview_command (self, widget, key):
		# param is a key
		global command
		command  = widget.children[key].get_text()
		print ('listview command: ', command)


	# listview  triggers RPC,  read or set

	def on_listview_action (self, widget, key):
		# param is a key

		action  = self.listView2.children[key].get_text()
		print ('listview action: ', action)

		s = 'action. cam: %s. command: %s. action: %s. s1: %d. s2: %d.' %(cam, command, action, slider1_value, slider2_value)
		print(s)
		logging.info(str(datetime.datetime.now())+ s )

		# rpc.sh expect read_timelapse etc ..  read is action  timelapse is command
		if action in ['read']:
			# get the data with RPC

			rpc='/home/pi/monit/rpc.sh ' + action + '_' + command + ' '
			print('rpc: ', rpc)
			remote = all_cam[cam]
			print('remote: ', remote)

			# data is either stdout if OK , or ret code
			(result,data) = do_rpc(rpc,remote)
			print('RPC returned ', result)
			if result:
				self.label_output.set_text('OK: ' + data)
			else:
				self.label_output.set_text('ERROR: ' + data)


		elif action == 'set':

			# need to read one slider or the other, based on drop down
			if command == 'threshold':
				param = slider1_value
			else:
				param = slider2_value

			rpc='/home/pi/monit/rpc.sh ' + action + '_' + command + ' ' + str(param)
			print('rpc: ', rpc)
			remote = all_cam[cam]
			print('remote: ', remote)
			logging.info(str(datetime.datetime.now())+ ' %s %s' %(rpc,remote) )

			(result,data) = do_rpc(rpc,remote)
			print('RPC returned ', result)
			if result:
				self.label_output.set_text('OK: ' +  data)
			else:
				self.label_output.set_text('ERROR: ' + data)

		else:
			print('bad command ', action)
			logging.error(str(datetime.datetime.now())+ ' bad action: %s' %(command) )



print('start remi GUI')

try:
#	start(remi_app, username='meaudre', password='camera', address='0.0.0.0', port=5010, multiple_instance=False, enable_file_cache=True, update_interval=0.1, start_browser=True, standalone=False)
	start(remi_app, username=data['user'], password=data['passwd'], address='0.0.0.0', port=int(data['remi_port_lan']), multiple_instance=True, enable_file_cache=True, update_interval=0.1, start_browser=True, standalone=False)
except Exception as e:
	print('Exception starting remi: ', str(e))
	logging.error(str(datetime.datetime.now())+ ' error staring remi: %s' %str(e) )
