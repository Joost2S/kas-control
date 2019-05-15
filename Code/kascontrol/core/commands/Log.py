#!/usr/bin/python3

# Author: J. Saarloos
# v1.0.01	10-05-2019


import logging

from Code.kascontrol.globstuff import globstuff as gs
from .base.netCommand import NetCommand


class Log(NetCommand):

	def __init__(self):
		super(Log, self).__init__()
		self.command = "log"
		self.name = "Log"
		self.args = "%entries%\t%level%"
		self.help = "Shows the log entries.\n"
		self.help += "Arguments:\n"
		self.help += "Entries\tShow the last n log entries. Default is 100.\n"
		self.help += "Level\t'debug' or 'error' Can be entered for entries of just one severity level.\n"
		self.help += "\tOtherwise all entries will be shown."
		self.argList = {"info" : "INFO", "debug" : "DEBUG", "warning" : "WARNING", "error" : "ERROR", "critical" : "CRITICAL"}

	def runCommand(self, client, args=None):

		a = ""
		lines = 100
		output = []
		msg = ""

		# Getting settings from arguments
		if (args is not None):
			check, i = self.isInt(args[0])
			if (not check):
				if (args[0] not in self.argList.keys()):
					return("Invalid argument.")
				else:
					a = args[0]
			elif (not i > 0):
				return("Please enter positive number.")
			else:
				lines = i

				if (a == "" and len(args) > 1):
					if (args[1] not in self.argList.keys()):
						return("Invalid argument.")
					else:
						a = args[1]

		# Loading in file
		try:
			with open(gs.logfile, "r") as file:
				for line in file:
					if (a == ""):
						output.append(line)
					elif (line.find(self.argList[a]) is not -1):
							output.append(line)
		except FileNotFoundError:
			logging.warning("Logfile not found...")
			msg = ("File not found. No log to show.")
			output = -1
		except IOError:
			msg = ("IO error. Unable to retrieve log.")
			output = -1

		if (output != -1):
			if (len(output) == 0):
				msg = "No entries found."
			if (len(output) < lines):
				lines = len(output)
			for line in output[0 - lines:]:
				msg += str(line) + "\n"

		return(msg)
