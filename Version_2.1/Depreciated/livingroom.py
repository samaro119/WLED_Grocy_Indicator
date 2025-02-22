#!/usr/bin/env python

# General imports
import math
import time

# Sunset/Sunrise imports and definitions
from datetime import datetime
from astral.sun import sun
from astral.geocoder import database, lookup
from pytz import timezone  # Import pytz for timezone handling

city_name = "Sydney"  # Replace with your city name
city = lookup(city_name, database())
city_tz = timezone(city.timezone)  # Convert city.timezone to a tzinfo object

# WLED configuration
WLED_IP = "192.168.1.100"  # Replace with your WLED strip's IP address
WLED_STATE_URL = f"http://{WLED_IP}/json/state"

# Grocy web scrape imports and setup
import requests
from bs4 import BeautifulSoup
import re

BASE_URL = "http://192.168.1.116:9283"
LOGIN_URL = f"{BASE_URL}/login"

credentials = {
	"username": "Sam",
	"password": "Sam",
}
session = requests.Session()

# Send a POST request to log in
response = session.post(LOGIN_URL, data=credentials)

# Check if login was successful
if response.ok and "Logout" in response.text:  # Adjust the check based on Grocy's response
	print(f"Grocy login successful!		{BASE_URL}\n")
else:
	print("Login failed. Please check your credentials.\n")


CHORE_URL = f"{BASE_URL}/choresoverview"

study_choreID = [96, 72, 91, 92, 93, 94, 20, 21, 22]

colour_index = [(150, 50, 250), (98, 36, 77), (0, 250, 250)]

colours = []



def grocy_update():
	page = session.get(CHORE_URL)

	soup = BeautifulSoup(page.content, "html.parser")

	current_datetime = datetime.now()
	output_datetime = current_datetime.strftime("%H:%M %d-%m-%Y")
	print(f"\nUpdate ({output_datetime}):\n")

	for current_choreID in study_choreID:
		chore_data = soup.find(id=f"chore-{current_choreID}-row")
		chore_name = chore_data.find("td", class_="chorecard-trigger cursor-link")
		#print(chore_name.text.strip())
		chore_duetime = chore_data.find("time")
		#print(chore_duetime)
		match = re.search(r'datetime="([^"]+)"', str(chore_duetime))
		#print(match)
		if match:
			date_only = match.group(1).split(" ")[0]
			extracted_date = datetime.strptime(date_only, "%Y-%m-%d")
			delta = (extracted_date.date() - current_datetime.date()).days
			chore_colour = "(CYAN)"
			if delta <= 0:
				colours.append(colour_index[0])
				chore_colour = "(RED), Bad :("
			elif delta < 4 and 1 == 0:
				colours.append(colour_index[1])
				chore_colour = "getting closeee to dueeeee..."
			else:
				colours.append(colour_index[2])
				chore_colour = "(CYAN), Good!"
			print(f"\t{chore_name.text.strip()}: {delta} days {chore_colour}")
		else:
			print("no match!")
			print(match)



def set_wled_segments(chore_ids, current_colours, brightness):
	if len(chore_ids) != len(current_colours):
		print("Error: Number of colours must match number of chores.")
		print(f"{len(chore_ids)} chores, {len(current_colours)} colours")
		return

	# Define segments for each chore
	segments = []
	num_leds = 84  # Example: Total number of LEDs in the strip
	leds_per_segment = num_leds // len(chore_ids)

	for i, (chore_id, color) in enumerate(zip(chore_ids, current_colours)):
		segment = {
			"start": i * leds_per_segment,            # Start LED index
			"stop": (i + 1) * leds_per_segment,  # Stop LED index - 1
			"col": [list(color)],                    # Colour (RGB tuple to list)
			"fx": 0                                  # Effect ID (0 = solid)
		}
		segments.append(segment)

	payload = {
		"on": True,
		"bri": brightness,
		"seg": segments
	}

	# Send the payload to WLED
	response = requests.post(WLED_STATE_URL, json=payload)
	if response.ok:
		print(f"\n\tWLED ({WLED_IP}) segment update successful!")
	else:
		print("Failed to update WLED segments.")



def is_nighttime():
	s = sun(city.observer, date=datetime.now(city_tz))  # Use the corrected timezone
	now = datetime.now(city_tz)  # Use the tzinfo object

	return now < s["sunrise"] or now > s["sunset"]


try:
	while True:
		time.sleep(0.01)
		colours = []
		grocy_update()
		if not is_nighttime():
			set_wled_segments(study_choreID, colours, 250)
		print("---------------------------------------------------------------")


		time.sleep(60)
except KeyboardInterrupt:
	print("keyboard exit")
	pass

