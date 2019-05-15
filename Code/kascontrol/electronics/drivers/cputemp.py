#!/usr/bin/python3

# Author: J. Saarloos
# v0.1.00	09-05-2019

def getCPUtemp():
	"""Retruns the current CPU temperature in degrees C"""

	with open("/sys/class/thermal/thermal_zone0/temp", "r") as file:
		cputemp = file.readline()
	return (round(float(cputemp) / 1000, 1))
