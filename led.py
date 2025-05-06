import machine
import neopixel
import time
import network


class LEDController:
    def __init__(
        self, led_pin, button_pin, num_leds=5, led_color=(255, 255, 255), no=1
    ):
        self.led_pin = led_pin
        self.no = no
        self.button_pin = button_pin
        self.num_leds = num_leds
        self.led_color = led_color
        self.led_strip = neopixel.NeoPixel(machine.Pin(led_pin), num_leds)
        self.button = machine.Pin(button_pin, machine.Pin.IN, machine.Pin.PULL_UP)
        self.num = False
        self.last_press_time = 0  # To track the last button press time
        self.debounce_delay = 200  # Debounce delay in milliseconds

        # Initialize LED as OFF
        self.turn_off_leds()

        # Set up button interrupt
        self.button.irq(
            trigger=machine.Pin.IRQ_FALLING, handler=self.handle_button_press
        )

    def turn_on_leds(self):
        for i in range(self.num_leds):
            self.led_strip[i] = self.led_color
        self.led_strip.write()

    def turn_off_leds(self):
        for i in range(self.num_leds):
            self.led_strip[i] = (0, 0, 0)
        self.led_strip.write()

    def handle_button_press(self, pin):
        current_time = time.ticks_ms()  # Get current time in milliseconds
        if time.ticks_diff(current_time, self.last_press_time) > self.debounce_delay:
            self.last_press_time = current_time
            print(f"Button on pin {self.no} clicked!")
            self.num = not self.num
            if self.num:
                self.turn_on_leds()
            else:
                self.turn_off_leds()



led2 = LEDController(25, 14, led_color=(0, 128, 0), no=2)  # LED/Button Pair 2
led3 = LEDController(26, 15, led_color=(0, 0, 128), no=3)  # LED/Button Pair 3
led4 = LEDController(27, 16, led_color=(128, 128, 0), no=4)  # LED/Button Pair 4

led2.turn_on_leds()
led3.turn_on_leds()
led4.turn_on_leds()


while True:
    time.sleep(0.1)