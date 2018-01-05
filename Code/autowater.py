#! /usr/bin/python

import logging
import RPi.GPIO as GPIO
import threading
import time

import globstuff
import network
import sensor

gs = globstuff.globstuff

# Main monitoring method. Will check on the status of all sensors every 15 seconds.
# Will also start methods/actions based on the sensor input.
def monitor():
	logging.debug("Starting - monitor")
	while (True):
		start = time.time()
		output = (time.strftime("%H:%M:%S") + ":\n" +"Temp\t|lght")
		for g in gs.ch_list:
			output += ("\t|ch" + str(g.chan))
		t = sensor.temp.get_temp()
		if (t == None):
			logging.debug("No temperature sensor")
			output += ("\nFaal")
		else:
			output += ("\n" + str(t))
		l = sensor.light.get_light()
		output += ("\t|" + str(l))
		check_connected()
		for g in gs.ch_list:
			if (g.connected == True and g.watering == False):
				lvl = sensor.moisture.get_moisture(g, 1)
				output += ("\t|" + str(lvl))
				if (not(gs.fltdev.low_water)):
					if (sensor.moisture.get_moisture(g, 0) <= g.lowrange):
						g.below_range += 1
						if (g.below_range >= 5):
							g.watering = True
							t = threading.Thread(name = "Watering ch" + str(g.chan), target = watering, args = (g,))
							t.setDaemon(True)
							t.start()
							g.below_range = 0
			elif (g.watering == True):
				output += ("\t|Bezig")
			elif (g.connected == False):
				output += ("\t|N/C")
			else:
				output += ("\t|WTF")
		print(output)
		gs.currentstats = output
		time.sleep(gs.time_res-(time.time()-start))
	logging.debug("Exiting - monitor")

#	controls the actual watering. Watering is intermittent to allow the water to drain a little
#	to get a better measurement.
def watering(g):
	start = time.time()
	i = 1
	while (g.watering and not gs.fltdev.low_water):
		g.pumping = True
		GPIO.output(g.valve, GPIO.HIGH)
		time.sleep(0.1)
		GPIO.output(gs.pump, GPIO.HIGH)
		gs.sLED.on()
		for j in range(0, int(18/i)):
			if (gs.fltdev.low_water):
				break
			time.sleep(1)
		g.pumping = False
		if (not checkpump() or gs.fltdev.low_water):
			GPIO.output(gs.pump, GPIO.LOW)
			gs.sLED.off()
			time.sleep(0.1)
			if (gs.fltdev.low_water):
				g.watering = False
		GPIO.output(g.valve, GPIO.LOW)
		if (not g.watering):
			break
		time.sleep(10)
		if (sensor.moisture.get_moisture(g, 0) >= g.highrange):
			g.watering = False
	end = int(time.time() - start)
	msg = ("Done watering on channel " + str(g.chan) + ", watered for " + str(end) + " seconds.")
	logging.debug(msg)
	gs.addToWlist(msg + "\n")

#	this method performs a check to see if the pump can be turned off or wether another group is currently using it.
def checkpump():
	blah = False
	for g in gs.ch_list:
		if (g.pumping):
			blah = True
	return blah
	
# checks and sets wether a sensor is connected to each channel of the ADC.
def check_connected():
	for g in gs.ch_list:
		lvl = sensor.moisture.get_moisture(g, 0)
		if (lvl >= 5 and lvl < 4085):
			g.connected = True
		else:
			g.connected = False

def valvetest():
	for g in gs.ch_list:
		print("valve" + str(g.chan))
		GPIO.output(g.valve, GPIO.HIGH)
		time.sleep(1)
		GPIO.output(g.valve, GPIO.LOW)
		time.sleep(0.5)

def pumptest(t):
		GPIO.output(gs.pump, GPIO.HIGH)
		time.sleep(t)
		GPIO.output(gs.pump, GPIO.LOW)