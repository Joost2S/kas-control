#!/usr/bin/python3

# Author: J. Saarloos
# v0.1.00	08-05-2019


import glob
import logging

from Code.kascontrol.electronics.drivers.cputemp import getCPUtemp
from Code.kascontrol.electronics.drivers.ds18b20 import ds18b20


class TDevManager(object):

	__devAddrs = []
	__devList = {}

	def __init__(self):
		super(TDevManager, self).__init__()
		self.__getTdevs()

	def __getTdevs(self):
		"""Returns a list with the location of each DS18B20 temp sensor."""

		devicelist = glob.glob("/sys/bus/w1/devices/28*")
		if (devicelist is None):
			logging.warning("No temp devices found.")
			return(None)
		for d in devicelist:
			self.__devAddrs.append(d[-12:])

	def getTdevList(self):
		return(self.__devAddrs)

	def getMeasurement(self, name):

		if name.lower() == "cpu":
			return getCPUtemp()
		if (name in self.__devList.keys()):
			return(self.__devList[name].getTemp())
		return(None)

	def setDev(self, name, addr):

		if (addr in self.__devAddrs):
			if (not name in self.__devList.keys()):
				for dev in self.__devList.values():
					if (dev.addr == addr):
						logging.error("Device with address {} is already assigned.".format(addr))
						return(False)
				self.__devList[name] = ds18b20(addr, name)
				return(True)
			logging.error("Name {} already exists. Please enter a unique name for each device.".format(name))
			return(False)


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
