﻿#!/usr/bin/python3

# Author: J. Saarloos
# v0.10.07	08-07-2018

from collections import OrderedDict
import json
import logging
import time

import ds18b20
import flowsensor
from globstuff import globstuff as gs
import globstuff
import group
import hd44780
import ina219
import lcdcontrol
import ledbar
import mcp3x08
import powerLEDs


class hwControl(object):
	"""
	Main object for interacting with the hardware and taking appropriate actions
	like watering, and making sensordata available to outputs (console/network/display/ledbar).
	"""

	# Lists and dicts for storing sensors and groups
	# and accessing them in various ways.
	__groups = {}				# Dict with group instances. {name : group}
	__sensors = OrderedDict()	# {name : type}
	__otherSensors = []		# List of sensor names that are not part of any group.
	__adc = None				# u1
	__tempMGR =  None			# Manager for DS18B20 temperature sensors
	__flowSensors = {}		# List of all flowsensors. {name : flowMeter object}
	__ina = {}					# Powermonitors. {name : ina219 object}
	__statusLED = None		# Reference to status led controller
	__plcontroller = None	# Reference to powerLED controller
	__pump = None				# Reference to pump object.
	__floatSwitch = None		# Reference to floatSwitch object
	LCD = None				   # Reference to LCDcontrol module for HD44780 device.
	__LEDbars = {}				# Reference to some LEDbars.
	__tempbar = []				# List of sensor names for the temperature LEDbar
	__fan = None				# Reference to fan object.
	__fanToggleTemp = 45		# Temoerature at which to turn on fan.
	__powerManager = None	# Priority queue to keep track of the powerconsuming devices on the 12v rail.
	__template = ""			# Template for __currentstats
	__currentstats = ""		# Latest output of the monitor method. Is formatted for display in console.
	__rawStats = {}			# Dict with the latest results from sensors. {senorName : latestValue}
	__timeRes = 0.0			# How often the sensors get polled in seconds.
	__connectedCheckValue = 0	# If value is below this threhold, sensor is considered disconnected
	__maxPower = 1.6			# Maximum allowed power draw in amps.
	__lastPowerRequest = 0	# Time function to make sure a power request is enacted and current power draw includes last request.
	__maxPSUtemp = 80.0		# Maximum allowed temperature for PSU. Above this, don't accept further power draw.
	__enabled = True			# Dunno.
	__spoof = False

	def __init__(self):

		self.__adc = mcp3x08.MCP3208(0, gs.mcplist[0])
		self.__connectedCheckValue = self.__adc.getResolution() * 0.05
		self.__tempMGR = ds18b20.tdevManager()
		self.__setINA219devs()
		self.__setDataFromFile()
		if (gs.hwOptions["powermonitor"]):
			gs.pwrmgr.setINA(self.__ina["12v"])
		self.__statusLED = globstuff.sigLED(gs.sLEDpin)
		self.__pump = globstuff.Pump(gs.pumpPin, self.__statusLED)
		if (gs.hwOptions["floatswitch"]):
			self.__floatSwitch = globstuff.floatUp(gs.float_switch, self.__pump, self.__statusLED)
		if (gs.hwOptions["lcd"]):
			self.__setLCD()
		if (gs.hwOptions["ledbars"]):
			self.__setLEDbars()
		if (gs.hwOptions["powermonitor"]):
			self.__plcontroller = powerLEDs.PowerLEDcontroller()
		if (gs.hwOptions["fan"]):
			self.__fan = globstuff.Fan(gs.fanPin)
		self.__setTemplate()
		self.setTimeRes()
		gs.control = self


	def requestData(self, type = None, name = None, caller = None, perc = False):
		"""
		Main method for getting sensor data.
		Be aware that calling this method with different arguments will result in
		different types of variables being returned and even calling it with the
		same arguments may result in different types being returned at different times.
		"""

		if (self.__spoof):
			return(self.__getSpoofData(type, name, caller))
		try:
			# Get data from specific sensor.
			if (name is not None):
				name = name.replace("_", "-")
				if (name in self.__sensors.keys()):
					if (type is not None and type is not self.__sensors[name]):
						return("Sensor {} is not of type {}.".format(name, type))
					type = self.__sensors[name][1]
					if (type == "mst"):
						for g in self.__groups.values():
							if (g.mstName == name):
								if (caller in ["db", "wtr"]):
									if (not g.enabled):
										return(None)
									if (not g.connected and caller == "db"):
										return(None)
									return(self.__adc.getMeasurement(name))
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
						return(self.__flowSensors[name].getFlowRate())
					if (type == "temp"):
						if (name[-2] == "g" and not gs.hwOptions["soiltemp"]):
							return(None)
						temp = self.__tempMGR.getMeasurement(name)
						if (name.upper() == "PSU"):
							self.__checkPSUtemp(temp)
						return(temp)
				elif (type == "pwr"):
					# name = "12vp"
					if (name[-1] == "p"):
						return(self.__ina[name[:-1]].getPower())
					# name = "12vc"
					if (name[-1] == "c"):
						return(self.__ina[name[:-1]].getCurrent())
					# name = "12vv"
					if (name[-1] == "v"):
						return(self.__ina[name[:-1]].getVolage())
					# name = "12vs"
					if (name[-1] == "s"):
						return(self.__ina[name[:-1]].getShuntVoltage())
				# If name is the name of a group with option for sensortype.
				elif (name in self.__groups.keys()):
					if (type == "mst"):
						return(self.__groups[name].getM())
					elif (type == "temp"):
						return(self.__groups[name].getT())
					elif (type == "flow"):
						return(self.__groups[name].getF())
					else:
						return(self.__groups[name].getSensorData())
				else:
					logging.warning("Requested sensor does not exist. Name: {}".format(name))
					return(False)
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

			# Get raw data for displays (LEDbar, LCD, network client).
			elif (caller == "display"):
				return(self.__rawStats)
			# Get all data.
			else:
				return(self.__currentstats)
		except:
			logging.error("Error occured during measurement of " + str(type) + " at channel: " + str(name))
			return(False)

	def __checkPSUtemp(self, temp):

		if (temp > self.__maxPSUtemp):
			pass
			#doEmergencyThing()
		elif (temp > self.__fanToggleTemp):
			if (not self.__fan.getState()):
				self.__fan.on()
		elif (temp < (self.__fanToggleTemp - 15)):
			if (self.__fan.getState()):
				self.__fan.off()

	def requestPumping(self, name, forTime = None):
		"""
		Method to request pumping water to a container. Requests will be accepted if
		enough resources are available, else it will be entered into a queue.
		"""

		check = False
		# Loop to wait while resources become available.
		while (not check):
			if (not self.__pump.isPumping):
				check, msg = self.__chekPumpAvail(self.__groups[name].valve, self.__pump)
			else:
				check, msg = self.__chekPumpAvail(self.__groups[name].valve)
			logging.info(msg)
			if (not check):
				time.sleep(1)
			if (not gs.running):
				return
		self.__groups[name].valve.on()
		# Turning on pump if not already pumping.
		if (not self.__pump.isPumping):
			time.sleep(0.1)
			self.__pump.on()
		if (forTime is not None):
			for i in range(int(forTime)):
				time.sleep(1)
				if (not gs.running):
					break
			self.endPumpRequest(name)

	def endPumpRequest(self, group):
		"""Turn off watering container."""

		# Checking if any other containers are being watered.
		i = 0
		for g in self.__groups.values():
			if (g.valve.open):
				if (not self.__groups[group] is g):
					i += 1
		# No other containers are being watered, turning off pump.
		if (i == 0):
			self.__pump.off()
			time.sleep(0.1)
		self.valves[group].off()

	def __chekPumpAvail(self, *cur):
		"""Use this to check if the pump is available for use."""

		# Add calendar function.
		if (not self.__pump.enabled):
			return(False, "Pump is currently disabled.")
		if (not self.__requestPower(cur)):
			return(False, "Not enough power available.")
		if (self.__floatSwitch.getStatus() and gs.hwOptions["floatswitch"]):
			return("Not enough water in the container.")
		return(True, "All good.")

	def __requestPower(self, *cur):
		"""Use this method to check if enough power is available for the requested action."""

		# There is a delay of a second so the effects of the last request can be noticed.
		while ((time.time() - self.__lastPowerRequest) < 1.0):
			time.sleep(1)
		self.__lastPowerRequest = time.time()
		if (gs.hwOptions["powermonitor"]):
			current = self.__ina["12v"].getCurrent()		# get current power draw from the PSU.
		else:
			# TODO: get ID, time, power, priority
			return (gs.pwrmgr.addRequest("a", "t", "p", "pri"))
		if (isinstance(cur[0], int)):
			for c in cur:
				current += c
		else:
			for c in cur:
				current += c.power
		print("Expected power draw: " + str(current) + " mA")
		if (current > self.__maxPower):
			return(False)
		return(True)

	def disable(self):

		self.__enabled = False
		while (self.__pump.isPumping):
			time.sleep(0.1)
		self.__pump.off()

	def setTriggers(self, group, low = None, high = None):
		"""Set 1 or both trigger levels for a container. Will be checked for valid values."""

		#Getting a base 10 value instead of a base 2 value:
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
		if (gs.hwOptions["ledbars"]):
			self.__LEDbars["mst"].updateBounds(self.__groups[group].groupname, self.__groups[group].lowtrig, self.__groups[group].hightrig)
		return("New value of trigger: {}, {}".format(self.__groups[group].lowtrig, self.__groups[group].hightrig))

	def getTriggers(self, group):
		"""Set a new trigger level for a container."""

		if (group in self.__groups):
			return(self.__groups[group].lowtrig, self.__groups[group].hightrig)
		return(None, None)

	def addPlant(self, group, name, species = None):
		"""Add a plant to a container. If a new species is added, it will be added to the database."""

		if (group in self.__groups):
			if (self.__groups[group].getName() == group):
				if(self.__groups[group].addPlant(name, group, species)):
					return("Added plant {} to container {}.".format(name.title(), group[-1]))
				return("Error trying to add plant. Check log for details.")
			return("Can't add new plant. Plant {} is already assigned to container {}.".format(self.__groups[group].getName(), group[-1]))
		return("Invalid group.")

	def removePlant(self, group):

		if (group in self.__groups):
			return(self.__groups[group].removePlant(group))

	def getGroupName(self, group):
		"""Returns the groupname or plantname if available."""

		if (group in self.__groups):
			return(self.__groups[group].getName())
		return(None)

	def setPlantsAndTriggers(self):
		"""Trigger each group to retrieve data from the database and activate if appropriate."""

		for g in self.__groups.values():
			g.setFromDB()
			#TODO: set lcd and ledbar trigger levels

	def __setDataFromFile(self):
		"""Sets all the sensors as defined in the sensors setup file."""

		with open(gs.sensorSetup, "r") as f:
			data = json.load(f)["sensorData"]
		for sensorType, setup in data.items():
			if (sensorType == "light"):
				self.__setLightSensors(setup)
			elif (sensorType == "temp"):
				self.__setTempSensors(setup)
			if (sensorType == "cputemp"):
				self.__setLCPUtempSensors(setup)
			if (sensorType == "flow"):
				self.__setFlowSensors(setup)
			if (sensorType == "groups"):
				self.__setGroupSensors(setup)

	def __setLightSensors(self, setup):
		""""""

		for sensor in setup["sensors"]:
			self.__adc.setChannel(sensor["name"], sensor["channel"])
			self.__sensors[sensor["name"]] = setup["type"]
			self.__otherSensors.append(sensor["name"])

	def __setTempSensors(self, setup):
		""""""

		tempAddresses = self.__tempMGR.getTdevList()
		for sensor in setup["sensors"]:
			if (sensor["address"] in tempAddresses):
				self.__tempMGR.setDev(sensor["name"], sensor["address"])
			else:
				logging.warning("Addres not available: " + sensor["address"])
			self.__sensors[sensor["name"]] = setup["type"]
			self.__otherSensors.append(sensor["name"])

	def __setLCPUtempSensors(self, setup):
		""""""

		for sensor in setup["sensors"]:
			self.__otherSensors.append(sensor["name"])
			self.__sensors[sensor["name"]] = setup["type"]

	def __setFlowSensors(self, setup):
		""""""

		if (gs.hwOptions["flowsensors"]):
			for sensor in setup["sensors"]:
				self.__flowSensors[sensor["name"]] = flowsensor.flowMeter(sensor["pin"])
				self.__sensors[sensor["name"]] = setup["type"]
				self.__otherSensors.append(sensor["name"])

	def __setGroupSensors(self, setup):
		""""""

		for data in setup["groupdata"]:
			if (not data["enabled"]):
				continue
			# Setting soil moisture level sensor:
			mst = data["mstSensor"]
			# self.__setSoilSensor(mname, output[3], output[2], output[1])
			gs.getPinDev(mst["ffPin1"]).setPin(gs.getPinNr(mst["ffPin1"]), False)
			gs.getPinDev(mst["ffPin2"]).setPin(gs.getPinNr(mst["ffPin2"]), False)
			self.__adc.setChannel(mst["name"], mst["ADCchannel"], mst["ffPin1"],
			                      mst["ffPin2"], gs.getPinDev(mst["ffPin1"]))
			self.__sensors[mst["name"]] = "mst"
			mname = mst["name"]
			tname = None
			fname = None
			# Setting soil temperature sensor:
			tdev = data["tempSensor"]
			if (gs.hwOptions["soiltemp"] and tdev["address"] is not None):
				if (self.__tempMGR.setDev(tdev["name"], tdev["address"])):
					self.__sensors[tdev["name"]] = "temp"
					tname = tdev["name"]
			# Setting water flow meter sensor:
			fdev = data["flowMeter"]
			if (gs.hwOptions["flowSensors"] and fdev["pin"] is not None):
				self.__sensors[fdev["name"]] = "flow"
				self.__flowSensors[fdev["name"]] = flowsensor.flowMeter(fdev["pin"])
				fname = fdev["name"]
			# Creating group instance.
			self.__groups[setup["name"]] = group.Group(data["name"], mname,
										tname, fname, data["valve"])

	def __setINA219devs(self):
		"""Set the registers of the INA219 devices and add voltage and current to sensors."""

		with open(gs.sensorSetup, "r") as f:
			data = json.load(f)
		for dev in data["ina219"]["devices"]:
			self.__ina[dev["name"]] = ina219.INA219(dev["address"], dev["voltage"])
			self.__ina[dev["name"]].setConfig(dev["PGA"], dev["BADC"], dev["SADC"], dev["mode"])
			self.__ina[dev["name"]].setCalibration(dev["maxCurrent"], dev["rShunt"])
			self.__ina[dev["name"]].engage()
			self.__sensors[dev["name"] + "v"] = data["ina219"]["type"]
			self.__otherSensors.append(dev["name"] + "v")
			self.__sensors[dev["name"] + "c"] = data["ina219"]["type"]
			self.__otherSensors.append(dev["name"] + "c")

	def __setLCD(self):

		with open(gs.sensorSetup, "r") as f:
			data = json.load(f)["lcd"]

		lcd = hd44780.Adafruit_CharLCD(data["pins"], data["size"]["cols"],
		                               data["size"]["rows"], initial_backlight = 0)
		self.LCD = lcdcontrol.lcdController(lcd)
		self.LCD.setNames(data["defaultSensors"])
		LCDmsg  = "   Welcome to   \n"
		LCDmsg += "   Kas-Control  "
		if (data["size"]["rows"] == 4):
			LCDmsg = "\n  " + LCDmsg[:17] + "  " + LCDmsg[17:]
		self.LCD.message(LCDmsg)

	def __setLEDbars(self):
		"""Sets the values and bounds for the LEDbars to display."""

		with open(gs.sensorSetup, "r") as f:
			data = json.load(f)
		for bar in data["ledbars"]["bars"]:

			self.__LEDbars[bar["name"]] = ledbar.LEDbar(bar["pins"], bar["Icount"], bar["startAtEnd"])
			self.__LEDbars[bar["name"]].setNames(bar["sensors"])
			# else:
			# 	self.__LEDbars[bar[""]].setNames()

	def __setTemplate(self):
		"""Generates the template for the formatted currentstats."""

		lines = list()
		lines.append("{time}")
		lines.append("Plant\t")
		lines.append("Mst\t")
		if (gs.hwOptions["flowsensors"]):
			lines.append("Water\t")
		if (gs.hwOptions["soiltemp"]):
			lines.append("Temp\t")
		for g in self.__groups.values():
			lines[1] += "{" + g.groupname + "}"
			lines[2] += "{" + g.mstName + "}"
			if (gs.hwOptions["flowsensors"]):
				lines[3] += "{" + g.flowName + "}"
			if (gs.hwOptions["soiltemp"]):
				lines[4] += "{" + g.tempName + "}"
		lines.append("")
		currentlines = len(lines)
		lines.append("Light:\tTemps:")
		if (gs.hwOptions["flowsensors"]):
			hasOtherFlow = False
			for t in self.__otherSensors:
				if (self.__sensors[t] == "flow"):
					hasOtherFlow = True
				if (self.__sensors[t] in ["temp", "cputemp"]):
					lines[currentlines + 0] += "\t"
			if (hasOtherFlow):
				lines[currentlines + 0] += "Water:"
		if (gs.hwOptions["powermonitor"]):
			for t in self.__otherSensors:
				if (self.__sensors[t] == "flow"):
					lines[currentlines + 0] += "\t"
			lines[currentlines + 0] += "Power:"
		lines.append("")
		lines.append("")
		for t in self.__otherSensors:
			lines[currentlines + 2] += "{" + t + "}"
			if (len(t) > 7):
				t = t[:7]
			lines[currentlines + 1] += gs.getTabs("|{}".format(t), 1)

		template = ""
		for l in lines:
			template += l + "\n"
		self.__template = template + "\n"

	def startMonitor(self):
		"""Use this function to start monitor to prevent more than 1 instance running at a time."""

		running = False
		for t in gs.draadjes:
			if (t.name == "Monitor" and t.is_alive()):
				if (running):
					return
				running = True
		self.__checkConnected()
		self.__monitor()

	def __monitor(self):
		"""\t\tMain monitoring method. Will check on the status of all sensors every %timeRes seconds.
		Will also start methods/actions based on the sensor input."""

		# output format:
		# {timestamp}:
		# plant	|{group1}|{group2}|{group3}|{group4}|{group5}|{group6}
		# moist	|{soil1}	|{soil2}	|{soil3}	|{soil4}	|{soil5}	|{soil6}
		# water	|{water1}|{water2}|{water3}|{water4}|{water5}|{water6}
		# temp	|{temp1}	|{temp2}	|{temp3}	|{temp4}	|{temp5}	|{temp6}
		# Other sensors:
		#	Light:	Temps:													Water:	Power:
		#	|{ambient}|{sun}	|{shade}	|{ambient}|{cpu}	|{PSU}	|{total}	|{5v}		|{5v}		|{12v}	|{12v}
		#	|{light}	|{temp}	|{temp}	|{temp}	|{temp}	|{temp}	|{water}	|{power}	|{volt}	|{power}	|{volt}


		#	Indicate to user that the system is up and running.
		if (gs.hwOptions["lcd"]):
			self.LCD.toggleBacklight()
		else:
			self.__statusLED.blinkSlow(3)

		try:
			while (gs.running):
				data = dict()

				# Start collecting data.
				data["time"] = time.strftime("%H:%M:%S")

				# Get group data.
				for g in self.__groups.values():
					n = g.getName()
					m, t, f = g.getSensorData()
					data[g.groupname] = n
					data[g.mstName] = m
					if (gs.hwOptions["soiltemp"]):
						data[g.tempName] = t
					if (gs.hwOptions["flowsensors"]):
						data[g.flowName] = f
					if (not gs.running):
						return

				# Get data from other sensors.
				for sname in self.__otherSensors:
					if (self.__sensors[sname] == "light"):
						data[sname] = self.requestData(name = sname, perc = True)
					else:
						data[sname] = self.requestData(name = sname)

				# Outputting data to availabe outouts:
				self.__rawStats = data
				# if (gs.hwOptions["lcd"]):
				# 	self.LCD.updateScreen()
				# if (gs.hwOptions["ledbars"]):
				# 	for bar in self.__LEDbars.values():
				# 		bar.updateBar()

				# Formatting data.
				for name, value in data.items():
					if (name == "time"):
						continue
					data[name] = gs.getTabs("|" + str(value), 1)
				self.__currentstats = self.__template.format(**data)
				print(self.__currentstats)

				# Emitting event to alert devices of new data
				gs.ee.emit("hwMonitorDataUpdate")

				# Waiting for next interval of timeRes to start next itertion of loop.
				if ((not gs.running) or gs.wait(self.__timeRes)):
					return
				# End of loop

		except KeyboardInterrupt:
			pass
		finally:
			for t in gs.wtrThreads:
				t.join()

	def __perc(self, value, decimals = 1):
		"""Returns the value as percentage of the ADC resolution."""

		return(round((value * 100) / float(self.__adc.getResolution()), decimals))

	def __checkConnected(self):
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

	def lcdNames(self, names):

		self.LCD.names(names)

	def powerLEDtoggle(self, channel):
		"""Toggle powerLED channel. Can only turn on if channel is set."""

		if (0 < channel <= len(gs.powerLEDpins)):
			if (self.__plcontroller.getState(channel)[0]):
				self.__plcontroller.turnOff(channel)
				return(True)
			if (self.__requestPower(self.__plcontroller.getState(channel)[2])):
				self.__plcontroller.turnOn(channel)
				return(True)
		return(False)

	def powerLEDon(self, channel):
		"""Turn on powerLED channel. Only possible if set."""

		if (0 < channel <= len(gs.powerLEDpins)):
			if (self.__requestPower(self.__plcontroller.getState(channel)[2])):
				self.__plcontroller.turnOn(channel)
				return(True)
		return(False)

	def powerLEDoff(self, channel):
		"""Turn off powerLED channel."""

		if (0 < channel <= len(gs.powerLEDpins)):
			self.__plcontroller.turnOff(channel)

	def powerLEDset(self, channel, mode):
		"""Set powerLED channel to mode: '1ww', '3ww', '3ir' to enable channel."""

		if (0 < channel <= len(gs.powerLEDpins)):
			self.__plcontroller.setLED(channel, mode)

	def powerLEDstate(self, channel):
		"""Returns state, mode and power of the powerLEDchannel."""

		if (0 < channel <= len(gs.powerLEDpins)):
			return(self.__plcontroller.getState(channel))

	def setTimeRes(self, time = None):
		"""
		Change the interval at which measurements are taken. Interval must be
		at least 5 and at least 0.8 * amount of ds18b20 sensors since they
		need .75s for a single measurement. Choosing a low value may result in
		missed updates when a sensor is giving trouble.
		If no time argument is given, the system will default to the amount
		of ds18b20 sensors in seconds, with a minimum of 5 seconds.
		"""

		tempsensors = len(self.__tempMGR.getTdevList())
		if (time is None):
			if (tempsensors < 5):
				self.__timeRes = 5
			else:
				self.__timeRes = tempsensors
		else:
			time = int(time)
			if (time >= 5 and time >= tempsensors * 0.8):
				self.__timeRes = float(time)

	def isPumpEnabled(self):
		"""Returns pump availability"""

		return(self.__pump.enabled)

	def getDBgroups(self):
		"""The DB uses this to make a new db or check integrity on startup."""

		data = {}
		for n, g in self.__groups.items():
			# SQLite3 doesn't support dashes (-) in column names, so replace with underscore (_).
			names = [g.mstName.replace("-", "_")]
			if (gs.hwOptions["soiltemp"] and g.tempName is not None):
				names.append(g.tempName.replace("-", "_"))
			if (gs.hwOptions["flowsensors"] and g.flowName is not None):
				names.append(g.flowName.replace("-", "_"))
			data[n] = names
		return(data)

	def getSensors(self):
		"""Data for setting up database."""

		return(self.__sensors)

	def getDBcheckData(self):
		"""Returns a table to be compared with the sensor setup in the database as integrity check."""

		groups = {}
		for name, g in self.getDBgroups().values():
			for sensor in g:
				groups[sensor] = name
		dbCheckData = []
		for i, s, t in enumerate(OrderedDict(sorted(self.__sensors.items()))):
			dbCheckData.append([s.replace("-", "_"), t, None, None])
			if (t == "mst" or t == "light"):
				dbCheckData[i][3] = self.getADCres()
			if (s in groups):
				dbCheckData[i][2] = groups[s]
		return(dbCheckData)

	def setLEDbarMode(self, mode):

		for bar in self.__LEDbars.values():
			bar.setMode(mode)

	def getLEDbarConfig(self):

		data = []
		for name, bar in self.__LEDbars.items():
			data.append(name)
			data.append(bar.getConfig())

	def getADCres(self):
		"""Returns the resultion of the installed ADC."""

		return(self.__adc.getResolution())

	def grouplen(self):
		"""Returns the amount of containers."""

		return(len(self.__groups))

	def connCheckValue(self):
		"""Returns the value below which a soil moisture sensor is considered disconnected."""

		return(self.__connectedCheckValue)

	def toggleSpoof(self):
		"""Toggle between real sensor data or algorithmically generated data."""

		self.__spoof = not self.__spoof
		return(self.__spoof)

	def __getSpoofData(self, type = None, name = None, caller = None):
		"""Returns fake sensor data generated by excessively advanced algorithms."""

		return("Stuff.")

	def shutdown(self):
		"""Reset and turn off all in- and outputs when shutting down the system."""

		if (gs.hwOptions["lcd"]):
			self.LCD.disable()
		if (gs.hwOptions["ledbars"]):
			for bar in self.__LEDbars.values():
				bar.setMode("off")
		self.__statusLED.off()
		self.__pump.disable()
		# Turn off valve in each Group.
		for g in self.__groups.values():
			g.valve.off()
		# reset INA219 devices if option.
		if (gs.hwOptions["powermonitor"]):
			for ina in self.__ina.values():
				ina.reset()
		if (gs.hwOptions["status LED"]):
			self.__statusLED.disable()


class Monitor(globstuff.protoThread):
	def run(self):
		logging.info("Starting thread{0}: {1}".format(self.threadID, self.name))
		gs.control.startMonitor()
		logging.info("Exiting thread{0}: {1}".format(self.threadID, self.name))


class PowerManager(globstuff.protoThread):
	def run(self):
		logging.info("Starting thread{0}: {1}".format(self.threadID, self.name))
		gs.control.startPowerManager()
		logging.info("Exiting thread{0}: {1}".format(self.threadID, self.name))