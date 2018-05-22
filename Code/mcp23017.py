#!/usr/bin/python3

# Author: J. Saarloos
# v0.10.1	19-05-2018

"""
This is a python driver for an i2c MCP23017. python-smbus must be installed for this driver to work.
You have to set up the pins you want to use and device settings first. Then run engage().
After this you can use chip.
Exclusivity: Setting up a pin as exclusive returns a UUID that needs te be sent along when turning pins on and off.
For details about MCP23x17, see datasheet: http://ww1.microchip.com/downloads/en/DeviceDoc/20001952C.pdf
Currently undergoing changes to add support for mcp23008. Needs to be tested.
For details about MCP23x08, see datasheet: http://ww1.microchip.com/downloads/en/DeviceDoc/21919e.pdf
"""


from abc import ABCMeta, abstractmethod
from collections import Iterable
import logging
import smbus
import uuid


class Pin(object):
	# value
	@property
	def value(self):
		return(self.__value)
	@value.setter
	def value(self, value):
		self.__value = value
	# name
	@property
	def name(self):
		return(self.__name)
	@name.setter
	def name(self, name):
		self.__name = name
	# direction
	@property
	def direction(self):
		return(self.__direction)
	@direction.setter
	def direction(self, direction):
		self.__direction = direction
	# polarity
	@property
	def polarity(self):
		return(self.__polarity)
	@polarity.setter
	def polarity(self, polarity):
		self.__polarity = polarity
	# interrupt enable
	@property
	def intEn(self):
		return(self.__intEn)
	@intEn.setter
	def intEn(self, intEn):
		self.__intEn = intEn
	# Default comparison input value
	@property
	def defVal(self):
		return(self.__defVal)
	@defVal.setter
	def defVal(self, defVal):
		self.__defVal = defVal
	# Interrupt control value
	# If a bit is set, the corresponding I/O pin is compared against the associated bit in the DEFVAL register.
	# If a bit value is clear, the corresponding I/O pin is compared against the previous value
	@property
	def intCon(self):
		return(self.__intCon)
	@intCon.setter
	def intCon(self, intCon):
		self.__intCon = intCon
	# pull-up resistor
	@property
	def pullUp(self):
		return(self.__pullUp)
	@pullUp.setter
	def pullUp(self, pullUp):
		self.__pullUp = pullUp
	# state, to keep track of whether in output is on or off.
	@property
	def state(self):
		return(self.__state)
	@state.setter
	def state(self, state):
		self.__state = state

	def __init__(self, value, name):
		self.value = value
		self.name = name
		self.direction = False
		self.polarity = False
		self.intEn = False
		self.defVal = False
		self.intCon = False
		self.pullUp = False
		self.state = None
		self.__uuid = None

	def setDir(self, direction, exclusive=False):
		"""Set pin as input (True) or output (False)."""

		if (self.__uuid is not None):
			logging.warning("Attempt to assign new pin with exclusivty already claimed denied.")
			return(False)
		self.direction = direction
		if (self.direction):
			self.intEn = True
			self.intCon = True
			self.pullUp = False
		else:
			self.intEn = False
			self.intCon = False
			self.pullUp = False
			self.state = False
			if (exclusive):
				self.__uuid = uuid.uuid4()
		return(self.__uuid)

	def setState(self, state):
		if (not self.direction):
			self.state = state

	def validate(self, uid=None):
		if (self.__uuid is None):
			return(True)
		elif (uid is None):
			return(False)
		if (self.__uuid == uid):
			return(True)
		return(False)

	def showStatus(self):
		return("name: " + str(self.name) + "\ndir: " + str(self.direction) + "\npol: " + str(self.polarity) + "\nintEn: " + str(self.intEn)
			+ "\nintCon: " + str(self.intCon) + "\ndefval: " + str(self.defVal))


class mcp230xx(object):

	# bus
	@property
	def bus(self):
		return(self.__bus)
	@bus.setter
	def bus(self, bus):
		self.__bus = bus
	# enabled
	@property
	def enabled(self):
		return(self.__enabled)
	@enabled.setter
	def enabled(self, enabled):
		self.__enabled = enabled
	# devAddr
	@property
	def devAddr(self):
		return(self.__devAddr)
	@devAddr.setter
	def devAddr(self, devAddr):
		self.__devAddr = devAddr
	# intPin
	@property
	def intPin(self):
		return(self.__intPin)
	@intPin.setter
	def intPin(self, intPin):
		self.__intPin = intPin
	# GPA
	@property
	def GPA(self):
		return(self.__GPA)
	@GPA.setter
	def GPA(self, GPA):
		self.__GPA = GPA
	# interruptObjects
	@property
	def interruptObjects(self):
		return(self.__interruptObjects)
	@interruptObjects.setter
	def interruptObjects(self, interruptObjects):
		self.__interruptObjects = interruptObjects
	# regMap
	@property
	def regMap(self):
		return(self.__regMap)
	@regMap.setter
	def regMap(self, regMap):
		self.__regMap = regMap

	IOCON = {
		"INTPOL": True,
			"ODR": True,
		  "HAEN": True,
		"DISSLW": True,
		 "SEQOP": True,
		"MIRROR": True,
		  "BANK": False
	}

	trigger =  {"high" : (False, True, True),
					"low" : (True, True, True),
					"both" : (False, False, True)
					}

	def __init__(self, devAddr, intPin = None):

		self.__metaclass__ = ABCMeta
		self.devAddr = devAddr
		self.bus = smbus.SMBus(1)	# 0 = /dev/i2c-0 (port I2C0), 1 = /dev/i2c-1 (port I2C1)
		self.intPin = intPin
		self.hasAinput = False		#	True if there is at least one pin in the A bank set as an input.
		self.enabled = False
		self.interruptObjects = {}
		self.GPA = []
		# Setting interrupt pin on the Raspberry Pi.
		if (self.intPin is not None):
			import RPi.GPIO as GPIO
			GPIO.setup(self.intPin, GPIO.IN, pull_up_down = GPIO.PUD_UP)
			GPIO.add_event_detect(self.intPin, GPIO.FALLING, callback = self.runInterrupt)
			logging.info("Set interrupt on {} with GPIO pin {}".format(hex(self.devAddr), self.intPin))
		# Populating banks with unset pins.
		for i in range(8):
			self.GPA.append(Pin(2 ** i, "B" + str(i)))


	@abstractmethod
	def checkPinInput(self, input):
			return(self.GPA, input)

	@abstractmethod
	def getInterruptPin(self):
		pass

	@abstractmethod
	def engage(self):
		pass

	def setRegisters(self, bank, bankChar = ""):

		# GPIO DIRECTION input/output setup
		ioDir = 0x00
		for pin in bank:
			if (pin.direction):
				ioDir += pin.value
		self.bus.write_byte_data(self.devAddr, self.regMap["IODIR" + bankChar], ioDir)

		# GPI POLARITY setup
		IPOL = 0x00
		for pin in bank:
			if (pin.polarity):
				IPOL += pin.value
		self.bus.write_byte_data(self.devAddr, self.regMap["IPOL" + bankChar], IPOL)

		# GPINTEN interrupt enable setup
		intEn = 0x00
		for pin in bank:
			if (pin.intEn):
				intEn += pin.value
		self.bus.write_byte_data(self.devAddr, self.regMap["GPINTEN" + bankChar], intEn)

		# Default compare value for interrupt-on-change, compare to high or low.
		defVal = 0x00
		for pin in bank:
			if (pin.defVal):
				defVal += pin.value
		self.bus.write_byte_data(self.devAddr, self.regMap["DEFVAL" + bankChar], defVal)

		# Interrupt compare register, compare to DEFVAL or last pinstate.
		intCon = 0x00
		for pin in self.GPA:
			if (pin.intCon):
				intCon += pin.value
		self.bus.write_byte_data(self.devAddr, self.regMap["INTCON" + bankChar], intCon)

		# GPI PULLUP resistor setup
		GPPU = 0x00
		for pin in self.GPA:
			if (pin.pullUp):
				GPPU += pin.value
		self.bus.write_byte_data(self.devAddr, self.regMap["GPPU" + bankChar], GPPU)

		# General configuration
		s = 2
		value = 0x00
		for setting in self.IOCON:
			if (self.IOCON[setting]):
				value += s
			s *= 2

		return(value)

	def setPin(self, pin, direction, exclusive=False):
		"""Call this method to setup a pin as input (direction = True) or output (direction = False).
		Returns False if exclsivty is alreay claimed."""

		if (not self.enabled):
			try:
				bank, pin = self.checkPinInput(pin)
			except PinValueError:
				return
			if (bank == self.GPA and direction):
				self.hasAinput = True
			elif (direction):
				self.hasBinput = True
			uid = bank[pin].setDir(direction, exclusive)
			if (exclusive and not direction):
				return(uid)
		else:
			logging.debug("MCP23017 device on {} is already enabled. Can't change pin {} anymore.".format(hex(self.devAddr), pin))

	def setSetup(self, reg, val):
		"""Call this method to change a setting in IOCON. See datasheet for details."""

		if (reg.upper() in self.IOCON.keys()):
			try:
				self.IOCON[reg.upper()] = bool(val)
			except ValueError:
				logging.warning("Failed to set register " + str(reg).upper())
		else:
			logging.debug("Cannot set register {}. Does not exist.".format(reg.upper()))

	def output(self, pins, state, uid=None):
		"""Call this method to change one or more output pins to low (state = False) or high (state = True)."""

		if (self.enabled):
			AbankChanged = False
			BbankChanged = False
			if (not self.__typeCheck(pins)):
				pins = (pins, )
			for p in pins:
				try:
					bank, pin = self.checkPinInput(p)
				except PinValueError:
					logging.debug("Output requested on invalid pin {}:{}".format(hex(self.devAddr), p))
					continue
				if (not bank[pin].validate(uid)):
					logging.warning("Unauthorized access to pin {}:{} requested and denied.".format(hex(self.devAddr), p))
					continue
				if (bank == self.GPA):
					AbankChanged = True
				else:
					BbankChanged = True
					# Changing state in driver software only.
				bank[pin].setState(state)
			# Changing the pins in the GPIO device. Need to be set per bank (NCP23017).
			if (AbankChanged):
				OLATa = 0x00
				for p in self.GPA:
					if (p.state):
						OLATa += p.value
				self.bus.write_byte_data(self.devAddr, self.regMap["OLATA"], OLATa)
			if (BbankChanged):
				OLATb = 0x00
				for p in self.GPB:
					if (p.state):
						OLATb += p.value
				self.bus.write_byte_data(self.devAddr, self.regMap["OLATB"], OLATb)
		else:
			logging.debug("MCP23017 on " + hex(self.devAddr) + " not enabled yet.")

	def __typeCheck(self, obj):
		"""Returns True if iterable, False if str."""

		return not isinstance(obj, str) and isinstance(obj, Iterable)

	def allOff(self):
		"""Call this method when shutting down the software to turn all outputs off."""

		for p in self.GPA:
			if (not p.direction):
				p.setState(False)
		for p in self.GPA:
			if (not p.direction):
				p.setState(False)
		self.bus.write_byte_data(self.devAddr, self.regMap["OLATA"], 0x00)
		self.bus.write_byte_data(self.devAddr, self.regMap["OLATB"], 0x00)

	def interruptSeperate(self, intPin):
		"""This method should be called when 2 iterrupt pins are set."""

		bank = 0
		gp = None
		if (intPin == self.intPin):
			gp = self.GPA
			bank = int(self.bus.read_byte_data(self.devAddr, self.regMap["INTCAPA"]))
		elif (intPin == self.intPin2):
			gp = self.GPB
			bank = int(self.bus.read_byte_data(self.devAddr, self.regMap["INTCAPB"]))
		else:
			return("Invalid intPin " + str(intPin))
		for p in gp:
			if (p.direction):
				if (not (p.value & bank) == 0):
					logging.debug("Interrupt triggered on pin {}:{}".format(hex(self.devAddr), p.name))
					return(p.name)
		logging.debug("No pin found on interrupt. Addr: " + hex(self.devAddr) + " :(")
		return("")

	def getPinStats(self, pin):
		"""Call this method to get the most important settings of the given pin."""

		try:
			bank, pin = self.checkPinInput(pin)
			return(bank[pin].showStatus())
		except PinValueError:
			logging.debug("Stats requested for invalid pin {}:{}".format(hex(self.devAddr), pin))

	def getPinState(self, pin):
		"""Call this method to see if a pin is high or low."""

		try:
			bank, pin = self.checkPinInput(pin)
		except PinValueError:
			logging.debug("State requested for invalid pin {}:{}".format(hex(self.devAddr), pin))
		register = "GPIOB"
		if (bank == self.GPA):
			register = "GPIOA"
		bankValue = int(self.bus.read_byte_data(self.devAddr, self.regMap[register]))
		if (not (self.GPA[self.checkedPin[1]].value & bankValue) == 0):
			return(True)
		return(False)

	def addInterruptInput(self, pin, obj, trig):
		"""Add an object which has a run() method which will be called when interrupt pin is triggered."""

		if (not trig.lower() in self.trigger.keys()):
			logging.debug("Invalid trigger type.")
			return

		if (not self.enabled):
			if (self.intPin is not None):
				try:
					bank, pin = self.checkPinInput(pin)
				except PinValueError:
					return
				# Check to see if pin is set as output.
				if (bank[pin].direction):
					bank[pin].defVal = self.trigger[trig][0]
					bank[pin].intCon = self.trigger[trig][1]
					bank[pin].intEn = self.trigger[trig][2]
					self.interruptObjects[pin] = obj
				else:
					logging.debug("pin {}:{} is not set as output.".format(hex(self.devAddr), pin))

	def runInterrupt(self, *args):

		p = self.getInterruptPin()
		print("{} args: {}\t{}".format(hex(self.devAddr), args[0], p))
		if (p in self.interruptObjects):
			# check for triggertype from INTCON to see if to send state along
			state = None
			if (p[0] == "A"):
				# If pin gives interrupt on both RISE and FALL, add current state to return data.
				if (not self.GPA[int(p[1])].intCon):
					state = self.getPinState(p)
			elif (p[0] == "B"):
				if (not self.GPB[int(p[1])].intCon):
					state = self.getPinState(p)
#			try:
			if (state is None):
				self.interruptObjects[p].run()
			else:
				self.interruptObjects[p].run(state)
				print(p, " state")
#			except:
#				logging.warning("Failed to run the run() method for the object for pin {}:{}".format(hex(self.devAddr), p))
		else:
			logging.warning("Pin {}:{} has no associated object.".format(hex(self.devAddr), p))


class mcp23008(mcp230xx):

	def __init__(self, devAddr, intPin = None):
		super(mcp23008, self).__init__(devAddr, intPin)
		self.regMap = {
					# Direction
					"IODIR" : 0x00,
					# polarity. True = reflect opposite pin value.
					"IPOL":	0x01,
					# Interupt-on-change enable
					"GPINTEN" : 0x02,
					# Default compare value for inputs.
					"DEFVAL" : 0x03,
					# Interupt-on-change. False = compare to last pin value
					"INTCON" : 0x04,
					"IOCON" : 0x05,
					# GPPU, pull-up resistors for input pins. Default off, user can override.
					"GPPU" : 0x06,
					"INTF" : 0x07,
		 			# INTCAP, use to read input pin state.
					"INTCAP" : 0x08,
					"GPIO" : 0x09,
					# OLATx, use to set output pin state.
					"OLAT" : 0x0A
				}


	def engage(self):
		"""\t\tCall this method after setting the pins and setting of the chip.
		After enable, you can make no further changes and you can start using the chip."""

		if (not self.enabled):
			print("Init MCP23017 (" + hex(self.devAddr) + ")...")
			# Set device's registers and get value for last register.
			value = self.setRegisters(self.GPA)

			self.bus.write_byte_data(self.devAddr, self.regMap["IOCON"], value)

			self.enabled = True
			msg = "MCP23017 init on addres " + hex(self.devAddr) + " done!"
			if (self.intPin is not None):
				msg += "\tInt pin: " + str(self.intPin)
			print(msg)
		else:
			logging.debug("MCP23017 device on " + hex(self.devAddr) + " is already enabled. Can't change it anymore.")

	def checkPinInput(self, input):
		"""
		Returns the bank and pin number as int if the pin is valid.
		Valid pin input values: 0-7
		"""

		try:
			input = int(input)
		except ValueError:
			logging.debug("Invalid pin: " + str(input))
			raise PinValueError
		if (0 <= input <= 7):
			return(self.GPA, input)
		logging.debug("Invalid pin: " + str(input))
		raise PinValueError

	def getInterruptPin(self):
		"""Interrupt routine should be called when the interrupt pin has been set."""

		if (self.hasAinput):
			bank1 = int(self.bus.read_byte_data(self.devAddr, self.regMap["INTCAPA"]))
			for p in self.GPA:
				if (p.direction):
					if (not (p.value & bank1) == 0):
						logging.info("Interrupt triggered: " + p.name)
						return(p.name)
		logging.debug("No pin found on interrupt at addr: " + hex(self.devAddr) + " :(")
		return(None)


class mcp23017(mcp230xx):

	# intPin2
	@property
	def intPin2(self):
		return(self.__intPin2)
	@intPin2.setter
	def intPin2(self, intPin2):
		self.__intPin2 = intPin2
	# GPB
	@property
	def GPB(self):
		return(self.__GPB)
	@GPB.setter
	def GPB(self, GPB):
		self.__GPB = GPB

	def __init__(self, devAddr, intPin = None, intPin2 = None):

		super(mcp23017, self).__init__(devAddr, intPin)
		self.intPin2 = intPin2
		self.hasBinput = False		#	True if there is at least one pin in the B bank set as an input.
		if (self.intPin is not None and intPin2 is not None):
			self.setSetup("MIRROR", False)
		self.GPB = []
		# Setting the second interrupt pin on the Raspberry Pi.
		if (self.intPin2 is not None):
			import RPi.GPIO as GPIO
			GPIO.setup(self.intPin2, GPIO.IN, pull_up_down = GPIO.PUD_UP)
			GPIO.add_event_detect(self.intPin2, GPIO.FALLING, callback = self.runInterrupt)
			logging.info("Set interrupt pin 2 on {} with GPIO pin {}".format(hex(self.devAddr), self.intPin))
		# Populating banks with unset pins.
		for i in range(8):
			self.GPB.append(Pin(2 ** i, "A" + str(i)))
		self.regMap = {
					# Direction
				  "IODIRA":	0X00,		  "IODIRB":	0X01,
					# polarity. True = reflect opposite pin value.
					"IPOLA":	0X02,			"IPOLB":	0X03,
					# Interupt-on-change enable
				"GPINTENA": 0X04,		"GPINTENB": 0X05,
					# Default compare value for inputs.
				 "DEFVALA":	0X06,		 "DEFVALB":	0X07,
					# Interupt-on-change. False = compare to last pin value
				 "INTCONA":	0X08,		 "INTCONB":	0X09,
				  "IOCONA":	0X0A,		  "IOCONB":	0X0B,
					# GPPUx, pull-up resistors for input pins. Default off, user can override.
					"GPPUA":	0X0C,			"GPPUB":	0X0D,
					"INTFA":	0X0E,			"INTFB":	0X0F,
		 			# INTCAPx, use to read input pin state.
				 "INTCAPA":	0X10,		 "INTCAPB":	0X11,
					"GPIOA":	0X12,			"GPIOB":	0X13,
					# OLATx, use to set output pin state.
					"OLATA":	0X14,			"OLATB":	0X15
				}


	def engage(self):
		"""\t\tCall this method after setting the pins and setting of the chip.
		After enable, you can make no further changes and you can start using the chip."""

		if (not self.enabled):
			print("Init MCP23017 (" + hex(self.devAddr) + ")...")

			self.setRegisters(self.GPA, "A")
			value = self.setRegisters(self.GPB, "B")


			self.bus.write_byte_data(self.devAddr, self.regMap["IOCONA"], value)
			self.bus.write_byte_data(self.devAddr, self.regMap["IOCONB"], value)

			self.enabled = True
			msg = "MCP23017 init on addres " + hex(self.devAddr) + " done!"
			if (self.intPin is not None):
				msg += "\tInt pin: " + str(self.intPin)
				if(self.intPin2 is not None):
					msg += "\tInt pin 2: " + str(self.intPin2)
			print(msg)
		else:
			logging.debug("MCP23017 on " + hex(self.devAddr) + " is already enabled. Can't change it anymore.")

	def checkPinInput(self, input):
		"""
		Returns the bank and pin number as int if the pin is valid.
		Valid pin input values: "A0" - "A7", "B0" - "B7"
		"""

		bank = None
		pin = -1
		if (isinstance(input, str)):
			if (len(input) == 2):
				if (input[0].upper() == "A"):
					bank = self.GPA
				elif (input[0].upper() == "B"):
					bank = self.GPB
				else:
					logging.debug("Invalid pin: " + str(input))
					raise PinValueError
				try:
					pin = int(input[1])
				except ValueError:
					logging.debug("Invalid pin: " + str(input))
					raise PinValueError
				if (0 <= pin <= 7):
					return(bank, pin)
		logging.debug("Invalid pin: " + str(input))
		raise PinValueError

	def getInterruptPin(self):
		"""Interrupt routine should be called when an interrupt pin has been set."""

		if (self.hasAinput):
			bank1 = int(self.bus.read_byte_data(self.devAddr, self.regMap["INTCAPA"]))
			for p in self.GPA:
				if (p.direction):
					if (not (p.value & bank1) == 0):
						logging.info("Interrupt triggered: " + p.name)
						return(p.name)

		if (self.hasBinput):
			bank2 = int(self.bus.read_byte_data(self.devAddr, self.regMap["INTCAPB"]))
			for p in self.GPB:
				if (p.direction):
					if (not (p.value & bank2) == 0):
						logging.info("Interrupt triggered: " + p.name)
						return(p.name)
			logging.debug("No pin found on interrupt at addr: " + hex(self.devAddr) + " :(")
		return(None)


class PinValueError(Exception):
	pass