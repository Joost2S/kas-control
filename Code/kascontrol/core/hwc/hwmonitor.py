#!/usr/bin/python3

# Author: J. Saarloos
# v0.01.02	20-05-2019


from abc import ABCMeta, abstractmethod
import logging
import time

from Code.kascontrol.globstuff import globstuff as gs
from Code.kascontrol.utils.threadingutils import ProtoThread
from .hwbase import HWbase


class HWmonitor(HWbase):

	__metaclass__ = ABCMeta

	def __init__(self):
		super(HWmonitor, self).__init__()
		self.__setTemplate()
		self.setTimeRes()

	def __setTemplate(self):
		"""Generates the template for the formatted currentstats."""

		lines = list()
		lines.append("{time}")
		lines.append("Plant\t")
		lines.append("Mst\t")
		if (gs.hwOptions["flowsensors"]):
			lines.append("Water\t")
		if (gs.hwOptions["soiltemp"]):
			lines.append("Temp\t")
		for g in self.__groups.values():
			lines[1] += "{" + g.groupname + "}"
			lines[2] += "{" + g.mstName + "}"
			if (gs.hwOptions["flowsensors"]):
				lines[3] += "{" + g.flowName + "}"
			if (gs.hwOptions["soiltemp"]):
				lines[4] += "{" + g.tempName + "}"
		lines.append("")
		currentlines = len(lines)
		lines.append("Light:\tTemps:")
		if (gs.hwOptions["flowsensors"]):
			hasOtherFlow = False
			for t in self.__otherSensors:
				if (self.__sensors[t] == "flow"):
					hasOtherFlow = True
				if (self.__sensors[t] in ["temp", "cputemp"]):
					lines[currentlines + 0] += "\t"
			if (hasOtherFlow):
				lines[currentlines + 0] += "Water:"
		if (gs.hwOptions["powermonitor"]):
			for t in self.__otherSensors:
				if (self.__sensors[t] == "flow"):
					lines[currentlines + 0] += "\t"
			lines[currentlines + 0] += "Power:"
		lines.append("")
		lines.append("")
		for t in self.__otherSensors:
			lines[currentlines + 2] += "{" + t + "}"
			if (len(t) > 7):
				t = t[:7]
			lines[currentlines + 1] += gs.getTabs("|{}".format(t), 1)

		template = ""
		for l in lines:
			template += l + "\n"
		self.__template = template + "\n"

	def setTimeRes(self, t = None):
		"""
		Change the interval at which measurements are taken. Interval must be
		at least 5 and at least 0.8 * amount of ds18b20 sensors since they
		need .75s for a single measurement. Choosing a low value may result in
		missed updates when a sensor is giving trouble.
		If no time argument is given, the system will default to the amount
		of ds18b20 sensors in seconds, with a minimum of 5 seconds.
		"""

		tempsensors = len(self.__tempMGR.getTdevList())
		if (t is None):
			if (tempsensors < 5):
				tr = 5
			else:
				tr = tempsensors
		else:
			try:
				t = int(t)
			except ValueError:
				return False
			if (t >= 5 and t >= tempsensors * 0.8):
				tr = float(t)
			else:
				return False
		self.__timeRes = tr
		self.__adcMGR.setLockTimeout(tr)

	def startMonitor(self):
		"""Use this function to start monitor to prevent more than 1 instance running at a time."""

		# Won't work. Discard I guess.
		running = False
		for t in gs.draadjes:
			if (t.name == "Monitor" and t.is_alive()):
				if (running):
					return
				running = True
		self.__checkConnected()
		self.__monitor()

	def __monitor(self):
		"""\t\tMain monitoring method. Will check on the status of all sensors every %timeRes seconds.
		Will also start methods/actions based on the sensor input."""

		# output format:
		# {timestamp}:
		# plant	|{group1}|{group2}|{group3}|{group4}|{group5}|{group6}
		# moist	|{soil1}	|{soil2}	|{soil3}	|{soil4}	|{soil5}	|{soil6}
		# water	|{water1}|{water2}|{water3}|{water4}|{water5}|{water6}
		# temp	|{temp1}	|{temp2}	|{temp3}	|{temp4}	|{temp5}	|{temp6}
		# Other sensors:
		#	Light:	Temps:													Water:	Power:
		#	|{ambient}|{sun}	|{shade}	|{ambient}|{cpu}	|{PSU}	|{total}	|{5v}		|{5v}		|{12v}	|{12v}
		#	|{light}	|{temp}	|{temp}	|{temp}	|{temp}	|{temp}	|{water}	|{power}	|{volt}	|{power}	|{volt}


		#	Indicate to user that the system is up and running.
		if (gs.hwOptions["lcd"]):
			self.__LCD.toggleBacklight()
		else:
			self.__statusLED.blinkSlow(3)

		try:
			while (gs.running):
				self.__loop()
		except KeyboardInterrupt:
			pass
		finally:
			for t in gs.wtrThreads:
				t.join()

	def __loop(self):

		data = dict()

		# Start collecting data.
		data["time"] = time.strftime("%H:%M:%S")

		# Get group data.
		for g in self.__groups.values():
			n = g.getName()
			m, t, f = g.getSensorData()
			data[g.groupname] = n
			data[g.mstName] = m
			if (gs.hwOptions["soiltemp"]):
				data[g.tempName] = t
			if (gs.hwOptions["flowsensors"]):
				data[g.flowName] = f
			if (not gs.running):
				return

		# Get data from other sensors.
		for sname in self.__otherSensors:
			data[sname] = self.requestData(name=sname)
			if sname.lower() == "psu":
				self.__checkPSUtemp(data[sname])

		# Outputting data to availabe outouts:
		self.__rawStats = data
		# if (gs.hwOptions["lcd"]):
		# 	self.LCD.updateScreen()
		# if (gs.hwOptions["ledbars"]):
		# 	for bar in self.__LEDbars.values():
		# 		bar.updateBar()

		# Formatting data.
		for name, value in data.items():
			if (name == "time"):
				continue
			data[name] = gs.getTabs("|" + str(value), 1)
		self.__currentstats = self.__template.format(**data)
		print(self.__currentstats)

		# Emitting event to alert devices of new data
		gs.ee.emit("hwMonitorDataUpdate")

		# Waiting for next interval of timeRes to start next itertion of loop.
		if (not gs.running) or gs.wait(self.__timeRes):
			return

	def __checkConnected(self):
		"""Checks and sets wether a sensor is connected to each channel of the ADC."""

		for g in self.__groups.values():
			lvl = self.__adc.getMeasurement(g.mstName)
			connected = lvl > self.__connectedCheckValue
			if (connected != g.connected):
				g.connected = not g.connected
				if (connected):
					logging.debug("{} enabled".format(g.groupname))
				else:
					logging.debug("{} disabled".format(g.groupname))

	def __checkPSUtemp(self, temp):

		if (temp > self.__maxPSUtemp):
			pass
			#doEmergencyThing()
		elif (temp > self.__fanToggleTemp):
			if (not self.__fan.state()):
				self.__fan.on()
		elif (temp < (self.__fanToggleTemp - 15)):
			if (self.__fan.state()):
				self.__fan.off()

	@abstractmethod
	def requestData(self, stype=None, name=None, formatted=None):
		return super().requestData(stype=stype, name=name, formatted=formatted)

	@abstractmethod
	def requestPower(self, *cur):
		return super().requestPower(cur)


class Monitor(ProtoThread):
	def run(self):
		logging.info("Starting thread{0}: {1}".format(self.threadID, self.name))
		gs.control.startMonitor()
		logging.info("Exiting thread{0}: {1}".format(self.threadID, self.name))
