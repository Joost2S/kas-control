#!/usr/bin/python3

# Author: J. Saarloos
# v0.01.00	25-04-2019


from abc import ABCMeta, abstractmethod
import time

from ...globstuff import globstuff as gs
from .hwbase import HWbase


class PowerControllerInterface(HWbase):
	__metaclass__ = ABCMeta

	def __init__(self):
		super(PowerControllerInterface, self).__init__()

	def requestPower(self, *cur):
		"""Use this method to check if enough power is available for the requested action."""

		# There is a delay of a second so the effects of the last request can be noticed.
		while ((time.time() - self.__lastPowerRequest) < 1.0):
			time.sleep(1)
		self.__lastPowerRequest = time.time()
		if (gs.hwOptions["powermonitor"]):
			current = self.__ina["12v"].getCurrent()		# get current power draw from the PSU.
		else:
			# TODO: get ID, time, power, priority
			return (gs.pwrmgr.addRequest("a", "t", "p", "pri"))
		if (isinstance(cur[0], int)):
			for c in cur:
				current += c
		else:
			for c in cur:
				current += c.power
		print("Expected power draw: " + str(current) + " mA")
		if (current > self.__maxPower):
			return(False)
		return(True)

	@abstractmethod
	def requestData(self, stype = None, name = None, caller = None, perc = False):
		return super().requestData(stype = stype, name = name, caller = caller, perc = perc)
