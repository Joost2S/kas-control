#!/usr/bin/python3

# Author: J. Saarloos
# v0.01.00	25-04-2019


import logging

from ..globstuff import globstuff as gs


class Fan(object):

	__state = False
	__power = 65
	__objectUUID = None
	__requestUUID = None

	def __init__(self, pin):

		self.__objectUUID = gs.pwrmgr.pinSetup(pin)
		if (self.__objectUUID is False):
			gs.shutdown()

	def on(self):

		if not self.state:
			uuid = gs.pwrmgr.addRequest(self.__objectUUID, 0, self.__power, "critical")
			if (uuid is not False):
				self.__state = True
				self.__requestUUID = uuid
				return True
			return "Request denied by power manager"
		return "Fan already on"

	def off(self):

		if self.state:
			self.__state = False
			report = gs.pwrmgr.cancelRequest(self.__requestUUID)
			if report is False:
				logging.warning("Fan shut down failed.")
				return False
			return report
		return "Fan already off"

	@property
	def state(self):

		return(self.__state)
