import math
import os
import time
import signal

from planar import Vec2

import evdev
import RPi.GPIO as GPIO
from pizypwm import *

"""
INFO:
	lol nobody is going to read this anyways. If you're using this and you're not Aaron Beckman... good luck

	- Orange LEDs going in a circle means the Pi is booting up. Once LEDs are blue, press and hold [1] and [2]
	  on the Wiimote to pair. The Wiimote's lights should look like this: * - - *
	- Rainbow LEDs means it's enabled.
	- Green LEDs means it's in secondary mode. This could be calibration or power off mode.
	- Red/Pink LEDs means it's low on battery (power down ASAP!)

	- Press B to toggle field centric mode. Currently does nothing as the gyro isn't setup yet.
	- Nunchuk joysticks move the robot in X and Y.
	- Hold [C] for high speed, and hold [Z] for low speed.
	- [L] and [R] on the d pad rotate the robot (holding the wiimote normally, not sideways).
	- Hold [HOME] and move the joystick to all extremes to calibrate. Let the joystick center before releasing
	  the [HOME] button. LEDs should change color while this process is happening.

	- To quit AND power off, press [+] and [-] and [B] at the same time. LEDs will switch back to the boot color
	  (see LED guide above) when it is safe to unplug.
	- To quit WITHOUT powering off, just press [+] and [-]. LEDs will change color and debugging can continue.

CONSTANTS TO MODIFY:
	- LOW_SPEED: a mulitplier from (0.0, 1.0] that defines the low speed.
	- DEF_SPEED: a multiplier from (0.0, 1.0] that defies the default speed.
	- HIGH_SPEED: a mulitplier from (0.0, 1.0] that defines the high speed.
	- ACCEL_CONSTANT: motor values cannot change by more than this amount per loop.
	  Meant to limit motor acceleration (the easy way).
	- STRAFING_CONSTANT: adjustment [1.0, ~1.5] to make strafing feel more natural.
	- ROTATION_CONSTANT: the speed to rotate (0.0, 1.0] when [L ARROW] or [R ARROW] is pressed.
	  Might jerk a lot at higher values
"""

# Variables, Etc. ------------------------------------------------------------------------------------------------------

LOW_SPEED = 0.3
DEF_SPEED = 0.6
HIGH_SPEED = 0.9
ACCEL_CONSTANT = 0.05
STRAFING_CONSTANT = 1.2
ROTATION_CONSTANT = 0.3
BASE_DEVICE_NAME = '/dev/input/event'  # Final name will have a 0, 1, etc. on the end of this string

field_centric = False
motor_values = [0, 0, 0, 0, 0, 0, 0, 0]  # Motor values to write to GPIO
prev_motor_values = [-1, -1, -1, -1, -1, -1, -1, -1]
x_joystick = [50, 127, 205]
y_joystick = [50, 127, 205]
x_rotation = 0.0  # Used in the motor speeds function to utilize the left and right arrow stuff
robot_rotation = 0.0  # TODO not implemented yet because the MPU6050 would have drift
mpu6050_data = [0.0, 0.0, 0.0, 0.0, 0.0, 0.0]  # aX, aY, aZ, gX, gY, gZ
speed_multiplier = DEF_SPEED  # The defualt speed setting on startup

# Event code: event value
key_log = {
	0: 0,  # JoystickX on Nunchuk, 0-127-255 but actually around 24-125-226
	1: 0,  # JoystickY on Nunchuk, 0-127-255 but actually around 37-136-225
	30: 0,  # A on Wiimote
	48: 0,  # B on Wiimote
	46: 0,  # C on Nunchuk
	35: 0,  # Home on Wiimote
	44: 0,  # Z on Nunchuk
	2: 0,  # 1 on Wiimote
	3: 0,  # 2 on Wiimote
	4: 0,  # Minus on Wiimote
	5: 0,  # Plus on Wiimote
	103: 0,  # Up on Wiimote
	108: 0,  # Down on Wiimote
	105: 0,  # Left on Wiimote
	106: 0,  # Right on Wiimote
}

# Motion Control -------------------------------------------------------------------------------------------------------

def scale_motor_speeds(motor_speeds):
	motor_signal_max = max([math.fabs(i) for i in motor_speeds], default=0)

	if motor_signal_max > 1.0:
		motor_speeds[:] = [j / motor_signal_max for j in motor_speeds]

	return motor_speeds

def scale_value(value, old_min, old_max, new_min, new_max):
	value = old_min if value < old_min else old_max if value > old_max else value
	value = (new_max - new_min) * (value - old_min) / (old_max - old_min)

	return value + new_min

def get_motion_values(x_val, y_val, robot_rotation, field_centric):
	global x_joystick
	global y_joystick

	if x_val < x_joystick[1]:
		x_val = scale_value(x_val, x_joystick[0], x_joystick[1], -1.0, 0.0)
	elif x_val > x_joystick[1]:
		x_val = scale_value(x_val, x_joystick[1], x_joystick[2], 0.0, 1.0)
	else:
		x_val = 0.0

	if y_val < y_joystick[1]:
		y_val = scale_value(y_val, y_joystick[0], y_joystick[1], -1.0, 0.0)
	elif y_val > y_joystick[1]:
		y_val = scale_value(y_val, y_joystick[1], y_joystick[2], 0.0, 1.0)
	else:
		y_val = 0.0

	motion_vector = Vec2(x_val, y_val)
	motion_vector = Vec2.polar(angle=motion_vector.angle - (robot_rotation if field_centric else 0), length=motion_vector.length)

	return (motion_vector.x, motion_vector.y)

def get_motor_values(motion_values):
	global STRAFING_CONSTANT
	global ROTATION_CONSTANT
	global x_rotation
	global speed_multiplier

	motor_values = [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
	x = motion_values[0] * STRAFING_CONSTANT
	y = motion_values[1]
	r = x_rotation * ROTATION_CONSTANT

	motor_speeds = [
		y + x + r,  # Front left motor
		y - x + r,  # Back left motor
		y - x - r,  # Front right motor
		y + x - r   # Back right motor
	]

	scale_motor_speeds(motor_speeds)

	motor_speeds[:] = [s * speed_multiplier for s in motor_speeds]

	for i in range(len(motor_speeds)):
		if motor_speeds[i] > 0.0:
			motor_values[i*2] = motor_speeds[i]
		elif motor_speeds[i] < 0.0:
			motor_values[i*2+1] = math.fabs(motor_speeds[i])

	motor_values_scaled = [int(round(v * 100)) for v in motor_values]

	return motor_values_scaled

def write_motor_values(m_vals):
	global prev_motor_values

	if m_vals[0] != prev_motor_values[0]:
		M3A.changeDutyCycle(m_vals[0])
#		print(m_vals[0], end="   ")
#	else:
#		print("--", end="   ")

	if m_vals[1] != prev_motor_values[1]:
		M3B.changeDutyCycle(m_vals[1])
#		print(m_vals[1], end="   ")
#	else:
#		print("--", end="   ")

	if m_vals[2] != prev_motor_values[2]:
		M1A.changeDutyCycle(m_vals[2])
#		print(m_vals[2], end="   ")
#	else:
#		print("--", end="   ")

	if m_vals[3] != prev_motor_values[3]:
		M1B.changeDutyCycle(m_vals[3])
#		print(m_vals[3], end="   ")
#	else:
#		print("--", end="   ")

	if m_vals[4] != prev_motor_values[4]:
		M4A.changeDutyCycle(m_vals[4])
#		print(m_vals[4], end="   ")
#	else:
#		print("--", end="   ")

	if m_vals[5] != prev_motor_values[5]:
		M4B.changeDutyCycle(m_vals[5])
#		print(m_vals[5], end="   ")
#	else:
#		print("--", end="   ")

	if m_vals[6] != prev_motor_values[6]:
		M2A.changeDutyCycle(m_vals[6])
#		print(m_vals[6], end="   ")
#	else:
#		print("--", end="   ")

	if m_vals[7] != prev_motor_values[7]:
		M2B.changeDutyCycle(m_vals[7])
#		print(m_vals[7], end="   ")
#	else:
#		print("--", end="   ")

	print(m_vals)
	prev_motor_values = m_vals[:]

# PWM Initialization ---------------------------------------------------------------------------------------------------

def end_process(signalnum = None, handler = None):
	attiny.stop()
	M1A.stop()
	M1B.stop()
	M2A.stop()
	M2B.stop()
	M3A.stop()
	M3B.stop()
	M4A.stop()
	M4B.stop()
	GPIO.cleanup()

	print("  PWM Halted, GPIO reset. Goodbye!")
	exit(0)

signal.signal(signal.SIGTERM, end_process)
signal.signal(signal.SIGINT, end_process)

"""
PI PINOUTS AND ROBOT WIRING DIAGRAM:
	- 3V3 is the top left pin, aligned as seen on www.pinout.xyz
	- "B__" pins are BCM pins, the same as used on the GPIO library

 |3V3| 5V|       PWR*
 |SDA| 5V|  MPU*
 |SCL|GND|  MPU* GND
 |B04|B14|
 |GND|B15|
 |B17|B18|  M3B  LED
 |B27|GND|  M4A
 |B22|B23|  M3A  M1A
 |3V3|B24|       M4B
 |B10|GND|  M1B
 |B09|B25|  M2A  M2B

 * = optional (PWR should be from microUSB for surge protection, MPU not yet implemented)
  ___                     ___
 |   |       FRONT       |   |
 |M3A|                   |M4A|
 |M3B|                   |M4B|
 |   |                   |   |
  ---                     ---
    LEFT     ROBOT    RIGHT
  ___                     ___
 |   |                   |   |
 |M1A|                   |M2A|
 |M1B|                   |M2B|
 |___|       BACK        |___|

"""
attiny_pin = 18  # Hardware PWM

# attiny = PiZyPwm(100, 18, GPIO.BCM)
# M2A = PiZyPwm(100, 23, GPIO.BCM)
# M2B = PiZyPwm(100, 10, GPIO.BCM)
# M4A = PiZyPwm(100, 9, GPIO.BCM)
# M4B = PiZyPwm(100, 25, GPIO.BCM)
# M1A = PiZyPwm(100, 22, GPIO.BCM)
# M1B = PiZyPwm(100, 17, GPIO.BCM)
# M3A = PiZyPwm(100, 27, GPIO.BCM)
# M3B = PiZyPwm(100, 24, GPIO.BCM)

# OLD (rotation didn't work, etc.) USE FOR WIRING REFERENCE
M1A = PiZyPwm(100, 23, GPIO.BCM)
M1B = PiZyPwm(100, 10, GPIO.BCM)
M2A = PiZyPwm(100, 9, GPIO.BCM)
M2B = PiZyPwm(100, 25, GPIO.BCM)
M3A = PiZyPwm(100, 22, GPIO.BCM)
M3B = PiZyPwm(100, 17, GPIO.BCM)
M4A = PiZyPwm(100, 27, GPIO.BCM)
M4B = PiZyPwm(100, 24, GPIO.BCM)

GPIO.setmode(GPIO.BCM)
GPIO.setup(attiny_pin, GPIO.OUT)
attiny = GPIO.PWM(attiny_pin, 1000)

attiny.start(0)  # Command for hardware PWM is the same as software PWM
M1A.start(0)
M1B.start(0)
M2A.start(0)
M2B.start(0)
M3A.start(0)
M3B.start(0)
M4A.start(0)
M4B.start(0)


# WiiMote Connection ---------------------------------------------------------------------------------------------------

attiny.ChangeDutyCycle(66)
print("LED mode: CONNECTING")
time.sleep(3)
os.system("sh /home/pi/connectwiimote.sh")  # Has a 1 second delay built in

# WiiMote Initialization -----------------------------------------------------------------------------------------------

def find_wiimote_device(recur):  # Repeats 3-4? times in case connecting was faulty
	time.sleep(1)
	devs = [evdev.InputDevice(path) for path in evdev.list_devices()]
	dev_id = -1

	for dev in devs:
		print(dev.path, dev.name)
		if dev.name == "Nintendo Wiimote":
			dev_id = max(dev_id, int(dev.path[-1]))
			if dev_id != -1:
				return dev_id
			elif recur < 3:
				recur += 1
				return find_wiimote_device(recur)
			return -1

device_id = find_wiimote_device(0)

if device_id == -1:
	print("No Wiimote detected as input! Check your Wiimote connection or the initial configuration steps and try again.")
	exit(0)

BASE_DEVICE_NAME += str(device_id)
print("Wiimote found: ", BASE_DEVICE_NAME)
device = evdev.InputDevice(BASE_DEVICE_NAME)

attiny.ChangeDutyCycle(33)
print("LED mode: ENABLED")

# Main Loop ------------------------------------------------------------------------------------------------------------

for event in device.read_loop():
	e_c = event.code  # Joystick: 0 or 1   Button: ecodes values
	e_t = event.type  # Null: 0   Button: 1   Joystick: 3
	e_v = event.value  # Pressed: 1   Released: 0   Joystick: 0-255

	if e_t > 0:
		# old_joystick[0] = key_log[0]
		# old_joystick[1] = key_log[1]

		key_log[e_c] = e_v

		# Calibration Sequence ---------------------------------------------------------------------------------

		if key_log[35] == 1:
			if e_c == 35:
				attiny.ChangeDutyCycle(100)
				print("LED mode: CALIBRATION")

			if e_t == 3 and e_c == 0:  # X joystick activated
				if e_v < x_joystick[0]:   # Less than threshold
					x_joystick[0] = e_v
					#print("X min saved:", x_joystick[0])
				elif e_v > x_joystick[2]:  # Greater than threshold
					x_joystick[2] = e_v
					#print("X max saved:", x_joystick[2])
			elif e_t == 3 and e_c == 1:  # Y joystick activated
				if e_v < y_joystick[0]:  # Less than threshold
					y_joystick[0] = e_v
					#print("Y min saved:", y_joystick[0])
				elif e_v > y_joystick[2]:  # Greater than threshold
					y_joystick[2] = e_v
					#print("Y max saved:", y_joystick[2])

		elif key_log[35] == 0 and e_c == 35:
			attiny.ChangeDutyCycle(33)
			print("LED mode: ENABLED")

			x_joystick[1] = key_log[0]
			y_joystick[1] = key_log[1]
			#print("Calibration complete:", x_joystick, y_joystick)

		elif key_log[48] == 0 and e_c == 48:
			field_centric = not field_centric
			#print("Field centric:", field_centric)

		# Input Processing ------------------------------------------------------------------------------------

		if key_log[44] == 1:
			speed_multiplier = LOW_SPEED
		elif key_log[46] == 1:
			speed_multiplier = HIGH_SPEED
		else:
			speed_multiplier = DEF_SPEED

		if key_log[4] == 1 and key_log[5] == 1:
			if key_log[48] == 0:
				attiny.ChangeDutyCycle(100)
				print("LED mode: SHUTTING DOWN")  # Same as calibration
				os.system("sudo shutdown now --poweroff")
			else:
				end_process()

		# TODO update this with time-based processing rather than the current joystick position

		if e_c != 35 and key_log[35] == 0 and (e_c < 2 or e_c > 104):  # Has to be a main control button (jX jY R L)
			x_rotation = -1 if key_log[105] == 1 else 1 if key_log[106] == 1 else 0

			x_temp = math.fabs(key_log[0] - x_joystick[1])
			y_temp = math.fabs(key_log[1] - y_joystick[1])

			if x_temp > 7 or y_temp > 7 or x_rotation != 0:
				motor_values = get_motor_values(get_motion_values(key_log[0], key_log[1], robot_rotation, field_centric))

			elif x_temp < 8 and y_temp < 8:
				motor_values[:] = [0 for v in motor_values]

			write_motor_values(motor_values)
