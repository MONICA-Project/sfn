#!/bin/bash

while true; do
vcaActive=`systemctl status vca-cored| grep "active (running)"| wc -l`
echo "Checking the VCA status"
if [ "$vcaActive" -eq 0 ]; then
	echo "VCA core is crashed, restarting:"
	systemctl restart vca-cored
elif [ "$vcaActive" -eq 1 ]; then
	echo "VCA core is running. Carry on."
fi
sleep 30
done
