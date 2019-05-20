#!/usr/bin/python3

# Author: J. Saarloos
# v0.01.01	20-05-2019


from abc import ABCMeta, abstractmethod
from contextlib import contextmanager
import threading


class TimeoutLock(object):
	def __init__(self, timeout):
		self._lock = threading.Lock()
		self.timeout = timeout

	def acquire(self):
		return self._lock.acquire(blocking=True, timeout=self.timeout)

	@contextmanager
	def acquire_timeout(self):
		result = self.acquire()
		yield result
		if result:
			self.release()

	def release(self):
		self._lock.release()


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
