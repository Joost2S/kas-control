#! /usr/bin/python
 
# Author: J. Saarloos
# v0.06.52	15-05-2019

import RPi.GPIO as GPIO
import threading
import time


class FlowMeter(object):
	"""Object providing basic functionality for a water flow meter."""
	
	# pulses
	@property
	def pulses(self):
		return self.__pulses
	@pulses.setter
	def pulses(self, pulses):
		self.__pulses = pulses
	# lock
	@property
	def lock(self):
		return self.__lock
	@lock.setter
	def lock(self, lock):
		self.__lock = lock
	# sendToObj
	@property
	def sendToObj(self):
		return self.__sendToObj
	@sendToObj.setter
	def sendToObj(self, sendToObj):
		self.__sendToObj = sendToObj
	# flowcounter
	@property
	def flowcounter(self):
		return self.__flowcounter
	@flowcounter.setter
	def flowcounter(self, flowcounter):
		self.__flowcounter = flowcounter
	# lastTime
	@property
	def lastTime(self):
		return self.__lastTime
	@lastTime.setter
	def lastTime(self, lastTime):
		self.__lastTime = lastTime
	# flowRate
	@property
	def flowRate(self):
		return self.__flowRate
	@flowRate.setter
	def flowRate(self, flowRate):
		self.__flowRate = flowRate

	def __init__(self, pin):

		self.pulses = 0
		self.lock = threading.Lock()
		self.sendToObj = []
		self.flowcounter = 0
		self.lastTime = 0
		self.flowRate = 0
		if isinstance(pin, int):
			GPIO.setup(pin, GPIO.IN)#, pull_up_down = GPIO.PUD_UP)
			GPIO.add_event_detect(pin, GPIO.FALLING, callback=self.addPulse)
		else:
			from ...globstuff import globstuff as gs
			gs.getPinDev(pin).setPin(gs.getPinNr(pin), True)
			gs.getPinDev(pin).addInterruptInput(gs.getPinNr(pin), self, "high")

	def requestData(self, obj):
		"""\t\tObject can subscribe by sending itself as argument to have it's own pulsecount.
		Object is required to have an addPulse() method.
		Can be useful for tracking water consumption during events.
		"""

		self.sendToObj.append(obj)

	def endRqeuest(self, obj):
		"""Object can unsubscribe to end it's measuring."""

		if obj in self.sendToObj:
			self.sendToObj.remove(obj)

	def run(self):
		self.addPulse()

	def addPulse(self, *args):
		"""Adds a pulse to the pulsecount of self and all subscribed objects."""

#		print("args: ", *args)
		with self.lock:
			self.pulses += 1
		for obj in self.sendToObj:
			try:
				obj.addPulse()
			except:
				self.endRqeuest(obj)
				print("Failed to run addPulse() method of object: ", obj)
		self.flowcounter += 1
		if self.flowcounter >= 5:
			self.__setFlowRate(args[0])
			self.flowcounter = 0

	def storePulses(self):
		"""Store current pulsecount in DB and reset count."""

		with self.lock:
			p = 0
			p += self.pulses
			self.pulses = 0
		return p

	def __setFlowRate(self, pin):
		"""Calculates the flowrate in pulses/min."""

		dt = time.time() - self.lastTime
		self.lastTime = time.time()
		self.flowRate = 5 / dt * 60
		print(pin, self.flowRate, dt)

	def getFlowRate(self):
		"""Returns the current flowRate and resets it if last pulse was > 5 seconds ago."""

		if (time.time() - self.lastTime) > 5:
			self.flowRate = 0
			self.flowcounter = 0
		return self.flowRate
