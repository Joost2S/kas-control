#!/usr/bin/python3

# Author: J. Saarloos
# v0.01.03	19-05-2019


from abc import ABCMeta, abstractmethod
import logging
import smbus

from Code.kascontrol.core.group import Group
from Code.kascontrol.electronics.drivers.floatswitch import FloatSwitch
from Code.kascontrol.electronics.drivers.hd44780 import Adafruit_CharLCD
from Code.kascontrol.electronics.drivers.ina219 import INA219
from Code.kascontrol.electronics.drivers.fan import Fan
from Code.kascontrol.electronics.drivers.ledbar import LEDbar
from Code.kascontrol.electronics.drivers.powerLEDs import PowerLEDcontroller
from Code.kascontrol.electronics.drivers.pump import Pump
from Code.kascontrol.electronics.drivers.sigLED import sigLED
from Code.kascontrol.electronics.managers.adcmanager import ADCmanager
from Code.kascontrol.electronics.managers.flowsensormanager import FlowSensorManager
from Code.kascontrol.electronics.managers.gpiomanager import GPIOManager
from Code.kascontrol.electronics.managers.lcdcontrol import lcdController
from Code.kascontrol.electronics.managers.spimanager import SPImanager
from Code.kascontrol.electronics.managers.tdevmanager import TDevManager
from Code.kascontrol.globstuff import globstuff as gs
from .hwbase import HWbase


class HWinit(HWbase):

	__metaclass__ = ABCMeta

	def __init__(self):
		super(HWinit, self).__init__()

		gs.hwOptions = gs.getSetupFile("hardware")["options"]
		self.__i2cBus = smbus.SMBus(1)
		self.__gpio = GPIOManager(self.__i2cBus)
		self.__spi = SPImanager(self.__gpio)
		self.__adcMGR = ADCmanager(gpio=self.__gpio, spi=self.__spi)
		# TODO: make ccv into a function
		# self.__connectedCheckValue = self.__adcMGR.getResolution() * 0.05
		self.__tempMGR = TDevManager()
		self.__flowMGR = FlowSensorManager(self.__i2cBus)
		self.__setINA219devs()
		self.__setSensorDataFromFile()
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
		self.__gpio.finalize()

	def __setSensorDataFromFile(self):
		"""Sets all the sensors as defined in the sensors setup file."""

		data = gs.getSetupFile("sensor")["sensorData"]
		for manager, sensors in data.items():
			if (manager == "light"):
				self.__setLightSensors(sensors)
			elif (manager == "temp"):
				self.__setTempSensors(sensors)
			if (manager == "flow"):
				self.__setFlowSensors(sensors)
			if (manager == "groups"):
				self.__setGroupSensors(sensors)

	def __setLightSensors(self, sensors):
		""""""

		for sensor in sensors["sensors"]:
			self.__adcMGR.setChannel(sensor["name"], sensor["channel"])
			self.__sensors[sensor["name"]] = sensors["type"]
			self.__otherSensors.append(sensor["name"])

	def __setTempSensors(self, sensors):
		""""""

		tempAddresses = self.__tempMGR.getTdevList()
		for sensor in sensors["sensors"]:
			if (sensor["address"] in tempAddresses):
				self.__tempMGR.setDev(sensor["name"], sensor["address"])
			else:
				logging.warning("Addres not available: " + sensor["address"])
			self.__sensors[sensor["name"]] = sensors["type"]
			self.__otherSensors.append(sensor["name"])

	def __setFlowSensors(self, sensors):
		""""""

		if (gs.hwOptions["flowsensors"]):
			for sensor in sensors["sensors"]:
				self.__flowMGR.setChannel(sensor["name"], args=sensor["setup"])
				self.__sensors[sensor["name"]] = sensors["type"]
				self.__otherSensors.append(sensor["name"])

	def __setGroupSensors(self, sensors):
		""""""

		for data in sensors:
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
			if (gs.hwOptions["flowSensors"]):
				if self.__flowMGR.setChannel(fdev["name"], fdev["setup"]) is True:
					self.__sensors[fdev["name"]] = "flow"
				fname = fdev["name"]
			# Creating group instance.
			self.__groups[data["name"]] = Group(data["containerNumber"],
			                                    data["name"], mname, tname,
			                                    fname, data["valve"])

	def __setINA219devs(self):
		"""Set the registers of the INA219 devices and add voltage and current to sensors."""

		data = gs.getSetupFile("hardware")
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

		data = gs.getSetupFile("hardware")["lcd"]

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

		data = gs.getSetupFile("hardware")
		for bar in data["ledbars"]["bars"]:

			self.__LEDbars[bar["name"]] = LEDbar(bar["pins"], bar["Icount"], bar["startAtEnd"])
			self.__LEDbars[bar["name"]].setNames(bar["sensors"])
			# else:
			# 	self.__LEDbars[bar[""]].setNames()

	@abstractmethod
	def requestData(self, stype=None, name=None, formatted=None):
		return super().requestData(stype=stype, name=name, formatted=formatted)

	@abstractmethod
	def requestPower(self, *cur):
		return super().requestPower(cur)
