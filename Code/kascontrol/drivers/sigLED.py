#!/usr/bin/python3

# Author: J. Saarloos
# v0.01.00	25-04-2019


import RPi.GPIO as GPIO
import time


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
