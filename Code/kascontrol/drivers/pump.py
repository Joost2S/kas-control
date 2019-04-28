#!/usr/bin/python3

# Author: J. Saarloos
# v0.01.00	25-04-2019


import logging
import time

from ..globstuff import globstuff as gs


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

	def disable(self):
		"""Disables the ability to pump."""

		print("Pump disabled.")
		self.enabled = False
		self.off()

	def enable(self):
		"""Re-enable pumping ability."""

		if (not gs.testmode):
			self.enabled = True

	def on(self):
		"""Turn the pump on."""

		if (self.enabled):
			logging.info("Pump turned on.")
			self.isPumping = True
			if (self.sLED is not None):
				self.sLED.on()
			self.startTime = time.time()
			gs.getPinDev(self.pumpPin).output(gs.getPinNr(self.pumpPin), True)

	def off(self):
		"""Turn the pump off."""

		self.isPumping = False
		if (self.sLED is not None):
			self.sLED.off()

		gs.getPinDev(self.pumpPin).output(gs.getPinNr(self.pumpPin), False)
		if (self.startTime is not None):
			logging.info("Pump turned off. Pumped for " + str(round(time.time() - self.startTime, 2)) + " seconds.")
			self.startTime = None
