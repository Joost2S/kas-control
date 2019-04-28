#!/usr/bin/python3

# Author: J. Saarloos
# v1.0.00	24-04-2019


from ...globstuff import globstuff as gs
from .base.netCommand import NetCommand


class Cur(NetCommand):

	def __init__(self):
		super(Cur, self).__init__()
		self.command = "cur"
		self.name = "Current stats"
		self.args = None
		self.help = "Returns the current value of all the sensors."

	def runCommand(self, client, args=None):
		if (client == "GUI"):
			return(gs.control.requestData())
		elif (client == "TERMINAL"):
			return(gs.control.formattedData)
