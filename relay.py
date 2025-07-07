import RPi.GPIO as GPIO 

class Relay:
    """
    A class to control a relay connected to a Raspberry Pi GPIO pin.
    """
    def __init__(self, gpio_pin=14, initial_state="off", active_high=True):
        self.gpio_pin = gpio_pin
        self.active_high = active_high # True if HIGH turns ON, False if LOW turns ON
        self._current_state = None

        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.gpio_pin, GPIO.OUT)

        if initial_state.lower() == "off":
            self.off()
        elif initial_state.lower() == "on":
            self.on()
        else:
            GPIO.cleanup(self.gpio_pin)
            raise ValueError("initial_state must be 'on' or 'off'")

        print(f"Relay initialized on GPIO BCM {self.gpio_pin} (Physical Pin {self._get_physical_pin(self.gpio_pin)}) to {self.get_state().upper()}.")

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.cleanup()
        print(f"Relay on GPIO BCM {self.gpio_pin} cleaned up.")

    def on(self):
        """Turns the relay ON."""
        output_state = GPIO.HIGH if self.active_high else GPIO.LOW
        if self._current_state != "on":
            GPIO.output(self.gpio_pin, output_state)
            self._current_state = "on"
            # print(f"Relay on GPIO {self.gpio_pin} turned ON.")

    def off(self):
        """Turns the relay OFF."""
        output_state = GPIO.LOW if self.active_high else GPIO.HIGH
        if self._current_state != "off":
            GPIO.output(self.gpio_pin, output_state)
            self._current_state = "off"
            # print(f"Relay on GPIO {self.gpio_pin} turned OFF.")

    def toggle(self):
        """Toggles the current state of the relay."""
        if self._current_state == "on":
            self.off()
        else:
            self.on()

    def get_state(self):
        """Gets the current logical state of the relay ('on' or 'off')."""
        return self._current_state

    def cleanup(self):
        """Cleans up the GPIO pin, ensuring the relay is off."""
        self.off() # Ensure relay is off before cleanup
        GPIO.cleanup(self.gpio_pin)
        self._current_state = None

    def _get_physical_pin(self, bcm_pin):
        bcm_to_physical = {
            2: 3, 3: 5, 4: 7, 14: 8, 15: 10, 17: 11, 18: 12, 27: 13, 22: 15,
            23: 16, 24: 18, 10: 19, 9: 21, 25: 22, 11: 23, 8: 24, 7: 26, 5: 29,
            6: 31, 12: 32, 13: 33, 19: 35, 16: 36, 20: 38, 21: 40
        }
        return bcm_to_physical.get(bcm_pin, "N/A (check pinout)")
