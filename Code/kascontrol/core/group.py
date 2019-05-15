#!/usr/bin/python3

# Author: J. Saarloos
# v0.6.08	09-07-2018


import logging
import threading
import time

from ..globstuff import globstuff as gs
from ..utils.protothread import ProtoThread


class Group(object):
	"""This object represents the combination of a soil sensor and watervalve."""

	containerName = ""
	containerNumber = int
	mstName = ""
	flowName = None
	tempName = None
	plantName = ""
	connected = None
	enabled = False
	watering = None
	below_range = None
	lowtrig = None
	hightrig = None
	__valveUUID = None
	__lock = None

	def __init__(self, cname, cnumber, mname, tname, fname, valve):

		self.containerName = cname
		self.containerNumber = cnumber
		self.plantName = None
		self.mstName = mname
		self.flowName = fname
		self.tempName = tname
		ID = gs.pwrmgr.setPowerDevice(valve["pin"], "valve", valve["power"])
		self.__valveUUID = ID         # UUID for powerManager request
		self.below_range = 0				# Counts when mst value is below lowtrig. At 5 watering will begin.
		self.connected = False			# A sensor is considered disconnected when value <= adc resolution * 0.05.
		self.enabled = False				# Only enabled when a plant is present and triggers have been set.
		self.lowtrig = 0
		self.hightrig = 0
		self.watering = False
		self.__lock = threading.Lock()
		self.modes = ["enabled",
		              "not connected",
		              "watering requested",
		              "watering",
		              "done watering",
		              "disabled",
		              "planted",
		              "empty"]


	def getSensorData(self):

		soil = self.getM()
		temp = self.getT()
		flow = self.getF()
		return(soil, temp, flow)

	def getName(self):
		"""Returns the plant name if present, else the groupname."""

		if (self.enabled):
			return(self.plantName)
		else:
			return(self.containerName)

	def getStatus(self):
		"""
		Returns a named state if measurements are interrupted.
		Returns True if
		"""

		if not self.connected:
			return "N/C"
		elif self.watering:
			return "Busy"
		elif not self.enabled:
			return "NoPlant"
		return True

	def getM(self):
		"""Returns the soil moisture level of the associated sensor."""

		with self.__lock:
			mst = gs.control.requestData(name=self.mstName)
			if (gs.running and not gs.testmode):
				if (isinstance(mst, float)):
					if (mst <= self.lowtrig and gs.control.isPumpEnabled()):
						self.below_range += 1
						if (self.below_range >= 5):
							wt = WateringThread(gs.getThreadNr(), "watering" + self.containerName, obj=self)
							wt.start()
							gs.wtrThreads.append(wt)
							self.below_range = 0
		return(mst)

	def getT(self):
		"""Returns the temperature of the associated sensor."""

		if (self.tempName is None or not self.enabled ):
			return(None)
		if (not self.connected):
			return("N/C")
		return(gs.control.requestData(name = self.tempName))

	def getF(self):
		"""Returns the flowrate of the associated sensor if available."""

		if (self.flowName is None or not self.enabled ):
			return(None)
		if (not self.connected):
			return("N/C")
		return(self.flowName.getFlowRate())

	def removePlant(self):
		"""When removing a plant, the channel will be disabled until a new plant is entered."""

		if (self.plantName is not None):
			self.enabled = False
			self.lowtrig = 0
			self.hightrig = 0
			result = gs.db.removePlant(self.plantName)
			self.plantName = None
			return(result)
		return("No plant currently assigned to container {}.".format(self.containerNumber))

	def addPlant(self, name, species=None):
		"""\t\tAdd a plant. Only possible of no plant is currently assigned.
		Channel will be enabled when new trigger levels are set."""

		if (not self.enabled and self.plantName is None):
			name = str(name).title()
			gs.db.addPlant(name, self.containerName, species)
			self.plantName = name

	def setTriggers(self, lt=None, ht=None):
		"""If levels set below threshlod, container will be disabled."""

		if (self.plantName is not None):
			if (lt is None and ht is None):
				self.enabled = True	# can't get a measurement if the container is disabled.
				lvl = self.getM()
				self.lowtrig = int(lvl * 0.975)
				self.hightrig = int(lvl * 1.025)
			else:
				if (lt is not None):
					self.lowtrig = lt
				if (ht is not None):
					self.hightrig = ht
			# If both triggers are valid, re-enable the channel and write new value(s) to DB.
			if (gs.control.connCheckValue() <= self.lowtrig < self.hightrig):
				self.enabled = True
				gs.db.setTriggers(self.containerName, self.lowtrig, self.hightrig)
			else:
				self.enabled = False

	def setFromDB(self):

		data = gs.db.getContainerNameTriggers(self.containerName)
		self.containerNumber = data[0]
		self.plantName = data[1]

		self.setTriggers(data[2], data[3])


class WateringThread(ProtoThread):
	def run(self):
		print("Starting thread{0}: {1}".format(self.threadID, self.name))
		Water(self.obj)
		print("Exiting thread{0}: {1}".format(self.threadID, self.name))


class Water(object):

	group = None
	flow = 0

	def __init__(self, group):
		self.group = group
		self.watering()


	def watering(self):
		"""
		Controls the actual watering. Watering is intermittent to
		allow the water to drain a little to get a better measurement.
		"""

		self.group.watering = True
		if (self.group.flowName is not None):
			gs.control.getFlowSensor(self.group.flowName).requestData(self)
		start = round(time.time(), 2)
		while (gs.control.requestData(self.group.groupname, caller="wtr") < self.group.hightrig):
			gs.pwrmgr.addRequest(self.group.valve, 12)
			if (not self.group.connected):
				break
			for i in range(45):
				time.sleep(1)
				if ((not gs.running) or gs.testmode):
					break
		self.group.watering = False
		end = round(time.time(), 2)
		self.group.flowName.endRqeuest(self)
		msg = "{0}: Done watering on channel {1}, watered for {2} seconds.".format(time.strftime("%H:%M:%S"), self.group.chan, end)
		if (self.group.flowName is not None):
			msg += " Given {0} ticks of water".format(self.flow)
		print(msg)
		logging.info(msg)
		gs.db.wateringEvent(self.group.containerNumber, start, end, self.flow)

	def addPulse(self):
		""""""

		self.flow += 1
