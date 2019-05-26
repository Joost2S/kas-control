#!/usr/bin/python3

# Author: J. Saarloos
# v0.1.03	26-05-2019


class AbortInitError(Exception):
	pass


class ADCconfigError(AbortInitError):
	pass


class DBValidationError(Exception):
	pass


class HwInitError(AbortInitError):
	pass


class ShutdownError(Exception):
	pass


class SpiConfigError(AbortInitError):
	pass


class SpiPinError(AbortInitError):
	pass
