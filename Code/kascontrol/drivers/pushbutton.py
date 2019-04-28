#! /usr/bin/python
 
# Author: J. Saarloos
# v0.6.3	01-10-2017

from abc import ABCMeta, abstractmethod
import logging
import RPi.GPIO as GPIO
import time

from ..globstuff import globstuff as gs


class toggleButton(object):

	__metaclass__ = ABCMeta

	def __init__(self, buttonpin):
		
		gs.getPinDev(buttonpin).setPin(gs.getPinNr(buttonpin), True)
		gs.getPinDev(buttonpin).addInterruptInput(gs.getPinNr(buttonpin), self, "high")

		
	@abstractmethod
	def run(self):
		pass


class timedButton(object):

	__metaclass__ = ABCMeta

	def __init__(self):
		pass


class stopButton(object):

	#	button 1: stop/reboot/shutdown
	#	button 2: toggle LCD backlight
	timePressed = 0
	typ = "timed", "single"

	def __init__(self, pin):
		
		gs.getPinDev(pin).setPin(gs.getPinNr(pin), True)
		gs.getPinDev(pin).addInterruptInput(gs.getPinNr(pin), self, "both")

			

	def run(self, state):
		
		if (state):
			self.__pressed()
		else:
			self.__dePressed()
			
	def __pressed(self):

		self.timePressed = time.time()

	def __dePressed(self):
		
		deltaT = time.time() - self.timePressed
		if (deltaT < 2):
			gs.shutdownOpt = "-s"
		elif (deltaT < 5):
			gs.shutdownOpt = "-r"
		elif (deltaT < 15):
			gs.shutdownOpt = "-x"
		else:
			return
		gs.server.commands["exit"].stop()
	
class lightToggle(object):

	pin = ""
	state = True

	def __init__(self, lcdpin, buttonpin):
		
		self.pin = lcdpin
		GPIO.setup(self.pin, GPIO.OUT)
		GPIO.output(self.pin, GPIO.HIGH)
		gs.getPinDev(buttonpin).setPin(gs.getPinNr(buttonpin), True)
		gs.getPinDev(buttonpin).addInterruptInput(gs.getPinNr(buttonpin), self, "high")


	def run(self):
		"""Toggles the LCD backlight on and off."""

		self.state = not self.state
		if (self.state):
			GPIO.output(self.pin, GPIO.HIGH)
		else:
			GPIO.output(self.pin, GPIO.LOW)
