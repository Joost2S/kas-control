#!/usr/bin/python3

# Author: J. Saarloos
# v0.6.02	21-05-2018

import logging
import time

from globstuff import globstuff as gs


class lcdController(object):
	"""
	This object can be used to display formatted data on a 16*02 or 20*04 LCD.
	"""

	__LCD = None
	cols = 0
	rows = 0
	names = []				# [[sensorname, displayname],...]
	passStart = False		# Used to keep the welcome message on the display for a while.
	slotsAvailable = 0
	slotsPerRow = 0
	slotsUsed = 0
	__scrollIndex = 0
	__startMSGdisp = gs.boottime
	__displayMSGfor = 15
	__template = []

	def __init__(self, lcd):
		self.__LCD = lcd
		self.__LCD.enable_display(True)
		self.cols = self.__LCD._cols
		self.rows = self.__LCD._lines
		if (self.rows == 2 and self.cols == 16):
			self.slotsAvailable = 3
			self.slotsPerRow = 3
		elif (self.rows == 4 and self.cols == 20):
			self.slotsAvailable = 8
			self.slotsPerRow = 4
		gs.ee.on("hwMonitorDataUpdate", self.updateScreen)

	def __setTemplate(self):
		"""Sets the template to display sensor data on the LCD."""

		template = []
		self.slotsUsed = self.slotsAvailable
		if (len(self.names) < self.slotsAvailable):
			self.slotsUsed = len(self.names)
		y = int(self.slotsUsed / self.slotsPerRow)
		for i in range(y):
			template.extend(self.__addLines(self.slotsPerRow))
		# If the last line isn't filled completely, create a shorter template
		if (self.slotsUsed % self.slotsPerRow != 0):
			template.extend(self.__addLines(self.slotsUsed % self.slotsPerRow))
		# If there is an even length of slots, place a space in the middle for symmetry.
		if (not self.slotsPerRow % 2):
			for i, line in enumerate(template):
				if (len(line) > 8):
					template[i] = line[:int(len(line)/2)] + " " + line[int(len(line)/2):]
		self.__template = template

	def __addLines(self, slots):
		"""Returns 2 formatted rows with placeholders for format() of requested length."""

		template = []
		template.append("")
		template.append("")
		for i in range(slots):
			template[0] += "{} "
			template[1] += "{} "
		template[0] += "\n"
		template[1] += "\n"
		return(template)

	def updateScreen(self):

		if (len(self.names) == 0):
			return
		if (not self.passStart):
			if (time.time() - self.__startMSGdisp > self.__displayMSGfor):
				self.__LCD.clear()
				self.passStart = True
			else:
				return
		n = []
		v = []
		names = []
		index = self.slotsUsed
		values = gs.control.requestData(caller = "display")
		# Select names to be displayed if not all names are displayed at once.
		if (len(self.names) > self.slotsUsed):
			# If there are 2 lines of values.
			if (self.slotsUsed > self.slotsPerRow):
				odd = len(self.names) % 2
				breakpoint = int(len(self.names) / 2) + odd
				if (self.__scrollIndex + self.slotsPerRow > breakpoint):
					self.__scrollIndex = 0
				l1 = self.names[:breakpoint]
				names = l1[self.__scrollIndex:self.__scrollIndex + self.slotsPerRow]
				l2 = self.names[breakpoint:]
				if (self.__scrollIndex + self.slotsPerRow > len(l2)):
					lst = l2[self.__scrollIndex:len(self.names) - breakpoint]
					for i in range(self.slotsPerRow - len(lst)):
						lst.append(["", ""])
					names.extend(lst)
				else:
					names.extend(l2[self.__scrollIndex:self.__scrollIndex + self.slotsPerRow])
			else:
				if (self.__scrollIndex + self.slotsPerRow > len(self.names)):
					self.__scrollIndex = 0
				names = self.names[self.__scrollIndex:self.__scrollIndex + self.slotsAvailable]
			self.__scrollIndex += 1
		# Set index to end of line 1 as a breakpoint.
		if (self.slotsUsed > self.slotsPerRow):
			index = self.slotsPerRow
		for i in range(self.slotsUsed):
			try:
				n.append(gs.getTabs(names[i]["displayName"], 1, 4))
				v.append(gs.getTabs(values[names[i]["sensorName"]], 1, 4))
			except KeyError:
				n.append(gs.getTabs("", 1, 4))
				v.append(gs.getTabs("", 1, 4))
		i = n[:index]
		text = self.__template[0].format(*i)
		i = v[:index]
		text += self.__template[1].format(*i)
		if (self.slotsUsed > self.slotsPerRow):
			i = v[index:]
			text += self.__template[3].format(*i)
			i = n[index:]
			text += self.__template[2].format(*i)
		if (self.passStart):
			self.__LCD.home()
			self.__LCD.message(text[:-2])

	def setNames(self, names):

		self.names = []
		for name in names:
			if (name["sensorName"] in gs.control.getSensors().keys()):
				self.names.append(name)
		self.__setTemplate()
		self.__scrollIndex = 0

	def message(self, msg, t = None):

		if (t is not None):
			self.passStart = False
			self.__displayMSGfor = t
			self.__startMSGdisp = time.time()
			self.__LCD.clear()
		self.__LCD.message(msg)

	def toggleBacklight(self):
		""""""

		self.__LCD.set_backlight(not bool(self.__LCD._backlight))
		return(bool(self.__LCD._backlight))

	def disable(self):

		self.__LCD.set_backlight(False)
		self.__LCD.enable_display(False)