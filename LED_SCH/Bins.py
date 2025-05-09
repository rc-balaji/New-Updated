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

    