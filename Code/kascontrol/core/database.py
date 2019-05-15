#!/usr/bin/python3

# Author: J. Saarloos
# v0.4.06	25-04-2019

from abc import ABCMeta#, abstractmethod
import logging
import time

from ..globstuff import globstuff as gs
from.db.datalog import Datalog as dtl
from.db.dbinit import DBinit as dbi
from .db.dbplantinterface import DBplantInterface as dbp


class Database(dtl, dbp, dbi):

	__metaclass__ = ABCMeta

	__sensors = {"ambientl" : "light",
				 "ambientt" : "temp",
				 "out_sun" : "temp",
				 "out_shade" : "temp",
				 "PSU" : "temp",
				 "CPU" : "cputemp",
				 "totalw" : "flow",
				 "12vc" : "pwr",
				 "12vv" : "pwr",
				 "soil_g1" : "mst",
				 "soil_g2" : "mst",
				 "soil_g3" : "mst",
				 "soil_g4" : "mst",
				 "temp_g1" : "temp",
				 "temp_g2" : "temp",
				 "temp_g3" : "temp",
				 "temp_g4" : "temp",
				 "flow_g1" : "flow",
				 "flow_g2" : "flow",
				 "flow_g3" : "flow",
				 "flow_g4" : "flow"}
	__groups = {"group1" : ["soil_g1", "temp_g1", "flow_g1"],
				 "group2" : ["soil_g2", "temp_g2", "flow_g2"],
				 "group3" : ["soil_g3", "temp_g3", "flow_g3"],
				 "group4" : ["soil_g4", "temp_g4", "flow_g4"]}
	__fileName = ""
	__species = ["Generic", "Weed", "Cannabis", "Marijuana", "Hemp", "Tomato", "Chili pepper"]

	def __init__(self, reset=False):
		super(Database, self).__init__()

		self.__startup(reset)
		gs.db = self

	def wateringEvent(self, group, start, end, amount):
		"""
		Use this method to add a watering event to the DB.
		"""

		# TODO: get data from groupname
		if (not (0 < group <= len(self.__groups))):
			logging.info("Unknown group. Please enter valid group number. 1 - {}".format(len(self.__groups)))
			return(False)
		subquery = "SELECT plantID FROM groups WHERE id = {}".format(group)
		query = "INSERT INTO watering (id, starttime, endtime, amount) "
		query += "VALUES (({}), {}, {}, {});".format(subquery, start, end, amount)
		rows = self.__dbWrite(query)
		if (rows == 0):
			logging.error("Failed to add Watering event.")
			return(False)
		return(True)

	def getWaterEvents(self, group = None, amount = 20):
		"""
		Get the last watering events from 1 or all currently active container.
		amount is the records per container.
		Returns 2 lists of equal length:
		list 1: [[groupID, plantname],]
		list 2: [None, or [[starttime, time, water],],]
		"""

		# Get current plants
		query  = "SELECT g.groupName, p.name FROM groups AS g "
		query += "LEFT JOIN plants AS p ON g.plantID = p.plantID "
		if (group is not None):
			query += "WHERE g.groupName = '{}' ".format(group)
		query += "GROUP BY g.groupID;"
		data1 = self.__dbRead(query)
		if (data1 is None):
			return(None, None)
		data2 = []
		# Get the last watering events from the sensors
		for row in data1:
			group = row[0]
			query  = "SELECT w.starttime, w.endtime - w.starttime AS time, w.amount "
			query += "FROM watering AS w "
			query += "INNER JOIN groups AS g on w.plantID = g.plantID "
			query += "INNER JOIN plants AS p ON g.plantID = p.plantID "
			query += "WHERE g.groupName = '{}'" .format(group)
			query += "ORDER BY w.starttime ASC "
			query += "LIMIT {};".format(amount)
			data2.append(self.__dbRead(query))
		return(data1, data2)

	def getTriggers(self, group):

		if (not group in self.__groups.keys()):
			self.lastResult = False
			return("Unknown group. Please enter valid group number. 1 - {}".format(len(self.__groups)))
		subquery = "(SELECT plantID FROM groups WHERE id = {})".format(group)
		query = "SELECT lowertrig, uppertrig FROM plants WHERE id = {};".format(subquery)
		triggers = self.__dbRead(query)
		return(triggers[0])

	def setTriggers(self, group, lower = None, upper = None):
		"""Set one or both triggers of a container."""

		if (not group in self.__groups.keys()):
			self.lastResult = False
			print("Unknown group. Please enter valid group number. 1 - {}".format(len(self.__groups)))
			return
		subquery = "(SELECT id FROM groups WHERE groupID = {})".format(group)
		query = "UPDATE plants SET lowertrig = {}, uppertrig = {} WHERE id = {};".format(int(lower), int(upper), subquery)
		self.__dbWrite(query)

	def getContainerHistory(self, group):
		"""Returns the names and some info of all the plants associated with a conainer."""

		if (not group in self.__groups.keys()):
			self.lastResult = False
			return("Unknown group. Please enter valid group number. 1 - {}".format(len(self.__groups)))
		query   = "select p.name, s.species, total(w.amount)/1000 as total, p.dateRemoved == 0 as moi"
		query  += "from plants as p"
		query  += "left join plantTypes as s on s.typeID = p.plantType"
		query  += "left outer join watering as w on w.plantID = p.plantID"
		query  += "where p.groupID = {} group by p.plantID".format(group)
		return(self.__dbRead(query))

	def getSensorData(self, start, end = 0.0, names = None, types = None, group = None):
		"""Returns a 2D array with the sensor data. First row contains the sensor names."""
		"""
		SELECT datetime(timestamp, 'unixepoch', 'localtime') as t,
		sensor1, sensor2, sensor3
		FROM sensorData WHERE
		t > '2018-03-05';
		"""

		if (start == "min"):
			query = "SELECT min(timestamp) FROM sensorData;"
			return(self.__dbRead(query))

		st = float(time.time()) - float(start)*60*60*24
		if (end > 0):
			en = "AND timestamp < {};".format(float(time.time()) - float(end)*60*60*24)
		else:
			en = ";"
		sel = "timestamp"
		if (names is not None):
			if (isinstance(names, str)):
				names = [names]
			for n in names:
				if (n in self.__sensors.keys()):
					sel += ", {}".format(n)
			if (sel == "timestamp"):
				return(None)
		elif (types is not None):
			if (isinstance(types, str)):
				types = [types]
			for t in types:
				for fn, ft in self.__sensors.items():
					if (ft == t):
						sel += ", {}".format(fn)
			if (len(sel) == 0):
				return(None)
		elif (group is not None):
			if (group in self.__groups.keys()):
				for name in self.__groups[group]:
					sel += ", {}".format(name)
			else:
				return(None)
		else:
			sel = "*"
		query = "SELECT {} FROM sensorData WHERE timestamp > {} {}".format(sel, st, en)
		snames = [sel.split(",")]
		data = self.__dbRead(query)
		if (data is None):
			return(None)
		return(snames.extend(data))

	def getContainerNameTriggers(self, container):
		"""Returns [plantname, lowtrig, hightrig]"""

		query = "SELECT p.id, p.name, p.lowertrig, p.uppertrig "
		query += "FROM groups as g "
		query += "INNER JOIN plants as p ON g.plantID = p.plantID "
		query += "WHERE g.groupName = '{}';".format(container)
		data = self.__dbRead(query)
		if (data is None):
			return(data)
		return(data[0])
