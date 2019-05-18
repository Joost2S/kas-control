#!/usr/bin/python3

# Author: J. Saarloos
# v0.01.00	17-05-2019

"""
Manages all ADC pins on supported devices.
Upon setting a pin a UUID is returned by which it is easy to get the
data that is required through the read() method. It is also still
possible to get the data by the readPin() method. This reqires the
address, chip number or board designation of the ADC chip along with
the channel.
"""


from Code.kascontrol.electronics.drivers.mcp3x08 import MCP3004
from Code.kascontrol.electronics.drivers.mcp3x08 import MCP3008
from Code.kascontrol.electronics.drivers.mcp3x08 import MCP3204
from Code.kascontrol.electronics.drivers.mcp3x08 import MCP3208
from Code.kascontrol.globstuff import globstuff as gs


class ADCmanager(object):

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
		for adcType, setup in data.items():
			try:
				chip = self.supportedDevices[adcType]()
			except KeyError:
				continue
			# TODO: finish

	def setPin(self, pin, address=None, devNr=None, devDes=None):
		pass

	def read(self, pin):

		if pin not in self.__setPins:
			return

	def readPin(self, pin, address=None, devNr=None, devDes=None):
		pass
