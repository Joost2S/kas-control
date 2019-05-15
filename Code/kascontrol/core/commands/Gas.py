#!/usr/bin/python3

# Author: J. Saarloos
# v1.0.01	10-05-2019


from Code.kascontrol.globstuff import globstuff as gs
from .base.netCommand2 import NetCommand


class Gas(NetCommand):

	def __init__(self):
		super(Gas, self).__init__()
		self.command = "guiargs"
		self.name = "GUI Arguments"
		self.args = "%command%"
		self.guiArgs = {}
		self.help = "Return the gui argument list for one or all commands."

	def run(self, client, args):

		pass
