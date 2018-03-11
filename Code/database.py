#!/usr/bin/python3
 
# Author: J. Saarloos
# v0.4.04	08-03-2018

from collections import OrderedDict
from datetime import datetime, timedelta
import logging
import os
import sqlite3 as sql
import sys
import threading
import time

import globstuff
from globstuff import globstuff as gs

	
class Database(object):
	
	__allowedTypes = ["mst", "light", "flow", "temp", "cputemp", "pwr"]
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
	__tables = ["sensorData","sensorSetup","groups","plants","plantTypes","watering"]
	__views = ["defaultview", "sensorCheck"]
	__tlock = threading.Lock()
	__resetting = False
	__interval = 300						# By default, record sensor data every 5 minutes.
	pause = False


	lastPlant = ""
	lastAction = ""
	lastResult = False

	def __init__(self, reset = False):

		self.__fileName = gs.dataloc + "datalog.db"
		if (reset):
			self.__dropTables()
			self.__resetting = True
		for s, t in gs.control.getSensors().items():
			self.__sensors[s.replace("-", "_")] = t
		self.__groups = gs.control.getDBgroups()
		self.__createdb()
		gs.db = self


	def __setFieldsFromDB(self):
		# set planttypes from db.
		query1 = "SELECT sensorName, sensorType FROM sensorSetup;"
		query2 = "SELECT species from plantTypes;"
		self.__plantTypes = []
		for t in self.__dbRead(query2):
			self.__species.append(t[0])
		self.__fields = self.__dbRead(query1)

	def __checkFields(self):
		"""\t\tRun on boot. Check wether the data format in the DB is the same as
		the sensor setup of the main program.
		Set plantnames and triggers in gs.control.__groups{} at the end."""

		validated = False
		query = "SELECT * FROM sensorCheck ORDER BY sensorName ASC;"
		dbdata = self.__dbRead(query)
		if (dbdata == gs.control.getDBcheckData()):
			validated = True
		if (validated):
			gs.control.setPlantsAndTriggers()
		else:
			logging.critical("Fields data from database and from sensors don't match! DB won't work until fixed.")
			raise dbVaildationError

	def __dropTables(self):
		
		template1 = "SELECT * FROM sqlite_master WHERE type = '{}' AND name = '{}'"
		template2 = "DROP {} {};"
		dbmsg1 = "DROP VIEW defaultview;"
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
		print(tables)

		self.__dbWrite(tables)

	def __createdb(self):
		"""Check if a correctly named DB exists, or otherwise create it."""

		# if file already exists, run integrity check unless resetting the DB
		if (os.path.isfile(self.__fileName) and not self.__resetting):
			self.__setFieldsFromDB()
			try:
				self.__checkFields()
			except dbVaildationError:
				raise dbVaildationError
			return

		logging.debug("Creating new DB. " + str(self.__fileName))
		self.__resetting = False
		self.__fields = gs.control.getDBfields()

		# Creating sensorData table...
		sensorData = "CREATE TABLE sensorData (timestamp DATETIME NOT NULL"
		for fn, ft in self.__sensors.items():
			sensorData += ", " + fn
			if (ft in self.__allowedTypes[:3]):
				sensorData += " REAL"
			else:
				sensorData += " INTEGER"
			sensorData += " NULL"
		sensorData += ");"

		# Creating sensorSetup table...
		sensorSetup  = "CREATE TABLE sensorSetup ("
		sensorSetup += "sensorID INTEGER PRIMARY KEY, "
		sensorSetup += "sensorName TEXT NOT NULL, "
		sensorSetup += "sensorType TEXT NOT NULL, "
		sensorSetup += "groupID INTEGER REFERENCES groups(groupID) NULL, "
		sensorSetup += "resolution INTEGER NULL);"
			
		# Gathering data for sensorSetup table...
		sensorSData = []
		for i, fn, ft in enumerate(self.__sensors.items()):
			subquery = "NULL"
			res = "NULL"
			if (ft == "mst" or ft == "light"):
				res = "4095"
			for n, g in self.__groups.items():
				if (fn in g):
					subquery = "(SELECT groupID FROM groups WHERE groupName = '{}')".format(n)
					break
			sensorSData.append("INSERT INTO sensorSetup(sensorName, sensorType, groupID, resolution)")
			sensorSData[i] += " VALUES ('{}', '{}', {}, {});".format(fn, ft, subquery, res)
		
		# Creating groups table...
		groups  = "CREATE TABLE groups ("
		groups += "groupID INTEGER PRIMARY KEY, "
		groups += "groupName TEXT NOT NULL, "
		groups += "plantID INTEGER REFERENCES plants(plantID) NULL);"
			
		# Gathering data for groups table...
		groupsData = []
		for i, g in enumerate(self.__groups):
			groupsData.append("INSERT INTO groups(groupName) ")
			groupsData[i] += "VALUES ('{}');".format(g[0])

		# Creating plants table...
		plants  = "CREATE TABLE plants ("
		plants += "plantID INTEGER PRIMARY KEY, "
		plants += "name TEXT NOT NULL, "
		plants += "plantType INTEGER REFERENCES plantTypes(typeID) NOT NULL, "
		plants += "lowertrig INTEGER NULL, "
		plants += "uppertrig INTEGER NULL, "
		plants += "datePlanted DATE NOT NULL, "
		plants += "dateRemoved DATE NULL, "
		plants += "groupID INTEGER REFERENCES groups(groupID) NOT NULL);"
		
		# Creating plantTypes table...
		plantTypes  = "CREATE TABLE plantTypes ("
		plantTypes += "typeID INTEGER PRIMARY KEY, "
		plantTypes += "species TEXT NOT NULL);"
		
		# Gathering data for plantTypes table...
		plantTData = []
		for type in self.__species:
			plantTData.append("INSERT INTO plantTypes(species) VALUES('{}');".format(type.title()))

		# Creating watering table...
		watering  = "CREATE TABLE watering ("
		watering += "plantID INTEGER REFERENCES plants(plantID) NOT NULL ON CONFLICT IGNORE, "
		watering += "starttime DATETIME NOT NULL, "
		watering += "endtime DATETIME NOT NULL, "
		watering += "amount INTEGER NOT NULL);"

		# Creating defaultview view...
		defaultview  = "CREATE VIEW defaultview AS SELECT g.groupName, p.name AS plant, pt.species, p.datePlanted, p.lowertrig, p.uppertrig, "
		defaultview += "(SELECT CAST(TOTAL(w.amount) AS INTEGER) FROM watering AS w WHERE w.plantID = g.plantID) AS waterPlant, "
		defaultview += "(SELECT CAST(TOTAL(w.amount) AS INTEGER) FROM watering AS w WHERE w.plantID "
		defaultview += "IN (SELECT plantID FROM plants WHERE groupID = g.groupID)) AS waterContainer, "
		defaultview += "(SELECT s.sensorName FROM sensorSetup AS s WHERE g.groupID = s.groupID AND s.sensorType = 'mst') AS mstSensor, "
		defaultview += "(SELECT s.sensorName FROM sensorSetup AS s WHERE g.groupID = s.groupID AND s.sensorType = 'flow') AS flowSensor, "
		defaultview += "(SELECT s.sensorName FROM sensorSetup AS s WHERE g.groupID = s.groupID AND s.sensorType = 'temp') AS tempSensor "
		defaultview += "FROM groups AS g "
		defaultview += "LEFT JOIN plants AS p ON g.plantID = p.plantID "
		defaultview += "LEFT JOIN plantTypes AS pt ON p.plantType = pt.typeID "
		defaultview += "GROUP BY g.groupID;"
		
		# add sensorCheck view...
		sensorCheck  = "CREATE VIEW sensorCheck AS "
		sensorCheck += "SELECT s.sensorName, s.sensorType, g.groupName, s.resolution "
		sensorCheck += "FROM sensorSetup AS s LEFT JOIN groups AS g ON s.groupID = g.groupID; "


		self.__dbWrite(sensorData, groups, sensorSetup, groupsData, sensorSData,
							plants, plantTypes, plantTData, watering,
							defaultview, sensorCheck)
		
	def addPlant(self, name, group, species = None):
		"""
		Use this method when adding a new plant to a container.
		If a plant is already assigned to the specified container,
		plant will not be added. Use removePlant() first.
		"""
		
		self.lastAction = "Add plant"
		self.__printutf("\t\tAdd Plant. " + str(name))
		if (species is None):
			species = "Generic"
		name = name.title()
		species = species.title()
		self.lastPlant = name
		try:
			group = int(group)
		except:
			group = int(group[-1])
		if (not (0 < group <= len(self.__groups))):
			self.lastResult = False
			logging.error("Unknown group. Please enter valid group number. 1 - {}".format(len(self.__groups)))
			return(False)
		# Get info on requested container.
		dbmsg1 = "SELECT p.name FROM plants AS p LEFT JOIN groups AS g ON p.plantID = g.plantID "
		dbmsg1 += "WHERE g.groupID = {};".format(group)
		curPlant = self.__dbRead(dbmsg1)
		self.__printutf("curPlant:" + str(curPlant))
		# Abort if there is already a plant in the requested container
		if (curPlant is not None):
			self.lastResult = False
			logging.error("Plant '{}' is already assigned to container {}.".format(curPlant[0], group))
			return(False)
		# If species isn't in the DB yet, add entry
		if (not species in self.__species):
			logging.info("New species. Adding {} to DB...".format(species))
			self.__addSpecies(species)
		dbmsg2 = "INSERT INTO plants(name, plantType, datePlanted, groupID) "
		dbmsg2 += "VALUES('{}', ({}), datetime(), {});".format(name, dbmsg1[:-1], group)
		dbmsg3 = "UPDATE groups SET plantID = (SELECT max(plantID) FROM plants) WHERE groupID = {};".format(group)
		self.__dbWrite(dbmsg2, dbmsg3)
		self.lastResult = True
		return(True)
		
	def __addSpecies(self, species):

		self.__species.append(species)
		dbmsg = "INSERT INTO plantTypes(species) VALUES('{}');".format(species.title())
		self.__dbWrite(dbmsg)

	def removePlant(self, plantName):
		"""
		User can remove a plant by name or container number.
		"""

		self.__printutf("\t\tRemove Plant." + str(plantName))

		self.lastAction = "Remove plant"
		dbmsg1 = "SELECT groups.groupID, plants.plantID, plants.name "
		dbmsg1 += "FROM groups "
		dbmsg1 += "INNER JOIN plants ON groups.plantID = plants.plantID "
		# Select by plant name or integer of container.
		if (isinstance(plantName, str)):
			plantName = plantName.title()
			self.lastPlant = plantName
			dbmsg1 += "WHERE plants.name = '{}';".format(plantName)
		else:
			if (not (0 < group <= len(self.__groups))):
				print("Unknown group. Please enter valid group number. 1 - {}".format(len(self.__groups)))
				return(False)
			self.lastPlant = "Unknown"
			dbmsg1 += "WHERE groups.groupID = {};".format(plantName)
		with (self.__tlock):
			conn = sql.connect(self.__fileName)
			with conn:
				curs = conn.cursor()
				curs.execute(dbmsg1)
				plant = curs.fetchone()

		# Abort if no match found
		if (plant is None):
			self.lastResult = False
			if (isinstance(plantName, str)):
				print("Plant '{}' not found as currently assigned plant.".format(plantName))
			else:
				print("Container {} currently has no plant assigned.".format(plantName))
			return(False)
		self.lastPlant = plant[2]
		self.lastResult = True
		self.__printutf("Removed plant '{}' from container {}.".format(plant[2], plant[0]))#logging.info
		pID = plant[1]
		# Change plant assignment in table groups to NULL
		dbmsg2 = "UPDATE groups SET plantID = NULL WHERE plantID = {};".format(pID)
		# Change dateRemoved in table plants
		dbmsg3 = "UPDATE plants SET dateRemoved = date() WHERE plantID = {};".format(pID)
		self.__dbWrite(dbmsg2, dbmsg3)
		return(True)

	def wateringEvent(self, group, start, end, amount):
		"""
		Use this method to add a watering event to the DB.
		"""

		if (not (0 < group <= len(self.__groups))):
			logging.info("Unknown group. Please enter valid group number. 1 - {}".format(len(self.__groups)))
			return(False)
		subquery = "SELECT plantID FROM groups WHERE groupID = {}".format(group)
		query = "INSERT INTO watering (plantID, starttime, endtime, amount) "
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
		subquery = "(SELECT plantID FROM groups WHERE groupID = {})".format(group)
		query = "SELECT lowertrig, uppertrig FROM plants WHERE plantID = {};".format(subquery)
		triggers = self.__dbRead(query)

	def setTriggers(self, group, lower = None, upper = None):
		"""Set one or both triggers of a container."""
		
		if (not (0 < group <= len(self.__groups))):
			self.lastResult = False
			print("Unknown group. Please enter valid group number. 1 - {}".format(len(self.__groups)))
			return
		subquery = "(SELECT plantID FROM groups WHERE groupID = {})".format(group)
		query = "UPDATE plants SET lowertrig = {}, uppertrig = {} WHERE plantID = {};".format(int(lower), int(upper), subquery)
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
		data = self.__dbWrite(query)

	def getSensorData(self, start, end = 0.0, names = None, types = None, group = None):
		"""Returns a 2D array with the sensor data. First row contains the sensor names."""
		"""
		SELECT datetime(timestamp, 'unixepoch', 'localtime') as t,
		sensor1, sensor2, sensor3
		FROM sensorData WHERE
		t > '2018-03-05';
		"""
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

	def __dbRead(self, dbmsg):
		"""
		Use this method to send queries to the DB.
		Returns a 2d array with results.
		"""

		dat = []
		with (self.__tlock):
#			try:
			with sql.connect(self.__fileName) as conn:
				curs = conn.cursor()
				data = curs.execute(dbmsg)
				if (data is None):
					return(None)
				else:
					for row in data:
						a = []
						for t in row:
							a.append(t)
						dat.append(a)
#			except:
#				print("crap")
#			finally:
#				conn.close()
		return(dat)
		for line in dat:
			self.__printutf(line)
			
	def __dbWrite(self, *dbmsgs):
		"""Use this method to write data to the DB."""

		sortedmsgs = self.__sortmsgs(*dbmsgs)

		try:
			updRows = 0
			with (self.__tlock):
				conn = sql.connect(self.__fileName)
				with conn:
					curs = conn.cursor()
					for dbmsg in sortedmsgs:
						curs.execute(dbmsg)
					conn.commit()
					updRows = curs.rowcount
			if (updRows > 1):
				print("updRows:", updRows)
		except sql.Error as er:
			 logging.debug("er:", er.message)
			 return(0)
		return(updRows)
		
	def __sortmsgs(self, *dbmsgs):
		"""Recursive methed to extract all strings from arbitrarily nested arrays."""

		msgs = []
		if (not isinstance(dbmsgs, str)):
			for msg in dbmsgs:
				if (not isinstance(msg, str)):
					for m in self.__sortmsgs(*msg):
						msgs.append(m)
					pass
				else:
					msgs.append(msg)
		else:
			msgs.append(dbmsgs)
		return(msgs)

	def __printutf(self, text):

		t = text.encode("utf-8")
		sys.stdout.buffer.write(t)
		print()

	def setInterval(self, interval):
		"""Set a new interval in minutes. Will be rounded down to whole seconds."""

		if (interval >= 1.0):
			self.__interval = int(interval * 60)
	
	def getContainerNameTriggers(self, container):
		"""Returns [plantname, lowtrig, hightrig]"""

		query = "SELECT p.name, p.lowertrig, p.uppertrig "
		query += "FROM groups as g "
		query += "INNER JOIN plants as p ON g.plantID = p.plantID "
		query += "WHERE g.groupName = '{}';".format(container)
		data = self.__dbRead(query)
		if (data is None):
			return(data)
		return(data[0])

	def startDatalog(self):
		"""Use this function to start datalog to prevent more than 1 instance running at a time."""
		
		running = False
		for t in gs.draadjes:
			if (t.name == "Datalog" and t.is_alive()):
				if (running):
					return
				running = True
		self.__datalog()

	def __datalog(self):
		"""This is the main datalogging method. Every %interval minutes the data will be recorded into the database."""

		# Waiting to ensure recordings are synced to __interval
		if (self.__wait()):
			return

		# Datalogging loop.
		while (gs.running):
			if (not self.pause):
				start = time.time()
				txt1 = "INSERT INTO sensorData(timestamp"
				txt2 = ")VALUES({}".format(int(time.time()))
				for n in self.__sensors.keys():
					txt1 += ", " + str(n)
					txt2 += ", " + str(self.__getValue(n))
				dbmsg = (txt1 + txt2 + ");")
				self.__dbWrite(dbmsg)
			if ((not gs.running) or self.__wait()):
				return

	def __wait(self):
		"""Waiting for next interval of timeRes to start next itertion of loop."""

		while (int(time.time()) % self.__interval != self.__interval - 1):
			time.sleep(1)
			if (not gs.running):
				return(True)
		while(not int(time.time()) % self.__interval == 0):
			time.sleep(0.01)

	def __getValue(self, name):
		"""Takes a measurement of the value on the corresponding type and channel requested."""

		for i in range(5):
			data = gs.control.requestData(name = name.replace("_", "-"), caller = "db")
			if (data is not False):
				if (data is None):
					return("null")
				return(data)
		logging.warning("Failed to get a measurement for sensor {}.".format(name))
		return("NULL")
		
	
class Datalog(globstuff.protoThread):
	def run(self):
		logging.info("Starting thread{0}: {1}".format(self.threadID, self.name))
		try:
			gs.db.startDatalog()
		except dbVaildationError:
			pass
		except:
			logging.error("Error occured in datalog")
			self.run()
		finally:
			logging.info("Exiting thread{0}: {1}".format(self.threadID, self.name))
	

class dbVaildationError(Exception):
	pass