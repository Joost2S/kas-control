#!/usr/bin/python3

# Author: J. Saarloos
# v0.2.00	24-04-2019

"""
Template for making a new network command:

class cmd(NetCommand):

	def __init__(self):
		super(cmd, self).__init__()
		self.command = "command"
		self.name = "Command"
		self.args = ""
		self.guiArgs = {}
		self.help = "\n"
		self.help += ""

	def runCommand(self, client, args=None):
		if (args is not None):
			# Gather relavnt data.
			if (problem parsing):
				return("Please enter correctly formatted command. Enter 'help {}' for more information.".format(self.command))
			if (client == "GUI"):
				# Parse data for a GUI client and return data.
				return()
			elif (client == "TERMINAL"):
				# Parse data into text and return for TERMINAL client.
				txt = ""
				return(txt)
			else:
				return("Unsupported client type.")
"""

from abc import ABCMeta, abstractmethod

from ....globstuff import globstuff as gs


class NetCommand(object):
	"""Base object for commands available through the network interface."""

	__metaclass__ = ABCMeta

	# command
	@property
	def command(self):
		return(self.__command)
	@command.setter
	def command(self, command):
		self.__command = command
	# name
	@property
	def name(self):
		return(self.__name)
	@name.setter
	def name(self, name):
		self.__name = name
	# args
	@property
	def args(self):
		return(self.__args)
	@args.setter
	def args(self, args):
		self.__args = args
	# guiArgs
	@property
	def guiArgs(self):
		return(self.__guiArgs)
	@guiArgs.setter
	def guiArgs(self, guiArgs):
		self.__guiArgs = guiArgs
	# helpLong
	@property
	def help(self):
		return(self.__help)
	@help.setter
	def help(self, hlp):
		self.__help = hlp

	@abstractmethod
	def __init__(self):
		super(NetCommand, self).__init__()
		self.command = ""
		self.name = ""
		self.args = ""
		self.guiArgs = {}
		self.help = ""

	@abstractmethod
	def runCommand(self, client, args = None):
		pass

	@staticmethod
	def channelCheck(container):

		try:
			if (not (0 < int(container) <= gs.control.grouplen())):
				raise Exception
		except ValueError:
			return(False, "Enter valid channel. (1 - {0})".format(gs.control.grouplen()))
		return(True, "group" + str(container))

	@staticmethod
	def isInt(intgr):
		try:
			i = int(intgr)
		except (TypeError, ValueError):
			return(False, "Wrong input. Int expected. " + str(intgr))
		return(True, i)

	@staticmethod
	def isFloat(fltnr):
		try:
			f = float(fltnr)
		except (TypeError, ValueError):
			return(False, "Wrong input. Float expected. " + str(fltnr))
		return(True, f)

	def returnHelp(self):
		return(self.help)
