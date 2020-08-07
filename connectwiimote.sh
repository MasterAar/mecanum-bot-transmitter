#!/bin/bash
sleep 1
hcitool dev | grep hci >/dev/null

if test $? -eq 0 ; then
	wminput -d -q -c /home/pi/mywminput 00:23:CC:89:D5:DD > /dev/null 2>&1 &
else
	echo "Bluetooth adapter not present!"
	exit 1
fi
