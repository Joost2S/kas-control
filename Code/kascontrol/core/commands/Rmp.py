#!/usr/bin/python3

# Author: J. Saarloos
# v1.0.01	10-05-2019


from Code.kascontrol.globstuff import globstuff as gs
from .base.netCommand import NetCommand


class Rmp(NetCommand):
	"""Disassociate plant from container by plantname or container number."""

	def __init__(self):
		super(Rmp, self).__init__()
		self.command = "remplant"
		self.name = "Remove plant"
		self.args = "%plantName or %groupnr"
		self.help = ""

	def runCommand(self, args = None):
		if (args is not None):
			check, chan = self.channelCheck(args[0])
			if (not check):
				return(chan)
			group = gs.control.getGroupName(chan)
			if (gs.control.removePlant(group)):
				return("Succesfully removed plant from container {}.".format(chan))
			return("Failed to remove plant from container {}. Check log for details.".format(chan))
		return("Please enter correctly formatted command. Enter 'help {}' for more information.".format(self.command))
