#!/usr/bin/python3

# Author: J. Saarloos
# v1.0.01	10-05-2019


from Code.kascontrol.globstuff import globstuff as gs
from .base.netCommand import NetCommand


class Hlp(NetCommand):

	def __init__(self):
		super(Hlp, self).__init__()
		self.command = "help"
		self.name = "Help"
		self.args = "%command%"
		self.help = "Returns a list of all the commands available if no command is entered.\n"
		self.help += "If a valid command is entered as argument a more detailed description\n"
		self.help += "of how the given command works is returned."

	def runCommand(self, client, args=None):
		commlist = args[0]
		if (len(args) == 1):
			commandlist = "Name\t\tCommand\t\tArguments\n"
			for comm in sorted(commlist.keys()):
				commandlist += "\n{0}{1}{2}".format(gs.getTabs(commlist[comm].name + ":"), gs.getTabs(commlist[comm].command), commlist[comm].args)
			return(commandlist)
		else:
			arg = args[1]
			if (arg in commlist.keys()):
				text = commlist[arg].name + "\n\n"
				text += commlist[arg].returnHelp()
				return(text)
			else:
				return(str(arg) + "\tNo such command exists. Cannot give information.")
