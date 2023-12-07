===========================
fledge-south-mqtt-publisher
===========================

Fledge South MQTT Publisher plugin, Default MQTT version is v3.3.3; Use either MQTTv31 or MQTTv311.

The MQTT broker service should be running.
 

The example given here are tested using `mosquitto` http://test.mosquitto.org/

.. code-block:: console

    $ sudo apt install -y mosquitto
    $ sudo systemctl enable mosquitto.service


Install `paho-mqtt` pip package.

.. code-block:: console
    
    python3 -m pip install -r python/requirements.txt


Install plugin in your local Fledge installation

.. code-block:: console

    sh install-plugin.sh


Run Subsciber Test Script

.. code-block:: console

    $ mosquitto_sub -t "YourTopic" -h "localhost" -p 1883
    {
        "operation":"YourTopic",
        "parameters":[{
            "name":"example",
            "value":{...}
        }]
    }

The mosquitto_sub command should be ran right after installing and initializing Fledge and
will await MQTT payloads from the specified host. The South MQTT Publisher will await MQTT 
commands from the active North plugin and send them to the subscribed clients, such as the 
mosquitto example client. 