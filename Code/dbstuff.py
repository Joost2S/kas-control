#! /usr/bin/python

import datetime
import logging
import os.path
import sqlite3 as sql
import threading
import time


import globstuff
import sensor
import autowater as aw

gs = globstuff.globstuff


datalogfile = str("/home/j2s/greenhousefiles/dbfiles/datalog" + str(time.strftime("%Y")) + ".db")
daylogfile = str("/home/j2s/greenhousefiles/dbfiles/daylog" + str(time.strftime("%Y")) + ".db")

# creates and sets up 2 new databases if they don't exist yet.
# DB datalog<year>.db is for saving data at the time_res interval.
# DB daylog<year>.db if for saving MIN, AVG and MAX values for each day.
def yearStart():
	# Check and if needed, create the datalog<year> database.
	if (not os.path.isfile(datalogfile)):
		gs.dbchecked = True
		table = "CREATE TABLE data (timestamp DATETIME, temp NUMERIC, bright NUMERIC"
		for g in	gs.ch_list:
			table += (", mst" + str(g.chan) + " NUMERIC")
		table += ");"
		with (threading.Lock()):
			dataconn = sql.connect(datalogfile)
			datac = dataconn.cursor()
			datac.execute(table)
			dataconn.commit()
			dataconn.close()
	# Check and if needed, create the daylog<year> database.
	if (not os.path.isfile(daylogfile)):
		channels = (
			(1, "temperatuur"),
			(2, "licht"),
			(3, "vocht1"),
			(4, "vocht2"),
			(5, "vocht3"),
			(6, "vocht4"),
			(7, "vocht5"),
			)
		types = (
			(1, "min"),
			(2, "avg"),
			(3, "max"),
			)
		with (threading.Lock()):
			dayconn = sql.connect(daylogfile)
			dayc = dayconn.cursor()
			dayc.execute("""CREATE TABLE channels (id integer,channel text)""")
			dayc.execute("""CREATE TABLE types (id integer,type text)""")
			dayc.execute("""CREATE TABLE date (id integer,datestamp DATE)""")
			dayc.execute("""CREATE TABLE val (channels_id integer,types_id integer,date_id integer,value NUMERIC)""")
		
			for row in channels:
				dayc.execute("insert into channels values (?,?)", row)
			for row in types:
				dayc.execute("insert into types values (?,?)", row)
			dayconn.commit()
			dayconn.close()
		daylog()

# Saves the DATE, MIN, AVG and MAX values of the last day in the daylog<year>.db.
def daylog():
	min = []
	avg = []
	max = []
	date_id = get_last_day()
	for i in range(0, (2 + len(gs.ch_list))):
		min.append(5000)
		avg.append(0)
		max.append(0)
	yesterday = str(datetime.datetime.strftime(datetime.datetime.now()-datetime.timedelta(1),'%Y-%m-%d'))
	print("yesterday = " + yesterday)
	j = 0
	with (threading.Lock()):
		dataconn = sql.connect(datalogfile)
		datac = dataconn.cursor()
		for row in datac.execute("SELECT * FROM data WHERE timestamp=" + yesterday):# + "*"):
			i = 0
			j += 1
			for g in row:
				g = int(g)
				if (row[0] == g):
					continue
				if (g < min[i]):
					min[i] = g
				if (g > max[i]):
					row[i] = g
				avg[i] += g
				i += 1
		dataconn.close()
	values = []
	date = time.strftime("%Y-%m-%d")
	date_info = (date_id,date)
	for k in range(0, len(avg)):
		if (avg[k] != 0):
			avg[k] /= j
		values.append((date_id, k + 1, 1, min[k]))
		values.append((date_id, k + 1, 2, avg[k]))
		values.append((date_id, k + 1, 3, max[k]))
	with (threading.Lock()):
		dayconn = sql.connect(daylogfile)
		dayc = dayconn.cursor()
		dayc.execute("INSERT INTO date values (?,?)", date_info)
		for row in values:
			dayc.execute("INSERT INTO val values (?,?,?,?)", row)
		dayconn.commit()
		dayconn.close()

# Saves the values from the sensors in the datalog<year>.db at the time_res interval.
def datalog():
	while(True):
		start = time.time()
		if (not gs.dbchecked):
			logging.debug("Cheking last DB entry...")
			le = get_last_data(int(start))
			logging.debug("Last entry: " + str(le) + " seconds ago.")
			if (le < gs.time_res * 60):
				time.sleep((gs.time_res * 60) - le)
			gs.dbchecked = True
		else:
			t = sensor.temp.get_temp()
			if (t == None):
				t = 0
			l = sensor.light.get_light()
			msg = (str(t) + "," + str(l))
			aw.check_connected()
			for g in gs.ch_list:
				if (not g.connected):
					msg += (",0")
				else:
					msg += ("," + str(sensor.moisture.get_moisture(g, 0)))
			msg = ("INSERT INTO data values(strftime('%s')," + msg + (")"))
			with (threading.Lock()):
				conn = sql.connect(datalogfile)
				curs = conn.cursor()
				curs.execute(msg)
				conn.commit()
				conn.close()
			if (time.strftime("%H") == 0 and time.strftime("%M") <= gs.time_res):
				logging.debug("Daylog entry.")
				daylog()
			logging.debug(time.strftime("%H:%M:%S") + ", put new values in DB: " + msg)
			time.sleep(float(gs.time_res*60.0)-(time.time()-start))

# Returns all DB entries betweeen START and END days ago
def display_data(start, end):
	st = float(time.time()) - float(start)*60*60*24
	en = float(time.time()) - float(end)*60*60*24

	dbdata = ""
	with (threading.Lock()):
		conn = sql.connect(datalogfile)
		curs = conn.cursor()
		for row in curs.execute("SELECT * FROM data WHERE timestamp>" + str(st) + " AND timestamp<" + str(en)):
			dbdata += (str(datetime.datetime.fromtimestamp(int(row[0])).strftime("%Y-%m-%d %H:%M:%S")) + "\t" + str(row[1]) + "C\t" + str(row[2]) + "lm")
			for g in gs.ch_list:
				dbdata +=("\t" + str(row[g.chan+2]) + "%")
			dbdata += "\n"
		conn.close()
	if (dbdata == ""):
		return("No data.")
	return(dbdata)

#	Amount of seconds ago the last entry in the DB was made.
def get_last_data(start):
	with (threading.Lock()):
		conn = sql.connect(datalogfile)
		curs = conn.cursor()
		last_time = curs.execute("SELECT max(timestamp) FROM data")
		max_id = last_time.fetchone()[0]
		conn.close()
	return(int(start - max_id))

#	Returns the highest id from the date table in the daylog
def get_last_day():
	date_id = 1
	with (threading.Lock()):
		dayconn = sql.connect(daylogfile)
		dayc = dayconn.cursor()
		try:
			max = (int(dayc.execute("SELECT max(id) FROM date")) + 1)
			date_id = max.fetchone()[0]
		except:
			date_id = 1
		dayconn.close()
	return(date_id)