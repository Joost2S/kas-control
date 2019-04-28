#!/usr/bin/python3

# Author: J. Saarloos
# v1.02.00	18-10-2018

"""
Client for Kas control software.
"""

import json
import logging
import os
from pymitter import EventEmitter
import socket
import ssl
import sys
import webbrowser
new = 2  # open in a new tab, if possible

ee = EventEmitter()


class ShutdownError(Exception):
	pass


class ConnectionFailedError(Exception):
	pass


class KasControlClient(object):

	host = "kas-control"
	ipList = {"home-prod": "192.168.1.163",
				"remote": "123.456.789.012",
				"home-dev": "192.168.1.167"
				}
	ipAddr = ""
	port = 7500
	sslSocket = None
	clientType = ""
	dir = ""
	htmlFile = ""
	loop = True
	args = ""

	def __init__(self):

		args = sys.argv
		if (len(args) > 1):
			self.loop = False
			for a in args[1:]:
				self.args += str(a) + " "
		dir_path = os.path.dirname(os.path.realpath(__file__))
		self.dir = dir_path.replace("\\", "/")
		self.htmlFile = self.dir + "graph.html"
		self.ipName = "home-prod"

	def makeConnection(self):

		try:
			s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		except socket.error as msg:
			print("Failed to create socket. Error code: " + str(msg[0]) + " , Error message : " + msg[1])
			sys.exit()
		print("Socket Created")

		self.sslSocket = ssl.wrap_socket(s, ssl_version=ssl.PROTOCOL_TLSv1_2)
		print("Socket secured")

		# try:
		# 	self.ipAddr = socket.gethostbyname(self.host)
		# except socket.gaierror:
		# 	# could not resolve
		# 	print("Hostname could not be resolved.")

		connected = False
		self.ipAddr = self.ipList[self.ipName]
		for i in range(1):
			try:
				print("Trying... {}:{}".format(self.ipAddr, self.port))
				self.sslSocket.connect((self.ipAddr, self.port))
				connected = True
				break
			except (ConnectionRefusedError, TimeoutError):
				self.port += 1
			if (connected):
				break
		if (not connected):
			self.port = 7500
			ee.emit("ConnectionFailed")
			raise ConnectionFailedError
		print("Receiving...")
		# Get welcome message
		print(self.sslSocket.recv(64).decode())
		self.sslSocket.send(bytes(self.clientType, "utf-8"))
		ack = self.sslSocket.recv(3).decode()
		if (ack != "ACK"):
			self.port = 7500
			ee.emit("ConnectionRefused")
			raise ConnectionRefusedError
		ee.emit("ConnectionEstablished")

	def command(self, args=None):

		try:
			if (args is not None):
				command = args
			elif (self.args is not None):
				command = self.args
			else:
				return
			if (self.clientType == "TERMINAL"):
				if (command.strip() != ""):
					cmd = str(command.split()[0]).lower()
				else:
					return("No command given.")
			elif (self.clientType == "GUI"):
				# print("command sent:", command)
				if (isinstance(command, list)):
					cmd = str(command[0]).lower()
					command = json.dumps(command)
				else:
					return("No command given.")
			try:
				self.sslSocket.sendall(bytes(command, "utf-8"))
				print("Sent command:", command)
			except ssl.SSLError:
				return("Send failed")
			i, data = self.getData()
			if (cmd == "graph"):
				return(self.showgraph(data))
			elif (cmd == "exit"):
				print("Exiting...")
				raise ShutdownError
			else:
				return(data)
		except ShutdownError:
			if (self.clientType == "TERMINAL"):
				raise ShutdownError
			elif (self.clientType == "GUI"):
				return ("Shutting down.")
		except KeyboardInterrupt:
			raise KeyboardInterrupt
		# finally:
		# 	print(data)

	def getData(self):

		data = ""
		try:
			i = int(self.sslSocket.recv(16).decode())
			for j in range(i):
				print("Receiving packet {} of {}.".format(j+1, i))
				self.sslSocket.send(bytes("next", "utf-8"))
				data += str(self.sslSocket.recv(8192).decode())
			if (self.clientType == "GUI"):
				data = json.loads(data)
				# print("data:", data)
		except ConnectionResetError:
			print("Connection reset error.")
			raise ShutdownError
		except ValueError:
			self.shutdown()
			# todo: trigger event
			return (0, data)
		return(i, data)

	def showgraph(self, data):

		try:
			with open(self.htmlFile, "wb") as text_file:
				print("writing to file")
				text_file.write(bytes(data[:-6], "utf-8"))
		except FileNotFoundError:
			logging.debug("File not found: " + self.htmlFile)
			return("File not found. Unable to make graph.")
		except IOError:
			logging.debug("IO error trying to write to file: " + self.htmlFile)
			return("IO error. Unable to make graph.")

		# open browser to display file.
		url = "file://" + self.htmlFile
		webbrowser.open(url, new=2)
		return("Done.")

	def shutdown(self):

		print("Closing socket...")
		self.sslSocket.close()


def connect(cl):

	while (True):
		try:
			cl.makeConnection()
			return True
		except ConnectionFailedError:
			if (input("Failed to setup connection. Retry?: ") != "y"):
				cl.shutdown()
				return False
		except ConnectionRefusedError:
			cl.shutdown()
			raise ShutdownError


if (__name__ == "__main__"):

	client = KasControlClient()
	client.clientType = "TERMINAL"
	try:
		if (connect(client)):
			while (True):
				try:
					comm = input("Command: ")
					print(client.command(args=comm))
					if (client.loop):
						continue
				except ShutdownError:
					raise ShutdownError
		else:
			print("Shutting down.")
	except KeyboardInterrupt:
		print("Shutdown by keyboard.")
	except ShutdownError:
		print("Exiting client....")
	finally:
		client.shutdown()
		sys.exit()
