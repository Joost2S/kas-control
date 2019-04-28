#!/usr/bin/python3

# Author: J. Saarloos
# v1.0.00	24-04-2019


from ...globstuff import globstuff as gs
from .base.netCommand import NetCommand


class Led(NetCommand):

	def __init__(self):
		super(Led, self).__init__()
		self.command = "powerled"
		self.name = "Toggle powerled"
		self.args = "%LED channel%"
		self.help = "Enter the channel of a powerLED string to toggle it on or off.\n"
		self.help += "Channel must be set to 1 of 3 values first with the setled command.\n"
		self.help += "There are 4 channels available.\n"
		self.help += "If no channel is entered, an overview of the current states will be returned.\n"

	def runCommand(self, args = None):
		if (args is not None):
			chan = args[0]
			try:
				if (not (0 < int(chan) <= len(gs.powerLEDpins))):
					raise ValueError
			except ValueError:
				return("Please enter valid channel.")
			if (gs.control.powerLEDtoggle(chan)):
				return("powerLED on channel {} toggled. State: {}".format(chan, gs.control.powerLEDstate(chan)[0]))
			else:
				return("Failed to toggle powerLED on channel {}. State: {}".format(chan, gs.control.powerLEDstate(chan)[0]))
		return("Please enter correctly formatted command. Enter 'help {}' for more information.".format(self.command))
