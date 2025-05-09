import _thread
import time
from ds3231 import DS3231
from machine import Pin
import machine
from neopixel import NeoPixel
import json
import gc

# Initialize RTC
rtc = DS3231()

# Constants
BUZZER_PIN = 32
RELAY_PIN = 33
BUZZER_WAIT_TIME = 600  # 10 minutes in seconds


class BinManager:
    def __init__(self):
        self.waiting_time = BUZZER_WAIT_TIME
        self.time_queue = {
            0: {"time": 0, "wait_state": False},
            1: {"time": 0, "wait_state": False},
            2: {"time": 0, "wait_state": False},
            3: {"time": 0, "wait_state": False},
        }

        # Initialize buzzer and relay
        self.buzzer = machine.Pin(BUZZER_PIN, machine.Pin.OUT)
        self.relay = machine.Pin(RELAY_PIN, machine.Pin.OUT)
        self.turn_off_buzzer()
        self.turn_off_relay()

    def turn_on_buzzer(self):
        self.buzzer.on()

    def turn_off_buzzer(self):
        self.buzzer.off()

    def turn_on_relay(self):
        self.relay.on()

    def turn_off_relay(self):
        self.relay.off()

    def check_state(self):
        any_on = False
        for index in range(4):
            wait_state = self.time_queue[index]["wait_state"]
            curr_time = self.time_queue[index]["time"]

            if wait_state:
                if curr_time == 0:
                    any_on = True
                else:
                    curr_time -= 1
                self.time_queue[index]["time"] = curr_time

        # Control buzzer based on any LED state
        if any_on:
            self.turn_on_buzzer()
        else:
            self.turn_off_buzzer()

        return any_on

    def change_state(self, index, state):
        self.time_queue[index]["time"] = 0 if state == "OFF" else self.waiting_time
        self.time_queue[index]["wait_state"] = False if state == "OFF" else True


class Bin:
    def __init__(self, bin_config, index, bin_manager):
        self.button_pin = bin_config["button_pin"]
        self.led_pin = bin_config["led_pin"]
        self.color = tuple(bin_config["color"])
        self.last_pressed_time = 0
        self.clicked = bin_config["clicked"]
        self.index = index
        self.schedules = bin_config.get("schedules", [])
        self.bin_manager = bin_manager
        self.num_leds = 10

        # Initialize hardware
        self.button = machine.Pin(self.button_pin, machine.Pin.IN, machine.Pin.PULL_UP)
        self.np = NeoPixel(machine.Pin(self.led_pin), self.num_leds)
        self.button.irq(
            trigger=machine.Pin.IRQ_FALLING, handler=self.handle_button_press
        )

        # Initialize LED state
        if self.clicked:
            self.turn_off_leds()
        else:
            self.change_led_color()

    def change_led_color(self):
        for i in range(self.num_leds):
            self.np[i] = self.color
        self.np.write()
        self.bin_manager.change_state(self.index, "ON")
        self.save_state()

    def turn_off_leds(self):
        for i in range(self.num_leds):
            self.np[i] = (0, 0, 0)
        self.np.write()
        self.bin_manager.change_state(self.index, "OFF")
        self.save_state()

        # Check queue for next color
        self.check_queue()

    def handle_button_press(self, pin):
        current_time = time.ticks_ms()
        if time.ticks_diff(current_time, self.last_pressed_time) > 400:
            self.last_pressed_time = current_time

            # Toggle the clicked state
            self.clicked = not self.clicked

            if self.clicked:
                self.turn_off_leds()
            else:
                self.change_led_color()

    def check_queue(self):
        try:
            with open("bin_queue.json", "r") as f:
                queue = json.load(f)
        except:
            queue = {str(i): [] for i in range(4)}

        if queue[str(self.index)]:
            next_color = queue[str(self.index)].pop(0)
            self.color = tuple(next_color)
            self.clicked = False
            self.change_led_color()

            with open("bin_queue.json", "w") as f:
                json.dump(queue, f)

    def save_state(self):
        try:
            with open("data.json", "r") as f:
                config = json.load(f)
        except:
            config = load_default_config()

        config[self.index]["clicked"] = self.clicked
        config[self.index]["color"] = list(self.color)

        with open("data.json", "w") as f:
            json.dump(config, f)


def load_default_config():
    return [
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


def load_config():
    try:
        with open("data.json", "r") as f:
            return json.load(f)
    except:
        return load_default_config()


def check_schedules(bins, rtc):
    while True:
        try:
            current_time = rtc.get_formatted_time()  # Expected format: "HH:MM"
            current_hour, current_minute = map(int, current_time.split(":"))

            try:
                with open("bin_queue.json", "r") as f:
                    queue = json.load(f)
            except:
                queue = {str(i): [] for i in range(4)}

            for bin in bins:
                for schedule in bin.schedules:
                    if schedule["enabled"]:
                        schedule_time = schedule["time"]
                        schedule_hour, schedule_minute = map(
                            int, schedule_time.split(":")
                        )

                        if (
                            current_hour == schedule_hour
                            and current_minute == schedule_minute
                        ):
                            if bin.clicked:
                                # Bin is off, add to queue
                                queue[str(bin.index)].append(schedule["color"])
                            else:
                                # Bin is on, change color immediately
                                bin.color = tuple(schedule["color"])
                                bin.change_led_color()

            with open("bin_queue.json", "w") as f:
                json.dump(queue, f)

            gc.collect()
            time.sleep(60)  # Check every minute
        except Exception as e:
            print(f"Error in schedule check: {e}")
            time.sleep(10)


def main():
    # Load configuration
    data = load_config()

    # Initialize bin manager
    bin_manager = BinManager()

    # Create bin objects
    bins = [
        Bin(bin_config, index, bin_manager)
        for index, bin_config in enumerate(data)
        if bin_config["enabled"]
    ]

    # Initialize queue file if not exists
    try:
        with open("bin_queue.json", "r") as f:
            pass
    except:
        with open("bin_queue.json", "w") as f:
            json.dump({str(i): [] for i in range(4)}, f)

    # Start schedule checking thread
    _thread.start_new_thread(check_schedules, (bins, rtc))

    # Main loop
    while True:
        # Check if any bins need to be turned off based on time queue
        if bin_manager.check_state():
            for i, bin in enumerate(bins):
                if (
                    bin_manager.time_queue[i]["time"] == 0
                    and bin_manager.time_queue[i]["wait_state"]
                ):
                    bin.turn_off_leds()
                    bin_manager.change_state(i, "OFF")

        time.sleep(1)


if __name__ == "__main__":
    main()
