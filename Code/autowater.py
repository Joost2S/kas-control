#!/usr/bin/python3
 
# Author: J. Saarloos
# v0.9.1	16-08-2017

import csv
from datetime import datetime, timedelta
import logging
import RPi.GPIO as GPIO
import threading
import time

import globstuff

gs = globstuff.globstuff


class wateringthread(globstuff.protoThread):
	def run(self):
		logging.debug("Starting thread{0}: {1}".format(self.threadID, self.name))
		watering(self.args)
		logging.debug("Exiting thread{0}: {1}".format(self.threadID, self.name))


def monitor():
	"""\tMain monitoring method. Will check on the status of all sensors every 15 seconds.
	Will also start methods/actions based on the sensor input."""

	try:
		while (gs.running):
			start = time.time()

			# Start making output string.
			output = (time.strftime("%H:%M:%S") + ":\n")
			t = []
			for tdev in gs.tDevList:
				output += (str(tdev.name) + "\t|")
				t.append(tdev.getTemp())
			output += (gs.lightname)
			for g in gs.ch_list:
				output += ("\t|" + str(g.name))
			output += ("\n")

			# Get temperature(s).
			for temp in t:
				if (t == None):
					logging.debug("No temperature sensor")
					output += ("Faal\t|")
				else:
					output += (str(temp) + "\t|")

			# Get light level.
			l = gs.adc.getMeasurement(gs.lightname, 1)
			output += (str(l))

			# Get moisture levels and if needed, start a watering thread for the sensor.
			check_connected()
			for g in gs.ch_list:
				if (g.connected and not g.watering):
					lvl = gs.adc.getMeasurement(g.name, 0)
					if (lvl <= g.lowtrig and gs.pump.enabled):
						if (not gs.testmode):
							g.below_range += 1
							if (g.below_range >= 5):
# check this (g,) ->		t = threading.Thread(name = "Watering ch" + str(g.chan), target = watering, args = (g,))
#								t.setDaemon(True)
#								t.start()
								wt = wateringthread(gs.getThreadNr(), "watering" + str(g.chan + 1), args = g)
								wt.start()
								gs.wtrThreads.append(wt)
								g.below_range = 0
								g.watering = True
				if (g.watering):
					output += ("\t|Bezig")
				elif (not g.connected):
					output += ("\t|N/C")
				else:
					output += ("\t|" + convertToPrec(lvl, 1))

			print(output)
			gs.currentstats = output
			sleep = gs.time_res-(time.time()-start)
			if (sleep > 0):
				time.sleep(sleep)
			# End of loop
	except KeyboardInterrupt:
		pass
	finally:
		for t in gs.wtrThreads:
			t.join()

def watering(g):
	"""\tControls the actual watering. Watering is intermittent to allow the water to
	drain a little to get a better measurement."""
	
	g.watering = True
	start = time.time()
	t = 1
	while (gs.pump.enabled and g.connected):
		gs.pump.waterChannel(g, int(12/t))
		if (not g.connected or t == 3):
			break
		for i in range(45):
			time.sleep(1)
			if ((not gs.running) or gs.testmode):
				break
		lvl = gs.adc.getMeasurement(g.name, 0)
		if (lvl >= g.hightrig):
			t = 3
	g.watering = False
	end = int(time.time() - start)
	msg = "{0}: Done watering on channel {1}, watered for {2} seconds.".format(str(time.strftime("%H:%M:%S")), str(g.chan), str(end))
	print(msg)
	logging.info(msg)
	addToWlist(str(g.chan), end)

def check_connected():
	"""Checks and sets wether a sensor is connected to each channel of the ADC."""

	for g in gs.ch_list:
		lvl = gs.adc.getMeasurement(g.name, 0, True)
		if (lvl >= 150):
			g.connected = True
			gs.adc.channels[g.name].locked = False
			if (not g.connected):
				logging.debug("{} enabled. lvl: {}".format(g.chan + 1, lvl))
		else:
			g.connected = False
			gs.adc.channels[g.name].locked = True
			if (g.connected):
				logging.debug("{} disabled. lvl: {}".format(g.chan + 1, lvl))

def convertToPrec(data, places):
	"""Returns the percentage value of the number."""

	m = ((data * 100) / float(gs.adc.bits))
	return(str(round(m, places)))
						
def addToWlist(channel, length):
	"""Manages a list with the last %waterlength% watering notifications."""

	with open(gs.wateringlist, "r", newline = "") as filestream:
		file = csv.reader(filestream, delimiter = ",")
		stuff = []
		for line in file:
			stuff.append(line)
	while(True):
		if (len(stuff) >= gs.waterlength):
			del(stuff[0])
		else:
			break
	stuff.append([channel, int(time.time()), length])
	with open(gs.wateringlist, "w", newline = "") as filestream:
		file = csv.writer(filestream, delimiter = ",")
		for i in stuff:
			file.writerow(i)