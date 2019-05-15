#!/usr/bin/python3

# Author: J. Saarloos
# v0.01.01	10-05-2019


from abc import ABCMeta, abstractmethod

from Code.kascontrol.globstuff import globstuff as gs
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
	def requestData(self, stype=None, name=None, formatted=None):
		return super().requestData(stype=stype, name=name, formatted=formatted)

	@abstractmethod
	def requestPower(self, *cur):
		return super().requestPower(cur)
