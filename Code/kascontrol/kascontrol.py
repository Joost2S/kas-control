#!/usr/bin/python3

# Author: J. Saarloos
# v0.08.01	11-05-2019


import logging

from Code.kascontrol.core.database import Database
from Code.kascontrol.core.db.datalog import DatalogThread
from Code.kascontrol.core.hwcontrol import hwControl
from Code.kascontrol.core.powermanager import PowerManager
from Code.kascontrol.core.hwc.hwmonitor import Monitor
from Code.kascontrol.electronics.drivers import pushbutton
from Code.kascontrol.globstuff import globstuff as gs
from Code.kascontrol.core.network import Server
from Code.kascontrol.core.network import ShutdownError


def run():
	logging.basicConfig(level=logging.DEBUG,
							  format="%(asctime)s - [%(levelname)s] - %(threadName)s - %(message)s",
							  datefmt="%m-%d %H:%M:%S",
							  filename=gs.logfile)

	try:
		# Initiating major modules:
		PowerManager()
		hwControl()
		Database()
		Server()
		# TODO: move buttons to json and init in hwinit
		# Adding buttons:
		if (gs.hwOptions["buttons"]):
			pushbutton.stopButton(gs.button0pin)
			# pushbutton.lightToggle(gs.button1pin)

		# Start recording the sensor data to the DB.
		datalog = DatalogThread(gs.getThreadNr(), "Datalog")
		gs.draadjes.append(datalog)
		datalog.start()

		# Start monitoring the soil and other sensors.
		monitor = Monitor(gs.getThreadNr(), "Monitor")
		gs.draadjes.append(monitor)
		monitor.start()

		gs.server.serverLoop()
	except ShutdownError:
		logging.info("Shutdown by client.")
	except KeyboardInterrupt:
		logging.debug("Shutdown by keyboard.")
	finally:
		gs.shutdown()
