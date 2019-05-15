#!/usr/bin/python3

# Author: J. Saarloos
# v1.0.01	10-05-2019


from Code.kascontrol.globstuff import globstuff as gs
from .base.netCommand import NetCommand


class Lcd(NetCommand):

	def __init__(self):
		super(Lcd, self).__init__()
		self.command = "lcd"
		self.name = "LCD settings"
		self.args = "%setting\t%arguments%"
		self.help = "Change settings for the LCD display.\n"
		self.help += "%setting:\n"
		self.help += "light:\tToggle the backlight on or off.\n"
		self.help += "sensors:\tEnter the names of the sensors to be displayed.\n"
		self.help += "\tMore names can de entered than can be displayed.\n"
		self.help += "\tFormat must be: 'sensorname:displayname'.\n"
		self.help += "\tOr: 'sensorname'. Last 4 characters will be used as displayname.\n"
		self.help += "\tEnter command 'sensors' to get a full list of available sensors.\n"
		self.help += "msg:\tEnter a message to be displayed. Set a time in seconds to display the message.\n"
		self.help += "\tFollowed by the message.\n"
		self.help += "mode:\tTo be implemented in the future.\n"
		self.help += "\tsensor:\tDisplays latest sensor readouts of selected sensors.\n"
		self.help += "\ttoggle\tToggle the LCD on or off.\n"
		self.help += "\n"

	def runCommand(self, args = None):

		if (args is not None):
			if (not args[0] in ["light", "sensors", "msg", "mode"]):
				return("Not a valid LCD command.")
			if (args[0] == "light"):
				state = gs.control.LCD.toggleBacklight()
				return("Turned backlight state to {}.".format(state))
			if (args[0] == "sensors"):
				if (len(args) > 1):
					pass
					# extract names and display names from args.
				return("Enter names of sensors to display on the LCD.")
			if (args[0] == "msg"):
				if (len(args) > 1):
					try:
						t = int(args[1])
						del(args[1])
					except ValueError:
						t = 15
					if (len(args) > 1):
						msg = ""
						for arg in args[1:]:
							msg += arg + " "
						gs.control.LCD.message(msg[:-1], t)
						return("Message set.")
		return("Please enter correctly formatted command. Enter 'help {}' for more information.".format(self.command))
