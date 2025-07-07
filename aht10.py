import time
from smbus2 import SMBus

class AHT10:
    """
    AHT10 Temperature and Humidity Sensor Class.

    Attributes:
        i2c_bus_num (int): The I2C bus number (e.g., 1 for Raspberry Pi).
        i2c_address (int): The I2C address of the AHT10 sensor (default: 0x38).
        _bus (smbus2.SMBus): The SMBus object for I2C communication.
    """

    AHT10_ADDRESS = 0x38
    AHT10_CMD_INITIALIZE = [0xBE, 0x08, 0x00]
    AHT10_CMD_MEASURE = [0xAC, 0x33, 0x00]
    AHT10_STATUS_REG = 0x71 # Register to read status byte

    def __init__(self, i2c_bus_num=1, i2c_address=AHT10_ADDRESS):
        """
        Initializes the AHT10 sensor object.

        Args:
            i2c_bus_num (int): The I2C bus number.
            i2c_address (int): The I2C address of the AHT10.
        """
        self.i2c_bus_num = i2c_bus_num
        self.i2c_address = i2c_address
        self._bus = None

        self.open_bus()

        self.initialize_sensor()

    def __enter__(self):
        """Context manager entry point."""
        self.open_bus()
        if self._bus and not self.initialize_sensor():
            raise IOError("Failed to initialize AHT10 sensor.")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit point."""
        self.close_bus()

    def open_bus(self):
        """Opens the I2C bus connection."""
        try:
            self._bus = SMBus(self.i2c_bus_num)
            print(f"I2C bus {self.i2c_bus_num} opened.")
        except FileNotFoundError:
            raise FileNotFoundError(
                "I2C bus not found. Make sure I2C is enabled and you have "
                "the correct permissions (e.g., add user to i2c group)."
            )
        except Exception as e:
            raise IOError(f"Error opening I2C bus: {e}")

    def close_bus(self):
        """Closes the I2C bus connection."""
        if self._bus:
            self._bus.close()
            self._bus = None
            print(f"I2C bus {self.i2c_bus_num} closed.")

    def _read_status(self):
        """Reads the AHT10 status byte."""
        if not self._bus:
            raise RuntimeError("I2C bus not open. Call open_bus() first.")
        try:
            return self._bus.read_byte_data(self.i2c_address, self.AHT10_STATUS_REG)
        except Exception as e:
            raise IOError(f"Error reading AHT10 status: {e}")

    def is_calibrated(self):
        """Checks if the AHT10 sensor is calibrated."""
        status = self._read_status()
        return (status & 0x08) != 0

    def is_busy(self):
        """Checks if the AHT10 sensor is busy with a measurement."""
        status = self._read_status()
        return (status & 0x80) != 0

    def initialize_sensor(self):
        """Initializes the AHT10 sensor."""
        if not self._bus:
            raise RuntimeError("I2C bus not open. Call open_bus() first.")
        
        # Check if already calibrated
        if self.is_calibrated():
            print("AHT10 already calibrated.")
            return True

        print("AHT10 not calibrated. Initializing...")
        try:
            self._bus.write_i2c_block_data(self.i2c_address, self.AHT10_CMD_INITIALIZE[0], self.AHT10_CMD_INITIALIZE[1:])
            time.sleep(0.01) # Small delay after initialization command
            
            # Verify calibration
            if not self.is_calibrated():
                print("Failed to initialize AHT10. Calibration bit not set.")
                return False
            print("AHT10 initialized successfully.")
            return True
        except Exception as e:
            print(f"Error during AHT10 initialization: {e}")
            return False

    def read_raw_data(self, timeout=0.5):
        """
        Triggers a measurement and reads raw 6 bytes of data from AHT10.

        Args:
            timeout (float): Maximum time in seconds to wait for measurement.

        Returns:
            list: A list of 6 raw bytes if successful, None otherwise.
        """
        if not self._bus:
            raise RuntimeError("I2C bus not open. Call open_bus() first.")

        try:
            # Trigger measurement
            self._bus.write_i2c_block_data(self.i2c_address, self.AHT10_CMD_MEASURE[0], self.AHT10_CMD_MEASURE[1:])

            # Wait for measurement to complete
            start_time = time.time()
            while self.is_busy():
                if time.time() - start_time > timeout:
                    raise TimeoutError(f"AHT10 measurement timeout after {timeout} seconds.")
                time.sleep(0.01) # Wait 10ms before checking again

            # Read 6 bytes of data
            # Note: AHT10 does not use registers for data read, just reads from device address
            # The 0x00 is a dummy register for this sensor with smbus2's read_i2c_block_data
            data = self._bus.read_i2c_block_data(self.i2c_address, 0x00, 6)
            return data
        except Exception as e:
            print(f"Error reading raw AHT10 data: {e}")
            return None

    def get_humidity_temperature(self):
        """
        Reads sensor data and converts it to humidity and temperature.

        Returns:
            tuple: (humidity, temperature) in %RH and °C.
                   Returns (None, None) if data reading or conversion fails.
        """
        raw_data = self.read_raw_data()
        if raw_data is None or len(raw_data) != 6:
            return None, None

        # raw_data[0] is the status byte (bit 7 is busy, bit 3 is calibrated)
        # raw_data[1], raw_data[2], raw_data[3] (upper 4 bits) are humidity
        # raw_data[3] (lower 4 bits), raw_data[4], raw_data[5] are temperature

        # Combine bytes to get raw humidity (20-bit value)
        raw_humidity = ((raw_data[1] << 16) | (raw_data[2] << 8) | raw_data[3]) >> 4
        humidity = (raw_humidity / 1048576.0) * 100.0 # 2^20 = 1048576

        # Combine bytes to get raw temperature (20-bit value)
        raw_temperature = (((raw_data[3] & 0x0F) << 16) | (raw_data[4] << 8) | raw_data[5])
        temperature = (raw_temperature / 1048576.0) * 200.0 - 50.0 # 2^20 = 1048576

        return humidity, temperature

