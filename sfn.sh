#!/bin/bash

SFN_NAME=sfn

if [ "$1" == "create" ]; then
	echo "Stopping container ${SFN_NAME}"
	sudo docker stop sfn
	echo "Removing container ${SFN_NAME}"
	sudo docker container rm ${SFN_NAME}
	echo "Creating container ${SFN_NAME}"
	sudo docker run -d --restart always --name=${SFN_NAME} --net="host" -t ${SFN_NAME}
	echo "Registering Tivoli"
	sleep 5
	python3 /home/tivoli/monica/WP5/KU/SecurityFusionNodeService/tivoli_reg.py
	echo "Attaching to stdio"
	sudo docker attach --no-stdin ${SFN_NAME}
elif [ "$1" == "start" ]; then
	echo "Starting ${SFN_NAME}"
	sudo docker start ${SFN_NAME}
	echo "Registering Tivoli"
	sleep 5
	python3 /home/tivoli/monica/WP5/KU/SecurityFusionNodeService/tivoli_reg.py
	echo "Done"
elif [ "$1" == "stop" ]; then
	echo "Stopping ${SFN_NAME}"
	sudo docker stop ${SFN_NAME}
	echo "Done"
elif [ "$1" == "attach" ]; then
	sudo docker attach ${SFN_NAME}
else
  echo "Argument missing. Options:" 
  echo "create	Creates and runs new ${SFN_NAME} container and calls registration. Stops and removes current if exists."
  echo "start	Starts ${SFN_NAME} container and calls registration."
  echo "stop    Stops ${SFN_NAME} container."
  echo "attach  Attches to stdio of running ${SFN_NAME} container."
fi
