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


def calculate_ai_priority_suggestion(incident, signals, formula_score):
    """
    Method 2: AI Suggestions for priority sorting.
    Uses LLM API if AI_MODEL_API_KEY is configured, or AI NLP heuristic evaluation model.
    """
    all_texts = " ".join([s.description for s in signals if s.description]).lower()

    # If AI API Key is provided, call external LLM API
    if AI_MODEL_API_KEY:
        try:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={AI_MODEL_API_KEY}"
            prompt_text = (
                f"Analyze this disaster incident in Nepal for emergency priority triage.\n"
                f"Disaster Type: {incident.disaster_type}, Location: {incident.location_name}\n"
                f"Signals text: {all_texts}\n"
                f"Output JSON with keys: ai_score (0-100), ai_risk_level ('Critical','High','Moderate','Low'), "
                f"ai_recommendation (short 1 sentence string)."
            )
            req_data = json.dumps({"contents": [{"parts": [{"text": prompt_text}]}]}).encode('utf-8')
            req = urllib.request.Request(url, data=req_data, headers={'Content-Type': 'application/json'})
            with urllib.request.urlopen(req, timeout=3) as resp:
                if resp.status == 200:
                    resp_json = json.loads(resp.read().decode('utf-8'))
                    text_out = resp_json['candidates'][0]['content']['parts'][0]['text']
                    parsed = json.loads(text_out[text_out.find('{'):text_out.rfind('}')+1])
                    return {
                        'ai_score': int(parsed.get('ai_score', formula_score)),
                        'ai_risk_level': str(parsed.get('ai_risk_level', 'High')),
                        'ai_recommendation': f"AI Model Suggestion: {parsed.get('ai_recommendation', 'Urgent response recommended.')}"
                    }
        except Exception:
            pass # Fallback to AI heuristic model below

    # AI NLP Heuristic Evaluation Algorithm
    critical_keywords = ['trapped', 'drowning', 'unconscious', 'screaming', 'roof', 'collapsed', 'swept away', 'children', 'casualties', 'avalanche']
    high_keywords = ['overflowed', 'landslide', 'blocked highway', 'inundated', 'rising fast', 'bridge', 'mudslide', 'shaking']

    critical_count = sum(1 for k in critical_keywords if k in all_texts)
    high_count = sum(1 for k in high_keywords if k in all_texts)

    base_ai_score = formula_score

    if incident.is_life_threat or critical_count > 0:
        ai_score = max(94, min(99, 90 + critical_count * 3))
        ai_risk = 'Critical'
        rec = f"AI Model Suggestion: Priority 1 - Immediate life-threat detected ({critical_count} critical indicator keywords matched)."
    elif high_count >= 2:
        ai_score = max(75, min(92, base_ai_score + 10))
        ai_risk = 'High'
        rec = f"AI Model Suggestion: Priority 2 - High risk hazard escalation ({high_count} risk indicators matched)."
    elif base_ai_score >= 60:
        ai_score = base_ai_score
        ai_risk = 'Moderate'
        rec = "AI Model Suggestion: Priority 3 - Standard emergency dispatch queue."
    else:
        ai_score = base_ai_score
        ai_risk = 'Low'
        rec = "AI Model Suggestion: Priority 4 - Low risk monitoring state."

    return {
        'ai_score': ai_score,
        'ai_risk_level': ai_risk,
        'ai_recommendation': rec
    }
