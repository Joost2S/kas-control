#!/usr/bin/python3

# Author: J. Saarloos
# v0.01.02	25-05-2019


import logging
import spidev
import uuid

from Code.kascontrol.electronics.drivers.spi_74ls138 import SPI_74LS138
from Code.kascontrol.globstuff import globstuff as gs


class SPImanager(object):

	__devList = dict()
	ls138 = None
	spiBus = None

	def __init__(self, gpio):
		super(SPImanager, self).__init__()

		self.spiBus = spidev.SpiDev()
		self.spiBus.max_speed_hz = 2000000
		self.spiBus.open(0, 0)
		try:
			data = gs.getSetupFile("hardware")["74LS138"]
			self.ls138 = SPI_74LS138(data["pins"], gpio)
		except KeyError:
			self.ls138 = None


	def registerDevice(self, devChannel):

		uid = uuid.uuid4()
		if self.ls138 is not None:
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

	def readbytes(self, devChannel, n):

		if self.__setSpiForTransaction(devChannel):
			return self.spiBus.readbytes(n)
		return None

	def writebytes(self, devChannel, data):

		if self.__setSpiForTransaction(devChannel):
			return self.spiBus.writebytes(data)
		return None

	def writebytes2(self, devChannel, data):

		if self.__setSpiForTransaction(devChannel):
			return self.spiBus.writebytes2(data)
		return None

	def xfer(self, devChannel, data):

		if self.__setSpiForTransaction(devChannel):
			return self.spiBus.xfer(data)
		return None

	def xfer2(self, devChannel, data):

		if self.__setSpiForTransaction(devChannel):
			return self.spiBus.xfer2(data)
		return None

	def xfer3(self, devChannel, data):

		if self.__setSpiForTransaction(devChannel):
			return self.spiBus.xfer3(data)
		return None

	def __setSpiForTransaction(self, devChannel):

		if devChannel not in self.__devList.keys():
			logging.debug("UUID used to access SPI does not exist.")
			return False
		if self.ls138 is not None:
			self.ls138.set(self.__devList[devChannel])
		return True

	def mode(self, value: int=None):

		if value is None:
			return self.spiBus.mode
		elif 0 <= value < 4:
			self.spiBus.mode = value
		else:
			logging.debug("Tried to set incorrect mode for the SPI bus: {}".format(value))

	def close(self):
		self.spiBus.close()
