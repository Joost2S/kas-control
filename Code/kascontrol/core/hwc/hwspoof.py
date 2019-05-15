#!/usr/bin/python3

# Author: J. Saarloos
# v0.01.01	10-05-2019


from abc import ABCMeta, abstractmethod

from Code.kascontrol.globstuff import globstuff as gs
from .hwbase import HWbase


class HWspoof(HWbase):

	__metaclass__ = ABCMeta

	def __init__(self):
		super(HWspoof, self).__init__()

	def toggleSpoof(self):
		"""Toggle between real sensor data or algorithmically generated data."""

		self.__spoof = not self.__spoof
		return(self.__spoof)

	def getSpoofData(self, stype=None, name=None, caller=None, perc=False):
		"""Returns fake sensor data generated by excessively advanced algorithms."""

		if not self.__spoof:
			return None
		return("Stuff.")

	@abstractmethod
	def requestData(self, stype=None, name=None, formatted=None):
		return super().requestData(stype=stype, name=name, formatted=formatted)

	@abstractmethod
	def requestPower(self, *cur):
		return super().requestPower(cur)
