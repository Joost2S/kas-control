#! /usr/bin/python

# Author: J. Saarloos
# v0.01.00	08-05-2019


import smbus


class ArduinoFlowmeter(object):

	def __init__(self, address, smBus=None):

		self.address = address
		if smBus is None:
			self.bus = smBus
		else:
			self.bus = smbus.SMBus(1)
		self.__VALVE_NO = 6
		self.__subsAvailable = 2

	def getMonitorData(self, channel):
		return self.__getData(0, channel)

	def getDbData(self, channel):
		return self.__getData(1, channel)

	def subscribe(self, channel):
		"""Returns the subscription slot nr."""

		check, data = self.__getData(2, channel)
		if data == 404:
			return False, "No subscription slots available."
		return check, data

	def endSubscription(self, channel, slot):
		if slot >= self.__subsAvailable:
			return False, "Invalid subscription slot."
		function = slot + 3
		return self.__getData(function, channel)

	def __getData(self, function, channel):

		if not 0 <= function < 5:
			return False, "Not a valid function."
		if 0 <= channel < self.__VALVE_NO:
			return False, "Channel not within range."

		var = (function << 4) + channel
		value = self.bus.read_word_data(self.address, var)

		if value < (2 ** 16) - 2:
			return True, value
		if value == 2 ** 16:
			return False, "invalid function"
		if value == (2 ** 16) - 1:
			return False, "invalid channel"
		if value == (2 ** 16) - 2:
			return False, "invalid subscription"
