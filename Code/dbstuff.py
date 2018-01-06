#!/usr/bin/python3
 
# Author: J. Saarloos
# v1.4	15-08-2017

"""
Database object which will make and maintain a database for storing various environmental sensor inputs.
Optionally another database will be made and maintained with min, avg and max values for each channel each day.
Fields must follow this example:
[(name, type),
(name, type)]
"""

import calendar
from datetime import datetime, timedelta
import logging
import os.path
import sqlite3 as sql
import threading
import time


class db(object):
	
	dbfolder = ""			# Location of DB files.
	dbLogFile = ""			# Name and path of the DB file.
	dbMmaFile = ""			# Name and path of the MMA DB file.
	fields = []				# Setup of the DB.
	dataCheck = False		# Set to enable checkValue() in case of poor perfoming hardware.
	mma = False				# Set to make a new DB to track min, max and avg of all channels in 'fields'.
	period = None			# Make a new DB every month ("M"), year ("Y") or never (None).
	interval = 0.0			# amount of minutes between each db entry.
	year = time.strftime("%Y")			# Current Year.
	month = time.strftime("%m")		# Current month.
	day = time.strftime("%d")			# Current day.
	adc = None				# reference to the ADC to be used.
	tdev = []				# Reference to the DS18B20 devices. Only devices with a name are allowed.
	tlock = None			# Threading lock to prevent multple threads from accessing the database at once.
	running = True
	pauze = False

	def __init__(self, fields, interval, dbfolder, adc, temps, mma = False, period = None):
		
		if (period == "Y" or period == "M"):
			self.period = period
		self.interval = interval * 60
		self.dbfolder = dbfolder
		self.adc = adc
		self.mma = mma
		self.tlock = threading.Lock()
		for i in fields:
			self.fields.append(i)
		for t in temps:
			if (t.name is not None):
				self.tdev.append(t)
		self.setFileNames()
		self.createdb()


	def setInterval(self, interval):
		self.interval = interval *60

	def setFileNames(self):
		if (self.period == None):
			self.dbLogFile = self.dbfolder + "datalog.db"
		elif (self.period == "Y"):
			self.dbLogFile = self.dbfolder + "datalog" + str(self.year) + ".db"
		else:
			self.dbLogFile = self.dbfolder + "datalog" + str(self.year) + "-" + str(self.month) + ".db"
		if (self.mma == True):
			if (self.period == None):
				self.dbMmaFile = self.dbfolder + "mmalog.db"
			elif (self.period == "Y"):
				self.dbMmaFile = self.dbfolder + "mmalog" + str(self.year) + ".db"
			elif (self.period == "M"):
				self.dbMmaFile = self.dbfolder + "mmalog" + str(self.year) + "-" + str(self.month) + ".db"

	def setDataCheck(self, check):
		"""To prevet outliers in the databse."""

		if (isinstance(check, bool)):
			self.dataCheck = check

	def createdb(self):
		"""Check if a correctly named DB exists, or otherwise create it."""

		if (not os.path.isfile(self.dbLogFile)):
			logging.debug("Creating new DB. " + str(self.dbLogFile))
			table = "CREATE TABLE data (timestamp DATETIME"
			for f in self.fields:
				table += ", " + f[0]
				if (f[1] == "mst" or f[1] == "temp" or f[1] == "light" or f[1] == "water"):
					table += " NUMERIC"
				else:
					table += " INTEGER"
			table += ");"
			print("Table:")
			print(table)
			with (self.tlock):
				conn = sql.connect(self.dbLogFile)
				curs = conn.cursor()
				curs.execute(table)
				conn.commit()
				conn.close()
		if (self.mma):
			if (not os.path.isfile(self.dbMmaFile)):
				channels = []
				i = 1
				for f in self.fields:
					channels.append((i, f[0]))
					i += 1
				types = (
					(1, "min"),
					(2, "avg"),
					(3, "max")
					)
				with (self.tlock):
					dayconn = sql.connect(self.dbMmaFile)
					dayc = dayconn.cursor()
					dayc.execute("CREATE TABLE channels (id INTEGER, channel TEXT)")
					dayc.execute("CREATE TABLE types (id INTEGER, type TEXT)")
					dayc.execute("CREATE TABLE date (id INTEGER, datestamp DATE)")
					dayc.execute("CREATE TABLE val (date_id INTEGER, channels_id INTEGER, types_id INTEGER, value NUMERIC)")
					print("channels:")
					print(channels)
					for row in channels:
						dayc.execute("INSERT INTO channels VALUES (?,?)", row)
					for row in types:
						dayc.execute("INSERT INTO types VALUES (?,?)", row)
					dayconn.commit()
					dayconn.close()

	def datalog(self):
		"""This is the main datalogging method. Every %interval minutes the data will be recorded into the database."""

		le = time.time() - self.get_last_data()
		logging.debug("Last entry: " + str(le) + " seconds ago.")
		if (le < self.interval):
			if ((self.interval - le) > 10):
				for i in range(int((self.interval - le) / 5) - 1):
					if (self.running):
						time.sleep(5)
			else:
				time.sleep(self.interval - le)
		while(self.running):
			if (not self.pauze):
				start = time.time()
				dbmsg = ("INSERT INTO data VALUES(strftime('%s')")
				for f in self.fields:
					dbmsg += ", " + self.getValue(f[1], f[0])
				dbmsg += (");")
				with (self.tlock):
					conn = sql.connect(self.dbLogFile)
					curs = conn.cursor()
					curs.execute(dbmsg)
					conn.commit()
					conn.close()
				print(dbmsg)
				if (self.mma):
					if (not self.day == time.strftime("%d")):
						self.day = time.strftime("%d")
						self.daylog()
				if (self.period is not None):
					if (not self.month == time.strftime("%m")):
						self.month = time.strftime("%m")
						if (not self.year == time.strftime("%Y")):
							self.year = time.strftime("%Y")
						self.setFileNames()
						self.createdb()
				for i in range(int((self.interval - (time.time() - start)) / 5) - 1):
					if (self.running):
						time.sleep(5)
				if (self.running):
					time.sleep(self.interval - (time.time() - start))
			else:
				while (self.running and self.pauze):
					time.sleep(1)

	def getValue(self, type, name):
		"""Takes a measurement of the value on the corresponding type and channel requested."""

		try:
			if (type == "mst"):
				if (self.dataCheck):
					return(str(self.checkValue(name)))
				else:
					return(str(self.adc.getMeasurement(name, 0)))
			if (type == "light"):
				return(str(self.adc.getMeasurement(name, 0)))
			if (type == "temp"):
				for t in self.tdev:
					if (t.name == name):
						# Up to 5 tries to make sure a temperature is retrieved.
						for i in range(5):
							temp = t.getTemp()
							if (temp is not None):
								return(str(temp))
						logging.warning("Failed to get a temperature for " + str(t.name))
						return("0")
			logging.warning("1Failed to get a measurement for " + str(type) + " at channel: " + str(name))
			return("0")
		except:
			logging.error("2Failed to get a measurement for " + str(type) + " at channel: " + str(name))
			return("0")

	def daylog(self, start = None, end = None):
		"""Sets min, max and avg values in the mmaDB for the previous day."""

		min = []
		avg = []
		max = []
		data = None
		date_id = self.get_last_day()
		for i in range(len(self.fields)):
			min.append(5000.0)
			avg.append(0.0)
			max.append(0.0)
		if (start == None):
			start = str(datetime.strftime(datetime.now()-timedelta(1),"%Y-%m-%d"))
		if (end == None):
			end = str(time.strftime("%Y-%m-%d"))
		st = calendar.timegm(time.strptime(start, "%Y-%m-%d"))
		en = calendar.timegm(time.strptime(end, "%Y-%m-%d"))
		j = 0.0
		with (self.tlock):
			dataconn = sql.connect(self.dbLogFile)
			datac = dataconn.cursor()
			for row in datac.execute("SELECT * FROM data WHERE timestamp>=" + str(st) + " AND timestamp<" + str(en)):
				i = 0
				j += 1
				for g in row[1:]:
					g = float(g)
					if (g < min[i]):
						min[i] = g
					if (g > max[i]):
						max[i] = g
					avg[i] += g
					i += 1
			dataconn.close()
		values = []
		date_info = (date_id[0], start)
		for k in range(len(avg)):
			if (not avg[k] == 0.0):
				avg[k] = round(avg[k] / j, 2)
			values.append((date_id[0], k + 1, 1, min[k]))
			values.append((date_id[0], k + 1, 2, avg[k]))
			values.append((date_id[0], k + 1, 3, max[k]))
		print("Values daylog:")
		for v in values:
			print(v)
		with (self.tlock):
			dayconn = sql.connect(self.dbMmaFile)
			dayc = dayconn.cursor()
			dayc.execute("INSERT INTO date values (?,?)", date_info)
			for row in values:
				dayc.execute("INSERT INTO val values (?,?,?,?)", row)
			dayconn.commit()
			dayconn.close()

	def get_last_day(self):
		"""Returns The datestamp of the latest entry in the mmaDB."""
	
		date_id = None
		with (self.tlock):
			dayconn = sql.connect(self.dbMmaFile)
			dayc = dayconn.cursor()
			max = (dayc.execute("SELECT max(id) FROM date"))
			date_id = max.fetchone()
			dayconn.close()
		if(date_id[0] == None):
			date_id = (1,)
		else:
			date_id = (date_id[0] + 1,)
		print(date_id)
		return(date_id)

	def display_data(self, start, end, raw = False):
		"""Returns all datalogDB entries betweeen START and END days ago"""

		st = float(time.time()) - float(start)*60*60*24
		en = float(time.time()) - float(end)*60*60*24

		dbdata = []
		with (self.tlock):
			conn = sql.connect(self.dbLogFile)
			curs = conn.cursor()
			for row in curs.execute("SELECT * FROM data WHERE timestamp>" + str(st) + " AND timestamp<" + str(en)):
				r = []
				for f in row:
					r.append(f)
				dbdata.append(r)
			conn.close()

		if (raw):
			return(dbdata)

		if (len(dbdata) == 0):
			return("No data.")

		dbtext = ""
		try:
			for row in dbdata:
				dbtext += "{0}: {1}\n".format(str(datetime.fromtimestamp(int(row[0])).strftime("%Y-%m-%d %H:%M:%S")), self.formatRow(row[1:]))
		except fieldException as txt:
			return(txt)
		return(dbtext)

	def formatRow(self, row):
		""""""

		if (len(row) == len(self.fields)):
			data = ""
			for i, r in enumerate(row):
				type = self.fields[i][1]
				if ((type == "light") or (type == "mst")):
					data += (self.perc(r) + ", ")
				else:
					data += (str(r) + ", ")
			return(data[:-2])
		else:
			raise fieldException("Incorrect amount of datafields.")

	def get_last_data(self):
		"""\t\tAmount of seconds ago the last entry in the DB was made.
		If no entry exists yet, an amount will be generated to enable the program to continue without delay."""

		with (self.tlock):
			conn = sql.connect(self.dbLogFile)
			curs = conn.cursor()
			last_time = curs.execute("SELECT max(timestamp) FROM data")
			max_id = last_time.fetchone()[0]
			conn.close()
		if (max_id == None):
			return(0)
		return(int(max_id))

	def get_first_data(self):
		"""Returns the epoch timestamp of the first record in the datalogDB"""

		with (self.tlock):
			conn = sql.connect(self.dbLogFile)
			curs = conn.cursor()
			first_time = curs.execute("SELECT min(timestamp) FROM data")
			min_id = first_time.fetchone()[0]
			conn.close()
		if (min_id == None):
			return(0)
		return(int(min_id))

	def perc(self, number):
		"""Retruns the value as a percentage."""

		return(str(round(float((number / self.adc.bits) * 100.0), 2)))

	def checkValue(self, channel):
		"""\t\tThe last 2 hours of DBdata will be averaged, then checked if a measurement does not deviate too much.
		This is to ensure cleaner data in the DB."""
		st = float(time.time()) - 7200.0		# 2 hours, 2*60*60
		en = float(time.time())
		level = 0.0
		i = 0
		with (self.tlock):
			conn = sql.connect(self.dbLogFile)
			curs = conn.cursor()
			for row in curs.execute("SELECT * FROM data WHERE timestamp>" + str(st) + " AND timestamp<" + str(en)):
				level += int(row[2])
				i += 1
			conn.close()
		if (i == 0):	# In case there are no measurements in the last 2 hours.
			return(self.adc.getMeasurement(channel, 0))
		avg = level / float(i)
		threshold = round(avg - (avg / 50.0), 1)
		i = 0
		dump = 0.0
		while(True):
			value = self.adc.getMeasurement(channel, 0)
			if (value >= threshold):
				return(value)
			else:
				i += 1
				dump += value
				logging.debug("Value outside of range (i: " + str(i) + "): " + str(value) + " < " + str(threshold))
			if (i > 10):
				return(round(dump / float(i), 1))

class fieldException(Exception):
	pass