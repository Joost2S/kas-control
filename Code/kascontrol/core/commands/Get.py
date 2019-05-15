#!/usr/bin/python3

# Author: J. Saarloos
# v1.0.01	10-05-2019


from Code.kascontrol.globstuff import globstuff as gs
from .base.netCommand import NetCommand


class Get(NetCommand):

	def __init__(self):
		super(Get, self).__init__()
		self.command = "get"
		self.name = "Get"
		self.args = "%channel"
		self.guiArgs = {"channel": None}
		self.help = "Returns the min, current and max values for all soil sensors\n"
		self.help += "or just the selected soil sensor.\n"
		self.help += "Arguments:\n"
		self.help += "channel\tenter a channel number if the values of only one soil sensor needs to be displayed."

	def runCommand(self, args = None):
		"""Get values for min, current and max soilmoisture level."""

		reply = ""
		if (args is not None):
			if (len(args) == 1):
				check, chan = self.channelCheck(args[0])
				if (not check):
					return(chan)
				reply += ("Values of group " + gs.control.getGroupName(chan) + ":\n")
				reply += ("Low\t|Now\t|High\n")
				lt, ht = gs.control.getTriggers(chan)
				lvl = gs.control.requestData("soil-g" + chan[-1])
				reply += "{}\t|{}\t|{}\n".format(lt, lvl, ht)
				return (reply)
			return("Please enter correctly formatted command. Enter 'help {}' for more information.".format(self.command))

		reply += ("Group\t|Low\t|Now\t|High\n")
		for i in range(gs.control.grouplen()):
			name = "group" + str(i + 1)
			lt, ht = gs.control.getTriggers(name)
			lvl = gs.control.requestData("soil-g" + str(i + 1))
			name = gs.control.getGroupName(name)
			reply += "{}\t|{}\t|{}\t|{}\n".format(name, lt, lvl, ht)
		return(reply)
