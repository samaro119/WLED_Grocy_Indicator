#!/usr/bin/env python

# General imports
import math
import time
import random

# Sunset/Sunrise imports and definitions
from datetime import datetime
from astral.sun import sun
from astral.geocoder import database, lookup
from pytz import timezone  # Import pytz for timezone handling

city_name = "Sydney"  # Replace with your city name
city = lookup(city_name, database())
city_tz = timezone(city.timezone)  # Convert city.timezone to a tzinfo object

# WLED configuration
WLED_IP = "192.168.1.120"  # Replace with your WLED strip's IP address
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

study_choreID = [35, 34, 76, 24,
				29, 40, 25, 36,
				39, 33, 44, 31,
				32, 42, 45, 43,
				27, 26, 46, 37]
chore_duetime_last = []
chore_duetime_current = []
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
			chore_colour = "(GREEN)"
			if delta <= 0:
				colours.append((255, 0, 0))
				chore_colour = "(RED)"
			else:
				colours.append((0, 255, 229))
				chore_colour = "(CYAN)"
			print(f"\t{chore_name.text.strip()}: {delta} days {chore_colour}")
			chore_duetime_current.append(delta)

def set_wled_segments(chore_ids, current_colours, brightness):
	#print(f"{len(chore_ids)} chores, {len(current_colours)} colours")


	# Define segments for each chore
	segments = []
	num_leds = 64  # Example: Total number of LEDs in the strip
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

def matrix_format():
	for i in range(1, 5):
		colours.insert(0, (1, 1, 1))
		study_choreID.insert(0, 0)

	shopping_check()
	bin_check()

def bin_check():
	study_choreID.insert(0, 0)
	study_choreID.insert(0, 0)
	study_choreID.insert(0, 0)
	study_choreID.insert(0, 0)

	week_number = int(time.strftime("%U"))+1
	print()
	print("\n\tWeek number:", week_number)

	day_number = int(datetime.today().weekday())
	print(f"\tDay number of the week: {day_number}")
	if day_number < 3:
		if week_number % 2 == 0:
			print("\tGreen bin week")
			for i in range(1, 3):
				colours.insert(0, (0, 255, 0))
		else:
			print("\tYellow bin week")
			for i in range(1, 3):
				colours.insert(0, (255, 255, 0))
		for i in range(1, 3):
			colours.insert(0, (255, 0, 0))
	else:
		print("\tnot early week")
		randRed = random.randint(0, 255)
		randGreen = random.randint(0, 255)
		randBlue = random.randint(0, 255)
		print(f"Random colour is: {randRed}, {randGreen}, {randBlue}")
		for i in range(1, 5):
			colours.insert(0, (randRed, randGreen, randBlue))

def shopping_check():
	study_choreID.append(0)
	study_choreID.append(0)
	study_choreID.append(0)
	study_choreID.append(0)

	page = session.get(CHORE_URL)
	soup = BeautifulSoup(page.content, "html.parser")

	current_datetime = datetime.now()
	output_datetime = current_datetime.strftime("%H:%M %d-%m-%Y")
	chore_data = soup.find(id="chore-95-row")
	chore_name = chore_data.find("td", class_="chorecard-trigger cursor-link")
	chore_duetime = chore_data.find("time")

	match = re.search(r'datetime="([^"]+)"', str(chore_duetime))

	if match:
		date_only = match.group(1).split(" ")[0]
		extracted_date = datetime.strptime(date_only, "%Y-%m-%d")
		delta = (extracted_date.date() - current_datetime.date()).days
		chore_colour = "blank"
		if delta <= 0:
			for i in range(1, 5):
				colours.append((0, 255, 0))
			chore_colour = "(GREEN)"
		elif delta < 2:
			for i in range(1, 4):
				colours.append((0, 255, 0))
			colours.append((0, 0, 0))
			chore_colour = "(GREEN)"
		elif delta < 3:
			for i in range(1, 3):
				colours.append((0, 255, 0))
			for i in range(1, 3):
				colours.append((0, 0, 0))
			chore_colour = "(GREEN)"
		elif delta < 4:
			colours.append((0, 255, 0))
			for i in range(1, 4):
				colours.append((0, 0, 0))
		else:
			for i in range(1, 5):
				colours.append((0, 0, 0))
			chore_colour = "(BLANK)"
		print(f"\t{chore_name.text.strip()}: {delta} days {chore_colour}")

try:
	while True:
		time.sleep(0.01)
		colours = []
		grocy_update()
		matrix_format()
		#print(colours)
		if chore_duetime_last == chore_duetime_current:
			print("\tLED update not required")
		else:
			chore_duetime_last = chore_duetime_current
			chore_duetime_current = []
			if is_nighttime():
				set_wled_segments(study_choreID, colours, 5)
			else:
				set_wled_segments(study_choreID, colours, 20)

		study_choreID = [35, 34, 76, 24,
						29, 40, 25, 36,
						39, 33, 44, 31,
						32, 42, 45, 43,
						27, 26, 46, 37]
		print("---------------------------------------------------------------")
		time.sleep(60)

except KeyboardInterrupt:
	pass

