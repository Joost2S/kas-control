#!/usr/bin/python3

# Author: J. Saarloos
# v0.01.00	10-05-2019


from abc import ABCMeta, abstractmethod
import logging

from Code.kascontrol.globstuff import globstuff as gs
from Code.kascontrol.core.hwc.hwbase import HWbase


class RequestData(HWbase):

	__metaclass__ = ABCMeta

	def __init__(self):
		super(RequestData, self).__init__()

	def requestData(self, stype=None, name=None, formatted=None, args=None):
		"""
		Main method for getting sensor data.
		Be aware that calling this method with different arguments will result in
		different types of variables being returned and even calling it with the
		same arguments may result in different types being returned at different times.
		"""

		if self.__spoof:
			return self.getSpoofData(stype=stype, name=name, formatted=formatted, args=args)
		try:
			# Get data from specific sensor.
			if name is not None:
				return self.__getDataFromSensor(stype, name, formatted, args)

			# Get data from all sensors of specified type.
			# return [[sensorname, value], ...]
			elif stype is not None:
				return self.__getDataByType(stype)

			# Get formatted data for text output.
			elif formatted is True:
				return self.__currentstats

			# Get all raw data for LEDbar, LCD, network client, etc.
			elif formatted is False:
				return self.__rawStats

		except:
			logging.error("Error occured during measurement of " + str(stype) + " at channel: " + str(name))
			return False

	def __getDataFromSensor(self, stype=None, name=None, formatted=None, args=None):
		name = name.replace("_", "-")
		if name in self.__sensors.keys():
			if stype is not None and stype is not self.__sensors[name]:
				return "Sensor {} is not of type {}.".format(name, stype)
			stype = self.__sensors[name][1]
			if stype == "mst":
				return self.__getMstData(name=name, formatted=formatted)
			if stype == "light":
				return self.__adc.getMeasurement(name, perc=formatted)
			if stype == "flow":
				if not gs.hwOptions["flowsensors"]:
					return None
				if args["caller"] == "db":
					# TODO: fix!
					return self.__flowSensors[name].storePulses()
				return self.__flowSensors[name].getFlowRate()
			if stype == "temp":
				if name not in self.__otherSensors and not gs.hwOptions["soiltemp"]:
					return None
				return self.__tempMGR.getMeasurement(name=name)
		elif stype == "pwr":
			return self.__getPowerData(name=name)

		# If name is the name of a group with option for sensortype.
		elif name in self.__groups.keys():
			return self.__getGroupData(name=name, stype=stype)
		else:
			logging.warning("Requested sensor does not exist. Name: {}".format(name))
			return False

	def __getDataByType(self, stype):
		data = []
		for n, t in self.__sensors.items():
			if t == stype:
				val = self.requestData(n)
				if val is False:
					val = "Error"
				data.append([n, val])
		return data

	def __getMstData(self, name, formatted=None):
		for g in self.__groups.values():
			if g.mstName == name:
				if formatted is True:
					return self.__adc.getMeasurement(name, perc=True)
				else:
					if not g.enabled or not g.connected:
						return None
					return self.__adc.getMeasurement(name)
		return None

	def __getPowerData(self, name):
		# name = "12vp"
		if name[-1] == "p":
			return self.__ina[name[:-1]].getPower()
		# name = "12vc"
		if name[-1] == "c":
			return self.__ina[name[:-1]].getCurrent()
		# name = "12vv"
		if name[-1] == "v":
			return self.__ina[name[:-1]].getVolage()
		# name = "12vs"
		if name[-1] == "s":
			return self.__ina[name[:-1]].getShuntVoltage()
		return None

	def __getGroupData(self, name, stype=None):
		if stype == "mst":
			return self.__groups[name].getM()
		if stype == "temp":
			return self.__groups[name].getT()
		if stype == "flow":
			return self.__groups[name].getF()
		return self.__groups[name].getSensorData()

	@abstractmethod
	def requestPower(self, *cur):
		return super().requestPower(cur)
