import win32gui
import time
import socket
from threading import Thread

MESSAGE = "Hello, World!"

while True:
    point = win32gui.GetCursorPos()
    print(point[0])
    time.sleep(0.1)
    for i in range(100):
        print(MESSAGE)
        MESSAGE = MESSAGE + str(i)
        time.sleep(1)
