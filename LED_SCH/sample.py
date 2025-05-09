import _thread
import time
from machine import Pin
import machine
from neopixel import NeoPixel
import json
import gc

# Constants
BUZZER_PIN = 32
RELAY_PIN = 33
RELAY_WAIT_TIME = 120  # 2 minutes in seconds for relay timeout


# Simulated clock for testing
class SimulatedClock:
    def __init__(self):
        self.hour = 0
        self.minute = 0
        self.last_update = time.time()

    def get_formatted_time(self):
        # Update time based on real time elapsed
        now = time.time()
        elapsed_seconds = int(now - self.last_update)
        if elapsed_seconds >= 60:
            self.minute += elapsed_seconds // 60
            self.last_update = now
            if self.minute >= 60:
                self.hour += self.minute // 60
                self.minute = self.minute % 60
                if self.hour >= 24:
                    self.hour = 0
        return f"{self.hour:02d}:{self.minute:02d}"

    def set_time(self, hour, minute):
        self.hour = hour
        self.minute = minute
        self.last_update = time.time()
        print(f"Time set to: {self.hour:02d}:{self.minute:02d}")


class BinManager:
    def __init__(self):
        self.waiting_time = RELAY_WAIT_TIME
        self.time_queue = {
            0: {"time": 0, "wait_state": False},
            1: {"time": 0, "wait_state": False},
            2: {"time": 0, "wait_state": False},
            3: {"time": 0, "wait_state": False},
        }

        self.led_state = [False] * 4
        # Initialize buzzer and relay
        self.buzzer = machine.Pin(BUZZER_PIN, machine.Pin.OUT)
        self.relay = machine.Pin(RELAY_PIN, machine.Pin.OUT)
        self.turn_off_buzzer()
        self.turn_off_relay()

    def turn_on_buzzer(self):
        self.buzzer.on()
        print("Buzzer: ON")

    def turn_off_buzzer(self):
        self.buzzer.off()
        print("Buzzer: OFF")

    def turn_on_relay(self):
        self.relay.on()
        print("Relay: ON")

    def turn_off_relay(self):
        self.relay.off()
        print("Relay: OFF")

    def check_buzzer_state(self, index):
        # Buzzer turns on if any bin LED is on
        any_on = False
        for i in self.led_state:
            if i:
                any_on = True
                break

        if any_on:
            self.turn_on_buzzer()
        else:
            self.turn_off_buzzer()

    def change_buzzer_state(self, index, state):
        self.led_state[index] = state
        if state:
            self.turn_on_buzzer()
        else:
            self.turn_off_buzzer()

    def check_relay_state(self):
        # Relay turns on if any bin has wait_state=True and time > 0
        isON = False
        for index in range(4):
            wait_state = self.time_queue[index]["wait_state"]
            curr_time = self.time_queue[index]["time"]

            if wait_state == True:
                if curr_time == 0:
                    isON = True
                else:
                    curr_time -= 1
            self.time_queue[index]["time"] = curr_time

        if isON:
            self.turn_on_relay()
        else:
            self.turn_off_relay()

    def change_state(self, index, state):
        self.time_queue[index]["time"] = 0 if state == "OFF" else self.waiting_time
        self.time_queue[index]["wait_state"] = False if state == "OFF" else True


def check_queue(bin):
    try:
        with open("bin_queue.json", "r") as f:
            queue = json.load(f)
    except:
        queue = {str(i): [] for i in range(4)}

    if queue[str(bin.index)]:
        next_color = queue[str(bin.index)].pop(0)
        bin.change_led_color(next_color)

        print(f"Bin {bin.index} activated with color {next_color}")

        with open("bin_queue.json", "w") as f:
            json.dump(queue, f)


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

    def change_led_color(self, color=None):
        if color:
            self.color = tuple(color)
        for i in range(self.num_leds):
            self.np[i] = self.color
        self.np.write()
        self.clicked = False
        self.save_state()
        self.bin_manager.change_buzzer_state(self.index, True)
        self.bin_manager.check_buzzer_state(self.index)
        self.bin_manager.change_state(self.index, "ON")
        print(f"Bin {self.index} ON with color {self.color}")

    def turn_off_leds(self):
        for i in range(self.num_leds):
            self.np[i] = (0, 0, 0)
        self.np.write()
        self.clicked = True
        self.save_state()
        print(f"Bin {self.index} OFF")
        check_queue(self)
        self.bin_manager.change_buzzer_state(self.index, False)
        self.bin_manager.check_buzzer_state(self.index)
        self.bin_manager.change_state(self.index, "OFF")

    def handle_button_press(self, pin):
        current_time = time.ticks_ms()
        if time.ticks_diff(current_time, self.last_pressed_time) > 400:
            self.last_pressed_time = current_time
            # Only turn off if LEDs are on (don't toggle)
            if not self.clicked:
                self.turn_off_leds()

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
            "color": [255, 0, 0],
            "led_pin": 12,
            "button_pin": 13,
            "schedules": [],
            "enabled": True,
            "clicked": True,  # Default to OFF state
        },
        {
            "color": [0, 255, 0],
            "led_pin": 25,
            "button_pin": 14,
            "schedules": [],
            "enabled": True,
            "clicked": True,
        },
        {
            "color": [0, 0, 255],
            "led_pin": 26,
            "button_pin": 15,
            "schedules": [],
            "enabled": True,
            "clicked": True,
        },
        {
            "color": [255, 255, 0],
            "led_pin": 27,
            "button_pin": 16,
            "schedules": [],
            "enabled": True,
            "clicked": True,
        },
    ]


def load_config():
    try:
        with open("data.json", "r") as f:
            return json.load(f)
    except:
        return load_default_config()


def check_schedules(bins, clock):
    while True:
        try:
            current_time = clock.get_formatted_time()
            print(f"\nChecking schedules at {current_time}")

            # Parse current time
            current_hour, current_minute = map(int, current_time.split(":"))

            try:
                with open("bin_queue.json", "r") as f:
                    queue = json.load(f)
            except:
                queue = {str(i): [] for i in range(4)}

            schedule_triggered = False

            for bin in bins:
                for schedule in bin.schedules:
                    if schedule["enabled"]:
                        schedule_hour, schedule_minute = map(
                            int, schedule["time"].split(":")
                        )
                        if (
                            current_hour == schedule_hour
                            and current_minute == schedule_minute
                        ):
                            schedule_triggered = True
                            print(f"Bin {bin.index} schedule triggered")
                            if bin.clicked:
                                # Bin is available, activate immediately
                                bin.change_led_color(schedule["color"])
                            else:
                                # Bin is busy, add to queue
                                queue[str(bin.index)].append(schedule["color"])
                                print(f"Added to bin {bin.index} queue")

            if schedule_triggered:
                with open("bin_queue.json", "w") as f:
                    json.dump(queue, f)

            if not schedule_triggered:
                print("No schedules at this time")

            time.sleep(60)
        except Exception as e:
            print(f"Schedule error: {e}")
            time.sleep(10)

    # Load configuration


data = load_config()
print("Initial configuration loaded")

# Initialize bin manager
bin_manager = BinManager()

# Create bin objects
bins = [
    Bin(bin_config, index, bin_manager)
    for index, bin_config in enumerate(data)
    if bin_config["enabled"]
]
print(f"Initialized {len(bins)} bins")


def main():

    for i in bins:
        check_queue(i)
    # Initialize queue file
    try:
        with open("bin_queue.json", "r") as f:
            pass
    except:
        with open("bin_queue.json", "w") as f:
            json.dump({str(i): [] for i in range(4)}, f)

    # Set initial time for testing (e.g., 10:00 AM)
    clock = SimulatedClock()
    clock.set_time(10, 0)

    # Start schedule checking thread
    _thread.start_new_thread(check_schedules, (bins, clock))

    # Main loop
    print("Starting main loop")
    while True:
        bin_manager.check_relay_state()
        print(bin_manager.time_queue)
        time.sleep(1)


if __name__ == "__main__":
    main()
