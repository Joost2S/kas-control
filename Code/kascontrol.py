#!/usr/bin/python3
 
# Author: J. Saarloos
# v0.6.1	16-08-2017

import logging
import RPi.GPIO as GPIO
import threading
import time

import globstuff
import autowater as aw
import network

gs = globstuff.globstuff

GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)
logging.basicConfig(level=logging.DEBUG, format="%(asctime)s - [%(levelname)s] - %(threadName)s - %(message)s", datefmt="%m-%d %H:%M:%S", filename = gs.logfile, filemode="w")

# Setting GPIO inputs:
GPIO.setup(gs.float_switch, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
GPIO.add_event_detect(gs.float_switch, GPIO.RISING, callback=(gs.fltdev.lwstart), bouncetime=1000)

# Setting GPIO outputs and ADC and valvw channels:
GPIO.setup(gs.sLEDpin, GPIO.OUT)
GPIO.output(gs.sLEDpin, GPIO.LOW)
for g in gs.ch_list:
	gs.getPinDev(g.valve).setPin(gs.getPinNr(g.valve), False)
	gs.getPinDev(g.ff1).setPin(gs.getPinNr(g.ff1), False)
	gs.getPinDev(g.ff2).setPin(gs.getPinNr(g.ff2), False)
	gs.adc.setChannel(g.name, g.devchan, gs.getPinNr(g.ff1), gs.getPinNr(g.ff2))
	gs.pump.setChannel(g.chan, g.valve)
for mcp in gs.mcplist:
	mcp.engage()

gs.adc.setChannel(gs.lightname, 7)

# Check water and sensor levels
if (gs.fltdev.getStatus()):
	gs.fltdev.lwstrt()
else:
	gs.pump.enable()
aw.check_connected()
	

class Datalog(globstuff.protoThread):
	def run(self):
		logging.info("Starting thread{0}: {1}".format(self.threadID, self.name))
		try:
			gs.db.datalog()
		except:
			logging.error("Error occured in datalog")
			self.run()
		logging.info("Exiting thread{0}: {1}".format(self.threadID, self.name))
		
class Monitor(globstuff.protoThread):
	def run(self):
		logging.info("Starting thread{0}: {1}".format(self.threadID, self.name))
		aw.monitor()
		logging.info("Exiting thread{0}: {1}".format(self.threadID, self.name))
		
#	 Start recording the sensor data to the DB.
datalog = Datalog(gs.getThreadNr(), "Datalog")
datalog.start()
gs.draadjes.append(datalog)

#	Start monitoring the soil and other sensors.
monitor = Monitor(gs.getThreadNr(), "Monitor")
monitor.start()
gs.draadjes.append(monitor)

try:
	netServer = network.Server()
	netServer.makeSocket()
	#	Indicate to user that the system is up and running.
	gs.sLED.blinkSlow(4)
	netServer.serverLoop()
except network.shutdownError:
	logging.info("Shutdown by client.")
except KeyboardInterrupt:
	logging.debug("Shutdown by keyboard.")
finally:
	gs.shutdown()