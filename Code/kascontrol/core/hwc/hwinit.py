#!/usr/bin/python3

# Author: J. Saarloos
# v0.01.00	25-04-2019


from abc import ABCMeta, abstractmethod
import json
import logging

from ...core.group import Group
from ...drivers.ds18b20 import tdevManager
from ...drivers.fan import Fan
from ...drivers.floatswitch import FloatSwitch
from ...drivers.flowsensor import flowMeter
from ...drivers.hd44780 import Adafruit_CharLCD
from ...drivers.ina219 import INA219
from ...drivers.lcdcontrol import lcdController
from ...drivers.ledbar import LEDbar
from ...drivers.mcp3x08 import MCP3208
from ...drivers.powerLEDs import PowerLEDcontroller
from ...drivers.pump import Pump
from ...drivers.sigLED import sigLED
from ...globstuff import globstuff as gs
from .hwbase import HWbase


class HWinit(HWbase):

	__metaclass__ = ABCMeta

	def __init__(self):
		super(HWinit, self).__init__()

		self.__adc = MCP3208(spi=gs.spi, dev=0,
		                             tLock=gs.spiLock,
		                             gpio=gs.mcplist[0])
		self.__connectedCheckValue = self.__adc.getResolution() * 0.05
		self.__tempMGR = tdevManager()
		self.__setINA219devs()
		self.__setDataFromFile()
		if (gs.hwOptions["powermonitor"]):
			gs.pwrmgr.setINA(self.__ina["12v"])
		self.__statusLED = sigLED(gs.sLEDpin)
		self.__pump = Pump(gs.pumpPin, self.__statusLED)
		if (gs.hwOptions["floatswitch"]):
			self.__floatSwitch = FloatSwitch(gs.float_switch, self.__pump, self.__statusLED)
		if (gs.hwOptions["lcd"]):
			self.__setLCD()
		if (gs.hwOptions["ledbars"]):
			self.__setLEDbars()
		if (gs.hwOptions["powermonitor"]):
			self.__plcontroller = PowerLEDcontroller()
		if (gs.hwOptions["fan"]):
			self.__fan = Fan(gs.fanPin)

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
				self.__flowSensors[sensor["name"]] = flowMeter(sensor["pin"])
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
				else:
					logging.error("Temperature sensor {}, {} not found.".format(tdev["name"], tdev["address"]))
			# Setting water flow meter sensor:
			fdev = data["flowMeter"]
			if (gs.hwOptions["flowSensors"] and fdev["pin"] is not None):
				self.__sensors[fdev["name"]] = "flow"
				self.__flowSensors[fdev["name"]] = flowMeter(fdev["pin"])
				fname = fdev["name"]
			# Creating group instance.
			self.__groups[data["name"]] = Group(data["continaerNumber"],
                                          data["name"], mname, tname,
                                          fname, data["valve"])

	def __setINA219devs(self):
		"""Set the registers of the INA219 devices and add voltage and current to sensors."""

		with open(gs.sensorSetup, "r") as f:
			data = json.load(f)
		for dev in data["ina219"]["devices"]:
			self.__ina[dev["name"]] = INA219(dev["address"], dev["voltage"])
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

		lcd = Adafruit_CharLCD(data["pins"], data["size"]["cols"],
		                               data["size"]["rows"], initial_backlight = 0)
		self.LCD = lcdController(lcd)
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

			self.__LEDbars[bar["name"]] = LEDbar(bar["pins"], bar["Icount"], bar["startAtEnd"])
			self.__LEDbars[bar["name"]].setNames(bar["sensors"])
			# else:
			# 	self.__LEDbars[bar[""]].setNames()

	@abstractmethod
	def requestData(self, stype = None, name = None, caller = None, perc = False):
		return super().requestData(stype = stype, name = name, caller = caller, perc = perc)

	@abstractmethod
	def requestPower(self, *cur):
		return super().requestPower(cur)
