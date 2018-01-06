#!/usr/bin/python3
 
# Author: J. Saarloos
# v1.3.2	03-08-2017

"""
For controlling MCP3208 and MCP3008 adc for light and moisture readings.
FF (flip-flop) support is available per channel for when you have a flip-flop setup to prevent electrolysis.
Select a gpio chip (raspberry pi GPIO, mcp23017, etc) as main controller for flip-flop pins.
Alternate GPIO's can be set for each channel.
"""

from abc import ABCMeta, abstractmethod
import logging
import spidev
import threading


class channel(object):

	chan = 0
	p1 = None
	p2 = None
	mcp = None
	ff = False
	ffstate = False
	lock = None
	locked = False

	def __init__(self, chan, mcp, p1 = None, p2 = None):

		self.chan = chan
		self.mcp = mcp
		self.p1 = p1
		self.p2 = p2
		if (p1 is not None and p2 is not None):
			self.ff = True
		self.ffstate = False
		self.lock = threading.Lock()


class adc(object):
	__metaclass__ = ABCMeta
	spi = None					# Sets the SPI channel.
	gpio = None					# Sets which gpio to use.
	total = 0					# Max value of 1023 (MCP3008) or 4095 (MCP3208).
	samples = 15				# How many samples per measurement.
	channels = {}				# List of flip flop pins.
	debug = False				# To enable debug mode if you need to check the circuit.
	debug_output = ""			# Select to send the data to console or to log it. Options "cons" or "log".


	def __init__(self, spi, gpio = None):
		
		# Setup for the adc connected with spi
		self.spi = spidev.SpiDev()
		self.spi.open(0, spi)
		self.spi.max_speed_hz = 2000000
		self.gpio = gpio
		

	@abstractmethod
	def readChannel(self, channel):
		pass


	def setSamples(self, samples):
		"""Set how many individual reads you want to return for each measurement."""

		self.samples = samples


	def setChannel(self, name, chan, p1 = None, p2 = None, gpio = None):
		"""Define flip-flop pins for each channel. Optional to define an alternate gpio for the channel."""
		
		if (chan < 0 or chan > 7):
			logging.debug("Incorrect channel: " + str(chan))
		if (name in self.channels):
			logging.debug("Name must be unique. Please make sure all channels have a different name. " + str(name))
			return
		for b in self.channels:
			if (self.channels[b].chan == chan):
				logging.debug("Channel defined already: " + str(chan))
				return
		if (gpio is None):
			mcp = self.gpio
		if (p1 is None and p2 is None):
			self.channels[name] = channel(chan, mcp, p1, p2)
		elif (p1 is not None and p2 is not None):
			self.channels[name] = channel(chan, mcp, p1, p2)
		else:
			logging.debug("Only one flip flop pin given, please give 2 pins for a complete flip-flop circuit.")
			

	def getMeasurement(self, name, rtype, check = False):
		"""Get a reading of soil moisture level."""

		level = 0.0
		if (self.channels[name].locked and not check):
			return(level)
		gpo = self.channels[name].mcp
		with self.channels[name].lock:
			for i in range(self.samples):
				if (self.channels[name].ff):
					gpo.output(self.channels[name].p1, self.channels[name].ffstate)
					gpo.output(self.channels[name].p2, not self.channels[name].ffstate)
					self.channels[name].ffstate = not self.channels[name].ffstate
				level += self.readChannel(name)
			if (self.channels[name].ff):
				gpo.output((self.channels[name].p1, self.channels[name].p2), False)
		level /= self.samples
		if(rtype == 0):
			return(round(level, 1))
		elif(rtype == 1):
			return(self.convertToPrec(level, 1))


	def setDebug(self, output):
		"""\t\tEnable debug mode to provide more data, either in
		the console window ("cons") or in the logfile ("log") (not recommended, lots of data)."""

		if (output == "cons" or output == "log"):
			self.debug = True
			self.debug_output = output
		else:
			logging.debug("Set output to either \"cons\" or \"log\".")


	def debugReturn(self, name, value):
		"""Debug data is collected and displayed in the console or logfile"""

		dbgmsg = "Channel: "
		if (not self.channels[name].ffstate):
			dbgmsg += str(name) + "\tCor value: " + str(self.bits - value) + "\t"
		else:
			dbgmsg += str(name) + "\tValue: " + str(value) + "\t"
		if (self.channels[name].ff):
			p1 = ""
			p2 = ""
			if (self.channels[name].ffstate):
				p1 = "Off"
				p2 = "On"
			else:
				p1 = "On"
				p2 = "Off"
			dbgmsg += "Pin 1: " + str(self.channels[name].p1) + "\tState: "  + p1
			dbgmsg += "\nPin 2: " + str(self.channels[name].p2) + "\tState: " + p2
			dbgmsg += "\tFlip-Flop State: " + str(self.channels[name].ffstate) + "\tgpioDev: " + str(hex(self.channels[name].mcp.devAddr))
		else:
			dbgmsg += "No flip-flop."
		if (self.debug_output == "log"):
			logging.debug(dbgmsg)
		elif (self.debug_output == "cons"):
			print(dbgmsg)
			

	def convertToPrec(self, data, places):
		"""Returns the percentage value of the number."""

		m = ((data * 100) / float(self.bits))
		return(round(m, places))



class mcp3208(adc):

	bits = 4095

	def readChannel(self, name):
		r = self.spi.xfer2([4 | 2 | (self.channels[name].chan >> 2), (self.channels[name].chan & 3) << 6, 0])
		data = ((r[1] & 15) << 8) + r[2]
#		adcdata = self.spi.xfer2([96 + (4 * self.channels[name].chan), 0, 0])
#		data = int((adcdata[1] << 4) + (adcdata[2] >> 4))
		if (self.debug):
			self.debugReturn(name, data)
		if (self.channels[name].ffstate):
			return(data)
		else:
			return(self.bits - data)



class mcp3008(adc):
	
	bits = 1023

	def readChannel(self, name):
		adcdata = self.spi.xfer2([1, (8 + self.channels[name].chan) << 4, 0])
		data = int(((adcdata[1]&3) << 8) + adcdata[2])
		if (self.debug):
			self.debugReturn(name, data)
		if (self.channels[name].ffstate):
			return(data)
		else:
			return(self.bits - data)