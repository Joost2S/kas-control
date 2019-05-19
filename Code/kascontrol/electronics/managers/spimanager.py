#!/usr/bin/python3

# Author: J. Saarloos
# v0.01.01	19-05-2019


import logging
import spidev
import uuid

from Code.kascontrol.electronics.drivers.spi_74ls138 import SPI_74LS138
from Code.kascontrol.globstuff import globstuff as gs
from Code.kascontrol.utils.errors import SpiConfigError


class SPImanager(object):

	__devList = dict()
	spi = None
	spiBus = None

	def __init__(self, gpio):
		super(SPImanager, self).__init__()

		self.spiBus = spidev.SpiDev()
		self.spiBus.max_speed_hz = 2000000
		self.spiBus.open(0, 0)
		try:
			data = gs.getSetupFile("hardware")["74LS138"]
			self.gpio = gpio
			self.__set74LS138(data)
		except KeyError:
			self.__setSPI()


	def __setSPI(self):

		self.spi = self.spiBus

	def __set74LS138(self, data):

		try:
			self.spi = SPI_74LS138(data["pins"], self.spiBus, self.gpio)
		except KeyError:
			raise SpiConfigError

	def registerDevice(self, devChannel):

		uid = uuid.uuid4()
		if isinstance(self.spi, SPI_74LS138):
			if 0 < devChannel < 8:
				if devChannel in self.__devList.values():
					logging.error("SPI channel {} already in use.".format(devChannel))
					return False
				self.__devList[uid] = devChannel
				return uid
			logging.warning("Could not register SPI device. Invalid SPI channel: {}".format(devChannel))
			return False
		if len(self.__devList) == 0:
			self.__devList[uid] = 0
			return uid
		logging.warning("Could not register SPI device. Invalid SPI channel: {}".format(devChannel))
		return False

	def xfer(self, dev, data):

		if isinstance(self.spi, SPI_74LS138):
			try:
				return self.spi.xfer(self.__devList[dev], data)
			except KeyError:
				logging.debug("Wrong uid used to access SPI.")
			return
		if dev in self.__devList.keys():
			return self.spi.xfer2(data)
		logging.debug("Wrong uid used to access SPI.")
