#!/usr/bin/python3

# Author: J. Saarloos
# v0.01.01	10-05-2019


from abc import ABCMeta#, abstractmethod
import logging
import time

from Code.kascontrol.globstuff import globstuff as gs
from .base import BaseDBinterface
from Code.kascontrol.utils.errors import DBValidationError
from Code.kascontrol.utils.threadingutils import ProtoThread


class Datalog(BaseDBinterface):

	__metaclass__ = ABCMeta

	def __init__(self):
		super(Datalog, self).__init__()

	def startDatalog(self):
		"""Use this function to start datalog to prevent more than 1 instance running at a time."""

		running = False
		for t in gs.draadjes:
			if (t.name == "Datalog" and t.is_alive()):
				if (running):
					return
				running = True
		self.__datalog()

	def __datalog(self):
		"""This is the main datalogging method. Every %interval minutes the data will be recorded into the database."""

		# Waiting to ensure recordings are synced to __interval
		if (gs.wait(self.__interval)):
			return

		# Datalogging loop.
		while (gs.running):
			if (not self.__pause):
				txt1 = "INSERT INTO sensorData(timestamp"
				txt2 = ")VALUES({}".format(int(time.time()))
				for n in self.__sensors.keys():
					txt1 += ", " + str(n)
					txt2 += ", " + str(self.__getValue(n))
				dbmsg = (txt1 + txt2 + ");")
				self.__dbWrite(dbmsg)
			if ((not gs.running) or gs.wait(self.__interval)):
				return


class DatalogThread(ProtoThread):
	def run(self):
		logging.info("Starting thread{0}: {1}".format(self.threadID, self.name))
		try:
			gs.db.startDatalog()
		except DBValidationError:
			pass
		except:
			logging.error("Error occured in datalog")
			self.run()
		finally:
			logging.info("Exiting thread{0}: {1}".format(self.threadID, self.name))
