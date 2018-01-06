#!/usr/bin/python3
 
# Author: J. Saarloos
# v1.0	16-08-2017

from abc import ABCMeta, abstractmethod
import csv
from datetime import datetime
import logging
import RPi.GPIO as GPIO
import socket
import ssl
import threading
import time

import globstuff
import autowater as aw

gs = globstuff.globstuff

class netCommand(object):
	"""Base object for commands available through the network interface."""

	__metaclass__ = ABCMeta
	 
	# command
	@property
	def command(self):
		return(self.__command)
	@command.setter
	def command(self, command):
		self.__command = command
	# name
	@property
	def name(self):
		return(self.__name)
	@name.setter
	def name(self, name):
		self.__name = name
	# helpShort
	@property
	def args(self):
		return(self.__args)
	@args.setter
	def args(self, args):
		self.__args = args
	# helpLong
	@property
	def help(self):
		return(self.__help)
	@help.setter
	def help(self, help):
		self.__help = help
	
#	args = {}
#	[name] : (optional, values, priority, description)
#	optional:	bool
#	values:		{[name] : (type, values)}
#	type:			min/max, absolute
#	values:		(,)
#	priority:	order in which to search
#	description:	description for helpfile

	@abstractmethod
	def __init__(self):
		pass
		#return super().__init__(**kwargs)
	
	@abstractmethod
	def runCommand(self, args = None):
		pass
	
	def isInt(self, intgr):
		try:
			i = int(intgr)
		except (TypeError, ValueError):
			return(False, "Wrong input. Int expected. " + str(intgr))
		return(True, i)

	def isFloat(self, flt):
		try:
			f = float(flt)
		except (TypeError, ValueError):
			return(False, "Wrong input. Float expected. " + str(flt))
		return(True, f)
	
	def returnHelp(self):
		return(self.help)

class ext(netCommand):

	def __init__(self):
		self.command = "exit"
		self.name = "Exit"
		self.args = "'-s'\t'-r'\t'-x'"
		self.help = "Arguments:\n\n"
		self.help += "None\tExit the client.\n"
		self.help += "-s\tStop the software.\n"
		self.help += "-r\tReboot the RaspBerry Pi.\n"
		self.help += "-x\tShutdown the Raspberry Pi."
		self.argList = {"-s" : "Stopping Kas Control software.",
							"-r" : "Rebooting rPi.",
							"-x" : "Shutting down rPi."}

	def runCommand(self, args = None):
		if (args is not None):
			a = args[0]
			if (a in self.argList.keys()):
				gs.shutdownOpt = a
				self.stop()
				raise shutdownError(self.argList[a])
		return("Exiting client.")


	def stop(self):
		"""Function to stop this program."""

		gs.running = False
		sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		ssock = ssl.wrap_socket(sock, ssl_version = ssl.PROTOCOL_TLSv1_2)
		ssock.connect(("127.0.0.1", gs.port))
		ssock.close()

class cur(netCommand):

	def __init__(self):
		self.command = "cur"
		self.name = "Current stats"
		self.args = ""
		self.help = "Returns the current value of all the sensors."

	def runCommand(self, args = None):
		return(gs.currentstats)

class tem(netCommand):

	def __init__(self):
		self.command = "temp"
		self.name = "Temperature"
		self.args = "%name%"
		self.help = "Takes a measurement and returns the current temperature(s).\n"
		self.help += "Give the name of a sensor for just that temperature."

	def runCommand(self, args = None):

		msg = ""
		if (args is not None):
			for arg in args:
				for td in gs.tDevList:
					if (td.name.lower() == arg):
						t = td.getTemp()
						if (t == None):
							t = "Could not get temp"
						msg += "{0}:\t{1}\n".format(str(td.name), str(t))
			if (msg == ""):
				return("Temp device not found.")
		else:
			for td in gs.tDevList:
				t = td.getTemp()
				if (t == None):
					t = "Could not get temp"
				msg += "{0}:\t{1}\n".format(str(td.name), str(t))
			if (msg == ""):
				return("Error, no sensor. Please check the log for more information.")
		return(msg)

class mst(netCommand):

	def __init__(self):
		self.command = "mst"
		self.name = "Moisture level"
		self.args = "%groupnumber"
		self.help = []
		self.help.append("Takes a measurement of the given sensor and returns the soilmoisture level.\n")
		self.help.append("Available sensors:\n")
		self.help.append(self.listConnected())

	def returnHelp(self):
		self.help[-1] = self.listConnected()
		h = ""
		for line in self.help:
			h += (line)
		return(h)

	def runCommand(self, args = None):

		if (args is not None):
			check, group = self.isInt(args[0])
			if (not check):
				return("Enter a correct groupnumber. (1 - " + str(len(gs.ch_list)) + ")")
			if (group >= 1 and group <= len(gs.ch_list)):
				for g in gs.ch_list:
					if (g.chan == (group - 1)):
						if (g.connected):
							return(str(gs.adc.getMeasurement(g.name, 1)))
						else:
							return("Sensor " + str(g.chan + 1) + " is disconnected. No value available.")
			else:
				return("Enter a correct groupnumber. (1 - " + str(len(gs.ch_list)) + ")")
		else:
			return("Enter a groupnumber. (1 - " + str(len(gs.ch_list)) + ").")

	def listConnected(self):
		list = ""
		conn = False
		for g in gs.ch_list:
			if (g.connected):
				list += str(g.name) + ", "
				conn = True
		if (not conn):
			return("No sensors available.")
		return(list[:-2])

class dat(netCommand):

	def __init__(self):
		self.command = "data"
		self.name = "Data"
		self.args = "%start, %end%"
		self.help = "Displays the last entries from the logging database.\n\n"
		self.help += "%start\tamount of days ago you want to start the log.\n"
		self.help += "%end\twhen you want to stop the log. If not entered 0 will be assumed.\n"
		self.help += "%start and %end% can be entered in fractions."

	def runCommand(self, args = None):
		start = 0.0
		end = 0.0
		if (args is not None):
			if (len(args) > 1):
				check, end = self.isFloat(args[1])
				if (not check):
					return("Wrong value for %end. " + end)
			check, start = self.isFloat(args[0])
			if (not check):
				return("Wrong value for %start. " + start)
			return(gs.db.display_data(start,end))
		else:
			return("Please enter a start time.")

class utm(netCommand):

	def __init__(self):
		self.command = "uptime"
		self.name = "Uptime"
		self.args = ""
		self.help = "Returns a summary of the boot time,\n"
		self.help += "current time and the uptime of the system."

	def runCommand(self, args = None):
		return(self.uptime())
	
	def uptime(self):
		"""Returns the boottime and current uptime."""

		reply = ("Boottime:\t" + str(datetime.fromtimestamp(float(gs.boottime)).strftime("%Y-%m-%d %H:%M:%S")) + "\n")
		reply += ("Current time:\t" + str(datetime.now().strftime("%Y-%m-%d %H:%M:%S")) + "\n")
		diff = time.time() - gs.boottime
		tDiff = gs.timediff(diff)
		reply += ("Uptime:\t\t" + str(tDiff[0]) + "d, " + str(tDiff[1]) + ":" + str(tDiff[2]) + ":" + str(tDiff[3]))
		return(reply)

class hlp(netCommand):

	def __init__(self):
		self.command = "help"
		self.name = "Help"
		self.args = "%command%"
		self.help = "Returns a list of all the commands available if no command is entered.\n"
		self.help += "If a valid command is entered as argument a more detailed description\n"
		self.help += "of how the given command works is returned."

	def runCommand(self, args):
		commlist = args[0]
		if (len(args) == 1):
			commandlist = "Name\t\tCommand\t\tArguments\n"
			for comm in sorted(commlist.keys()):
				commandlist += "\n{0}{1}{2}".format(self.getTabs(commlist[comm].name + ":"), self.getTabs(commlist[comm].command), commlist[comm].args)
			return(commandlist)
		else:
			arg = args[1]
			if (arg in commlist.keys()):
				text = commlist[arg].name + "\n\n"
				text += commlist[arg].returnHelp()
				return(text)
			else:
				return(str(arg) + "\tNo such command exists. Cannot give information.")

	def getTabs(self, name):
		if (len(name) < 8):
			return(name + "\t\t")
		else:
			return(name + "\t")

class thr(netCommand):

	def __init__(self):
		self.command = "threads"
		self.name = "Threads"
		self.args = ""
		self.help = "Returns a list of the currently running threads of this software."
		
	def runCommand(self, args = None):
		"""Gives information about the active threads."""

		tinfo = ("Number of threads active: " + str(threading.activeCount()) + "\n\n")
		main_thread = threading.main_thread()
		for t in gs.draadjes:
			if (t.isAlive()):
				tinfo += ("Thread" + str(t.threadID) + " name: " + str(t.getName()) + "\n")
		for t in gs.wtrThreads:
			if (t.isAlive()):
				tinfo += ("Thread" + str(t.threadID) + " name: " + str(t.getName()) + "\n")
		return(tinfo)

class wtr(netCommand):

	def __init__(self):
		self.command = "water"
		self.name = "Waterlist"
		self.args = "%channel%"
		self.help = "Returns a list of the last times each channel has watered\n"
		self.help += "and the time in between. Doesn't funtion correctly yet."

	def runCommand(self, args = None):

		data = {}
		results = ""
		watered = False

		# Sorting data per group
		for i in range(len(gs.ch_list)):
			data[i] = []
		with open(gs.wateringlist, "r", newline = "") as filestream:
			file = csv.reader(filestream, delimiter = ",")
			for line in file:
				data[int(line[0])].append(line)

		for g in gs.ch_list:
			results += "Channel {0} ({1}):\n".format(g.chan + 1, len(data[g.chan]))
			if (len(data[g.chan]) == 0):
				results += "\tNothing yet.\n"
			else:
				for i in range(len(data[g.chan])):
					if (i > 0):
						zeit = gs.timediff(int(data[g.chan][i][1]) - int(data[g.chan][i - 1][1]))
						results += ("\t\tTime since previous watering: {0}d, {1}:{2}:{3}\n".format(str(zeit[0]), str(zeit[1]), str(zeit[2]), str(zeit[3])))
					results += ("\t{0} - Watered for {1} seconds.\n".format(str(datetime.fromtimestamp(int(data[g.chan][i][1])).strftime("%Y-%m-%d %H:%M:%S")), str(data[g.chan][i][2])))
				zeit = gs.timediff(time.time() - int(data[g.chan][-1][1]))
				results += ("\t\tTime since last watering: {0}d, {1}:{2}:{3}\n".format(str(zeit[0]), str(zeit[1]), str(zeit[2]), str(zeit[3])))
				watered = True
				
		if (not watered):
			results = "System hasn't watered yet.\n"
		for g in gs.ch_list:
			if (g.watering):
				results += "\nSystem is currently watering on channel {0}.".format(str(g.chan + 1))
		return(results)

class vts(netCommand):

	def __init__(self):
		self.command = "vtest"
		self.name = "Valve test"
		self.args = "%valve%\t%time%"
		self.help = "Can be used to test the valves. Only works if system is in testmode."
		self.help += "Arguments:\n"
		self.help += "None\tCycle through all valves.\n"
		self.help += "%valve%\tEnter the number of the valve to test. (1 - {0})\n".format(str(len(gs.ch_list)))
		self.help += "%time%\tEnter the time in seconds (max 60) to leave the valve open.\n"
		self.help += "\tOnly works if a valvenumber has been entered. If not entered, 5 will be used."

	def runCommand(self, args = None):
		if (gs.testmode):
			if (args is None):
				for g in gs.ch_list:
					print("valve" + str(g.chan))
					g.valveOn()
					time.sleep(1)
					g.valveOff()
					time.sleep(0.5)
				return("Test done.")
			else:
				t = 5
				if (len(args) > 1):
					check, t = self.isInt(args[1])
					if (not check):
						return("Please enter a valid time.")
					if (not (t > 1 and t <= 60)):
						return("Invalid amount of time. (1 - 60)")
				check, v = self.isInt(args[0])
				if (not check):
					return("Enter valid valvenumber. (1 - {0})".format(str(len(gs.ch_list))))
				if (not (v > 0 and v <= len(gs.ch_list))):
					return("Enter valid valvenumber. (1 - {0})".format(str(len(gs.ch_list))))
				gs.ch_list[v - 1].valveOn()
				time.sleep(t)
				gs.ch_list[v - 1].valveOff()
				return("Valve test done.")
		else:
			return("Please turn on Testmode before doing a valvetest.")

class wts(netCommand):

	def __init__(self):
		self.command = "wtest"
		self.name = "Water test"
		self.args = "%channels%\t%time%"
		self.help = "Use this to test the watering system.\n"
		self.help += "The test has 2 components: First, water is given on all entered channels.\n"
		self.help += "Second, water is given 1 channel at a time.\n\n"
		self.help += "Arguments:\n"
		self.help += "channels:\tEnter the number of the channel(s) you want. 'all' for all available channels.\n"
		self.help += "time:\tThe last argument given is assumed to be the time. Default time is 5 seconds.\n"

	def runCommand(self, args = None):
		if (gs.testmode):
			if (args == None):
				g, t = self.defaultParams()
				gs.pump.demo(g, t)
				return("Default watering test done.")
			else:
				t = 5
				valves = []
				check, t = self.isInt(args[-1])
				if (not check):
					return("Please enter a valid time.")
				if (not (t > 1 and t <= 60)):
					return("Invalid amount of time. (1 - 60)")
				if (len(args) >= 2 and args[0] == "all"):
					g, t = self.defaultParams(t)
					gs.pump.demo(g, t)
					return("Done watering test for {0} seconds per valve on all valves.".format(str(t)))
				for va in args[:-1]:
					check, v = self.isInt(va)
					if (not check):
						return("Enter valid valvenumber. (1 - {0})".format(str(len(gs.ch_list))))
					if (not (v > 0 and v <= len(gs.ch_list))):
						return("Enter valid valvenumber. (1 - {0})".format(str(len(gs.ch_list))))
					valves.append(gs.ch_list[v - 1])
				gs.pump.demo(valves, t)
			return("Done watering test for {0} seconds per valve.".format(str(t)))
		else:
			return("Please turn on Testmode before testing the watering hardware.")

	def defaultParams(self, t = None):
		valves = []
		for g in gs.ch_list:
			valves.append(g)
		if (t is not None):
			return(valves, t)
		return(valves, 5)
		
class tsm(netCommand):

	def __init__(self):
		self.command = "testmode"
		self.name = "Testmode"
		self.args = "'on'\t'off'"
		self.help = "Turn the testmode on or off.\n"
		self.help += "Testmode disables database recording and watering.\n"
		self.help += "Measurements from the monitor will continue."

	def runCommand(self, args = None):
		if (args is not None):
			if (args[0] == "on"):
				gs.testmode = True
				gs.pump.disable()
				gs.db.pauze = True
				return("Testmode enabled.")
			elif (args[0] == "off"):
				gs.testmode = False
				gs.pump.enable()
				gs.db.pauze = False
				return("Testmode disabled.")
			return("Please specify 'on' or 'off'.")
		return(gs.testmode)

class spf(netCommand):

	def __init__(self):
		self.command = "spoof"
		self.name = "Spoof"
		self.args = "%settings"
		self.help = "Use this to spoof adc data when yours isn't working\n"
		self.help += "or if you don't have plants to test with.\n"
		self.help += "Isn't working yet."

	def runCommand(self, args = None):
		return("Not yet implemented.")

class flt(netCommand):

	def __init__(self):
		self.command = "flt"
		self.name = "Float switch"
		self.args = ""
		self.help = "Returns a brief overview of the settings related to the float switch."

	def runCommand(self, args = None):

		return("fltdev pinstate: " + str(gs.fltdev.getStatus()) + " low_water state: " + str(gs.fltdev.low_water))

class dlg(netCommand):

	def __init__(self):
		self.command = "daylog"
		self.name = "Daylog"
		self.args = ""
		self.help = "Run this to make an MMAdb if you haven't enabled it."

	def runCommand(self, args = None):
		if (not gs.db.mma):
			gs.db.mma = True
			gs.db.daylog()
			return("Done.")
		else:
			return("Function already enabled.")
	
class pst(netCommand):

	def __init__(self):
		self.command = "pinstats"
		self.name = "Pin stats"
		self.args = "%pin"
		self.help = "Returns a list of stats for the given pin.\n"
		self.help += "Format must be 'dpp', d = device number, p = pin nuber.\n"
		self.help += "Example: pinstats 1b5"

	def runCommand(self, args = None):
		
		if (args is not None):
			if (len(args[0]) == 3):

				# Checking device number
				check, dev = self.isInt(args[0][0])
				if (not check):
					return("Wrong device number. (0 - {0})".format(str(len(gs.mcplist) - 1)))
				if (not (dev >= 0 and dev < len(gs.mcplist))):
					return("Device does not exist. (0 - {0})".format(str(len(gs.mcplist) - 1)))
				
				# Checking bank letter
				if (not (args[0][1] == "a" or args[0][1] == "b")):
					return("Bank does not exist. (a or b)")
				
				# Checking pin number
				check, nr = self.isInt(args[0][2])
				if (not check):
					return("Not a pin number. (0 - 7)")
				if (not (nr >= 0 and nr <= 7)):
					return("Pin number out of range. (0 - 7)")
				
				# If all checks clear, return requested data.
				blah = "Device addr: {}\n".format(hex(gs.getPinDev(args[0]).devAddr))
				return(blah + gs.getPinDev(args[0]).getPinStats(gs.getPinNr(args[0])))
			else:
				return("0Incorrect format: " + str(args[0]))
		else:
			return("Enter pin number.")
		
class set(netCommand):

	def __init__(self):
		self.command = "set"
		self.name = "Set"
		self.args = "'low'\t'high'\t%channel\t%value"
		self.help = "Use this command to set a new value for what moisture level is wanted.\n"
		self.help += "Arguments:\n"
		self.help += "trigger\t'low'\tcontrols when the pumping starts. Select how dry the soil can become.\n"
		self.help += "\t'high'\tcontrols how wet the soil may become.\n"
		self.help += "channel\t\tWhich channel to change.\n"
		self.help += "value\t\tSelect the value for the channel. (200 - 4000)\n"

	def runCommand(self, args = None):
		"""set values for min and max soilmoisture level."""

		trig = ""
		chan = 0
		value = 0
		if (args is not None):
			if (not (args[0] == "low" or args[0] == "high")):
				return("Enter 'low' or 'high' as first argument.")
			trig = args[0]
			if (len(args) > 1):
				check, chan = self.isInt(args[1])
				if (not check):
					return("Enter valid channel. (1 - {0})".format(str(len(gs.ch_list))))
				elif (not (0 < chan <= len(gs.ch_list))):
					return("Enter valid channel. (1 - {0})".format(str(len(gs.ch_list))))
				chan -= 1
				if (len(args) > 2):
					check, value = self.isInt(args[2])
					if (not check):
						return("Enter valid value.")
					if (trig == "low"):
						if (not (200 <= value < gs.ch_list[chan].hightrig)):
							return("Invalid value. ({0} - {1})".format(200, gs.ch_list[chan].hightrig - 1))
					if (trig == "high"):
						if (not (gs.ch_list[chan].lowtrig < value <= 4000)):
							return("Invalid value. ({0} - {1})".format(gs.ch_list[chan].lowtrig + 1, 4000))
					gs.setfile(trig[0], chan, value)
					if (trig == "low"):
						value = gs.ch_list[chan].lowtrig
					if (trig == "high"):
						value = gs.ch_list[chan].hightrig
					return ("New value of {0}range on channel {1}: {2}".format(trig, str(gs.ch_list[chan].chan), value))
		return("Enter arguments to set.")
		
class get(netCommand):

	def __init__(self):
		self.command = "get"
		self.name = "Get"
		self.args = "%channel"
		self.help = "Returns the min, current and max values for each soil sensor\n"
		self.help += "or just the selected soil sensor.\n"
		self.help += "Arguments:\n"
		self.help += "channel\tenter a channel number if the values of only one soil sensor needs to be displayed."

	def runCommand(self, args = None):
		"""Get values for min, current and max soilmoisture level."""

		reply = ""
		if (args is not None):
			check, chan = self.isInt(args[0])
			if (not check):
				return("Enter valid channel. (1 - " + str(len(gs.ch_list)) + ").")
			elif (not (0 < chan <= len(gs.ch_list))):
				return("Enter valid channel. (1 - " + str(len(gs.ch_list)) + ").")
			chan -= 1
			reply += ("Values of group " + str(gs.ch_list[chan].chan) + ":\n")
			reply += ("Low\t|Now\t|High\n")
			reply += (str(gs.ch_list[chan].lowtrig) + "\t|" + str(gs.adc.getMeasurement(gs.ch_list[chan].name, 0)) + "\t|" + str(gs.ch_list[chan].hightrig))
			return (reply)
		else:
			reply += ("Group\t|Low\t|Now\t|High\n")
			for g in gs.ch_list:
				reply += str(g.chan + 1) + "\t|" + (str(g.lowtrig) + "\t|" + str(gs.adc.getMeasurement(g.name, 0)) + "\t|" + str(g.hightrig) + "\n")
			return(reply)

class gra(netCommand):

	def __init__(self):
		self.command = "graph"
		self.name = "Graph"
		self.args = "%start\t%end%\t%type%"
		self.help = []
		self.help.append("Makes a graph of the wanted data in an html file.")
		self.help.append("The file can be found in the same folder the database is stored.")
		self.help.append("Arguments:\n")
		self.help.append("Start\tStart time of the graph in days ago. Fractions accepted.")
		self.help.append("End\tOptional. End time of the graph in days ago. Fractions accepted. 0 if not entered.")
		self.help.append("Type\tOptional. Enter the name(s) of the sensors you want. Names available:")
		self.help.append(self.listNames())

	def returnHelp(self):
		self.help[-1] = self.listNames()
		h = ""
		for line in self.help:
			h += (line + "\n")
		return(h)

	def listNames(self):
		text = ""
		for f in gs.db.fields:
			text += (f[0] + ", ")
		return(text[:-2])

	def runCommand(self, args = None):

		msg = ""
		if (args is not None):
			start = 0.0
			end = 0.0
			names = []
			print(args)
			# Checking for valid start time.
			check, start = self.isFloat(args[0])
			if (not check):
				return("Enter numeric start time.")
			elif (not (start > 0.0)):
				return("Enter valid start time.")
			# Checking for valid end time and sensor names.
			if (len(args) > 1):
				check, en = self.isFloat(args[1])
				if (check):
					if (en < start):
						end = en
					else:
						return("Enter valid end time.")
					if (len(args) > 2):
						names = self.checkNames(args[2:])
				# No endtime, checking for sensor names.
				else:
					names = self.checkNames(args[1:])
				if (names == None):
					# Names where entered, but none where valid so no graph can be made.
					return("No valid name entered. Check 'help graph' for valid names.")
				elif (len(names) == 0):
					# No names where entered. Passing None to the makeGraph script so all sensor output will be shown.
					names = None
				msg = gs.wgraph.makeGraph(start, end, names)
			else:
				msg = gs.wgraph.makeGraph(start)
			if (msg == None):
				msg = "Done."
			return(msg)
		else:
			return("Enter arguments for graph creation.")

	def checkNames(self, args):
		"""Check the entered names and return only the ones with a valid name."""

		names = []
		for arg in args:
			found = False
			for f in gs.db.fields:
				if (arg == f[0].lower()):
					names.append(arg)
					found = True
					break
			if (not found):
				for t in gs.db.tdev:
					if (arg == f[0].lower()):
						names.append(arg)
						break
		if (len(names) == 0):
			return(None)
		return(names)

class log(netCommand):

	def __init__(self):
		self.command = "log"
		self.name = "Log"
		self.args = "%entries%\t%level%"
		self.help = "Shows the log entries.\n"
		self.help += "Arguments:\n"
		self.help += "Entries\tShow the last n log entries. Default is 100.\n"
		self.help += "Level\t'debug' or 'error' Can be entered for entries of just one severity level.\n"
		self.help += "Otherwise all entries will be shown."
		self.argList = {"info" : "INFO", "debug" : "DEBUG", "warning" : "WARNING", "error" : "ERROR", "critical" : "CRITICAL"}


	def runCommand(self, args = None):
		
		a = ""
		lines = 100
		output = []
		msg = ""
		
		# Getting settings from arguments
		if (args is not None):
			check, i = self.isInt(args[0])
			if (not check):
				if (args[0] not in self.argList.keys()):
					return("Invalid argument.")
				else:
					a = args[0]
			elif (not i > 0):
				return("Please enter positive number.")
			else:
				lines = i

				if (a == "" and len(args) > 1):
					if (args[1] not in self.argList.keys()):
						return("Invalid argument.")
					else:
						a = args[1]

		# Loading in file
		try:
			with open(gs.logfile, "r") as file:
				for line in file:
					if (a == ""):
						output.append(line)
					elif (line.find(self.argList[a]) is not -1):
							output.append(line)
		except FileNotFoundError:
			logging.warning("Logfile not found...")
			msg = ("File not found. No log to show.")
			output = -1
		except IOError:
			msg = ("IO error. Unable to retrieve log.")
			output = -1

		if (not output == -1):
			if (len(output) == 0):
				msg = "No entries found."
			if (len(output) > lines):
				for line in output[(0 - lines):]:
					msg += str(line)# + "\n"
			else:
				for line in output[(0 - lines):]:
					msg += str(line)# + "\n"

		return(msg)

class Server(object):
	
	# commands
	@property
	def commands(self):
		return(self.__commands)
	@commands.setter
	def commands(self, commands):
		self.__commands = commands
	# sslSock
	@property
	def sslSock(self):
		return(self.__sslSock)
	@sslSock.setter
	def sslSock(self, sslSock):
		self.__sslSock = sslSock
	# clientNr
	@property
	def clientNr(self):
		return(self.__clientNr)
	@clientNr.setter
	def clientNr(self, clientNr):
		self.__clientNr = clientNr

	def __init__(self):

		self.clientNr = 1
		self.commands = {}
		comms = [ ext(), cur(), tem(),
					 mst(), dat(), utm(),
					 hlp(), thr(), wtr(),
					 vts(), wts(), tsm(),
					 spf(), flt(), dlg(),
					 pst(), set(), get(),
					 gra(), log() ]

		for command in comms:
			self.commands[command.command] = command
		del(comms)


	def makeSocket(self):
		"""Create a network connection to start the server."""

		try:
			s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		except socket.error as msg:
			logging.critical("Failed to create socket. Error code: " + str(msg[0]) + " , Error message : " + msg[1])
			raise shutdownError("Socket creation failed.")
		print("Socket created")
		
		self.sslSock = ssl.wrap_socket(s,
												server_side = True,
												ssl_version = ssl.PROTOCOL_TLSv1_2,
												certfile = gs.dataloc + "cert.pem",
												keyfile = gs.dataloc + "key.pem")
		print("Socket secured.")
		gs.socket = self.sslSock

		while(1):
			if (gs.port == 7505):
				gs.port = 7500
			try:
				self.sslSock.bind((gs.host, gs.port))
				break
			except ssl.SSLError as msg:
				logging.warning("Bind failed. Error Code : " + str(msg[0]) + " Message " + str(msg[1]))
			except OSError as msg:
				logging.warning("Failed bind. " + str(msg))
			gs.port += 1
		print("Socket bind complete")
		
		self.sslSock.listen(10)
		print("Socket now listening")
		

	def serverLoop(self):
		"""Main loop, waiting to accept new connections."""
		
		try:
			while (gs.running):
				# Wait to accept a connection - blocking call.
				conn, addr = self.sslSock.accept()
								
				if (addr[0] != "127.0.0.1"):
					try:
						nt = client(gs.getThreadNr(), "client-" + str(self.clientNr), args = (conn, addr[0], str(addr[1]), self))
						nt.start()
						gs.draadjes.append(nt)
					except ConnectionResetError:
						logging.debug("Connection reset with client-" + str(self.clientNr))
				elif (gs.shutdownOpt is not None):
					raise shutdownError
				self.clientNr += 1
		except KeyboardInterrupt:
			raise KeyboardInterrupt

	def clientthread(self, conn, ip, port):
		"""Function for handling connections. This will be used by the network thread."""
		
		logging.info("Connected with " + ip + ":" + port)
		# Sending welcome message to connected client
		try:
			conn.send(bytes("Welcome to Kas control. Type 'help' for available commands.\n", "utf-8"))
		except ssl.SSLError:
			print("Send failed")

		while (gs.running):
			# Receiving data from client
			data = conn.recv(256).decode().split()
			logging.info((len(data), data))
			print(data)

			# Processing data
			i = 0
			try:
				i, msg = self.handleData(data)
			except shutdownError as text:
				msg = [str(text) + "\nEOF"]
			except:
				logging.error("Some error occured while executing net command {}".format(str(data[0])))
				msg = ["Unknown error occured while executing command.\nEOF"]
			
			# Sending reply back to client
			conn.sendall(bytes(str(i), "utf-8"))
			for j in range(i + 1):
				conn.recv()
				conn.sendall(bytes(msg[j], "utf-8"))
			if (str(data[0]).lower() == "exit"):
				break
		conn.close()
		logging.info("Connection closed with " + ip + ":" + port)

	def handleData(self, data):
		"""Handles incoming data and returns a reply for the client."""

		command = str(data[0]).lower()
		if (command in self.commands):
			args = None
			if (len(data) > 1):
				args = []
				for item in data[1:]:
					args.append(str(item).lower())
				if (command == "help"):
					args = (self.commands, args[0].lower())
			elif (command == "help"):
				args = (self.commands,)
			try:
				msg = str(self.commands[command].runCommand(args)) + "\n\n\n\n"
			except shutdownError as text:
				raise shutdownError(text)

			# Removing trailing white lines
			msg = msg.splitlines()
			for line in reversed(msg):
				if (line.strip()):
					break
				else:
					msg = msg[:-1]
			length = 0
			i = 0
			text = [""]
			if (len(msg) == 0):
				text = ["No reply generated."]

			# Parting message if too large.
			else:
				for line in msg:
					length += (len(line) + 2)
					text[i] += str(line) + "\n"
					if (length > 7500):
						i += 1
						length = 0
						text.append("")
				text[i] += "EOF"
			return(i, text)
		else:
			return(0, ["Not a valid command. " + command])
	
class client(globstuff.protoThread):
	def run(self):
		print("Starting thread{0}: {1}".format(self.threadID, self.name))
		self.args[3].clientthread(self.args[0], self.args[1], self.args[2])
		print("Exiting thread{0}: {1}".format(self.threadID, self.name))

class shutdownError(Exception):
	pass