#!/usr/bin/python3
 
# Author: J. Saarloos
# v0.5.02	11-02-2018

import logging

from globstuff import globstuff as gs

class LEDbar(object):
	
	__iPins = []			# List with indicator pin numbers
	__lPins = []			# List with LED pin numbers
	__mode = 0				# Select from bar or dot mode. 0, 1
	__indicator = 0		# Tells user which sensor is displayed from selected range
	__ledAmount = 0		# Amount of leds in bar
	__curVal = 0			# Current value displayed on LEDbar
	__names = {}			# {name : bool(displayed), name : bool(displayed),...}

	def __init__(self, icount = 0, pins = [], fromLorR = "r"):
		
		if (len(pins) < 1):
			raise Exception("No pins are defined for the LEDbar.")
		if (not (len(pins) > icount)):
			raise Exception("No pins are defined for the LEDbar, too many indicator LEDs.")
		if (fromLorR == "r"):
			pins = reversed(pins)
		elif (not fromLorR == "l"):
			raise Exception("Invalid setting for fromLorR. Must be 'l' or 'r'.")
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
			for n in names:
				self.__names[n] = moi

	# Used to calculate the correct amount of LEDs to indicate levels,
	# based on the displayrange and amount of LEDs.
	def dispLEDs(self, value):
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
			self.mcp0.output((self.lsta[n],), True)
		elif ((n - len(self.lsta)) < len(self.lstb)):
			self.mcp1.output((self.lstb[n - len(self.lsta)],), True)
			
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
			self.mcp0.output((self.lsta[n],), False)
		elif ((n - len(self.lsta)) < len(self.lstb)):
			self.mcp1.output((self.lstb[n - len(self.lsta)],), False)

	def updateBar(self, names, values):

		# Check how many LEDs should be on with new value:
		curVal = doMathTo(value)
		if (curVal < self.__curVal):
			# get difference.
			# turn off selected LEDs.
			pass
		elif (curVal == self.__curVal):
			# Nothing to do really...
			pass
		elif (curVal > self.__curVal):
			pass
		self.__curVal = curVal