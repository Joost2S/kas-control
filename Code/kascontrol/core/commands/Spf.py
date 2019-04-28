#!/usr/bin/python3

# Author: J. Saarloos
# v1.0.00	24-04-2019


from ...globstuff import globstuff as gs
from .base.netCommand import NetCommand


class Spf(NetCommand):

	def __init__(self):
		super(Spf, self).__init__()
		self.command = "spoof"
		self.name = "Spoof"
		self.args = "%settings"
		self.help = "Use this to spoof adc data when yours isn't working\n"
		self.help += "or if you don't have plants to test with.\n"
		self.help += "Isn't working yet."

	def runCommand(self, client, args = None):

		if (gs.control.toggleSpoof()):
			return("Spoofmode enabled.")
		else:
			return("Spoofmode disabled.")
