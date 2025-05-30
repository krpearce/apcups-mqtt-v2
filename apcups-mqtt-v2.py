import paho.mqtt.client as mqtt
import configparser
import subprocess
import logging
from datetime import datetime
import time


logging.basicConfig(level=logging.DEBUG)

stored_params = {}

# List of params with "Volts" on the end that needs to be trimmed:
voltsParams = {'hitrans', 'lotrans', 'battv', 'nominv', 'linev', 'nombattv', 'outputv', 'nomoutv'}
wattsParams = {'nompower'}
percentParams = {'bcharge', 'mbattchg', 'loadpct', 'retpct'}
secondsParams = {'cumonbatt', 'alarmdel', 'tonbatt', 'maxtime', 'dwake', 'dshutd'}
minutesParams = {'mintimel', 'timeleft'}
datesParams = {'end apc', 'starttime', 'date', 'xonbatt', 'xoffbatt'}
tempParams = {'itemp'}
freqParams = {'linefreq'}



def on_connect(client, userdata, flags, reasonCode, properties=None):
    logging.info("Connected with reason code " + str(reasonCode))
    client.publish(root_topic + "/LWT", payload="Online", qos=0, retain=True)

def scan_ups():
    # Read all of the UPS settings...
    po = subprocess.check_output(['apcaccess'])

    # Load each setting into our dictionary
    splitstrings = po.splitlines()

    upsParams = {}

    for line in splitstrings:
        line = line.decode("utf-8")
        varname = str(line[:9].strip().lower())
        varval = str(line[11:].strip())

        if varname in voltsParams:
            varval = varval.replace('Volts', '').strip()
        if varname in wattsParams:
            varval = varval.replace('Watts', '').strip()
        if varname in percentParams:
            varval = varval.replace('Percent', '').strip()
        if varname in secondsParams:
            varval = varval.replace('Seconds', '').strip()
        if varname in minutesParams:
            varval = varval.replace('Minutes', '').strip()
        if varname in tempParams:
            varval = varval.replace('C', '').strip()
        if varname in freqParams:
            varval = varval.replace('Hz', '').strip()
        if varname in datesParams:
            try:
                varval = datetime.strptime(varval, '%Y-%m-%d %H:%M:%S %z').strftime('%Y-%m-%dT%H:%M:%S%z')
            except:
                varval = "0000-01-01T00:00:00+0000"
        # battdate is just a date, so requires slightly different reformatting.
        if varname == 'battdate':
            varval = datetime.strptime(varval, '%Y-%m-%d').strftime('%Y-%m-%dT%H:%M:%S%z')

        upsParams[varname] = varval

    return upsParams


def rescan_ups():
    new_params = scan_ups()

    for param in new_params:
        # check if param is already in our dictionary
        if param in stored_params:
            # if exists already, then compare, and update if necessary (and publish)
            if new_params[param] != stored_params[param]:
                logging.info("Updating param " + param + " from " + stored_params[param] + " to " + new_params[param])
                stored_params[param] = new_params[param]
                client.publish("{}/{}".format(root_topic, param), new_params[param], 0, True)
        else:
            # add if missing (and publish)
            logging.info("Adding new param " + param)
            client.publish("{}/{}".format(root_topic, param), new_params[param], 0, True)


# ------------------------------------------------------------------------------------------

# Load settings...
SettingsFile = configparser.ConfigParser()
SettingsFile.optionxform = str
SettingsFile.read("./apcups-mqtt.ini")

# Debugging: Log the loaded configuration values
try:
    username = SettingsFile.get("mqtt", "broker_username")
    password = SettingsFile.get("mqtt", "broker_password")
    broker_address = SettingsFile.get("mqtt", "broker_address")
    client_name = SettingsFile.get("mqtt", "client_name")
    root_topic = SettingsFile.get("mqtt", "root_topic")

    # Log the loaded settings to verify they're correct
    logging.info(f"Loaded MQTT Configurations:")
    logging.info(f"  Broker Username: {username}")
    logging.info(f"  Broker Password: {password}")
    logging.info(f"  Broker Address: {broker_address}")
    logging.info(f"  Client Name: {client_name}")
    logging.info(f"  Root Topic: {root_topic}")

except Exception as e:
    logging.error(f"Error reading config: {e}")
    raise


# Set up MQTT client...
client = mqtt.Client(client_id=client_name, userdata=None, protocol=mqtt.MQTTv5)
client.username_pw_set(username, password)
client.on_connect = on_connect

# Setup LWT
client.will_set(root_topic + "/LWT", payload="Offline", qos=0, retain=True)


# Connect to the MQTT broker with port 1883
broker_port = 1883  # Specify the correct port here
client.connect(broker_address, broker_port, 60)  # Use the broker port here

# Load UPS data...
stored_params = scan_ups()

# Output (and publish) our dictionary values on startup...
for param in stored_params:
    logging.info("{}  --  {}".format(param, stored_params[param]))
    client.publish("{}/{}".format(root_topic, param), stored_params[param], 0, True)

# Start MQTT client messaging loop...
client.loop_start()

try:
    while True:
        # Rescan every 10 seconds (even though apcaccess only updates its
        # status every 60 seconds from what I can tell.)
        time.sleep(30)
        rescan_ups()

except KeyboardInterrupt:
    client.disconnect()
