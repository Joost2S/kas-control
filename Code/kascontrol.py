#!/usr/bin/python3
 
# Author: J. Saarloos
# v0.7.09	11-02-2018

import logging
import RPi.GPIO as GPIO
import threading
import time

import database
from globstuff import globstuff as gs
import globstuff
import hwcontrol
import network
import pushbutton
import webgraph

class Datalog(globstuff.protoThread):
	def run(self):
		logging.info("Starting thread{0}: {1}".format(self.threadID, self.name))
		try:
			gs.db.datalog()
		except database.dbVaildationError:
			pass
		except:
			logging.error("Error occured in datalog")
			self.run()
		finally:
			logging.info("Exiting thread{0}: {1}".format(self.threadID, self.name))
		
class Monitor(globstuff.protoThread):
	def run(self):
		logging.info("Starting thread{0}: {1}".format(self.threadID, self.name))
		gs.control.monitor()
		logging.info("Exiting thread{0}: {1}".format(self.threadID, self.name))
		
GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)
logging.basicConfig(level = logging.DEBUG,
						  format = "%(asctime)s - [%(levelname)s] - %(threadName)s - %(message)s",
						  datefmt = "%m-%d %H:%M:%S",
						  filename = gs.logfile)#,
						  #filemode = "w")
						  
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

	#	 Start recording the sensor data to the DB.
	datalog = Datalog(gs.getThreadNr(), "Datalog")
	datalog.start()
	gs.draadjes.append(datalog)

	#	Start monitoring the soil and other sensors.
	monitor = Monitor(gs.getThreadNr(), "Monitor")
	monitor.start()
	gs.draadjes.append(monitor)

	gs.server.serverLoop()
except network.shutdownError:
	logging.info("Shutdown by client.")
except KeyboardInterrupt:
	logging.debug("Shutdown by keyboard.")
finally:
	gs.shutdown()