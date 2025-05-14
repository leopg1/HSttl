# Event message for maze navigation robot

# Event type
string event_type    # EXIT_DETECTED, ALCOHOL_DETECTED, VIBRATION_DETECTED

# Position where event was detected
float32 x
float32 y

# Timestamp
time timestamp

# Additional data (optional)
float32 value        # Sensor reading value
string details       # Additional information
