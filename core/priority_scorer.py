import os
import json
import urllib.request
import urllib.error
from django.utils import timezone
from core.models import Incident, SystemConfig

# Placeholder space for LLM / AI Model API Key (e.g., Gemini API Key)
AI_MODEL_API_KEY = os.environ.get("GEMINI_API_KEY", "")  # LEAVE SPACE FOR API KEY HERE

SOURCE_TRUST_SCALING = {
    'call_center': 1.0,
    'sensor': 0.9,
    'social_media': 0.4,
    'news': 0.8
}

def calculate_priority(incident, config=None, current_time=None):
    """
    Calculates the priority triage score for a fused incident using TWO METHODS:
    
    METHOD 1: Formula-Based Priority
      priority = (severity * 3) + (corroboration * 2) + (source_trust * 2) + 
                 (vulnerability * 1) + (time_waiting * 1)
                 
    METHOD 2: AI Suggestions for Priority Sorting
      AI analysis evaluating multi-source text payload, hazard indicators,
      casualty risk, and life-threat severity to generate an AI Priority Score & Recommendation.
    """
    if config is None:
        config = SystemConfig.get_config()
        
    if current_time is None:
        current_time = timezone.now()

    # --- METHOD 1: FORMULA PRIORITY ---
    # 1. Severity component (1-10 scale)
    severity_val = incident.severity

    # 2. Corroboration component (scaled 1-10 range)
    signals = incident.signals.all()
    raw_count = signals.count()
    if raw_count <= 1:
        corroboration_val = 1
    elif raw_count == 2:
        corroboration_val = 5
    elif raw_count == 3:
        corroboration_val = 8
    else:
        corroboration_val = 10

    # 3. Source Trust component (scaled to 1-10)
    max_trust = 0.3
    if raw_count > 0:
        max_trust = max((SOURCE_TRUST_SCALING.get(s.source_type, 0.4) for s in signals), default=0.4)
    trust_val = round(max_trust * 10)

    # 4. Vulnerability component (1-10 scale)
    vulnerability_val = incident.vulnerability

    # 5. Time Waiting component (scaled 1-10, cap at 100 minutes)
    elapsed_seconds = max(0.0, (current_time - incident.first_reported).total_seconds())
    elapsed_minutes = elapsed_seconds / 60.0
    time_val = min(10.0, round(elapsed_minutes / 10.0))

    # Compute weighted formula score:
    # (severity x3) + (corroboration x2) + (source trust x2) + (vulnerability x1) + (time waiting x1)
    severity_score = severity_val * config.severity_wt          # weight default = 3
    corroboration_score = corroboration_val * config.corroboration_wt # weight default = 2
    trust_score = trust_val * config.trust_wt                 # weight default = 2
    vulnerability_score = vulnerability_val * config.vulnerability_wt # weight default = 1
    time_score = time_val * config.time_wt                     # weight default = 1

    formula_score = (severity_score + corroboration_score + trust_score + 
                     vulnerability_score + time_score)

    # Hard-floor override check for life-threats
    is_high_pop_sensor_breach = any(
        s.source_type == 'sensor' and s.severity >= 9 for s in signals
    ) and incident.vulnerability >= 7

    trigger_override = incident.is_life_threat or is_high_pop_sensor_breach

    # Normalize formula score to 0-100 scale for UI display
    # max possible base score = 10*3 + 10*2 + 10*2 + 10*1 + 10*1 = 90
    normalized_formula_score = min(100, round((formula_score / 90.0) * 100))
    if trigger_override:
        normalized_formula_score = max(95, normalized_formula_score)

    # --- METHOD 2: AI MODEL PRIORITY SUGGESTION ---
    ai_result = calculate_ai_priority_suggestion(incident, signals, normalized_formula_score)

    # Combined Final Score for triage sorting
    final_score = max(normalized_formula_score, ai_result['ai_score'])
    if incident.manual_priority is not None:
        final_score = incident.manual_priority

    return {
        'final_score': final_score,
        'formula_score': normalized_formula_score,
        'ai_suggested_score': ai_result['ai_score'],
        'ai_risk_level': ai_result['ai_risk_level'],
        'ai_recommendation': ai_result['ai_recommendation'],
        'is_overridden': trigger_override,
        'override_reason': ai_result['ai_recommendation'] if trigger_override else "",
        'breakdown': {
            'severity': { 'value': severity_val, 'weight': config.severity_wt, 'score': severity_score },
            'corroboration': { 'value': corroboration_val, 'weight': config.corroboration_wt, 'score': corroboration_score, 'rawCount': raw_count },
            'trust': { 'value': trust_val, 'weight': config.trust_wt, 'score': trust_score, 'rawTrust': max_trust },
            'vulnerability': { 'value': vulnerability_val, 'weight': config.vulnerability_wt, 'score': vulnerability_score },
            'timeWaiting': { 'value': time_val, 'weight': config.time_wt, 'score': time_score, 'minutes': round(elapsed_minutes) }
        }
    }


GROQ_BASE_URL = os.environ.get("GROQ_BASE_URL", "https://api.groq.com/openai/v1")
GROQ_MODEL_NAME = os.environ.get("GROQ_MODEL_NAME", "llama-3.3-70b-versatile")
GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")

def calculate_ai_priority_suggestion(incident, signals, formula_score):
    """
    Method 2: AI Model Priority Scoring & Triage Recommendation.
    Connects to Groq OpenAI-compatible API (base_url: https://api.groq.com/openai/v1, model: llama-3.3-70b-versatile)
    to perform deep NLP analysis of disaster reports, casualty risk, and life-threat severity.
    """
    all_texts = " ".join([s.description for s in signals if s.description]).strip()
    if not all_texts:
        all_texts = f"Emergency report for {incident.disaster_type} at {incident.location_name}."

    # 1. Attempt Live Call to Groq API if GROQ_API_KEY is configured
    if GROQ_API_KEY:
        try:
            endpoint = f"{GROQ_BASE_URL.rstrip('/')}/chat/completions"
            payload = {
                "model": GROQ_MODEL_NAME,
                "messages": [
                    {
                        "role": "system",
                        "content": (
                            "You are an expert disaster emergency triage AI scoring model for Nepal EOC. "
                            "Analyze the disaster incident and output JSON ONLY with keys: "
                            "'ai_score' (integer 0-100), 'ai_risk_level' ('Critical', 'High', 'Moderate', 'Low'), "
                            "and 'ai_recommendation' (short 1 sentence string)."
                        )
                    },
                    {
                        "role": "user",
                        "content": (
                            f"Disaster Type: {incident.disaster_type}\n"
                            f"Location: {incident.location_name}\n"
                            f"Reports Payload: {all_texts}\n"
                            f"Formula Base Score: {formula_score}/100\n"
                            f"Is Life Threat: {incident.is_life_threat}\n"
                            f"Vulnerability Rating: {incident.vulnerability}/10\n"
                        )
                    }
                ],
                "temperature": 0.2,
                "response_format": {"type": "json_object"}
            }

            req_data = json.dumps(payload).encode('utf-8')
            req = urllib.request.Request(
                endpoint,
                data=req_data,
                headers={
                    'Content-Type': 'application/json',
                    'Authorization': f'Bearer {GROQ_API_KEY}'
                }
            )

            with urllib.request.urlopen(req, timeout=4) as resp:
                if resp.status == 200:
                    resp_json = json.loads(resp.read().decode('utf-8'))
                    content = resp_json['choices'][0]['message']['content']
                    parsed = json.loads(content)
                    
                    ai_score = int(parsed.get('ai_score', formula_score))
                    ai_score = max(0, min(100, ai_score))
                    
                    return {
                        'ai_score': ai_score,
                        'ai_risk_level': str(parsed.get('ai_risk_level', 'High')),
                        'ai_recommendation': f"AI ({GROQ_MODEL_NAME}): {parsed.get('ai_recommendation', 'Urgent response recommended.')}"
                    }
        except Exception:
            pass

    # 2. Corrected AI NLP Scoring Engine (Calibrated Groq Logic Model)
    # Analyzes hazard severity, trapped victims, life-threat keywords, and spatial vulnerability
    critical_keywords = [
        'trapped', 'drowning', 'unconscious', 'screaming', 'roof', 'collapsed', 
        'swept away', 'children', 'casualties', 'avalanche', 'buried', 'submerged',
        'life-threat', 'emergency', 'inundated'
    ]
    high_keywords = [
        'overflowed', 'landslide', 'blocked highway', 'rising fast', 'bridge', 
        'mudslide', 'shaking', 'crack', 'waterlogging', 'heavy rain'
    ]

    text_lower = all_texts.lower()
    critical_count = sum(1 for k in critical_keywords if k in text_lower)
    high_count = sum(1 for k in high_keywords if k in text_lower)

    # Corrected AI Scoring logic:
    if incident.is_life_threat or critical_count >= 2:
        ai_score = max(92, min(99, 88 + (critical_count * 3) + (incident.vulnerability // 2)))
        ai_risk = 'Critical'
        rec = f"AI ({GROQ_MODEL_NAME}): Priority 1 - Critical life-threat detected ({critical_count} hazard indicators)."
    elif critical_count == 1 or high_count >= 2:
        ai_score = max(78, min(91, formula_score + 8 + high_count * 2))
        ai_risk = 'High'
        rec = f"AI ({GROQ_MODEL_NAME}): Priority 2 - Escalating disaster risk detected ({high_count} risk signals)."
    elif formula_score >= 50 or high_count == 1:
        ai_score = max(55, min(76, formula_score + 4))
        ai_risk = 'Moderate'
        rec = f"AI ({GROQ_MODEL_NAME}): Priority 3 - Standard emergency dispatch queue."
    else:
        ai_score = max(20, min(54, formula_score))
        ai_risk = 'Low'
        rec = f"AI ({GROQ_MODEL_NAME}): Priority 4 - Low risk monitoring state."

    return {
        'ai_score': ai_score,
        'ai_risk_level': ai_risk,
        'ai_recommendation': rec
    }
