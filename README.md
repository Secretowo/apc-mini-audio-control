# apc-mini-audio-control
Control Audio on a per-process level using an AKAI Professional APC mini.

Requires [apc-mini-py](https://github.com/Secretowo/apc-mini-py) and the things in requirements.txt

The code is a mess. i know. but it works.

# What do the buttons do?:
Button | Function
------ | --------
Arrow up | Volume up
Arrow down | Volume down
Arrow left | Previous song
Arrow right | Next song
Volume | Play/Pause
Pan | -
Send | -
Device | Reload active processes
Shift | Reset leds 
Stop all clips | -
Lower empty button | Decrease audio visualizer speed
Upper empty button | Increase audio visualizer speed
Select | Switch between per-process and main output peaks
Mute | Simulates pressing the 'm' key
Rec Arm | -
Solo | -
Clip stop | -
Sliders 1-8 | process volumes
Silder 9 | Main audio device volume

The buttons above the sliders will light up if theres an audio session for that slider. if the button blinks, that means the process's window is currently in focus.

If you have any issues or question please contact me, im always happy to help.
