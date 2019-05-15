#!/usr/bin/python3

# Author: J. Saarloos
# v1.0.01	10-05-2019


from Code.kascontrol.globstuff import globstuff as gs
from .base.netCommand import NetCommand

class Mst(NetCommand):

	def __init__(self):
		super(Mst, self).__init__()
		self.command = "mst"
		self.name = "Moisture level"
		self.args = "%group"
		# TODO: implement returning data for all sensors
		self.guiArgs = {#None : "Returns levels of all containers.",
			"group" : [1, gs.control.grouplen()]}
		self.help = []
		self.help.append("Takes a measurement of the given sensor and returns the soilmoisture level.\n")
		self.help.append("Available sensors:\n")
		self.help.append(self.listConnected())

	def returnHelp(self):
		"""Updates the last line of the help text to reflect the currently connected sensors."""

		self.help[-1] = self.listConnected()
		h = ""
		for line in self.help:
			h += (line)
		return(h)

	def runCommand(self, client, args = None):

		if (args is not None):
			if (len(args) > 0):
				check, chan = self.channelCheck(args[0])
				if (not check):
					return(chan)
				return(gs.control.requestData(chan, "mst"))
		return("Enter a group number. (1 - " + str(len(gs.control.grouplen())) + ").")

	def listConnected(self):
		lst = ""
		conn = False
		for g in gs.ch_list:
			if (g.connected):
				lst += str(g.name) + ", "
				conn = True
		if (not conn):
			return("No sensors available.")
		return(lst[:-2])
