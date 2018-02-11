#!/usr/bin/python3
 
# Author: J. Saarloos
# v0.0.01	10-02-2018

import logging

from globstuff import globstuff as gs


class LEDchannel(object):

	pin = ""
	power = 0
	mode = ""
	enabled = False
	on = False

	def __init__(self, pin):
		self.pin = pin
		gs.getPinDev(pin).setPin(gs.getPinNr(pin), False)

	def set(self, mode, power):

		if (not self.on):
			self.mode = mode
			self.power = power
			self.enabled = True

	def unset(self):

		if (self.on):
			self.off()
		self.mode = ""
		self.power = 0
		self.enabled = False

	def turnOn(self):

		if (self.enabled):
			self.on = True
			gs.getPinDev(self.pin).output(gs.getPinNr(self.pin), True)

	def turnOff(self):

		self.on = False
		gs.getPinDev(self.pin).output(gs.getPinNr(self.pin), False)


class PowerLEDcontroller(object):

	channels = []
	__modes = {"1ww" : 350, "3ww" : 700, "3ir" : 500}

	def __init__(self):
		for pin in gs.powerLEDpins:
			self.channels.append(LEDchannel(pin))