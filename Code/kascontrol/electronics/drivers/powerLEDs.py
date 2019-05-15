#!/usr/bin/python3

# Author: J. Saarloos
# v0.1.02	20-05-2018


from Code.kascontrol.globstuff import globstuff as gs


class LEDchannel(object):

	pin = ""
	power = 0
	mode = ""
	enabled = False
	on = False

	def __init__(self, pin):
		self.pin = pin
		gs.getPinDev(pin).setPin(gs.getPinNr(pin), False)

	def set(self, mode, power):

		if (not self.on):
			self.mode = mode
			self.power = power
			self.enabled = True

	def unset(self):

		if (self.on):
			self.turnOff()
		self.mode = ""
		self.power = 0
		self.enabled = False

	def turnOn(self):

		if (self.enabled):
			self.on = True
			gs.getPinDev(self.pin).output(gs.getPinNr(self.pin), True)

	def turnOff(self):

		self.on = False
		gs.getPinDev(self.pin).output(gs.getPinNr(self.pin), False)


class PowerLEDcontroller(object):

	__channels = []
	__modes = {"1ww" : 350, "3ww" : 700, "3ir" : 500}

	def __init__(self):
		for pin in gs.powerLEDpins:
			self.__channels.append(LEDchannel(pin))


	def toggle(self, channel):

		if (0 < channel <= len(self.__channels)):
			if (self.__channels[channel - 1].enabled):
				if (self.__channels[channel - 1].on):
					self.__channels[channel - 1].turnOff()
				else:
					self.__channels[channel - 1].turnOn()

	def turnOn(self, channel):

		if (0 < channel <= len(self.__channels)):
			if (self.__channels[channel - 1].enabled):
				self.__channels[channel - 1].turnOn()

	def turnOff(self, channel):

		if (0 < channel <= len(self.__channels)):
			if (self.__channels[channel - 1].enabled):
				self.__channels[channel - 1].turnOff()

	def setLED(self, channel, mode = None):

		if (0 < channel <= len(self.__channels)):
			if (mode is None):
				self.__channels[channel].unset()
			elif (str(mode).lower() in self.__modes):
				mode = str(mode).lower()
				self.__channels[channel - 1].set(mode, self.__modes[mode])

	def getState(self, channel):

		if (0 < channel <= len(self.__channels)):
			state = self.__channels[channel - 1].on
			mode = self.__channels[channel - 1].mode
			power = self.__channels[channel - 1].power
			return([state, mode, power])
