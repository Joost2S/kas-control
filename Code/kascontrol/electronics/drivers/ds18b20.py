#!/usr/bin/python3

# Author: J. Saarloos
# v1.4.4	24-04-2019

"""
Small module to control and use the DS18B20 temperature sensor.
Run getTdev to get a list of all the sensors, then make a ds18b20 object for each sensor.
Objects can be set with a name, or a name can be set later.
"""


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
