#!/usr/bin/python3

# Author: J. Saarloos
# v1.0.00	24-04-2019


import threading

from ...globstuff import globstuff as gs
from .base.netCommand import NetCommand


class Thr(NetCommand):

	def __init__(self):
		super(Thr, self).__init__()
		self.command = "threads"
		self.name = "Threads"
		self.args = None
		self.help = "Returns a list of the currently running threads of this software."

	def runCommand(self, client, args=None):
		"""Gives information about the active threads."""

		tinfo = ("Number of threads active: " + str(threading.activeCount()) + "\n\n")
		for t in gs.draadjes:
			if (t.isAlive()):
				tinfo += "Thread {} name: ()\n".format(t.threadID, t.getName())
		for t in gs.wtrThreads:
			if (t.isAlive()):
				tinfo += "Thread {} name: {}\n".format(t.threadID, t.getName())
		return(tinfo)
