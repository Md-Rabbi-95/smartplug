from django.db import models

class PowerLog(models.Model):
    timestamp = models.DateTimeField(auto_now_add=True)
    status = models.BooleanField()
    voltage = models.FloatField()
    current = models.FloatField()
    power = models.FloatField()
    energy_today = models.FloatField(default=0)
    energy_total = models.FloatField(default=0)