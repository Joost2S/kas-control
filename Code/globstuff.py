#! /usr/bin/python

import datetime
import logging
import RPi.GPIO as GPIO
import smtplib
import threading
import time

import sensor


	
# Object for handeling a low water level.
class floatUp(object):
	@property
	def low_water(self):
		return(self.__low_water)
	@low_water.setter
	def low_water(self, low_water):
		self.__low_water = low_water
	@property
	def float_switch(self):
		return(self.__float_switch)
	@float_switch.setter
	def float_switch(self, float_switch):
		self.__float_switch = float_switch
	@property
	def sLED(self):
		return(self.__sLED)
	@sLED.setter
	def sLED(self, sLED):
		self.__sLED = sLED

	def __init__(self, float_switch, sLED):
		self.low_water = False
		self.float_switch = float_switch
		self.sLED = sLED
		
	def check_level(self):
		while(self.low_water):
			input_state = GPIO.input(self.float_switch)
			self.sLED.blink(5)
			if (input_state):
				self.low_water = False

	def lwstart(self, channel):
		self.low_water = True

		#	Start level checking and alarm LED.
		blink = threading.Thread(name = "water level check", target = self.check_level, args=())
		blink.setDaemon(True)
		blink.start()

		#	Send an email to alert user.
#		fromaddr = ""
#		toaddr  = ""
#		subject = "Test bericht."
#		text = "."
#		msg = "Subject: %s\n\n%s" % (subject, text)

		# Credentials
#		username = fromaddr
#		password = ""

		# The actual mail send
#		server = smtplib.SMTP("smtp.gmail.com:587")
#		server.starttls()
#		server.login(username,password)
#		server.sendmail(fromaddr, toaddr, msg)
#		server.quit()


#	This object represents the combination of a soil sensor and watervalve.
class Group(object):
	@property
	def chan(self):
		return(self.__chan)
	@chan.setter
	def chan(self, chan):
		self.__chan = chan
	@property
	def devchan(self):
		return(self.__devchan)
	@devchan.setter
	def devchan(self, devchan):
		self.__devchan = devchan
	@property
	def spichan(self):
		return(self.__spichan)
	@spichan.setter
	def spichan(self, spichan):
		self.__spichan = spichan	
	
	@property
	def valve(self):
		return(self.__valve)
	@valve.setter
	def valve(self, valve):
		self.__valve = valve
		
	@property
	def connected(self):
		return(self.__connected)
	@connected.setter
	def connected(self, connected):
		self.__connected = connected
		
	@property
	def watering(self):
		return(self.__watering)
	@watering.setter
	def watering(self, watering):
		self.__watering = watering
	
	@property
	def pumping(self):
		return(self.__pumping)
	@pumping.setter
	def pumping(self, pumping):
		self.__pumping = pumping
		
	@property
	def below_range(self):
		return(self.__below_range)
	@below_range.setter
	def below_range(self, below_range):
		self.__below_range = below_range
		
	@property
	def lowrange(self):
		return(self.__lowrange)
	@lowrange.setter
	def lowrange(self, lowrange):
		self.__lowrange = lowrange
		
	@property
	def highrange(self):
		return(self.__highrange)
	@highrange.setter
	def highrange(self, highrange):
		self.__highrange = highrange
		
	def __init__(self, i, v):
		self.chan = i
		if (i <= 7):
			self.devchan = i
			self.spichan = 0
		elif (i <= 14):
			self.devchan = (i - 7)
			self.spichan = 1
		else:
			logging.debug("Too many group channels defined. Group: " + i)
		self.valve = v
		self.connected = False
		self.watering = False
		self.pumping = False
		self.below_range = 0
		self.lowrange = 575
		self.highrange = 675

		

#	This object is for controlling the signalling LED on the box.
class sigLED(object):
	
	@property
	def low(self):
		return(self.__low)
	@low.setter
	def low(self, low):
		self.__low = low

	@property
	def high(self):
		return(self.__high)
	@high.setter
	def high(self, high):
		self.__high = high

	@property
	def interval(self):
		return(self.__interval)
	@interval.setter
	def interval(self, interval):
		self.__interval = interval

	@property
	def threshold(self):
		return(self.__threshold)
	@threshold.setter
	def threshold(self, threshold):
		self.__threshold = threshold
		
	def __init__(self, low, high):
		self.low = low
		self.high = high
		self.interval = 0.5
		self.threshold = 800

	def blink(self, i):
		for j in range(0, i):
			self.on()
			time.sleep(self.interval / 2)
			self.off()
			time.sleep(self.interval / 2)

	def on(self):
		if (sensor.light.get_light() <= self.threshold):
			GPIO.output(self.high, GPIO.LOW)
			GPIO.output(self.low, GPIO.HIGH)
		else:
			GPIO.output(self.low, GPIO.LOW)
			GPIO.output(self.high, GPIO.HIGH)

	def off(self):
			GPIO.output(self.low, GPIO.LOW)
			GPIO.output(self.high, GPIO.LOW)



class globstuff:
	# Lists for pin numbers and other I/O
	ch_list = []

	wateringlist = []
	currentstats = ""
	
	dbchecked = False								# To check the last entry in the DB only once
	# Other GPIO pin assignments:
	pump = 6
	sigLEDlow = 17
	sigLEDhigh = 18
	float_switch = 27
			
	# Networking vars:
	host = ""
	port = 7500
	
	# Misc vars
	time_res = 5.0									# sets the time resolution for recording to the database (in min)
																# and polling (in sec) of all the data.
	sLED = sigLED(sigLEDlow, sigLEDhigh)
	fltdev = floatUp(float_switch, sLED)
	running = True									# Set to False to enable shutdown
	
		# Populating ledlist with pin numbers
#		with open("setup/leds.txt", "r") as filestream:
#			for line in filestream:
#				currentline = line.strip().split(',')
#				for i in currentline:
#					self.ledlist.append(i)
					
	# Populating ch_list with groups of (sensor + valve)
	with open("/home/j2s/greenhousefiles/setup/valves.txt", "r") as filestream:
		for line in filestream:
			currentline = line.strip().split(",")
			i = 1
			for v in currentline:
				ch_list.append(Group(i, int(v)))
				i += 1

	def addToWlist(msg):
		if (len(globstuff.wateringlist) >= 11):
			del globstuff.wateringlist[0]
		globstuff.wateringlist.append(msg)