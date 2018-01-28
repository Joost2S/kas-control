#!/usr/bin/python3
 
# Author: J. Saarloos
# v0.0.2	27-01-2018

# For details, see datasheet: http://www.ti.com/lit/ds/symlink/ina219.pdf

import logging
import smbus


class ina219(object):

	__addr = 0
	__bus = None
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
		self.__bus = smbus.SMBus(1)


	def engage(self):

		if (not self.__engaged):
			conVal = 0
			calVal = 0
			self.bus.write_byte_data(self.devAddr, self.regMap["config"], conVal)
			self.bus.write_byte_data(self.devAddr, self.regMap["calibration"], calVal)
		else:
			logging.debug("INA219 device on " + hex(self.devAddr) + " is already enabled.")

	def setup(self, setting):

		if (not self.__engaged):
			pass
		else:
			logging.debug("INA219 device at {} already enabled, settings can't change anymore.".format(self.__addr))

	def getCurrent(self):

		if (self.__engaged):
			current = int(self.bus.read_byte_data(self.devAddr, self.regMap["current"]))
			return(current)

	def getVolage(self):

		if (self.__engaged):
			voltage = int(self.bus.read_byte_data(self.devAddr, self.regMap["busV"]))
			return(voltage)

	def getShuntVoltage(self):

		if (self.__engaged):
			shuntVoltage = int(self.bus.read_byte_data(self.devAddr, self.regMap["shuntV"]))
			return(shuntVoltage)

	def getPower(self):

		if (self.__engaged):
			power = int(self.bus.read_byte_data(self.devAddr, self.regMap["power"]))
			return(power)