#!/usr/bin/python3

# Author: J. Saarloos
# v0.10.07	25-04-2019


from abc import ABCMeta, abstractmethod
import logging
import time

from ..globstuff import globstuff as gs
from ..utils.protothread import ProtoThread
from .hwc.dbchecks import DBchecks as dbc
from .hwc.faninterface import FanInterface as fni
from .hwc.floatswitchinterface import FloatSwitchInterface as fsi
from .hwc.hwgroups import HWgroups as hwg
from .hwc.hwinit import HWinit as ini
from .hwc.hwmonitor import HWmonitor as hwm
from .hwc.hwspoof import HWspoof as hws
from .hwc.powercontrollerinterface import PowerControllerInterface as pci
from .hwc.powerledinterface import PowerLEDinterface as pli
from .hwc.waterflowsensorinterface import WaterFlowSensorInterface as wfi
# from .hwc.hwspoof import HWspoof as hws


class hwControl(wfi, pli, pci, hws, hwm, hwg, fsi, fni, dbc, ini):
	"""
	Main object for interacting with the hardware and taking appropriate actions
	like watering, and making sensordata available to outputs (console/network/display/ledbar).
	"""

	__metaclass__ = ABCMeta

	# Lists and dicts for storing sensors and groups
	# and accessing them in various ways.
	# __groups = {}				# Dict with group instances. {name : group}
	# __sensors = OrderedDict()	# {name : type}
	# __otherSensors = []		# List of sensor names that are not part of any group.
	# __adc = None				# u1
	# __tempMGR =  None			# Manager for DS18B20 temperature sensors
	# __flowSensors = {}		# List of all flowsensors. {name : flowMeter object}
	# __ina = {}					# Powermonitors. {name : ina219 object}
	# __statusLED = None		# Reference to status led controller
	# __plcontroller = None	# Reference to powerLED controller
	# __pump = None				# Reference to pump object.
	# __floatSwitch = None		# Reference to floatSwitch object
	# __LCD = None				# Reference to LCDcontrol module for HD44780 device.
	# __LEDbars = {}				# Reference to some LEDbars.
	# __tempbar = []				# List of sensor names for the temperature LEDbar
	# __fan = None				# Reference to fan object.
	# __fanToggleTemp = 45		# Temoerature at which to turn on fan.
	# __powerManager = None	# Priority queue to keep track of the powerconsuming devices on the 12v rail.
	# __template = ""			# Template for __currentstats
	# __currentstats = ""		# Latest output of the monitor method. Is formatted for display in console.
	# __rawStats = {}			# Dict with the latest results from sensors. {senorName : latestValue}
	# __timeRes = 0.0			# How often the sensors get polled in seconds.
	# __connectedCheckValue = 0	# If value is below this threhold, sensor is considered disconnected
	# __maxPower = 1.6			# Maximum allowed power draw in amps.
	# __lastPowerRequest = 0	# Time function to make sure a power request is enacted and current power draw includes last request.
	# __maxPSUtemp = 80.0		# Maximum allowed temperature for PSU. Above this, don't accept further power draw.
	# __enabled = True			# Dunno.
	# __spoof = False

	def __init__(self):
		super(hwControl, self).__init__()

		# self.__adc = MCP3208(spi=gs.spi, dev=0,
		#                              tLock=gs.spiLock,
		#                              gpio=gs.mcplist[0])
		# self.__connectedCheckValue = self.__adc.getResolution() * 0.05
		# self.__tempMGR = tdevManager()
		# self.__setINA219devs()
		# self.__setDataFromFile()
		# if (gs.hwOptions["powermonitor"]):
		# 	gs.pwrmgr.setINA(self.__ina["12v"])
		# self.__statusLED = sigLED(gs.sLEDpin)
		# self.__pump = Pump(gs.pumpPin, self.__statusLED)
		# if (gs.hwOptions["floatswitch"]):
		# 	self.__floatSwitch = floatUp(gs.float_switch, self.__pump, self.__statusLED)
		# if (gs.hwOptions["lcd"]):
		# 	self.__setLCD()
		# if (gs.hwOptions["ledbars"]):
		# 	self.__setLEDbars()
		# if (gs.hwOptions["powermonitor"]):
		# 	self.__plcontroller = PowerLEDcontroller()
		# if (gs.hwOptions["fan"]):
		# 	self.__fan = Fan(gs.fanPin)
		gs.control = self


	def requestData(self, stype = None, name = None, caller = None, perc = False):
		"""
		Main method for getting sensor data.
		Be aware that calling this method with different arguments will result in
		different types of variables being returned and even calling it with the
		same arguments may result in different types being returned at different times.
		"""

		if (self.__spoof):
			return(self.__getSpoofData(stype, name, caller))
		try:
			# Get data from specific sensor.
			if (name is not None):
				name = name.replace("_", "-")
				if (name in self.__sensors.keys()):
					if (stype is not None and stype is not self.__sensors[name]):
						return("Sensor {} is not of type {}.".format(name, stype))
					stype = self.__sensors[name][1]
					if (stype == "mst"):
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
					if (stype == "light"):
						return(self.__adc.getMeasurement(name, perc))
					if (stype == "cputemp"):
						return(gs.getCPUtemp())
					if (stype == "flow"):
						if (not gs.hwOptions["flowsensors"]):
							return(None)
						if (caller == "db"):
							return(self.__flowSensors[name].storePulses())
						return(self.__flowSensors[name].getFlowRate())
					if (stype == "temp"):
						if (name[-2] == "g" and not gs.hwOptions["soiltemp"]):
							return(None)
						temp = self.__tempMGR.getMeasurement(name)
						if (name.upper() == "PSU"):
							self.__checkPSUtemp(temp)
						return(temp)
				elif (stype == "pwr"):
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
					if (stype == "mst"):
						return(self.__groups[name].getM())
					elif (stype == "temp"):
						return(self.__groups[name].getT())
					elif (stype == "flow"):
						return(self.__groups[name].getF())
					else:
						return(self.__groups[name].getSensorData())
				else:
					logging.warning("Requested sensor does not exist. Name: {}".format(name))
					return(False)
			# Get data from all sensors of specified type.
			# return [[sensorname, value], ...]
			elif (stype is not None):
				data = []
				for n, t in self.__sensors.items():
					if (t == stype):
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
			logging.error("Error occured during measurement of " + str(stype) + " at channel: " + str(name))
			return(False)

	def __checkPSUtemp(self, temp):

		if (temp > self.__maxPSUtemp):
			pass
			#doEmergencyThing()
		elif (temp > self.__fanToggleTemp):
			if (not self.__fan.state()):
				self.__fan.on()
		elif (temp < (self.__fanToggleTemp - 15)):
			if (self.__fan.state()):
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
				check, msg = self._checkIfPumpIsAvailable(self.__groups[name].valve, self.__pump)
			else:
				check, msg = self._checkIfPumpIsAvailable(self.__groups[name].valve)
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

	def _checkIfPumpIsAvailable(self, *cur):
		"""Use this to check if the pump is available for use."""

		# Add calendar function.
		if (not self.__pump.enabled):
			return(False, "Pump is currently disabled.")
		if (not self.requestPower(cur)):
			return(False, "Not enough power available.")
		if (self.__floatSwitch.getStatus() and gs.hwOptions["floatswitch"]):
			return("Not enough water in the container.")
		return(True, "All good.")

	def disable(self):

		self.__enabled = False
		while (self.__pump.isPumping):
			time.sleep(0.1)
		self.__pump.off()

	def lcdNames(self, names):

		self.LCD.names(names)

	def isPumpEnabled(self):
		"""Returns pump availability"""

		return(self.__pump.enabled)

	def getSensors(self):
		"""Data for setting up database."""

		return(self.__sensors)

	def setLEDbarMode(self, mode):

		for bar in self.__LEDbars.values():
			bar.setMode(mode)

	def getLEDbarConfig(self):

		data = []
		for name, bar in self.__LEDbars.items():
			data.append(name)
			data.append(bar.getConfig())

	def connCheckValue(self):
		"""Returns the value below which a soil moisture sensor is considered disconnected."""

		return(self.__connectedCheckValue)

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

	@abstractmethod
	def requestPower(self, *cur):
		return super().requestPower(cur)


class PowerManager(ProtoThread):
	def run(self):
		logging.info("Starting thread{0}: {1}".format(self.threadID, self.name))
		gs.control.startPowerManager()
		logging.info("Exiting thread{0}: {1}".format(self.threadID, self.name))
