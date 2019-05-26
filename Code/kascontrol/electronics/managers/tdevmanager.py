#!/usr/bin/python3

# Author: J. Saarloos
# v0.1.01	24-05-2019


import glob
import logging
import uuid

from Code.kascontrol.electronics.drivers.cputemp import getCPUtemp
from Code.kascontrol.electronics.drivers.ds18b20 import ds18b20


class TDevManager(object):

	__devAddrs = []
	__devList = {}
	devByAddr = dict()
	devByBoardDes = dict()
	devByNr = dict()
	supportedDevices = ["ds18b20", "bmp280", "bme280", "bme680"]

	def __init__(self):
		super(TDevManager, self).__init__()
		self.__getTdevs()

	def __getTdevs(self):
		"""Returns a list with the location of each DS18B20 temp sensor."""

		devicelist = glob.glob("/sys/bus/w1/devices/28*")
		if devicelist is None:
			logging.warning("No temp devices found.")
			return None
		for d in devicelist:
			self.__devAddrs.append(d[-12:])

	def getTdevList(self):
		return self.__devAddrs

	def getMeasurement(self, name):

		if name.lower() == "cpu":
			return getCPUtemp()
		if name in self.__devList.keys():
			return self.__devList[name].getTemp()
		return None

	def setDev(self, addr, devType):

		if devType.lower() in self.supportedDevices:
			if devType.lower() == "ds18b20":
				return self.__setDS18B20device(addr)
		logging.warning("Tries to set temperature sensor of unspported type: {}".format(devType))
		return False

	def __setDS18B20device(self, addr):
		if addr not in self.__devAddrs:
			logging.error("No temperature device at address {}.".format(address))
			return False
		for dev in self.__devList.values():
			if dev.addr == addr:
				logging.error("Device with address {} is already assigned.".format(addr))
				return False
			uid = uuid.uuid4()
			self.__devList[uid] = ds18b20(addr)
			return uid
		logging.error("Name {} already exists. Please enter a unique name for each device.".format(name))
		return False


if __name__ == "__main__":
	import sys
	import time

	mgr = TDevManager()
	devNames = []
	template = ""
	for i, address in enumerate(mgr.getTdevList()):
		devName = "Sensor{}".format(i + 1)
		devNames.append(devName)
		template += "|{}\t".format(address)
		mgr.setDev(devName, address)
	template += "\n"
	for device in devNames:
		template += "|{}\t\t"
	template += "\n"

	while (1):
		try:
			temps = []
			for device in devNames:
				temps.append(mgr.getMeasurement(device))
			print(template.format(*temps))
			time.sleep(5)
		except KeyboardInterrupt:
			sys.exit()
