#!/usr/bin/python3

# Author: J. Saarloos
# v1.2.02	17-05-2019


# TODO: import hashlib
import json
import logging
import socket
import ssl

from Code.kascontrol.globstuff import globstuff as gs
from Code.kascontrol.utils.errors import ShutdownError
from Code.kascontrol.utils.protothread import ProtoThread
from .commands.Adp import Adp
from .commands.Cth import Cth
from .commands.Cur import Cur
from .commands.Dat import Dat
from .commands.Ext import Ext
from .commands.Flt import Flt
from .commands.Gas import Gas
from .commands.Get import Get
from .commands.Hlp import Hlp
from .commands.Lbm import Lbm
from .commands.Lcd import Lcd
from .commands.Led import Led
from .commands.Log import Log
from .commands.Mst import Mst
from .commands.Pst import Pst
from .commands.Pwr import Pwr
from .commands.Rmp import Rmp
from .commands.Rnp import Rnp
from .commands.Sen import Sen
from .commands.Set import Set
from .commands.Spf import Spf
from .commands.Stl import Stl
from .commands.Tem import Tem
from .commands.Thr import Thr
from .commands.Tsm import Tsm
from .commands.Utm import Utm
from .commands.Vts import Vts
from .commands.Wtr import Wtr
from .commands.Wts import Wts


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

		self.supportedClientTypes = ["GUI", "TERMINAL"]
		self.__makeSocket()
		self.clientNr = 1
		self.commands = {}
		self.sslSock = None
		comms = [Ext, Cur, Tem,
					Mst, Dat, Utm,
					Hlp, Thr, Wtr,
					Vts, Wts, Tsm,
					Spf, Flt, Pst,
					Set, Get, Log,
					Adp, Rmp, Rnp,
					Cth, Sen, Gas]
		if (gs.hwOptions["powermonitor"]):
			comms.extend([Led, Stl,
					Pwr])
		if (gs.hwOptions["ledbars"]):
			comms.extend([Lbm])
		if (gs.hwOptions["lcd"]):
			comms.extend([Lcd])
		for command in comms:
			self.commands[command().command] = command
		gs.server = self

	def __makeSocket(self):
		"""Create a network connection to start the server."""

		try:
			s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		except socket.error as msg:
			logging.critical("Failed to create socket. Error message : " + str(msg))
			raise ShutdownError("Socket creation failed.")
		print("Socket created")

		self.sslSock = ssl.wrap_socket(s,
												server_side=True,
												ssl_version=ssl.PROTOCOL_TLSv1_2,
												certfile=gs.dataloc + "cert.pem",
												keyfile=gs.dataloc + "key.pem")
		print("Socket secured.")

		while(1):
			if (gs.port == 7505):
				gs.port = 7500
			try:
				self.sslSock.bind((gs.host, gs.port))
				break
			except ssl.SSLError as msg:
				logging.warning("Bind failed. Error message " + str(msg))
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
				logging.info("New connection from: {}:{}".format(*addr))

				if (addr[0] != "127.0.0.1"):
					try:
						nt = Client(gs.getThreadNr(), "client-" + str(self.clientNr), args = (conn, addr[0], str(addr[1])))
						nt.start()
						gs.draadjes.append(nt)
					except ConnectionResetError:
						logging.debug("Connection reset with client-" + str(self.clientNr))
					# except Exception as e:
					# 	logging.exception("Bad client.")
				elif (gs.shutdownOpt is not None):
					raise ShutdownError
				self.clientNr += 1
		except KeyboardInterrupt:
			raise KeyboardInterrupt

	def clientthread(self, conn, ip, port):
		"""Function for handling connections. This will be used by the network thread."""

		# Sending welcome message to connected client
		try:
			conn.send(bytes("Welcome to Kas control. Type 'help' for available commands.\n", "utf-8"))
			clientType = conn.recv(32).decode()
			if (clientType not in self.supportedClientTypes):
				conn.send(bytes("NOT", "utf-8"))
				conn.close()
				logging.debug("Client of type {} is not supported. Connection closed.")
				return
			else:
				conn.send(bytes("ACK", "utf-8"))
		except ssl.SSLError:
			print("Send failed")
			return
		logging.info("{}-client connected with {}:{}".format(clientType, ip, port))
		if (clientType == "TERMINAL"):
			self.terminalClientThread(conn)
		elif (clientType == "GUI"):
			self.guiClientThread(conn)
		conn.close()
		logging.info("Connection closed with " + ip + ":" + port)

	def guiClientThread(self, conn):

		# incoming data structure:
		# [command, {args}]

		# outgoing data structure:
		# {"succes": Bool,
		#  "data": any format}

		while (gs.running):
			# Receiving data from client
			data = json.loads(conn.recv(1024).decode())

			i, returnData = self.handleDataForGui(data)
			conn.sendall(bytes(str(i), "utf-8"))
			for chunk in returnData:
				conn.recv(4)
				conn.sendall(bytes(chunk, "utf-8"))
			if (str(data[0]).lower() == "exit"):
				break

	def handleDataForGui(self, indata):

		command = str(indata[0]).lower()
		if (command not in self.commands):
			returnData = {"succes": False, "data": "Invalid command."}
		else:
			args = None
			if (len(indata) > 1):
				args = indata[1]
			try:
				s, outdata = self.commands[command]("GUI").runCommand(args)
				returnData = {"succes": s, "data": outdata}
			except ShutdownError as text:
				raise ShutdownError(text)
		jsonFile = json.dumps(returnData)
		chunkSize = 8192
		chunks = []
		count = 0
		for i in range(0, len(jsonFile), chunkSize):
			chunks.append(jsonFile[i:i+chunkSize])
			count += 1
		return(count, chunks)

	def terminalClientThread(self, conn):

		while (gs.running):
			# Receiving data from client
			data = conn.recv(256).decode().split()
			logging.info((len(data), data))

			# Processing data
			i = -1
			try:
				i, msg = self.handleDataForTerminal(data)
			except ShutdownError as text:
				msg = [str(text) + "\nEOF"]
			# except:
			# 	logging.error("Some error occured while executing net command {}".format(str(data[0])))
			# 	msg = ["Unknown error occured while executing command.\nEOF"]

			# Sending reply back to client
			conn.sendall(bytes(str(i+1), "utf-8"))
			for j in range(i + 1):
				conn.recv()
				conn.sendall(bytes(msg[j], "utf-8"))
			if (str(data[0]).lower() == "exit"):
				break

	def handleDataForTerminal(self, data):
		"""Handles incoming data and returns a reply for the client."""

		command = str(data[0]).lower()
		if (command not in self.commands):
			return(0, ["Not a valid command. " + command])
		args = None
		if (len(data) > 1):
			args = []
			for item in data[1:]:
				args.append(str(item).lower())
			if (command == "help"):
				args = (self.commands, args[0])
		elif (command == "help"):
			args = (self.commands,)
		try:
			check, msg = self.commands[command]("TERMINAL").runCommand(args)
		except ShutdownError as text:
			raise ShutdownError(text)

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


class Client(ProtoThread):

	def run(self):

		print("Starting thread{0}: {1}".format(self.threadID, self.name))
		gs.server.clientthread(self.args[0], self.args[1], self.args[2])
		print("Exiting thread{0}: {1}".format(self.threadID, self.name))
