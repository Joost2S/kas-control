#!/usr/bin/python3

# Author: J. Saarloos
# v0.01.01	10-05-2019


from abc import ABCMeta, abstractmethod

from ...globstuff import globstuff as gs
from .hwbase import HWbase


class FanInterface(HWbase):
	__metaclass__ = ABCMeta

	def __init__(self):
		super(FanInterface, self).__init__()

	def turnFanOn(self):

		# TODO: get temperature check if there is an associated sensor
		result = self.__fan.on()
		if result is True:
			return True, result
		return False, result

	def turnFanOff(self):

		report = self.__fan.off()
		if isinstance(report, dict):
			return True, report
		return False, report

	def getFanSatate(self):
		return self.__fan.state

	@abstractmethod
	def requestData(self, stype=None, name=None, formatted=None):
		return super().requestData(stype=stype, name=name, formatted=formatted)

	@abstractmethod
	def requestPower(self, *cur):
		return super().requestPower(cur)
