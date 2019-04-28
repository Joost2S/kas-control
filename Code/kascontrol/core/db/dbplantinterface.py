#!/usr/bin/python3

# Author: J. Saarloos
# v0.01.00	25-04-2019


from abc import ABCMeta  # , abstractmethod
import logging
import sqlite3 as sql

# from ...globstuff import globstuff as gs
from .base import BaseDBinterface


class DBplantInterface(BaseDBinterface):
	__metaclass__ = ABCMeta

	def __init__(self):
		super(DBplantInterface, self).__init__()

	def addPlant(self, name, group, species = None):
		"""
		Use this method when adding a new plant to a container.
		If a plant is already assigned to the specified container,
		plant will not be added. Use removePlant() first.
		"""

		self.lastAction = "Add plant"
		self.__printutf("\t\tAdd Plant. " + str(name))
		if (species is None):
			species = "Generic"
		name = name.title()
		species = species.title()
		self.lastPlant = name
		try:
			group = int(group)
		except ValueError:
			group = int(group[-1])
		if (not (0 < group <= len(self.__groups))):
			self.lastResult = False
			logging.error("Unknown group. Please enter valid group number. 1 - {}".format(len(self.__groups)))
			return(False)
		# Get info on requested container.
		dbmsg1 = "SELECT p.name FROM plants AS p LEFT JOIN groups AS g ON p.plantID = g.plantID "
		dbmsg1 += "WHERE g.groupID = {};".format(group)
		curPlant = self.__dbRead(dbmsg1)
		self.__printutf("curPlant:" + str(curPlant))

		# Abort if there is already a plant in the requested container
		if (curPlant is not None):
			self.lastResult = False
			logging.error("Plant '{}' is already assigned to container {}.".format(curPlant[0], group))
			return(False)

		# If species isn't in the DB yet, add entry
		if (not species in self.__species):
			logging.info("New species. Adding {} to DB...".format(species))
			self.__addSpecies(species)

		# Add new plant
		submsg2 = "SELECT p.typeID FROM plantTypes AS p WHERE p.species = '{}' ".format(species)
		dbmsg2 = "INSERT INTO plants(name, plantType, datePlanted, groupID) "
		dbmsg2 += "VALUES('{}', ({}), datetime(), {});".format(name, submsg2, group)
		# Update group association to new plant
		dbmsg3 = "UPDATE groups SET plantID = (SELECT max(plantID) FROM plants) WHERE groupID = {};".format(group)
		self.__dbWrite(dbmsg2, dbmsg3)
		self.lastResult = True

		return(True)

	def __addSpecies(self, species):

		self.__species.append(species)
		dbmsg = "INSERT INTO plantTypes(species) VALUES('{}');".format(species.title())
		self.__dbWrite(dbmsg)

	def removePlant(self, plantName):
		"""
		User can remove a plant by name or container number.
		"""

		self.__printutf("\t\tRemove Plant." + str(plantName))

		self.lastAction = "Remove plant"
		dbmsg1 = "SELECT groups.groupID, plants.plantID, plants.name "
		dbmsg1 += "FROM groups "
		dbmsg1 += "INNER JOIN plants ON groups.plantID = plants.plantID "
		# Select by plant name or integer of container.
		try:
			if (0 < int(plantName) <= len(self.__groups)):
	#			print("Unknown group. Please enter valid group number. 1 - {}".format(len(self.__groups)))
				dbmsg1 += "WHERE groups.groupID = {};".format(plantName)
		except ValueError:
			plantName = plantName.title()
			self.lastPlant = plantName
			dbmsg1 += "WHERE plants.name = '{}';".format(plantName)
		with (self.__tlock):
			conn = sql.connect(self.__fileName)
			with conn:
				curs = conn.cursor()
				curs.execute(dbmsg1)
				plant = curs.fetchone()

		# Abort if no match found
		if (plant is None):
			self.lastResult = False
			if (isinstance(plantName, str)):
				msg = "Plant '{}' not found as currently assigned plant.".format(plantName)
			else:
				msg = "Container {} currently has no plant assigned.".format(plantName)
			return(False, msg)
		self.lastPlant = plant[2]
		self.lastResult = True
		self.__printutf("Removed plant '{}' from container {}.".format(plant[2], plant[0]))#logging.info
		pID = plant[1]
		# Change plant assignment in table groups to NULL
		dbmsg2 = "UPDATE groups SET plantID = NULL WHERE plantID = {};".format(pID)
		# Change dateRemoved in table plants
		dbmsg3 = "UPDATE plants SET dateRemoved = date() WHERE plantID = {};".format(pID)
		self.__dbWrite(dbmsg2, dbmsg3)
		return(True)

	def renamePlant(self, newName, container=None, oldName=None):
		# TODO: finish method
		query = "UPDATE plants SET name = {} WHERE plantID = {};".format(newName, oldName)

		result = self.__dbWrite(query)

		if result is False:
			return False, result
		return True, result
