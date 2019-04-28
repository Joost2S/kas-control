#!/usr/bin/python3

# Author: J. Saarloos
# v1.0.00	24-04-2019


from datetime import datetime
import time

from ...globstuff import globstuff as gs
from .base.netCommand import NetCommand


class Wtr(NetCommand):

	def __init__(self):
		super(Wtr, self).__init__()
		self.command = "water"
		self.name = "Waterlist"
		self.args = "%container%, %entries%"
		self.help = "Returns a list of the last times each channel has watered\n"
		self.help += "and the time in between.\n"
		self.help += "container:\tNumber of the container you want to check.\n"
		self.help += "entries:\tHow many events to display per container. Default is 20."

	def runCommand(self, client, args = None):

		# get plantname
		# get last x entries for each plant
		data1 = None
		data2 = None
		txt = ""
		amount = None

		# Extract and validate user input:
		if (args is not None):
			if (len(args) > 0):
				check, container = self.channelCheck(args[0])
				if (not check):
					return(container)
				if (len(args) > 1):
					try:
						if (int(args[1]) >= 1):
							amount = int(args[1])
						else:
							raise ValueError
					except ValueError:
						return("Invalid amount.")
				# Collect and validate requested data:
				data1, data2 = gs.db.getWaterEvents(container, amount)
				if (data1 is None):
					return("No plant assigned to container {}.".format(container))
			else:
				data1, data2 = gs.db.getWaterEvents()
				if (data1 is None):
					return("No plants currently assigned.")

		if (client == "GUI"):
			return({"plants": data1, "data": data2})

		# Process data:
		for i, plant in enumerate(data1):
			if (data2[i] is not None):
				txt += "\nLast {} watering events for plant {}:\n".format(len(data2[i]), plant[1])
				for j, row in reversed(data2[i]):
					if (j > 0):
						zeit = gs.timediff(int(row[0]) - int(data2[j - 1][0]))
						txt += "\t\tTime since previous watering: {0}d, {1}:{2}:{3}\n".format(*zeit)
					txt += "\tTime\t\t|Duration\t|Amount\n"
					txt += "\t{}|{}|{}\n".format(gs.getTabs(datetime.fromtimestamp(int(row[0])).strftime("%Y-%m-%d %H:%M:%S")),
							 gs.getTabs(round(row[1], 1)), gs.getTabs(row[2]))
				zeit = gs.timediff(time.time() - int(data2[-1][0]))
				txt += "\t\tTime since last watering: {0}d, {1}:{2}:{3}\n".format(*zeit)
			else:
				txt += "\nPlant {} has not been watered yet.\n".format(plant[0])
		return(txt)
