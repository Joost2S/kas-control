#!/usr/bin/python3
 
# Author: J. Saarloos
# v0.8.3	16-08-2017


from abc import ABCMeta, abstractmethod
import csv
import datetime
import logging
import os
import RPi.GPIO as GPIO
import subprocess
import sys
import threading
import time

import dbstuff
import ds18b20
import mcp23017
import mcp3x08
import webgraph


class Group(object):
	"""This object represents the combination of a soil sensor and watervalve."""

	# chan
	@property
	def chan(self):
		return(self.__chan)
	@chan.setter
	def chan(self, chan):
		self.__chan = chan
	#devchan
	@property
	def devchan(self):
		return(self.__devchan)
	@devchan.setter
	def devchan(self, devchan):
		self.__devchan = devchan
	# spichan
	@property
	def spichan(self):
		return(self.__spichan)
	@spichan.setter
	def spichan(self, spichan):
		self.__spichan = spichan	
	# name
	@property
	def name(self):
		return(self.__name)
	@name.setter
	def name(self, name):
		self.__name = name
	# connected
	@property
	def connected(self):
		return(self.__connected)
	@connected.setter
	def connected(self, connected):
		self.__connected = connected
	# watering
	@property
	def watering(self):
		return(self.__watering)
	@watering.setter
	def watering(self, watering):
		self.__watering = watering
	#below_range	
	@property
	def below_range(self):
		return(self.__below_range)
	@below_range.setter
	def below_range(self, below_range):
		self.__below_range = below_range
	# lowtrig
	@property
	def lowtrig(self):
		return(self.__lowtrig)
	@lowtrig.setter
	def lowtrig(self, lowtrig):
		self.__lowtrig = lowtrig
	# hightrig
	@property
	def hightrig(self):
		return(self.__hightrig)
	@hightrig.setter
	def hightrig(self, hightrig):
		self.__hightrig = hightrig
	# ff1
	@property
	def ff1(self):
		return(self.__ff1)
	@ff1.setter
	def ff1(self, ff1):
		self.__ff1 = ff1
	# ff2
	@property
	def ff2(self):
		return(self.__ff2)
	@ff2.setter
	def ff2(self, ff2):
		self.__ff2 = ff2
		
	def __init__(self, i, v, lowtrig, hightrig, ff1, ff2):
		self.chan = i
		if (i <= 7):
			self.devchan = i
			self.spichan = 0
		elif (i <= 14):
			self.devchan = (i - 7)
			self.spichan = 1
		else:
			logging.waring("Too many group channels defined. Group: " + i)
		self.name = "Soil" + str(i + 1)
		self.valve = v

		self.connected = False			# A sensor is considered disconnected when value <= 150
		self.watering = False
		self.below_range = 0
		self.lowtrig = lowtrig
		self.hightrig = hightrig
		self.ff1 = ff1
		self.ff2 = ff2

		
class sigLED(object):
	"""This object is for controlling the signalling LED on the box."""
	# GPIO pin
	@property
	def pin(self):
		return(self.__pin)
	@pin.setter
	def pin(self, pin):
		self.__pin = pin

	@property
	def interval(self):
		return(self.__interval)
	@interval.setter
	def interval(self, interval):
		self.__interval = interval
		
	def __init__(self, pin):
		self.pin = pin
		self.interval = 0.5
		
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

	def on(self):
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

	def __init__(self, float_switch, pump, sLED):
		self.low_water = False
		self.float_switch = float_switch
		self.sLED = sLED
		self.pump = pump
		self.lastMailSent = 0
		
	def check_level(self):
		"""\t\tRun as seperate thread when a low water level situation occurs.
		Will self terminate when the water level is high enough again."""

		while(self.low_water):
			input_state = self.getStatus()
			print(input_state)
			self.sLED.blinkFast(5)
			if (not input_state and not globstuff.running):
				self.low_water = False

	def getStatus(self):
		"""\t\tChecks and returns the current status of the float switch.
		True if low water, False if enough water."""

		return(GPIO.input(self.float_switch))

	def lwstrt(self):
		"""Run at startup to check initial water level."""

		if (self.getStatus):
			self.low_water = True
			print("Low water status: " + str(self.low_water))
			self.pump.disable()

			#	Start level checking and alarm LED.
			blink = lowWater(globstuff.getThreadNr(), "water level check")
			blink.start()
			globstuff.draadjes.append(blink)

	def lwstart(self, startup):
		"""If low water level is detected, run this to disable pumping and send an email to user."""

		if (GPIO.input(self.float_switch)):
			self.low_water = True
			print("Low water status: " + str(self.low_water))
			self.pump.disable()

			#	Start level checking and alarm LED.
			blink = lowWater(globstuff.getThreadNr(), "water level check")
			blink.start()
			globstuff.draadjes.append(blink)

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
				server.login(username,password)
				server.sendmail(fromaddr, toaddr, msg)
				server.quit()
				logging.debug("Sent mail to " + toaddr)


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
		print("Starting thread{0}: {1}".format(self.threadID, self.name))
		globstuff.fltdev.check_level()
		print("Exiting thread{0}: {1}".format(self.threadID, self.name))
		

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

	def __pumpOn(self):
		"""Turn the pump on."""
		
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


class globstuff:

	# Lists for pin numbers and other I/O
	ch_list = []
	dataloc = os.path.dirname(os.path.realpath(__file__)) + "/datafiles/"
	valvelist = dataloc + "valves.csv"
	wateringlist = dataloc + "waterlist.csv"
	logfile = dataloc + "kascontrol.log"
	lightname = "light"							# Name of the channel of the lightsensor.
	tempname = "kastemp"
	waterlength = 100								# Amount of entries in the watering list.
	currentstats = ""								# Copy of sensor output updated eachtime_res seconds.
														# For fast disply of data to user.
	# Other GPIO pin assignments:
	pumpPin = "1A0"
	sLEDpin = 23
	float_switch = 22
			
	# Networking vars:
	host = ""
	port = 7500
	socket = None
	
	# Misc vars
	draadjes = []						# List with all the active threads.
	wtrThreads = []					# List with all watering threads.
	threadnr = 0						# Keep track of the thread number.
	shutdownOpt = None				# Set shutdown mode.
	testmode = False					# Disables certain features for diagnositc purposes.
	time.sleep(0.5)					# Make sure some time has passed so the system clock is updated after boot.
	boottime = time.time()			# Record boot time to display system uptime.
	running = True						# Set to False to enable shutdown
	time_res = 5.0						# sets the time resolution for recording to the database (in min)
											# and polling (in sec) of all the data.

	# Populating ch_list with groups of (sensor + valve)
	with open(valvelist, "r", newline = "") as filestream:
		file = csv.reader(filestream, delimiter = ",")
		for i, line in enumerate(file):
			if (i == 0):
				continue
			ch_list.append(Group(i-1, str(line[0]), int(line[1]), int(line[2]), str(line[3]), str(line[4])))

	dbSetup = [(tempname, "temp"),
					(lightname, "light")]
	for g in ch_list:
		dbSetup.append((g.name, "mst"))
			
	# Initiate various devices:
	tDevList = []
	for d in ds18b20.getTdev():
		name = None
		if (d == "/sys/bus/w1/devices/28-000007c0d519/w1_slave"):
			name = tempname
		tDevList.append(ds18b20.ds18b20(d, name))
	sLED = sigLED(sLEDpin)
	pump = Pump(pumpPin, sLED)
	fltdev = floatUp(float_switch, pump, sLED)
	mcplist = [mcp23017.mcp23017(0x21), mcp23017.mcp23017(0x20)]	# u2, u4
	adc = mcp3x08.mcp3208(0, mcplist[0])		# u1
	db = dbstuff.db(dbSetup, time_res, dataloc, adc, tDevList, mma = True, period = "Y")
	wgraph = webgraph.webgraph(db)
		
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

	def setfile(trigger, channel, value):
		"""Changes to the trigger values for watering are handeled here"""

		if (trigger == "h"):
			globstuff.ch_list[channel].hightrig = int(value)
			t = 2
		else:
			globstuff.ch_list[channel].lowtrig = int(value)
			t = 1
		with open(globstuff.valvelist, "r", newline = "") as filestream:
			file = csv.reader(filestream, delimiter = ",")
			stuff = []
			for line in file:
				stuff.append(line)
			stuff[channel + 1][t] = value
		with open(globstuff.valvelist, "w", newline = "") as filestream:
			file = csv.writer(filestream, delimiter = ",")
			for i in stuff:
				file.writerow(i)

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
		globstuff.socket.close()
		globstuff.sLED.off()
		GPIO.cleanup()
		print("Cleanup done.")
		if (globstuff.shutdownOpt == "-r" or globstuff.shutdownOpt == "-x"):
			if (globstuff.shutdownOpt == "-x"):
				globstuff.shutdownOpt = "-h"
			command = "/usr/bin/sudo /sbin/shutdown {0} now".format(globstuff.shutdownOpt) # "/usr/bin/sudo /sbin/shutdown {0} now"
			process = subprocess.Popen(command.split(), stdout=subprocess.PIPE)
			output = process.communicate()[0]
			print("Moi " + str(output))

		sys.exit()