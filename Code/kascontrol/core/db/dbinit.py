#!/usr/bin/python3

# Author: J. Saarloos
# v0.1.01	10-05-2019


from abc import ABCMeta#, abstractmethod
import logging
import os
import sqlite3 as sql
import threading

from .base import BaseDBinterface
from .base import DBValidationError
from Code.kascontrol.globstuff import globstuff as gs


class DBinit(BaseDBinterface):

	__metaclass__ = ABCMeta

	def __init__(self):
		super(DBinit, self).__init__()

		self.__allowedTypes = ["mst", "light", "flow", "temp", "cputemp", "pwr"]
		self.__fileName = gs.dataloc + "datalog.db"
		self.interval = 5
		self.__species = ["Generic", "Weed", "Cannabis", "Marijuana", "Hemp", "Tomato", "Chili pepper"]
		self.__tables = ["sensorData", "sensorSetup", "groups", "plants", "plantTypes", "watering"]
		self.__tlock = threading.Lock()
		self.__views = ["defaultview", "sensorCheck"]
		for s, t in gs.control.getSensors().items():
			self.__sensors[s.replace("-", "_")] = t
		self.__groups = gs.control.getDBgroups()

	def __startup(self, reset):

		# if file already exists, run integrity check unless resetting the DB
		if reset:
			if (os.path.isfile(self.__fileName)):
				self.__dropTables()
			self.__createdb()

		if (os.path.isfile(self.__fileName)):
			self.__setLocalsFromDB()
			try:
				self.__validateDB()
			except DBValidationError:
				raise DBValidationError
			return
		else:
			self.__createdb()

	def __createdb(self):
		"""Check if a correctly named DB exists, or otherwise create it."""


		logging.debug("Creating new DB. " + str(self.__fileName))
		self.__fields = gs.control.getDBfields()

		# Creating sensorData table...
		sensorData = "CREATE TABLE sensorData (timestamp DATETIME NOT NULL"
		for fn, ft in self.__sensors.items():
			sensorData += ", " + "'{}'".format(fn)
			if (ft in self.__allowedTypes[:3]):
				sensorData += " REAL"
			else:
				sensorData += " INTEGER"
			sensorData += " NULL"
		sensorData += ");"

		# Creating sensorSetup table...
		sensorSetup  = "CREATE TABLE sensorSetup ("
		sensorSetup += "id INTEGER PRIMARY KEY, "
		sensorSetup += "sensorName TEXT NOT NULL, "
		sensorSetup += "sensorType TEXT NOT NULL, "
		sensorSetup += "groupID INTEGER REFERENCES groups(id) NULL, "
		sensorSetup += "resolution INTEGER NULL);"

		# Gathering data for sensorSetup table...
		sensorSData = []
		for i, f in enumerate(self.__sensors.items()):
			fn, ft = f
			subquery = "NULL"
			res = "NULL"
			if (ft == "mst" or ft == "light"):
				res = "4095"
			for n, g in self.__groups.items():
				if (fn in g):
					subquery = "(SELECT id FROM groups WHERE groupName = \'{}\')".format(n)
					break
			sensorSData.append("INSERT INTO sensorSetup(sensorName, sensorType, groupID, resolution)")
			sensorSData[i] += " VALUES ('{}', '{}', {}, {});".format(fn, ft, subquery, res)

		# Creating groups table...
		groups  = "CREATE TABLE groups ("
		groups += "id INTEGER PRIMARY KEY, "
		groups += "groupName TEXT NOT NULL, "
		groups += "plantID INTEGER REFERENCES plants(id) NULL);"

		# Gathering data for groups table...
		groupsData = []
		for i, g in enumerate(self.__groups.keys()):
			groupsData.append("INSERT INTO groups(groupName) ")
			groupsData[i] += "VALUES ('{}');".format(g)

		# Creating plants table...
		plants  = "CREATE TABLE plants ("
		plants += "id INTEGER PRIMARY KEY, "
		plants += "name TEXT NOT NULL, "
		plants += "species_id INTEGER REFERENCES species(id) NOT NULL, "
		plants += "lowertrig INTEGER NULL, "
		plants += "uppertrig INTEGER NULL, "
		plants += "datePlanted DATE NOT NULL, "
		plants += "dateRemoved DATE NULL, "
		plants += "groupID INTEGER REFERENCES groups(id) NOT NULL);"

		# Creating species table...
		species  = "CREATE TABLE species ("
		species += "id INTEGER PRIMARY KEY, "
		species += "name TEXT NOT NULL, "
		species += "info TEXT NOT NULL);"

		# Gathering data for plantTypes table...
		speciesData = []
		for s in self.__species:
			speciesData.append("INSERT INTO species(name) VALUES('{}');".format(s.title()))

		# Creating watering table...
		watering  = "CREATE TABLE watering ("
		watering += "id INTEGER PRIMARY KEY, "
		watering += "plantID INTEGER REFERENCES plants(id) NOT NULL ON CONFLICT IGNORE, "
		watering += "starttime DATETIME NOT NULL, "
		watering += "endtime DATETIME NOT NULL, "
		watering += "amount INTEGER NOT NULL);"

		# Creating defaultview view...
		defaultview  = "CREATE VIEW defaultview AS SELECT g.groupName, p.name AS plant, pt.species, p.datePlanted, p.lowertrig, p.uppertrig, "
		defaultview += "(SELECT CAST(TOTAL(w.amount) AS INTEGER) FROM watering AS w WHERE w.plantID = g.plantID) AS waterPlant, "
		defaultview += "(SELECT CAST(TOTAL(w.amount) AS INTEGER) FROM watering AS w WHERE w.plantID "
		defaultview += "IN (SELECT id FROM plants WHERE groupID = g.id)) AS waterContainer, "
		defaultview += "(SELECT s.sensorName FROM sensorSetup AS s WHERE g.id = s.groupID AND s.sensorType = 'mst') AS mstSensor, "
		defaultview += "(SELECT s.sensorName FROM sensorSetup AS s WHERE g.id = s.groupID AND s.sensorType = 'flow') AS flowSensor, "
		defaultview += "(SELECT s.sensorName FROM sensorSetup AS s WHERE g.id = s.groupID AND s.sensorType = 'temp') AS tempSensor "
		defaultview += "FROM groups AS g "
		defaultview += "LEFT JOIN plants AS p ON g.plantID = p.id "
		defaultview += "LEFT JOIN species AS sp ON p.plantType = sp.id "
		defaultview += "GROUP BY g.id;"

		# add sensorCheck view...
		sensorCheck  = "CREATE VIEW sensorCheck AS "
		sensorCheck += "SELECT s.sensorName, s.sensorType, g.groupName, s.resolution "
		sensorCheck += "FROM sensorSetup AS s LEFT JOIN groups AS g ON s.groupID = g.id; "


		self.__dbWrite(sensorData, groups, sensorSetup, groupsData, sensorSData,
							plants, species, speciesData, watering,
							defaultview, sensorCheck)

	def __setLocalsFromDB(self):
		# set planttypes from db.
		query = "SELECT name from species;"
		self.__species = list()
		for t in self.__dbRead(query):
			self.__species.append(t[0])

	def __validateDB(self):
		"""\t\tRun on boot. Check whether the data format in the DB is the same as
		the sensor setup of the main program.
		Set plantnames and triggers in gs.control.__groups{} at the end."""

		validated = False
		query = "SELECT * FROM sensorCheck ORDER BY sensorName ASC;"
		dbdata = self.__dbRead(query)
		if (dbdata == gs.control.getDBcheckData()):
			validated = True
		# TODO: include else clause
		if (validated):
			gs.control.setPlantsAndTriggersFromDB()
		else:
			logging.critical("Validation data from database and from hardware don't match! DB won't work until fixed.")
			raise DBValidationError

	def __dropTables(self):

		template1 = "SELECT * FROM sqlite_master WHERE type = '{}' AND name = '{}'"
		template2 = "DROP {} {};"
		tables = []
		conn = sql.connect(self.__fileName)
		curs = conn.cursor()
		for table in self.__tables:
			curs.execute(template1.format("table", table))
			if (curs.fetchone() is not None):
				tables.append(template2.format("TABLE", table))
		for view in self.__views:
			curs.execute(template1.format("view", view))
			if (curs.fetchone() is not None):
				tables.append(template2.format("VIEW", view))
		conn.close()

		self.__dbWrite(tables)
