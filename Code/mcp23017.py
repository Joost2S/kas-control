#!/usr/bin/python3
 
# Author: J. Saarloos
# v0.9.3	02-08-2017

"""
This is a python driver for an i2c MCP23017. python-smbus must be installed for this driver to work.
You have to set up the pins you want to use and device settings first. Then run engage().
After this you can use chip.
Driver only accepts lists/tuples as input, also for single pin. Should be resolved now.
"""


from collections import Iterable
import logging
import smbus


class pin(object):
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
	# state, to keep track of wether in output is on or off.
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

	def setDir(self, direction):
		"""Set pin as input (True) or output (False)."""

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

	def setState(self, state):
		if (not self.direction):
			self.state = state


	def showStatus(self):
		return("name: " + str(self.name) + "\ndir: " + str(self.direction) + "\npol: " + str(self.polarity) + "\nintEn: " + str(self.intEn)
			+ "\nintCon: " + str(self.intCon) + "\ndefval: " + str(self.defVal))

class mcp23017(object):
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
	# intPin2
	@property
	def intPin2(self):
		return(self.__intPin2)
	@intPin2.setter
	def intPin2(self, intPin2):
		self.__intPin2 = intPin2
	# GPA
	@property
	def GPA(self):
		return(self.__GPA)
	@GPA.setter
	def GPA(self, GPA):
		self.__GPA = GPA
	# GPB
	@property
	def GPB(self):
		return(self.__GPB)
	@GPB.setter
	def GPB(self, GPB):
		self.__GPB = GPB

	regMap = {
		  "IODIRA":	0X00,		  "IODIRB":	0X01,
			"IPOLA":	0X02,			"IPOLB":	0X03,
		"GPINTENA": 0X04,		"GPINTENB": 0X05,
		 "DEFVALA":	0X06,		 "DEFVALB":	0X07,
		 "INTCONA":	0X08,		 "INTCONB":	0X09,
		  "IOCONA":	0X0A,		  "IOCONB":	0X0B,
			# GPPUx, pull-up resistors for input pins. Default on, user can override.
			"GPPUA":	0X0C,			"GPPUB":	0X0D,
			"INTFA":	0X0E,			"INTFB":	0X0F,
		 	# INTCAPx, use to read input pin state.
		 "INTCAPA":	0X10,		 "INTCAPB":	0X11,
			"GPIOA":	0X12,			"GPIOB":	0X13,
			# OLATx, use to set output pin state.
			"OLATA":	0X14,			"OLATB":	0X15
	}

	IOCON = {
		"INTPOL": False,
			"ODR": False,
		  "HAEN": True,
		"DISSLW": True,
		 "SEQOP": True,
		"MIRROR": True,
		  "BANK": False
	}

	def __init__(self, devAddr, intPin1 = None, intPin2 = None):
		self.devAddr = devAddr
		self.bus = smbus.SMBus(1)	# 0 = /dev/i2c-0 (port I2C0), 1 = /dev/i2c-1 (port I2C1)
		self.intPin = intPin1
		self.intPin2 = intPin2
		if (intPin1 is not None and intPin2 is not None):
			self.setSetup("MIRROR", False)
		self.enabled = False
		self.GPA = []
		self.GPB = []
		for i in range(8):
			self.GPA.append(pin(2 ** i, str("A" + str(i))))
			self.GPB.append(pin(2 ** i, str("B" + str(i))))

	def engage(self):
		"""\t\tCall this method after setting the pins and setting of the chip.
		After enable, you can make no further changes and you can start using the chip."""

		if (not self.enabled):
			print("Init MCP23017 (" + hex(self.devAddr) + ")...")
		
			# General configuration
			s = 2
			value = 0x00
			for setting in self.IOCON:
				if (self.IOCON[setting]):
					value += s
				s *= 2
			self.bus.write_byte_data(self.devAddr, self.regMap["IOCONA"], value)
			self.bus.write_byte_data(self.devAddr, self.regMap["IOCONB"], value)
			
			# GPIO DIRECTION input/output setup
			ioDirA = 0x00
			for pin in self.GPA:
				if (pin.direction):
					ioDirA += pin.value
			self.bus.write_byte_data(self.devAddr, self.regMap["IODIRA"], ioDirA)
			ioDirB = 0x00
			for pin in self.GPB:
				if (pin.direction):
					ioDirB += pin.value
			self.bus.write_byte_data(self.devAddr, self.regMap["IODIRB"], ioDirB)

			# GPI POLARITY setup
			IPOLA = 0x00
			for pin in self.GPA:
				if (pin.polarity):
					IPOLA += pin.value
			self.bus.write_byte_data(self.devAddr, self.regMap["IPOLA"], IPOLA)
			IPOLB = 0x00
			for pin in self.GPB:
				if (pin.polarity):
					IPOLB += pin.value
			self.bus.write_byte_data(self.devAddr, self.regMap["IPOLB"], IPOLB)

			# GPINTEN interrupt enable setup
			intEnA = 0x00
			for pin in self.GPA:
				if (pin.intEn):
					intEnA += pin.value
			self.bus.write_byte_data(self.devAddr, self.regMap["GPINTENA"], intEnA)
			intEnB = 0x00
			for pin in self.GPB:
				if (pin.intEn):
					intEnB += pin.value
			self.bus.write_byte_data(self.devAddr, self.regMap["GPINTENB"], intEnB)
		
			# Default compare value for interrupt-on-change, compare to high or low.
			defValA = 0x00
			for pin in self.GPA:
				if (pin.defVal):
					defValA += pin.value
			self.bus.write_byte_data(self.devAddr, self.regMap["DEFVALA"], defValA)
			defValB = 0x00
			for pin in self.GPB:
				if (pin.defVal):
					defValB += pin.value
			self.bus.write_byte_data(self.devAddr, self.regMap["DEFVALB"], defValB)
		
			# Interrupt compare register, compare to DEFVAL or last pinstate.
			intConA = 0x00
			for pin in self.GPA:
				if (pin.intCon):
					intConA += pin.value
			self.bus.write_byte_data(self.devAddr, self.regMap["INTCONA"], intConA)
			intConB = 0x00
			for pin in self.GPB:
				if (pin.intCon):
					intConB += pin.value
			self.bus.write_byte_data(self.devAddr, self.regMap["INTCONB"], intConB)

			# GPI PULLUP resistor setup
			GPPUA = 0x00
			for pin in self.GPA:
				if (pin.pullUp):
					GPPUA += pin.value
			self.bus.write_byte_data(self.devAddr, self.regMap["GPPUA"], GPPUA)
			GPPUB = 0x00
			for pin in self.GPB:
				if (pin.pullUp):
					GPPUB += pin.value
			self.bus.write_byte_data(self.devAddr, self.regMap["GPPUB"], GPPUB)

			self.enabled = True
			msg = "MCP23017 init on addres " + hex(self.devAddr) + " done!"
			if (self.intPin is not None):
				msg += "\nInt pin: " + str(self.intPin)
				if(self.intPin2 is not None):
					msg += "\nInt pin 2: " + str(self.intPin2)
			print(msg)
		else:
			logging.debug("MCP23017 on " + hex(self.devAddr) + " is already enabled. Can't change it anymore.")

	
	def setPin(self, pin, direction):
		"""Call this method to setup a pin as input (direction = True) or output (direction = False)."""

		if (not self.enabled):
			checkedPin = self.checkPinInput(pin)
			if (checkedPin is not False):
				if (checkedPin[0] == "A"):
					self.GPA[checkedPin[1]].setDir(direction)
				elif (checkedPin[0] == "B"):
					self.GPB[checkedPin[1]].setDir(direction)
		else:
			logging.debug("MCP23017 on " + hex(self.devAddr) + " is already enabled. Can't change pin " + str(pin) + " anymore.")

	def setSetup(self, reg, val):
		"""Call this method to change a setting in IOCON. See datasheet for details."""

		self.IOCON[reg] = val

	def output(self, pins, state):
		"""Call this method to change one or more output pins to low (state = False) or high (state = True)."""

		if (self.enabled):
			hasA = False
			hasB = False
			if (not self.__typeCheck(pins)):
				pins = (pins, )
			for p in pins:
				checkedPin = self.checkPinInput(p)
				if (checkedPin is not False):
					if (checkedPin[0] == "A"):
						self.GPA[checkedPin[1]].setState(state)
						hasA = True
					elif (checkedPin[0] == "B"):
						self.GPB[checkedPin[1]].setState(state)
						hasB = True
			if (hasA):
				OLATa = 0x00
				for p in self.GPA:
					if (p.state):
						OLATa += p.value
				self.bus.write_byte_data(self.devAddr, self.regMap["OLATA"], OLATa)
			if (hasB):
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


	def interrupt_routine(self):
		"""Interrupt routine should be called when one interrupt pin has been set."""

		bank1 = int(self.bus.read_byte_data(self.devAddr, self.regMap["INTCAPA"]))
		bank2 = int(self.bus.read_byte_data(self.devAddr, self.regMap["INTCAPB"]))
		for p in self.GPA:
			if (p.direction):
				if (not (p.value & bank1) == 0):
					logging.debug("Interrupt triggered: " + p.name)
					return(p.name)
		for p in self.GPB:
			if (p.direction):
				if (not (p.value & bank2) == 0):
					logging.debug("Interrupt triggered: " + p.name)
					return(p.name)
		logging.debug("No pin found on interrupt addr: " + hex(self.devAddr) + " :(")
		return("")

	def interrupt_routine_seperate(self, intPin):
		"""This method should be called when 2 iterrupt pins are set."""

		bank = 0
		gp
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
					logging.debug("Interrupt triggered:" + p.name)
					return(p.name)
		logging.debug("No pin found on interrupt. Addr: " + hex(self.devAddr) + " :(")
		return("")
	
	def getPinStats(self, pin):
		"""Call this method to get the most important settings of the given pin."""

		checkedPin = self.checkPinInput(pin)
		if (checkedPin is not False):
			if (checkedPin[0] == "A"):
				return(self.GPA[checkedPin[1]].showStatus())
			elif (checkedPin[0] == "B"):
				return(self.GPB[checkedPin[1]].showStatus())
		
	def getPinState(self, pin):
		"""Call this method to see if a pin is high or low."""

		bank = 0
		checkedPin = self.checkPinInput(pin)
		if (checkedPin is not False):
			if (checkedPin[0] == "A"):
				bank = int(self.bus.read_byte_data(self.devAddr, self.regMap["GPIOA"]))
				if (not (self.GPA[checkedPin[1]].value & bank) == 0):
					return(True)
			elif (checkedPin[0] == "B"):
				bank = int(self.bus.read_byte_data(self.devAddr, self.regMap["GPIOB"]))
				if (not (self.GPB[checkedPin[1]].value & bank) == 0):
					return(True)
			else:
				return(False)

	def checkPinInput(self, input):
		"""This method makes sure the entered pin name is valid."""

		output = []
		try:
			port = str(input[0])
			nr = int(input[1])
			if (nr < 0 or nr > 7):
				logging.debug("Not a valid pin number. " + str(input))
				return(False)
		except ValueError:
			logging.debug("Not a valid pin name. " + str(input))
			return(False)
		if (port == "A" or port == "a"):
			output.append("A")
		elif (port == "B" or port == "b"):
			output.append("B")
		else:
			logging.debug("Not a valid pin name. " + str(input))
			return(False)
		output.append(nr)
		return(output)