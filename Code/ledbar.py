#!/usr/bin/python3
 
# Author: J. Saarloos
# v0.5.05	03-03-2018

import logging

from globstuff import globstuff as gs

class LEDbar(object):
	"""
	Object to control an LEDbar.
	Option to set some of the LEDs as indicators using binary notation.
	Can be used if user wants to display more than one value on 1 bar.
	"""
	
	__iPins = []			# List with indicator pin numbers
	__lPins = []			# List with LED pin numbers
	__mode = "bar"			# Select from 'bar' or 'dot' mode.
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
				self.__bounds.append([0.95 * name[1], 1.05 * name[2]])

	def updateBounds(self, name, low, high):
		"""Set bound levels based on the channel's trigger values."""
		
		try:
			i = self.__names.index(name)
			self.__bounds[i] = [0.85 * low, 1.15 * high]
		except ValueError:
			pass

	def updateBar(self, values, a = 0):
		
		if (self.__mode == "off"):
			return
		if (a >= len(self.__bounds)):
			# If all values are unavailable, turn off all lPins and end.
			self.__changeLEDs(self.__lPins, False)
			return
		if (len(values) == len(self.__displayed)):
			lOn = []
			lOff = []
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
			# Get lPin changes for dot mode:
			if (newLEDs != self.__curLEDs and self.__mode == "dot"):
				lOff.append(self.__curLEDs - 1)
				lOn.append(newLEDs - 1)
			elif (newLEDs < self.__curLEDs):
				# Get lPins to turn off.
				lOff.extend(self.__lPins[newLEDs - 1 : self.__curLEDs - 1])
			elif (newLEDs == self.__curLEDs):
				# No lPins to change.
				pass
			elif (newLEDs > self.__curLEDs):
				# Get lPins to turn on.
				lOn.extend(self.__lPins[self.__curLEDs - 1 : newLEDs - 1])
			iOn, iOff = self.__setIpins(i)
			lOn.extend(iOn)
			lOff.extend(iOff)
			self.__curLEDs = newLEDs
			if (len(lOff) > 0):
				self.__changeLEDs(lOff, False)
			if (len(lOn) > 0):
				self.__changeLEDs(lOn, True)
		else:
			logging.warning("List of invalid length passed to LEDbar.")

	def __setIpins(self, index):
		"""Returns the pins that need to be turned on and off in the indicator section."""

		on = []
		off = []
		current = 0
		for i, pin in enumerate(self.__iPins):
			if (pin):
				current += 2 ** i
		changed = index ^ current
		for i, pin in enumerate(self.__iPins):
			# Check if pins is changed:
			if (2**i & changed):
				# Check if pin needs to be on:
				if (2**i & current):
					off.append(pin)
				# Or if pin needs to be off:
				else:
					on.append(pin)
		return(on, off)

	def __changeLEDs(self, pins, state):
		"""Turns all given LEDs on or off."""

		changePins = {}
		for pin in pins:
			if (not pin[0] in changePins):
				changePins[0] = []
			changePins[pin[0]].append(gs.getPinNr(pin))
		for dev, pinlist in changePins.items():
			gs.getPinDev(dev).output(pinlist, state)
	
	def setMode(self, mode):
		"""Change between bar mode and dot mode."""

		if (mode in ["bar", "dot", "off"]):
			if (self.__mode != mode):
				self.__mode = mode
				if (mode == "bar"):
					self.__changeLEDs(self.__lPins[:self.__curLEDs - 2], True)
				elif (mode == "dot"):
					self.__changeLEDs(self.__lPins[:self.__curLEDs - 2], False)
				elif (mode == "off"):
					self.__changeLEDs(self.__lPins, False)
					self.__changeLEDs(self.__iPins, False)