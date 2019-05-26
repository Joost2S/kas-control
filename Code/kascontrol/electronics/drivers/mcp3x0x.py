#!/usr/bin/python3

# Author: J. Saarloos
# v1.05.05	26-05-2019

"""
For controlling MCP3208 and MCP3008 adc for light and moisture readings.
FF (flip-flop) support is available per channel for when you have a
flip-flop setup to prevent electrolysis.
Select a gpio chip (raspberry pi GPIO, mcp23017, etc) as main controller for flip-flop pins.
A GPIO manager is expected for use with multiple GPIO devices.
For details about MCP3208/3204: http://ww1.microchip.com/downloads/en/DeviceDoc/21298c.pdf
For Details about MCP3008/3004: http://ww1.microchip.com/downloads/en/DeviceDoc/21295C.pdf
"""

from abc import ABCMeta, abstractmethod
import logging


class Channel(object):

	chan = 0
	p1 = None
	p2 = None
	mcp = None
	ff = False
	ffstate = False

	def __init__(self, chan, p1=None, p2=None):

		self.chan = chan
		self.p1 = p1
		self.p2 = p2
		if (p1 is not None and p2 is not None):
			self.ff = True
		self.ffstate = False


class MCP3x0x(object):

	__metaclass__ = ABCMeta
	__bits = 0				# Max value of 1023 (MCP3008) or 4095 (MCP3208).
	chanAmount = 0
	channels = {}			# Dict of {channelNumber: channelObject, ...}.
	debug = False			# To enable debug mode if you need to check the circuit.
	debug_output = ""		# Select to send the data to console or to log it. Options "cons" or "log".
	gpio = None				# Sets which gpio to use.
	samples = 15			# How many samples per measurement.
	spi = None				# Sets the SPI device.
	spiChan = None
	__tlock = None


	def __init__(self, spi, spiChan, tLock, gpio=None):

		# Setup for the adc connected with spi
		self.spi = spi
		self.spiChan = spiChan
		self.gpio = gpio
		self.__tlock = tLock


	@abstractmethod
	def read(self, channel):
		pass

	def readChannel(self, channel):

		data = self.read(channel)
		if self.debug:
			self.__debugReturn(channel.name, data)
		if channel.ffstate:
			return data
		else:
			return self.__bits - data

	def setSamples(self, samples):
		"""Set how many individual reads you want to return for each measurement."""

		if samples > 0:
			self.samples = samples

	def setChannel(self, channel, p1=None, p2=None):
		"""Define flip-flop pins for each channel."""

		if not (0 <= channel < self.chanAmount):
			logging.debug("Incorrect channel: {}".format(channel))
			return
		if channel in self.channels.keys():
			logging.debug("Channel {} on SPI {} already set.".format(channel, self.spiChan))
			return
		if (p1 is None and p2 is None):
			self.channels[channel] = Channel(channel)
		elif (p1 is not None and p2 is not None):
			self.channels[channel] = Channel(channel, p1, p2)
		else:
			logging.debug("Only one flip flop pin given, please give 2 pins for a complete flip-flop circuit.")

	def getMeasurement(self, channel, perc=False):
		"""Get a reading of soil moisture level."""

		try:
			channel = self.channels[channel]
		except KeyError:
			return None
		level = 0.0
		with self.__tlock() as result:
			if not result:
				logging.error("Could not get threading lock for adc on channel {}".format(channel))
				return None
			if self.spi.mode() != 0:
				self.spi.mode(0)
			for i in range(self.samples):
				if channel.ff:
					self.gpio.output(channel.p1, channel.ffstate)
					self.gpio.output(channel.p2, not channel.ffstate)
					channel.ffstate = not channel.ffstate
				level += self.readChannel(channel)
			if channel.ff:
				self.gpio.output((channel.p1, channel.p2), False)
		level /= self.samples
		if perc:
			return self.__convertToPrec(level, 1)
		return round(level, 1)

	def setDebug(self, output):
		"""\t\tEnable debug mode to provide more data, either in
		the console window ("cons") or in the logfile ("log") (not recommended, lots of data)."""

		if output == "cons" or output == "log":
			self.debug = True
			self.debug_output = output
		else:
			logging.warning("Set output to either \"cons\" or \"log\".")

	def getResolution(self):

		return self.__bits

	def __debugReturn(self, channel, value):
		"""Debug data is collected and displayed in the console or logfile"""

		dbgmsg = "Channel: "
		if channel.ffstate:
			dbgmsg += "{}\tValue: {}\t".format(channel.chan, value)
		else:
			dbgmsg += "{}\tCor value: {}\t".format(channel.chan, self.__bits - value)
		if channel.ff:
			if channel.ffstate:
				p1 = "Off"
				p2 = "On"
			else:
				p1 = "On"
				p2 = "Off"
			pin1 = self.gpio.getAddress(channel.p1)
			pin2 = self.gpio.getAddress(channel.p2)
			dbgmsg += "Pin 1: {}\tAddr: {}\tState: {}".format(pin1["pin"], pin1["address"], p1)
			dbgmsg += "Pin 2: {}\tAddr: {}\tState: {}".format(pin2["pin"], pin2["address"], p2)
			dbgmsg += "\tFlip-Flop State: ".format(channel.ffstate)
		else:
			dbgmsg += "No flip-flop."
		if self.debug_output == "log":
			logging.debug(dbgmsg)
		elif self.debug_output == "cons":
			print(dbgmsg)

	def __convertToPrec(self, data, places):
		"""Returns the percentage value of the number."""

		m = (data * 100) / float(self.__bits)
		return(round(m, places))


class MCP320x(MCP3x0x):

	def __init__(self, spi, spiChan, tLock=None, gpio=None):
		super(MCP320x, self).__init__(spi=spi, spiChan=spiChan, tLock=tLock, gpio=gpio)
		self.__bits = 4095

	def read(self, channel):
		args = [4 | 2 | (channel.chan >> 2),
		                    (channel.chan & 3) << 6, 0]
		adcdata = self.spi.xfer2(self.spiChan, args)
		return ((adcdata[1] & 15) << 8) + adcdata[2]
#		adcdata = self.spi.xfer2([96 + (4 * self.channels[name].chan), 0, 0])
#		data = int((adcdata[1] << 4) + (adcdata[2] >> 4))


class MCP300x(MCP3x0x):

	def __init__(self, spi, spiChan, tLock=None, gpio=None):
		super(MCP300x, self).__init__(spi=spi, spiChan=spiChan, tLock=tLock, gpio=gpio)
		self.__bits = 1023

	def read(self, channel):
		args = [1, (8 + channel.chan) << 4, 0]
		adcdata = self.spi.xfer2(self.spiChan, args)
		return int(((adcdata[1]&3) << 8) + adcdata[2])


class MCP3004(MCP300x):

	def __init__(self, spi, spiChan, tLock=None, gpio=None):
		super(MCP3004, self).__init__(spi=spi, spiChan=spiChan, tLock=tLock, gpio=gpio)
		self.chanAmount = 4


class MCP3008(MCP300x):

	def __init__(self, spi, spiChan, tLock=None, gpio=None):
		super(MCP3008, self).__init__(spi=spi, spiChan=spiChan, tLock=tLock, gpio=gpio)
		self.chanAmount = 8


class MCP3204(MCP320x):

	def __init__(self, spi, spiChan, tLock=None, gpio=None):
		super(MCP3204, self).__init__(spi=spi, spiChan=spiChan, tLock=tLock, gpio=gpio)
		self.chanAmount = 4


class MCP3208(MCP320x):

	def __init__(self, spi, spiChan, tLock=None, gpio=None):
		super(MCP3208, self).__init__(spi=spi, spiChan=spiChan, tLock=tLock, gpio=gpio)
		self.chanAmount = 8
