#!/usr/bin/python3

# Author: J. Saarloos
# v0.01.03	26-05-2019


import logging

from Code.kascontrol.utils.errors import SpiPinError


class SPI_74LS138(object):

	spi = None
	devices = {}
	pins = []
	lut = [
		[0, 0, 0],
		[0, 0, 1],
		[0, 1, 0],
		[0, 1, 1],
		[1, 0, 0],
		[1, 0, 1],
		[1, 1, 0],
		[1, 1, 1]
	]

	def __init__(self, pins, gpio):

		self.gpio = gpio
		for p in pins:
			pinID = self.gpio.setPin(p["pin"], False, p["address"])
			if pinID is False:
				logging.error("Pin {} could not be set for SPI-74LS138 IC. Aborting init.")
				raise SpiPinError
			self.pins.append(pinID)


	def set(self, devChannel):

		for i, state in enumerate(self.lut[self.devices[devChannel]]):
			self.gpio.output(self.pins[i], state)
