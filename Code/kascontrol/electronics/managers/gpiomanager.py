#!/usr/bin/python3

# Author: J. Saarloos
# v0.01.03	26-05-2019


import logging
import RPi.GPIO as GPIO
import uuid

from Code.kascontrol.globstuff import globstuff as gs
from Code.kascontrol.electronics.drivers.mcp230xx import mcp23017
from Code.kascontrol.electronics.drivers.mcp230xx import mcp23008


class GPIOManager(object):

	devByAddr = dict()
	devByBoardDes = dict()
	devByNr = dict()
	devSetups = list()
	finalized = False
	setPins = list() # pins that are set up are registered here so no duplicates are set.
					# gets deleted upon finalisation of manager
	pinList = dict() # list of all set pins. Used throughout program lifecycle.

	def __init__(self, smBus):
		super(GPIOManager, self).__init__()

		GPIO.setmode(GPIO.BCM)
		GPIO.setwarnings(False)
		self.smBus = smBus
		self.supportedDevices = [
			"rpi", "mcp23017", "mcp23008"
		]
		self.setDevices()

	def setDevices(self):

		self.devByNr[-1] = GPIO
		self.devByBoardDes["j1"] = GPIO
		self.devByAddr["rpi"] = GPIO
		data = gs.getSetupFile("hardware")
		try:
			self.setMCP32017devices(data["mcp23017"])
		except KeyError:
			pass
		try:
			self.setMCP32008devices(data["mcp23008"])
		except KeyError:
			pass

	def setMCP32017devices(self, setup):

		for dev in setup:
			try:
				intPin = dev["interuptPin"]
			except KeyError:
				intPin = None
			try:
				intPin2 = dev["interuptPin2"]
			except KeyError:
				intPin2 = None
			device = mcp23017(
						devAddr=int(dev["address"], 16),
                  intPin=intPin,
						intPin2=intPin2,
						bus=self.smBus)
			self.devByNr[dev["number"]] = device
			self.devByBoardDes[dev["boardDesignation"]] = device
			self.devByAddr[dev["address"]] = device
			self.devSetups.append(dev)

	def setMCP32008devices(self, setup):

		for dev in setup:
			try:
				intPin = dev["interuptPin"]
			except KeyError:
				intPin = None
			device = mcp23008(
						devAddr=int(dev["address"], 16),
                  intPin=intPin,
						bus=self.smBus)
			self.devByNr[dev["number"]] = device
			self.devByBoardDes[dev["boardDesignation"]] = device
			self.devByAddr[dev["address"]] = device
			self.devSetups.append(dev)

	def setPin(self, pin, state, devAddr=None, devNr=None, devDes=None, args=None):

		if devAddr is devNr is devDes is None:
			return False
		if self.finalized is True:
			if devAddr is not None:
				device = devAddr
			elif devNr is not None:
				device = devNr
			else:
				device = devDes
			logging.debug("Tried to set pin {} on device {} when GPIO is already enabled".format(pin, device))
			return False
		dev = self.__getDevice(number=devNr, address=devAddr, designation=devDes)
		if isinstance(dev, (mcp23017, mcp23008)):
			return self.__setmcp230xxPin(dev, pin, state)
		if isinstance(dev, GPIO):
			return self.__setRPiPin(pin, state, args)
		return False

	def __setmcp230xxPin(self, device, pin, direction):

		if not self.__checkPinToSet(device.devAddr, pin):
			return False
		uid = device.setPin(pin=pin, direction=direction, exclusive=True)
		self.pinList[uid] = {"device": device,
		                     "input": device.getPinState,
		                     "output": device.output,
		                     "address": hex(device.devAddr),
		                     "pin": pin,
		                     "direction": direction}
		return uid

	def __setRPiPin(self, pin, direction, args):

		if not self.__checkPinToSet("rpi", pin):
			return False
		if direction:
			direction = GPIO.IN
		else:
			direction = GPIO.OUT
		pud = None
		try:
			if args["pud"] == "down":
				pud = GPIO.PUD_DOWN
			elif args["pud"] == "up":
				pud = GPIO.PUD_UP
			elif args["pud"] == "both":
				pud = GPIO.PUD_UP
		except KeyError:
			pass
		GPIO.setup(pin, direction, pull_up_down=pud)
		uid = uuid.uuid4()
		self.pinList[uid] = {"device": GPIO,
		                     "input": GPIO.input,
		                     "output": GPIO.output,
		                     "address": "rpi",
		                     "pin": pin,
		                     "direction": direction}
		return uid

	def __checkPinToSet(self, address, pin):

		setPin = {
			"address": address,
			"pin": pin
		}
		if setPin in self.setPins:
			logging.debug("Pin {} {} already set".format(address, pin))
			return False
		self.setPins.append(setPin)
		return True

	def addInterrupt(self, pin, edge, callback, args=None):

		try:
			p = self.pinList[pin]
		except KeyError:
			logging.debug("Interrupt requested for unknown pin.")
			return False
		if p["state"] is False:
			logging.debug("Tried to add interrupt on output pin.")
			return False
		if isinstance(p["device"], GPIO):
			self.__setRpiInterrupt(p, edge, callback, args)
		elif isinstance(p["device"], (mcp23017, mcp23008)):
			p["device"].addInterruptInput(pin=p["pin"],
			                              callback=callback,
			                              edge=edge)

	def __setRpiInterrupt(self, pin, edge, callback, args):
		if edge.lower() == "rising":
			edge = GPIO.RISING
		elif edge.lower() == "falling":
			edge = GPIO.FALLING
		elif edge.lower() == "both":
			edge = GPIO.BOTH
		else:
			logging.error("Illegal edge for pin {} on rPi.GPIO".format(pin["pin"]))
			return
		bouncetime = None
		try:
			bouncetime = args["bouncetime"]
		except KeyError:
			pass
		GPIO.add_event_detect(channel=pin["pin"],
		                      edge=edge,
		                      callback=callback,
		                      bouncetime=bouncetime)

	def finalize(self):
		self.finalized = True
		del(self.setPins)
		for dev in self.devByAddr.values():
			if isinstance(dev, (mcp23017, mcp23008)):
				dev.engage()

	def cleanup(self):

		self.finalized = False
		for dev in self.devByAddr.values():
			if isinstance(dev, (mcp23017, mcp23008)):
				dev.allOff()
		GPIO.cleanup()

	def getState(self, number=None, address=None, pin=None):

		dev = self.__getDevice(number=number, address=address, pin=pin)
		state = bool()
		return state

	def __getDevice(self, pin=None, number=None, address=None, designation=None):

		if pin is not None:
			try:
				return self.pinList[pin]
			except KeyError:
				return "Unknown GPIO pin: {}".format(pin)

		if number is not None:
			try:
				return self.devByNr[number]
			except KeyError:
				return "Unknown GPIO device: {}".format(number)

		if address is not None:
			try:
				return self.devByAddr[address]
			except KeyError:
				return "Unknown GPIO device: {}".format(address)

		if designation is not None:
			try:
				return self.devByBoardDes[designation]
			except KeyError:
				return "Unknown GPIO device: {}".format(designation)

	def getSetups(self):

		return self.devSetups

	def getAddress(self, pin):
		"""Reverse look-up. Get pin address and number for pin ID."""

		try:
			return {"address": self.pinList[pin]["address"],
			        "pin": self.pinList[pin]["pin"]}
		except KeyError:
			return None

	def input(self, pin):

		if not self.finalized:
			return
		try:
			p = self.pinList[pin]
			return p["input"](p["pin"])
		except KeyError:
			logging.debug("Pin {} not found.".format(pin))

	def output(self, pin, state):

		if not self.finalized:
			return
		try:
			p = self.pinList[pin]
			return p["output"](p["pin"], state)
		except KeyError:
			logging.debug("Pin {} not found.".format(pin))
