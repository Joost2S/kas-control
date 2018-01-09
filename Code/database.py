#!/usr/bin/python3
 
# Author: J. Saarloos
# v0.2.3	06-01-2018

import calendar
from datetime import datetime, timedelta
import logging
import os.path
import random
import re
import sqlite3 as sql
import sys
import threading
import time

import globstuff
gs = globstuff.globstuff


class Reprinter:
	"""\t\tClass copied/pasted from:
		https://stackoverflow.com/a/15586020"""

	def __init__(self):
		self.text = ''

	def moveup(self, lines):
		for _ in range(lines):
			sys.stdout.write("\x1b[A")

	def reprint(self, text):
		# Clear previous text by overwritig non-spaces with spaces
		self.moveup(self.text.count("\n"))
		sys.stdout.write(re.sub(r"[^\s]", " ", self.text))

		# Print new text
		lines = min(self.text.count("\n"), text.count("\n"))
		self.moveup(lines)
		sys.stdout.buffer.write(text.encode("utf-8"))
		self.text = text
	
class Database(object):
	
	__allowedTypes = ["mst", "temp", "cputemp", "light", "flow", "pwr"]
	__fields = [["light", "light"],
				 ["inside", "temp"],
				 ["outside", "temp"],
				 ["PSU", "temp"],
				 ["CPU", "cputemp"],
				 ["total", "flow"],
				 ["soil_g1", "mst"],
				 ["soil_g2", "mst"],
				 ["soil_g3", "mst"],
				 ["soil_g4", "mst"],
				 ["temp_g1", "temp"],
				 ["temp_g2", "temp"],
				 ["temp_g3", "temp"],
				 ["temp_g4", "temp"],
				 ["flow_g1", "flow"],
				 ["flow_g2", "flow"],
				 ["flow_g3", "flow"],
				 ["flow_g4", "flow"]]
	__groups = [["group1", ["soil_g1", "temp_g1", "flow_g1"]],
				 ["group2", ["soil_g2", "temp_g2", "flow_g2"]],
				 ["group3", ["soil_g3", "temp_g3", "flow_g3"]],
				 ["group4", ["soil_g4", "temp_g4", "flow_g4"]]]
	__fileName = os.path.dirname(os.path.realpath(__file__)) + "/datalog.db"
	__plantTypes = ["Generic", "Weed", "Cannabis", "Marijuana", "Hemp", "Tomato", "Chili pepper"]
	__tables = ["sensorData","sensorSetup","groups","plants","plantTypes","watering"]
	__views = ["defaultview", "sensorCheck"]
	__tlock = threading.Lock()
	__resetting = False
	__interval = 5.0						# Record sensor data every x min
	pause = False

	count = 0
	a = 0
	b = 0.88

	lastPlant = ""
	lastAction = ""
	lastResult = False
	repr = Reprinter()

	def __init__(self, reset = False):

		if (reset):
			self.__dropTables()
			self.__resetting = True
		self.__groups = gs.control.getDBgroups()
		self.__createdb()
		gs.db = self


	def getCount(self):
		self.count += 1
		return(str(self.count))

	def getA(self):

		 return(7 + int(random.random() * 5))

	def recTest(self):
		
		blah = []
		for i in range(0, self.getA()):
			if (random.random() < self.b):
				blah.append(self.getCount())
			else:
				blah.append([])
				for j in range(0, self.getA()):
					if (random.random() < self.b):
						blah[i].append(self.getCount())
					else:
						blah[i].append([])
						for k in range(0, self.getA()):
							if (random.random() < self.b):
								blah[i][j].append(self.getCount())
							else:
								blah[i][j].append([])
								for l in range(0, self.getA()):
									if (random.random() < self.b):
										blah[i][j][k].append(self.getCount())
									else:
										blah[i][j][k].append([])
										for m in range(0, self.getA()):
											if (random.random() < self.b):
												blah[i][j][k][l].append(self.getCount())
											else:
												blah[i][j][k][l].append([])
												for n in range(0, self.getA()):
													if (random.random() < self.b):
														blah[i][j][k][l][m].append(self.getCount())
													else:
														blah[i][j][k][l][m].append([])
														for o in range(0, self.getA()):
															blah[i][j][k][l][m][n].append(self.getCount())
		print(blah)
		print(self.__sortmsgs(0, blah))
		print(self.a)

	def __setFieldsFromDB(self):
		
		query = "SELECT sensorName, sensorType FROM sensorSetup;"
		self.__fields = self.__dbRead(query)

	def __checkFields(self):
		"""\t\tRun on boot. Check wether the data format in the DB is the same as
		the sensor setup of the main program.
		Set plantnames and triggers in gs.control.__groups[] at the end."""

		validated = False
		fields = gs.control.getDBfields()

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
			except:
				raise dbVaildationError
			return

		logging.debug("Creating new DB. " + str(self.__fileName))
		self.__resetting = False
		self.__fields = gs.control.getDBfields()

		# Creating sensorData table...
		sensorData = "CREATE TABLE sensorData (timestamp DATETIME NOT NULL"
		for f in self.__fields:
			sensorData += ", " + f[0]
			if (f[1] in self.__allowedTypes[1:2]):
				sensorData += " REAL"
			else:
				sensorData += " INTEGER"
			sensorData += " NOT NULL"
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
		subquery = "NULL"
		for i, f in enumerate(self.__fields):
			res = "NULL"
			if (f[1] == "mst" or f[1] == "light"):
				res = "4095"
			for g in self.__groups:
				if (f[0] in g[1]):
					subquery = "(SELECT groupID FROM groups WHERE groupName = '{}')".format(g[0])
					break
			sensorSData.append("INSERT INTO sensorSetup(sensorName, sensorType, groupID, resolution)")
			sensorSData[i] += " VALUES ('{}', '{}', {}, {});".format(f[0], f[1], subquery, res)
		
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
		for type in self.__plantTypes:
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
		
	def addplant(self, name, group, species = None):
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
			group = group[-1]
		if (not (0 < group <= len(self.__groups))):
			self.lastResult = False
			print("Unknown group. Please enter valid group number. 1 - {}".format(len(self.__groups)))
			return
		# Get species ID for given species.
		dbmsg1 = "SELECT typeID FROM plantTypes WHERE species = '{}';".format(species)
		# Get info on requested container.
		dbmsg2 = "SELECT p.name FROM plants AS p LEFT JOIN groups AS g ON p.plantID = g.plantID "
		dbmsg2 += "WHERE g.groupID = {};".format(group)
		with (self.__tlock):
			conn = sql.connect(self.__fileName)
			with conn:
				curs = conn.cursor()
				curs.execute(dbmsg1)
				sID = curs.fetchone()
				curs.execute(dbmsg2)
				curPlant = curs.fetchone()
				self.__printutf("curPlant:" + str(curPlant))
		# Abort if there is already a plant in the requested container
		if (curPlant is not None):
			self.lastResult = False
			self.__printutf("Plant '{}' is already assigned to container {}.".format(curPlant[0], group)) # logging.debug
			return
		# If species isn't in the DB yet, add entry
		if (sID is None):
			self.__printutf("New species. Adding {} to DB...".format(species))	# logging.info
			self.__addSpecies(species)
		dbmsg3 = "INSERT INTO plants(name, plantType, datePlanted, groupID) "
		dbmsg3 += "VALUES('{}', ({}), datetime(), {});".format(name, dbmsg1[:-1], group)
		dbmsg4 = "UPDATE groups SET plantID = (SELECT max(plantID) FROM plants) WHERE groupID = {};".format(group)
		self.__dbWrite(dbmsg3, dbmsg4)
		self.lastResult = True

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

	def wateringEvent(self, group, start, end, amount):

		if (not (0 < group <= len(self.__groups))):
			print("Unknown group. Please enter valid group number. 1 - {}".format(len(self.__groups)))
			return
		subquery = "SELECT plantID FROM groups WHERE groupID = {}".format(group)
		query = "INSERT INTO watering (plantID, starttime, endtime, amount) "
		query += "VALUES (({}), {}, {}, {});".format(subquery, start, end, amount)
		rows = self.__dbWrite(query)
		if (rows == 0):
			print("Failed to add Watering event.")

	def __addSpecies(self, species):

		dbmsg = "INSERT INTO plantTypes(species) VALUES('{}');".format(species.title())
		self.__dbWrite(dbmsg)

	def getTriggers(self, group):
		
		if (not (0 < group <= len(self.__groups))):
			self.lastResult = False
			print("Unknown group. Please enter valid group number. 1 - {}".format(len(self.__groups)))
			return
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
		
		if (not (0 < group <= len(self.__groups))):
			self.lastResult = False
			print("Unknown group. Please enter valid group number. 1 - {}".format(len(self.__groups)))
			return
		query   = "select p.name, s.species, total(w.amount)/1000 as total, p.dateRemoved == 0 as moi"
		query  += "from plants as p"
		query  += "left join plantTypes as s on s.typeID = p.plantType"
		query  += "left outer join watering as w on w.plantID = p.plantID"
		query  += "where p.groupID = {} group by p.plantID".format(group)
		data = self.__dbWrite(query)

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
				for row in curs.execute(dbmsg):
					a = []
					for t in row:
						a.append(t)
					dat.append(a)
#			except:
#				print("crap")
#			finally:
#				conn.close()
		return(dat)
		text = ""
		for line in dat:
			self.__printutf(line)
			
	def __dbWrite(self, *dbmsgs):
		"""Use this method to write data to the DB."""

		sortedmsgs = self.__sortmsgs(*dbmsgs)

#		try:
		updRows = 0
		with (self.__tlock):
			conn = sql.connect(self.__fileName)
			with conn:
				curs = conn.cursor()
				for dbmsg in sortedmsgs:
#					self.printutf(dbmsg)
					curs.execute(dbmsg)
				conn.commit()
				updRows = curs.rowcount
		if (updRows > 1):
			print("updRows:", updRows)
#		except sql.Error as er:
#			 print ("er:", er.message)
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
		"""Set a new interval in minutes."""

		self.__interval = float(interval)
	
	def getContainerNameTriggers(self, container):
		"""Returns [plantname, lowtrig, hightrig]"""

		query = "SELECT p.name, p.lowertrig, p.uppertrig "
		query += "FROM groups as g "
		query += "INNER JOIN plants as p ON g.plantID = p.plantID "
		query += "WHERE g.groupName = '{}';".format(container)
		data = self.__dbRead(query)
		return(data)# return(data[0])?

	def datalog(self):
		"""This is the main datalogging method. Every %interval minutes the data will be recorded into the database."""

		# Checking the last entry in the db to ensure recordings are synced to __interval
		le = time.time() - self.get_last_data()
		logging.debug("Last entry: " + str(le) + " seconds ago.")
		timeRes = self.__interval * 60.0
		if (le < timeRes):
			while (int(time.time()) % timeRes != timeRes - 1):
				time.sleep(1)
				if (not gs.running):
					return
			while(1):
				if (int(time.time()) % timeRes == 0):
					break
				else:
					time.sleep(0.01)

		# Datalogging loop.
		while (gs.running):
			if (not self.pause):
				start = time.time()
				dbmsg = ("INSERT INTO sensorData VALUES({}".format(int(time.time())))
				for f in self.__fields:
					dbmsg += ", " + str(self.__getValue(f[0]))
				dbmsg += (");")
				self.__dbWrite(dbmsg)

			# Waiting for next interval of timeRes to start next itertion of loop.
			timeRes = self.__interval * 60.0
			while (int(time.time()) % timeRes != timeRes - 1):
				time.sleep(1)
				if (not gs.running):
					return
			while(1):
				if (int(time.time()) % timeRes == 0):
					break
				else:
					time.sleep(0.01)

	def __getValue(self, name):
		"""Takes a measurement of the value on the corresponding type and channel requested."""

		for i in range(5):
			data = gs.control.requestData(name = name, caller = "db")
			if (data is not False):
				return(data)
		logging.warning("Failed to get a measurement for sensor {}.".format(name))
		return(0)
		
	
class dbVaildationError(Exception):
	pass

if __name__ == "__main__":
	import random

	def wtrEvent(group):
		global db
		start = time.time() - ((12 + random.random() * 12) * 3600)
		end = start + (5 + random.random() * 5)
		amount = 3000 + int(random.random() * 3000)
		db.wateringEvent(group, start, end, amount)


	print()
	db = Database(reset = True)
	
	db.addplant("plaNT", 1)
	for i in range(25):
		wtrEvent(1)
	db.addplant("haze", 2, "Weed")
	
	for i in range(25):
		wtrEvent(2)
	db.addplant("chili", 1, "Chili pepper")
	db.addplant("White Widow", 4, "Weed")
	for i in range(25):
		wtrEvent(4)
	db.addplant("Pumpkin", 3, "PumPKin")
	db.addplant("Tomato", 2, "Tomato")
	db.removePlant("moi")
	db.removePlant("plant")
	db.removePlant("plant")
	db.addplant("NoRthern LIghts", 1, "WeED")
	db.removePlant("TomatO")
	db.addplant("chili", 2, "Chili pepper")
	db.removePlant("haze")
	db.addplant("Tomato", 2, "Tomato")
	db.removePlant(4)
	db.removePlant("WhitE wIDow")
	a = "JalapeÑo"
	db.addplant(a, 4, "Chili pepper")
	db.removePlant(2)
	db.addplant("drakenboompje", 2, "TREE")
	for i in range(-4, 6):
		db.addplant("tomATO", i, "TOMato")
	db.removePlant(1)
	db.addplant("I am with stupid -->", 1, "I AM LEGEND!!!!111!!11oneoneone!1one11one")
	for i in range(25):
		wtrEvent(1)
		wtrEvent(3)
	db.removePlant(1)
	db.addplant("Kush", 1, "WeeD")
	for i in range(25):
		wtrEvent(1)
	db.removePlant("drakenboompjE")
	db.removePlant(2)
	db.removePlant("drakenboompjE")
	for i in range(4):
		db.setTriggers(i + 1, 3000 + random.random() * 100, 3500 + random.random() * 100)
	for i in range(4):
		db.getTriggers(i + 1)
	for i in range(25):
		wtrEvent(2)
	db.addplant("NuMex Twilight", 2, "Chili pepper")
	for i in range(25):
		wtrEvent(2)
	db.removePlant("pumpkin")
	db.addplant("frisian dew", 3, "WEED")
	db.setTriggers(3, 3000 + random.random() * 100, 3500 + random.random() * 100)
	
	db.getData()
#	db.getData(True)