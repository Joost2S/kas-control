#!/usr/bin/python3

# Author: J. Saarloos
# v0.01.01	17-05-2019


import datetime
import logging
import smtplib
import time

from Code.kascontrol.globstuff import globstuff as gs
from Code.kascontrol.utils.protothread import ProtoThread


class FloatSwitch(object):
	"""Object for handeling a low water level."""

	# low_water
	@property
	def lowWater(self):
		return(self.__low_water)
	@lowWater.setter
	def lowWater(self, low_water):
		self.__low_water = low_water
	# float_switch
	@property
	def pin(self):
		return(self.__float_switch)
	@pin.setter
	def pin(self, float_switch):
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

	def __init__(self, pin, pump, gpio, sLED = None):
		super(FloatSwitch, self).__init__()

		self.gpio = gpio
		self.lowWater = False
		self.sLED = sLED
		self.pump = pump
		self.lastMailSent = 0
		self.pin = self.gpio.setPin(
			pin=pin,
			state=True,
			devAddr=pin["addr"],
			args=pin["args"])
		self.gpio.addInterrupt(pin=self.pin,
		                       edge="rising",
		                       callback=self.lwstart,
		                       args={"bouncetime": 1000})
		if (self.getStatus()):
			self.lwstart()


	def getStatus(self):
		"""\t\tChecks and returns the current status of the float switch.
		True if low water, False if enough water."""

		return(self.gpio.input(self.pin))

	def lwstart(self, mail=False):
		"""If low water level is detected, run this to disable pumping and send an email to user."""

		if (self.getStatus()):
			self.lowWater = True
			logging.info("Low water status: " + str(self.lowWater))
			self.pump.disable()

			#	Start level checking and alarm LED.
			blink = lowWater(gs.getThreadNr(), "water level check", obj=self)
			blink.start()
			gs.draadjes.append(blink)

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

	def checkLevel(self):
		"""\t\tRun as seperate thread when a low water level situation occurs.
		Will self terminate when the water level is high enough again."""

		while(self.lowWater):
			self.sLED.blinkFast(5)
			if (not self.getStatus() or not gs.running):
				self.lowWater = False


class lowWater(ProtoThread):

	def run(self):
		logging.info("Starting thread{0}: {1}".format(self.threadID, self.name))
		self.obj.checkLevel()
		logging.info("Exiting thread{0}: {1}".format(self.threadID, self.name))
