from django.core.management.base import BaseCommand
from dashboard.models import PowerLog
import tinytuya, time

DEVICE_ID = "bf52f933daca3ce0dbzsc7"
LOCAL_KEY = "DYePUg]Plk2{S?q`"
IP_ADDRESS = "192.168.0.125"

class Command(BaseCommand):
    help = "Logs power data every second"

    def handle(self, *args, **kwargs):
        plug = tinytuya.OutletDevice(DEVICE_ID, IP_ADDRESS, LOCAL_KEY)
        plug.set_version(3.5)
        while True:
            data = plug.status().get("dps", {})
            PowerLog.objects.create(
                status=data.get("1", False),
                voltage=data.get("20", 0) / 10,
                current=data.get("18", 0) / 1000,
                power=data.get("19", 0) / 10,
                energy_today=data.get("17", 0) / 1000,
               
            )
            time.sleep(1)