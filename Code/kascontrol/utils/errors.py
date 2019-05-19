#!/usr/bin/python3

# Author: J. Saarloos
# v0.1.01	19-05-2019


class AbortInitError(Exception):
	pass


class ADCconfigError(AbortInitError):
	pass


class ShutdownError(Exception):
	pass


class SpiConfigError(AbortInitError):
	pass


class SpiPinError(AbortInitError):
	pass
