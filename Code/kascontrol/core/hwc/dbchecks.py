#!/usr/bin/python3

# Author: J. Saarloos
# v0.01.01	10-05-2019


from abc import ABCMeta, abstractmethod
from collections import OrderedDict

from ...globstuff import globstuff as gs
from .hwbase import HWbase


class DBchecks(HWbase):

	__metaclass__ = ABCMeta

	def __init__(self):
		super(DBchecks, self).__init__()

	def getDBgroups(self):
		"""The DB uses this to make a new db or check integrity on startup."""

		data = {}
		for n, g in self.__groups.items():
			# SQLite3 doesn't support dashes (-) in column names, so replace with underscore (_).
			names = [g.mstName.replace("-", "_")]
			if (gs.hwOptions["soiltemp"] and g.tempName is not None):
				names.append(g.tempName.replace("-", "_"))
			if (gs.hwOptions["flowsensors"] and g.flowName is not None):
				names.append(g.flowName.replace("-", "_"))
			data[n] = names
		return(data)

	def getDBcheckData(self):
		"""Returns a table to be compared with the sensor setup in the database as integrity check."""

		groups = {}
		for name, g in self.getDBgroups().values():
			for sensor in g:
				groups[sensor] = name
		dbCheckData = []
		for i, s, t in enumerate(OrderedDict(sorted(self.__sensors.items()))):
			dbCheckData.append([s.replace("-", "_"), t, None, None])
			if (t == "mst" or t == "light"):
				dbCheckData[i][3] = self.getADCres()
			if (s in groups):
				dbCheckData[i][2] = groups[s]
		return(dbCheckData)

	@abstractmethod
	def requestData(self, stype=None, name=None, formatted=None):
		return super().requestData(stype=stype, name=name, formatted=formatted)

	@abstractmethod
	def requestPower(self, *cur):
		return super().requestPower(cur)
