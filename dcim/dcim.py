#!usr/bin/python

import requests
import sys
import getpass
import json
import readline

BASE_URL = 'https://{uri}/api/1.0/'  # This is production D42


def creds():
    username = raw_input("Enter Username: ")
    password = getpass.getpass()
    return username, password

def login(): 
    global auth
    auth = creds()

def get_buildings():
    url = BASE_URL + "buildings/"
    r = requests.get(url, auth=(auth[0], auth[1]), verify=False)
    print json.dumps(r.json(), sort_keys=True, indent=4, separators=(',', ': '))


def get_serial_numbers():
    url = BASE_URL + "devices/serial/"
    serialNumber = raw_input("Enter the device serial number:")
    serialUrl = url + serialNumber + "/"
    r = requests.get(serialUrl, auth=(auth[0], auth[1]), verify=False)
    print json.dumps(r.json(), sort_keys=True, indent=4, separators=(',', ': '))


def get_room_id(username, password):
    url = BASE_URL + "rooms/"
    r = requests.get(url, auth=(username, password), verify=False)
    json_data = json.loads(r.text)

    rooms_dictionary = None
    for key, value in json_data.iteritems():  # Get the room list from the dict and assign it
        if key == 'rooms':
            rooms_dictionary = value

    print "Choose a room ID:"

    buildings = None
    for item in rooms_dictionary:
        buildings = item
        for key, value in buildings.iteritems():
            if key == 'building':
                print "Building: " + value
            if key == 'room_id':
                print "Room ID: " + str(value)
            if key == 'name':
                print "Name: " + value

    room_id = input("Enter the room ID number:")
    return room_id


def output_room(room_id):
    url = BASE_URL + "rooms/" + str(room_id) + "/"
    r = requests.get(url, auth=(auth[0], auth[1]), verify=False)
    print json.dumps(r.json(), sort_keys=True, indent=4, separators=(',', ': '))


def get_rack_id(room_id, username, password):
    rack_name = raw_input("Enter the rack you are looking for:")
    url = BASE_URL + "rooms/" + str(room_id) + "/"
    r = requests.get(url, auth=(username, password), verify=False)
    json_data = json.loads(r.text)

    racks_dictionary = None
    for key, value in json_data.iteritems():
        if key == "racks":
            racks_dictionary = value

    device_dictionary = None  # Create empty var
    for rack in racks_dictionary:  # Pull out the list of racks
        device_dictionary = rack
        for key, value in device_dictionary.iteritems(): # Pull out racks dictionary (includes info of that rack)
            rack_info = value
            for key, value in rack_info.iteritems():  # Find name of rack user wants
                if value == rack_name:
                    print "Rack Name: " + str(value)
                    for key, value in rack_info.iteritems():  # Go back through dictionary and grab the rack_id
                        if key == 'rack_id':
                            print "Rack ID: " + str(value)
                            rack_id = value
                            return rack_id


def output_devices(rack_id, username, password):
    url = BASE_URL + "racks/" + str(rack_id) + '/'
    #auth = creds()
    r = requests.get(url, auth=(username, password), verify=False)
    print json.dumps(r.json(), sort_keys=True, indent=4, separators=(',', ': '))
