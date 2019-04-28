#!/usr/bin/python3

# Author: J. Saarloos
# v0.08.00	24-04-2019


import logging
import RPi.GPIO as GPIO

from .core import database
from.core import hwcontrol
from .core import powermanager
from .core.hwc.hwmonitor import Monitor
from .drivers import pushbutton
from .globstuff import globstuff as gs
from .network import network


def run():
	GPIO.setmode(GPIO.BCM)
	GPIO.setwarnings(False)
	logging.basicConfig(level = logging.DEBUG,
							  format = "%(asctime)s - [%(levelname)s] - %(threadName)s - %(message)s",
							  datefmt = "%m-%d %H:%M:%S",
							  filename = gs.logfile)

	try:
		# Initiating major modules:
		powermanager.PowerManager()
		hwcontrol.hwControl()
		database.Database()
		network.Server()
		# TODO: move buttons to json
		# Adding buttons:
		if (gs.hwOptions["buttons"]):
			pushbutton.stopButton(gs.button0pin)
			# pushbutton.lightToggle(gs.button1pin)

		# Getting the MCP23017 GPIO expanders ready for use:
		for mcp in gs.mcplist:
			mcp.engage()

		# Start recording the sensor data to the DB.
		datalog = database.Datalog(gs.getThreadNr(), "Datalog")
		gs.draadjes.append(datalog)
		datalog.start()

		# Start monitoring the soil and other sensors.
		monitor = Monitor(gs.getThreadNr(), "Monitor")
		gs.draadjes.append(monitor)
		monitor.start()

		gs.server.serverLoop()
	except network.ShutdownError:
		logging.info("Shutdown by client.")
	except KeyboardInterrupt:
		logging.debug("Shutdown by keyboard.")
	finally:
		gs.shutdown()
