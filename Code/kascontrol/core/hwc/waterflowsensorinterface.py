#!/usr/bin/python3

# Author: J. Saarloos
# v0.01.00	25-04-2019


from abc import ABCMeta, abstractmethod

from ...globstuff import globstuff as gs
from .hwbase import HWbase


class WaterFlowSensorInterface(HWbase):
	__metaclass__ = ABCMeta

	def __init__(self):
		super(WaterFlowSensorInterface, self).__init__()

	def getFlowSensor(self, name):
		if (name in self.__flowSensors.keys()):
			return self.__flowSensors[name]
		return False

	@abstractmethod
	def requestData(self, stype=None, name=None, caller=None, perc=False):
		return super().requestData(stype=stype, name=name, caller=caller, perc=perc)


	@abstractmethod
	def requestPower(self, *cur):
		return super().requestPower(cur)
