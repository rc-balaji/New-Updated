import os


# "config.json":"""

# {
#   "PASSWORD": "",
#   "KIT_NO": "",
#   "SSID": "",
#   "SERVER_NO": "",
#   "STATIC_NO": ""
# }


# """


file_data = {
    "Bin_Constants.py": """




# Bin_Constants.py

import json

from Bins import Bin

class BinConstants:
    def __init__(self, rack_id, bins_config,bin_manager,server_ip,kt_id,sta):
        self.bins = [Bin(bin_cfg, idx, rack_id,bin_manager=bin_manager,server_ip=server_ip,kt_id=kt_id,sta=sta) for idx, bin_cfg in enumerate(bins_config)]
        

    

    



    



""",
    "config.json": """

{
  "PASSWORD": "",
  "KIT_NO": "",
  "SSID": "",
  "SERVER_NO": "",
  "STATIC_NO": ""
}



""",
    "bin_queue.json": """
{ "1": [], "0": [], "3": [], "2": [] }

""",
    "Bins.py": """

import machine
from neopixel import NeoPixel

from file_opertaions import get_bin_queue,set_bin_queue,get_data,set_data , add_to_queue
import time

import gc

class BinManager:
    def __init__(self):
        # self._active_bins = []
        self._buzzer_pin = 32
        self._relay_pin = 33
        self._buzzer = machine.Pin(self._buzzer_pin, machine.Pin.OUT)
        self._relay = machine.Pin(self._relay_pin, machine.Pin.OUT)
        self.waiting_time = 600
        
        self.time_queue = {
            0 : {
                
                "time" : 0,
                "wait_state" : False
            },
            1 : {
                
                "time" : 0,
                "wait_state" : False
            },
            2 : {
                
                "time" : 0,
                "wait_state" : False
            },
            3 : {
                
                "time" : 0,
                "wait_state" : False
            }
            
        }

    def turn_on_buzzer(self):
        self._buzzer.on()
        # self._relay.on()
    
    def turn_off_buzzer(self):
        self._buzzer.off()
        # self._relay.off()

    
    def turn_on_relay(self):
        # self._buzzer.on()
        self._relay.off()
    
    def turn_off_relay(self):
        # self._buzzer.off()
        self._relay.on()

    # def check_state(self):
    #     isON = False

    #     for index in range(4):
    #         wait_state = self.time_queue[index]["wait_state"]
    #         curr_time = self.time_queue[index]["time"]

    #         if wait_state  == True:
    #             if curr_time == 0:
    #                 isON = True
    #             else:
    #                 curr_time -= 1
    #         self.time_queue[index]["time"] = curr_time
        
    #     return isON

          
    def check_state_buzzer(self):
        data = get_data()
        if data['master']:
            return data['buzzer_on']
        return False

    def check_state_relay(self):
        data = get_data()
        if data['master']:
            return data['relay_on']
        return False

          
    def change_state(self,index,state):

        self.time_queue[index]["time"] = 0 if state=="OFF" else self.waiting_time
        self.time_queue[index]["wait_state"] = False if state=="OFF" else True


        

    

    # def add_to_active_bins(self, rack_id, bin_index, color):
    #     if (rack_id, bin_index) not in [(b[0], b[1]) for b in self._active_bins]:
    #         self._active_bins.append((rack_id, bin_index, color))
    #         print(f"Added bin {bin_index} in rack {rack_id} with color {color} to active bins.")
    #     self.check_and_update_buzzer_relay()

    # def remove_from_active_bins(self, rack_id, bin_index):
    #     self._active_bins = [b for b in self._active_bins if not (b[0] == rack_id and b[1] == bin_index)]
    #     print(f"Removed bin {bin_index} in rack {rack_id} from active bins.")
    #     self.check_and_update_buzzer_relay()

    # def check_and_update_buzzer_relay(self):
    #     if self._active_bins:
    #         self._buzzer.on()
    #         # self._relay.on()
    #         print("Buzzer and Relay turned ON")
    #     else:
    #         self._buzzer.off()
    #         # self._relay.off()
    #         print("Buzzer and Relay turned OFF")



class Bin:
    def __init__(self, bin_config, index, rack_id, bin_manager, server_ip,kt_id,sta):
        self.button_pin = bin_config['button_pin']
        self.led_pin = bin_config['led_pin']
        self.color = tuple(bin_config['colorESP'])
        self.last_pressed_time = 0
        self.clicked = bin_config['clicked']
        self.index = index
        self.rack_id = rack_id
        self.schedules = bin_config.get("schedules", [])
        self.queued_color = None
        self.active_schedules = []
        self.bin_manager = bin_manager
        self.server_ip = server_ip
        self.kt_id = kt_id
        self.sta = sta

        

        self.button = machine.Pin(self.button_pin, machine.Pin.IN, machine.Pin.PULL_UP)
        self.num_leds = 10
        self.np = NeoPixel(machine.Pin(self.led_pin), self.num_leds)

        self.button.irq(trigger=machine.Pin.IRQ_FALLING, handler=self.handle_button_press)
        print(f"Button configured on pin {self.button_pin}")

        self.initialize_leds()

    def change_led_color(self):
        for i in range(self.num_leds):
            self.np[i] = self.color
        self.np.write()
        print(f"LEDs changed to color: {self.color}")
        # self.bin_manager.add_to_active_bins(self.rack_id, self.index, self.color)
        # self.bin_manager.change_state(self.index,"ON")


    def turn_off_leds(self):
        for i in range(self.num_leds):
            self.np[i] = (0, 0, 0)
        self.np.write()
        print("LEDs turned off.")
        # self.bin_manager.change_state(self.index,"OFF")

        

    def initialize_leds(self):

        print(f"Index : {self.index} - - - Clicked : {self.clicked}  - - - Color : {self.color}")
        if self.clicked:
            self.turn_off_leds()
        else:
            self.change_led_color()

    def handle_button_press(self, pin):
        current_time = time.ticks_ms()
        if time.ticks_diff(current_time, self.last_pressed_time) > 400:
            print(f"Button pressed for bin {self.button_pin}")
            self.last_pressed_time = current_time

            bin_queue = get_bin_queue()

            data = get_data()

            self.turn_off_leds()

            if bin_queue[str(self.index)]:
                next_color = bin_queue[str(self.index)].pop(0)
                self.color = next_color
                data['bins'][self.index]['colorESP'] = list(next_color)
                self.change_led_color()
            else:
                self.turn_off_leds()
                self.clicked = True
                data['bins'][self.index]['clicked'] = True
            

            set_data(data)

            set_bin_queue(bin_queue)

            # self.bin_manager.check_and_update_buzzer_relay()
            self.send_message(self.index, 'click-change')

    def send_message(self, bin_index, operation):

        if self.rack_id == "":

            data = get_data()

            self.rack_id = data['rack_id']

        request_data = {
            'url': f"http://{self.server_ip}:5000/click/KT-{self.kt_id}",
            'data': {
                'rack_id': self.rack_id,
                'bin_idx': bin_index,
                'operation': operation
            },
            'method': 'POST',  # Set to POST since we are sending data
            'retries': 0  # Initialize retries
        }

        gc.collect()

        try:
            add_to_queue(request_data)
        except Exception as e:
            print(f"Error sending message: {e}. Adding to queue.")
            add_to_queue(request_data)  # Add to queue on exception

 

    def update_data_json_from_message(self, msg_data):
        try:
            data = get_data()
            rack_id = msg_data.get('rack_id')
            bin_idx = msg_data.get('bin_idx')

            if not rack_id or bin_idx is None:
                print("Error: Missing required fields in the message")
                return

            data["bins"][bin_idx]['clicked'] = True
            set_data(data)

            print("Data JSON updated based on received message")

        except Exception as err:
            print(f"Error updating JSON from message: {err}")













""",
    
    
    
    
    "constants.py": """



import machine
from ds3231 import DS3231
import time

from file_opertaions import read_config



class Constants:
    def __init__(self):
        self.sda_pin = machine.Pin(21)
        self.scl_pin = machine.Pin(22)

        self.i2c = machine.I2C(0, scl=self.scl_pin, sda=self.sda_pin)


        time.sleep(0.5)

        self.rtc = DS3231(self.i2c)


        self.Local = read_config()


        self.KIT_NO = self.Local.get("KIT_NO", "")
        self.STATIC_NO = self.Local.get("STATIC_NO", "")
        if self.STATIC_NO == "":
            self.STATIC_IP = self.KIT_NO

        self.SERVER_NO = self.Local.get("SERVER_NO", 0)
        self.SSID = self.Local.get("SSID", "")
        self.PASSWORD = self.Local.get("PASSWORD", "")


""",
    "data.json": """
{
  "rack_id": "",
  "KIT_ID": "",
  "bins": [
    {
      "color": [255, 255, 255],
      "led_pin": 12,
      "bin_id": "RC-1_01",
      "button_pin": 13,
      "schedules": [],
      "enabled": false,
      "colorESP": [0, 0, 0],
      "clicked": true
    },
    {
      "color": [255, 255, 255],
      "led_pin": 25,
      "bin_id": "RC-1_02",
      "button_pin": 14,
      "schedules": [],
      "enabled": false,
      "colorESP": [0, 0, 0],
      "clicked": true
    },
    {
      "color": [255, 255, 255],
      "led_pin": 26,
      "bin_id": "RC-1_03",
      "button_pin": 15,
      "schedules": [],
      "enabled": false,
      "colorESP": [0, 0, 0],
      "clicked": true
    },
    {
      "color": [255, 255, 255],
      "led_pin": 27,
      "bin_id": "RC-1_04",
      "button_pin": 16,
      "schedules": [],
      "enabled": false,
      "colorESP": [0, 0, 0],
      "clicked": true
    }
  ]
}



""",
    "ds3231.py": """
# ds3231.py

import utime
import machine
import sys





DS3231_I2C_ADDR = 104

try:
    rtc = machine.RTC()
except:
    print('Warning: machine module does not support the RTC.')
    rtc = None

def bcd2dec(bcd):
    return (((bcd & 0xf0) >> 4) * 10 + (bcd & 0x0f))

def dec2bcd(dec):
    tens, units = divmod(dec, 10)
    return (tens << 4) + units

def tobytes(num):
    return num.to_bytes(1, 'little')

class DS3231:
    def __init__(self, i2c):
        self.ds3231 = i2c
        self.timebuf = bytearray(7)
        if DS3231_I2C_ADDR not in self.ds3231.scan():
            raise RuntimeError("DS3231 not found on I2C bus at %d" % DS3231_I2C_ADDR)

    def get_time(self, set_rtc=False):
        if set_rtc:
            self.await_transition()
        else:
            self.ds3231.readfrom_mem_into(DS3231_I2C_ADDR, 0, self.timebuf)
        return self.convert(set_rtc)

    def convert(self, set_rtc=False):
        data = self.timebuf
        ss = bcd2dec(data[0])
        mm = bcd2dec(data[1])
        if data[2] & 0x40:
            hh = bcd2dec(data[2] & 0x1f)
            if data[2] & 0x20:
                hh += 12
        else:
            hh = bcd2dec(data[2])
        wday = data[3]
        DD = bcd2dec(data[4])
        MM = bcd2dec(data[5] & 0x1f)
        YY = bcd2dec(data[6])
        if data[5] & 0x80:
            YY += 2000
        else:
            YY += 1900
        result = YY, MM, DD, hh, mm, ss, wday - 1, 0
        if set_rtc:
            if rtc is None:
                secs = utime.mktime(result)
                utime.localtime(secs)
            else:
                rtc.datetime((YY, MM, DD, wday, hh, mm, ss, 0))
        return result

    def set_time(self, YY, MM, mday, hh, mm, ss, wday, yday):
        self.ds3231.writeto_mem(DS3231_I2C_ADDR, 0, tobytes(dec2bcd(ss)))
        self.ds3231.writeto_mem(DS3231_I2C_ADDR, 1, tobytes(dec2bcd(mm)))
        self.ds3231.writeto_mem(DS3231_I2C_ADDR, 2, tobytes(dec2bcd(hh)))
        self.ds3231.writeto_mem(DS3231_I2C_ADDR, 3, tobytes(dec2bcd(wday + 1)))
        self.ds3231.writeto_mem(DS3231_I2C_ADDR, 4, tobytes(dec2bcd(mday)))
        self.ds3231.writeto_mem(DS3231_I2C_ADDR, 5, tobytes(dec2bcd(MM)))
        self.ds3231.writeto_mem(DS3231_I2C_ADDR, 6, tobytes(dec2bcd(YY - 1900)))
    
    def await_transition(self):
        self.ds3231.readfrom_mem_into(DS3231_I2C_ADDR, 0, self.timebuf)
        ss = self.timebuf[0]
        while ss == self.timebuf[0]:
            self.ds3231.readfrom_mem_into(DS3231_I2C_ADDR, 0, self.timebuf)
        return self.timebuf

    def get_temperature(self):
        t = self.ds3231.readfrom_mem(DS3231_I2C_ADDR, 0x11, 2)
        i = t[0] << 8 | t[1]
        return self._twos_complement(i >> 6, 10) * 0.25

    def _twos_complement(self, input_value: int, num_bits: int) -> int:
        mask = 2 ** (num_bits - 1)
        return -(input_value & mask) + (input_value & ~mask)





""",
    "file_opertaions.py": """

import json

import urequests

bin_queue_file = '/bin_queue.json'
   
queue_file = "/queue.json"


MAX_RETRIES = 3  # Maximum number of retries for failed requests


def process_queue(server_ip, kit_no):

    # Read the queue from the file
    try:
        with open(queue_file, 'r') as file:
            queue = json.load(file)
    except Exception:
        print("Queue file not found. Initializing a new queue.")
        queue = []  # Initialize an empty queue if the file does not exist

    if not queue:
        print("No pending requests in the queue.")
        return

    # New queue to hold requests that failed processing
    new_queue = []

    # Process requests until the queue is empty
    while queue:
        request = queue.pop(0)
        data = request.get("data")
        method = request.get("method", "GET").upper()
        # retries = request.get("retries", 0)  # Number of attempts made

        url = f"http://{server_ip}:5000/click/KT-{kit_no}"

        try:
            # Send the request
            if method == "GET":
                response = urequests.get(url)
            elif method == "POST":
                response = urequests.post(url, json=data)

            if response.status_code == 200:
                print(f"Successfully processed request to {kit_no}")
            else:
                print(f"Failed to process request to {url}. Status code: {response.status_code}")
                # request["retries"] = retries + 1
                new_queue.append(request)

            response.close()

        except Exception as e:
            print(f"Error processing request to {url}: {e}")
            # request["retries"] = retries + 1
            new_queue.append(request)

        

    # Update the queue file with failed requests
    set_queue(new_queue)

    

def set_queue(queue):
    with open(queue_file, 'w') as file:
        json.dump(queue, file)

def add_to_queue(request_data):

    try:
        with open(queue_file, 'r') as file:
            queue = json.load(file)
    except Exception:
        print("Queue file not found. Initializing a new queue.")
        queue = []

    # Initialize retries for the new request
    request_data["retries"] = 0

    # Add the new request to the queue
    queue.append(request_data)

    # Save the updated queue back to the file
    with open(queue_file, 'w') as file:
        json.dump(queue, file)

    print("Request added to the queue.")


# Example usage
# Uncomment the following lines to add requests to the queue
# add_to_queue({"url": "http://example.com/api", "data": {"key": "value"}, "method": "POST"})
# process_queue()



def get_bin_queue():
    print("Called2")
    try:
        with open('/bin_queue.json', 'r') as f:
            bin_queue = json.load(f)
            print(bin_queue)
            return bin_queue
    except Exception:
        # If the file does not exist, initialize an empty queue structure
        bin_queue = {index: [] for index in range(4)}
        set_bin_queue(bin_queue)


def set_bin_queue(queue):
    with open('/bin_queue.json', 'w') as f:
        json.dump(queue, f)

def read_config():

    try:
        with open('/config.json', 'r') as file:
            config = json.load(file)
            return config
    except OSError:
        return {}


def get_data():
    
    try:
        with open('/data.json', 'r') as file:
            config = json.load(file)
            return config
    except OSError:
        return {}

def set_data(new_data):
    with open('/data.json', 'w') as file:
        json.dump(new_data, file)




""",
    "queue.json": """
[]



""",
    "schedule.py": """
import gc

import time

from file_opertaions import get_data , get_bin_queue , set_bin_queue , set_data


def check_schedules(rtc,bin_obj):
    while True:
        # Get current time from DS3231 RTC
        current_time = rtc.get_time()
        current_hour = current_time[3]
        current_minute = current_time[4]

        print(f"Current Time: {current_hour:02}:{current_minute:02}")
        data = get_data()
        
        bin_queue = get_bin_queue()
        # print(bin_queue)


        for index, _bin in enumerate(data['bins']):
            for schedule in _bin['schedules']:
                if schedule['enabled']:
                    schedule_hour, schedule_minute = map(int, schedule['time'].split(":"))
                    if current_hour == schedule_hour and current_minute == schedule_minute:
                        if bin_obj.bins[index].clicked:
                            _bin['colorESP'] = schedule['colorESP']
                            _bin['clicked'] = False
                            bin_obj.bins[index].color = tuple(schedule['colorESP'])
                            bin_obj.bins[index].change_led_color()
                            bin_obj.bins[index].clicked = False
                            bin_obj.bins[index].active_schedules.append(schedule)
                        else:
                            bin_queue[str(index)].append(tuple(schedule['colorESP']))
                            print(f"Schedule missed for bin {index}, color added to queue")
        

        # print(bin_queue)
        set_data(data)
        set_bin_queue(bin_queue)


        gc.collect()
        time.sleep(60) 






""",
    "STA_MODE.py": """
import _thread
import time

from Bins import BinManager
from file_opertaions import get_data, process_queue , get_bin_queue , set_bin_queue
from schedule import check_schedules
from Bin_Constants import BinConstants
from constants import Constants
from station import Station

import gc 

import urequests

from machine import Pin

from time import sleep

print("TP-1")
const = Constants()
bin_manager = BinManager()
sta = Station(const.SSID, const.PASSWORD, const.SERVER_NO, const.rtc, kit_id=const.KIT_NO,static_no=const.STATIC_NO)
print("TP-2")
sta.connect_to_wifi()
sta.update_data_from_server()


# Load configuration from JSON
data = get_data()
rack_id = data.get("rack_id", "")
bins_config = data.get("bins", [])





bin_obj = BinConstants(bins_config=bins_config, rack_id=rack_id, bin_manager=bin_manager,server_ip=sta.server_ip,kt_id=const.KIT_NO,sta=sta )

_thread.start_new_thread(check_schedules, (const.rtc, bin_obj))

# def chech_relay_state():

#     while True:
#         if bin_manager.check_state():
#             bin_manager.turn_on_buzzer_and_relay()
#         else:
#             bin_manager.turn_off_buzzer_and_relay()
#         print(bin_manager.time_queue)
#         time.sleep(1)

# _thread.start_new_thread(chech_relay_state , ())

def chech_buzzer_state():

    if bin_manager.check_state_buzzer():
        bin_manager.turn_on_buzzer()
    else:
        bin_manager.turn_off_buzzer()

def chech_relay_state():

    if bin_manager.check_state_relay():
        bin_manager.turn_on_relay()
    else:
        bin_manager.turn_off_relay()





def get_click_data_from_server():
        if not sta.server_ip:
            print("Server IP is not set. Generate the server IP first.")
            return

        try:
            url = f"http://{sta.server_ip}:5000/get-click/KT-{const.KIT_NO}"
            response = urequests.get(url)

            if response.status_code == 200:
                click_data = response.json()
                print("Click Data:", click_data)

                bin_queue = get_bin_queue()


                for index in click_data:

                    current_bin = bin_obj.bins[index]
                    current_bin.turn_off_leds()

                    if bin_queue[str(index)]:
                        next_color = bin_queue[str(index)].pop(0)
                        current_bin.color = next_color
                        current_bin.change_led_color()
                    else:
                        current_bin.turn_off_leds()
                        current_bin.clicked = True
                    set_bin_queue(bin_queue)
                # print("Okii")  # Print "Okii" as requested
                
            else:
                print("No clicks found for the specified KIT_ID")
                # return None

            response.close()  # Properly close the connection

        except Exception as e:
            print(f"Error fetching click data: {e}")
            return None

        finally:
            gc.collect()  # Force garbage collection


print(sta.server_ip)

led = Pin(17, Pin.OUT)

# Function to blink the LED
def blink_led():
    led.on()   # Turn the LED on
    sleep(0.5) # Wait for 0.5 seconds
    led.off()  # Turn the LED off
    sleep(0.5) # Wait for 0.5 seconds

# Function to turn the LED on
def turn_on_led():
    led.on()




print(sta.server_ip)
print(sta.local_ip)

while True:
    if sta.isconnected():
        turn_on_led()
        process_queue(sta.server_ip , const.KIT_NO)
        sta.get_time_from_server()
        sta.update_data_from_server()
        get_click_data_from_server()

        chech_buzzer_state()

        chech_relay_state()

    else:
        print("Not Connecting With Wifi")
        blink_led() 
        sta.connect_to_wifi()
        
    time.sleep(10)
    
    

print("System initialized and running.")



""",
    "station.py": """
import network
import time
import urequests
from machine import RTC
import gc
import machine

from file_opertaions import get_data , set_data , process_queue , set_bin_queue , set_queue

class Station:
    def __init__(self, ssid, password, server_no, rtc,kit_id,static_no):
        self.ssid = ssid
        self.password = password
        self.server_no = server_no  # Added server number from constructor
        self.rtc = rtc
        self.local_ip = None
        self.server_ip = None
        self.wlan = network.WLAN(network.STA_IF)
        self.kit_id = kit_id
        self.static_no = static_no

    # Connect to Wi-Fi
    def connect_to_wifi(self):
        self.wlan.active(True)
        
        # Disconnect if already connected
        if self.wlan.isconnected():
            print("Already connected to WiFi. Disconnecting...")
            self.disconnect_wifi()
            machine.reset()

        self.wlan.connect(self.ssid, self.password)
        
        max_attempts = 10
        attempt = 0
        while not self.wlan.isconnected() and attempt < max_attempts:
            print(f"Connecting to WiFi... Attempt {attempt + 1}/{max_attempts}")
            time.sleep(1)
            attempt += 1
        
        if self.wlan.isconnected():
            # self.local_ip = self.wlan.ifconfig()[0]
            # print("Connected to WiFi")
            # print("IP Address: ", self.local_ip)


            ip_info = self.wlan.ifconfig()
            print("Current IP info:", ip_info)
            ip_address = ip_info[0]
            ip_parts = ip_address.split('.')

            if len(ip_parts) == 4:
                new_ip_address = f"{ip_parts[0]}.{ip_parts[1]}.{ip_parts[2]}.{self.static_no}"
                self.server_ip = f"{ip_parts[0]}.{ip_parts[1]}.{ip_parts[2]}.{self.server_no}"
            
                self.local_ip = new_ip_address
                # Reconfigure network interface
                self.wlan.ifconfig((new_ip_address, ip_info[1], ip_info[2], ip_info[3]))
            
                time.sleep(2)  # Short wait to ensure it's applied
                new_ip_info = self.wlan.ifconfig()
                print('Updated network configuration:', new_ip_info)
                if new_ip_info[0] == new_ip_address:
                    print("IP updated successfully.")
                else:
                    print("IP update failed.")
            else:
                print("Unexpected IP address format.")

            # self.generate_server_ip()


            # process_queue(self.server_ip , self.kit_id)

            return True, self.local_ip
        else:
            print("Failed to connect to WiFi")
            self.wlan.active(False)
            gc.collect()
            return False, None
    
    def isconnected(self):
        return self.wlan.isconnected()

    # Disconnect from Wi-Fi
    def disconnect_wifi(self):
        if self.wlan.isconnected():
            self.wlan.disconnect()
            print("Disconnected from WiFi")
        self.wlan.active(False)
        gc.collect()

    # Parse ISO formatted time string
    def parse_iso_time(self, iso_string):
        date_time = iso_string.split("T")
        date_parts = date_time[0].split("-")
        year = int(date_parts[0])
        month = int(date_parts[1])
        day = int(date_parts[2])
        time_parts = date_time[1].split("+")[0].split(":")
        hour = int(time_parts[0])
        minute = int(time_parts[1])
        second = int(time_parts[2])
        return year, month, day, hour, minute, second

    # Get time from server
    def get_time_from_server(self):
        if not self.server_ip:
            print("Server IP is not set. Generate the server IP first.")
            return
        
        try:
            url = f"http://{self.server_ip}:5000/get-time1"
            response = urequests.get(url)
            if response.status_code == 200:
                time_data = response.json().get('time')
                print(f"Received time from server: {time_data}")
                year, month, day, hour, minute, second = self.parse_iso_time(time_data)
                self.rtc.set_time(year, month, day, hour, minute, second, 0, 0)
                print(f"RTC updated to: {year}-{month}-{day} {hour}:{minute}:{second}")
            else:
                print("Failed to get time from server")
            response.close()  # Properly close the connection
        except Exception as e:
            print(f"Error fetching time: {e}")
        finally:
            gc.collect()  # Force garbage collection

    def update_data_from_server(self):

        not_found =     {
  "rack_id": "",
  "KIT_ID": "",
  "bins": [
    {
      "color": [255, 255, 255],
      "colorESP": [0, 0, 0],
      "led_pin": 12,
      "bin_id": "RC-1_01",
      "button_pin": 13,
      "schedules": [],
      "enabled": False,
      "clicked": True
    },
    {
      "color": [255, 255, 255],
      "colorESP": [0, 0, 0],
      "led_pin": 25,
      "bin_id": "RC-1_02",
      "button_pin": 14,
      "schedules": [],
      "enabled": False,
      "clicked": True
    },
    {
      "color": [255, 255, 255],
      "colorESP": [0, 0, 0],
      "led_pin": 26,
      "bin_id": "RC-1_03",
      "button_pin": 15,
      "schedules": [],
      "enabled": False,
      "clicked": True
    },
    {
      "color": [255, 255, 255],
      "colorESP": [0, 0, 0],
      "led_pin": 27,
      "bin_id": "RC-1_04",
      "button_pin": 16,
      "schedules": [],
      "enabled": False,
      "clicked": True
    }
  ]
}


        new_bin_q = {"1": [], "0": [], "3": [], "2": []}


        if not self.server_ip:
            print("Server IP is not set. Generate the server IP first.")
            return

        try:
            url = f"http://{self.server_ip}:5000/get-data/KT-{self.kit_id}"
            response = urequests.get(url)

            if response.status_code == 200:
                data = response.json()
                if 'message' in data and data['message'] == 'Rack not found':
                    print("Rack not found. Setting data to an empty object.")
                    set_data(not_found)
                    set_queue([])
                    set_bin_queue(new_bin_q)
                else:
                    set_data(data)
                    print("Update data from server: Success")
                    # Further processing can be done with the received data


            response.close()  # Properly close the connection

        except Exception as e:
            print(f"Error fetching data: {e}")
              # Set data to an empty object in case of error
        finally:
            gc.collect()  # Force garbage collection

    
    # Dynamically generate the server IP address based on local IP
    def generate_server_ip(self):
        if not self.local_ip:
            print("Local IP is not set. Connect to WiFi first.")
            return None
        ip_parts = self.local_ip.split('.')
        ip_parts[-1] = str(self.server_no)  # Use the server_no from the constructor
        self.server_ip = '.'.join(ip_parts)
        return self.server_ip

    # Clean up the class instance (for memory management)
    def cleanup(self):
        self.disconnect_wifi()
        self.rtc = None
        self.local_ip = None
        self.server_ip = None
        self.wlan = None
        gc.collect()
        print("Resources cleaned up")

# Example usage
# station = Station("your_ssid", "your_password", 1, RTC())  # Specify server number directly
# wifi_connected, local_ip = station.connect_to_wifi()

# if wifi_connected:
#     station.generate_server_ip()  # Automatically uses server_no from constructor
#     station.update_data_from_server()  # Fetch data from server

# # Disconnect and clean up when done
# station.cleanup()




""",
}

AP_file = {
    "main.py": """

# main.py

import time
import machine
from neopixel import NeoPixel
import gc
gc.enable()

#Define the pin for the switch
switch_pin = machine.Pin(2, machine.Pin.IN)

curr_state = switch_pin.value()



def set_default_color():
    pins = [12, 25, 26, 27]
    neopixels = [NeoPixel(machine.Pin(pin), 10) for pin in pins]
    color_tup = [(65, 0, 0) ,(0, 65, 0) ,(0, 0, 65),(0,0,0)]


    for col in color_tup:
        for np in neopixels:
            for i in range(np.n):
                np[i] = col
            np.write() 
            time.sleep(0.05)  

set_default_color()

print("Coming")
if curr_state == 1:
    print("TP-1")
    try:
        with open('AP_MODE.py', 'r') as file:
            code = file.read()
        exec(code)
    except Exception:
        
        machine.reset()

elif curr_state == 0:
    print("TP-2")
    try:
        with open('STA_MODE.py', 'r') as file:
            code = file.read()
        exec(code)
    except Exception as err:
        print(err)
        machine.reset()
        


    """,
    "AP_MODE.py": """
# AP_MODE.py

import json
import network
import usocket as socket
import machine
from neopixel import NeoPixel
import esp
import gc
import time

gc.enable()

def set_default_color():
    pins = [12, 25, 26, 27]
    neopixels = [NeoPixel(machine.Pin(pin), 10) for pin in pins]
    for np in neopixels:
        for i in range(np.n):
            np[i] = (0, 0, 0)  # Set each LED to (0, 0, 0)
        np.write()  # Update the LEDs with the new color

set_default_color()




def setup_access_point():
    ap = network.WLAN(network.AP_IF)
    ap.active(True)
    wlan_mac = ap.config('mac')
    mac_arr = [str(i) for i in wlan_mac]
    
    # print(mac_arr)
    
    MAC_ADD = mac_arr[-2:]

    MAC_STR = "".join(MAC_ADD)
    
    # print(MAC_STR)
    
    ap.config(essid='ESP32-'+MAC_STR, password='12345678', channel=1, authmode=network.AUTH_WPA_WPA2_PSK)
    while not ap.active():
        pass
    print('AP Mode configured:', ap.ifconfig())
    return ap



def teardown_access_point(ap):
    ap.active(False)
    print("Access Point deactivated.")

def teardown_wifi(sta):
    # Initiate disconnection
    sta.disconnect()
    
    # Wait until the station is disconnected
    while sta.isconnected():
        print("Waiting for Wi-Fi to disconnect...")
        time.sleep(1)
    
    # Deactivate Wi-Fi once fully disconnected
    sta.active(False)
    print("Wi-Fi disconnected and deactivated.")


local_ip = "192.168.4.1"

def load_config():
    try:
        with open('config.json', 'r') as f:
            return json.load(f)
    except:
        return {"KIT_NO": "", "STATIC_NO": "", "SERVER_NO": "", "SSID": "", "PASSWORD": ""}

def save_config(config):
    with open('config.json', 'w') as f:
        json.dump(config, f)

def render_html(template, config, ip):
    global local_ip
    
    local_ip = ip
    for key, value in config.items():
        template = template.replace('{{' + key + '}}', value)
    
    print("TP - - 1")
    # static_no = str("120")
    if local_ip is not None:
        #print(local_ip)
        local_ip = local_ip.split(".")
        
        local_ip =  ".".join(local_ip[:-1])
        print("TF - 2")
        local_ip = local_ip + "." + config['STATIC_NO']
        print("TF - 3")
    else: 
        local_ip = "EMPTY"
    print("TP - - 2")       
    template = template.replace('{{IP_ADDRESS}}', local_ip )
    print("TF - 4")
    return template

def url_decode(url_encoded_str):
   
    result = url_encoded_str.replace('+', ' ')
    parts = result.split('%')
    decoded_str = parts[0]
    for part in parts[1:]:
        try:
            decoded_str += chr(int(part[:2], 16)) + part[2:]
        except ValueError:
            decoded_str += '%' + part
    return decoded_str

def parse_form_data(body):

    data = {}
    pairs = body.split('&')
    for pair in pairs:
        if '=' in pair:
            key, value = pair.split('=', 1)
            data[url_decode(key)] = url_decode(value)
    return data

def connect_to_wifi(ssid, password):
    sta = network.WLAN(network.STA_IF)
    sta.active(True)
    
    # If already connected, disconnect first
    if sta.isconnected():
        print("Already connected, disconnecting...")
        sta.disconnect()
    
    # Connect to the Wi-Fi network
    print(f"Connecting to {ssid}...")
    sta.connect(ssid, password)
    
    timeout = 10
    while not sta.isconnected() and timeout > 0:
        timeout -= 1
        time.sleep(1)
    
    # Check if the connection was successful
    if sta.isconnected():
        ip = sta.ifconfig()[0]
        print(f"Connected successfully, IP address: {ip}")
        return ip
    else:
        print("Failed to connect.")
        return None


def handle_request(client, config):
    request = client.recv(1024).decode('utf-8')
    if 'POST /update' in request:
        body = request.split('\\r\\n\\r\\n')[1]
        params = parse_form_data(body)
        config.update(params)
        save_config(config)
        response = 'HTTP/1.1 303 See Other\\r\\nLocation: /\\r\\n\\r\\n'
        client.send(response.encode('utf-8'))
    else:
        with open('index.txt', 'r') as f:
            html = f.read()
        ip_address = ""
        # try:
        #     ip_address = connect_to_wifi(config['SSID'], config['PASSWORD'])
        # except Exception as err:
        #     print("ERROR : ",err)
        response = render_html(html, config, ip_address)
        client.send('HTTP/1.1 200 OK\\r\\nContent-Type: text/html\\r\\n\\r\\n'.encode('utf-8'))
        client.send(response.encode('utf-8'))
        if ip_address:
            teardown_wifi(network.WLAN(network.STA_IF))
        
        
def start_server_AP():
    ap = setup_access_point()  # Setup the Access Point
    config = load_config()     # Load the configuration
    addr = socket.getaddrinfo("0.0.0.0", 80)[0][-1]
    s_ap = None
    try:
        s_ap = socket.socket()  # Create a new socket
        try:
            s_ap.bind(addr)     # Bind to the address and port
        except Exception as bind_error:
            print(f"Socket binding failed: {bind_error}")
            machine.reset()     # Resetting device if binding fails
        s_ap.listen(5)          # Start listening for clients
        print('Web server running on http://192.168.4.1:80')
    except OSError as err:
        print("Socket error during setup:", err)
        return
    client = None
    try:
        while True:
            print("TP 1")
            try:
                client, client_addr = s_ap.accept()  # Accept a client connection
                print('Client connected from', client_addr)
                handle_request(client, config)       # Handle the client request
            except OSError as client_err:
                print("Error while handling client:", client_err)
            finally:
                if client is not None:
                    client.close()  # Ensure the client socket is closed after handling
    finally:
        if s_ap is not None and ap is not None:
            s_ap.close()           
            print("TP 2")
            teardown_access_point(ap)

try:
    setup_access_point()
    start_server_AP()
except Exception as err:
    print(err)


    """,
    "index.txt": """

<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>ESP32 Configuration</title>
    <style>
      body {
        font-family: Arial, sans-serif;
        background-color: #f4f4f4;
        margin: 0;
        padding: 0;
        display: flex;
        justify-content: center;
        align-items: center;
        height: 100vh;
      }

      .container {
        background: #ffffff;
        border-radius: 8px;
        box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
        padding: 20px;
        width: 100%;
        max-width: 600px;
      }

      h2 {
        margin-top: 0;
        color: #333;
        text-align: center;
      }

      .form-group {
        margin-bottom: 15px;
      }

      .form-group label {
        display: block;
        margin-bottom: 5px;
        font-weight: bold;
        color: #555;
      }

      .form-group div {
        font-size: 16px;
        color: #333;
        margin-bottom: 5px;
      }

      .form-group input[type="text"],
      .form-group input[type="password"] {
        width: 100%;
        padding: 8px;
        border: 1px solid #ddd;
        border-radius: 4px;
        box-sizing: border-box;
      }

      .form-group input[type="checkbox"] {
        margin-right: 10px;
      }

      .form-group input[type="button"] {
        background-color: #007bff;
        color: #fff;
        border: none;
        padding: 10px 20px;
        border-radius: 4px;
        cursor: pointer;
        font-size: 16px;
        display: block;
        margin: 10px auto;
      }

      .form-group input[type="button"]:hover {
        background-color: #0056b3;
      }

      #submit_button {
        border: 1px solid green;
        border-radius: 4px;
        background-color: green;
        color: white;
        width: 100%;
        padding: 5px;
        font-size: 20px;
        font-weight: bold;
        /* font-size: large; */
      }

      .switch {
        position: relative;
        display: inline-block;
        width: 50px;
        height: 24px;
      }

      .switch input {
        opacity: 0;
        width: 0;
        height: 0;
      }

      .slider {
        position: absolute;
        cursor: pointer;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        background-color: #ccc;
        transition: 0.4s;
        border-radius: 24px;
      }

      .slider:before {
        position: absolute;
        content: "";
        height: 16px;
        width: 16px;
        border-radius: 50%;
        left: 4px;
        bottom: 4px;
        background-color: white;
        transition: 0.4s;
      }

      input:checked + .slider {
        background-color: #007bff;
      }

      input:checked + .slider:before {
        transform: translateX(26px);
      }

      .container h4 {
        color: #555;
        text-align: center;
        margin-top: 20px;
      }
    </style>
  </head>
  <body>
    <div class="container">
      <h2>ESP32 Configuration</h2>
      <!-- Toggle Switch -->
      Change Mode :
      <label class="switch">
        <input
          class="toggle-edit"
          type="checkbox"
          id="editModeSwitch"
          onchange="toggleEdit()"
        />
        <span class="slider round"></span>
      </label>
      <form id="configForm">
        <!-- Form group for KIT_NO -->
        <div class="form-group">
          <label for="KIT_NO">KIT NO:-</label>
          <div id="KIT_NO_display">{{KIT_NO}}</div>
          <input
            type="text"
            id="KIT_NO_input"
            name="KIT_NO"
            style="display: none"
          />
        </div>

        <!-- Form group for STATIC_NO -->
        <div class="form-group">
          <label for="STATIC_NO">LOCAL IP :-</label>
          <div id="STATIC_NO_display">{{STATIC_NO}}</div>
          <input
            type="text"
            id="STATIC_NO_input"
            name="STATIC_NO"
            style="display: none"
          />
        </div>

        <!-- Form group for SERVER_NO -->
        <div class="form-group">
          <label for="SERVER_NO">HOST IP :-</label>
          <div id="SERVER_NO_display">{{SERVER_NO}}</div>
          <input
            type="text"
            id="SERVER_NO_input"
            name="SERVER_NO"
            style="display: none"
          />
        </div>

        <!-- Form group for SSID -->
        <div class="form-group">
          <label for="SSID">SSID :-</label>
          <div id="SSID_display">{{SSID}}</div>
          <input
            type="text"
            id="SSID_input"
            name="SSID"
            style="display: none"
          />
        </div>

        <!-- Form group for PASSWORD -->
        <div class="form-group">
          <label for="PASSWORD">PASSWORD:-</label>
          <div id="PASSWORD_display">{{PASSWORD}}</div>
          <input
            type="password"
            id="PASSWORD_input"
            name="PASSWORD"
            style="display: none"
          />
          <!-- Show Password Checkbox -->
          <div style="display: flex; margin: 5px">
            <input
              type="checkbox"
              id="showPasswordCheckbox"
              onclick="togglePasswordVisibility()"
              style="display: none; margin-top: 5px; width: 20px; height: 20px"
            />
            <label
              for="showPasswordCheckbox"
              style="display: none; margin-top: 7px"
              id="showPasswordLabel"
              >Show Password</label
            >
          </div>
        </div>

        <input
          type="button"
          value="Save"
          onclick="submitForm()"
          id="submit_button"
          style="display: none"
        />

       
      </form>
    </div>
    <script>
      const config = {
        KIT_NO: "{{KIT_NO}}",
        STATIC_NO: "{{STATIC_NO}}",
        SERVER_NO: "{{SERVER_NO}}",
        SSID: "{{SSID}}",
        PASSWORD: "{{PASSWORD}}",
      };

      function toggleEdit() {
        var isEditing =
          document.getElementById("KIT_NO_input").style.display === "block";

        var elements = ["KIT_NO", "STATIC_NO", "SERVER_NO", "SSID", "PASSWORD"];

        elements.forEach(function (element) {
          document.getElementById(element + "_display").style.display =
            isEditing ? "block" : "none";
          document.getElementById(element + "_input").style.display = isEditing
            ? "none"
            : "block";
          if (!isEditing) {
            document.getElementById(element + "_input").value = config[element];
          }
        });

        // Show or hide the show password checkbox and label based on editing mode
        document.getElementById("showPasswordCheckbox").style.display =
          isEditing ? "none" : "block";
        document.getElementById("showPasswordLabel").style.display = isEditing
          ? "none"
          : "block";

        document.getElementById("submit_button").style.display = isEditing
          ? "none"
          : "block";
      }

      function togglePasswordVisibility() {
        var passwordInput = document.getElementById("PASSWORD_input");
        var showPasswordCheckbox = document.getElementById(
          "showPasswordCheckbox"
        );

        if (showPasswordCheckbox.checked) {
          passwordInput.type = "text";
        } else {
          passwordInput.type = "password";
        }
      }

      function submitForm() {
        var form = document.getElementById("configForm");
        var formData = new FormData(form);

        // Convert form data to an object
        var params = new URLSearchParams(formData);

        fetch("/update", {
          method: "POST",
          body: params,
        })
          .then((response) => {
            if (response.ok) {
              window.location.reload();
            } else {
              alert("Failed to update configuration");
            }
          })
          .catch((error) => {
            console.error("Error:", error);
          });
      }
    </script>
  </body>
</html>



    """,
}


# Create the files with the corresponding code strings
for filename, content in AP_file.items():
    with open(filename, "w") as file:
        file.write(content)
# Create the files with the corresponding code strings
for filename, content in file_data.items():
    with open(filename, "w") as file:
        file.write(content)

print("Files have been created.")
