#!/usr/bin/python3

# Author: J. Saarloos
# v0.01.00	25-04-2019


from abc import ABCMeta, abstractmethod

from ...globstuff import globstuff as gs
from .hwbase import HWbase


class PowerLEDinterface(HWbase):

	__metaclass__ = ABCMeta

	def __init__(self):
		super(PowerLEDinterface, self).__init__()

	def powerLEDtoggle(self, channel):
		"""Toggle powerLED channel. Can only turn on if channel is set."""

		if (0 < channel <= len(gs.powerLEDpins)):
			if (self.__plcontroller.state(channel)[0]):
				self.__plcontroller.turnOff(channel)
				return(True)
			if (self.requestPower(self.__plcontroller.state(channel)[2])):
				self.__plcontroller.turnOn(channel)
				return(True)
		return(False)

	def powerLEDon(self, channel):
		"""Turn on powerLED channel. Only possible if set."""

		if (0 < channel <= len(gs.powerLEDpins)):
			if (self.requestPower(self.__plcontroller.state(channel)[2])):
				self.__plcontroller.turnOn(channel)
				return(True)
		return(False)

	def powerLEDoff(self, channel):
		"""Turn off powerLED channel."""

		if (0 < channel <= len(gs.powerLEDpins)):
			self.__plcontroller.turnOff(channel)

	def powerLEDset(self, channel, mode):
		"""Set powerLED channel to mode: '1ww', '3ww', '3ir' to enable channel."""

		if (0 < channel <= len(gs.powerLEDpins)):
			self.__plcontroller.setLED(channel, mode)

	def powerLEDstate(self, channel):
		"""Returns state, mode and power of the powerLEDchannel."""

		if (0 < channel <= len(gs.powerLEDpins)):
			return(self.__plcontroller.state(channel))

	@abstractmethod
	def requestData(self, stype = None, name = None, caller = None, perc = False):
		return super().requestData(stype = stype, name = name, caller = caller, perc = perc)

	@abstractmethod
	def requestPower(self, *cur):
		return super().requestPower(cur)
