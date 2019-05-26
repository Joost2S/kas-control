#!/usr/bin/python3

# Author: J. Saarloos
# v0.8.29	26-05-2019


import json
import logging
import os
import subprocess
import sys
import threading
import time

from pymitter import EventEmitter


class globstuff:

	hwOptions = None

	# Locations of files.
	dataloc = str(os.path.dirname(os.path.realpath(__file__))) + "/__datafiles/"
	setupFiles = {
		"sensor": dataloc + "sensorSetup.json",
		"hardware": dataloc + "hardwareSetup.json",
	}
	logfile = dataloc + "kascontrol.log"

	# Misc GPIO pin assignments:
	button0pin = "2B0"				# Input pin for button 0.
	button1pin = "2B1"				# Input pin for button 1.
	pumpPin = "1A0"					# Pin for the pump.
	sLEDpin = 23						# Status LED pin.
	float_switch = 22					# Float switch pin, goes high if there is too little water in the storage tank.

	powerLEDpins = ["43", "42", "41", "40"]

	fanPin = "44"

	# Networking vars:
	host = ""							# Hostname.
	port = 7500							# Default network port. If already used, can go up to port 7504

	# Misc vars
	ee = EventEmitter()           # PyMitter event manager.
	draadjes = []						# List with all the active threads.
	wtrThreads = []					# List with all watering threads.
	threadnr = 0						# Keep track of the thread number.
	spiLock = threading.Lock()    # Use when using an SPI device to ensure communication
	testmode = False					# Disables certain features for diagnositc purposes.
	time.sleep(0.5)					# Make sure some time has passed so the system clock is updated after boot.
	boottime = time.time()			# Record boot time to display system uptime.
	running = True						# Set to False to start shutdown
	shutdownOpt = None				# Set shutdown mode.

	# Major modules:
	control = None						# Reference to the hwcontrol instance.
	pwrmgr = None                 # Reference to the powerManager instance.
	db = None							# Reference to database instance.
	server = None						# Reference to the server object.

	@staticmethod
	def getSetupFile(file):
		try:
			with open(globstuff.setupFiles[file], "r") as f:
				data = json.load(f)
			return data
		except KeyError:
			return dict()

	@staticmethod
	def getThreadNr():
		"""Just counts the threads."""

		globstuff.threadnr +=1
		return(globstuff.threadnr)

	@staticmethod
	def convertToPrec(data, places):
		"""Returns the percentage value of the number."""

		m = ((data * 100) / float(globstuff.control.getADCres()))
		return(str(round(m, places)))

	@staticmethod
	def getTabs(txt, tabs = 2, tablength = 8):
		"""Returns a string of a fixed length for easier formatting of tables. Assuming your console has a tab length of 8 chars."""

		txt = str(txt)
		size = tabs * tablength
		if (len(txt) > size):
			return(txt[:size])
		elif (len(txt) == size):
			return(txt)
		elif (tablength == 8):
			t = int(size / len(txt))
			if (size % len(txt) != 0):
				t += 1
			return(txt + "\t" * t)
		else:
			return(txt + " " * (tabs * tablength - len(txt)))

	@staticmethod
	def timediff(diff, fractions=0):
		"""Converts seconds into dd, HH:MM:SS"""

		days = 0
		hours = 0
		minutes = 0
		if (diff >= 86400):
			days = int(diff / 86400)
			diff -= days * 86400
			if (days < 10):
				if (days == 0):
					days = "00"
				else:
					days = ("0" + str(days))
		if (diff >= 3600):
			hours = int(diff / 3600)
			diff -= hours * 3600
			if (hours < 10):
				if (hours == 0):
					hours = "00"
				else:
					hours = ("0" + str(hours))
		if (diff >= 60):
			minutes = int(diff / 60)
			diff -= minutes * 60
			if (minutes < 10):
				if (minutes == 0):
					minutes = "00"
				else:
					minutes = ("0" + str(minutes))
		if (fractions <= 0):
			seconds = int(diff)
		else:
			seconds = round(diff, fractions)
		if (seconds < 10):
			# if (seconds == 0):
			# 	seconds = "00"
			# else:
			seconds = ("0" + str(seconds))
		return((days, hours, minutes, seconds))

	@staticmethod
	def wait(interval):
		"""Waiting for next interval of timeRes to start next itertion of loop."""

		while (int(time.time()) % interval != interval - 1):
			time.sleep(1)
			if (not globstuff.running):
				return(True)
		while(not int(time.time()) % interval == 0):
			time.sleep(0.01)

	@staticmethod
	def shutdown():
		"""\t\tUse this method to either shutdown this software or,
		with '-x' or '-r' as argument, shutdown or reboot
		the Raspberry pi, respectively."""

		print("Shutting down system.")
		globstuff.running = False
		globstuff.control.disable()
		for t in globstuff.draadjes:
				t.join()
		print("Cleaning up and exiting Main Thread")
		globstuff.server.sslSock.close()
		globstuff.control.shutdown()
		print("Cleanup done.")
		logging.info("Program shutdown complete, without errors.")
		if (globstuff.shutdownOpt == "-r" or globstuff.shutdownOpt == "-x"):
			if (globstuff.shutdownOpt == "-x"):
				globstuff.shutdownOpt = "-h"
			command = "/usr/bin/sudo /sbin/shutdown {0} now".format(globstuff.shutdownOpt) # "/usr/bin/sudo /sbin/shutdown {0} now"
			process = subprocess.Popen(command.split(), stdout=subprocess.PIPE)
			output = process.communicate()[0]
			print(output)

		sys.exit()
