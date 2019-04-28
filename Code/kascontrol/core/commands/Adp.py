#!/usr/bin/python3

# Author: J. Saarloos
# v1.0.00	24-04-2019


from ...globstuff import globstuff as gs
from .base.netCommand import NetCommand


class Adp(NetCommand):
	"""
	The name and type of the plant are seperated by a comma to enable users to
	enter multi-word plant names and species.
	"""

	def __init__(self):
		super(Adp, self).__init__()
		self.command = "addplant"
		self.name = "Add plant"
		self.args = "%container\t%plantName\t%plantType%"
		self.help  = "Add a plant by name to a container to set the system up\n"
		self.help += "to water that container. When the plantname is set, the trigger values must be set.\n"
		self.help += "Arguments:\n"
		self.help += "%container:\tThe number of the container. 1 - {}\n".format(gs.control.grouplen())
		self.help += "%plantName:\tName of the plant.\n"
		self.help += "%plantType%:\tSpecies of the plant.\n"
		self.help += "Plant name and type can contain spaces, are seperated by a comma (,).\n"

	def runCommand(self, args = None):

		name = None
		type = None
		if (args is not None):
			if (len(args) >= 2):
				check, chan = self.channelCheck(args[0])
				if (not check):
					return(chan)
				txt = ""
				for arg in args[1:]:
					txt += str(arg) + " "
				if (txt.find(",",) != -1):
					list = txt.split(",", 1)
					name = list[0]
					type = list[1]
				else:
					name = txt.strip()
				return(gs.control.addPlant(chan, name, type))
		return("Please enter correctly formatted command. Enter 'help {}' for more information.".format(self.command))
