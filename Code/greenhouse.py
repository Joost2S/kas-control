#!/bin/sh
#! /usr/bin/python

import logging
import RPi.GPIO as GPIO
import socket
import sys
import threading
import time

import dbstuff as db
import globstuff
import autowater as aw
import network
import sensor
#import board

gs = globstuff.globstuff
GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)
logging.basicConfig(level=logging.DEBUG, format="[%(levelname)s] (%(threadName)-10s) %(message)s",)

# GPIO inputs:
GPIO.setup(gs.float_switch, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
GPIO.add_event_detect(gs.float_switch, GPIO.RISING, callback=(gs.fltdev.lwstart), bouncetime=1000)

#		for i in self.ledlist:
#			GPIO.setup(ledlist[i], GPIO.OUT)
for i in gs.ch_list:
	GPIO.setup(i.valve, GPIO.OUT)
GPIO.setup(gs.pump, GPIO.OUT)
GPIO.setup(gs.sigLEDlow, GPIO.OUT)
GPIO.setup(gs.sigLEDhigh, GPIO.OUT)


#	Check if the yearly databases exist already.
db.yearStart()

#	Indicate to user that the system is up and running.
gs.sLED.on()
time.sleep(3)
gs.sLED.off()

#	 Start recording the sensor data to the DB.
dlog = threading.Thread(name = "Datalog", target = db.datalog, args=())
dlog.setDaemon(True)
dlog.start()

#	Start monitoring the soil and other sensors.
dmon = threading.Thread(name = "Monitor", target = aw.monitor, args=())
dmon.setDaemon(True)
dmon.start()

#	Open up a network connection to start the server.
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
print("Socket created")

try:
	s.bind((gs.host, gs.port))
except socket.error as msg:
	print("Bind failed. Error Code : " + str(msg[0]) + " Message " + msg[1])
	sys.exit()
print("Socket bind complete")

s.listen(10)
print("Socket now listening")
i = 1
while (gs.running):
	try:
		# Wait to accept a connection - blocking call.
		conn, addr = s.accept()

		# Display client information.
#			if(addr[0] != '127.0.0.1'):
		print("Connected with " + addr[0] + ":" + str(addr[1]))

		t = threading.Thread(name = "client-" + str(i), target = network.clientthread, args = (conn, addr[0], str(addr[1])))
		t.start()
		i = i + 1
	except KeyboardInterrupt:
		s.close()
		GPIO.cleanup()
		sys.exit()
