import math
import time

import keyboard
import mouse
from planar import Vec2

"""
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
"""

# Assumes 100% scaling and default JoyToKey mouse seetings; 0,0 at top left
SCREEN_RES = (1920, 1080)
MOUSE_CENTER = (SCREEN_RES[0]/2, SCREEN_RES[1]/2)
MOUSE_MAX = (
    MOUSE_CENTER[0] / 2, MOUSE_CENTER[1] / 2)
LOW_SPEED = 0.5
HIGH_SPEED = 1.0

field_centric = False
motor_speeds = [0.0, 0.0, 0.0, 0.0]
speed_multiplier = LOW_SPEED


def scale_motor_speeds(motor_speeds):
    """
    Returns True if any motor signals are above 1.0, in which case they should be scaled
    to a -1.0 to 1.0 range as to not cause irregular movement when doing diagonals

    NOTE: COULD BE MERGED WITH scale_value TO INCREASE EFFICIENCY
    """

    motor_signal_max = max([math.fabs(i) for i in motor_speeds], default=0)

    if motor_signal_max > 1.0:
        motor_speeds[:] = [j / motor_signal_max for j in motor_speeds]

    return motor_speeds


def scale_value(value, min_value, max_value):
    """
    A copy of the Arduino map() function, outputting a capped value from 0 to 1
    """

    value = -max_value if value < - \
        max_value else max_value if value > max_value else value
    return (value - min_value) / (max_value - min_value)


def get_motion_values(robot_rotation, field_centric):
    """
    Processes user input and robot data to get motor output values
    - Vectors are lists in the [length, direction] format
    - Direction/rotation is an angle from 0-360 degrees going CW from 12:00
    """

    mouse_position = list(mouse.get_position())

    motion_vector = Vec2(
        mouse_position[0] - MOUSE_CENTER[0], MOUSE_CENTER[1] - mouse_position[1])
    motion_vector = Vec2.polar(
        angle=motion_vector.angle - (robot_rotation if field_centric else 0), length=motion_vector.length)

    return (scale_value(motion_vector.x, 0, MOUSE_MAX[0]),
            scale_value(motion_vector.y, 0, MOUSE_MAX[1]))


def get_motor_values(motion_values):
    """
    Processes input motion values for XY movement, checks keyboard
    for keypresses (or wiimote button presses) and outputs data
    to be sent directly to motor controllers.
    """

    # Multiplied by a strafing constant for nicer motion
    x = motion_values[0] * 1.4
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
        motor_speeds[:] = [k * temp_speed_multiplier for k in motor_speeds]
    else:
        motor_speeds[:] = [k * speed_multiplier for k in motor_speeds]

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


keyboard.on_press_key("g", lambda _: mouse.move(
    MOUSE_CENTER[0], MOUSE_CENTER[1]))  # Centers mouse for debugging purposes

while True:
    if keyboard.is_pressed(2):
        speed_multiplier = LOW_SPEED
    elif keyboard.is_pressed(3):
        speed_multiplier = HIGH_SPEED

    field_centric = True if keyboard.is_pressed(35) else False

    print(field_centric)

    robot_rotation = 0

    motor_speeds = get_motor_values(
        get_motion_values(robot_rotation, field_centric))

    time.sleep(0.05)  # 50ms seems to work fine with button presses
