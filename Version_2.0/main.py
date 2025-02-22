#!/usr/bin/env python

import time
from grocy_wled import (
    setup_city,
    login_to_grocy,
    grocy_update,
    set_wled_segments,
    is_nighttime
)

# ==== CONFIGURATION ====
CITY_NAME = "Sydney"
GROCY_URL = "http://192.168.1.116:9283"
# Living room WLED details
WLED_IP_LIVINGROOM = "192.168.1.100"
LIVINGROOM_CHORE_IDS = [96, 72, 91, 92, 93, 94, 20, 21, 22]
livingroom_colours_previous = []
# Bedroom WLED details
WLED_IP_BEDROOM = "192.168.1.108"
BEDROOM_CHORE_IDS = [61, 58, 57, 68, 52, 51, 60]
bedroom_colours_previous = []

COLOUR_INDEX = [(150, 50, 250), (98, 36, 77), (0, 250, 250)]

# ==== INITIAL SETUP ====
city, city_tz = setup_city(CITY_NAME)
session = login_to_grocy(GROCY_URL, "Sam", "Sam")

if not session:
    exit("Exiting due to failed login.")

CHORE_URL = f"{GROCY_URL}/choresoverview"

# ==== MAIN LOOP ====
try:
    while True:
        time.sleep(0.01)

        current_time = time.localtime()
        output_time = time.strftime("%H:%M %d-%m-%Y", current_time)
        print(f"\nUpdate ({output_time}):")

        print("\n\tLiving Room Update:")
        livingroom_colours = grocy_update(session, CHORE_URL, LIVINGROOM_CHORE_IDS, COLOUR_INDEX)
        print("\n\tBedroom Update:")
        bedroom_colours = grocy_update(session, CHORE_URL, BEDROOM_CHORE_IDS, COLOUR_INDEX)

        if not is_nighttime(city, city_tz):
            print("\n\tUpdating WLED Instances:")
            if livingroom_colours == livingroom_colours_previous:
                print("\tWLED ("+WLED_IP_LIVINGROOM+") update not required")
            else:
                livingroom_colours_previous = livingroom_colours
                set_wled_segments(WLED_IP_LIVINGROOM, LIVINGROOM_CHORE_IDS, livingroom_colours, 84, 250)
            if bedroom_colours == bedroom_colours_previous:
                print("\tWLED ("+WLED_IP_BEDROOM+") update not required")
            else:
                bedroom_colours_previous = bedroom_colours
                set_wled_segments(WLED_IP_BEDROOM, BEDROOM_CHORE_IDS, bedroom_colours, 43, 50)

        print("---------------------------------------------------------------")
        time.sleep(10)

except KeyboardInterrupt:
    print("Keyboard exit")
