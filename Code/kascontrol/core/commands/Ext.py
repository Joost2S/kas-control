#!/usr/bin/python3

# Author: J. Saarloos
# v1.0.01	10-05-2019


import logging
import socket
import ssl

from Code.kascontrol.globstuff import globstuff as gs
from Code.kascontrol.core.network import ShutdownError
from .base.netCommand import NetCommand


class Ext(NetCommand):

	def __init__(self):
		super(Ext, self).__init__()
		self.command = "exit"
		self.name = "Exit"
		self.args = "'-s'\t'-r'\t'-x'"
		self.guiArgs = {"-s": "Stopping Kas Control software.",
							"-r": "Rebooting rPi.",
							"-x": "Shutting down rPi."}
		self.help = "Arguments:\n\n"
		self.help += "None\tExit the client.\n"
		self.help += "-s\tStop the software.\n"
		self.help += "-r\tReboot the RaspBerry Pi.\n"
		self.help += "-x\tShutdown the Raspberry Pi."
		self.argList = {"-s": "Stopping Kas Control software.",
							"-r": "Rebooting rPi.",
							"-x": "Shutting down rPi."}

	def runCommand(self, client, args=None):
		if (args is not None):
			a = args[0]
			if (a in self.argList.keys()):
				gs.shutdownOpt = a
				self.stop()
				raise ShutdownError(self.argList[a])
		return("Exiting client.")

	@staticmethod
	def stop():
		"""Function to stop this program."""

		logging.debug("Shutting down by network command.")
		gs.running = False
		sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		ssock = ssl.wrap_socket(sock, ssl_version=ssl.PROTOCOL_TLSv1_2)
		ssock.connect(("127.0.0.1", gs.port))
		ssock.close()
