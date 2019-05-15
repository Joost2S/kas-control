#!/usr/bin/python3

# Author: J. Saarloos
# v0.01.00	25-04-2019


from abc import ABCMeta, abstractmethod
import threading


class ProtoThread(threading.Thread):
	"""Use this to create new threads."""

	__metaclass__ = ABCMeta

	# threadID
	@property
	def threadID(self):
		return(self.__threadID)
	@threadID.setter
	def threadID(self, threadID):
		self.__threadID = threadID
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
	# obj
	@property
	def obj(self):
		return(self.__obj)
	@obj.setter
	def obj(self, obj):
		self.__obj = obj

	def __init__(self, threadID, name, args=None, obj:object=None):
		threading.Thread.__init__(self)
		self.threadID = threadID
		self.name = name
		self.args = args
		self.obj = obj

	@abstractmethod
	def run(self):
		pass
