#! /usr/bin/python

import glob
import logging
import spidev


# Setup for the adc connected with spi
spi0 = spidev.SpiDev()
spi0.open(0,0)
spi0.max_speed_hz = 1000000
spi1 = spidev.SpiDev()
spi1.open(0,1)
spi1.max_speed_hz = 1000000


def _readChannel(channel, spichan):
	spi = spi0
	if (spichan == 1):
		spi = spi1
	data = 0
	for i in range(0, 15):
		adc = spi.xfer2([96+(4*channel), 0, 0])
		data += (adc[1]<<4) + (adc[2]>>4)
	data /= 15
	return(4095 - int(data))


class moisture:
	def get_moisture(group, rtype):
		mlevel = _readChannel(group.devchan, group.spichan)
		if(rtype == 0):
			return(round(mlevel, 1))
		elif(rtype == 1):
			return(moisture.__convertToPrec(mlevel, 1))

	def __convertToPrec(data, places):
		m = ((data * 100) / float(4095))
		m = round(m, places)
		return(str(m) + "%")



class light:
	# Get the current amount of light
	def get_light():
		llevel = _readChannel(0, 0)
		return(round(llevel, 1))



class temp:
	#	Get the current temperature from the sensor
	def get_temp():
		try:
	#		fileobj = open('/sys/bus/w1/devices/28-000006d218ac/w1_slave','r')
			fileobj = open(tdev,'r')
			lines = fileobj.readlines()
			fileobj.close()
		except:
			return(None)
				# get the status from the end of line 1 
		status = lines[0][-4:-1]
		# if the status is ok, get the temperature from line 2
		if (status == "YES"):
			tempstr = lines[1][-6:-1]
			tempval = float(tempstr)/1000
			t = float("%.1f" % tempval)
			if (t == 85.0):
				return(None)
			return(t)
		else:
			return(None)
		
	#	Get the name of the installed temperature sensor
	def get_tdev():
		devicelist = glob.glob('/sys/bus/w1/devices/28*')#28-000007c0d519
		if len(devicelist) == 0:
			logging.debug('No temp device found.')
			return None
		else:
			return(devicelist[0] + '/w1_slave')


tdev = temp.get_tdev()