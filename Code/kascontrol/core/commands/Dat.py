#!/usr/bin/python3

# Author: J. Saarloos
# v1.0.01	10-05-2019


import time

from Code.kascontrol.globstuff import globstuff as gs
from .base.netCommand2 import NetCommand


class Dat(NetCommand):

	def __init__(self, client):
		super(Dat, self).__init__(client)
		self.command = "data"
		self.name = "Data"
		self.args = "%start\t%end%\t%names | types | group%"
		self.guiArgs = {
			"fetchmethod": [{"type": str,
								  "any": ["timestamp", "relativeTime"]}],
			"start": [{"type": float},
						 {"type": str, "match": "min"}
						 ],
			"end": [{"type": float},
						{"type": None}
					  ],
			"sensors": [{"type": list,
							 "constrain": "all_members_in",
							 "constrain_value": gs.control.getSensors().keys()
							 }],
		}
			# "timestamp": {"start": None,
			# 									"end": None},
			# 				"relativeTime": {"start": None,
			# 										"end": None},
			# 				"sensors": [],
			# 				"groups": [],
			# 				"types": []
			# 				}
		self.help = "Displays the last entries from the logging database.\n\n"
		self.help += "%start\tamount of days ago you want to start the log.\n"
		self.help += "%end%\twhen you want to stop the log. If not entered 0 will be assumed.\n"
		self.help += "%start and %end% can be entered in fractions.\n"
		self.help += "%names%\tEnter the name(s) of the sensors you want read.\n"
		self.help += "%-types%Read all sensors of type(s).\n"
		self.help += "%--group%Enter container number to get associated sensors read.\n"
		self.help += "Choose max one from names, types and group.\n"
		self.help += "Examples:\n"
		self.help += "'data 5'\n"
		self.help += "Get data from all sensors over last 5 days.\n\n"
		# TODO: Support plantname
		self.help += "'data 4 2 --2'\n"
		self.help += "Get data from the sensors from container 2 over the last 4 days.\n"
		self.help += "'data 0.75 0.25 ambientl out_shade totalw'\n"
		self.help += "Get data from the 3 sensors from 18h - 6h ago.\n"
		self.help += "'data 7 -temp pwr'\n"
		self.help += "Get data from all temp and power sensors over the last week."

	def getTERMargs(self, args=None):

		arguments = dict()
		arguments["fetchmethod"] = "relativeTime"
		if (args is None or len(args) == 0):
			return(False, "Please enter a start time.")
		try:
			# If 2nd argument is convertable to float, it is assumed te be the end time
			# and will be removed so checking for names can start at the same point in the array.
			end = float(args[1])
			arguments["end"] = end
			del(args[1])
		except ValueError:
			pass
		if (args[1][0] == "-"):
			if (args[1][1] == "-"):
				# 2 dashes: group selected
				check, container = self.containerCheck(args[1][2:])
				if (not check):
					return(False, container)
				arguments["containers"] = [container]
			else:
				# 1 dash: types selected
				arguments["types"] = list()
				arguments["types"].append(args[1][1:])
				if (len(args) > 2):
					for a in args[2:]:
						arguments["types"].append(a)
		# No dashes: sensors selected
		else:
			arguments["sensors"] = args[1:]
		check, start = self.isFloat(args[0])
		arguments["start"] = start
		if not check:
			return False, "Wrong value for %start. " + start
		return True, arguments

	def run(self, args):
		if "containers" in args.keys() and args["containers"] is not None:
			data = gs.db.getSensorData(args["start"], args["end"], group=args["containers"])
		elif "sensors" in args.keys() and args["sensors"] is not None:
			data = gs.db.getSensorData(args["start"], args["end"], types=args["sensors"])
		elif "types" in args.keys() and args["types"] is not None:
			data = gs.db.getSensorData(args["start"], args["end"], names=args["types"])
		else:
			data = gs.db.getSensorData(args["start"], args["end"])
		if data is None:
			return False, "No data found."
		return True, data

	def termReturn(self, data):
		txt = ""
		template = str(gs.getTabs("{}") * len(data[0])) + "\n"
		print(template)
		print(data)
		# txt += template.format(*data[0])
		for row in data[1:]:
			txt += template.format(*row)
		return True, txt

	def guiRun(self, args):

		start = None
		end = None
		sensors = None
		groups = None
		types = None
		if ("timestamp" in args.keys()):
			start = args["timestamp"]["start"]
			end = args["timestamp"]["end"]
		elif ("relativeTime" in args.keys()):
			if (args["relativeTime"]["start"] == "min"):
				start = "min"
				end = None
			else:
				start = time.time() - float(args["relativeTime"]["start"])*3600*24
				end = time.time() - float(args["relativeTime"]["end"])*3600*24
		else:
			return("No timestamps were given.")
		if ("sensors" in args.keys()):
			if (len(args["sensors"]) > 0):
				sensors = args["sensors"]
		elif ("groups" in args.keys()):
			if (len(args["groups"]) > 0):
				groups = args["groups"]
		elif ("types" in args.keys()):
			if (len(args["types"]) > 0):
				types = args["types"]
		data = gs.db.getSensorData(start, end, group=groups, types=types, names=sensors)
		if (data is None):
			return("No data found.")
		return(data)
