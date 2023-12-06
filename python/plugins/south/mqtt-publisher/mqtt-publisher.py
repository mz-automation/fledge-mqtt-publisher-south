

import asyncio
import random
import copy
import json
import logging
import re
import sys
import uuid

import paho.mqtt.publish as mqtt_publish
import paho.mqtt.client as mqtt_client

from fledge.common import logger
from fledge.plugins.common import utils
from fledge.services.south import exceptions
from fledge.services.south.ingest import Ingest
from fledge.common.plugin_discovery import PluginDiscovery
from fledge.services.core.api import south
from fledge.services.core.api import north
import binascii
import async_ingest
import json

# MQTT config
MQTT_BROKER = "localhost"
# MQTT_BROKER = "test.mosquitto.org"
MQTT_PORT = 1883
KEEP_ALIVE_INTERVAL = 45

_LOGGER = logger.setup(__name__, level=logging.INFO)

c_callback = None
c_ingest_ref = None
loop = None


_DEFAULT_CONFIG = {
    'plugin': {
        'description': 'MQTT Publisher South Plugin',
        'type': 'string',
        'default': 'mqtt-publisher',
        'readonly': 'true'
    },
    'brokerHost': {
        'description': 'Hostname or IP address of the broker to connect to',
        'type': 'string',
        'default': 'localhost',
        'order': '1',
        'displayName': 'MQTT Broker host',
        'mandatory': 'true'
    },
    'brokerPort': {
        'description': 'The network port of the broker to connect to',
        'type': 'integer',
        'default': '1883',
        'order': '2',
        'displayName': 'MQTT Broker Port',
        'mandatory': 'true'
    },
    'keepAliveInterval': {
        'description': 'Maximum period in seconds allowed between communications with the broker. If no other messages are being exchanged, '
                        'this controls the rate at which the client will send ping messages to the broker.',
        'type': 'integer',
        'default': '60',
        'order': '3',
        'displayName': 'Keep Alive Interval'
    },
    'topic': {
        'description': 'The subscription topic to publish to subscribers',
        'type': 'string',
        'default': 'PivotCommand',
        'order': '4',
        'displayName': 'Topic To Publish',
        'mandatory': 'true'
    },
    'qos': {
        'description': 'The desired quality of service level for the subscription',
        'type': 'integer',
        'default': '0',
        'order': '5',
        'displayName': 'QoS Level',
        'minimum': '0',
        'maximum': '2'
    },
    'assetName': {
        'description': 'Name of Asset',
        'type': 'string',
        'default': 'mqtt-',
        'order': '6',
        'displayName': 'Asset Name',
        'mandatory': 'true'
    },
    'gpiopin': {
        'description': 'The GPIO pin into which the DHT11 data pin is connected',
        'type': 'integer',
        'order':'7',
        'default': '4'
    }
}

def receive_config():
    return

def plugin_info():
    _LOGGER.info("Publisher Info loaded")
    return {
        'name':'MQTT Publisher',
        'version':'1.0',
        'mode':'control',
        'type':'south',
        'sp_control':'',
        'interface': '1.0',
        'config':_DEFAULT_CONFIG
    }

def plugin_init(config):
    _LOGGER.info("Publisher initializing")
    handle = copy.deepcopy(config)
    handle["_mqtt"] = MqttPublisherClient(handle)
    _LOGGER.info("Publisher initiated %s", handle)
    return handle

def plugin_start(handle):
    global loop
    loop = asyncio.new_event_loop()

    _LOGGER.info('Starting MQTT publisher south plugin...')
    try:
        _mqtt = handle["_mqtt"]
        _mqtt.loop = loop
        _mqtt.start()
    except Exception as e:
        _LOGGER.exception(str(e))
    else:
        _LOGGER.info('MQTT south plugin started.')

def plugin_reconfigure(handle, new_config):
    _LOGGER.info('Reconfiguring MQTT south plugin...')
    plugin_shutdown(handle)
    new_handle = plugin_init(new_config)
    plugin_start(new_handle)
    _LOGGER.info('MQTT south plugin reconfigured.')
    return new_handle

def plugin_shutdown(handle):
    global loop
    try:
        _LOGGER.info('Shutting down MQTT south plugin...')
        _mqtt = handle["_mqtt"]
        _mqtt.stop()
        
        loop.stop()
        loop = None
    except Exception as e:
        _LOGGER.exception(str(e))
    else:
        _LOGGER.info('MQTT south plugin shut down.')

def plugin_operation(handle, operation, params):
    x = json.dumps(operation)
    _LOGGER.debug("plugin_operation(): operation={}, params={}".format(operation, params))
    params_json = []

    for param in params:
        if param[1][0] == '{':
            param_value = json.loads(param[1])
        else:
            param_value = param[1]

        params_json.append({'name':param[0],'value': param_value})    

    _MQQT_PAYLOAD = {
        'operation':operation,
        'parameters':params_json
    }
    payload_json = json.dumps(_MQQT_PAYLOAD)
    handle["_mqtt"].mqtt_client.publish(str(operation),payload_json)
    return True

# def plugin_poll(handle):
#     _LOGGER.info("in plugin_poll")
#     return None

def plugin_register_ingest(handle, callback, ingest_ref):
    global c_callback, c_ingest_ref
    c_callback = callback
    c_ingest_ref = ingest_ref

class MqttPublisherClient(object):

    __slots__ = ['mqtt_client', 'broker_host', 'broker_port', 'topic', 'qos', 'keep_alive_interval', 'asset', 'loop']

    def __init__(self, config):
        _LOGGER.info("MQTT Publisher initializing")
        self.mqtt_client = mqtt_client.Client()
        self.broker_host = config['brokerHost']['value']
        self.broker_port = int(config['brokerPort']['value'])
        self.topic = config['topic']['value']
        self.qos = int(config['qos']['value'])
        self.keep_alive_interval = int(config['keepAliveInterval']['value'])
        self.asset = config['assetName']['value']
        _LOGGER.info("MQTT Publisher connecting to broker")
        self.mqtt_client.connect(self.broker_host, self.broker_port, self.keep_alive_interval)

    def on_connect(self, client, userdata, flags, rc):
        """ The callback for when the client receives a CONNACK response from the server
        """
        client.connected_flag = True

    def on_disconnect(self, client, userdata, rc):
        self.mqtt_client.disconnect()
        pass

    def on_publish(self, client, data, granted_qos):
        pass

    def start(self):
        _LOGGER.info("MQTT Publisher starting")
        if self.username and len(self.username.strip()) and self.password and len(self.password):
            # no strip on pwd len check, as it can be all spaces?!
            self.mqtt_client.username_pw_set(self.username, password=self.password)
        # event callbacks
        self.mqtt_client.on_connect = self.on_connect

        self.mqtt_client.on_disconnect = self.on_disconnect

        self.mqtt_client.connect(self.broker_host, self.broker_port, self.keep_alive_interval)
        _LOGGER.info("MQTT connecting..., Broker Host: %s, Port: %s", self.broker_host, self.broker_port)

        self.mqtt_client.loop_start()

    def stop(self):
        self.mqtt_client.disconnect()
        self.mqtt_client.loop_stop()