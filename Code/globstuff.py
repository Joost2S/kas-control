#!/usr/bin/python3
 
# Author: J. Saarloos
# v0.8.17	09-02-2018


from abc import ABCMeta, abstractmethod
import datetime
import logging
import os
import RPi.GPIO as GPIO
import subprocess
import sys
import threading
import time

import mcp23017

		
class sigLED(object):
	"""This object is for controlling the status LED."""

	# GPIO pin
	@property
	def pin(self):
		return(self.__pin)
	@pin.setter
	def pin(self, pin):
		self.__pin = pin
	# interval
	@property
	def interval(self):
		return(self.__interval)
	@interval.setter
	def interval(self, interval):
		self.__interval = interval
	# enabled
	@property
	def enabled(self):
		return(self.__enabled)
	@enabled.setter
	def enabled(self, enabled):
		self.__enabled = enabled

	def __init__(self, pin):
		self.pin = pin
		self.interval = 0.5
		self.enabled = True
		GPIO.setup(pin, GPIO.OUT)
		GPIO.output(pin, GPIO.LOW)

	def blinkSlow(self, i):
		for j in range(0, i):
			self.on()
			time.sleep(self.interval * 2)
			self.off()
			time.sleep(self.interval * 2)
			
	def blinkFast(self, i):
		for j in range(0, i):
			self.on()
			time.sleep(self.interval / 2)
			self.off()
			time.sleep(self.interval / 2)

	def disable(self):
		self.enabled = False
		self.off()

	def on(self):
		if (self.enabled):
			GPIO.output(self.pin, GPIO.HIGH)

	def off(self):
		GPIO.output(self.pin, GPIO.LOW)

	
class floatUp(object):
	"""Object for handeling a low water level."""

	# low_water
	@property
	def low_water(self):
		return(self.__low_water)
	@low_water.setter
	def low_water(self, low_water):
		self.__low_water = low_water
	# float_switch
	@property
	def float_switch(self):
		return(self.__float_switch)
	@float_switch.setter
	def float_switch(self, float_switch):
		self.__float_switch = float_switch
	# sLED
	@property
	def sLED(self):
		return(self.__sLED)
	@sLED.setter
	def sLED(self, sLED):
		self.__sLED = sLED
	# pump
	@property
	def pump(self):
		return(self.__pump)
	@pump.setter
	def pump(self, pump):
		self.__pump = pump

	def __init__(self, float_switch, pump, sLED = None):
		self.low_water = False
		self.float_switch = float_switch
		self.sLED = sLED
		self.pump = pump
		self.lastMailSent = 0
		GPIO.setup(self.float_switch, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
		GPIO.add_event_detect(self.float_switch, GPIO.RISING, callback=(self.lwstart), bouncetime=1000)
		if (self.getStatus()):
			self.lwstart()
		

	def getStatus(self):
		"""\t\tChecks and returns the current status of the float switch.
		True if low water, False if enough water."""

		return(GPIO.input(self.float_switch))
	
	def lwstart(self, mail = False):
		"""If low water level is detected, run this to disable pumping and send an email to user."""

		if (GPIO.input(self.float_switch)):
			self.low_water = True
			logging.info("Low water status: " + str(self.low_water))
			self.pump.disable()

			#	Start level checking and alarm LED.
			blink = lowWater(globstuff.getThreadNr(), "water level check")
			blink.start()
			globstuff.draadjes.append(blink)

			if (mail):
				# prevent sending mails too often.
				if (not (time.time() - self.lastMailSent) < 10800):
					#	Send an email to alert user.
					self.lastMailSent = time.time()
					fromaddr = ""
					toaddr  = ""
					subject = "Laag water"
					text = "Er is te weinig water in de regenton. Automatische bewatering is gestopt tot de regenton verder is gevuld"
					date = datetime.datetime.now().strftime( "%d/%m/%Y %H:%M" )
					msg = ("From: %s\nTo: %s\nSubject: %s\nDate: %s\n\n%s" % ( fromaddr, toaddr, subject, date, text ))

					# Credentials
					username = fromaddr
					password = ""

					# The actual mail send
					server = smtplib.SMTP("smtp.gmail.com:587")
					server.starttls()
					server.login(username, password)
					server.sendmail(fromaddr, toaddr, msg)
					server.quit()
					logging.debug("Sent mail to " + toaddr)
					
	def check_level(self):
		"""\t\tRun as seperate thread when a low water level situation occurs.
		Will self terminate when the water level is high enough again."""

		while(self.low_water):
			input_state = self.getStatus()
			self.sLED.blinkFast(5)
			if (not input_state and not globstuff.running):
				self.low_water = False


class protoThread(threading.Thread):
	"""Use this to create new threads."""

	__metaclass__ = ABCMeta

	# threadID
	@property
	def threadID(self):
		return(self.__threadID)
	@threadID.setter
	def threadID(self, threadID):
		self.__threadID = threadID
	# name
	@property
	def name(self):
		return(self.__name)
	@name.setter
	def name(self, name):
		self.__name = name
	# args
	@property
	def args(self):
		return(self.__args)
	@args.setter
	def args(self, args):
		self.__args = args

	def __init__(self, threadID, name, args = None):
		threading.Thread.__init__(self)
		self.threadID = threadID
		self.name = name
		self.args = args

	@abstractmethod
	def run(self):
		pass


class lowWater(protoThread):

	def run(self):
		logging.info("Starting thread{0}: {1}".format(self.threadID, self.name))
		globstuff.fltdev.check_level()
		logging.info("Exiting thread{0}: {1}".format(self.threadID, self.name))
		

class Pump(object):
	"""Object encompassing the pump and all valves."""
	
	# enabled
	@property
	def enabled(self):
		return(self.__enabled)
	@enabled.setter
	def enabled(self, enabled):
		self.__enabled = enabled	  
	# startTime
	@property
	def startTime(self):
		return(self.__startTime)
	@startTime.setter
	def startTime(self, startTime):
		self.__startTime = startTime	  
	# pumpPin
	@property
	def pumpPin(self):
		return(self.__pumpPin)
	@pumpPin.setter
	def pumpPin(self, pumpPin):
		self.__pumpPin = pumpPin	  
	# isPumping
	@property
	def isPumping(self):
		return(self.__isPumping)
	@isPumping.setter
	def isPumping(self, isPumping):
		self.__isPumping = isPumping	  
	# sLED
	@property
	def sLED(self):
		return(self.__sLED)
	@sLED.setter
	def sLED(self, sLED):
		self.__sLED = sLED	  
	# channels
	@property
	def channels(self):
		return(self.__channels)
	@channels.setter
	def channels(self, channels):
		self.__channels = channels

	#channels = {
	#chan : (valvepin, active)
	#2 : (1B0, False) }
	power = 560

	def __init__(self, pin, sLED = None):
		self.startTime = None
		self.pumpPin = pin
		self.isPumping = False
		self.sLED = sLED
		self.enabled = False
		self.channels = {}

	def setChannel(self, channel, pin):
		"""Use this to set a channel for pumping."""

		self.channels[channel] = [pin, False]

	def waterChannel(self, group, t):
		"""\t\tWill pump water to the selected channel when possible.
		Time in sec."""

		if (group.chan in self.channels):
			if (self.enabled):
				self.channels[group.chan][1] = True
				self.__valveOn(group.chan)
				if (not self.isPumping):
					time.sleep(0.1)
					self.__pumpOn()
				for i in range(t):
					if (not self.enabled or not group.connected):
						break
					else:
						time.sleep(1)
				self.channels[group.chan][1] = False
				time.sleep(0.01)
				pumping = False
				for chan in self.channels.values():
					if (chan[1]):
						pumping = True
				if (not pumping):
					self.__pumpOff()
					time.sleep(0.1)
				self.__valveOff(group.chan)

	def disable(self):
		"""Disables the ability to pump."""

		print("Pump disabled.")
		self.enabled = False
		self.__pumpOff()
		time.sleep(0.1)
		for chan in self.channels.keys():
			self.__valveOff(chan)

	def enable(self):
		"""Re-enable pumping ability."""

		if (not globstuff.testmode):
			self.enabled = True

	def demo(self, groups, t):
		"""When in testmode, you can test the watering hardware."""

		if (globstuff.testmode):
			for g in groups:
				self.__valveOn(g.chan)
			time.sleep(0.1)
			self.__pumpOn()
			time.sleep(t)
			self.__pumpOff()
			time.sleep(0.1)
			for g in groups:
				self.__valveOff(g.chan)
			time.sleep(0.8)
			for g in groups:
				self.__valveOn(g.chan)
				time.sleep(0.1)
				self.__pumpOn()
				time.sleep(t)
				self.__pumpOff()
				time.sleep(0.1)
				self.__valveOff(g.chan)
				time.sleep(1.2)

	def on(self):
		"""Turn the pump on."""
		
		if (self.enabled):
			logging.info("Pump turned on.")
			self.isPumping = True
			if (self.sLED is not None):
				self.sLED.on()
			self.startTime = time.time()
			globstuff.getPinDev(self.pumpPin).output(globstuff.getPinNr(self.pumpPin), True)

	def __pumpOff(self):
		"""Turn the pump off."""

		self.isPumping = False
		if (self.sLED is not None):
			self.sLED.off()
			
		globstuff.getPinDev(self.pumpPin).output(globstuff.getPinNr(self.pumpPin), False)
		if (self.startTime is not None):
			logging.info("Pump turned off. Pumped for " + str(round(time.time() - self.startTime, 2)) + " seconds.")
			self.startTime = None

	def __valveOn(self, chan):
		"""Turn on a valve."""

		self.channels[chan][1] = True
		globstuff.getPinDev(self.channels[chan][0]).output(globstuff.getPinNr(self.channels[chan][0]), True)
		
	def __valveOff(self, chan):
		"""Turn off a valve."""

		if (self.__isInt(chan)):
			chan = (chan,)

		for c in chan:
			self.channels[c][1] = False
			globstuff.getPinDev(self.channels[c][0]).output(globstuff.getPinNr(self.channels[c][0]), False)

	def __isInt(self, obj):
		try:
			blah = int(obj)
		except:
			return(False)
		return(True)


class fan(object):

	__mcp = None
	__pin = ""
	__state = False

	def __init(self, pin):
		
		if (globstuff.getPinDev(pin).setPin(globstuff.getPinNr(pin))):
			self.__mcp = globstuff.getPinDev(pin)
			self.__pin = globstuff.getPinNr(pin)


	def on(self):
		self.__mcp.output(self.__pin, True)

	def off(self):
		self.__mcp.output(self.__pin, False)


class globstuff:

	hwOptions = {"lcd" : True,
				  "buttons" : True,
				  "ledbars" : True,
				  "flowsensors" : True,
				  "floatswitch" : True,
				  "soiltemp" : True,
				  "powermonitor" : True,
				  "status LED" : True,
				  "fan" : True,
				  }

	# Locations of files.
	dataloc = str(os.path.dirname(os.path.realpath(__file__))) + "/datafiles/"
	sensSetup = dataloc + "sensorSetup.csv"
	logfile = dataloc + "kascontrol.log"

	# Misc GPIO pin assignments:
	button0pin = "2B0"				# Input pin for button 0.
	button1pin = "2B1"				# Input pin for button 1.
	pumpPin = "1A0"					# Pin for the pump.
	sLEDpin = 23						# Status LED pin.
	float_switch = 22					# Float switch pin, goes high if there is too little water in the storage tank.
	intPinU4 = 5						# Interrupt pin for mcp23017 0x20, U4
	intPinU5 = 25						# Interrupt pin for mcp23017 0x23, U5
			
	# LCD pins:
	LCD4 = 26
	LCD5 = 16
	LCD6 = 21
	LCD7 = 20
	LCD_E = 19
	LCD_RS = 13
	LCD_L = 12

	# Networking vars:
	host = ""							# Hostname.
	port = 7500							# Default network port. If already used, can go up to port 7504
	
	# Misc vars
	draadjes = []						# List with all the active threads.
	wtrThreads = []					# List with all watering threads.
	threadnr = 0						# Keep track of the thread number.
	testmode = False					# Disables certain features for diagnositc purposes.
	time.sleep(0.5)					# Make sure some time has passed so the system clock is updated after boot.
	boottime = time.time()			# Record boot time to display system uptime.
	running = True						# Set to False to enable shutdown
	shutdownOpt = None				# Set shutdown mode.

	# Initiate MCP23017 GPIO expanders:
	mcplist = [mcp23017.mcp23017(0x21),				# u2
				mcp23017.mcp23017(0x20, intPintU4),	# u4
				mcp23017.mcp23017(0x23, intPinU5),	# u5
				mcp23017.mcp23017(0x27)					# u6
				]
	if (hwOptions["powermonitor"]):
		mcplist.append(mcp23017.mcp23008(0x22))	# u12

	# Major modules:
	control = None						# Reference to the hwcontrol instance.
	db = None							# Reference to database instance.
	webgraph = None					# Reference to webgraph instance.
	server = None						# Reference to the server object.
		
	def getPinNr(pin):
		"""Returns the pin number without device number."""

		return(str(pin[1:]))

	def getPinDev(pin):
		"""Returns the mpc23017 device for the corresponding pin."""
		
		if (int(pin[0]) < len(globstuff.mcplist)):
			return(globstuff.mcplist[int(pin[0])])
		else:
			logging.error("Invalid MCP23017 instance: " + str(pin))
			return(None)
			
	def getThreadNr():
		globstuff.threadnr +=1
		return(globstuff.threadnr)
		
	def convertToPrec(self, data, places):
		"""Returns the percentage value of the number."""

		m = ((data * 100) / float(globstuff.control.getADCres()))
		return(str(round(m, places)))

	def getCPUtemp():
		"""Retruns the current CPU temperature in degrees C"""

		tempFile = open("/sys/class/thermal/thermal_zone0/temp")
		cpu_temp = tempFile.read()
		tempFile.close()
		return(round(float(cpu_temp)/1000, 1))

	def timediff(diff):
		"""Converts seconds into dd, HH:MM:SS"""

		days = 0
		hours = 0
		minutes = 0
		if (diff >= 86400):
			days = int(diff / 86400)
			diff -= days * 86400
			if (days < 10):
				if (days == 0):
					days = "00"
				else:
					days = ("0" + str(days))
		if (diff >= 3600):
			hours = int(diff / 3600)
			diff -= hours * 3600
			if (hours < 10):
				if (hours == 0):
					hours = "00"
				else:
					hours = ("0" + str(hours))
		if (diff >= 60):
			minutes = int(diff / 60)
			diff -= minutes * 60
			if (minutes < 10):
				if (minutes == 0):
					minutes = "00"
				else:
					minutes = ("0" + str(minutes))
		seconds = int(diff)
		if (seconds < 10):
			if (seconds == 0):
				seconds = "00"
			else:
				seconds = ("0" + str(seconds))
		return((days, hours, minutes, seconds))
	
	def shutdown():
		"""\t\tUse this method to either shutdown this software or,
		with '-x' or '-r' as argument, shutdown or reboot
		the Raspberry pi, respectively."""

		print("Shutting down system.")
		globstuff.running = False
		globstuff.pump.disable()
		globstuff.db.running = False
		for t in globstuff.draadjes:
				t.join()
		print("Cleaning up and exiting Main Thread")
		for mcp in globstuff.mcplist:
			mcp.allOff()
		globstuff.server.sslSock.close()
		globstuff.control.shutdown()
		GPIO.cleanup()
		print("Cleanup done.")
		if (globstuff.shutdownOpt == "-r" or globstuff.shutdownOpt == "-x"):
			if (globstuff.shutdownOpt == "-x"):
				globstuff.shutdownOpt = "-h"
			command = "/usr/bin/sudo /sbin/shutdown {0} now".format(globstuff.shutdownOpt) # "/usr/bin/sudo /sbin/shutdown {0} now"
			process = subprocess.Popen(command.split(), stdout=subprocess.PIPE)
			output = process.communicate()[0]
			print(output)

		sys.exit()