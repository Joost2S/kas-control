#!/usr/bin/python3
 
# Author: J. Saarloos
# v1.2	01-06-2017

"""
Small library to control and use the DS18B20 temperature sensor.
Run getTdev to get a list of all the sensors, then make a ds18b20 object for each sensor.
Objects can be set with a name, or a name can be set later.
"""
"""
/sys/bus/w1/devices/28-000006d218ac/w1_slave = school
/sys/bus/w1/devices/28-000007c0d519/w1_slave = kas_mam
/sys/bus/w1/devices/28-03168bf394ff/w1_slave = thuis_buiten
/sys/bus/w1/devices/28-0516b50d41ff/w1_slave = thuis_binnen
"""

import glob
import logging


class ds18b20(object):
	
	dev = ""
	name = ""

	def __init__(self, dev, name = None):
		self.dev = dev
		self.name = name

	def setName(self, name):
		self.name = name

	def getTemp(self):
		"""Get the current temperature from the sensor"""

		try:
			fileobj = open(self.dev, "r")
			lines = fileobj.readlines()
			fileobj.close()
		except:
			logging.error(self.dev + " not found.")
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
				tempval = float(tempstr)/1000
			except ValueError:
				logging.error(str(self.dev).strip() + " failed conversion to float: " + str(lines[1]).strip())
				tempval = 0.0
			t = float("%.1f" % tempval)
			if (t == 85.0):
				logging.error("Init fail code given, sensor " + str(self.dev).strip() + " has a  problem.")
				return(None)
			return(t)
		else:
			logging.error("Status of temp sensor {0} is '{1}', please check sensor.".format(str(self.dev), str(status)))
			return(None)

def getTdev():
	"""Returns a list with the location of each DS18B20 temp sensor."""

	devicelist = glob.glob("/sys/bus/w1/devices/28*")
	if (len(devicelist) == 0):
		logging.debug("No temp device found.")
		return(None)
	devList = []
	for d in devicelist:
		devList.append(d + "/w1_slave")
	return(devList)