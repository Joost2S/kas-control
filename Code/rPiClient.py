#!/usr/bin/python3
 
# Author: J. Saarloos
# v1.0	16-08-2017

"""
Client for Kas control software.
"""

import os 
import socket
import ssl
import sys
import webbrowser
new = 2 # open in a new tab, if possible



class shutdownError(Exception):
	pass

class kasControlClient(object):
	
	host = "kas-control"
	ipList = [("", "Login from home."),
				("", "Login from remote location."),
				("", "Login from test location.")
				]
	ipAddr = ""
	port = 7500
	sslSocket = None
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

	def makeConnection(self):
		try:
			s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		except socket.error as msg:
			print("Failed to create socket. Error code: " + str(msg[0]) + " , Error message : " + msg[1])
			sys.exit()
		print("Socket Created")

		self.sslSocket = ssl.wrap_socket(s, ssl_version = ssl.PROTOCOL_TLSv1_2)
		print("Socket secured")

		try:
			self.ipAddr[0] = socket.gethostbyname(self.host)
		except socket.gaierror:
			# could not resolve
			print("Hostname could not be resolved.")

		connected = False
		for ip in self.ipList:
			self.ipAddr = ip
			for i in range(5):
				try:
					print("Trying... {}:{}".format(self.ipAddr[0], self.port))
					self.sslSocket.connect((self.ipAddr[0], self.port))
					connected = True
					print(self.ipAddr[1])
					break
				except:
					self.port += 1
			if (connected):
				break
			else:
				self.port -= 5
		print("Receiving...")
		print(self.sslSocket.recv(256).decode())	# Get welcome message

	def client(self):
		try:
			while (True):
				if (self.loop):
					reply = input("Command: ")
				else:
					reply = self.args
				if (not reply.strip() == ""):
					rep = reply.split()
				else:
					print("No command given.")
					continue
				try:
					self.sslSocket.sendall(bytes(reply, "utf-8"))
				except ssl.SSLError:
					# Send failed
					print("Send failed")
					continue
				i, data = self.getData()
				if (str(rep[0]).lower() == "graph"):
					print(self.showgraph(data))
				else:
					print(data)
				print(i)
				if (str(rep[0]).lower() == "exit"):
					raise shutdownError
				if (not self.loop):
					break
		except KeyboardInterrupt:
			raise KeyboardInterrupt

	def getData(self):
		
		data = ""
		try:
			i = int(self.sslSocket.recv(256).decode())
			for j in range(i + 1):
				self.sslSocket.send(bytes("next", "utf-8"))
				data += str(self.sslSocket.recv(8192).decode())
		except ConnectionResetError:
			print("Connection reset error.")
			raise shutdownError
		except:
			print("Something happened.")
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
		except:
			return("Unknown error writing to file.")
		
#		open browser to display file.
		url = "file://" + self.htmlFile
		webbrowser.open(url,new=2)
		return("Done.")

	def shutdown(self):
		
		print("Closing socket...")
		self.sslSocket.close()
		sys.exit()

client = kasControlClient()
client.makeConnection()
try:
	client.client()
except KeyboardInterrupt:
	print("Shutdown by keyboard.")
except shutdownError:
	print("Exiting client....")
finally:
	client.shutdown()