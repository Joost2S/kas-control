#!/usr/bin/python3

# Author: J. Saarloos
# v1.0.00	24-04-2019


from ...globstuff import globstuff as gs
from .base.netCommand import NetCommand


class Tsm(NetCommand):

	def __init__(self):
		super(Tsm, self).__init__()
		self.command = "testmode"
		self.name = "Testmode"
		self.args = "'on'\t'off'"
		self.help = "Turn the testmode on or off.\n"
		self.help += "Testmode disables database recording and watering.\n"
		self.help += "Measurements from the monitor will continue."

	def runCommand(self, client, args = None):
		if (args is not None):
			if (args[0] == "on"):
				gs.testmode = True
				gs.control.disable()
				gs.db.pauze = True
				return("Testmode enabled.")
			elif (args[0] == "off"):
				gs.testmode = False
				gs.control.enable() # TODO: implement
				gs.db.pauze = False
				return("Testmode disabled.")
			return("Please specify 'on' or 'off'.")
		return(gs.testmode)
