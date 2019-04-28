#!/usr/bin/python3

# Author: J. Saarloos
# v0.2.00	28-04-2019

"""
class cmd(NetCommand):

	def __init__(self):
		super(cmd, self).__init__()
		self.args = ""
		self.availableTo = ["GUI", "TERMINAL"]
		self.command = "command"
		self.guiArgs = {}
		self.help = "\n"
		self.help += ""
		self.name = "Command"
		self.processSeperate = bool

	@abstractmethod
	def runCommand(self, client, args=None):
		override if necessary

	@staticmethod
	def getGUIargs(args):
		override if necessary

	@staticmethod
	@abstractmethod
	def getTERMargs(args):
		always override
"""


guiArgs = {
	"argname": {
		"vartype": None,
		"varConstrain": ["matchOne", "matchAny", "limit"],
		"condition": ["required", "required_if", "otional"],
		"helpText": ""
	}
}


from abc import ABCMeta, abstractmethod

from ....globstuff import globstuff as gs


class NetCommand(object):
	"""Base object for commands available through the network interface."""

	__metaclass__ = ABCMeta

	@abstractmethod
	def __init__(self, client):
		super(NetCommand, self).__init__()
		self.args = ""
		self.availableTo = ["GUI", "TERMINAL"]
		self.client = client
		self.command = ""
		self.guiArgs = {}
		self.help = ""
		self.name = ""
		self.processSeperate = True

	def runCommand(self, args=None):

		check = True
		arguments = {}

		if self.client not in self.availableTo:
			return False, "Command {} not available to client of type {}".format(self.command, self.client)

		if args is None or len(args) == 0:
			if len(self.guiArgs) != 0:
				return False, "Command {} requires arguments, none were provided."
		else:
			if self.processSeperate:
				if self.client == "GUI":
					check, arguments = self.getGUIargs(args)
				elif self.client == "TERMINAL":
					check, arguments = self.getTERMargs(args)
			else:
				check, arguments = self.getArgs(args)
		if check is False:
			return False, arguments

		check, data = self.run(arguments)
		if check is False:
			return False, data

		if self.processSeperate:
			if self.client == "GUI":
				return self.guiReturn(data)
			elif self.client == "TERMINAL":
				return self.termReturn(data)
		return self.dataReturn(data)

	@abstractmethod
	def run(self, args):
		pass

	@staticmethod
	def getGUIargs(args):

		#TODO: implement
		succes = False
		return succes, args

	@staticmethod
	def getTERMargs(args):

		succes = False
		return succes, args

	@staticmethod
	def getArgs(args):

		succes = False
		return succes, args

	@staticmethod
	def guiReturn(data):

		succes = True
		return succes, data

	@staticmethod
	def termReturn(data):

		succes = True
		return succes, data

	@staticmethod
	def dataReturn(data):

		succues = True
		return succues, data

	@staticmethod
	def containerCheck(container):
		"""
		Accepts container number or container name.
		Returns the name of the requested container or False if not found.
		"""

		try:
			container = int(container)
		except ValueError:
			pass

		if isinstance(container, int):
			check, name = gs.control.getGroupNameFromNumber(container)
			if not check:
				return check, name
		elif isinstance(container, str):
			check, name = gs.control.validateGroupName(container)
			if not check:
				return check, name
		else:
			return False, "Unrecognized container format."
		return(True, name)

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
