import math
from datetime import datetime
from django.utils import timezone
from core.models import Incident, Signal, AuditLog, SystemConfig
from core.nlp_extractor import extract_from_text
from core.nepal_geo_data import DISTRICTS

SOURCE_TRUST = {
    'call_center': 1.0,
    'sensor': 0.9,
    'social_media': 0.4
}

def get_haversine_distance(lat1, lon1, lat2, lon2):
    """
    Computes distance in kilometers between two lat/lng coordinates.
    """
    R = 6371.0 # Earth radius
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    
    a = (math.sin(dlat / 2) ** 2 + 
         math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * (math.sin(dlon / 2) ** 2))
    
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c

def normalize_signal_data(raw_data, source_type, timestamp_str=None):
    """
    Normalizes raw payload data into a dictionary structure mapping to Signal fields.
    """
    trust = SOURCE_TRUST.get(source_type, 0.3)
    
    if timestamp_str:
        # Parse ISO timestamp
        timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
    else:
        timestamp = timezone.now()

    disaster_type = 'General'
    location_name = 'Reported Emergency Area'
    district = 'general'
    lat = None
    lng = None
    severity = 5
    is_life_threat = False
    description = ''
    raw_payload = raw_data

    if source_type == 'call_center':
        disaster_type = raw_data.get('needType', 'General')
        description = raw_data.get('description', '')
        severity = int(raw_data.get('operatorSeverity', 5))
        is_life_threat = bool(raw_data.get('isLifeThreat', False))
        
        lat = float(raw_data.get('lat')) if raw_data.get('lat') else None
        lng = float(raw_data.get('lng')) if raw_data.get('lng') else None
        district = raw_data.get('district') or 'general'
        location_name = raw_data.get('locationName') or 'Reported Emergency Area'

    elif source_type == 'sensor':
        disaster_type = raw_data.get('hazardType', 'Sensor Threshold')
        sensor_name = raw_data.get('sensorName', 'Remote Sensor')
        val = raw_data.get('value', 0)
        unit = raw_data.get('unit', '')
        threshold = raw_data.get('threshold', 0)
        
        description = f"Sensor Breach: {sensor_name} reported {val} {unit} (Threshold: {threshold} {unit})"
        
        # Calculate severity based on breach ratio
        if val >= threshold * 1.5:
            severity = 9
        elif val >= threshold * 1.2:
            severity = 7
        else:
            severity = 5
            
        is_life_threat = severity >= 9
        lat = float(raw_data.get('lat')) if raw_data.get('lat') else None
        lng = float(raw_data.get('lng')) if raw_data.get('lng') else None
        district = raw_data.get('district', 'unknown')
        location_name = raw_data.get('locationName', sensor_name)

    elif source_type == 'social_media':
        text = raw_data.get('text', '')
        nlp = extract_from_text(text)
        
        disaster_type = nlp['disaster_type']
        description = text
        severity = nlp['severity']
        is_life_threat = nlp['is_life_threat']
        
        if nlp['location']:
            location_name = nlp['location']['name']
            lat = nlp['location']['lat']
            lng = nlp['location']['lng']
            district = nlp['location']['district']

    return {
        'source_type': source_type,
        'disaster_type': disaster_type,
        'timestamp': timestamp,
        'description': description,
        'lat': lat,
        'lng': lng,
        'district': district,
        'location_name': location_name,
        'severity': severity,
        'is_life_threat': is_life_threat,
        'raw_payload': raw_payload
    }

def should_fuse(signal_obj, incident_obj, config):
    """
    Checks if a signal matches linkage constraints of an active incident.
    """
    # 1. Exact location name match
    if signal_obj.location_name and incident_obj.location_name:
        sig_loc = signal_obj.location_name.strip().lower()
        inc_loc = incident_obj.location_name.strip().lower()
        if sig_loc == inc_loc and sig_loc not in ['nepal emergency site', 'unknown location']:
            return True

    # 2. Check disaster type compatibility
    is_type_compatible = (
        signal_obj.disaster_type == incident_obj.disaster_type or
        signal_obj.disaster_type in ['General', 'Emergency'] or
        incident_obj.disaster_type in ['General', 'Emergency']
    )
    if not is_type_compatible:
        return False

    # 3. Spatial coordinates proximity check
    if signal_obj.lat is not None and signal_obj.lng is not None and incident_obj.lat is not None and incident_obj.lng is not None:
        distance = get_haversine_distance(signal_obj.lat, signal_obj.lng, incident_obj.lat, incident_obj.lng)
        if distance <= 10.0:
            return True

    return False

def calculate_weighted_centroid(incident):
    """
    Recalculates lat/lng centroid of an incident weighted by signal source trust.
    """
    signals = incident.signals.all()
    lat_sum = 0.0
    lng_sum = 0.0
    weight_sum = 0.0

    for sig in signals:
        if sig.lat is not None and sig.lng is not None:
            weight = SOURCE_TRUST.get(sig.source_type, 0.3)
            lat_sum += sig.lat * weight
            lng_sum += sig.lng * weight
            weight_sum += weight

    if weight_sum == 0:
        return incident.lat, incident.lng

    return lat_sum / weight_sum, lng_sum / weight_sum

def fuse_signal_to_incident(signal_obj, incident_obj):
    """
    Attaches a Signal to an Incident and updates incident metrics.
    """
    # Associate ForeignKey
    signal_obj.incident = incident_obj
    signal_obj.save()

    # Recalculate Centroid
    new_lat, new_lng = calculate_weighted_centroid(incident_obj)
    incident_obj.lat = new_lat
    incident_obj.lng = new_lng

    # Update severity (max of all signals)
    max_severity = max(incident_obj.severity, signal_obj.severity)
    incident_obj.severity = max_severity

    # Update life threat status
    incident_obj.is_life_threat = incident_obj.is_life_threat or signal_obj.is_life_threat

    # Update activity timestamps
    if signal_obj.timestamp < incident_obj.first_reported:
        incident_obj.first_reported = signal_obj.timestamp
    if signal_obj.timestamp > incident_obj.last_reported:
        incident_obj.last_reported = signal_obj.timestamp

    # Select best location name (prefer call center or sensor names over social media)
    signals = incident_obj.signals.all()
    best_source = None
    for sig in signals:
        if best_source is None or SOURCE_TRUST.get(sig.source_type, 0) > SOURCE_TRUST.get(best_source.source_type, 0):
            best_source = sig
            
    if best_source and best_source.location_name:
        incident_obj.location_name = best_source.location_name

    incident_obj.save()

    # Write Audit Step
    msg = f"Fused report {signal_obj.id} from {signal_obj.source_type}. Centroid updated to ({new_lat:.4f}, {new_lng:.4f})."
    AuditLog.objects.create(incident=incident_obj, message=msg)

    return incident_obj

def create_new_incident_from_signal(signal_obj):
    """
    Initializes a new Incident from a single signal.
    """
    # Resolve base vulnerability
    district_obj = next((d for d in DISTRICTS if d['id'] == signal_obj.district), None)
    base_vuln = district_obj['vulnerability'] if district_obj else 5

    resolved_dtype = signal_obj.disaster_type
    if not resolved_dtype or resolved_dtype in ['General', 'Emergency', 'Unknown']:
        if district_obj and district_obj.get('riskType'):
            resolved_dtype = district_obj['riskType'].split('/')[0]
        else:
            resolved_dtype = 'Flood'

    incident = Incident.objects.create(
        disaster_type=resolved_dtype,
        location_name=signal_obj.location_name or 'Unknown Location',
        district_id=signal_obj.district or 'unknown',
        lat=signal_obj.lat if signal_obj.lat is not None else 27.7,
        lng=signal_obj.lng if signal_obj.lng is not None else 85.3,
        first_reported=signal_obj.timestamp,
        last_reported=signal_obj.timestamp,
        severity=signal_obj.severity,
        is_life_threat=signal_obj.is_life_threat,
        vulnerability=base_vuln,
        status='active'
    )

    # Link ForeignKey
    signal_obj.incident = incident
    signal_obj.save()

    # Write Initial Audit Step
    msg = f"Incident initialized from {signal_obj.source_type} report {signal_obj.id}."
    AuditLog.objects.create(incident=incident, message=msg)

    return incident
