#!/usr/bin/python3

# Author: J. Saarloos
# v0.1.02	20-05-2019


from abc import ABCMeta
import logging
import sqlite3 as sql
import sys

from Code.kascontrol.globstuff import globstuff as gs


class BaseDBinterface(object):

	__metaclass__ = ABCMeta

	__allowedTypes = []
	__sensors = {}
	__groups = {}
	__fileName = ""
	__species = []
	__tables = []
	__views = []
	__tlock = None
	__interval = 0 					# By default, record sensor data every 5 minutes.
	__pause = False

	lastPlant = ""
	lastAction = ""
	lastResult = False

	def __init__(self):
		super(BaseDBinterface, self).__init__()

	def __dbRead(self, dbmsg):
		"""
		Use this method to send queries to the DB.
		Returns a 2d array with results.
		"""

		dat = []
		with self.__tlock():
			#			try:
			with sql.connect(self.__fileName) as conn:
				curs = conn.cursor()
				curs.execute(dbmsg)
				data = curs.fetchall()
				if data is None or len(data) == 0:
					return None
				else:
					for row in data:
						a = []
						for t in row:
							a.append(t)
						dat.append(a)
		#			except:
		#				print("crap")
		#			finally:
		#				conn.close()
		return dat

	def __dbWrite(self, *dbmsgs):
		"""Use this method to write data to the DB."""

		sortedmsgs = self.__sortmsgs(*dbmsgs)

		try:
			with self.__tlock():
				conn = sql.connect(self.__fileName)
				with conn:
					curs = conn.cursor()
					for dbmsg in sortedmsgs:
						curs.execute(dbmsg)
					conn.commit()
					updRows = curs.rowcount
			if updRows > 1:
				print("updRows:", updRows)
		except sql.Error as er:
			logging.debug("er:", er)
			return 0
		return updRows

	def __sortmsgs(self, *dbmsgs):
		"""Recursive methed to extract all strings from arbitrarily nested arrays."""

		msgs = []
		if not isinstance(dbmsgs, str):
			for msg in dbmsgs:
				if not isinstance(msg, str):
					for m in self.__sortmsgs(*msg):
						msgs.append(m)
					pass
				else:
					msgs.append(msg)
		else:
			msgs.append(dbmsgs)
		return msgs

	def interval(self, interval):
		"""Set a new interval in minutes. Will be rounded down to whole seconds."""

		if interval >= 1.0:
			self.__interval = int(interval * 60)

	@staticmethod
	def __getValue(name):
		"""Takes a measurement of the value on the corresponding type and channel requested."""

		for i in range(5):
			data = gs.control.requestData(name=name, formatted=False)
			if data is not False and data is not None:
				return data
		logging.warning("Failed to get a measurement for sensor {}.".format(name))
		return "NULL"

	@staticmethod
	def __printutf(text):

		t = text.encode("utf-8")
		sys.stdout.buffer.write(t)
		print()
