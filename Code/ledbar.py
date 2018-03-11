#!/usr/bin/python3
 
# Author: J. Saarloos
# v0.6.01	10-03-2018

import logging

from globstuff import globstuff as gs

class LEDbar(object):
	"""
	Object to control an LEDbar.
	Option to set some of the LEDs as indicators using binary notation.
	Can be used if user wants to display more than one value on 1 bar.
	"""
	
	# iPins			List with indicator pin numbers
	@property
	def iPins(self):
		return(self.__iPins)
	@iPins.setter
	def iPins(self, iPins):
		self.__iPins = iPins
	# lPins			List with LED pin numbers
	@property
	def lPins(self):
		return(self.__lPins)
	@lPins.setter
	def lPins(self, lPins):
		self.__lPins = lPins
	# mode			Select 'bar', 'dot' or 'off' mode.
	@property
	def mode(self):
		return(self.__mode)
	@mode.setter
	def mode(self, mode):
		self.__mode = mode
	# indicator		Tells user which sensor is displayed from selected range
	@property
	def indicator(self):
		return(self.__indicator)
	@indicator.setter
	def indicator(self, indicator):
		self.__indicator = indicator
	# curLEDs		Current amount of LEDs turned on
	@property
	def curLEDs(self):
		return(self.__curLEDs)
	@curLEDs.setter
	def curLEDs(self, curLEDs):
		self.__curLEDs = curLEDs
	# curIndex		[bool(state), bool(state),...] current state of each iPin
	@property
	def curIndex(self):
		return(self.__curIndex)
	@curIndex.setter
	def curIndex(self, curIndex):
		self.__curIndex = curIndex
	# displayed		[bool(displayed), bool(displayed),...] for names
	@property
	def displayed(self):
		return(self.__displayed)
	@displayed.setter
	def displayed(self, displayed):
		self.__displayed = displayed
	# names			[sensorname, sensorname,...]
	@property
	def names(self):
		return(self.__names)
	@names.setter
	def names(self, names):
		self.__names = names
	# bounds			[[low, high], [low, high],...]
	@property
	def bounds(self):
		return(self.__bounds)
	@bounds.setter
	def bounds(self, bounds):
		self.__bounds = bounds

	def __init__(self, pins = [], icount = 0, fromLorR = "r", mode = "bar"):
		
		if (len(pins) < 1):
			raise Exception("No pins are defined for the LEDbar.")
		if (not (len(pins) > icount)):
			raise Exception("No pins are defined for the LEDbar, too many indicator LEDs.")
		self.iPins = []
		self.lPins = []
		self.mode = mode
		self.indicator = 0
		self.curLEDs = 0
		self.curIndex = []
		self.displayed = []
		self.names = []
		self.bounds = []
		if (fromLorR == "r"):
			if (icount > 0):
				lp = []
				for pin in reversed(pins[:0 - icount]):
					lp.append(pin)
				self.lPins = lp
				self.iPins = pins[0 - icount:]
				print(self.lPins)
				print(self.iPins)
			else:
				lp = []
				for pin in reversed(pins):
					lp.append(pin)
				self.lPins = lp
		elif (fromLorR == "l"):
			if (icount > 0):
				self.lPins = pins[icount:]
				self.iPins = pins[:icount]
			else:
				self.lPins = pins
		else:
			raise Exception("Invalid setting for fromLorR. Must be 'l' or 'r'.")
		if (icount > 0):
			for i in range(icount):
				self.curIndex.append(False)

		for pin in pins:
			gs.getPinDev(pin).setPin(gs.getPinNr(pin), False)

		
	def setNames(self, names):
		
		# names = [[name, lower, upper], [name, lower, upper],..]
		if (len(names) > 0):
			if (len(names) > (2 ** len(self.iPins))):
				names = names[:2 ** len(self.iPins)]
				logging.warning("Not enough indicator LEDs are defined. Not all sensors will be displayed.")
			self.names = []
			for name in names:
				self.names.append(name[0])
				self.displayed.append(False)
				self.bounds.append(name[1:])

	def updateBounds(self, name, low, high):
		"""Set bound levels based on the channel's trigger values."""
		
		try:
			i = self.names.index(name)
			self.bounds[i] = [0.85 * low, 1.15 * high]
		except ValueError:
			return

	def getConfig(self):
		"""[[name, displayed, low, high],...]"""

		data = []
		for i, name in enumerate(self.names):
			data.extend([name, self.displayed[i], self.bounds[0], self.bounds[1]])
		return(data)

	def updateBar(self, a = 0):
		
		if (self.mode == "off"):
			return
		if (a >= len(self.names)):
			# If all values are unavailable, turn off all lPins and end.
			self.__changeLEDs(self.lPins, False)
			return
		lOn = []
		lOff = []
		newLEDs = 0
		# Get index of currently displayed value and update to new index.
		try:
			i = self.displayed.index(True)
			self.displayed[i] = False
		except ValueError:
			i = -1
		if (i >= len(self.displayed) - 1):
			i = 0
		else:
			i += 1
#		print(self.displayed)
		self.displayed[i] = True
		values = gs.control.requestData(caller = "display")
		# Skip to next value if current value is disabled or sensor data is not available.
		if (self.bounds[i][0] == None or isinstance(values[self.names[i]], str)):
			self.updateBar(values, a + 1)
		# Check how many LEDs should be on with new value:
		if (values[self.names[i]] < self.bounds[i][0]):
			newLEDs = 0
		elif (values[self.names[i]] >= self.bounds[i][1]):
			newLEDs = len(self.lPins)
		else:
			step = (self.bounds[i][1] - self.bounds[i][0]) / len(self.lPins)
			newLEDs = int((values[self.names[i]] - self.bounds[i][0]) / step)
		# Get lPin changes for dot mode:
		if (newLEDs != self.curLEDs and self.mode == "dot"):
			lOff.append(self.lPins[self.curLEDs - 1])
			lOn.append(self.lPins[newLEDs - 1])
		elif (newLEDs < self.curLEDs):
			# Get lPins to turn off.
			lst = self.lPins[newLEDs : self.curLEDs]
			lOff.extend(lst)
		elif (newLEDs == self.curLEDs):
			# No lPins to change.
			pass
		elif (newLEDs > self.curLEDs):
			# Get lPins to turn on.
			lst = self.lPins[self.curLEDs : newLEDs]
			lOn.extend(lst)
		if (len(self.iPins) > 0):
			iOn, iOff = self.__setIpins(i)
			lOn.extend(iOn)
			lOff.extend(iOff)
		self.curLEDs = newLEDs
		if (len(lOff) > 0):
			self.__changeLEDs(lOff, False)
		if (len(lOn) > 0):
			self.__changeLEDs(lOn, True)

	def __setIpins(self, index):
		"""Returns the pins that need to be turned on and off in the indicator section."""

		on = []
		off = []
		current = 0
		for i, pin in enumerate(self.curIndex):
			if (pin):
				current += 2 ** i
		changed = index ^ current
		for i, pin in enumerate(reversed(self.iPins)):
			# Check if pins is changed:
			if (2**i & changed):
				# Check if pin needs to be on:
				if (2**i & current):
					off.append(pin)
					self.curIndex[i] = False
				# Or if pin needs to be off:
				else:
					on.append(pin)
					self.curIndex[i] = True
		return(on, off)

	def __changeLEDs(self, pins, state):
		"""Turns all given LEDs on or off."""

		changePins = {}
		for pin in pins:
			if (not pin[0] in changePins.keys()):
				changePins[pin[0]] = []
			changePins[pin[0]].append(gs.getPinNr(pin))
		for dev, pinlist in changePins.items():
			gs.getPinDev(dev).output(pinlist, state)
	
	def setMode(self, mode):
		"""Change between bar mode and dot mode."""

		if (mode in ["bar", "dot", "off"]):
			if (self.mode != mode):
				self.__mode = mode
				if (mode == "bar"):
					self.__changeLEDs(self.lPins[:self.curLEDs - 2], True)
				elif (mode == "dot"):
					self.__changeLEDs(self.lPins[:self.curLEDs - 2], False)
				elif (mode == "off"):
					self.__changeLEDs(self.lPins, False)
					self.__changeLEDs(self.iPins, False)