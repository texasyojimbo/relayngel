from flask import Flask
from flask import request, jsonify
app = Flask(__name__)

import os
import sys
import time
import serial
import subprocess

import ftd2xx as ft
import xml.etree.ElementTree as ET


### Parse configuration file and setup hardware

tree = ET.parse('config.xml')
root = tree.getroot()

def confErrorExit(message):
    print (" ! Configuration config.xml is invalid: "+message)
    sys.exit(1)

if root.tag != "relayngel":
    confErrorExit("Root tag is invalid")

relay_index = -1

for relay in root:
    relay_index     = relay.get("index")
    relay_type      = relay.get("type")
    print (" ~ Relay Device Configured:\n ~ #"+relay_index+"\tType: "+relay_type)
    device_index = -1
    for device in relay:
        device_index        = device.get("index")
        device_action       = device.get("on")
        device_action_tuple = device_action.split(",")
        item_number=0
        for item_state in device_action_tuple:
            if item_state == "1":
                item_state_tag = "ON"
            elif item_state == "0":
                item_state_tag = "OFF"
            else:
                item_state_tag = "NULL"
        if relay_type == "PROCESS":
            item_state_tag = device_action
            print (" ~\t SDRAngel Device "+str(device_index)+"\tProcess "+str(item_number)+"\tProcess Called (when Device Active): "+item_state_tag)
        else:
            print (" ~\t SDRAngel Device "+str(device_index)+"\tRelay "+str(item_number)+"\tRelay State (When Device Active): "+item_state_tag)
        item_number += 1

    if device_index == -1:
        confErrorExit("No device actions configured where relay_index="+str(relay_index))

if relay_index == -1:
    confErrorExit("No relay devices configured")

if device_index == -1:
    confErrorExit("No device actions configured where relay_index="+str(relay_index))


### Define activity and inactivity functions

def setRelay(rcvd_dev_index,rcvd_dev_state):
    
    for relay in root:
        relay_index     = relay.get("index")
        relay_type      = relay.get("type")

# FTDI type devices for example Sainsmart and Quimat 4 channel USB relays

        if relay_type == "FTDI_1982-USB4CH":
        
            relay_serial    = relay.get("serial_number")

            ON  = True
            OFF = False
            RELAY_ADDR = ( 0x01, 0x02, 0x04, 0x08 )

            ftdi_dev_list_index = 0
            ftdi_dev_index = -1

            ftdi_dev_list = ft.listDevices()

            for item in ftdi_dev_list:
                if item == relay_serial:
                    ftdi_dev_index = ftdi_dev_list_index
                else:
                    ftdi_dev_list_index += 1
            
            if ftdi_dev_index == -1:
                confErrorExit ("FTDI_1982-USB4CH Device with Serial# "+str(relay_serial)+"Not Found.")

            ftdi_dev = ft.open(ftdi_dev_index)

            ftdi_dev.setBitMode(0xFF, 0x01)  # sets BitBang mode

            def setRelaySub(relay_sub_index, relay_sub_state):
                ftdi_dev_relayStates = ftdi_dev.getBitMode()
                if relay_sub_state == ON:
                    ftdi_dev.write( chr( ftdi_dev_relayStates | relay_sub_index ))
                if relay_sub_state == OFF:
                    ftdi_dev.write( chr( ftdi_dev_relayStates & ~relay_sub_index ))

            for device in relay:
                device_index = device.get("index")
                if device_index == str(rcvd_dev_index):
                    if rcvd_dev_state == 0:
                        device_action = device.get("off")
                        device_delay = device.get("delay_off")
                    if rcvd_dev_state == 1:
                        device_action = device.get("on")
                        device_delay = device.get("delay_on")
                    device_action_tuple = device_action.split(",")
                    device_delay_tuple = device_delay.split(",")
                    item_number=0
                    for item_state in device_action_tuple:
                        item_state_tag = "Null"
                        device_delay = int(device_delay_tuple[item_number])
                        device_delay = device_delay/1000.00
                        if item_state == "1":
                            time.sleep(device_delay)
                            item_state_tag = ON
                        elif item_state == "0":
                            time.sleep(device_delay)
                            item_state_tag = OFF
                        if item_state_tag != "Null":
                            setRelaySub(RELAY_ADDR[item_number], item_state_tag) 
                        item_number += 1
                        if item_number > 4:
                            confErrorExit ("More channels specified than are available on this device")
            
            state_string = str('{0:04b}'.format(ftdi_dev.getBitMode()))[::-1]
            print (" ! Updated State for Relay "+relay_type+" with s/n "+relay_serial+": "+state_string)           
            ftdi_dev.close()                    


# CH341 type devices particularly the LC Technology LCUS Type 1


        if relay_type == "CH341_LCUS-1":

            relay_port=relay.get("port")
            relay_baud=relay.get("baud")

            ser=serial.Serial()
            ser.port=relay_port
            ser.baud=relay_baud
            ser.open()
            
            for device in relay:
                device_index = device.get("index")
                device_delay = 0
                if device_index == str(rcvd_dev_index):
                    if rcvd_dev_state == 1:
                        device_action = device.get("on")
                        device_delay = int(device.get("delay_on"))
                    elif rcvd_dev_state == 0:
                        device_action = device.get("off")
                        device_delay = int(device.get("delay_off"))
                    device_delay = device_delay/1000.00
                    if device_action == "1":
                            time.sleep(device_delay)
                            ser.write("A00101A2".decode('hex'))
                            print (" ! Updated State for Relay "+relay_type+" on "+relay_port+": 1")
                    elif device_action == "0":
                            time.sleep(device_delay)
                            ser.write("A00100A1".decode('hex'))
                            print (" ! Updated State for Relay "+relay_type+" on "+relay_port+": 0")
            ser.close()

# Call a program instead of a device. This will allow facilitation of relays without good Python support
# as well as permit other actions (logging transmissions to file, etc).

        if relay_type == "PROCESS":
        
            for device in relay:
                device_index = device.get("index")
                device_delay = 0
                if device_index == str(rcvd_dev_index):
                    if rcvd_dev_state == 1:
                        device_action = device.get("on")
                        device_delay = int(device.get("delay_on"))
                    elif rcvd_dev_state == 0:
                        device_action = device.get("off")
                        device_delay = int(device.get("delay_off"))
                    device_delay = device_delay/1000.00
                    time.sleep(device_delay)
                    process_name = device_action.split(" ")
                    with open(os.devnull, "w") as devnull:
                        process_return_value = subprocess.call(process_name, stdout=devnull, stderr=devnull)
                    print (" ~ Process "+device_action+" was called and returned "+str(process_return_value))



# Below this point is heavily rooted in reversapi.py
# by Edouard F4EXB. 

@app.route('/sdrangel')
def hello_sdrangel():
    return 'Hello, SDRangel!'


@app.route('/sdrangel/deviceset/<int:deviceset_index>/device/run', methods=['GET', 'POST', 'DELETE'])
def device_run(deviceset_index):
    ''' Reply with the expected reply of a working device '''
    if request.method == 'POST':
        print(" ? Start Request for SDRAngel Device %d" % deviceset_index)
        reply = { "state": "idle" }
        setRelay(deviceset_index,1)
        return jsonify(reply)
    elif request.method == 'DELETE':
        print(" ? Stop Request for SDRAngel Device %d" % deviceset_index)
        reply = { "state": "running" }
        setRelay(deviceset_index,0)
        return jsonify(reply)
    elif request.method == 'GET':
        return "RUN device %d" % deviceset_index


@app.route('/sdrangel/deviceset/<int:deviceset_index>/device/settings', methods=['GET', 'PATCH', 'PUT'])
def device_settings(deviceset_index):
    ''' Reply with a copy of the device setting structure received '''
    content = request.get_json(silent=True)
    if request.method == 'PATCH':
        # Not yet implemented
        print(" ? Partial update of device %d" % deviceset_index)
        return jsonify(content)
    if request.method == 'PUT':
        # Not yet implemented
        print(" ? Full update of device %d" % deviceset_index)
        return jsonify(content)
    if request.method == 'GET':
        return 'GET settings for device %d' % deviceset_index


@app.route('/sdrangel/deviceset/<int:deviceset_index>/channel/<int:channel_index>/settings', methods=['GET', 'PATCH', 'PUT'])
def channel_settings(deviceset_index, channel_index):
    ''' Reply with a copy of the channel setting structure received '''
    content = request.get_json(silent=True)
    if request.method == 'PATCH':
        # Not yet implemented
        print(" ? Partial update of device %d channel %d" % (deviceset_index, channel_index))
        return jsonify(content)
    if request.method == 'PUT':
        # Not yet implemented
        print(" ? Full update of device %d channel %d" % (deviceset_index, channel_index))
        return jsonify(content)
    if request.method == 'GET':
        return 'GET settings for device %d and channel %d' % (deviceset_index, channel_index)
