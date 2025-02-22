import math
import time
from datetime import datetime
from astral.sun import sun
from astral.geocoder import database, lookup
from pytz import timezone
import requests
from bs4 import BeautifulSoup
import re

def setup_city(city_name):
    """Set up city location and timezone for sunrise/sunset calculations."""
    city = lookup(city_name, database())
    city_tz = timezone(city.timezone)
    return city, city_tz

def login_to_grocy(base_url, username, password):
    """Logs into Grocy and returns a session object."""
    login_url = f"{base_url}/login"
    session = requests.Session()
    credentials = {"username": username, "password": password}
    response = session.post(login_url, data=credentials)

    if response.ok and "Logout" in response.text:
        print(f"Grocy login successful! {base_url}\n")
        return session
    else:
        print("Login failed. Please check your credentials.\n")
        return None

def grocy_update(session, chore_url, study_chore_ids, colour_index):
    # Fetches chore data from Grocy and determines urgency colours.
    page = session.get(chore_url)
    soup = BeautifulSoup(page.content, "html.parser")

    current_datetime = datetime.now()
    output_datetime = current_datetime.strftime("%H:%M %d-%m-%Y")

    colours = []

    for current_choreID in study_chore_ids:
        chore_data = soup.find(id=f"chore-{current_choreID}-row")
        if not chore_data:
            print(f"Chore ID {current_choreID} not found.")
            continue

        chore_name = chore_data.find("td", class_="chorecard-trigger cursor-link")
        chore_duetime = chore_data.find("time")
        match = re.search(r'datetime="([^"]+)"', str(chore_duetime))

        if match:
            date_only = match.group(1).split(" ")[0]
            extracted_date = datetime.strptime(date_only, "%Y-%m-%d")
            delta = (extracted_date.date() - current_datetime.date()).days
            chore_colour = "(CYAN)"

            if delta <= 0:
                colours.append(colour_index[0])
                chore_colour = "Bad :("
            else:
                colours.append(colour_index[2])
                chore_colour = "Good!"

            print(f"\t{chore_name.text.strip()}: {delta} days {chore_colour}")
        else:
            print(f"Failed to extract due date for chore {current_choreID}.")

    return colours

def set_wled_segments(wled_ip, chore_ids, current_colours, num_leds, brightness):
    # Sends a request to WLED to set LED segments based on chore urgency.
    if len(chore_ids) != len(current_colours):
        print("Error: Number of colours must match number of chores.")
        return

    wled_state_url = f"http://{wled_ip}/json/state"
    leds_per_segment = num_leds // len(chore_ids)
    segments = []

    for i, color in enumerate(current_colours):
        segment = {
            "start": i * leds_per_segment,
            "stop": (i + 1) * leds_per_segment,
            "col": [list(color)],
            "fx": 0
        }
        segments.append(segment)

    payload = {"on": True, "bri": brightness, "seg": segments}
    response = requests.post(wled_state_url, json=payload)

    if response.ok:
        print(f"\tWLED ({wled_ip}) segment update successful!")
    else:
        print("Failed to update WLED segments.")

def is_nighttime(city, city_tz):
    # Determines if it's currently nighttime in the given city.
    s = sun(city.observer, date=datetime.now(city_tz))
    now = datetime.now(city_tz)
    return now < s["sunrise"] or now > s["sunset"]
