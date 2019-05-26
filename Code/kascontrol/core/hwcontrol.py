#!/usr/bin/python3

# Author: J. Saarloos
# v0.10.07	25-04-2019


from abc import ABCMeta, abstractmethod
import logging
import time

from ..globstuff import globstuff as gs
from ..utils.threadingutils import ProtoThread
from .hwc.dbchecks import DBchecks as dbc
from .hwc.faninterface import FanInterface as fni
from .hwc.floatswitchinterface import FloatSwitchInterface as fsi
from .hwc.hwgroups import HWgroups as hwg
from .hwc.hwinit import HWinit as ini
from .hwc.hwmonitor import HWmonitor as hwm
from .hwc.hwspoof import HWspoof as hws
from .hwc.powercontrollerinterface import PowerControllerInterface as pci
from .hwc.powerledinterface import PowerLEDinterface as pli
from .hwc.requestdata import RequestData as rqd
from .hwc.waterflowsensorinterface import WaterFlowSensorInterface as wfi
# from .hwc.hwinit import HWinit as ini


class hwControl(wfi, rqd, pli, pci, hws, hwm, hwg, fsi, fni, dbc, ini):
	"""
	Main object for interacting with the hardware and taking appropriate actions
	like watering, and making sensordata available to outputs (console/network/display/ledbar).
	"""

	__metaclass__ = ABCMeta

	def __init__(self):
		super(hwControl, self).__init__()
		gs.control = self


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
		"""
		Reset and turn off all in- and outputs and ICs when
		shutting down the system.
		"""

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
		self.__spi.close()
		self.__gpio.cleanup()

	@abstractmethod
	def requestPower(self, *cur):
		return super().requestPower(cur)


class PowerManager(ProtoThread):
	def run(self):
		logging.info("Starting thread{0}: {1}".format(self.threadID, self.name))
		gs.control.startPowerManager()
		logging.info("Exiting thread{0}: {1}".format(self.threadID, self.name))
