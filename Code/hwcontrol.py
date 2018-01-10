#!/usr/bin/python3
 
# Author: J. Saarloos
# v0.9.8	09-01-2018

import csv
from datetime import datetime, timedelta
import logging
import RPi.GPIO as GPIO
import threading
import time

import ds18b20
import flowsensor
import group
import ina219
import mcp3x08
import globstuff

gs = globstuff.globstuff


class hwControl(object):
	"""\tObject handling the sensor inputs and taking appropriate hardware actions
	like watering, and making sensordata available to outputs (console/network/display).
	"""

	# Lists and dicts for storing sensors and groups 
	# and accessing them in various ways.
	__chanlist = []			# Should be removed in future version
	__groups = {}				# Dict with group instances. {name : group}
	__sensors = {}				# {name : type}
	__otherSensors = []		# List of sensor names that are not part of any group.
	__adc = None				# u1
	__tempMGR =  None			# Manager for DS18B20 temperature sensors
	__flowSensors = {}		# List of all flowsensors. {name : flowMeter object}
	__ina = {}					# Powermonitors. {name : ina219 object}
	__statusLED = None		# Reference to status led controller
	__pump = None				# Reference to pump object.
	__floatSwitch = None		# Reference to floatSwitch object
	__template = ""			# Template for __currentstats
	__currentstats = ""		# Latest output of the monitor method. Is formatted for display in console.
	__rawStats = []			# List with the latest results from sensors.
	__timeRes = 0.0			# How often the sensors get polled in seconds.
	__connectedCheckValue = 0	# If value is below this threhold, sensor is considered disconnected
	__enabled = True			# Dunno.
	__spoof = False

	def __init__(self):
		
		self.__adc = mcp3x08.mcp3208(0, gs.mcplist[0])
		self.__tempMGR = ds18b20.tdevManager()
		self.__connectedCheckValue = self.__adc.getResolution() * 0.05
		self.__setDataFromFile()
		self.__statusLED = globstuff.sigLED(gs.sLEDpin)
		self.__pump = globstuff.Pump(gs.pumpPin, self.__statusLED)
		self.__floatSwitch = globstuff.floatUp(gs.float_switch, self.__pump, self.__statusLED)
		self.__template = self.__setTemplate()
		self.setTimeRes()
		self.__check_connected()
		gs.control = self


	def requestData(self, type = None, name = None, caller = None, perc = False):
		""""""

		if (self.__spoof):
			return(self.__getSpoofData(type, name, caller))
		try:
			# Get data from specific sensor.
			if (name is not None):
				if (name in self.__sensors.keys()):
					if (type is not None and type is not self.__sensors[name]):
						return("Sensor {} is not of type {}.".format(name, type))
					type = self.__sensors[name][1]
					if (type == "mst"):
						if (caller == "db" or caller == "wtr"):
							return(self.__adc.getMeasurement(name, perc))
						else:
							for g in self.__groups.values():
								if (g.mstName == name):
									if (not g.connected):
										return("N/C")
									elif (g.watering):
										return("Busy")
									elif (not g.enabled):
										return("NoPlant")
									else:
										return(self.__adc.getMeasurement(name, perc))
						return(None)
					if (type == "light"):
						return(self.__adc.getMeasurement(name, perc))
					if (type == "cputemp"):
						return(gs.getCPUtemp())
					if (type == "flow"):
						if (not gs.hwOptions["flowsensors"]):
							return(None)
						if (caller == "db"):
							return(self.__flowSensors[name].storePulses())
						return
					if (type == "temp"):
						if (name[-2] == "g" and not gs.hwOptions["soiltemp"]):
							return(None)
						return(self.__tempMGR.getMeasurement(name))
					if (type == "pwr"):
						# name = "12vp"
						if (name[-1] == "p"):
							return(self.__ina[name[:-1]].getPower())
						# name = "12vc"
						if (name[-1] == "c"):
							return(self.__ina[name[:-1]].getCurrent())
						# name = "12vv"
						if (name[-1] == "v"):
							return(self.__ina[name[:-1]].getVolage())
				else:
					logging.warning("Requested sensor does not exist. Name: {}".format(name))
					return(False)
			elif (name in self.__groups.keys()):
				if (type == "mst"):
					return(self.__groups[name].getM())
				elif (type == "temp"):
					return(self.__groups[name].getT())
				elif (type == "flow"):
					return(self.__groups[name].getF())
			# Get data from all sensors of specified type.
			# return [[sensorname, value], ...]
			elif (type is not None):
				data = []
				for n, t in self.__sensors.items():
					if (t == type):
						val = self.requestData(n)
						if (val == False):
							val = "Error"
						data.append([n, val])
				return(data)

			# Get all data.
			else:
				return(self.__currentstats)
		except:
			logging.error("Error occured during measurement of " + str(type) + " at channel: " + str(name))
			return(False)
		
	def requestPumping(self, name, forTime = None):

		check = False
		while (not check):
			check, msg = self.__chekPumpAvail(self.__groups[name])
			logging.info(msg)
			if (not check):
				time.sleep(1)
			if (not gs.running):
				return
		if (not self.__pump.isPumping):
			self.__pump.on()
			time.sleep(0.1)
		self.__groups[name].valve.On()
		if (forTime is not None):
			for i in range(int(forTime)):
				time.sleep(1)
				if (not gs.running):
					break
			self.endPumpRequest(name)
	
	def endPumpRequest(self, chan):

		i = 0
		with self.lock:
			for g in self.__groups.values():
				if (g.valve.open):
					if (not self.valves[chan] == v):
						i += 1
			if (i == 0):
				self.valves[chan].open = False
				self.pump.off()
				time.sleep(0.1)
		self.valves[chan].off()
			
	def __chekPumpAvail(self, *cur):
		"""Add calendar function."""

		current = self.__ina["12v"].getCurrent()		# get current power draw from the PSU.
		for c in cur:
			current += c
		print("Expected power draw: " + str(current) + " mA")
		return(True, "All good.")

	def disable(self):

		self.__enabled = False

	def setTriggers(self, group, low = None, high = None):

		#Getting a pow(10) value instead of a pow(2):
		upperthreshold = self.getADCres() - (self.getADCres() % 1000)
		if (self.__groups[group].plantName is None):
			return("Container {} has no plant assigned. Cannot change trigger values.".format(group))
		if (not self.__groups[group].connected):
			return("Sensor for container {} is disconnected. Cannot change trigger values.".format(group))

		# when changing both triggers
		if (low is not None and high is not None):
			if (low < self.connCheckValue or high > upperthreshold):
				return("Values out of bounds. Must be {} < lowtrig < hightrig < {}".format(self.connCheckValue, upperthreshold))
			if (low >= high):
				return("Lowtrig must be lower than hightrig.")

		# When changing one trigger or none
		elif (low is not None):
			if (self.__groups[group].hightrig <= low):
				return("Too high value for lowtrig. Value must be < {}".format(self.__groups[group].hightrig))
			elif (low < self.__connectedCheckValue):
				return("Too low value for lowtrig. Value must be >= {}".format(self.__connectedCheckValue))
		elif (high is not None):
			if (self.__groups[group].lowtrig >= high):
				return("Too low value for hightrig. Value must be > {}".format(self.__groups[group].lowtrig))
			elif (high > upperthreshold):
				return("Too high value for hightrig. Value must be <= {}".format(upperthreshold))
		self.__groups[group].setTriggers(low, high)
		return("New value of trigger: {}, {}".format(self.__groups[group].lowtrig, self.__groups[group].hightrig))

	def getTriggers(self, group):
		
		if (group in self.__groups):
			return(self.__groups[group].lowtrig, self.__groups[group].hightrig)
		return(None, None)

	def addPlant(self, group, name, type = None):

		pass

	def getGroupName(self, group):

		if (group in self.__groups):
			return(self.__groups[group].getName())
		return(None)

	def getDBfields(self):

		return

	def setPlantsAndTriggers(self):

		for g in self.__groups.values():
			g.setFromDB()

	def __setDataFromFile(self):
		
		tempAddresses = self.__tempMGR.getTdevList()
		types = ["temp", "cputemp", "light", "flow", "pwr", "group"]
		with open(gs.sensSetup, "r", newline = "") as filestream:
			file = csv.reader(filestream, delimiter = ",")

			curType = ""	# Keeps track of last encountered data type.
			for line in file:
				if (len(line) > 0):
					# Search for data type. see types[].
					if (line[0][0] == "#"):
						if (len(line[0]) > 1):
							t = line[0][1:].strip()
							if (t in types):
								curType = t
					else:
						tdev = None
						output = []

						# Collecting variables...
						for item in line:
							output.append(str(item).strip())

						# Setting temp, light and flowsensors.
						if (curType in types[:-1]):
							if (curType == "temp"):
								if (output[1] in tempAddresses):
									tdev = output[1]
									self.__tempMGR.setDev(output[0], tdev)
								else:
									logging.warning("Addres not available: " + output[1])
								self.__sensors[output[0]] = curType
							elif (curType == "cputemp"):
								tdev = "cpu"
								self.__sensors[output[0]] = curType
							elif (curType == "light"):
								self.__sensors[output[0]] = curType
								gs.adc.setChannel(output[0], output[1])
							elif (curType == "flow" and gs.hwOptions["flowsensors"]):
								self.__flowSensors["flow-g" + i] = flowsensor.flowMeter(output[1])
							elif (curType == "pwr" and gs.hwOptions["powermonitor"]):
								self.__ina[output[0]] = ina219.ina219(output[1])
								self.__sensors[output[0]] = curType
							self.__otherSensors.append(output[0])
				
						# Setting sensors of groups and making group instances.
						else:
							i = str(len(self.__groups) + 1)
							name = "group" + i
							if (output[5] is not None and output[5] in tempAddresses):
								tdev = output[5]
							else:
								tdev = None
							mst = self.__setSoilSensor("soil-g" + i, output[3], output[2], output[1])
							if (gs.hwOptions["soiltemp"] and tdev is not None):
								self.__sensors["temp-g" + i] = "temp"
								self.__tempMGR.setDev("temp-g" + i, tdev)
							flow = self.__setFlowSensor("flow-g" + i, output[4])
							if (gs.hwOptions["flowSensors"]):
								self.__sensors["flow-g" + i] = "flow"
								self.__flowSensors["flow-g" + i] = flowsensor.flowMeter(output[4])
							else:
								logging.info("flowSensors not available.")
							self.__groups[name] = group.Group()#output	# group instance
							self.__chanlist.append(name)

	def __setSoilSensor(self, name, channel, ff1, ff2):

		gs.getPinDev(ff1).setPin(gs.getPinNr(ff1), False)
		gs.getPinDev(ff2).setPin(gs.getPinNr(ff2), False)
		gs.adc.setChannel(name, channel, ff1, ff2, gs.getPinDev(ff1))
		self.__sensors[name] = "mst"
		return(name)

	def __setTemplate(self):
		"""Generates the template for the formatted currentstats."""

		lines = []
		lines.append("{}")	# timestamp
		lines.append("Plant")
		lines.append("Mst")
		if (gs.hwOptions["flowsensors"]):
			lines.append("Water")
		if (gs.hwOptions["soiltemp"]):
			lines.append("Temp")
		for i in range(len(self.__groups)):
			lines[1] += "\t|{}"
			lines[2] += "\t|{}"
			if (gs.hwOptions["flowsensors"]):
				lines[3] += "\t|{}"
			if (gs.hwOptions["soiltemp"]):
				lines[4] += "\t|{}"
		lines.append("")
		currentlines = len(lines)
		lines.append("Light:\tTemps:")
		for t in self.__otherSensors:
			if (self.__sensors[t][1] == "temp"):
				lines[currentlines + 0] += "\t"
		lines[currentlines + 0] += "Water:"
		lines.append("")
		lines.append("")
		for t in self.__otherSensors:
			if (len(t) > 6):
				t = t[:6]
			lines[currentlines + 1] += "|{}\t".format(t)
			lines[currentlines + 2] += "|{}\t"
		template = ""
		for l in lines[:-1]:
			template += l + "\n"
		return(template + lines[-1])

	def monitor(self):
		"""\t\tMain monitoring method. Will check on the status of all sensors every %timeRes seconds.
		Will also start methods/actions based on the sensor input."""

		# output format:
		# timestamp:
		# plant	|group1	|group2	|group3	|group4	|group5	|group6
		# moist	|soil1	|soil2	|soil3	|soil4	|soil5	|soil6
		# water	|water1	|water2	|water3	|water4	|water5	|water6
		# temp	|temp1	|temp2	|temp3	|temp4	|temp5	|temp6
		# Other sensors:
		#	Light:	Temps:										Water:
		#	|ambient	|sun		|shade	|ambient	|cpu		|total
		#	|light	|temp		|temp		|temp		|temp		|water

		
		try:
			while (gs.running):
				data = []

				# Start collecting data.
				data.append(time.strftime("%H:%M:%S"))

				# Get group data.
				gn = []	# Group names
				gm = []	# Group moist data
				gt = []	# Group temp data
				gf = []	# Group flow data
				for g in self.__groups.values():
					n = g.getName()
					m, t, f = g.getSensorData()
					gn.append(n)
					gm.append(m)
					gt.append(t)
					gf.append(f)
					if (not gs.running):
						break
				
				# Get data from other sensors.
				sdata = []	# Data from the other sensors.
				for s in self.__otherSensors:
					if (self.__sensors[s][1] == "light"):
						sdata.append(gs.adc.getMeasurement(s, 0))
					elif (self.__sensors[s][1] == "temp"):
						if (self.__sensors[s][0] == "cpu"):
							sdata.append(gs.getCPUtemp())
						else:
							sdata.append(self.__sensors[s][0].getTemp())
					elif (self.__sensors[s][1] == "flow"):
						sdata.append(self.__sensors[s][0].getFlowRate())

				# Sort data to make it available in raw and formatted forms.
				data.extend(gn)
				data.extend(gm)
				if (gs.hwOptions["soiltemp"]):
					data.extend(gt)
				if (gs.hwOptions["flowsensors"]):
					data.extend(gf)
				data.extend(sdata)
				self.__rawStats = data

				# Formatting data.
				self.__currentstats = self.__template.format(*data)
				print(self.__currentstats)

				# Waiting for next interval of timeRes to start next itertion of loop.
				while (int(time.time()) % self.__timeRes != self.__timeRes - 1):
					time.sleep(1)
					if (not gs.running):
						return
				while (1):
					if (int(time.time()) % self.__timeRes == 0):
						break
					else:
						time.sleep(0.01)
				# End of loop

		except KeyboardInterrupt:
			pass
		finally:
			for t in gs.wtrThreads:
				t.join()
			
	def __check_connected(self):
		"""Checks and sets wether a sensor is connected to each channel of the ADC."""

		for g in self.__groups.values():
			lvl = self.__adc.getMeasurement(g.mstName)
			locked = lvl < self.__connectedCheckValue
			if (locked == g.connected):
				g.connected = not g.connected
				if (locked):
					logging.debug("{} disabled".format(g.groupname))
				else:
					logging.debug("{} enabled".format(g.groupname))
					
	def setTimeRes(self, time = None):
		"""
		Change the interval at which measurements are taken. Interval must be
		at least 5 and at least 0.8 * amount of ds18b20 sensors since they
		need .75s for a single measurement. Choosing a low value may result in
		missed updates when a sensor is giving trouble.
		If no time argument is given, the system will default to the amount
		of ds18b20 sensors in seconds, with a minimum of 5 seconds.
		"""
		
		tempsensors = float(len(self.__tempMGR.getTdevList()))
		if (time == None):
			if (tempsensors < 5):
				self.__timeRes = 5.0
			else:
				self.__timeRes = tempsensors
		else:
			time = int(time)
			if (time >= 5 and time >= tempsensors * 0.8):
				self.__timeRes = float(time)
			
	def isPumpEnabled(self):

		return(self.__pump.enabled)

	def getDBgroups(self):

		data = []
		for n, g in self.__groups.items():
			names = [g.mstName]
			if (gs.hwOptions["soiltemp"] and g.tempName is not None):
				names.append(g.tempName)
			if (gs.hwOptions["flowsensors"] and g.flowName is not None):
				names.append(g.flowName)
			data.append([n, names])
		return(data)

	def getADCres(self):

		return(self.__adc.getResolution())

	def grouplen(self):
		"""Returns the amount of containers."""

		return(len(self.__groups))

	def connCheckValue(self):

		return(self.__connectedCheckValue)

	def toggleSpoof(self):

		self.__spoof = not self.__spoof
		return(self.__spoof)

	def __getSpoofData(self, type = None, name = None, caller = None):

		return("Stuff.")