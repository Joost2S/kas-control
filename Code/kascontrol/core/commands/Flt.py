#!/usr/bin/python3

# Author: J. Saarloos
# v1.0.00	24-04-2019


from ...globstuff import globstuff as gs
from .base.netCommand import NetCommand


class Flt(NetCommand):

	def __init__(self):
		super(Flt, self).__init__()
		self.command = "flt"
		self.name = "Float switch"
		self.args = ""
		self.help = "Returns a brief overview of the settings related to the float switch."

	def runCommand(self, client, args = None):

		if (client == "GUI"):
			return(gs.fltdev.low_water)
		if (client == "TERMINAL"):
			return("fltdev pinstate: " + str(gs.fltdev.getStatus()) + " low_water state: " + str(gs.fltdev.low_water))
