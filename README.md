# A recording box for USB microphones and audio interfaces

This small project is a audio recording box built from a Raspberry Pi and some basic components. 
Audio recording is possible via any USB microphone. For playback a USB sound card is recommended.
The goal is to have simple cassette recorder like functionality.

Features are

- direct recording with one button push
- a display with a basic menu to navigate through recordings and setup audio devices
- menu navigation is done with a rotary encoder with a built-in switch (push)
- playback can be started by navigating to a recorded file and pushing the play button
- a separate button can be used to set up a A/B loop for continuous playback.
- recorded files are named with a date and time stamp
- the RTC module keeps time and date when unplugged from power

## List of materials

- Raspberry Pi 3
- 3 push buttons (1 momentary: Loop, and 2 on/off switches: Rec and Play)
- 3 LEDs and resistors
- a rotary encoder with integrated push button (for menu navigation)
- real Time Clock module
- LCD Display (20x4 characters)
- an adequate enclosure
- a USB microphone or USB sound card (with speaker out and mic in)
- some wire

## Basic schematic
![schematic](recording_box_bb.jpg)

## install required packages on a standard RaspberryPi Os lite
```
sudo apt-get update
sudo apt-get install python3-pip python3-pyaudio python3-smbus python3-gpiozero git 
sudo pip3 install RPLCD
```
