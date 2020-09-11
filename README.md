# Mecanum Bot Code
This is a backup of the code for the Wiimote-controlled mecanum robot. Currently it uses a Pi Zero W and Attiny85 as the main controllers, and has basic features (motion with strafing, battery indication, nunchuk calibration, slow/fast modes, safe shutdown indication, etc.)

**See photos [here](https://photos.app.goo.gl/PudXENaW6ujRSE3S7)**

To use, make sure `mywminput`, `pi-main.py`, `pyzypwm.py` and `connectwiimote.sh` are all in the main (~/) directory. Some elements of the tutorials listed below will be needed to set it up. This README is for re-building the SD card later on as I had to overwrite the current one for a different project.

-https://pimylifeup.com/raspberry-pi-wiimote-controllers/
-https://retropie.org.uk/docs/Wiimote-Controller/
-https://www.programcreek.com/python/example/93202/evdev.categorize
-http://himeshp.blogspot.com/2018/08/fast-boot-with-raspberry-pi.html#:~:text=The%20Hardware%20and%20bootloader%20take,processor%20was%20around%201.5%20seconds.
-https://github.com/abstrakraft/cwiid/blob/master/doc/wminput.list
-https://github.com/torvalds/linux/blob/master/include/uapi/linux/input-event-codes.h
-https://www.raspberrypi.org/forums/viewtopic.php?t=63784&p=482624

Later on, this project should be adapted to use a sole ESP32. This will simplify electronics, greatly reduce setup time (turning on the robot takes ~30sec with the Pi Zero W), and make it easier to develop. It also has hardware PWM and proper timing, both things that the Pi Zero W lack.
