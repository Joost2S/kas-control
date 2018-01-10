﻿#!/usr/bin/python3
 
# Author: J. Saarloos
# v1.4.1	06-01-2018

"""
Small library to control and use the DS18B20 temperature sensor.
Run getTdev to get a list of all the sensors, then make a ds18b20 object for each sensor.
Objects can be set with a name, or a name can be set later.
"""
"""
000006d218ac = school
000007c0d519 = kas_mam
03168bf394ff = thuis_buiten
0516b50d41ff = thuis_binnen
0416c170a7ff = WindowPlanter_board
"""

import glob
import logging


class ds18b20(object):
	
	dir = ""
	addr = ""
	name = ""

	def __init__(self, addr, name = None):

		self.dir = "/sys/bus/w1/devices/28-{}/w1_slave".format(addr)
		self.addr = addr
		self.name = name

	def setName(self, name):
		self.name = str(name)

	def getTemp(self):
		"""Get the current temperature from the sensor"""

		try:
			fileobj = open(self.dir, "r")
			lines = fileobj.readlines()
			fileobj.close()
		except:
			logging.error(self.addr + " not found.")
			return(None)
		status = lines[0].strip()[-3:]
		if (status == "YES"):
			ok = False
			tempstr = ""
			for l in lines[1][-8:]:
				if (ok):
					tempstr += l
				elif (l == "="):
					ok = True
			try:
				t = round(float(tempstr)/1000, 1)
			except ValueError:
				logging.error("Sensor {0} at address {1} failed conversion to float: {2}".format(self.name, self.addr, lines[1]))
				return(False)
			if (t == 85.0):
				logging.error("Init fail code given, sensor {0} at address {1} has a  problem.".format(self.name, self.addr))
				return(False)
			return(t)
		else:
			logging.error("Status of temp sensor {0} is '{1}', please check sensor.".format(str(self.addr), str(status)))
			return(False)

class tdevManager(object):

	__devAddrs = []
	__devList = {}

	def __init__(self):
		self.__getTdevs()

	def __getTdevs(self):
		"""Returns a list with the location of each DS18B20 temp sensor."""

		with glob.glob("/sys/bus/w1/devices/28*") as devicelist:
			if (devicelist == None):
				logging.warning("No temp devices found.")
				return(None)
			for d in devicelist:
				self.__devAddrs.append(d[-12:])

	def getTdevList(self):
		return(self.__devAddrs)

	def getMeasurement(self, name):
		
		if (name in self.__devList.keys()):
			return(self.__devList[name].getTemp())
		return(None)

	def setDev(self, name, addr):

		if (addr in self.__devAddrs):
			if (not name in self.__devList.keys()):
				for dev in self.__devList.values():
					if (dev.addr == addr):
						logging.error("Device with address {} is already assigned.".format(addr))
						return
				self.__devList[name] = ds18b20(addr, name)
			else:
				logging.error("Name {} already exists. Please enter a unique name for each device.".format(name))


if __name__ == "__main__":
	import sys
	import time
	
	mgr = tdevManager()
	devNames = []
	template = ""
	for i, addr in enumerate(mgr.getTdevList()):
		name = "Sensor{}".format(i + 1)
		devNames.append(name)
		template += "|{}\t".format(addr)
		mgr.setDev(name, addr)
	template += "\n"
	for dev in devNames:
		template += "|{}\t\t"
	template += "\n"

	while (1):
		try:
			temps = []
			for dev in devNames:
				temps.append(mgr.getMeasurement(dev))
			print(template.format(*temps))
			time.sleep(5)
		except KeyboardInterrupt:
			sys.exit()

	"""
	names = getTdev()
	tdevList = []
	for i, tdev in enumerate(names):
		print(tdev)
		tdevList.append(ds18b20(tdev, "temp" + str(i)))
	del(names)
	while(1):
		try:
			line1 = ""
			line2 = ""
			for dev in tdevList:
				line1 += dev.name + "\t|"
				line2 += str(dev.getTemp()) + "\t\t|"
			print(line1 + "\n" + line2)
			time.sleep(5)
		except KeyboardInterrupt:
			sys.exit()
	"""