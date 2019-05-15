#!/usr/bin/python3

# Author: J. Saarloos
# v0.01.00	03-02-2019


import RPi.GPIO as GPIO
import spidev


class SPI_74LS138(object):

	spi = None
	devices = {}
	pins = None
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

	def __init__(self, pins):

		self.spi = spidev.SpiDev()
		self.spi.max_speed_hz = 2000000
		self.pins = pins
		for pin in pins:
			GPIO.setup(pin, GPIO.OUT)
			GPIO.output(pin, GPIO.LOW)
		self.spi.open(0, 0)


	def xfer(self, dev, args):

		for i, state in enumerate(self.lut[self.devices[dev]]):
			GPIO.output(self.pins[i], state)

		data = self.spi.xfer2(args)

		return(data)
