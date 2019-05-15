#!/usr/bin/python3

# Author: J. Saarloos
# v0.1.00	10-05-2019


import logging
import smbus

from Code.kascontrol.electronics.drivers.arduinoFlowmeter import ArduinoFlowmeter
from Code.kascontrol.electronics.drivers.flowsensor import FlowMeter


class FlowSensorManager(object):

	allowedTypes = ["arduino", "direct"]
	arduinos = []
	devices = {}
	bus = None

	def __init__(self, bus=None):
		super(FlowSensorManager, self).__init__()
		if bus is None:
			self.bus = smbus.SMBus(1)
		else:
			self.bus = bus

	def setArduinos(self, setup):
		for dev in setup:
			self.arduinos.append(ArduinoFlowmeter(dev["address"], self.bus))

	def setChannel(self, sname, args):
		if sname in self.devices.keys():
			logging.error("Flowsensor name {} already defined.".format(sname))
			return False
		try:
			if args["type"] not in self.allowedTypes:
				logging.error("Flowsensor type '{}' not allowed.".format(args["type"]))
				return False
		except KeyError:
			logging.error("No type given for flowsensor {}.".format(sname))
			return False
		if args["type"] == "direct":
			try:
				self.devices[sname] = FlowMeter(args["pin"])
				return True
			except KeyError:
				logging.warning("No 'pins' argument given for flowsensor {}.".format(sname))
				return False

		elif args["stype"] == "arduino":
			try:
				if args["channel"] not in self.devices.values():
					if args["channel"] < len(self.arduinos) * 6:
						self.devices[sname] = args["channel"]
						return True
					else:
						logging.error("Channel {} out of range.".format(args["channel"]))
						return False
				else:
					logging.error("Flowsensor channel {} already in use.".format(args["channel"]))
					return False
			except KeyError:
				logging.error("No 'channel' argument given for flowsensor {}.".format(sname))
				return False
		logging.info("Failed to create flowsensor {}, unknown sensor type.".format(args["stype"]))
