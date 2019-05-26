#!/usr/bin/python3

# Author: J. Saarloos
# v1.04.05	24-05-2019

"""
Small module to control and use the DS18B20 temperature sensor.
Run getTdev to get a list of all the sensors, then make a ds18b20 object for each sensor.
"""


import logging


class ds18b20(object):

	dir = ""
	addr = ""

	def __init__(self, addr):

		self.dir = "/sys/bus/w1/devices/28-{}/w1_slave".format(addr)
		self.addr = addr

	def getTemp(self):
		"""Get the current temperature from the sensor"""

		try:
			fileobj = open(self.dir, "r")
			lines = fileobj.readlines()
			fileobj.close()
		except FileNotFoundError:
			logging.error(self.addr + " not found.")
			return False
		status = lines[0].strip()[-3:]
		if status == "YES":
			startRead = False
			tempstr = ""
			for l in lines[1][-8:]:
				if startRead:
					tempstr += l
				elif l == "=":
					startRead = True
			try:
				t = round(float(tempstr)/1000, 1)
			except ValueError:
				logging.error("Temperature sensor at address {} failed conversion to float: {}".format(self.addr, lines[1]))
				return False
			if  t == 85.0:
				logging.error("Init fail code given, temperature sensor at address {} has a  problem.".format(self.addr))
				return False
			return t
		else:
			logging.error("Status of temperature sensor {0} is '{1}', please check sensor.".format(str(self.addr), str(status)))
			return False
