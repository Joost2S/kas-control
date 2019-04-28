#!/usr/bin/python3

# Author: J. Saarloos
# v1.0.00	24-04-2019


from ...globstuff import globstuff as gs
from .base.netCommand import NetCommand


class Sen(NetCommand):

	def __init__(self):
		super(Sen, self).__init__()
		self.command = "sensors"
		self.name = "Sensor list"
		self.args = None
		self.help = "Returns a list with all sensors and some metadata per sensor.\n"

	def runCommand(self, client, args=None):

		slist = gs.control.getSensorNames()
		if (client == "GUI"):
			return(list(slist))
		msg = ""
		for item in ["|Name", "|Type", "|Group", "|Resolution"]:
			msg += gs.getTabs(item)
		msg += "\n"
		for row in slist:
			for item in row:
				msg += gs.getTabs("|" + item)
		return(msg)
