import re
from core.nepal_geo_data import DISTRICTS, MUNICIPALITIES

DISASTER_KEYWORDS = {
    'Flood': [
        "flood", "inundation", "river overflow", "swept away", "drowning", "heavy rainfall", "rising water", "submerged",
        "rainfall", "rain", "torrential", "monsoon", "deluge", "waterlogging",
        "बाढी", "डुबान", "बगायो", "बगाएको", "सतह बढ्यो"
    ],
    'Landslide': [
        "landslide", "mudslide", "rockfall", "debris flow", "highway blocked", "buried under mud", "slope failure",
        "road blocked", "debris", "cave-in",
        "पहिरो", "पहिरोले", "पहिरो खस्यो", "सडक अवरुद्ध", "पुरियो", "पुरिएको"
    ],
    'Earthquake': [
        "earthquake", "seismic", "tremor", "quake", "shaking", "rubble", "aftershock", "building collapse",
        "epicenter", "magnitude",
        "भूकम्प", "कम्पन्न", "भूकम्पको धक्का", "घर भत्कियो", "भत्किएको"
    ],
    'Fire': [
        "wildfire", "blaze", "smoke", "forest fire", "inferno", "building fire", "structural fire",
        "आगलागी", "डढेलो", "आगो", "सल्कियो", "जल्यो"
    ],
    'Avalanche': [
        "avalanche", "snowslide", "blizzard", "expedition", "mountaineer", "peak", "broad peak", "snowstorm", "high altitude",
        "हिउँपहिरो", "हिउँ"
    ],
    'Storm': [
        "storm", "lightning", "thunderstorm", "cloudburst", "hailstorm", "gale", "cyclone", "tempest", "windstorm",
        "हावाहुरी", "चट्याङ"
    ],
    'Emergency': [
        "structural collapse", "building collapse", "bridge collapse", "dam breach", "explosion", "industrial accident",
        "disaster rescue", "mass casualty", "trapped under rubble", "hazard emergency"
    ]
}

LIFE_THREAT_KEYWORDS = [
    "trapped", "unconscious", "collapsed", "not breathing", "drowning", "buried", "under rubble", "casualties",
    "casualty", "severe injuries", "critical condition", "missing", "swept away", "avalanche", "drone attack",
    "killed", "dead", "fatalities", "victim", "shot", "death", "shooting", "clashes", "torched",
    "पुरिएको", "अचेत", "सम्पर्कविहीन", "सास फेर्न", "बगायो", "चेत नभएको", "पुरिएका", "च्यापिएको", "गुहार", "मर्न लाग्यो"
]

URGENCY_KEYWORDS = [
    "emergency", "urgent", "immediate", "help", "save us", "rescue", "critical", "severe", "worst hit", "fatal",
    "curfew", "protest", "clash", "warning", "alert",
    "अति आवश्यक", "उद्धार", "गुहार", "तुरन्त", "खतरा", "आकस्मिक"
]

def extract_from_text(text):
    """
    Parses unstructured text to extract structured information.
    """
    if not text:
        return {
            'disaster_type': 'General',
            'is_life_threat': False,
            'urgency': 'low',
            'location': None,
            'severity': 3
        }

    clean_text = text.lower()

    # 1. Classify Disaster Type
    disaster_type = 'General'
    max_matches = 0

    for dtype, keywords in DISASTER_KEYWORDS.items():
        match_count = sum(1 for kw in keywords if kw.lower() in clean_text)
        if match_count > max_matches:
            max_matches = match_count
            disaster_type = dtype

    # 2. Detect Life-Threat Language
    is_life_threat = any(kw.lower() in clean_text for kw in LIFE_THREAT_KEYWORDS)

    # 3. Detect Urgency
    urgency_matches = sum(1 for kw in URGENCY_KEYWORDS if kw.lower() in clean_text)
    
    if is_life_threat or urgency_matches >= 2:
        urgency = 'high'
    elif urgency_matches == 1 or max_matches > 0:
        urgency = 'medium'
    else:
        urgency = 'low'

    # 4. Estimate Severity (1-10 Scale)
    severity = 3
    if is_life_threat:
        severity = 9
    elif urgency == 'high':
        severity = 7
    elif urgency == 'medium':
        severity = 5

    # Incremental adjustments
    if any(kw in clean_text for kw in ["destroyed", "भत्कियो", "complete loss", "fatal", "killed"]):
        severity = min(10, severity + 1)

    # 5. Geocode Location matching
    matched_location = None

    # Search in municipalities first (finer resolution)
    for mun in MUNICIPALITIES:
        if mun['name'].lower() in clean_text or (mun.get('nameNep') and mun['nameNep'] in text):
            matched_location = {
                'name': f"{mun['name']}, {mun['district'].capitalize()}",
                'lat': mun['lat'],
                'lng': mun['lng'],
                'district': mun['district'],
                'type': 'municipality',
                'pop': mun['pop']
            }
            break

    # Search in districts if no municipality was matched
    if not matched_location:
        for dist in DISTRICTS:
            if dist['name'].lower() in clean_text or (dist.get('nameNep') and dist['nameNep'] in text):
                matched_location = {
                    'name': f"{dist['name']} District",
                    'lat': dist['lat'],
                    'lng': dist['lng'],
                    'district': dist['id'],
                    'type': 'district',
                    'pop': dist['population']
                }
                break

    return {
        'disaster_type': disaster_type,
        'is_life_threat': is_life_threat,
        'urgency': urgency,
        'location': matched_location,
        'severity': severity
    }
