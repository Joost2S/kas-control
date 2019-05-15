#!/usr/bin/python3

# Author: J. Saarloos
# v0.01.01	10-05-2019


from abc import ABCMeta, abstractmethod

from ...globstuff import globstuff as gs
from .hwbase import HWbase


class HWgroups(HWbase):

	__metaclass__ = ABCMeta

	def __init__(self):
		super(HWgroups, self).__init__()

	def setTriggers(self, group, low = None, high = None):
		"""Set 1 or both trigger levels for a container. Will be checked for valid values."""

		#Getting a base 10 value instead of a base 2 value:
		upperthreshold = self.getADCres() - (self.getADCres() % 1000)
		if (self.__groups[group].plantName is None):
			return("Container {} has no plant assigned. Cannot change trigger values.".format(group))
		if (not self.__groups[group].connected):
			return("Sensor for container {} is disconnected. Cannot change trigger values.".format(group))

		# when changing both triggers
		if (low is not None and high is not None):
			if (low < self.__connectedCheckValue or high > upperthreshold):
				return("Values out of bounds. Must be {} < lowtrig < hightrig < {}".format(self.__connectedCheckValue, upperthreshold))
			if (low >= high):
				return("Lowtrig must be lower than hightrig.")

		# When changing one trigger or none
		elif (low is not None):
			if (self.__groups[group].hightrig <= low):
				return("Too high value for lowtrig. Value must be < {}".format(self.__groups[group].hightrig))
			elif (low < self.__connectedCheckValue):
				return("Too low value for lowtrig. Value must be >= {}".format(self.__connectedCheckValue))
		elif (high is not None):
			if (self.__groups[group].lowtrig >= high):
				return("Too low value for hightrig. Value must be > {}".format(self.__groups[group].lowtrig))
			elif (high > upperthreshold):
				return("Too high value for hightrig. Value must be <= {}".format(upperthreshold))
		self.__groups[group].setTriggers(low, high)
		if (gs.hwOptions["ledbars"]):
			self.__LEDbars["mst"].updateBounds(self.__groups[group].groupname, self.__groups[group].lowtrig, self.__groups[group].hightrig)
		return("New value of trigger: {}, {}".format(self.__groups[group].lowtrig, self.__groups[group].hightrig))

	def getTriggers(self, group):
		"""Set a new trigger level for a container."""

		if (group in self.__groups):
			return(self.__groups[group].lowtrig, self.__groups[group].hightrig)
		return(None, None)

	def setPlantsAndTriggersFromDB(self):
		"""Trigger each group to retrieve data from the database and activate if appropriate."""

		for g in self.__groups.values():
			g.setFromDB()
			#TODO: set lcd and ledbar trigger levels

	def addPlant(self, group, name, species = None):
		"""Add a plant to a container. If a new species is added, it will be added to the database."""

		if (group in self.__groups):
			if (self.__groups[group].getName() == group):
				if(self.__groups[group].addPlant(name, group, species)):
					return("Added plant {} to container {}.".format(name.title(), group[-1]))
				return("Error trying to add plant. Check log for details.")
			return("Can't add new plant. Plant {} is already assigned to container {}.".format(self.__groups[group].getName(), group[-1]))
		return("Invalid group.")

	def removePlant(self, group):

		if (group in self.__groups):
			return(self.__groups[group].removePlant(group))

	def getGroupName(self, group):
		"""Returns the groupname or plantname if available."""

		if (group in self.__groups):
			return(self.__groups[group].getName())
		return(False)

	def getGroupNameFromNumber(self, number: int):

		for group in self.__groups:
			if group.containerNumber == number:
				return True, group.groupname
		return False, "No container with number: {}.".format(number)

	def getGroupSensorNames(self, groupname: str):

		if (groupname in self.__groups):
			g = self.__groups[groupname]
			return (g.mstName, g.flowName, g.tempName)

	def validateGroupName(self, name: str):

		for group in self.__groups:
			if group.groupname.lower() == name.lower():
				return True, group.groupname
		return False, "No container with name: {}.".format(name)

	def grouplen(self):
		"""Returns the amount of containers."""

		return(len(self.__groups))

	@abstractmethod
	def requestData(self, stype=None, name=None, formatted=None):
		return super().requestData(stype=stype, name=name, formatted=formatted)

	@abstractmethod
	def requestPower(self, *cur):
		return super().requestPower(cur)
