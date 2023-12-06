#!/bin/bash

pip install paho-mqtt
sudo cp python/plugins/south/mqtt-publisher/mqtt-publisher.py /usr/local/fledge/python/fledge/plugins/south/mqtt-publisher
echo Restart fledge to install plugin
./../../fledge/scripts/fledge stop
sudo ./../../fledge/scripts/fledge start