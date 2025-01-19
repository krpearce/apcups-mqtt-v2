# Introduction 
A simple MQTT client for publishing APC UPS status changes.

**This is an updated version which will actually work based on  JamieTemple's excellent work**
Main edits:
- The original script was using an outdated API version of the paho-mqtt library. As of paho-mqtt version 2.0, a callback_api_version parameter is required for the mqtt.Client class
  - Updated the mqtt.Client initialization to include callback_api_version=5 as required by paho-mqtt 2.0.
- No port was defined in the original script
  - Added default mqtt port 1883 in the script

# Getting Started

## Platform support

This script has been tested on Debian Linux using a python venv. It should probably run fine on any other distros.

Although completely untested, there is a fair chance that most of it might work on Windows as well.

## Dependencies

This script is of absolutely no use whatsoever unless you've installed `apcupsd` (and have a connected UPS!).

This script is designed to run on Python 3. It'll probably work on Python 2 as well, but attempt at your own risk ;)

This script depends on the following Pyton libraries:

```
configparser
paho-mqtt
```

## Configuration
Before you begin, you need to modify the configuration file:

```
[mqtt]
broker_address  = <your MQTT broker address>
broker_username = <your MQTT broker user name>
broker_password = <your MQTT broker password>
client_name     = <name this service will expose itself to the MQTT broker as>
root_topic      = <root topic for publishing messages under>
```

## Running in python venv

```
python3 -m venv upsmqtt
source upsmqtt/bin/activate
pip3 install -r requirements.txt
python3 apcups-mqtt.py
```

## Run everything as a systemd services

### Enable and start apcupsd service
We first need to enable the service apcupsd
```
systemctl enable apcupsd
systemctl start apcupsd
```
Now verify that the service runs fine `systemctl status apcupsd`

### Enable apcups-mqtt-v2 service
Copy the example systemd unit file [apcups-mqtt.service](https://github.com/giovi321/apcups-mqtt-v2/blob/master/apcups-mqtt.service) to the directory `/etc/systemd/system/`.
Edit the unit file according to your venv and enable the service:
```
systemctl enable apcups-mqtt.service
systemctl start apcups-mqtt.service
```
Now verify that the service runs fine `systemctl status apcups-mqtt.service`
You can debug it using `journalctl -u apcups-mqtt.service`


# References
https://www.cyberciti.biz/faq/debian-ubuntu-centos-rhel-install-apcups/

http://www.apcupsd.org/manual/manual.html#basic-user-s-guide

https://github.com/JamieTemple/apcups-mqtt

