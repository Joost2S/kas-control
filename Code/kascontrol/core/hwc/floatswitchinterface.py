#!/usr/bin/python3

# Author: J. Saarloos
# v0.01.01	10-05-2019


from abc import ABCMeta, abstractmethod

from ...globstuff import globstuff as gs
from .hwbase import HWbase


class FloatSwitchInterface(HWbase):
	__metaclass__ = ABCMeta

	def __init__(self):
		super(FloatSwitchInterface, self).__init__()

	def getFloatSwitchStatus(self):
		return self.__floatSwitch.getStatus()

	@abstractmethod
	def requestData(self, stype=None, name=None, formatted=None):
		return super().requestData(stype=stype, name=name, formatted=formatted)

	@abstractmethod
	def requestPower(self, *cur):
		return super().requestPower(cur)
