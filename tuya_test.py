import tinytuya
import time

# Device Info
DEVICE_ID = "bf52f933daca3ce0dbzsc7"
LOCAL_KEY = "DYePUg]Plk2{S?q`"
IP_ADDRESS = "192.168.0.125"   # Replace with your plug's IP

# Create device object
plug = tinytuya.OutletDevice(DEVICE_ID, IP_ADDRESS, LOCAL_KEY)
plug.set_version(3.5)  # Most Tuya devices use 3.3

# Test ON
print("Turning ON plug...")
plug.set_status(True)  # True = ON

time.sleep(2)

# Test OFF
print("Turning OFF plug...")
plug.set_status(False)

# time.sleep(2)

# Get Status (including energy data)
print("Getting status...")
data = plug.status()
print(data)
