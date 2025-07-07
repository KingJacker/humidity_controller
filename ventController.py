from aht10 import AHT10
from relay import Relay
from dew_point_calc import calculate_dew_point
import time


class VentController:
    """
    Controls a bathroom vent fan based on AHT10 sensor readings and dew point.
    """

    def __init__(self,
                 aht10_bus_num=1,
                 relay_gpio_pin=14,
                 relay_active_high=True, # Set to False if your relay is active-low
                 dew_point_threshold_c=16.0, # e.g., 16C
                 hysteresis_c=2.0,           # Fan stays on until DP drops by this much
                 min_fan_runtime_seconds=300, # 5 minutes
                 max_fan_runtime_seconds=3600, # 1 hour
                 sensor_read_interval_seconds=10):
        """
        Initializes the VentController.

        Args:
            aht10_bus_num (int): I2C bus number for AHT10.
            relay_gpio_pin (int): BCM GPIO pin for the relay.
            relay_active_high (bool): True if relay turns ON with HIGH signal, False for LOW.
            dew_point_threshold_c (float): Dew point in Celsius to turn fan ON.
            hysteresis_c (float): Hysteresis value in Celsius for turning fan OFF.
            min_fan_runtime_seconds (int): Minimum time fan must run once activated.
            max_fan_runtime_seconds (int): Maximum time fan can run.
            sensor_read_interval_seconds (int): How often to read sensor and evaluate.
        """
        self.aht10_bus_num = aht10_bus_num
        self.relay_gpio_pin = relay_gpio_pin
        self.relay_active_high = relay_active_high

        self.dew_point_threshold_c = dew_point_threshold_c
        self.hysteresis_c = hysteresis_c
        self.min_fan_runtime_seconds = min_fan_runtime_seconds
        self.max_fan_runtime_seconds = max_fan_runtime_seconds
        self.sensor_read_interval_seconds = sensor_read_interval_seconds

        self.sensor = None  # AHT10 instance
        self.relay = None   # Relay instance

        self.fan_on_timestamp = 0  # To track fan run time
        self._running = False      # Control loop state

        print("VentController initialized. Ready to start.")

    def __enter__(self):
        """Context manager entry point: opens sensor and relay connections."""
        try:
            self.sensor = AHT10(self.aht10_bus_num)
            self.sensor.__enter__() # Manually call __enter__ for contained objects

            self.relay = Relay(self.relay_gpio_pin, initial_state="off", active_high=self.relay_active_high)
            self.relay.__enter__() # Manually call __enter__ for contained objects

            # Ensure fan is off at startup
            self.relay.off()
            print("Controller: Sensors and Relay initialized. Fan is OFF.")
            return self
        except Exception as e:
            print(f"Controller initialization failed: {e}")
            self.__exit__(None, None, None) # Ensure cleanup if init fails
            raise

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit point: cleans up sensor and relay connections."""
        print("Controller: Cleaning up resources...")
        self.stop() # Ensure main loop is stopped

        if self.relay:
            self.relay.__exit__(exc_type, exc_val, exc_tb)
            self.relay = None
        if self.sensor:
            self.sensor.__exit__(exc_type, exc_val, exc_tb)
            self.sensor = None
        
        # This is very important if RPi.GPIO was set up
        # If no other GPIO is in use by another class/module,
        # it's good practice to call global cleanup if needed.
        # But since Relay class's __exit__ does cleanup for its pin,
        # and __main__ block ensures context manager for Controller,
        # global cleanup might not be strictly necessary here if only one Relay object exists.
        # However, calling it generally ensures all pins are reset.
        try:
            GPIO.cleanup()
            print("Controller: RPi.GPIO global cleanup performed.")
        except Exception as e:
            print(f"Controller: Error during global GPIO cleanup: {e}")


    def _evaluate_fan_state(self, temp, rh, current_dp):
        """Internal method to determine if the fan should be on/off based on logic."""
        
        # Check if sensor data is valid
        if temp is None or rh is None or current_dp is None:
            print("Controller: Invalid sensor data, maintaining current fan state.")
            return

        fan_is_on = self.relay.get_state() == "on"
        current_time = time.time()

        # If fan is currently OFF
        if not fan_is_on:
            if current_dp > self.dew_point_threshold_c:
                self.relay.on()
                self.fan_on_timestamp = current_time
                print(f"Controller: Dew Point ({current_dp:.2f}°C) > Threshold ({self.dew_point_threshold_c:.1f}°C). Turning fan ON.")
            else:
                # print(f"Controller: DP ({current_dp:.2f}°C) below threshold. Fan remains OFF.")
                pass

        # If fan is currently ON
        else:
            # Check Minimum Run Time
            if (current_time - self.fan_on_timestamp) < self.min_fan_runtime_seconds:
                # print(f"Controller: Fan ON (Min runtime: {int(self.min_fan_runtime_seconds - (current_time - self.fan_on_timestamp))}s left). DP: {current_dp:.2f}°C")
                pass # Do nothing, let it run for min time

            # Check Maximum Run Time
            elif (current_time - self.fan_on_timestamp) > self.max_fan_runtime_seconds:
                self.relay.off()
                self.fan_on_timestamp = 0 # Reset
                print(f"Controller: Max fan runtime ({self.max_fan_runtime_seconds}s) reached. Turning fan OFF (DP: {current_dp:.2f}°C).")

            # Check Dew Point for Turning OFF (with Hysteresis)
            elif current_dp < (self.dew_point_threshold_c - self.hysteresis_c):
                self.relay.off()
                self.fan_on_timestamp = 0 # Reset
                print(f"Controller: Dew Point ({current_dp:.2f}°C) < (Threshold - Hysteresis) ({self.dew_point_threshold_c - self.hysteresis_c:.1f}°C). Turning fan OFF.")
            
            else:
                # Fan is ON, within min/max runtime, and DP is between threshold and hysteresis
                # print(f"Controller: Fan ON. DP ({current_dp:.2f}°C) within hysteresis range.")
                pass


    def start(self):
        """Starts the main control loop."""
        if not (self.sensor and self.relay):
            raise RuntimeError("Controller not properly initialized. Use 'with VentController(...)'")

        self._running = True
        print("Controller: Starting main loop. Press Ctrl+C to stop.")
        try:
            while self._running:
                humidity, temperature = self.sensor.get_humidity_temperature()
                current_dew_point = calculate_dew_point(temperature, humidity)
                
                print(f"Sensor: T={temperature:.2f}°C, RH={humidity:.2f}%, DP={current_dew_point:.2f}°C. Fan: {self.relay.get_state().upper()}")
                
                self._evaluate_fan_state(temperature, humidity, current_dew_point)
                time.sleep(self.sensor_read_interval_seconds)
        except KeyboardInterrupt:
            print("\nController: Ctrl+C detected. Stopping loop.")
        except Exception as e:
            print(f"Controller: An error occurred in the main loop: {e}")
        finally:
            self.stop() # Ensure cleanup when loop exits

    def stop(self):
        """Stops the main control loop and ensures fan is off."""
        self._running = False
        if self.relay:
            self.relay.off()
            # print("Controller: Fan ensured OFF on stop.")
