#!/usr/bin/python3

# Author: J. Saarloos
# v1.0.01	10-05-2019


from Code.kascontrol.globstuff import globstuff as gs
from .base.netCommand import NetCommand


class Set(NetCommand):

	"""
	network: check datatypes and container
	control: check if triggers are allowed to be set
				check if values are valid
	group:	(auto) set triggers and enable container if values are good
	db:		values are written to db if container enabled
	ledbar:  update bounds for appropriate bar
	"""

	def __init__(self):
		super(Set, self).__init__()
		self.command = "set"
		self.name = "Set"
		self.args = "%channel\t%trigger\t%value"
		self.guiArgs = {
			"channel": [{"type": int, "limit": [1, gs.control.grouplen()]},
							{"type": str, "match": ["auto"]}
							],
			"lowval": [{"type": int, "limit": [0, gs.control.getADCres()]}],
			"highval": [{"type": int, "limit": [0, gs.control.getADCres()]}],
		}
		self.help = "Use this command to set a new value for what moisture level is wanted.\n"
		self.help += "Arguments:\n"
		self.help += "%container\t\tNumber of container to change.\n"
		self.help += "trigger\t'low'\tcontrols when the pumping starts. Select how dry the soil can become.\n"
		self.help += "\t'high'\tcontrols how wet the soil may become.\n"
		self.help += "value\t\tSelect the value for the channel. (200 - 4000)\n"
		self.help += "Altrnative:\n"
		self.help += "%container\t\tNumber of container to change.\n"
		self.help += "%lowValue\tEnter value for lower trigger.\n"
		self.help += "%highValue\tEnter value for higher trigger.\n"
		self.data = {
			"channel": None,
			"lowval": None,
			"highval": None
		}

	def runCommand(self, client, args = None):
		"""set values for min and max soilmoisture level."""

		self.resetData()
		if (args is None):
			return("Please enter correctly formatted command. Enter 'help {}' for more information.".format(self.command))

		if (client == "GUI"):
			check, data = self.getGUIargs(args)
		elif(client == "TERMINAL"):
			check, data = self.getTERMargs(args)
		else:
			return
		if (not check):
			return(data)

		if (self.data["channel"] == "auto"):
			msg = []
			for i in range(gs.control.grouplen()):
				msg.append(gs.control.setTriggers("group" + str(i + 1)))
			if (client == "GUI"):
				return(msg)
			txt = str()
			for line in msg:
				txt += line + "\r"
			return (txt)

		check, channel = self.channelCheck(self.data["channel"])
		if (not check):
			return(channel)

		return(gs.control.setTriggers(self.data["channel"],
				 self.data["lowval"], self.data["highval"]))

	def getGUIargs(self, args):
		for setting in self.data.keys():
			try:
				self.data[setting] = args[setting]
			except ValueError:
				continue
			if (setting[-3:] == "val" and
					not isinstance(self.data[setting], int)):
				return(False, "Value {} not given as int.".format(setting))
		return(True, self.data)

	def getTERMargs(self, args):
		if (len(args) > 1):
			if (len(args) >= 3):
				trig = "lowval"
				if (not (args[1] == "low" or args[1] == "high")):
					try:
						self.data["lowval"] = int(args[1])
						self.data["highval"] = int(args[2])
					except ValueError:
						return("Enter 'low' or 'high' as first argument and a value as second.")
				else:
					if (args[1] == "high"):
						trig = "highval"
				try:
					self.data[trig] = int(args[2])
				except ValueError:
					return("Incorrect value for trigger.")
		elif (len(args) == 1):
			self.data["channel"] = args[0]
			# return(gs.control.setTriggers(args[0]))
		return(True, self.data)

	def resetData(self):
		self.data = {
			"channel": None,
			"lowval": None,
			"highval": None
		}
