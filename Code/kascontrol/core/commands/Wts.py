#!/usr/bin/python3

# Author: J. Saarloos
# v1.0.01	10-05-2019


from Code.kascontrol.globstuff import globstuff as gs
from .base.netCommand import NetCommand


class Wts(NetCommand):
	# TODO: implement in hwtests.py

	def __init__(self):
		super(Wts, self).__init__()
		self.command = "wtest"
		self.name = "Water test"
		self.args = "%container(s)%\t%time%"
		self.help = "Use this to test the watering system.\n"
		self.help += "The test has 2 components: First, water is given on all entered channels.\n"
		self.help += "Second, water is given 1 channel at a time.\n\n"
		self.help += "Arguments:\n"
		self.help += "%channel(s)%:\tEnter the number of the channel(s) you want. 'all' for all available channels.\n"
		self.help += "%time%:\tThe last argument given is assumed to be the time. Default time is 5 seconds.\n"

	def runCommand(self, client, args = None):
		if (gs.testmode):
			if (args is None):
				g, t = self.defaultParams()
				gs.pump.demo(g, t)
				return("Default watering test done.")
			else:
				t = 5
				valves = []
				check, t = self.isInt(args[-1])
				if (not check):
					return("Please enter a valid time.")
				if (not (t > 1 and t <= 60)):
					return("Invalid amount of time. (1 - 60)")
				if (len(args) >= 2 and args[0] == "all"):
					g, t = self.defaultParams(t)
					gs.pump.demo(g, t)
					return("Done watering test for {0} seconds per valve on all valves.".format(str(t)))
				for va in args[:-1]:
					check, v = self.isInt(va)
					if (not check):
						return("Enter valid valvenumber. (1 - {0})".format(str(len(gs.ch_list))))
					if (not (0 < v <= len(gs.ch_list))):
						return("Enter valid valvenumber. (1 - {0})".format(str(len(gs.ch_list))))
					valves.append(gs.ch_list[v - 1])
				gs.pump.demo(valves, t)
			return("Done watering test for {0} seconds per valve.".format(str(t)))
		else:
			return("Please turn on Testmode before testing the watering hardware.")

	def defaultParams(self, t = None):
		valves = []
		for g in gs.ch_list:
			valves.append(g)
		if (t is not None):
			return(valves, t)
		return(valves, 5)
