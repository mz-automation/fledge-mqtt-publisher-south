#!/bin/bash

if [ ! -d /usr/local/fledge/python/fledge/plugins/south/mqtt-publisher ]
then
    #creates new plugin folder on local fledge installation if there is none
    echo "mqtt-publisher file doesn't exist; creating new file"
    sudo mkdir /usr/local/fledge/python/fledge/plugins/south/mqtt-publisher
    sudo cp python/plugins/south/mqtt-publisher/mqtt-publisher.py /usr/local/fledge/python/fledge/plugins/south/mqtt-publisher
    sudo cp python/plugins/south/mqtt-publisher/__init__.py /usr/local/fledge/python/fledge/plugins/south/mqtt-publisher
    sudo cp python/requirements.txt /usr/local/fledge/python/fledge/plugins/south/mqtt-publisher
    sudo cp VERSION.south.mqtt-publisher /usr/local/fledge/python/fledge/plugins/south/mqtt-publisher
else
    #if there is a plugin folder already, only copies the plugin code to the preexisting folder
    echo "mqtt-publisher file already exists"
    sudo cp python/plugins/south/mqtt-publisher/mqtt-publisher.py /usr/local/fledge/python/fledge/plugins/south/mqtt-publisher
fi

./../../fledge/scripts/fledge stop
sudo ./../../fledge/scripts/fledge start
echo "mqtt-publisher installed"