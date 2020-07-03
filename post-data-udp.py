# Code on Lenovo

import socket
import time
import random
# int(time.time())
UDP_TX_IP = "192.168.0.17"  # The recieving end's IP (the Pi Zero W)
UDP_RX_IP = "192.168.0.40"  # This device's IP (the Lenovo)
UDP_PORT = 4536  # Why not

tx_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
rx_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

rx_socket.bind((UDP_RX_IP, UDP_PORT))

while True:
    random_tx_data = str(random.randrange(0, 256))
    tx_socket.sendto(str.encode(random_tx_data), (UDP_TX_IP, UDP_PORT))
    print("Sent Message: %s" % random_tx_data)

    data, addr = rx_socket.recvfrom(1024)  # Buffer size is 1024 bytes
    print("Received Message: %s" % data.decode("utf-8"))
