#!/bin/bash

HOME=/home/tivoli
VD_CC_NAME=crowd_counting
VD_ET_NAME=entity_tracker

if [ "$1" == "recreate" ]; then
	cd $HOME/entity_detector/crowd_counting
	echo "Stopping container ${VD_CC_NAME}"
        sudo docker stop ${VD_CC_NAME}
        echo "Stopping container ${VD_ET_NAME}"
        sudo docker stop ${VD_ET_NAME}
        echo "Removing container ${VD_CC_NAME}"
        sudo docker container rm ${VD_CC_NAME}
        echo "Removing container ${VD_ET_NAME}"
        sudo docker container rm ${VD_ET_NAME}
        echo "Creating container ${VD_CC_NAME}"
        nvidia-docker run -it --restart on-failure --name=${VD_ET_NAME} -p 9890:9890 -v $HOME/Desktop/entity_tracker/videos:/Entity_Tracker/videos ${VD_ET_NAME}
        echo "Starting ${VD_CC_NAME}"
        sudo docker run -it --restart on-failure -p 9891:9891 --name=${VD_CC_NAME} ${VD_CC_NAME}
        cd ..
        source venv27/bin/activate
        echo "RUN the main script"
        python main_script.py
        sleep 5
        echo "Done"

elif [ "$1" == "start" ]; then
	cd $HOME/entity_detector
	echo "Starting ${VD_ET_NAME}"
	sudo docker start ${VD_ET_NAME}
	echo "Starting ${VD_CC_NAME}"
	sudo docker start ${VD_CC_NAME}
	echo "Run the main script"
	source venv27/bin/activate
	python main_script.py
	sleep 5
	echo "Done"

elif [ "$1" == "stop" ]; then
	echo "Stopping main_script.py"
	sudo kill `ps aux|grep main_script.py|grep -v grep |cut -c 10-15`
	echo "Stopping ${VD_CC_NAME}"
	sudo docker stop ${VD_CC_NAME}
	echo "Stopping ${VD_ET_NAME}"
	sudo docker stop ${VD_ET_NAME}
	echo "Done"

elif [ "$1" == "attach" ]; then
	sudo docker attach --no-stdin ${VD_CC_NAME}
else
  echo "Argument missing. Options:" 
  echo "recreate	Reinstantiates and runs new ${VD_CC_NAME} and ${VD_ET_NAME} containers and run the main script. Stops and removes instances of current containers if exists."
  echo "start		Starts stopped ${VD_CC_NAME} and ${VD_ET_NAME} containers and run the main script."
  echo "stop		Stops running ${VD_CC_NAME} and ${VD_ET_NAME} containers."
  echo "attach		Attaches to stdio of running ${VD_CC_NAME} container."
fi
