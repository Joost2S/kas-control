#!/usr/bin/python3

# Author: J. Saarloos
# v1.0.00	24-04-2019


from ...globstuff import globstuff as gs
from .base.netCommand import NetCommand


class Pwr(NetCommand):

	def __init__(self):
		super(Pwr, self).__init__()
		self.command = "power"
		self.name = "power readings"
		self.args = "%power rail%, %type%"
		self.help = "Get current power reading.\n"
		self.help += "No arguments:\tGet all data from all rials.\n"
		self.help += "%power rail%:\tGet data from '5v' or '12v' power rail.\n"
		self.help += "%type%: \tGet current (c), voltage (v), power (p) or shunt voltage (s).\n"
		self.rials = ["5v", "12v"]
		self.options = ["c", "v", "p", "s"]

	def runCommand(self, args = None):

		rail = self.rials
		options = self.options
		if (args is not None):
			if (args[0] in self.rials):
				rail = [args[0]]
				if (len(args) > 1):
					if (args[1] in self.options):
						options = [args[1]]
					else:
						return("Not a valid option.")
			elif (args[0] in self.options):
				options = [args[0]]
			else:
				return("Please enter correctly formatted command. Enter 'help {}' for more information.".format(self.command))
		msg = ""
		for r in rail:
			msg += "|{}".format(gs.getTabs(r))
		msg += "\n" + "-" * (8 * len(rail)) + "\n"
		for o in options:
			for r in rail:
				msg += "|{}".format(gs.getTabs(gs.control.requestData(r + o)))
			msg += "\n"
		return(msg)
