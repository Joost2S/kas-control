#!/usr/bin/python3

# Author: J. Saarloos
# v1.0.01	10-05-2019


from Code.kascontrol.globstuff import globstuff as gs
from .base.netCommand import NetCommand


class Rnp(NetCommand):

	def __init__(self):
		super(Rnp, self).__init__()
		self.command = "renameplant"
		self.name = "Rename plant"
		self.args = "%currentName\t%newName"
		self.guiArgs = {"current_name": "The name of the plant you want to change",
		                "new_name": "The name you want the plant to be changed to."}
		self.help = "Alter the name of a plant.\n"
		self.help += "Only allows current plants to be changed"

	def runCommand(self, client, args = None):
		if (args is not None):
			pass
		return("Please enter correctly formatted command. Enter 'help {}' for more information.".format(self.command))
