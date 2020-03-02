#!/bin/bash

username=`cat /home/tivoli/monica/VPN_user`
password=`cat /home/tivoli/monica/VPN_pass`
connection_name="tun_vpn"
while true; do
tunActive=`ifconfig | grep $connection_name | wc -l`
echo "Checking the VPN Connection"
if [ $tunActive -eq 0 ]; then
	echo "VPN connection down, reconnecting:"
	sudo kill `ps aux|grep openconnect|grep -v grep |cut -c 10-15`
	echo $password | sudo openconnect -q https://vpn.monica-cloud.eu -i $connection_name -u $username --passwd-on-stdin -b
elif [ $tunActive -eq 1 ]; then
	echo "VPN connection is fine. Carry on."
fi
sleep 20
done

# ps -ef | grep openconnect
# sudo kill -9 <PID>
# nmcli con up id "vpn_auto"
# nmcli con

