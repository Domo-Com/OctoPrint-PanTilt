#!/usr/bin/env python
# -*- coding: utf-8 -*-

from time import sleep
import RPi.GPIO as GPIO
from thread import start_new_thread
from threading import Thread
import threading
import sys
import json
import os
import urlparse
import urllib
import ConfigParser
import urllib2
import json
import os
import sys
import time 
import optparse
import shutil
import time

class Motor(object):
	def __init__(self, pins):
		self.P1 = pins[0]
		self.P2 = pins[1]
		self.P3 = pins[2]
		self.P4 = pins[3]
		self.deg_per_step = 5.625 / 64
		self.steps_per_rev = int(360 / self.deg_per_step)  # 4096
		self.step_angle = 0  # Assume the way it is pointing is zero degrees
		self.angletohome=0
		self._stopevent = threading.Event()
		self.limstate=True
		GPIO.setup(18, GPIO.IN, pull_up_down=GPIO.PUD_UP)
		for p in pins:
			GPIO.setup(p, GPIO.OUT)
			GPIO.output(p, 0)
			
	def __exit__(self, type, value, traceback):
		self.clean_pins_up()
	   
	def _set_rpm(self, rpm):
		print "rpm set"
		#Set the turn speed in RPM.
		self._rpm = rpm
		# T is the amount of time to stop between signals
		self._T = (60.0 / rpm) / self.steps_per_rev
	# This means you can set "rpm" as if it is an attribute and
	# behind the scenes it sets the _T attribute
	rpm = property(lambda self: self._rpm, _set_rpm)
		
	def clean_pins_up(self):
		GPIO.output(self.P1, 0)
		GPIO.output(self.P2, 0)
		GPIO.output(self.P3, 0)
		GPIO.output(self.P4, 0)
	
	def checkstop(self):
		self.limstate = GPIO.input(18)
		if self.limstate == False: 
			print('Button Pressed...')
			return True
			
	def stop(self, timeout=None):
		""" Stop the thread. """
		self._stopevent.set( )
		threading.Thread.join(timeout)
		
	def move_to(self, angle):

		target_step_angle = 8 * (int(angle / self.deg_per_step) / 8)
		print(target_step_angle)
		steps = abs(target_step_angle - self.step_angle)
		steps = (steps % self.steps_per_rev)
		print("moving  steps %s target %s angle %s"  %(steps,target_step_angle, angle))
		if angle<0:
			#steps -= self.steps_per_rev
			self._move_acw(steps)
		else:
			self._move_cw(steps)
		
		self.step_angle = 0
		
		return
		
		if steps > self.steps_per_rev / 2:
			steps -= self.steps_per_rev
			
			self._move_acw(-steps / 8)
		else:
			print "moving " + `steps` + " steps"
			self._move_cw(steps / 8)
		#self.step_angle = target_step_angle #in case you want to keep track of the position
		self.step_angle = 0
		self.angletohome-=target_step_angle
		
		
	def _move_acw(self, big_steps):
		self.clean_pins_up()
		for i in range(big_steps+1):
			if self.checkstop():
				return
			#print i
			GPIO.output(self.P1, 0)
			sleep(self._T)
			GPIO.output(self.P3, 1)
			sleep(self._T)
			GPIO.output(self.P4, 0)
			sleep(self._T)
			GPIO.output(self.P2, 1)
			sleep(self._T)
			GPIO.output(self.P3, 0)
			sleep(self._T)
			GPIO.output(self.P1, 1)
			sleep(self._T)
			GPIO.output(self.P2, 0)
			sleep(self._T)
			GPIO.output(self.P4, 1)
			sleep(self._T)
			
		self.clean_pins_up()
		
	def _move_cw(self, big_steps):
		self.clean_pins_up()
		for i in range(big_steps+1):
			if self.checkstop():
				return
			GPIO.output(self.P3, 0)
			sleep(self._T)
			GPIO.output(self.P1, 1)
			sleep(self._T)
			GPIO.output(self.P4, 0)
			sleep(self._T)
			GPIO.output(self.P2, 1)
			sleep(self._T)
			GPIO.output(self.P1, 0)
			sleep(self._T)
			GPIO.output(self.P3, 1)
			sleep(self._T)
			GPIO.output(self.P2, 0)
			sleep(self._T)
			GPIO.output(self.P4, 1)
			sleep(self._T)
		self.clean_pins_up()

def initmotor(rpm,rot1,rot2):
	GPIO.cleanup()
	GPIO.setmode(GPIO.BCM)
	m_l = Motor([17,22,23,24])
	m_r = Motor([5,6,13,19])
	m_l.rpm = float(rpm)
	m_r.rpm = float(rpm)
	print "Pause in seconds: " + `m_l._T`
	try:
		t1 = Thread(None,m_l.move_to,None,(int(rot1),))
		t2 = Thread(None,m_r.move_to,None,(int(rot2),))
		t1.start()
		t2.start()
		t1.join()
		t2.join()
	except Exception as errtxt:
		print errtxt
			
	GPIO.cleanup()


parser = optparse.OptionParser("ExecCmd.py [options] cmdline")
parser.add_option("-r", "--rpm", type="string", dest="rpm",default="0")
parser.add_option("-a", "--rota", type="string", dest="rota",default="0")
parser.add_option("-b", "--rotb", type="string", dest="rotb",default="0")
parser.add_option("-t", "--home", type="string", dest="home",default="0")
parser.add_option("-v", "--auto", type="string", dest="auto",default="0")
(options, args) = parser.parse_args()
	
#cmdline = args[0]
if options.home:
	home=1
else:
	home=0

if options.auto:
	autopan=int(options.auto)
else:
	autopan=0

if options.rpm:
	rpm = int(options.rpm)
else:
	rpm=0

if options.rota:
	rota = int(options.rota)
else:
	rota=0

if options.rotb:
	rotb = int(options.rotb)
else:
	rotb=0
	
GPIO.cleanup()
GPIO.setmode(GPIO.BCM)

m_l = Motor([4,17,23,24])
m_r = Motor([5,6,13,19])
m_l.rpm = float(rpm)
m_r.rpm = float(rpm)
print "Pause in seconds: " + `m_l._T`
curdir=os.path.dirname(os.path.realpath(__file__))
print curdir
try:
	if autopan==1:
		halfpan=480
		t1 = Thread(None,m_l.move_to,None,(int(-halfpan),))
		t1.start()
		t1.join()
		i=0
		sign=2
		while 1:
			t1 = Thread(None,m_l.move_to,None,(int(sign*halfpan),))
			t1.start()
			t1.join()
			sign=-1*sign
			if os.path.isfile(curdir+"/stoptravel.lis"):
				print("Stop auto travel required")
				t1 = Thread(None,m_l.move_to,None,(int(sign*halfpan/abs(sign)),))
				t1.start()
				t1.join()
				os.remove(curdir+"/stoptravel.lis")
				sys.exit(0)
			
	else:
		t1 = Thread(None,m_l.move_to,None,(int(rota),))
		t2 = Thread(None,m_r.move_to,None,(int(rotb),))
		t1.start()
		t2.start()
		t1.join()
		t2.join()
		
except Exception as errtxt:
	print errtxt
		
GPIO.cleanup()
print json.dumps("ok")


