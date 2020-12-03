#!usr/bin/python

import dcim
import sys

def main():
    auth = dcim.creds()
#    dcim.get_buildings()  - WORKS
#    dcim.get_serial_numbers()  - WORKS
#    dcim.output_room(dcim.get_room_id())  - WORKS

    room_id = dcim.get_room_id(auth[0], auth[1])
    rack_id = dcim.get_rack_id(room_id, auth[0], auth[1])

    dcim.output_devices(rack_id, auth[0], auth[1])

    sys.exit(0)

if __name__ == "__main__":
    main()
