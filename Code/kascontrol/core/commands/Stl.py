#!/usr/bin/python3

# Author: J. Saarloos
# v1.0.00	24-04-2019


from ...globstuff import globstuff as gs
from .base.netCommand import NetCommand


class Stl(NetCommand):

	def __init__(self):
		super(Stl, self).__init__()
		self.command = "setled"
		self.name = "setled"
		self.args = "%LED channel, %value"
		self.help = "Enter a value for a channel to set.\n"
		self.help += "Values are not remembered between restarts.\n"
		self.help += "There are 4 channels available.\n"
		self.help += "Possible values:\n"
		self.help += "'1ww', for 1 watt white LEDS at 350 mA.\n"
		self.help += "'3ww', for 3 watt white LEDS at 700 mA.\n"
		self.help += "'3ir', for 1 watt white LEDS at 500 mA.\n"

	def runCommand(self, args = None):
		if (args is not None):
			if (len(args) >= 2):
				try:
					if (not (0 < int(args[0]) <= len(gs.powerLEDpins))):
						raise ValueError
				except ValueError:
					return("Please enter valid channel.")
				if (args[1] in ["1ww", "3ww", "3ir"]):
					gs.control.powerLEDset(args[0], args[1])
					return("Channel {} set to: '{}'. Now ready to be used.".format(args[0], args[1]))
		return("Please enter correctly formatted command. Enter 'help {}' for more information.".format(self.command))
