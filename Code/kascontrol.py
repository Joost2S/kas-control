#!/usr/bin/python3
 
# Author: J. Saarloos
# v0.7.12	03-03-2018

import logging
import RPi.GPIO as GPIO
import threading
import time

import database
from globstuff import globstuff as gs
import hwcontrol
import network
import pushbutton
import webgraph

GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)
logging.basicConfig(level = logging.DEBUG,
						  format = "%(asctime)s - [%(levelname)s] - %(threadName)s - %(message)s",
						  datefmt = "%m-%d %H:%M:%S",
						  filename = gs.logfile)
						  
try:
	# Initiating major modules:
	hwcontrol.hwControl()
	database.Database()
	webgraph.webgraph()
	network.Server()
	# Adding buttons:
	if (gs.hwOptions["buttons"]):
		pushbutton.stopButton(gs.button0pin)
		pushbutton.lightToggle(gs.LCD_L, gs.button1pin)
	
	# Getting the MCP23017 GPIO expanders ready for use:
	for mcp in gs.mcplist:
		mcp.engage()
		
	#	Start monitoring the soil and other sensors.
	powerManager = hwcontrol.PowerManager(gs.getThreadNr(), "PowerManager")
	gs.draadjes.append(powerManager)
	powerManager.start()

	#	 Start recording the sensor data to the DB.
	datalog = database.Datalog(gs.getThreadNr(), "Datalog")
	gs.draadjes.append(datalog)
	datalog.start()

	#	Start monitoring the soil and other sensors.
	monitor = hwcontrol.Monitor(gs.getThreadNr(), "Monitor")
	gs.draadjes.append(monitor)
	monitor.start()
	
	gs.server.serverLoop()
except network.shutdownError:
	logging.info("Shutdown by client.")
except KeyboardInterrupt:
	logging.debug("Shutdown by keyboard.")
finally:
	gs.shutdown()