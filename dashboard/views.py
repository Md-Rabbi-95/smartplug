from django.shortcuts import render, redirect
from django.views.decorators.csrf import csrf_exempt
from .models import PowerLog
from django.http import JsonResponse
import tinytuya
from django.utils import timezone
from datetime import datetime
from django.db.models import Sum
from django.utils.timezone import now
from calendar import month_name
from .models import PowerLog 
from django.db.models import Avg
from django.db.models.functions import TruncHour
from django.utils import timezone
import csv
import os
from django.http import FileResponse
from django.conf import settings

# Get today's date at midnight
today_start = timezone.localtime(timezone.now()).replace(hour=0, minute=0, second=0, microsecond=0)


timestamp = timezone.localtime(timezone.now()).strftime('%Y-%m-%d %H:%M:%S')

DEVICE_ID = "bf52f933daca3ce0dbzsc7"
LOCAL_KEY = "DYePUg]Plk2{S?q`"
IP_ADDRESS = "192.168.0.125"

# PowerLog.objects.all().delete()  # This will clear the table completely

plug = tinytuya.OutletDevice(DEVICE_ID, IP_ADDRESS, LOCAL_KEY)
plug.set_version(3.5)

def dashboard_view(request):
    status_data = plug.status()
    dps = status_data.get("dps", {})
    logs = PowerLog.objects.order_by("-timestamp")[:20][::-1]
    print(logs)
    today = (PowerLog.objects
        .filter(timestamp__date=today_start)  # Only today's entries
        .annotate(hour=TruncHour('timestamp'))  # Truncate timestamp to the hour
        .values('hour')  # Group by hour
        .annotate(average_value=Avg('power'))  # Calculate average for each hour
        .order_by('hour')  # Order by hour
    )

    today_logs_qs = PowerLog.objects.filter(timestamp__date=today_start.date()).order_by('timestamp')
    today_logs = [
        {
            "timestamp": log.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
            "power": log.power
        }
        for log in today_logs_qs
    ]
    energy_today = calculate_total_consumption(today_logs)
    monthly_cost = (energy_today * 8 ) # Adjust this multiplier as needed


    context = {
        "on_off": dps.get("1"),
        "voltage": dps.get("20", 0) / 10,
        "current": dps.get("18", 0) / 1000,
        "power": dps.get("19", 0) / 10,
        "energy_today": round(energy_today, 2),
        "monthly_cost": round(monthly_cost, 2),
        "timestamps": [log.timestamp.astimezone(timezone.get_current_timezone()).strftime("%H:%M:%S") for log in logs],
        "powers": [log.power for log in logs],
        "hours": [hour for hour in range(24)],
        "powers_today": [log.get('average_value') for log in today]
    }
    return render(request, "dashboard.html", context)



@csrf_exempt
def toggle_view(request):
    if request.method == "POST":
        status_data = plug.status()
        current_state = status_data.get("dps", {}).get("1")
        # Toggle ON/OFF
        plug.set_status(not current_state)
    return redirect("dashboard")
@csrf_exempt
def turn_on_view(request):
    if request.method == "POST":
        plug.set_status(True, "1")  # Turn ON
        return JsonResponse({"status": "on"})
    return JsonResponse({"error": "Invalid request"}, status=400)

@csrf_exempt
def turn_off_view(request):
    if request.method == "POST":
        plug.set_status(False, "1")  # Turn OFF
        return JsonResponse({"status": "off"})
    return JsonResponse({"error": "Invalid request"}, status=400)

@csrf_exempt
def energy_today_api(request):
    status_data = plug.status()
    dps = status_data.get("dps", {})
    today_logs_qs = PowerLog.objects.filter(timestamp__date=today_start.date()).order_by('timestamp')
    today_logs = [
        {
            "timestamp": log.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
            "power": log.power
        }
        for log in today_logs_qs
    ]
    energy_today = calculate_total_consumption(today_logs)
    energy_today= round(energy_today, 2)
    return JsonResponse({"energy_today": energy_today})

def power_data_api(request):
    status_data = plug.status()
    dps = status_data.get("dps", {})
    logs = PowerLog.objects.order_by("-timestamp")[:20][::-1]
    
    # Get only today's logs
    today_logs_qs = PowerLog.objects.filter(timestamp__date=today_start.date()).order_by('timestamp')
    today_logs = [
        {
            "timestamp": log.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
            "power": log.power
        }
        for log in today_logs_qs
    ]
    
    # Calculate energy today from logs
    energy_today = calculate_total_consumption(today_logs)
    monthly_cost = (energy_today * 8)  # Adjust this multiplier as needed

    today = (PowerLog.objects
        .filter(timestamp__date=today_start.date())
        .annotate(hour=TruncHour('timestamp'))
        .values('hour')
        .annotate(average_value=Avg('power'))
        .order_by('hour')
    )

    powers_today = [0 for _ in range(24)]
    for log in today:
        powers_today[log.get('hour').hour] = log.get('average_value')

    data = {
        "timestamps": [log.timestamp.astimezone(timezone.get_current_timezone()).strftime("%H:%M:%S") for log in logs],
        "powers": [log.power for log in logs],
        "energy_today": round(energy_today, 2),
        "monthly_cost": round(monthly_cost, 2),
        "current": dps.get("18", 0) / 1000,
        "power": dps.get("19", 0) / 10,
        "voltage": dps.get("20", 0) / 10,
        "on_off": dps.get("1", False),
        "hours": [hour for hour in range(24)],
        "powers_today": powers_today
    }
    
    return JsonResponse(data)



def download_csv(request):
    if not os.path.exists(CSV_FILE_PATH):
        return JsonResponse({"error": "No data available"}, status=404)
    return FileResponse(open(CSV_FILE_PATH, 'rb'), as_attachment=True, filename="power_logs.csv")


def calculate_total_consumption(logs):
    """Calculate total energy consumption in kWh from logs"""
    if not logs or len(logs) < 2:
        return 0.0
    
    total_wh = 0.0
    
    # Sort logs by timestamp to ensure chronological order
    sorted_logs = sorted(logs, key=lambda x: x['timestamp'])
    
    for i in range(1, len(sorted_logs)):
        prev_log = sorted_logs[i-1]
        current_log = sorted_logs[i]
        
        try:
            # Parse timestamps
            prev_time = datetime.strptime(prev_log['timestamp'], '%Y-%m-%d %H:%M:%S')
            current_time = datetime.strptime(current_log['timestamp'], '%Y-%m-%d %H:%M:%S')
            
            # Calculate time difference in hours
            time_diff_hours = (current_time - prev_time).total_seconds() / 3600.0
            
            # Calculate average power between the two points
            avg_power = (prev_log['power'] + current_log['power']) / 2.0
            
            # Add to total energy (in Wh)
            total_wh += avg_power * time_diff_hours
        except (KeyError, ValueError):
            continue
    
    # Convert to kWh
    return total_wh / 1000.0

CSV_FILE_PATH = os.path.join(settings.BASE_DIR, "power_logs.csv")

def log_to_csv(data):
    file_exists = os.path.isfile(CSV_FILE_PATH)
    
    with open(CSV_FILE_PATH, mode='a', newline='') as file:
        writer = csv.writer(file)
        if not file_exists:
            writer.writerow(["Timestamp", "Voltage (V)", "Current (A)", "Power (W)", "Energy Today (kWh)"])
        
        timestamp = timezone.localtime(timezone.now()).strftime("%Y-%m-%d %H:%M:%S")
        writer.writerow([
            timestamp,
            data.get("voltage", 0),
            data.get("current", 0),
            data.get("power", 0),
            data.get("energy_today", 0),
        ])