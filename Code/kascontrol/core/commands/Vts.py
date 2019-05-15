#!/usr/bin/python3

# Author: J. Saarloos
# v1.0.01	10-05-2019


import time

from Code.kascontrol.globstuff import globstuff as gs
from .base.netCommand import NetCommand


class Vts(NetCommand):
	# TODO: implement in hwtests.py

	def __init__(self):
		super(Vts, self).__init__()
		self.command = "vtest"
		self.name = "Valve test"
		self.args = "%valve%\t%time%"
		self.help = "Can be used to test the valves. Only works if system is in testmode."
		self.help += "Arguments:\n"
		self.help += "None\tCycle through all valves.\n"
		self.help += "%container%\tEnter the container number of the valve to test. (1 - {0})\n".format(str(gs.control.grouplen()))
		self.help += "%time%\tEnter the time in seconds (max 60) to leave the valve open.\n"
		self.help += "\tOnly works if a container number has been entered. If not entered, 5 will be used.\n"

	def runCommand(self, client, args = None):
		if (gs.testmode):
			if (args is None):
				for g in gs.ch_list:
					print("valve" + str(g.chan))
					g.valveOn()
					time.sleep(1)
					g.valveOff()
					time.sleep(0.5)
				return("Test done.")
			else:
				t = 5
				if (len(args) > 1):
					check, t = self.isInt(args[1])
					if (not check):
						return("Please enter a valid time.")
					if (not (1 < t <= 60)):
						return("Invalid amount of time. (1 - 60)")
				check, v = self.isInt(args[0])
				if (not check):
					return("Enter valid valvenumber. (1 - {0})".format(str(len(gs.ch_list))))
				if (not (0 < v <= gs.control.grouplen())):
					return("Enter valid valvenumber. (1 - {0})".format(str(len(gs.ch_list))))
				gs.ch_list[v - 1].valveOn()
				time.sleep(t)
				gs.ch_list[v - 1].valveOff()
				return("Valve test done.")
		else:
			return("Please turn on Testmode before doing a valvetest.")
