#!/usr/bin/python3

# Author: J. Saarloos
# v0.5.02	21-05-2018

# TODO: dependencies. pump depends on at least one valve being active.

import logging
import time
import uuid

from globstuff import globstuff as gs

class PowerManager(object):

	__ina = None
	__maxCurrent = 0
	__requests = list()
	__requestUUIDs = dict()   # {requestingUUID: pinUUID, ...}
	__stats = dict()
	priorityLevel = {"critical": [0, 0],
				        "emergency": [1, 10],
				        "security": [11, 25],
				        "user": [26, 50],
				        "auto-baseFunction": [51, 75],
				        "auto-miscFunction": [76, 100]
				        }

	def __init__(self, ina=None):
		super(PowerManager, self).__init__()
		self.__maxCurrent = 10000
		self.__ina = ina
		gs.pwrmgr = self
		gs.ee.on("cancelRequest", self.cancelRequest)
		gs.ee.on("unPauseRequest", self.unPauseRequest)
		gs.ee.on("pauseRequest", self.pauseRequest)
		gs.ee.on("addToActiveList", self.updateStats)
		gs.ee.on("addToQueueList", self.updateStats)
		gs.ee.on("removeFromActiveList", self.updateStats)
		gs.ee.on("removeFromQueueList", self.updateStats)

	def updateStats(self):
		data = dict()
		data["ql"] = 0
		data["al"] = 0
		data["cp"] = 0
		data["rl"] = len(self.__requests)
		for i, req in enumerate(self.__requests):
			# update positions
			if (req.active):
				data["cp"] += req.power
				data["al"] += 1
			else:
				data["ql"] += 1
		data["ap"] = 10000 - data["cp"]
		self.__stats = data
		gs.ee.emit("powerManagerStatsUpdated")

	def pinSetup(self, pin):

		pinuuid = gs.getPinDev(pin).setPin(gs.getPinNr(pin), False, True)
		if (pinuuid is False):
			return(False)
		uid = uuid.uuid4()
		self.__requestUUIDs[uid] = pinuuid
		return(uid)

	def addRequest(self, objectID, t, power, priority):
		"""Request to use a device on the 12v line."""

		# Check to see if the request meets all the requirements.
		# objectID uniqueness:
		for req in self.__requests:
			if (req.objectID == objectID):
				logging.debug("PowerRequest rejected. ObjectID already in use.")
				return(False)
		if (objectID not in self.__requestUUIDs.keys()):
			logging.debug("PowerRequest rejected. Invalid UUID.")
			return(False)
		# time validity:
		try:
			t = int(t)
		except ValueError:
			logging.debug("PowerRequest rejected. Invalid time.")
			return(False)
		# power requirements:
		try:
			power = int(power)
			if (not (0 < power <= self.__maxCurrent * 0.75)):
				raise ValueError
		except ValueError:
			logging.debug("PowerRequest rejected. Invalid power requested.")
			return(False)
		# priority level:
		try:
			priority = int(priority)
			if (not (0 <= priority <= 100)):
				raise ValueError
		except ValueError:
			logging.debug("PowerRequest rejected. Invalid priority level.")
			return(False)
		r = Request(objectID, t, power, priority)
		self.__requests.append(r)
		self.__prioritySort()
		self.__renewApprovalList()
		return(True)

	def cancelRequest(self, objectID):

		try:
			for i, req in enumerate(self.__requests):
				if (req.objectID == objectID):
					req.cancel()
					report = req.report()
					print("Deleting request:", objectID)
					self.__requests.remove(req)
					self.__renewApprovalList()
					if (req.manualPaused or req.autoPaused):
						gs.ee.emit("removeFromQueueList", req.objectID)
					else:
						gs.ee.emit("removeFromActiveList", req.objectID)
					return(report)
		except KeyError:
			pass

	def pauseRequest(self, objectID):

		try:
			for req in self.__requests:
				if (req.objectID == objectID):
					print("ManualPausing request: ", objectID)
					req.pause()
					req.manualPaused = True
					req.active = False
					self.__renewApprovalList()
					if (not req.autoPaused):
						gs.ee.emit("removeFromActiveList", req.objectID)
						gs.ee.emit("addToQueueList", req.data())
					return
		except KeyError:
			pass

	def unPauseRequest(self, objectID):
		try:
			for req in self.__requests:
				if (req.objectID == objectID):
					print("UnPausing request: ", objectID)
					# req.unpause()
					req.manualPaused = False
					self.__renewApprovalList()
					return
		except KeyError:
			pass

	def __renewApprovalList(self):
		"""
		Approves requests for which there is enough available power based on priority.
		If there is not enough power available for a request it is put in an autoPaused state.
		"""

		print("Renewing approvals.")
		power = 0
		turnOff = list()
		turnOn = list()
		for i, req in enumerate(self.__requests):
			power += req.power
			if (power <= self.__maxCurrent):
				# True if only autoPaused and not active OR
				# not at all paused and not active (request is being
				# considered for first tme).
				if ((req.autoPaused and not (req.active or req.manualPaused)) or
							(not req.autoPaused and not req.active and not req.manualPaused)):
					turnOn.append(i)
			else:
				# Correcting estimated total power usage:
				power -= req.power
				if (req.active or
							(not req.autoPaused and not req.active and not req.manualPaused)):
					turnOff.append(i)
		for i in turnOff:
			self.__autoPause(i)
		for i in turnOn:
			self.__autoActivate(i)

	def __prioritySort(self):
		"""Sort requests by priority. 1 is highest."""

		srtd = self.__requests
		# insertion sort
		i = 1
		while (i < len(srtd)):
			j = i
			while (j > 0 and srtd[j - 1].priority > srtd[j].priority):
				x = srtd[j]
				srtd[j] = srtd[j - 1]
				srtd[j - 1] = x
				j = j - 1
			i = i + 1

	def __autoPause(self, i):

		self.__requests[i].autoPaused = True
		self.__requests[i].active = False
		self.__requests[i].pause()
		print("autoPausing: {}".format(self.__requests[i].objectID))
		gs.ee.emit("removeFromActiveList", self.__requests[i].objectID)
		gs.ee.emit("addToQueueList", self.__requests[i].data())

	def __autoActivate(self, i):

		self.__requests[i].autoPaused = False
		self.__requests[i].active = True
		self.__requests[i].activate()
		print("autoActivating: {}".format(self.__requests[i].objectID))
		gs.ee.emit("removeFromQueueList", self.__requests[i].objectID)
		gs.ee.emit("addToActiveList", self.__requests[i].data())


class Request(object):

	def __init__(self, objectID, t, power, priority):
		self.objectID = objectID
		self.power = power
		self.timeDiff = t
		self.requestedDuration = t
		if (int(t) <= 0):
			self.timeDiff = 0
			self.timeLimited = False
			self.endTime = 0
			self.sessionStartTime = time.time()
		else:
			self.timeDiff = t
			self.timeLimited = True
			self.endTime = time.time() + self.timeDiff
			self.sessionStartTime = 0
		self.timeOfRequest = round(time.time(), 1)
		self.priority = priority
		self.active = False        # used to check if the request must change list
		self.autoPaused = False
		self.manualPaused = False
		self.cancelled = False

	def pause(self):
		"""Sets times when pausing the request."""

		print("pausing: ", self.objectID)
		if (self.timeLimited):
			self.timeDiff = round(self.endTime - time.time(), 1)
		else:
			self.timeDiff = round(time.time() - self.sessionStartTime, 1)
		# self.manualPaused = True
		gs.ee.emit("requestPaused", self.objectID)

	def activate(self):
		"""Sets times when (re)activating the request."""

		if (self.timeLimited):
			self.sessionStartTime = round(time.time(), 1)
			self.endTime = self.sessionStartTime + self.timeDiff
		else:
			self.sessionStartTime = round(time.time() - self.timeDiff, 1)

	def cancel(self):
		"""Sets times at the end of the request's lifetime."""

		if (self.active):
			self.timeDiff = self.requestedDuration - (self.endTime - time.time())
		self.endTime = time.time()
		self.cancelled = True

	def data(self):

		data = dict()
		data["objectID"] = self.objectID
		data["power"] = self.power
		data["timeDiff"] = self.timeDiff
		data["timeLimited"] = self.timeLimited
		data["priority"] = self.priority
		data["autoPaused"] = self.autoPaused
		data["manualPaused"] = self.manualPaused
		return(data)

	def report(self):
		"""
		This method is called at the end of the request's lifetime
		to give info on how the request was executed.
		"""

		report = dict()
		report["requestedDuration"] = self.requestedDuration
		report["actualDuration"] = self.timeDiff
		report["started"] = self.timeOfRequest
		report["ended"] = self.endTime
		# report[""] =
		# report[""] =
		# report[""] =
		return(report)
