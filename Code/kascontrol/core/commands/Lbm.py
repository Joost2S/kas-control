#!/usr/bin/python3

# Author: J. Saarloos
# v1.0.01	10-05-2019


from Code.kascontrol.globstuff import globstuff as gs
from .base.netCommand import NetCommand


class Lbm(NetCommand):

	def __init__(self):
		super(Lbm, self).__init__()
		self.command = "barmode"
		self.name = "LEDbar mode"
		self.args = "%mode%"
		self.guiArgs = {None: "Returns the current configuration.",
							"mode": {"bar" : "LEDs 1 - current light up.",
							          "dot": "Only the current LED lights up.",
							          "off": "Turns the LEDbar off"}}
		self.help = "Change LEDbar mode to 'bar', 'dot' or 'off'.\n"
		self.help += "If no argument is given, the current configuration is returned."

	def runCommand(self, args = None):

		if (args is not None):
			if (args[0] in self.guiArgs["mode"].keys()):
				gs.control.setLEDbarMode(args[0])
				return("LEDbars set to: {}".format(args[0]))
			return("Not a valid mode for LEDbars.")
		msg = ""
		for item in gs.control.getLEDbarConfig():
			if (isinstance(item, str)):
				msg += item + ":\n"
			else:
				for name in ["|Name", "|Displayed", "|Low", "|High"]:
					msg += gs.getTabs(name)
				msg += "\n"
				for row in item:
					for val in row:
						msg += gs.getTabs("|" + val)
					msg += "\n"
		return(msg)
