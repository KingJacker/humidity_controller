import math

def calculate_dew_point(temperature_celsius, relative_humidity):
    """
    Calculates the dew point temperature in Celsius using the Magnus formula approximation.

    Args:
        temperature_celsius (float): Ambient temperature in degrees Celsius.
        relative_humidity (float): Relative humidity in percentage (0-100%).

    Returns:
        float: Dew point temperature in degrees Celsius, or None if inputs are invalid.
    """
    if not (0 <= relative_humidity <= 100):
        print("Warning: Relative humidity must be between 0 and 100%.")
        return None
    
    if not (-50 <= temperature_celsius <= 50):
        print("Warning: Temperature outside typical range for this calculation.")

    # Constants for Magnus formula (typically valid for -30C to +35C)
    # These constants are specific to the formula's coefficients.
    A = 17.27
    B = 237.7 # degrees Celsius

    # Convert RH to a fraction (0 to 1)
    rh_fraction = relative_humidity / 100.0

    # Calculate saturation vapor pressure (es)
    # es = 6.112 * exp((A * T) / (B + T))
    es = 6.112 * math.exp((A * temperature_celsius) / (B + temperature_celsius))

    # Calculate actual vapor pressure (e)
    e = rh_fraction * es

    # Calculate dew point (Td)
    # Td = (B * ln(e / 6.112)) / (A - ln(e / 6.112))
    # It's often re-arranged to simplify the intermediate calculation:
    gamma = math.log(e / 6.112) # Use natural logarithm (ln)

    dew_point = (B * gamma) / (A - gamma)

    return dew_point
