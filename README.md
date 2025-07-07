# Humidity Controller

This project is about creating a controller to toggle a fan to avoid mould in a bathroom with shower.

## Setup
```bash
# Setup Python environment
python -m venv venv
python -m venv/bin/activate
pip install -r requirements.txt

# Start Controller
python main.py
```

## Configure
Configure the setup in [main.py](main.py).
```python
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
```

## Hardware
My setup is running on a Raspberry Pi 4.

### Sensor
The sensor used is an AHT10.
### Relay
A generic 5 Volt Relay was used.\
Default pin for relay switch is GPIO 14.