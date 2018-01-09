#!/usr/bin/python3
 
# Author: J. Saarloos
# v0.0.1	04-01-2018

# For details, see datasheet: http://www.ti.com/lit/ds/symlink/ina219.pdf

import logging
import smbus


class ina219(object):

	__addr = 0
	__engaged = False
	__regMap = {
		  "config":	0x00,	
		  "shuntV" : 0x01,
		  "busV" : 0x02,
		  "power" : 0x03,
		  "current" : 0x04,
		  "calibration" : 0x05
		  }

	def __init__(self, addr):
		
		self.__addr = addr


	def engage(self):

		if (not self.__engaged):
			pass

	def settings(self, setting):

		if (not self.__engaged):
			pass
		else:
			logging.debug("INA219 device at {} already enabled, settings can't change anymore.".format(self.__addr))

	def getCurrent(self):

		if (self.__engaged):
			return(current)

	def getVolage(self):

		if (self.__engaged):
			return(voltage)

	def getPower(self):

		if (self.__engaged):
			return(power)