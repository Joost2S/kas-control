#! /usr/bin/python

import logging
import RPi.GPIO as GPIO
import smtplib
import socket
import subprocess
import sys
import threading


import globstuff
import autowater as aw
import dbstuff as db
import sensor

gs = globstuff.globstuff


# Function for handling connections. This will be used to create threads.
def clientthread(conn, ip, port):
	logging.debug("Starting")
	if(gs.running):
		#Sending message to connected client
		try:
			conn.send(bytes("Welcome to the server. Type something and hit enter\n", "utf-8"))
		except socket.error:
			print("Send failed")
			gs.sLED.off()
			GPIO.cleanup()
			sys.exit()
		#infinite loop so that function does not terminate and thread does not end.
		while True:
			#Receiving from client
			data = conn.recv(1024).decode().split()
			print (data)
			print (len(data))
			conn.sendall(bytes(str(recv(data)).strip() + "\nEOF", "utf-8"))
			if (data[0] == "exit"):
				break
	conn.close()
	print("Connection closed with " + ip + ":" + port)
	logging.debug("Exiting")
	gs.sLED.off()
	GPIO.cleanup()
	sys.exit()
		
# Function to handle input from client and select the desired program or action.
def recv(data):
	# exit (-s, -r, -x)
	if (data[0] == "exit"):
		if (len(data) >= 2):
			if (data[1] == "-s"):
				stop()
				return("exiting server")
			elif (data[1] == "-r"):
				stop()
				reboot(True)
				return("rebooting rPi")
			elif (data[1] == "-x"):
				stop()
				reboot(False)
				return("shutting down rPi")
		else:
			return("exiting client")
		
	# huidig
	elif(data[0] == "huidig"):
		return(gs.currentstats)

	# temp
	elif (data[0] == "temp"):
		t = sensor.temp.get_temp()
		if (t == None):
			print("No sensor")
			return("Error, geen sensor.")
		return(t)

	# vocht
	elif (data[0] == "vocht"):
		if(len(data) >= 1):
			if(int(data[1]) >= 1 and int(data[1]) <= len(gs.ch_list)):
				for g in gs.ch_list:
					if (g.chan == int(data[1])):
						return(sensor.moisture.get_moisture(g, 1))
			else:
				return("Voer een correct groepnummer in. Groep 1 - " + str(len(gs.ch_list)))
		else:
			return("Voer ook een groepnummer in. (1 - " + str(len(gs.ch_list)) + ").")

	# data (start, end)
	elif (data[0] == "data"):
		if (len(data) >= 3):
			try:
				i = int(data[1])
				j = int(data[2])
			except:
				return("Voer 2 nummers in.")
			return(db.display_data(i, j))
		else:
			return("Geef 2 nummers op.")

	# help
	elif (data[0] == "help"):
		return(help())

	# threads
	elif (data[0] == "threads"):
		return(thread_info())

	# water
	elif (data[0] == "water"):
		msg = ""
		for line in gs.wateringlist:
			msg += line
		return(msg)

	#vtest
	elif (data[0] == "vtest"):
		aw.valvetest()
		return("Done")

	elif (data[0] == "ptest"):
		if (len(data) >= 2):
			try:
				t = float(data[1])
			except:
				return("Hoe lang moet er gepompt worden?.")
			aw.pumptest(t)
			return("Klaar.")
		return("Hoe lang moet er gepompt worden?.")

	# daylog
	elif (data[0] == "daylog"):
		db.daylog()
		return("Done.")

	# blink (x)
	elif (data[0] == "blink"):
		if (len(data) >= 2):
			try:
				i = int(data[1])
			except:
				return("Voer een getal in.")
			if (i >= 1):
				gs.sLED.blink(i)
				return("Geknipperd.")
			else:
				return("Voer een positief getal in.")
		else:
			return("Geef op hoe vaak te knipperen.")

	# set values for min and max soilmoisture level.
	elif (data[0] == "set"):
		if (len(data) >= 4):
			chan = 0
			value = 0
			try:
				if(int(data[2]) >= 1 and int(data[2]) <= int(len(gs.ch_list))):
					chan = int(data[2]) - 1
				chan = int(data[2]) - 1
			except:
				return ("Geef geldig kanaal op. (1 - " + str(len(gs.ch_list)) + ").")
			try:
				value = int(data[3])
			except:
				return ("Geef geldige waardes op")
			if (data[1] == "low"):
				gs.ch_list[chan].lowrange = value
				return ("Nieuwe waarde van lowrange op kanaal " + str(gs.ch_list[chan].chan) + ": " + str(gs.ch_list[chan].lowrange))
			elif (data[1] == "high"):
				gs.ch_list[chan].highrange = value
				return ("Nieuwe waarde van highrange op kanaal " + str(gs.ch_list[chan].chan) + ": " + str(gs.ch_list[chan].highrange))
			else:
				return ("Geef een geldige variabele op om te setten.")

	# get values for min, current and max soilmooisture level.
	elif (data[0] == "get"):
		reply = ""
		if (len(data) >= 2):
			try:
				chan = (int(data[1]) - 1)
			except:
				return ("Geef een geldig kanaal op. (1 - " + str(len(gs.ch_list)) + ").")
			reply += ("Waardes van groep " + str(gs.ch_list[chan].chan) + ":\n")
			reply += ("Low\t|Curr\t|High\n")
			reply += (str(gs.ch_list[chan].lowrange) + "\t|" + str(sensor.moisture.get_moisture(gs.ch_list[chan]), 0) + "\t|" + str(gs.ch_list[chan].highrange))
			return (reply)
		else:
			reply += ("grp\t|Low\t|Curr\t|High\n")
			for g in gs.ch_list:
				reply += str(g.chan) + "\t|" + (str(g.lowrange) + "\t|" + str(sensor.moisture.get_moisture(g, 0)) + "\t|" + str(g.highrange) + "\n")
			return(reply)

	# default reply if no valid command is entered.
	else:
		return("Geen geldig commando.")

# Function to stop this program.
def stop():
	gs.running = False
	sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM).connect(("127.0.0.1", gs.port))
	
# Function for restarting or shutting down the Raspberry Pi.
def reboot(moi):
	if (moi):
		command = "/usr/bin/sudo /sbin/shutdown -r now"
	else:
		command = "/usr/bin/sudo /sbin/shutdown -h now"
	process = subprocess.Popen(command.split(), stdout=subprocess.PIPE)
	output = process.communicate()[0]
	print(output)
	GPIO.cleanup()
	sys.exit()

# Helpfunction to remind the user what the various available actions are.
def help():
	helptext = ("commando's:\n")
	#exit
	helptext += ("exit\targ\tStop client\n\t-s\tStop client en server.\n\t-r\tHerstart het systeem.\n\t-x\tSluit het systeem af.\n")
	# huidig
	helptext += ("huidig\t\tGeeft een overzicht van de actuele temperatuur en licht-\n\t\thoeveelheid en de vochtigheid per groep.\n")
	#temp
	helptext += ("temp\t\tGeeft de actuele temperatuur.\n")
	#threads
	helptext += ("threads\t\tGeeft informatie over threads.\n")
	#mst
	helptext += ("mst\targ\tGeeft de actuele grondvochigheid.\n\tgroepnr\t1 - " + str(len(gs.ch_list)) + "\n")
	#data
	helptext += ("data\targ\tGeeft de data weer van de afgelopen tijd in dagen:\n\tStart\tWanneer begint de data\n\tEind\tLaatste meting, vaak 0.\n")
	#blink
	helptext += ("blink\targ x\tLaat de LED op de box x keer knipperen.")
	return(helptext)

# Gives information about the active threads.
def thread_info():
	tinfo = ("Number of threads active: " + str(threading.activeCount()) + "\n\n")
	main_thread = threading.main_thread()
	for t in threading.enumerate():
		if t is main_thread:
			continue
		tinfo += ("Thread name: " + str(t.getName()) + "\n")
	return(tinfo)

# Sends an email with the selecte message.
def sendmail(type):
	fromaddr = ""
	toaddr  = ""
	
	if (type == "lw"):
		subject = "Laag water"
		text = "Er is te weinig water in de regenton. Automatische bewatering is gestopt tot de regenton verder is gevuld"
	date = datetime.datetime.now().strftime( "%d/%m/%Y %H:%M" )


	msg = ("From: %s\nTo: %s\nSubject: %s\nDate: %s\n\n%s" % ( fromaddr, toaddr, subject, date, text ))

	# Credentials
	username = fromaddr
	password = ""

	# The actual mail send
	server = smtplib.SMTP("smtp.gmail.com:587")
	server.starttls()
	server.login(username,password)
	server.sendmail(fromaddr, toaddr, msg)
	server.quit()