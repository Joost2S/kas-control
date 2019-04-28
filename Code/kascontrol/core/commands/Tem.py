#!/usr/bin/python3

# Author: J. Saarloos
# v1.0.00	24-04-2019


from ...globstuff import globstuff as gs
from .base.netCommand import NetCommand

class Tem(NetCommand):

	def __init__(self):
		super(Tem, self).__init__()
		self.command = "temp"
		self.name = "Temperature"
		self.args = "%name%"
		self.guiArgs = {"names": []}
		self.help = "Takes a measurement and returns the current temperature(s).\n"
		self.help += "Give the name of a sensor for just that temperature."

	def runCommand(self, client, args=None):

		if (args is not None):
			temp = gs.control.requestData(name=args[0])
			if (temp is None):
				return("Invalid tempsensor.")
			elif (temp is False):
				return("Error retrieving temperature for sensor {}. See log for details.".format(args[0]))
			else:
				return("{} : {}".format(args[0], temp))
		txt = "Sensor\t\t| value\n"
		data = gs.control.requestData(stype="temp")
		if (len(data) > 0):
			for n, t in data.items():
				txt += "{}| {}\n".format(gs.getTabs(n), t)
		else:
			txt = "No temperature devices found."
		return(txt)
