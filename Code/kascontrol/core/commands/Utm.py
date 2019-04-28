#!/usr/bin/python3

# Author: J. Saarloos
# v1.0.00	24-04-2019


from datetime import datetime
import time

from ...globstuff import globstuff as gs
from .base.netCommand import NetCommand


class Utm(NetCommand):

	def __init__(self):
		super(Utm, self).__init__()
		self.command = "uptime"
		self.name = "Uptime"
		self.args = None
		self.help = "Returns a summary of the boot time,\n"
		self.help += "current time and the uptime of the system."

	def runCommand(self, client, args=None):
		if (client == "GUI"):
			return(gs.boottime)
		elif (client == "TERMINAL"):
			return(self.uptime())

	@staticmethod
	def uptime():
		"""Returns the boottime and current uptime."""

		reply = gs.getTabs("Boottime:", 3) + "{}\n".format(datetime.fromtimestamp(float(gs.boottime)).strftime("%Y-%m-%d %H:%M:%S"))
		reply += gs.getTabs("Current time:", 3) + "{}\n".format(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
		diff = time.time() - gs.boottime
		tDiff = gs.timediff(diff)
		reply += gs.getTabs("Uptime:", 3) + "{}d, {}:{}:{}".format(*tDiff)
		return(reply)
