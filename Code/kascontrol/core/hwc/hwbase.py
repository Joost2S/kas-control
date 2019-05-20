#!/usr/bin/python3

# Author: J. Saarloos
# v0.01.03	19-05-2019


from abc import ABCMeta, abstractmethod
from collections import OrderedDict


class HWbase(object):

	__metaclass__ = ABCMeta

	__adcMGR = None			# Manages the ADC devices. Currently only supports MCP3x0x devices.
	__connectedCheckValue = 0	# If value is below this threhold, sensor is considered disconnected
	__currentstats = ""		# Latest output of the monitor method. Is formatted for display in console.
	__enabled = True			# Dunno. TODO: make work or remove when most other things are done.
	__fan = None				# Reference to fan object.
	__fanToggleTemp = 45		# Temoerature at which to turn on fan.
	__floatSwitch = None		# Reference to floatSwitch object
	__flowMGR = None			# Waterflow sensor manager. Direct all queries for flowsensors of any type here.
	__gpio = None           # GPIO manager
	__groups = {}				# Dict with group instances. {name : group}
	__i2cBus = None
	__ina = {}					# Powermonitors. {name : ina219 object}
	__plcontroller = None	# Reference to powerLED controller
	__pump = None				# Reference to pump object.
	__lastPowerRequest = 0	# Time function to make sure a power request is enacted and current power draw includes last request.
	__LCD = None			   # Reference to LCDcontrol module for HD44780 device.
	__LEDbars = {}				# Reference to some LEDbars.
	__maxPower = 1.6			# Maximum allowed power draw in amps.
	__maxPSUtemp = 80.0		# Maximum allowed temperature for PSU. Above this, don't accept further power draw.
	__otherSensors = []		# List of sensor names that are not part of any group.
	__powerManager = None	# Priority queue to keep track of the powerconsuming devices on the 12v rail.
	__rawStats = {}			# Dict with the latest results from sensors. {senorName : latestValue}
	__sensors = OrderedDict()	# {name : type}
	__spi = None				# SPI manager
	__spoof = False
	__statusLED = None		# Reference to status led controller
	__tempbar = []				# List of sensor names for the temperature LEDbar
	__template = ""			# Template for __currentstats
	__tempMGR =  None			# Manager for DS18B20 temperature sensors
	__timeRes = 10.0			# How often the sensors get polled in seconds.

	def __init__(self):
		super(HWbase, self).__init__()

	def getADCres(self):
		"""Returns the resultion of the installed ADC."""

		return(self.__adcMGR.getResolution())

	@abstractmethod
	def requestData(self, stype=None, name=None, formatted=None):
		pass

	@abstractmethod
	def requestPower(self, *cur):
		pass
