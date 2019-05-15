#!/usr/bin/python3
 
# Author: J. Saarloos
# v0.3.01	09-05-2019

# For details, see datasheet: http://www.ti.com/lit/ds/symlink/ina219.pdf

import logging
import smbus


class INA219(object):

	__addr = 0				# i2c device address
	__bus = None			# i2c bus
	__rShunt = 0.0			# Usually small value resistor (0.1 - 0.01 ohm)
	__lineV = 0				# Normal line voltage. eg: 3.3, 5, 12
	__configVal = 0x399F	# Value for the configuration register.
	__calibVal = 0			# Value for the calibration register.
	__engaged = False		# Need to set the device first before using.
	__regMap = {
		  "config":	0x00,	
		  "shuntV" : 0x01,
		  "busV" : 0x02,
		  "power" : 0x03,
		  "current" : 0x04,
		  "calibration" : 0x05
		  }
	modes = ["Power-down",
			"Shunt voltage, triggered",
			"Bus voltage, triggered",
			"Shunt and bus, triggered",
			"ADC off (disabled)",
			"Shunt voltage, continuous",
			"Bus voltage, continuous",
			"Shunt and bus, continuous"]

	def __init__(self, addr, lineV, bus=None):
		
		self.__addr = addr
		if bus is None:
			self.__bus = smbus.SMBus(1)
		else:
			self.__bus = bus
		if (-26 <= lineV <= 26):
			self.__lineV = lineV
		else:
			raise ValueError("INA219 supports line voltage from -26 to +26 V.")


	def setConfig(self, PGA = 3, BADC = 3, SADC = 3, mode = 7, RST = False):
		"""
		For details on programming the configuration register: http://www.ti.com/lit/ds/symlink/ina219.pdf#%5B%7B%22num%22%3A179%2C%22gen%22%3A0%7D%2C%7B%22name%22%3A%22XYZ%22%7D%2C0%2C720%2C0%5D
		"""

		if (not self.__engaged):
			if (isinstance(mode, str)):
				try:
					mode = self.modes.index(mode)
				except ValueError:
					raise ValueError
			# Checking if values are correct
			if (0 > PGA >= 4 or 0 > BADC >= 12 or 0 > SADC >= 12 or 0 > mode >= 8):
				raise ValueError
			# Value for the configuration register.
			self.__configVal = int(RST) * (2 ** 15)
			# BRNG: Bus voltage range (16V : 0, 32V : 1)
			self.__configVal += int(self.__lineV > 16) * (2 ** 13)
			# PGA sets the gain and range of the shunt voltage.
			self.__configVal += PGA * 2 ** 11
			# BADC Bus and Shunt ADC Resolution/Averaging
			for v in [BADC, SADC]:
				if (v > 3):
					v += 4
				self.__configVal += v * (2 ** 7)
			self.__configVal += mode
		else:
			logging.debug("INA219 device on addr " + hex(self.devAddr) + " is already enabled.")

	def setCalibration(self, maxCurrent, rShunt):
		
		if (not self.__engaged):
			currentLSB = maxCurrent / (2 ** 15)
			cal = int(0.04096 / (currentLSB * rShunt))
			if (cal < (2 ** 16)):
				self.__calibVal = cal
		else:
			logging.debug("INA219 device on addr " + hex(self.devAddr) + " is already enabled.")

	def engage(self):

		if (not self.__engaged):
			self.bus.write_byte_data(self.devAddr, self.regMap["config"], self.__configVal)
			self.bus.write_byte_data(self.devAddr, self.regMap["calibration"], self.__calibVal)
			self.__engaged = True
		else:
			logging.debug("INA219 device on addr " + hex(self.devAddr) + " is already enabled.")

	def reset(self):

		if (self.__engaged):
			self.__engaged = False
			self.bus.write_byte_data(self.devAddr, self.regMap["config"], 0x399F)
			self.bus.write_byte_data(self.devAddr, self.regMap["calibration", 0x00])

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
