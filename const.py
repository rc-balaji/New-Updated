# Configuration files
CONFIG_FILE = "jsons/config.json"
SCHEDULE_FILE = "jsons/data.json"

# Default configuration
DEFAULT_CONFIG = {
    "SSID": "KT-AP",
    "PASSWORD": "1234567890",
    "KIT_NO": "1",
    "STATIC_NO": "1",
}

DEFAULT_SCHEDULE = [
    {
        "color": [0, 0, 0],
        "led_pin": 12,
        "button_pin": 13,
        "schedules": [],
        "enabled": True,
        "clicked": False,
    },
    {
        "color": [0, 0, 0],
        "led_pin": 25,
        "button_pin": 14,
        "schedules": [],
        "enabled": True,
        "clicked": False,
    },
    {
        "color": [0, 0, 0],
        "led_pin": 26,
        "button_pin": 15,
        "schedules": [],
        "enabled": True,
        "clicked": False,
    },
    {
        "color": [0, 0, 0],
        "led_pin": 27,
        "button_pin": 16,
        "schedules": [],
        "enabled": True,
        "clicked": False,
    },
]

# Predefined color options (8 colors) - now in RGB format [R, G, B]
COLOR_OPTIONS = [
    {"name": "White", "value": [255, 255, 255]},
    {"name": "Red", "value": [255, 0, 0]},
    {"name": "Green", "value": [0, 255, 0]},
    {"name": "Blue", "value": [0, 0, 255]},
    {"name": "Yellow", "value": [255, 255, 0]},
    {"name": "Cyan", "value": [0, 255, 255]},
    {"name": "Magenta", "value": [255, 0, 255]},
    {"name": "Orange", "value": [255, 165, 0]},
]


import uos
import json


MAIN_MENU_HTML = "pages/main.txt"
AP_SETUP_HTML = "pages/ap.txt"
SCHEDULE_SETUP_HTML = "pages/sch.txt"
TIME_MANAGEMENT_HTML = "pages/time.txt"


# Load HTML templates
try:
    with open(MAIN_MENU_HTML, "r") as file:
        MAIN_MENU = file.read()
except:
    MAIN_MENU = "<h1>Main Menu</h1><a href='/setup-ap'>AP Setup</a><br><a href='/setup-schedule'>Schedule Setup</a>"

try:
    with open(AP_SETUP_HTML, "r") as file:
        AP_SETUP_TEMPLATE = file.read()
except:
    AP_SETUP_TEMPLATE = "<h1>AP Setup</h1><form method='post' action='/save-ap'>SSID: <input name='ssid' value='{ssid}'><br>Password: <input name='password' value='{password}'><br>Kit No: <input name='kit_no' value='{kit_no}'><br>Static No: <input name='static_no' value='{static_no}'><br><button type='submit'>Save</button></form>"

try:
    with open(SCHEDULE_SETUP_HTML, "r") as file:
        SCHEDULE_SETUP_TEMPLATE = file.read()
except:
    SCHEDULE_SETUP_TEMPLATE = "<h1>Schedule Setup - Device {device_id}</h1><div>Device: <a href='/setup-schedule/0'>1</a> <a href='/setup-schedule/1'>2</a> <a href='/setup-schedule/2'>3</a> <a href='/setup-schedule/3'>4</a></div>{schedule_entries}"
try:
    with open(TIME_MANAGEMENT_HTML, "r") as file:
        TIME_MANAGEMENT_TEMPLATE = file.read()
except:
    TIME_MANAGEMENT_TEMPLATE = "<h1>Schedule Setup - Device {device_id}</h1><div>Device: <a href='/setup-schedule/0'>1</a> <a href='/setup-schedule/1'>2</a> <a href='/setup-schedule/2'>3</a> <a href='/setup-schedule/3'>4</a></div>{schedule_entries}"
