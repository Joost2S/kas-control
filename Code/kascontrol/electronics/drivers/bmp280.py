#!/usr/bin/python3

# Author: J. Saarloos
# v0.01.02	26-05-2019

"""
BMP280 can use SPI master in mode 0 and 3. Since the defalt in rPi is
mode 0, that will be used.
Datasheet: https://ae-bst.resource.bosch.com/media/_tech/media/datasheets/BST-BMP280-DS001.pdf
"""


class BMP280(object):

	REGMAP = {
		"temp_xlsb": 0xFC,
		"temp_lsb": 0xFB,
		"temp_msb": 0xFA,
		"press_xlsb": 0xF9,
		"press_lsb": 0xF8,
		"press_msb": 0xF7,
		"config": 0xF5,
		"crl_meas": 0xF4,
		"status": 0xF3,
		"reset": 0xE0,
		"id": 0xD0
	}
	calibration = dict()
	t_fine = int()

	def __init__(self, spi):
		super(BMP280, self).__init__()
		self.spi = spi
		self.t_fine = 0
		for i in range(26):
			self.REGMAP["calib"+str(i)] = 0x88 + i
		self.__setCalibration()
		# TODO: read ID register to confirm device is online if 0x58 and
		#  set device to SPI


	def __setCalibration(self):
		cal = dict()
		for i in range(24):
			cal[i] = self.spi.xfer(self.REGMAP["calib"+str(i)])
		for i in range(0, 6, 2):
			self.calibration["dig_T"+str((i/2)+1)] = self.__getCalValue(cal[i], cal[i + 1])
		for i in range(6, 24, 2):
			self.calibration["dig_P"+str(((i-6)/2)+1)] = self.__getCalValue(cal[i], cal[i + 1])

	def __getCalValue(self, b0, b1):

		return int()

	def config(self):
		masks = {
			"t_sb": 0b11100000,
			"filter": 0b00011100,
			"spi3w_en": 0b00000001
		}

	def ctrl_meas(self):
		masks = {
			"osrs_t": 0b11100000,
			"osrs_p": 0b00011100,
			"mode": 0b00000011
		}

	def read(self):
		resp = self.spi.readbytes(3)
		if (resp[0] != 255):
			value = resp[1] + resp[2]
			byte1 = resp[0] << 16
			byte2 = resp[1] << 8
			byte3 = resp[2]
			bits = byte1 + byte2 + byte3

	def compensateTemp(self, adc_T):
		"""Compensation formulae derived from code in appendix 8.1 of datasheet"""

		dig_T1 = self.calibration["dig_T1"]
		dig_T2 = self.calibration["dig_T2"]
		dig_T3 = self.calibration["dig_T3"]
		var1 = (adc_T / 16384.0 - dig_T1 / 1024.0) * dig_T2
		var2 = ((adc_T / 131072.0 - dig_T1 / 8192.0)
		        * (adc_T / 131072.0 - dig_T1 / 8192.0)) * dig_T3
		self.t_fine = var1 + var2
		T = (var1 + var2) / 5120.0
		return T

	def compensatePress(self, adc_P):

		dig_P1 = self.calibration["dig_P1"]
		dig_P2 = self.calibration["dig_P2"]
		dig_P3 = self.calibration["dig_P3"]
		dig_P4 = self.calibration["dig_P4"]
		dig_P5 = self.calibration["dig_P5"]
		dig_P6 = self.calibration["dig_P6"]
		dig_P7 = self.calibration["dig_P7"]
		dig_P8 = self.calibration["dig_P8"]
		dig_P9 = self.calibration["dig_P9"]

		var1 = self.t_fine / 2.0 - 64000.0
		var2 = var1 * var1 * dig_P6 / 32768.0
		var2 = var2 + var1 * dig_P5 * 2.0
		var2 = (var2 / 4.0) + (dig_P4 * 65536.0)
		var1 = (dig_P3 * var1 * var1 / 524288.0 + dig_P2 * var1) / 524288.0
		var1 = (1.0 + var1 / 32768.0) * dig_P1
		if var1 == 0.0:
			return 0
		# avoid exception caused by division by zero
		p = 1048576.0 - adc_P
		p = (p - (var2 / 4096.0)) * 6250.0 / var1
		var1 = dig_P9 * p * p / 2147483648.0
		var2 = p * dig_P8 / 32768.0
		p = p + (var1 + var2 + dig_P7) / 16.0
		return p

	def shutDown(self):
		# TODO: send code to reset register
		pass
