import math
import time

import keyboard
import mouse
from planar import Vec2

"""
INFO:
    Code to run on the PC is here (main.py), while the code to run on the
    Pi is also kept in this repository (pi-main.py). The Arduino code is
    within the typical Arduino-file-folder (attiny_85_battery_code).
    
    The Pi hostname is "mecanum-bot". For a new SD card, install the libaries
    listed in pi-main.py as well as pigpio. Enable SSH, I2C, and Remote GPIO
    through raspi-config, and set the pigpio daemon to launch at boot with
    this command: 'sudo systemctl enable pigpiod'

KEY/BUTTON ASSIGNMENTS
    75 [LEFT] Rotate CCW ✔
    77 [RIGHT] Rotate CW ✔
    35 [H] Toggle field centric mode ✔
    48 [B] Turn to direction (FC only) TODO
    44 [Z] Momentary low speed ✔
    46 [C] Momentary high speed ✔
    2  [1] Low speed ✔
    3  [2] high speed ✔

CONSTANTS TO MODIFY
    SCREEN_RES: primary screen resolution for JoyToKey pointer reading
    LOW_SPEED: a mulitplier from 0.0 to 1.0 that defines the low speed
    HIGH_SPEED: a mulitplier from 0.0 to 1.0 that defines the high speed
    ACCEL_CONSTANT: motor values cannot change by more than this amount
        per loop. Meant to limit motor acceleration (the easy way)
    STRAFING CONSTANT: adjustment to make strafing feel more natural
"""

# Assumes 100% scaling and default JoyToKey mouse seetings; 0,0 at top left
SCREEN_RES = (1920, 1080)
MOUSE_CENTER = (SCREEN_RES[0]/2, SCREEN_RES[1]/2)
MOUSE_MAX = (
    MOUSE_CENTER[0] / 2, MOUSE_CENTER[1] / 2)
LOW_SPEED = 0.5
HIGH_SPEED = 1.0
ACCEL_CONSTANT = 0.05
STRAFING_CONSTANT = 1.3

field_centric = False
motor_speeds = [0.0, 0.0, 0.0, 0.0]
robot_rotation = 0.0
mpu6050_data = [0.0, 0.0, 0.0, 0.0, 0.0, 0.0]  # aX, aY, aZ, gX, gY, gZ
speed_multiplier = LOW_SPEED  # The defualt speed setting on startup


def scale_motor_speeds(motor_speeds):
    """
    Scales motor signals if they are above 1.0, in which case they should be scaled
    to a -1.0 to 1.0 range as to not cause irregular movement when doing diagonals

    NOTE: COULD BE MERGED WITH scale_value TO INCREASE EFFICIENCY
    """

    motor_signal_max = max([math.fabs(i) for i in motor_speeds], default=0)

    if motor_signal_max > 1.0:
        motor_speeds[:] = [j / motor_signal_max for j in motor_speeds]

    return motor_speeds


def scale_value(value, old_min, old_max, new_min, new_max):
    """
    A copy of the Arduino map() function
    """

    value = old_min if value < old_min else old_max if value > old_max else value
    value = (new_max - new_min) * (value - old_min) / (old_max - old_min)
    return value + new_min


def get_motion_values(robot_rotation, field_centric):
    """
    Processes user input and robot data to get proper output "coordinates"
    """

    mouse_position = list(mouse.get_position())

    motion_vector = Vec2(
        mouse_position[0] - MOUSE_CENTER[0], MOUSE_CENTER[1] - mouse_position[1])
    motion_vector = Vec2.polar(
        angle=motion_vector.angle - (robot_rotation if field_centric else 0), length=motion_vector.length)

    return (scale_value(motion_vector.x, -MOUSE_MAX[0], MOUSE_MAX[0], -1, 1),
            scale_value(motion_vector.y, -MOUSE_MAX[1], MOUSE_MAX[1], -1, 1))


def get_motor_speeds(motion_values):
    """
    Processes input motion coordinates for XY movement, checks keyboard
    for keypresses (or wiimote button presses) and outputs data to be
    translated to the inA inB system used on the motor controllers
    """

    # Multiplied by a strafing constant for nicer motion
    global STRAFING_CONSTANT
    x = motion_values[0] * STRAFING_CONSTANT
    y = motion_values[1]
    rx = -1 if keyboard.is_pressed(75) else 1 if keyboard.is_pressed(77) else 0
    temp_speed_multiplier = LOW_SPEED if keyboard.is_pressed(
        44) else HIGH_SPEED if keyboard.is_pressed(46) else 0.0

    motor_speeds = [
        y + x + rx,  # Front Left
        y - x + rx,  # Back Left
        y - x - rx,  # Front Right
        y + x - rx   # Back Right
    ]

    scale_motor_speeds(motor_speeds)

    # If a momentary speed modified has been activated, use that speed multiplier
    if temp_speed_multiplier > 0.0:
        motor_speeds[:] = [s * temp_speed_multiplier for s in motor_speeds]
    else:
        motor_speeds[:] = [s * speed_multiplier for s in motor_speeds]

    # If the previous data has a difference greater than the acceleration constant
    # then the current data is scaled to have a difference equal to the constant
    
    # TODO: this

    '''
    print("%.2f ---------------- %.2f" % (motor_speeds[0], motor_speeds[2]))
    print("---------------------------")
    print("---------------------------")
    print("---------------------------")
    print("---------------------------")
    print("---------------------------")
    print("%.2f ---------------- %.2f" % (motor_speeds[1], motor_speeds[3]))
    '''

    return motor_speeds


def get_robot_rotation(mpu6050_data):
    return 0


keyboard.on_press_key("g", lambda _: mouse.move(
    MOUSE_CENTER[0], MOUSE_CENTER[1]))  # Centers mouse for debugging purposes

time.sleep(2)
start = time.time()

while True:
    if keyboard.is_pressed(2):
        speed_multiplier = LOW_SPEED
    elif keyboard.is_pressed(3):
        speed_multiplier = HIGH_SPEED

    # TODO: get MPU6050 + battery data through UDP

    if keyboard.is_pressed(35):
        field_centric = True
        robot_rotation = get_robot_rotation(mpu6050_data)

    motor_speeds = get_motor_speeds(
        get_motion_values(robot_rotation, field_centric))

    print("%s, %s" % (motor_speeds[0], (time.time() - start)))
    # print(motor_speeds)

    time.sleep(0.02)  # 50ms seems to work fine with button presses
