#!/usr/bin/python3
 
# Author: J. Saarloos
# v0.5.3	09-01-2018

import logging
import threading
import time

import globstuff
gs = globstuff.globstuff

class Group(object):
	"""This object represents the combination of a soil sensor and watervalve."""

	groupname = ""
	mstName = ""
	connected
	enabled = False
	watering
	below_range
	__lowtrig
	__hightrig
	valve
	__lock = None
	flowName = None
	tempName = None
	plantName = ""


	def __init__(self, gname, mname, tname, fname, valve, tdev, flowSensor):

		self.groupname = gname
		self.mstName = mname
		self.valve = valve		# do make object
		self.connected = False			# A sensor is considered disconnected when value <= adc resolution * 0.05.
		self.watering = False
		self.enabled = False				# Only enabled when a plant is present and triggers have been set.
		self.below_range = 0				# Counts when mst value is below lowtrig. At 5 watering will begin.
		self.lowtrig = 0
		self.hightrig = 0
		self.flowName = fname
		self.tempName = tname
		self.__lock = threading.Lock()
		self.plantName = None
	

	def getSensorData(self):
		
		moist = self.getM()
		temp = self.getT()
		flow = self.getF()
		return(soil, temp, flow)

	def getName(self):
		"""Returns the plant name if present, else the groupname."""

		if (self.enabled):
			return(self.plantName)
		else:
			return(self.mstName)

	def removePlant(self):
		"""When removing a plant, the channel will be disables until a new plant is entered."""

		self.enabled = False
		self.lowtrig = 0
		self.hightrig = 0
		gs.db.removePlant(self.plantName)
		self.plantName = None

	def addPlant(self, name, type = None):
		"""\t\tAdd a plant. Only possible of no plant is currently assigned.
		Channel will be enabled when new trigger levels are set."""

		if (not self.enabled and self.plantName == None):
			name = str(name).title()
			gs.db.addplant(name, type)
			self.plantName = name
			
	def getM(self):
		"""Returns the soil moisture level of the associated sensor."""

		with self.__lock:
			moist = gs.control.requestData(name = self.mstName)
			if (gs.running and not gs.testmode):
				try:
					moist = float(moist)
				except:
					return(moist)
				if (moist <= self.lowtrig and gs.control.isPumpEnabled()):
					self.below_range += 1
					if (self.below_range >= 5):
						wt = wateringthread(gs.getThreadNr(), "watering" + str(self.groupname[-1]), args = self)
						wt.start()
						gs.wtrThreads.append(wt)
						self.below_range = 0
			return(moist)

	def getT(self):
		"""Returns the temperature of the associated sensor."""

		if (self.tempName is None):
			return(None)
		return(gs.control.requestData(name = self.tempName))

	def getF(self):
		"""Returns the flowrate of the associated sensor if available."""

		if (self.flowName is None):
			return(None)
		return(self.flowName.getFlowRate())

	def setTriggers(self, lt = None, ht = None):
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
				gs.db.setTriggers(self.chan, self.lowtrig, self.hightrig)
			else:
				self.enabled = False

	def setFromDB(self):

		data = gs.db.getContainerNameTriggers(self.groupname)
		self.plantName = data[0]
		self.setTriggers(data[1], data[2])
		

class wateringthread(globstuff.protoThread):
	def run(self):
		print("Starting thread{0}: {1}".format(self.threadID, self.name))
		water(self.args)
		print("Exiting thread{0}: {1}".format(self.threadID, self.name))


class water(object):

	group = None
	flow = 0

	def __init__(self, group):
		self.group = group
		self.watering()


	def watering(self):
		"""\tControls the actual watering. Watering is intermittent to allow the water to
		drain a little to get a better measurement."""
	
		self.group.watering = True
		if (self.group.flowName is not None):
			self.group.flowName.requestData(self)
		start = round(time.time(), 2)
		t = 1
		while (gs.adc.getMeasurement(self.group.groupname, 0) < self.group.hightrig):
			gs.control.requestPumping(self.group.groupname, t)
			if (not self.group.connected or t == 3):
				break
			for i in range(45):
				time.sleep(1)
				if ((not gs.running) or gs.testmode):
					break
		gs.control.requestPumping(self.group.groupname, t)
		self.group.watering = False
		end = round(time.time(), 2)
		self.group.flowName.endRqeuest(self)
		msg = "{0}: Done watering on channel {1}, watered for {2} seconds.".format(time.strftime("%H:%M:%S"), self.group.chan, end)
		if (self.group.flowName is not None):
			msg +=  "Given {0} ticks of water".format(self.flow)
		print(msg)
		logging.info(msg)
		gs.db.wateringEvent(int(self.group.groupname[-1]), start, end, self.flow)

	def addPulse(self):
		""""""

		self.flow += 1