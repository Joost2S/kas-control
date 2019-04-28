#!/usr/bin/python3

# Author: J. Saarloos
# v1.0.00	27-04-2019


import time

from ...globstuff import globstuff as gs
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
