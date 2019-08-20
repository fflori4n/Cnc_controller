#!/usr/bin/env python
import gi
import sys
import time
import math
import serial
import sys
import re
#import threading, Queue

gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GObject
from multiprocessing import (Process, Queue, freeze_support)

class color:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'

Xpos = -2
Ypos = -10
Zpos = -20

status = ''
FEED = -1

com_queue = Queue()														#queue for com between main, and GUI
buttonq = Queue()

rRun = False
pPaused = False
sStep = False

counter = 0
count = 0
ardconnected = True

ProgC = -1
idlecounter = 0

def GUIthread(com_queue):

	def refresh(com_queue):
		try:
			Xdisp, Ydisp, Zdisp, status, FEED = com_queue.get(True, 0.05)
		except:
			return True
	
		Xlabel.set_text("X  " + str(int(Xdisp)).zfill(4) + str(abs(round(Xdisp, 4) % 1))[1:].ljust(4, '0'))
		Ylabel.set_text("Y  " + str(int(Ydisp)).zfill(4) + str(abs(round(Ydisp, 4) % 1))[1:].ljust(4, '0'))
		Zlabel.set_text("Z  " + str(int(Zdisp)).zfill(4) + str(abs(round(Zdisp, 4) % 1))[1:].ljust(4, '0'))

		statlabel.set_text('STATUS: ' + str(status))
		feedlabel.set_text('F ' + str(FEED).zfill(4))
		if FEED == -99:
			return False
		return True

	GObject.timeout_add(100,refresh,com_queue)									# update display every x ms, very ineficient but simple

	class drawGUI:
		def __init__(self):
			global CMDbox, Xlabel, Ylabel, Zlabel, statlabel, feedlabel
			builder = Gtk.Builder()
			builder.add_from_file("cnccontrolergui.glade")
			builder.connect_signals(Handler())

			window = builder.get_object("window1")
			CMDbox = builder.get_object('CMDtextbox')

			Xlabel = builder.get_object('Xdisp')
			Ylabel = builder.get_object('Ydisp')
			Zlabel = builder.get_object('Zdisp')

			statlabel = builder.get_object('status')
			feedlabel = builder.get_object('feed_disp')

			window.show_all()
		
	class Handler:
		def __init__(self):
			pass
		def onDestroy(self, *args):
			buttonq.put('EXIT',False)
			Gtk.main_quit()
			sys.exit(0)
		def Run_btn_toggled_cb(self, *args):
			buttonq.put('RUN',False)
		def on_Pause_btn_toggled(self, *args):
			buttonq.put('PAUSE',False)
		def on_Step_btn_toggled(self, *args):
			buttonq.put('STEP',False)
		def on_up_btn_clicked(self, *args):
			buttonq.put('UP',False)
		def on_Down_btn_clicked(self, *args):
			buttonq.put('DOWN',False)
		def on_EXEC_clicked(self, *args):
			msg2send = CMDbox.get_text()
			buttonq.put('EXEC ' + msg2send,False)
		def on_feed_inc(self, *args):
			buttonq.put('INCFEED',False)
		def on_feed_dec(self, *args):
			buttonq.put('DECFEED',False)
		def on_home(self, *args):
			buttonq.put('HOME',False)
		def on_p0_clk(self, *args):
			buttonq.put('P0',False)
		def on_p1_clk(self, *args):
			buttonq.put('P1',False)
		def cycle_btn_clicked_cb(self, *args):
			buttonq.put('CYCLE',False)
		def Feed_hold_clicked_cb(self, *args):
			buttonq.put('FDHLD',False)
		def RST_clicked_cb(self, *args):
			buttonq.put('RST',False)
		
	drawGUI()
	Gtk.main()


p1 = Process(target=GUIthread,args=(com_queue,))
p1.start()

def send2refresh():
	# get position from controller
	com_queue.put([Xpos,Ypos,Zpos,status,FEED],False)

def send_cmd(line):
	global ardconnected, rRun, ProgC, idlecounter

	#if 'Idle' in status:
	#	updatepos()
	#	idlecounter = idlecounter + 1
	#if idlecounter < 3:
	#	return False

	#idlecounter = 0
	ProgC = ProgC + 1

	print 'sending:',line
	#ser.flushInput()
	ser.write(line + '\n\r')

	EXT = False
	while(not(EXT)):
		try:
			reply = ser.read(ser.inWaiting())
		except:
			pass

		if reply.find('<') > -1:
			#print 'start'
			if reply.find('>') > -1:
				reply = reply[reply.find('<'):reply.find('>')]
				reply = reply[reply.find('ok') + len('ok'):]
				reply = reply[reply.find('ok') + len('ok'):]
			else:
				reply = reply[:reply.find('<')]
		if reply.find('>') > -1:
			reply = reply[reply.find('ok') + len('ok'):]
			reply = reply[reply.find('ok') + len('ok'):]
			
		if ('error' in reply) or ('ALARM:' in reply) or ('unlock' in reply or 'error:9' in reply):
			rRun = False
			if ('error' in reply):
				print color.WARNING,'>:',reply,color.ENDC
				return False
			elif 'ALARM:' in reply:
				print color.FAIL,'>:',reply,color.ENDC
				return False
			elif 'unlock' in reply or 'error:9' in reply:
				print color.WARNING,'>:','MACHINE IS LOCKED !',color.ENDC
		elif 'ok' in reply:
			print color.OKGREEN,'>:',reply,color.ENDC
			EXT = True

	return True
def send_im(line):
	global ardconnected, rRun, ProgC, idlecounter
	#ser.flushInput()
	ser.write(line + '\n\r')

	
def updatepos():
	global status, Xpos, Ypos, Zpos, FEED
	ser.write('?\n\r')
	time.sleep(.02)
	try:
		reply = ser.readline()
	except:
		return
	if reply.find('<') > -1 and reply.find('>') > -1:
		reply = reply[reply.find('<') + 1 : reply.find('>')]
	else:
		return
	try:
		info= reply.split("|")
		status = info[0]
	
		#if counter > 15:
		reply = info[1]
		reply = reply[reply.find('MPos:') + len('MPos:'):]
		Coords = reply.split(',')
		if len(Coords) >= 3:
			print 'update dem numbers'
			Xpos = float(Coords[0])
			Ypos = float(Coords[1])
			Zpos = float(Coords[2])
		if len(info) >= 4:
			reply = info[3]
			reply = reply[reply.find('Ov:') + len('Ov:'):reply.find(',')]
			FEED = float(reply)
			#counter = 0
		#else:
			#counter = counter +1		
	except:
		pass		# !!!
	

def chk_buttons():
	global rRun, pPaused, sStep

	try:
		button = buttonq.get(True, 0.05)
	except:
		return

	if 'RUN' in button:
		rRun = not(rRun)
		print rRun
	elif 'PAUSE' in button:
		pPaused = not(pPaused)
		print pPaused
	elif 'STEP' in button:
		sStep = not(sStep)
		print 'step'
	elif 'UP' in button:
		print 'UP'
	elif 'DOWN' in button:
		print 'Down'
	elif 'EXEC' in button:
		button = button[button.find(' ') + 1:]
		print button
		if len(str(button)) > 0:
			send_im(button)
		else:
			send_im(lines[ProgC])
	elif 'EXIT' in button:
		sys.exit(0)		
	elif 'INCFEED' in button:
			send_im(str(0x91))
	elif 'DECFEED' in button:
			send_im(str(0x92))
	elif 'CYCLE' in button:
			send_im('~')
	elif 'FDHLD' in button:
			send_im('!')
	elif 'RST' in button:
			if not(rRun):
				send_im(str(0x18))
	elif 'P0' in button:
			if not(rRun):
				send_im("X0 y250")
	elif 'P1' in button:
			if not(rRun):
				send_im("X100 y250")
	elif 'HOME' in button:
			if not(rRun):
				send_im('$h')
	else:
		print 'error'
		
def init_serial():
	global ser

	ardconnected = True									# for testig without contoller connected
	serstring = ['/dev/ttyUSB0','/dev/ttyUSB1','/dev/ttyUSB2']

	if len(sys.argv) < 2:
			print ' Usage: ./Cncgcodereader gcodefile.ngc [ -ioc]'
			exit(0)

	print 'Waiting for serial...'
	if ardconnected:
		i = 0
		waiting4ser = True
		while waiting4ser:

			i = i + 1
			time.sleep(0.2)
			if i >= 3:
				i = 0
			try:
				print serstring[i] + "\n"
				ser = serial.Serial(serstring[i], 9600)
				waiting4ser = False
				print 'Serial Connected\n'
			except:
				pass
		
def chkrdy():
	global ser, count, status

	try:
		reply = ser.read(ser.inWaiting())
	except:
		pass

	if reply.count('ok') >= 2:	# 2
		ser.flushInput()
		count = 0
		return True
	
	if count >= 200:				# backup refresh
		updatepos()
		send2refresh()
		count = 0
		if 'Idle' in status:
			time.sleep(.02)
			ser.flushInput()
			return True
	else:
		count = count + 1

	return False
# main

init_serial()
gcode = open(sys.argv[1].strip()).read()
lines = gcode.splitlines()

try:
	while True:
		if ProgC >= len(lines):
			print 'END OF GCODE'
			sys.exit(0)

		if rRun and not(pPaused) and not(sStep):
			if chkrdy():
				updatepos()
				send_cmd(lines[ProgC])
				send2refresh()
			
		chk_buttons()
		time.sleep(0.05)
except (KeyboardInterrupt, SystemExit):
	com_queue.put([Xpos,Ypos,Zpos,status,-99],False)
	time.sleep(0.1)
	p1.terminate()
	print "Keyboard interrupt. SYS EXT 0"
	sys.exit(0)


	




#1 	G-code words consist of a letter and a value. Letter was not found.
#2 	Numeric value format is not valid or missing an expected value.
#3 	Grbl '$' system command was not recognized or supported.
#4 	Negative value received for an expected positive value.
#5 	Homing cycle is not enabled via settings.
#6 	Minimum step pulse time must be greater than 3usec
#7 	EEPROM read failed. Reset and restored to default values.
#8 	Grbl '$' command cannot be used unless Grbl is IDLE. Ensures smooth operation during a job.
#9 	G-code locked out during alarm or jog state
#10 	Soft limits cannot be enabled without homing also enabled.
#11 	Max characters per line exceeded. Line was not processed and executed.
#12 	(Compile Option) Grbl '$' setting value exceeds the maximum step rate supported.
#13 	Safety door detected as opened and door state initiated.
#14 	(Grbl-Mega Only) Build info or startup line exceeded EEPROM line length limit.
#15 	Jog target exceeds machine travel. Command ignored.
#16 	Jog command with no '=' or contains prohibited g-code.
#17 	Laser mode requires PWM output.
#20 	Unsupported or invalid g-code command found in block.
#21 	More than one g-code command from same modal group found in block.
#22 	Feed rate has not yet been set or is undefined.
#23 	G-code command in block requires an integer value.
#24 	Two G-code commands that both require the use of the XYZ axis words were detected in the block.
#25 	A G-code word was repeated in the block.
#26 	A G-code command implicitly or explicitly requires XYZ axis words in the block, but none were detected.
#27 	N line number value is not within the valid range of 1 - 9,999,999.
#28 	A G-code command was sent, but is missing some required P or L value words in the line.
#29 	Grbl supports six work coordinate systems G54-G59. G59.1, G59.2, and G59.3 are not supported.
#30 	The G53 G-code command requires either a G0 seek or G1 feed motion mode to be active. A different motion was active.
#31 	There are unused axis words in the block and G80 motion mode cancel is active.
#32 	A G2 or G3 arc was commanded but there are no XYZ axis words in the selected plane to trace the arc.
#33 	The motion command has an invalid target. G2, G3, and G38.2 generates this error, if the arc is impossible to generate or if the probe target is the current position.
#34 	A G2 or G3 arc, traced with the radius definition, had a mathematical error when computing the arc geometry. Try either breaking up the arc into semi-circles or quadrants, or redefine them with the arc offset definition.
#35 	A G2 or G3 arc, traced with the offset definition, is missing the IJK offset word in the selected plane to trace the arc.
#36 	There are unused, leftover G-code words that aren't used by any command in the block.
#37 	The G43.1 dynamic tool length offset command cannot apply an offset to an axis other than its configured axis. The Grbl default axis is the Z-axis.
#38 	Tool number greater than max supported value.
