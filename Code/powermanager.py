#!/usr/bin/python3

# Author: J. Saarloos
# v0.6.00	09-07-2018

# TODO: dependencies. pump depends on at least one valve being active.
# UUIDs:
# pinID: used between manager and mcp driver.
# objectID: used for exclusice acces for the first requester of a resource.
# requestID: used in events (and thus publicly) and to get access to final report.
# TODO: get access to reports of cancelled requests. Store in dict{requestID: report, ...}.

"""
Manages the usage of a power line that has a limited amount of power
to ensure no more power is used than is available.
Users must get an accesUUID by registering a power object on a GPIO pin.
Multiple objects can be set on a single pin by sending along the first
accessUUID on successive object registrations. Only one of these objects can
have a request on it at one time.
This ensures ownership. When making a request a requestUUID will be returned
allowing the requesting process to get a report with info on how the
request was handeled.
accessUUID must be sent along when making a request.
A report will be returned when manually ending a request.
"""

import logging
import threading
import time
import uuid

from globstuff import globstuff as gs


class PowerManager(object):

	__ina = None
	__maxCurrent = 0
	__requests = list()
	__requestUUIDs = dict()    # {objectUUID: pinUUID, ...} !OBSOLETE!
	__powerObjects = dict()    # {objectUUID: powerObject(), ...}
	__stats = dict()
	__lock = None
	__priorityLevel = {"critical": [0, 0],
				        "emergency": [1, 10],
				        "security": [11, 25],
				        "user": [26, 50],
				        "auto-baseFunction": [51, 75],
				        "auto-miscFunction": [76, 100]
				        }

	def __init__(self, ina=None):
		super(PowerManager, self).__init__()
		self.__maxCurrent = 4000
		self.__ina = ina
		self.__lock = threading.Lock()
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

	def setPowerDevice(self, pin, devType, power, reqUUID=None):

		if (reqUUID is not None and reqUUID in self.__requestUUIDs.keys()):
			pass
		pinuuid = gs.getPinDev(pin).setPin(gs.getPinNr(pin), direction=False, exclusive=True)
		if (pinuuid is False):
			return(False)
		if (not (0 < power <= self.__maxCurrent * 0.75)):
			logging.warning("Power device with too high a current was requested and denied. {}: {}".format(devType, power))
			return(False)
		uid = uuid.uuid4()
		self.__requestUUIDs[uid] = pinuuid
		self.__powerObjects[uid] = PowerObject(pin, devType, power, pinuuid)
		return(uid)

	def addRequest(self, objectUUID, duration=None):
		"""Request to use a device on the 12v line."""

		with self.__lock:
			# Check to see if the request meets all the requirements.
			if (objectUUID not in self.__powerObjects.keys()):
				logging.debug("PowerRequest rejected. Invalid UUID.")
				return(False)
			# duration validity:
			if (duration is not None):
				try:
					duration = int(duration)
				except ValueError:
					logging.debug("PowerRequest rejected. Invalid time.")
					return(False)
			# objectID uniqueness:
			for req in self.__requests:
				if (req.objectID == objectUUID):
					logging.debug("PowerRequest rejected. ObjectID already in use.")
					return(False)
			# Check dependancies:

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
			requestID = uuid.uuid4()
			r = Request(requestID, objectID, duration, priority)
			self.__requests.append(r)
			self.__prioritySort()
			self.__renewApprovalList()
			# return new uuid for accessing report.
			return(requestID)

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
			return(False)

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

	def disableDevice(self, objectUUID):

		pass

	def enableDevice(self, objectUUID):

		pass


class Request(object):

	def __init__(self, requestID, objectID, duration, priority):

		if (duration is None):
			duration = 0
		self.objectID = objectID
		self.requestedDuration = duration
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

	def assignDependant(self, obj):

		pass

	def unassignDependant(self, obj):

		pass

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


class PowerObject(object):

	devType = ""
	enabled = True
	power = 0  # mA
	on = False
	pin = ""
	pinuuid = None

	def __init__(self, pin, devType, power, pinuuid):
		self.pin = pin
		self.devType = devType
		self.power = power
		self.pinuuid = pinuuid
		self.prioritySpace = []

	def turnOn(self):
		self.on = True
		gs.getPinDev(self.pin).output(gs.getPinNr(self.pin), True, uid=self.pinuuid)

	def turnOff(self):
		self.on = False
		gs.getPinDev(self.pin).output(gs.getPinNr(self.pin), False, uid=self.pinuuid)

	def disable(self):
		self.enabled = False
		self.turnOff()

	def enable(self):
		self.enabled = True