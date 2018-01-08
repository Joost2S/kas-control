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
- ~~Standard HD44780 16x2 or 20x4 character LCD with drivers kindly copied from ADAfruit.~~ Haven't tested yet.
- Network client to set the various setting and get the data.
  - Command-line only. Graph makes a Google graph html file that will open in a new tab in your browser
  - Basic encryption is implemented with openSSL
- Database
  - All sensor data is logged
  - Add a name and plant type to keep track of which plant you've grown
  
Future Features
---------------
- 2 configurable LEDbars.
- Network
  - Full-fledged GUI for the network client.
  - Webcam support so you can watch your plants from all over the world
- Database
  - Adding results such as plant size or harvest amount to each of your plants. Manual input only of course.
- 5v/12v PSU PCB with INA219 power monitor

Motivation
----------

I like weed. I like electronics. I like programming. Here's the result :)


Installation/requirements
-------------------------

- I use Arch Linux so only instructions for that.
- RPi.GPIO
- SMBus for i2c
- spidev for SPI


Contributors
------------

Sorry, no help wanted. This is my pet project and I want it to be just how I like it. Of Course you are welcome to use the code and pcb files as you wish.

License
-------

GNU General Public License v3.0