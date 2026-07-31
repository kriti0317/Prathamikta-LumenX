import json
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

def index(request):
    """
    Renders the single-page EOC Dispatch Dashboard template.
    """
    return render(request, 'core/index.html')

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

def get_incidents(request):
    """
    Returns active incidents serialized in JSON, sorted by triage priority.
    """
    if Incident.objects.count() == 0:
        seed_default_dataset()

    active_incidents = Incident.objects.exclude(status__in=['resolved', 'dismissed'])
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
            new_status = data['status']
            incident.status = new_status
            
            if new_status == 'rescuers_arrived':
                msg = f"🚑 Rescuers arrived at disaster site ({incident.location_name}). Rescuer arrival manually logged by dispatch."
            elif new_status == 'resolved':
                msg = f"✅ Rescuers completed work at disaster site ({incident.location_name}). Incident resolved and removed from active queue."
            else:
                msg = f"Dispatcher updated status from {old_status} to {new_status}."
                
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

@csrf_exempt
def fetch_gdacs_feeds(request):
    """
    Simulates / fetches live GDACS (Global Disaster Alert & Coordination System) 
    and RSS News feed alerts for real-time disaster monitoring.
    """
    gdacs_alerts = [
        {
            'sourceType': 'sensor',
            'title': 'GDACS Alert: Bhotekoshi River Flash Flood Gauge Threshold Breached',
            'locationName': 'Helambu, Sindhupalchok',
            'severity': 9,
            'description': 'GDACS Sensor Network: Automated hydrological warning trigger in Sindhupalchok basin.'
        },
        {
            'sourceType': 'news',
            'title': 'RSS News Feed: Torrential Rainfall Causes Landslide in Sisneri',
            'locationName': 'Sisneri, Sindhupalchok',
            'severity': 8,
            'description': 'RSS Live Feed: Highway traffic halted as landslide debris blocks Sisneri road corridor.'
        }
    ]
    return JsonResponse({'success': True, 'alerts': gdacs_alerts})

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

@csrf_exempt
def sync_gdacs_live_feed(request):
    """
    Fetches / ingests real-time GDACS (Global Disaster Alert & Coordination System) alerts into Django DB.
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=405)

    try:
        # Sample live GDACS alerts for Nepal region
        gdacs_events = [
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
            },
            {
                'sourceType': 'news',
                'timestamp': timezone.now().isoformat(),
                'rawData': {
                    'sensorId': 'rss_news_sisneri',
                    'sensorName': 'RSS Disaster Stream (Onlinekhabar)',
                    'hazardType': 'Landslide',
                    'lat': 27.791,
                    'lng': 85.850,
                    'district': 'sindhupalchok',
                    'locationName': 'Sisneri, Sindhupalchok',
                    'operatorSeverity': 8,
                    'isLifeThreat': False,
                    'description': 'RSS Feed Alert: Landslide halts highway movement in Sisneri corridor. Clearance team dispatched.'
                }
            }
        ]

        config = SystemConfig.get_config()
        ingested_count = 0

        for item in gdacs_events:
            norm_data = normalize_signal_data(item['rawData'], item['sourceType'], item['timestamp'])
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

        return JsonResponse({'success': True, 'count': ingested_count, 'message': f"Synced {ingested_count} live GDACS & RSS feeds to database."})

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


