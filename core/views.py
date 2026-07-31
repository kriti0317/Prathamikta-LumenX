import json
import requests
import threading
from django.db import close_old_connections
import ssl
import urllib.request
import urllib.parse
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone

from core.models import Incident, Signal, AuditLog, SystemConfig
from core.fusion_engine import (
    normalize_signal_data, should_fuse, fuse_signal_to_incident, 
    create_new_incident_from_signal
)
from core.priority_scorer import calculate_priority
from core.mock_scenarios import PRESETS

LAST_SYNC_TIME = None

def index(request):
    """
    Renders the EOC Dispatch Dashboard template.
    """
    return render(request, 'core/index.html')

def all_incidents(request):
    """
    Renders the All Disaster Incidents table view.
    """
    return render(request, 'core/incidents.html')

def full_map(request):
    """
    Renders the Full GIS Map view.
    """
    return render(request, 'core/full_map.html')

def reports_view(request):
    """
    Renders the Raw Disaster Reports & Signals Database view.
    """
    return render(request, 'core/reports.html')


def seed_default_dataset():
    """Seeds default incidents from prathamikta_default preset if database is empty."""
    preset = PRESETS.get('prathamikta_default')
    if not preset:
        return
    config = SystemConfig.get_config()
    for signal_data in preset['signals']:
        norm_data = normalize_signal_data(
            signal_data['rawData'], 
            signal_data['sourceType'], 
            signal_data['timestamp']
        )
        signal = Signal.objects.create(
            source_type=norm_data['source_type'],
            timestamp=norm_data['timestamp'],
            description=norm_data['description'],
            lat=norm_data['lat'],
            lng=norm_data['lng'],
            district=norm_data['district'],
            location_name=norm_data['location_name'],
            severity=norm_data['severity'],
            is_life_threat=norm_data['is_life_threat'],
            raw_payload=norm_data['raw_payload']
        )
        fused_incident = None
        active_incidents = Incident.objects.exclude(status__in=['resolved', 'dismissed'])
        for inc in active_incidents:
            if should_fuse(signal, inc, config):
                fused_incident = fuse_signal_to_incident(signal, inc)
                break
        if not fused_incident:
            create_new_incident_from_signal(signal)

def run_feeds_sync_in_background():
    try:
        close_old_connections()
        run_feeds_sync()
        print("Background live feeds auto-sync completed successfully.")
    except Exception as e:
        print(f"Background live feeds auto-sync failed: {e}")
    finally:
        close_old_connections()

def get_incidents(request):
    """
    Returns active incidents serialized in JSON, sorted by triage priority.
    Automatically triggers a live feeds sync in a background thread if not done recently.
    """
    print("get_incidents called")
    global LAST_SYNC_TIME
    now = timezone.now()
    if LAST_SYNC_TIME is None or (now - LAST_SYNC_TIME).total_seconds() > 60:
        LAST_SYNC_TIME = now
        # Run sync in a background daemon thread to avoid blocking homepage loading times
        threading.Thread(target=run_feeds_sync_in_background, daemon=True).start()

    if Incident.objects.count() == 0:
        seed_default_dataset()

    active_incidents = Incident.objects.exclude(status__in=['resolved', 'dismissed', 'completed', 'complete', 'closed'])

    config = SystemConfig.get_config()
    current_time = timezone.now()

    serialized = []
    for inc in active_incidents:
        triage = calculate_priority(inc, config, current_time)
        
        # Serialize associated reports
        reports = []
        for sig in inc.signals.all():
            reports.append({
                'signalId': sig.id,
                'sourceType': sig.source_type,
                'timestamp': sig.timestamp.isoformat(),
                'description': sig.description,
                'lat': sig.lat,
                'lng': sig.lng,
                'severity': sig.severity,
                'trust': sig.severity, # placeholder, gets trust in frontend if needed
                'meta': sig.raw_payload # raw payload contains user metadata
            })

        # Serialize audit logs
        audit_history = []
        for log in inc.audit_logs.all():
            audit_history.append({
                'timestamp': log.timestamp.isoformat(),
                'message': log.message
            })

        serialized.append({
            'id': f"inc_{inc.id}",
            'disasterType': inc.disaster_type,
            'locationName': inc.location_name if inc.location_name and 'unknown' not in inc.location_name.lower() else (f"{inc.district_id.title()} Sector" if inc.district_id and 'unknown' not in inc.district_id.lower() else 'Nepal Emergency Site'),
            'districtId': inc.district_id,
            'lat': inc.lat,
            'lng': inc.lng,
            'firstReported': inc.first_reported.isoformat(),
            'lastReported': inc.last_reported.isoformat(),
            'severity': inc.severity,
            'isLifeThreat': inc.is_life_threat,
            'vulnerability': inc.vulnerability,
            'status': inc.status,
            'manualPriority': inc.manual_priority,
            'manuallyAdjusted': inc.manually_adjusted,
            'triageScore': triage['final_score'],
            'formulaScore': triage['formula_score'],
            'aiSuggestedScore': triage['ai_suggested_score'],
            'aiRiskLevel': triage['ai_risk_level'],
            'aiRecommendation': triage['ai_recommendation'],
            'triageLevel': 'Very High' if triage['final_score'] >= 90 else 
                           'High' if triage['final_score'] >= 70 else 
                           'Medium' if triage['final_score'] >= 50 else 'Low',
            'triageOverridden': triage['is_overridden'],
            'triageReason': triage['override_reason'],
            'triageBreakdown': triage['breakdown'],
            'reports': reports,
            'history': audit_history
        })

    # Sort: manual priority overrides take absolute precedence, then triage score
    def get_sort_key(item):
        if item['manualPriority'] is not None:
            return item['manualPriority']
        return item['triageScore']

    serialized.sort(key=get_sort_key, reverse=True)

    # Return config alongside for UI sliders
    return JsonResponse({
        'incidents': serialized,
        'config': {
            'severity_wt': config.severity_wt,
            'corroboration_wt': config.corroboration_wt,
            'trust_wt': config.trust_wt,
            'vulnerability_wt': config.vulnerability_wt,
            'time_wt': config.time_wt,
            'distance_threshold_km': config.distance_threshold_km,
            'time_threshold_hours': config.time_threshold_hours
        }
    })

@csrf_exempt
def ingest_signal(request):
    """
    API endpoint to ingest a raw report.
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=405)

    try:
        data = json.loads(request.body)
        source_type = data.get('sourceType')
        raw_data = data.get('rawData')
        timestamp_str = data.get('timestamp')

        if not source_type or not raw_data:
            return JsonResponse({'error': 'Missing sourceType or rawData'}, status=400)

        # Normalize and create Signal object
        norm_data = normalize_signal_data(raw_data, source_type, timestamp_str)
        signal = Signal.objects.create(
            source_type=norm_data['source_type'],
            timestamp=norm_data['timestamp'],
            description=norm_data['description'],
            lat=norm_data['lat'],
            lng=norm_data['lng'],
            district=norm_data['district'],
            location_name=norm_data['location_name'],
            severity=norm_data['severity'],
            is_life_threat=norm_data['is_life_threat'],
            raw_payload=norm_data['raw_payload']
        )

        # Run Linkage
        config = SystemConfig.get_config()
        active_incidents = Incident.objects.exclude(status__in=['resolved', 'dismissed'])
        
        fused_incident = None
        for inc in active_incidents:
            if should_fuse(signal, inc, config):
                fused_incident = fuse_signal_to_incident(signal, inc)
                break

        if not fused_incident:
            fused_incident = create_new_incident_from_signal(signal)

        return JsonResponse({
            'success': True,
            'incidentId': f"inc_{fused_incident.id}",
            'fused': signal.incident_id is not None
        })

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@csrf_exempt
def load_preset(request):
    """
    Clears database and seeds timeline records of the selected preset.
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=405)

    try:
        data = json.loads(request.body)
        preset_key = data.get('presetKey')
        preset = PRESETS.get(preset_key)

        if not preset:
            return JsonResponse({'error': 'Invalid preset key'}, status=400)

        # 1. Clear database
        Signal.objects.all().delete()
        Incident.objects.all().delete()
        AuditLog.objects.all().delete()

        # 2. Ingest preset signals sequentially
        config = SystemConfig.get_config()
        for signal_data in preset['signals']:
            norm_data = normalize_signal_data(
                signal_data['rawData'], 
                signal_data['sourceType'], 
                signal_data['timestamp']
            )
            signal = Signal.objects.create(
                source_type=norm_data['source_type'],
                timestamp=norm_data['timestamp'],
                description=norm_data['description'],
                lat=norm_data['lat'],
                lng=norm_data['lng'],
                district=norm_data['district'],
                location_name=norm_data['location_name'],
                severity=norm_data['severity'],
                is_life_threat=norm_data['is_life_threat'],
                raw_payload=norm_data['raw_payload']
            )

            # Linkage
            fused_incident = None
            active_incidents = Incident.objects.exclude(status__in=['resolved', 'dismissed'])
            for inc in active_incidents:
                if should_fuse(signal, inc, config):
                    fused_incident = fuse_signal_to_incident(signal, inc)
                    break
            
            if not fused_incident:
                create_new_incident_from_signal(signal)

        return JsonResponse({'success': True, 'count': len(preset['signals'])})

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@csrf_exempt
def reset_db(request):
    """
    Resets all dynamic incident data in the database.
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=405)

    Signal.objects.all().delete()
    Incident.objects.all().delete()
    AuditLog.objects.all().delete()
    return JsonResponse({'success': True})

@csrf_exempt
def update_config(request):
    """
    Saves formula weights and record linkage parameters to the config database.
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=405)

    try:
        data = json.loads(request.body)
        config = SystemConfig.get_config()
        
        if 'severity_wt' in data: config.severity_wt = int(data['severity_wt'])
        if 'corroboration_wt' in data: config.corroboration_wt = int(data['corroboration_wt'])
        if 'trust_wt' in data: config.trust_wt = int(data['trust_wt'])
        if 'vulnerability_wt' in data: config.vulnerability_wt = int(data['vulnerability_wt'])
        if 'time_wt' in data: config.time_wt = int(data['time_wt'])
        if 'distance_threshold_km' in data: config.distance_threshold_km = float(data['distance_threshold_km'])
        if 'time_threshold_hours' in data: config.time_threshold_hours = float(data['time_threshold_hours'])
        
        config.save()
        return JsonResponse({'success': True})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@csrf_exempt
def incident_override(request, incident_id):
    """
    Allows dispatcher to override priority score or update status.
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=405)

    try:
        data = json.loads(request.body)
        # Strip 'inc_' prefix
        db_id = int(incident_id.replace('inc_', ''))
        incident = Incident.objects.get(id=db_id)

        if 'status' in data:
            old_status = incident.status
            requested_status = str(data['status']).strip().lower()
            if requested_status in ['resolved', 'completed', 'complete', 'closed', 'dismissed']:
                incident.status = 'resolved'
            else:
                incident.status = requested_status
            
            if incident.status == 'rescuers_arrived':
                msg = f"🚑 Rescuers arrived at disaster site ({incident.location_name}). Rescuer arrival manually logged by dispatch."
            elif incident.status == 'resolved':
                msg = f"✅ Rescuers completed work at disaster site ({incident.location_name}). Incident resolved and removed from active queue."
            else:
                msg = f"Dispatcher updated status from {old_status} to {incident.status}."
                
            incident.save()
            AuditLog.objects.create(incident=incident, message=msg)


        if 'manualPriority' in data:
            priority_val = data['manualPriority']
            if priority_val == "" or priority_val is None:
                incident.manual_priority = None
                incident.manually_adjusted = False
                msg = "Dispatcher cleared manual priority override."
            else:
                incident.manual_priority = int(priority_val)
                incident.manually_adjusted = True
                msg = f"Dispatcher manually overrode priority score to {incident.manual_priority}."
            
            AuditLog.objects.create(incident=incident, message=msg)

        incident.save()
        return JsonResponse({'success': True})

    except Incident.DoesNotExist:
        return JsonResponse({'error': 'Incident not found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

NEPAL_BOUNDS = {
    "min_lat": 26.3,
    "max_lat": 30.5,
    "min_lng": 80.0,
    "max_lng": 88.2
}

def is_within_nepal(lat, lng):
    if lat is None or lng is None:
        return False
    return (NEPAL_BOUNDS["min_lat"] <= lat <= NEPAL_BOUNDS["max_lat"] and 
            NEPAL_BOUNDS["min_lng"] <= lng <= NEPAL_BOUNDS["max_lng"])

def get_specific_location_name(lat, lng, default_name=None):
    """
    Resolves specific geocoded location name. Uses the local municipality database
    first for speed and offline reliability, and falls back to Nominatim API if no
    close municipality is matched.
    """
    if lat is None or lng is None:
        return default_name or "Nepal"
        
    # 1. Local Lookup: Find closest municipality from nepal_geo_data (instant, 0ms, offline)
    try:
        from core.nepal_geo_data import MUNICIPALITIES, DISTRICTS
        from core.fusion_engine import get_haversine_distance
        
        closest_mun = None
        min_mun_dist = float('inf')
        for mun in MUNICIPALITIES:
            dist = get_haversine_distance(lat, lng, mun['lat'], mun['lng'])
            if dist < min_mun_dist:
                min_mun_dist = dist
                closest_mun = mun
                
        if closest_mun and min_mun_dist < 20.0:
            return f"{closest_mun['name']}, {closest_mun['district'].capitalize()}"
    except Exception:
        pass

    # 2. OpenStreetMap Nominatim reverse geocode (fallback)
    try:
        url = f"https://nominatim.openstreetmap.org/reverse?lat={lat}&lon={lng}&format=json&accept-language=en"
        r = requests.get(url, headers={'User-Agent': 'LumneX-Emergency-App/1.0'}, timeout=1.5)
        if r.status_code == 200:
            data = r.json()
            addr = data.get('address', {})
            specific = (addr.get('suburb') or addr.get('town') or addr.get('village') or 
                        addr.get('municipality') or addr.get('city_district') or addr.get('city') or 
                        addr.get('hamlet') or addr.get('neighbourhood'))
            county = addr.get('county') or addr.get('state') or addr.get('country')
            if specific and county:
                county_clean = county.replace(" District", "").strip()
                return f"{specific}, {county_clean}"
            elif specific:
                return specific
    except Exception:
        pass

    # 3. Final Fallback: Closest District
    try:
        from core.nepal_geo_data import DISTRICTS
        from core.fusion_engine import get_haversine_distance
        closest_dist = None
        min_dist_val = float('inf')
        for dist in DISTRICTS:
            d = get_haversine_distance(lat, lng, dist['lat'], dist['lng'])
            if d < min_dist_val:
                min_dist_val = d
                closest_dist = dist
                
        if closest_dist:
            return f"Near {closest_dist['name']}"
    except Exception:
        pass
        
    return default_name or "Nepal"

def fetch_rss_news_items():
    """
    Fetches real-time RSS feeds from Onlinekhabar, Himalayan Times, and GDACS RSS,
    runs NLP extraction, and returns structured disaster/emergency news items.
    """
    import xml.etree.ElementTree as ET
    import re
    from core.nlp_extractor import extract_from_text
    
    rss_urls = [
        "https://english.onlinekhabar.com/feed",
        "https://thehimalayantimes.com/feed",
        "https://www.gdacs.org/xml/rss.xml"
    ]
    
    results = []
    seen_titles = set()
    
    for url in rss_urls:
        try:
            resp = requests.get(url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}, timeout=6.0)
            if resp.status_code == 200:
                raw_content = getattr(resp, 'content', None)
                if not raw_content and hasattr(resp, 'text') and resp.text:
                    raw_content = resp.text.encode('utf-8')
                if not raw_content:
                    continue
                root = ET.fromstring(raw_content)
                items = root.findall('.//item')
                for item in items:
                    title_node = item.find('title')
                    desc_node = item.find('description')
                    guid_node = item.find('guid')
                    
                    title = title_node.text if title_node is not None and title_node.text else ''
                    desc = desc_node.text if desc_node is not None and desc_node.text else ''
                    
                    title = re.sub(r'<[^>]+>', '', title).strip()
                    desc = re.sub(r'<[^>]+>', '', desc).strip()
                    
                    if not title or title in seen_titles:
                        continue
                    seen_titles.add(title)
                    
                    full_text = f"{title}. {desc}"
                    nlp_res = extract_from_text(full_text)
                    
                    # Check if disaster/emergency relevant
                    is_relevant = (
                        nlp_res['disaster_type'] != 'General' or 
                        nlp_res['location'] is not None or 
                        any(w in full_text.lower() for w in [
                            'disaster', 'emergency', 'rescue', 'casualty', 'death', 'killed', 
                            'avalanche', 'flood', 'landslide', 'fire', 'rain', 'storm', 'quake', 
                            'blast', 'curfew', 'clash', 'strike', 'missing', 'trapped'
                        ])
                    )
                    
                    if is_relevant:
                        loc = nlp_res['location']
                        if loc:
                            lat, lng = loc['lat'], loc['lng']
                            district = loc['district']
                            spec_loc = loc['name']
                        else:
                            lat, lng = 27.7, 85.32
                            district = 'kathmandu'
                            spec_loc = 'Nepal Emergency Site'
                            
                        guid_text = guid_node.text if guid_node is not None and guid_node.text else title
                        guid_id = guid_text.split('?p=')[-1] if '?p=' in guid_text else str(abs(hash(title)))
                        
                        results.append({
                            'sourceType': 'news',
                            'title': f"RSS News: {title[:75]}",
                            'locationName': spec_loc,
                            'district': district,
                            'severity': nlp_res['severity'],
                            'lat': lat,
                            'lng': lng,
                            'description': f"{title} - {desc[:150]}",
                            'disasterType': nlp_res['disaster_type'] if nlp_res['disaster_type'] != 'General' else 'Emergency',
                            'isLifeThreat': nlp_res['is_life_threat'],
                            'guid': guid_id,
                            'rawText': full_text
                        })
        except Exception:
            pass
            
    return results


@csrf_exempt
def fetch_gdacs_feeds(request):
    """
    Fetches live GDACS events and real RSS news feeds.
    Returns combined external alerts to front-end live feed sidebar.
    """
    alerts = []
    
    # 1. Fetch GDACS alerts
    try:
        url = "https://www.gdacs.org/gdacsapi/api/events/geteventlist/SEARCH"
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            data = response.json()
            features = data.get('features', [])
            for feat in features:
                props = feat.get('properties', {})
                geom = feat.get('geometry', {})
                coords = geom.get('coordinates', [])
                if len(coords) >= 2:
                    lng, lat = float(coords[0]), float(coords[1])
                    if is_within_nepal(lat, lng):
                        alertlevel = props.get('alertlevel', 'Green').capitalize()
                        severity = 5
                        if alertlevel == 'Orange':
                            severity = 7
                        elif alertlevel == 'Red':
                            severity = 9
                            
                        alerts.append({
                            'sourceType': 'sensor',
                            'title': f"GDACS {alertlevel} Alert: {props.get('eventname', 'Disaster')}",
                            'locationName': get_specific_location_name(lat, lng, default_name=props.get('name', 'Nepal')),
                            'severity': severity,
                            'lat': lat,
                            'lng': lng,
                            'description': props.get('description', f"GDACS alert level {alertlevel} near coordinates {lat}, {lng}.")
                        })
    except Exception:
        pass

    # 2. Fetch live RSS news items
    rss_items = fetch_rss_news_items()
    for item in rss_items[:8]:
        alerts.append({
            'sourceType': 'news',
            'title': item['title'],
            'locationName': item['locationName'],
            'severity': item['severity'],
            'lat': item['lat'],
            'lng': item['lng'],
            'description': item['description']
        })

    # 3. Fallback mock data if network returned no alerts
    if not alerts:
        alerts = [
            {
                'sourceType': 'sensor',
                'title': 'GDACS Alert: Bhotekoshi River Flash Flood Gauge Threshold Breached (Mock)',
                'locationName': 'Helambu, Sindhupalchok',
                'severity': 9,
                'lat': 27.832,
                'lng': 85.584,
                'description': 'GDACS Sensor Network: Automated hydrological warning trigger in Sindhupalchok basin.'
            },
            {
                'sourceType': 'news',
                'title': 'RSS News Feed: Torrential Rainfall Causes Landslide in Sisneri (Mock)',
                'locationName': 'Sisneri, Sindhupalchok',
                'severity': 8,
                'lat': 27.850,
                'lng': 85.600,
                'description': 'RSS Live Feed: Highway traffic halted as landslide debris blocks Sisneri road corridor.'
            }
        ]
        
    return JsonResponse({'success': True, 'alerts': alerts})


@csrf_exempt
def chatbot_query(request):
    """
    EOC AI Chatbot assistant that answers queries, gives real-time statistical data,
    explains priority scores, and allows executing rescuer logs & actions via chat.
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=405)


    try:
        data = json.loads(request.body)
        user_message = data.get('message', '').strip().lower()

        active_incidents = Incident.objects.exclude(status__in=['resolved', 'dismissed'])
        total_count = active_incidents.count()
        total_signals = Signal.objects.count()
        config = SystemConfig.get_config()
        current_time = timezone.now()

        high_priority = 0
        med_priority = 0
        low_priority = 0
        rescuers_arrived_count = 0
        top_incident = None
        max_score = -1

        incident_summaries = []
        for inc in active_incidents:
            triage = calculate_priority(inc, config, current_time)
            score = inc.manual_priority if inc.manual_priority is not None else triage['final_score']
            if score >= 80: high_priority += 1
            elif score >= 50: med_priority += 1
            else: low_priority += 1

            if inc.status == 'rescuers_arrived':
                rescuers_arrived_count += 1

            if score > max_score:
                max_score = score
                top_incident = inc

            incident_summaries.append(f"• {inc.disaster_type} at {inc.location_name} (Priority Score: {score}/100, Status: {inc.status.upper()})")

        # Response logic based on user query keywords
        if any(w in user_message for w in ['stat', 'summary', 'count', 'overview', 'how many']):
            reply = (
                f"📊 Live EOC Statistics Summary:\n"
                f"• Active Incidents: {total_count}\n"
                f"• High Priority: {high_priority} | Medium: {med_priority} | Low: {low_priority}\n"
                f"• Total Signals Ingested: {total_signals} (Calls, GDACS Sensors, Social Media, RSS News)\n"
                f"• Rescuer Teams Currently On-Site: {rescuers_arrived_count}\n"
                f"• Current Highest Priority Event: {top_incident.disaster_type if top_incident else 'None'} at {top_incident.location_name if top_incident else 'N/A'} (Score: {max_score}/100)"
            )
        elif any(w in user_message for w in ['highest', 'top', 'urgent', 'critical']):
            if top_incident:
                reply = (
                    f"🚨 Highest Priority Disaster Alert:\n"
                    f"• Incident: {top_incident.disaster_type} - {top_incident.location_name}\n"
                    f"• Combined Priority Score: {max_score}/100\n"
                    f"• Rescuer Status: {top_incident.status.replace('_', ' ').title()}\n"
                    f"• Location: Lat {top_incident.lat:.4f}, Lng {top_incident.lng:.4f}\n"
                    f"• Corroborating Reports Count: {top_incident.signals.count()}"
                )
            else:
                reply = "No active high priority incidents currently logged in system."

        elif any(w in user_message for w in ['method', 'formula', 'sort', 'score', 'ai']):
            reply = (
                f"🧠 PRATHAMIKTA Hybrid Priority Triage System uses 2 methods:\n"
                f"1. Method i (Formula Score):\n"
                f"   priority = (severity × 3) + (corroboration × 2) + (source_trust × 2) + (vulnerability × 1) + (time_waiting × 1)\n"
                f"2. Method ii (AI Model Suggestion):\n"
                f"   NLP semantic model evaluating life-threat keywords ('trapped', 'drowning', 'unconscious', 'collapsed') and casualty risk with space for Gemini LLM API Key."
            )

        elif any(w in user_message for w in ['list', 'incidents', 'all']):
            reply = "📋 Current Priority Incident List:\n" + "\n".join(incident_summaries if incident_summaries else ["No active incidents."])

        elif any(w in user_message for w in ['help', 'hi', 'hello', 'hey']):
            reply = (
                "👋 Hello! I am the PRATHAMIKTA EOC AI Chatbot Assistant.\n"
                "You can ask me about:\n"
                "• 'Show disaster statistics' for real-time overview counts\n"
                "• 'What is the highest priority incident?'\n"
                "• 'Explain the priority sorting methods'\n"
                "• 'List all active disaster sites'"
            )
        else:
            reply = (
                f"I processed your query against live EOC database. Active incidents: {total_count} ({high_priority} High Priority). "
                f"Highest priority event is {top_incident.location_name if top_incident else 'N/A'} (Score: {max_score}/100). "
                f"Ask me for 'statistics', 'highest priority', or 'priority sorting formula' for deeper breakdown!"
            )

        return JsonResponse({
            'success': True,
            'reply': reply,
            'stats': {
                'totalIncidents': total_count,
                'highPriority': high_priority,
                'medPriority': med_priority,
                'lowPriority': low_priority,
                'totalSignals': total_signals,
                'rescuersArrived': rescuers_arrived_count
            }
        })

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@csrf_exempt
def nearby_aid_layer(request):
    """
    Returns live nearby IATI responder activity records from d-portal's public dquery endpoint.
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=405)

    try:
        data = json.loads(request.body)
        district = (data.get('district') or '').strip()
        location = (data.get('location') or '').strip()
        lat = float(data.get('lat', 0) or 0)
        lng = float(data.get('lng', 0) or 0)

        if not lat or not lng:
            return JsonResponse({
                'success': True,
                'source': 'd-portal IATI live activity search',
                'resourceCount': 0,
                'nearby': [],
                'query': 'no coordinates'
            })

        lat_delta = 0.6
        lng_delta = 0.8
        min_lat = max(-90, lat - lat_delta)
        max_lat = min(90, lat + lat_delta)
        min_lng = max(-180, lng - lng_delta)
        max_lng = min(180, lng + lng_delta)

        sql = (
            "SELECT a.aid, a.title, a.reporting, a.reporting_ref, l.location_name, "
            "l.location_latitude, l.location_longitude "
            "FROM act a JOIN location l ON l.aid = a.aid "
            f"WHERE l.location_latitude BETWEEN {min_lat} AND {max_lat} "
            f"AND l.location_longitude BETWEEN {min_lng} AND {max_lng} "
            "LIMIT 5"
        )

        query_url = 'https://d-portal.iatistandard.org/dquery?sql=' + urllib.parse.quote(sql)
        ctx = ssl._create_unverified_context()
        req = urllib.request.Request(
            query_url,
            headers={'User-Agent': 'Mozilla/5.0', 'Accept': 'application/json'}
        )
        with urllib.request.urlopen(req, timeout=18, context=ctx) as resp:
            payload = json.loads(resp.read().decode('utf-8'))

        rows = payload.get('rows', [])
        nearby = []
        for row in rows:
            lat_val = row.get('location_latitude')
            lng_val = row.get('location_longitude')
            if not lat_val or not lng_val:
                continue

            nearby.append({
                'aid': row.get('aid'),
                'title': row.get('title') or 'IATI activity',
                'organization': row.get('reporting') or row.get('reporting_ref') or 'Unknown organisation',
                'contact': row.get('reporting_ref') or row.get('reporting') or 'Contact not disclosed',
                'datasetUrl': f"https://d-portal.iatistandard.org/ctrack.html#/search?search={urllib.parse.quote(row.get('aid') or '')}&view=main",
                'notes': (f"{row.get('location_name') or 'Exact location'} near {location or district or 'incident'}").strip()[:180],
                'lat': float(lat_val),
                'lng': float(lng_val)
            })

        return JsonResponse({
            'success': True,
            'source': 'd-portal IATI live activity search',
            'resourceCount': len(nearby),
            'nearby': nearby,
            'query': sql
        })

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


def get_all_signals(request):
    """
    Returns all raw signals stored in the database for the Reports view.
    """
    signals = Signal.objects.all().order_by('-timestamp')
    serialized = []
    for sig in signals:
        serialized.append({
            'id': sig.id,
            'sourceType': sig.source_type,
            'disasterType': sig.disaster_type,
            'timestamp': sig.timestamp.isoformat(),
            'description': sig.description,
            'locationName': (sig.location_name if sig.location_name and 'unknown' not in sig.location_name.lower() else None) or (sig.district if sig.district and 'unknown' not in sig.district.lower() else None) or 'Nepal Emergency Site',
            'district': sig.district,
            'lat': sig.lat,
            'lng': sig.lng,
            'severity': sig.severity,
            'isLifeThreat': sig.is_life_threat,
            'incidentId': f"inc_{sig.incident_id}" if sig.incident_id else None
        })
    return JsonResponse({'success': True, 'signals': serialized})

def run_feeds_sync():
    """
    Core sync logic that pulls live GDACS alerts, live Onlinekhabar news RSS,
    and generates realistic dummy call logs, geocoding them to specific locations.
    """
    config = SystemConfig.get_config()
    ingested_count = 0

    # 1. Sync Live GDACS Sensor Alerts
    try:
        url = "https://www.gdacs.org/gdacsapi/api/events/geteventlist/SEARCH"
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            data = response.json()
            features = data.get('features', [])
            for feature in features:
                props = feature.get('properties', {})
                geom = feature.get('geometry', {})
                coords = geom.get('coordinates', [])
                
                if len(coords) >= 2:
                    lng, lat = float(coords[0]), float(coords[1])
                    
                    # Filter for Nepal region
                    if is_within_nepal(lat, lng):
                        alert_level = props.get('alertlevel', 'Green').capitalize()
                        event_type = props.get('eventtype', 'Disaster')
                        event_id = props.get('eventid', '')
                        
                        if alert_level == 'Red':
                            val, threshold = 1.5, 1.0
                        elif alert_level == 'Orange':
                            val, threshold = 1.2, 1.0
                        else:
                            val, threshold = 1.0, 1.0
                            
                        spec_loc = get_specific_location_name(lat, lng, default_name=props.get('name', 'Nepal'))
                        
                        raw_data = {
                            'sensorId': f"gdacs_{event_type.lower()}_{event_id}",
                            'sensorName': f"GDACS Alert ({props.get('eventname', event_type)})",
                            'hazardType': props.get('eventname', event_type),
                            'value': val,
                            'unit': 'alert level multiplier',
                            'threshold': threshold,
                            'lat': lat,
                            'lng': lng,
                            'district': props.get('country', 'Nepal').lower(),
                            'locationName': spec_loc,
                            'description': props.get('description', f"GDACS {alert_level} Alert")
                        }
                        
                        norm_data = normalize_signal_data(raw_data, 'sensor', timezone.now().isoformat())
                        
                        unique_desc = norm_data['description']
                        if not Signal.objects.filter(description=unique_desc, lat=norm_data['lat'], lng=norm_data['lng']).exists():
                            signal = Signal.objects.create(
                                source_type=norm_data['source_type'],
                                timestamp=norm_data['timestamp'],
                                description=norm_data['description'],
                                lat=norm_data['lat'],
                                lng=norm_data['lng'],
                                district=norm_data['district'],
                                location_name=norm_data['location_name'],
                                severity=norm_data['severity'],
                                is_life_threat=norm_data['is_life_threat'],
                                raw_payload=norm_data['raw_payload']
                            )
                            ingested_count += 1
                            
                            # Fuse to incidents
                            fused_incident = None
                            active_incidents = Incident.objects.exclude(status__in=['resolved', 'dismissed'])
                            for inc in active_incidents:
                                if should_fuse(signal, inc, config):
                                    fused_incident = fuse_signal_to_incident(signal, inc)
                                    break
                            if not fused_incident:
                                create_new_incident_from_signal(signal)
    except Exception:
        pass

    # 2. Sync Live News as Social Media / News Alerts (Onlinekhabar, Himalayan Times, GDACS RSS)
    try:
        rss_news = fetch_rss_news_items()
        for news_item in rss_news:
            raw_data = {
                'sensorId': f"rss_{news_item['guid']}",
                'sensorName': f"RSS News Feed ({news_item['locationName']})",
                'text': news_item['description'],
                'lat': news_item['lat'],
                'lng': news_item['lng'],
                'district': news_item['district'],
                'locationName': news_item['locationName'],
                'operatorSeverity': news_item['severity'],
                'isLifeThreat': news_item['isLifeThreat'],
                'needType': news_item['disasterType']
            }
            
            norm_data = normalize_signal_data(raw_data, 'social_media', timezone.now().isoformat())
            norm_data['location_name'] = news_item['locationName']
            
            if not Signal.objects.filter(description=norm_data['description']).exists():
                signal = Signal.objects.create(
                    source_type=norm_data['source_type'],
                    timestamp=norm_data['timestamp'],
                    description=norm_data['description'],
                    lat=norm_data['lat'],
                    lng=norm_data['lng'],
                    district=norm_data['district'],
                    location_name=norm_data['location_name'],
                    severity=norm_data['severity'],
                    is_life_threat=norm_data['is_life_threat'],
                    raw_payload=norm_data['raw_payload']
                )
                ingested_count += 1
                
                fused_incident = None
                active_incidents = Incident.objects.exclude(status__in=['resolved', 'dismissed'])
                for inc in active_incidents:
                    if should_fuse(signal, inc, config):
                        fused_incident = fuse_signal_to_incident(signal, inc)
                        break
                if not fused_incident:
                    create_new_incident_from_signal(signal)
    except Exception as e:
        print(f"Error syncing RSS feed: {e}")

    # 3. Generate Simulated Real-time Call Log (with specific location/ward)
    try:
        import random
        from core.nepal_geo_data import MUNICIPALITIES
        
        mun = random.choice(MUNICIPALITIES)
        caller_names = ["Ram Prasad", "Sita Devi", "Hari Shrestha", "Gita Tamang", "Nabin Gurung", "Aayush Pandey", "Prerana Thapa"]
        caller_name = random.choice(caller_names)
        phone = f"98{random.randint(10000000, 99999999)}"
        
        disaster_templates = [
            ("Flood", f"Water levels rising rapidly in the local river corridor near {mun['name']}. Several farm fields are inundated and we need support."),
            ("Landslide", f"A landslide occurred on the slope above {mun['name']}. It has blocked the road and damaged electricity poles. No casualties reported yet."),
            ("Earthquake", f"Strong tremors felt in {mun['name']}. Houses have cracks and residents are staying outside in the open fields. Need blankets and food support.")
        ]
        dtype, desc = random.choice(disaster_templates)
        
        call_lat = mun['lat'] + (random.random() - 0.5) * 0.01
        call_lng = mun['lng'] + (random.random() - 0.5) * 0.01
        
        spec_loc = get_specific_location_name(call_lat, call_lng, default_name=f"{mun['name']}, {mun['district'].capitalize()}")
        spec_loc_with_ward = f"{spec_loc.split(',')[0]} Ward {random.randint(1, 9)}, {mun['district'].capitalize()}"
        
        raw_call = {
            'callerName': caller_name,
            'callerContact': phone,
            'needType': dtype,
            'lat': call_lat,
            'lng': call_lng,
            'district': mun['district'],
            'locationName': spec_loc_with_ward,
            'operatorSeverity': random.randint(5, 8),
            'isLifeThreat': random.choice([True, False]),
            'description': desc
        }
        
        norm_call = normalize_signal_data(raw_call, 'call_center', timezone.now().isoformat())
        
        signal_call = Signal.objects.create(
            source_type=norm_call['source_type'],
            timestamp=norm_call['timestamp'],
            description=norm_call['description'],
            lat=norm_call['lat'],
            lng=norm_call['lng'],
            district=norm_call['district'],
            location_name=norm_call['location_name'],
            severity=norm_call['severity'],
            is_life_threat=norm_call['is_life_threat'],
            raw_payload=norm_call['raw_payload']
        )
        ingested_count += 1
        
        fused_incident = None
        active_incidents = Incident.objects.exclude(status__in=['resolved', 'dismissed'])
        for inc in active_incidents:
            if should_fuse(signal_call, inc, config):
                fused_incident = fuse_signal_to_incident(signal_call, inc)
                break
        if not fused_incident:
            create_new_incident_from_signal(signal_call)
    except Exception:
        pass

    # 4. Fallback to mock ingest ONLY if the DB is completely empty and no live events are synced
    if ingested_count == 0 and Signal.objects.count() == 0:
        mock_events = [
            {
                'sourceType': 'sensor',
                'timestamp': timezone.now().isoformat(),
                'rawData': {
                    'sensorId': 'gdacs_flood_bhotekoshi',
                    'sensorName': 'GDACS Global Satellite & Gauge Alert (Bhotekoshi)',
                    'hazardType': 'Flood',
                    'value': 8.4,
                    'unit': 'meters',
                    'threshold': 6.0,
                    'lat': 27.832,
                    'lng': 85.584,
                    'district': 'sindhupalchok',
                    'locationName': 'Helambu, Sindhupalchok',
                    'operatorSeverity': 9,
                    'isLifeThreat': True,
                    'description': 'GDACS Orange Alert: Flood disaster level 2.5 in Bhotekoshi basin. Severe inundation risk.'
                }
            }
        ]
        for item in mock_events:
            norm_data = normalize_signal_data(item['rawData'], item['sourceType'], item['timestamp'])
            Signal.objects.create(
                source_type=norm_data['source_type'],
                timestamp=norm_data['timestamp'],
                description=norm_data['description'],
                lat=norm_data['lat'],
                lng=norm_data['lng'],
                district=norm_data['district'],
                location_name=norm_data['location_name'],
                severity=norm_data['severity'],
                is_life_threat=norm_data['is_life_threat'],
                raw_payload=norm_data['raw_payload']
            )
            ingested_count += 1

    return ingested_count

@csrf_exempt
def sync_gdacs_live_feed(request):
    """
    Fetches real-time GDACS (Global Disaster Alert & Coordination System) alerts,
    parses real Onlinekhabar RSS news as social media alerts,
    generates simulated realistic call log logs,
    and ingests everything using specific geocoded location names.
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=405)

    try:
        count = run_feeds_sync()
        return JsonResponse({
            'success': True,
            'count': count,
            'message': f"Synced {count} real-time signals (GDACS, News RSS, Call logs) to database."
        })
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@csrf_exempt
def vulnerability_layers(request):
    """
    Returns structured District Vulnerability Heatmap GIS layer for Leaflet map.
    """
    from core.nepal_geo_data import DISTRICTS, SENSOR_STATIONS

    district_heatmap = []
    for dist in DISTRICTS:
        vuln = dist.get('vulnerability', 5)
        color = '#ef4444' if vuln >= 8 else ('#f97316' if vuln >= 6 else '#eab308')
        district_heatmap.append({
            'id': dist['id'],
            'name': dist['name'],
            'nameNep': dist.get('nameNep', dist['name']),
            'lat': dist['lat'],
            'lng': dist['lng'],
            'vulnerability': vuln,
            'riskType': dist.get('riskType', 'General'),
            'population': dist.get('population', 0),
            'province': dist.get('province', 1),
            'color': color,
            'radius': vuln * 2200
        })

    return JsonResponse({
        'success': True,
        'districtHeatmap': district_heatmap,
        'sensorStations': SENSOR_STATIONS
    })




