import math
import time
import sys

import evdev
from planar import Vec2

"""
INFO:
    TODO

CONSTANTS TO MODIFY
    LOW_SPEED: a mulitplier from 0.0 to 1.0 that defines the low speed
    HIGH_SPEED: a mulitplier from 0.0 to 1.0 that defines the high speed
    ACCEL_CONSTANT: motor values cannot change by more than this amount
        per loop. Meant to limit motor acceleration (the easy way)
    STRAFING CONSTANT: adjustment to make strafing feel more natural
"""

# Variables, Etc. ------------------------------------------------------------------------------------------------------

LOW_SPEED = 0.5
HIGH_SPEED = 1.0
ACCEL_CONSTANT = 0.05
STRAFING_CONSTANT = 1.3
BASE_DEVICE_NAME = '/dev/input/event'  # Final name will have a 0, 1, etc. on the end of this string

field_centric = False
motor_speeds = [0.0, 0.0, 0.0, 0.0]
robot_rotation = 0.0
mpu6050_data = [0.0, 0.0, 0.0, 0.0, 0.0, 0.0]  # aX, aY, aZ, gX, gY, gZ
speed_multiplier = LOW_SPEED  # The defualt speed setting on startup

# Event code: event value
key_log = {
    0: 0,  # JoystickX on Nunchuk, 0-127-255 but actually around 24-125-226 TODO: calibration instructions
    1: 0,  # JoystickY on Nunchuk, 0-127-255 but actually around 37-136-225 TODO: calibration instructions
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

# WiiMote Initialization -----------------------------------------------------------------------------------------------

devices = [evdev.InputDevice(path) for path in evdev.list_devices()]
device_id = -1

for device in devices:
    print(device.path, device.name)
    if device.name == "Nintendo Wiimote":
        device_id = max(device_id, int(device.path[-1]))

if device_id == -1:
    sys.exit("No Wiimote detected as input! Check your Wiimote connection or the initial configuration steps and try again.")

BASE_DEVICE_NAME += device_id
print(BASE_DEVICE_NAME)
device = evdev.InputDevice(BASE_DEVICE_NAME)

# Main Loop ------------------------------------------------------------------------------------------------------------

for event in device.read_loop():
    e_c = event.code
    e_v = event.value
    print("E")

    # Add motion control stuff here
    if e_c == 2 and key_log[e_c] == 0:
        speed_multiplier = LOW_SPEED
        key_log[e_c] = 1
    else:
        key_log[e_c] = 0
    
    if e_c == 3 and key_log[e_c] == 0:
        speed_multiplier = HIGH_SPEED
        key_log[e_c] = 1
    else:
        key_log[e_c] = 0

    

    key_log[event.code] = event.value  # Update after acting on the event
