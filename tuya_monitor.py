import tinytuya
import time

DEVICE_ID = "bf52f933daca3ce0dbzsc7"
LOCAL_KEY = "DYePUg]Plk2{S?q`"
IP_ADDRESS = "192.168.0.126"

plug = tinytuya.OutletDevice(DEVICE_ID, IP_ADDRESS, LOCAL_KEY)
plug.set_version(3.5)

# Turn ON
plug.set_status(True)

while True:
    data = plug.status()
    if "dps" in data:
        dps = data["dps"]
        on_off = dps.get("1")
        energy_today = dps.get("17", 0) / 100.0  # if it's in Wh
        voltage = dps.get("18", 0) / 10
        current = dps.get("19", 0) / 1000
        power = dps.get("20", 0) / 10
        energy_total = dps.get("23", 0) / 100.0  # if it's in Wh

        print(f"Status: {'ON' if on_off else 'OFF'} | V: {voltage}V | A: {current}A | W: {power}W | Energy Today: {energy_today}Wh | Total: {energy_total}Wh")
    else:
        print("Failed to get data:", data)

    time.sleep(60)
