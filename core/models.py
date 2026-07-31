from django.db import models

class SystemConfig(models.Model):
    """
    Stores system-wide parameters for priority triage scoring and record linkage.
    Only one instance of this model should normally exist.
    """
    severity_wt = models.IntegerField(default=3)
    corroboration_wt = models.IntegerField(default=2)
    trust_wt = models.IntegerField(default=2)
    vulnerability_wt = models.IntegerField(default=1)
    time_wt = models.IntegerField(default=1)
    
    distance_threshold_km = models.FloatField(default=15.0)
    time_threshold_hours = models.FloatField(default=24.0)

    def __str__(self):
        return "System Configuration"

    @classmethod
    def get_config(cls):
        config, created = cls.objects.get_or_create(id=1)
        return config


class Incident(models.Model):
    """
    Represents a consolidated disaster incident fused from multiple raw signals.
    """
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('dispatched', 'Dispatched'),
        ('rescuers_arrived', 'Rescuers Arrived'),
        ('resolved', 'Resolved'),
        ('dismissed', 'Dismissed'),
    ]

    disaster_type = models.CharField(max_length=50, default='General')
    location_name = models.CharField(max_length=255, default='Reported Emergency Site')
    district_id = models.CharField(max_length=100, default='central')
    lat = models.FloatField(default=27.7)  # Central Nepal default
    lng = models.FloatField(default=85.3)
    
    first_reported = models.DateTimeField()
    last_reported = models.DateTimeField()
    severity = models.IntegerField(default=3)
    is_life_threat = models.BooleanField(default=False)
    vulnerability = models.IntegerField(default=5)
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    manual_priority = models.IntegerField(null=True, blank=True)
    manually_adjusted = models.BooleanField(default=False)

    class Meta:
        ordering = ['first_reported']

    def __str__(self):
        return f"{self.disaster_type} - {self.location_name} ({self.status})"


class Signal(models.Model):
    """
    Represents a raw report received from call centers, sensors, or social media.
    """
    SOURCE_CHOICES = [
        ('call_center', 'Call Center'),
        ('sensor', 'Sensor Alert'),
        ('social_media', 'Social Media'),
    ]

    source_type = models.CharField(max_length=20, choices=SOURCE_CHOICES)
    disaster_type = models.CharField(max_length=50, default='General')
    timestamp = models.DateTimeField()
    description = models.TextField()
    
    # Geocoded or explicitly entered location details
    lat = models.FloatField(null=True, blank=True)
    lng = models.FloatField(null=True, blank=True)
    district = models.CharField(max_length=100, null=True, blank=True)
    location_name = models.CharField(max_length=255, null=True, blank=True)
    
    severity = models.IntegerField(default=3)
    is_life_threat = models.BooleanField(default=False)
    
    # Associated incident after record linkage
    incident = models.ForeignKey(
        Incident, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='signals'
    )
    
    # Store dynamic raw JSON payload from source
    raw_payload = models.JSONField(default=dict)

    def __str__(self):
        return f"{self.source_type} ({self.id}) - {self.timestamp.strftime('%H:%M:%S')}"


class AuditLog(models.Model):
    """
    Audit trail detailing dispatcher updates and system fusion actions for an incident.
    """
    incident = models.ForeignKey(
        Incident, 
        on_delete=models.CASCADE, 
        related_name='audit_logs'
    )
    timestamp = models.DateTimeField(auto_now_add=True)
    message = models.TextField()

    class Meta:
        ordering = ['timestamp']

    def __str__(self):
        return f"[{self.timestamp.strftime('%H:%M:%S')}] Incident {self.incident_id}: {self.message[:40]}"
