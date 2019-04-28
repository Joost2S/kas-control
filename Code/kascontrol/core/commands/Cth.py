#!/usr/bin/python3

# Author: J. Saarloos
# v1.0.00	24-04-2019


from ...globstuff import globstuff as gs
from .base.netCommand import NetCommand


class Cth(NetCommand):

	def __init__(self):
		super(Cth, self).__init__()
		self.command = "cthist"
		self.name = "Container history"
		self.args = "%groupnr"
		self.help = "Returns the names and some stats for all the plants in the container.\n"
		self.help += ""

	def runCommand(self, args = None):
		if (args is not None):
			check, chan = self.channelCheck(args[0])
			if (not check):
				return(chan)
			# Maybe do some formatting.
			return(gs.db.getContainerHistory(chan))
		return("Please enter correctly formatted command. Enter 'help {}' for more information.".format(self.command))
