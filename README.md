# kas-control
Kas Control is a Raspberry Pi expansion board for watering plants and checking a few more environmental variables
PCB should be correct.
Software is currently not functional. Use v2017 for basic functionality.

Features
--------
- PCB plugs straight into your rPi. rPi is powered through the PCB
- Measuring soil moisture level of up to 7 plants/containers
  - Can pump water to plant/container when moisture level is below threshold so you don't have to!
- Measuring amount of water given per channel and total
- Default 3 temperature sensors are supported by the board. Software supports infinite sensors. Make a simple breakout (connect parallel) board for more sensors.
- Light sensor for ambient light measurement.
- Float switch for use in a water container.
- Outputs:
  - 2 configurable LEDbars.
  - Standard HD44780 16x2 or 20x4 character LCD with driver kindly copied from ADAfruit.
- Network client to set the various setting and get the data.
  - Command-line only. Graph makes a Google graph html file that will open in a new tab in your browser
  - Basic encryption is implemented with openSSL
- Database
  - All sensor data is logged
  - Add a name and plant type to keep track of which plants you've grown
- 5v/12v 4A PSU PCB with INA219 power monitor. PCB files are available, haven't tested it yet.
  - 4 powerLED connectors are available for 350/500/700mA powerLED strips.
  - Power monitoring is available via INA219 ICs
  
Future Features
---------------
- Network
  - Full-fledged GUI for the network client. Probably built on Kivy.
  - rPi camera support so you can watch your plants from all over the world
- Database
  - Adding results such as plant size or harvest amount to each of your plants. Manual input only of course.
- Implement event system

Motivation
----------

I like weed. I like electronics. I like programming. Here's the result :)


Installation/requirements
-------------------------

- I use Arch Linux so only instructions for that. Actual instructions will follow later.
- RPi.GPIO
- SMBus for i2c
- spidev for SPI
- SQlite for database
- Kivy (future)


Contributors
------------

Sorry, no help wanted. This is my pet project and I want it to be just how I like it. Of Course you are welcome to use the code and pcb files as you wish.

License
-------

GNU General Public License v3.0
