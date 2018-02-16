#!/usr/bin/python3
 
# Author: J. Saarloos
# v0.5.03	15-02-2018

import logging

from globstuff import globstuff as gs

class LEDbar(object):
	
	__iPins = []			# List with indicator pin numbers
	__lPins = []			# List with LED pin numbers
	__mode = 0				# Select from bar or dot mode. 0, 1
	__indicator = 0		# Tells user which sensor is displayed from selected range
	__ledAmount = 0		# Amount of leds in bar
	__curLEDs = 0			# Current amount of LEDs turned on
	__curIndex = []		# [bool(state), bool(state),...] for iPins
	__displayed = []		# [bool(displayed), bool(displayed),...] for lPins
	__names = []			# [sensorname, sensorname,...]
	__bounds = []			# [[low, high], [low, high],...]

	def __init__(self, icount = 0, pins = [], fromLorR = "r"):
		
		if (len(pins) < 1):
			raise Exception("No pins are defined for the LEDbar.")
		if (not (len(pins) > icount)):
			raise Exception("No pins are defined for the LEDbar, too many indicator LEDs.")
		if (fromLorR == "r"):
			pins = reversed(pins)
		elif (not fromLorR == "l"):
			raise Exception("Invalid setting for fromLorR. Must be 'l' or 'r'.")
		if (fromLorR == "r"):# should probably be equal 'l'
			self.__iPins = reversed(pins[:icount])
		else:
			self.__iPins = pins[:icount]
		self.__lPins = pins[icount:]

		for pin in pins:
			gs.getPinDev(pin).setPin(gs.getPinNr(pin), False)

		
	def setIndicators(self, names):
		
		# names = [[name, lower, upper], [name, lower, upper],..]
		if (len(names) > 0):
			if (len(names) > (2 ** len(self.__iPins))):
				names = names[:2 ** len(self.__iPins)]
				logging.warning("Not enough indicator LEDs are defined. Not all sensors will be displayed.")
			for name in names:
				self.__names.append(name[0])
				self.__displayed.append(False)
				self.__bounds.append([0.85 * name[1], 1.15 * name[2]])

	def updateBounds(self, name, low, high):
		"""Set bound levels based on the channel's trigger values."""
		
		try:
			i = self.__names.index(name)
			self.__bounds[i] = [0.85 * low, 1.15 * high]
		except ValueError:
			pass

	def updateBar(self, values, a = 0):

		if (a > len(self.__bounds)):
			return
		if (len(values) == len(self.__displayed)):
			newLEDs = 0
			# Get index of currently displayed value and update to new index.
			try:
				i = self.__displayed.index(True)
				self.__displayed[i] = False
			except ValueError:
				i = -1
			if (i == len(values) - 1):
				i = 0
			else:
				i += 1
			self.__displayed[i] = True
			# Skip to next value if current value is disabled or sensor data is not available.
			if (self.__bounds[i][0] == None or isinstance(values[i], str)):
				self.updateBar(values, a + 1)
			# Check how many LEDs should be on with new value:
			if (values[i] < self.__bounds[i][0]):
				newLEDs = 0
			elif (values[i] >= self.__bounds[i][1]):
				newLEDs = len(self.__lPins)
			else:
				step = (self.__bounds[i][1] - self.__bounds[i][0]) / len(self.__bounds)
				low = self.__bounds[i][0] - step
				newLEDs = int((values[i] - low) / step)
			if (newLEDs < self.__curLEDs):
				# get difference.
				# turn off selected LEDs.
				pass
			elif (newLEDs == self.__curLEDs):
				# Nothing to do really...
				pass
			elif (newLEDs > self.__curLEDs):
				# get difference.
				# turn on selected LEDs.
				pass
			self.__iPins
			self.__curLEDs = newLEDs
		else:
			logging.warning("List of invalid length passed to LEDbar.")

	def setMode(self, mode):

		if (mode in ["bar", "dot"]):
			self.__mode = mode

	def __setIpins(self, index):

		current = 0
		for i, pin in enumerate(self.__iPins):
			if (pin):
				current += 2 ** i
		changed = index ^ current
		for i, pin in enumerate(self.__iPins):
			bool(2**i) != bool(b)

	def dispLEDs(self, value):
		"""Used to calculate the correct amount of LEDs to indicate levels,
		based on the displayrange and amount of LEDs."""

		perStep = (self.rangeUpper - self.rangeLower) / (len(self.lsta) + len(self.lstb) - 1)
		amount = value - self.rangeLower
		if (amount <= 0):
			return
		elif (value < self.rangeUpper):
			self.upto(int(amount / perStep))# + 1)
		else:
			self.allOn()
				
	def returnLists(self):
		lst = []
		for l in self.lsta:
			lst.append("0" + l)
		for l in self.lstb:
			lst.append("1" + l)
		return(lst)

	def allOn(self):
		self.mcp0.output(self.lsta, True)
		self.mcp1.output(self.lstb, True)

	def oneOn(self, n):
		self.allOff()
		if (n < len(self.lsta)):
			self.mcp0.output((self.lsta[n]), True)
		elif ((n - len(self.lsta)) < len(self.lstb)):
			self.mcp1.output((self.lstb[n - len(self.lsta)]), True)
			
	def upto(self, n):
		self.allOff()
		if (n > (len(self.lsta) + len(self.lstb))):
			self.allOn()
		elif (n > len(self.lsta)):
			self.mcp0.output(self.lsta, True)
			l = []
			for i in range(n - len(self.lsta)):
				l.append(self.lstb[i])
			self.mcp1.output(l, True)
		elif (n > 0):
			l = []
			for i in range(n):
				l.append(self.lsta[i])
			self.mcp0.output(l, True)
			
	def allOff(self):
		self.mcp0.output(self.lsta, False)
		self.mcp1.output(self.lstb, False)

	def oneOff(self, n):
		if (n < len(self.lsta)):
			self.mcp0.output(self.lsta[n], False)
		elif ((n - len(self.lsta)) < len(self.lstb)):
			self.mcp1.output(self.lstb[n - len(self.lsta)], False)