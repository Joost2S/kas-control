#!/usr/bin/python3

# Author: J. Saarloos
# v1.0.01	10-05-2019


from Code.kascontrol.globstuff import globstuff as gs
from .base.netCommand import NetCommand


class Pst(NetCommand):

	def __init__(self):
		super(Pst, self).__init__()
		self.command = "pinstats"
		self.name = "Pin stats"
		self.args = "%pin"
		self.help = "Returns a list of stats for the given pin.\n"
		self.help += "Format must be 'dpp', d = device number, p = pin nuber.\n"
		self.help += "Example: pinstats 1b5"

	def runCommand(self, client, args=None):

		if (args is not None):
			if (len(args[0]) == 3):

				# Checking device number
				check, dev = self.isInt(args[0][0])
				if (not check):
					return("Wrong device number. (0 - {0})".format(str(len(gs.mcplist) - 1)))
				if (not (0 <= dev < len(gs.mcplist))):
					return("Device does not exist. (0 - {0})".format(str(len(gs.mcplist) - 1)))

				# Checking bank letter
				if (not (args[0][1] == "a" or args[0][1] == "b")):
					return("Bank does not exist. (a or b)")

				# Checking pin number
				check, nr = self.isInt(args[0][2])
				if (not check):
					return("Not a pin number. (0 - 7)")
				if (not (0 <= nr <= 7)):
					return("Pin number out of range. (0 - 7)")

				# If all checks clear, return requested data.
				blah = "Device addr: {}\n".format(hex(gs.getPinDev(args[0]).devAddr))
				return(blah + gs.getPinDev(args[0]).getPinStats(gs.getPinNr(args[0])))
			else:
				return("0Incorrect format: " + str(args[0]))
		else:
			return("Enter pin number.")
