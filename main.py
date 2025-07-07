from ventController import VentController

def main():
    # --- CONFIGURATION ---
    # Adjust these parameters for your setup and preferences
    AHT10_I2C_BUS = 1            # Typically 1 for Raspberry Pi
    RELAY_GPIO_PIN = 14          # BCM GPIO pin number (Physical Pin 8)
    RELAY_ACTIVE_HIGH = True     # Set to False if your relay is ACTIVE-LOW (most common)

    # Dew Point Control Parameters
    DEW_POINT_THRESHOLD = 19.0   # Degrees Celsius
    HYSTERESIS = 2.0             # Degrees Celsius (fan turns OFF when DP drops below threshold - hysteresis)

    # Fan Runtime Management
    MIN_FAN_RUN_TIME = 5 * 60    # 5 minutes in seconds
    MAX_FAN_RUN_TIME = 60 * 60   # 1 hour in seconds

    SENSOR_READ_INTERVAL = 10    # Read sensor and evaluate every 10 seconds
    # --- END CONFIGURATION ---

    print("Starting Bathroom Vent Controller application...")
    print("---------------------------------------------")
    print(f"Config: DP Threshold: {DEW_POINT_THRESHOLD}°C, Hysteresis: {HYSTERESIS}°C")
    print(f"Config: Min Run Time: {MIN_FAN_RUN_TIME/60}min, Max Run Time: {MAX_FAN_RUN_TIME/60}min")
    print(f"Config: Sensor Read Interval: {SENSOR_READ_INTERVAL}s")
    print("---------------------------------------------")

    controller = None
    try:
        with VentController(
            aht10_bus_num=AHT10_I2C_BUS,
            relay_gpio_pin=RELAY_GPIO_PIN,
            relay_active_high=RELAY_ACTIVE_HIGH,
            dew_point_threshold_c=DEW_POINT_THRESHOLD,
            hysteresis_c=HYSTERESIS,
            min_fan_runtime_seconds=MIN_FAN_RUN_TIME,
            max_fan_runtime_seconds=MAX_FAN_RUN_TIME,
            sensor_read_interval_seconds=SENSOR_READ_INTERVAL
        ) as controller:
            controller.start() # This will run until Ctrl+C

    except FileNotFoundError as e:
        print(f"\nCRITICAL ERROR: {e}")
        print("Ensure I2C is enabled (`sudo raspi-config`) and your user has permissions (`sudo adduser $USER i2c` then reboot).")
    except ImportError as e:
        print(f"\nCRITICAL ERROR: Missing library. {e}")
        print("Please ensure 'smbus2' and 'RPi.GPIO' are installed (`pip install smbus2 RPi.GPIO`).")
    except RuntimeError as e:
        print(f"\nCRITICAL ERROR: Controller setup issue: {e}")
    except Exception as e:
        print(f"\nAN UNEXPECTED ERROR OCCURRED: {e}")
        import traceback
        traceback.print_exc() # Print full traceback for unexpected errors
    finally:
        print("\nApplication exiting.")
        # The 'with' statement handles controller.__exit__ for cleanup automatically

if __name__ == "__main__":
    main()
