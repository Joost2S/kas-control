#!/usr/bin/python3

# Author: J. Saarloos
# v0.01.02	19-05-2019

"""
Manages all ADC pins on supported devices.
Upon setting a pin a UUID is returned by which it is easy to get the
data that is required through the read() method. It is also still
possible to get the data by the readPin() method. This reqires the
address, chip number or board designation of the ADC chip along with
the channel.
Flip-flop pins will be set here and the uuid will be passed to the
appropriaate IC.
"""


import logging
import threading
import uuid

from Code.kascontrol.electronics.drivers.mcp3x08 import MCP3004
from Code.kascontrol.electronics.drivers.mcp3x08 import MCP3008
from Code.kascontrol.electronics.drivers.mcp3x08 import MCP3204
from Code.kascontrol.electronics.drivers.mcp3x08 import MCP3208
from Code.kascontrol.globstuff import globstuff as gs
from Code.kascontrol.utils.errors import AbortInitError, ADCconfigError


class ADCmanager(object):

	__adclock = None
	devByAddr = dict()
	devByBoardDes = dict()
	devByNr = dict()
	devSetups = list()
	finalized = False
	__setPins = list() # pins that are set up are registered here so no duplicates are set.
					# gets deleted upon finalisation of manager
	pinList = dict() # list of all set pins. Used throughout program lifecycle.

	def __init__(self, gpio, spi):
		super(ADCmanager, self).__init__()

		self.__adclock = threading.Lock()
		self.devices = dict()
		self.gpio = gpio
		self.spi = spi
		self.supportedDevices = {
			"mcp3004": MCP3004,
			"mcp3008": MCP3008,
			"mcp3204": MCP3204,
			"mcp3208": MCP3208
		}
		self.setDevices()

	def setDevices(self):

		data = gs.getSetupFile("hardware")["adc"]
		for adcType, devs in data.items():
			for setup in devs:
				try:
					uid = uuid.uuid4()
					spi = self.spi.registerDevice(setup["spiChannel"])
					if spi is False:
						logging.critical("Failed to register spi channel for ADC {}.".format(setup["boardDesignation"]))
					dev = self.supportedDevices[adcType](
						spi=spi,
						dev=self.spi,
						tlock=self.__adclock,
						gpio=self.gpio
					)
					self.__setDevChannels(dev, setup["channels"], setup["boardDesignation"])
					self.devices[uid] = dev
					self.devByAddr[setup["spiChannel"]] = dev
					self.devByBoardDes[setup["boardDesignation"]] = dev
					self.devByNr[setup["number"]] = dev
				except KeyError:
					continue
				except ADCconfigError:
					raise AbortInitError
				# TODO: finish

	def __setDevChannels(self, dev, channels, devDes):

		if len(channels) != dev.chanAmount:
			logging.critical("Incorrent amount of channels defined for ADC device {}.".format(devDes))
			raise ADCconfigError
		for i, setup in enumerate(channels):
			if not setup["flip-flop"]:
				dev.setChannel(i, i)
			else:
				try:
					p1 = setup["pins"][0]
					p2 = setup["pins"][1]
				except KeyError:
					logging.critical("Too few flip-flop pins have been defined for channel {} on ADC {}.".format(i, devDes))
					raise ADCconfigError
				try:
					ff1 = self.gpio.setPin(p1["pin"], False, devNr=p1["devNumber"])
					ff2 = self.gpio.setPin(p2["pin"], False, devNr=p2["devNumber"])
				except KeyError:
					logging.critical("Flip-flop pins were incorrectly configured for channel {} on ADC {}.".format(i, devDes))
					raise ADCconfigError
				dev.setChannel(i, i, ff1, ff2)

	def setChannel(self, channel, address=None, devNr=None, devDes=None):
		pass

	def read(self, pin):

		if pin not in self.pinList:
			return

	def readPin(self, pin, address=None, devNr=None, devDes=None):
		pass
