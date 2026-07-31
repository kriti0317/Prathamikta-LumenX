from django.test import TestCase
from django.utils import timezone
from datetime import timedelta

from core.models import Incident, Signal, AuditLog, SystemConfig
from core.nlp_extractor import extract_from_text
from core.fusion_engine import (
    normalize_signal_data, should_fuse, fuse_signal_to_incident, 
    create_new_incident_from_signal
)
from core.priority_scorer import calculate_priority

class NDIFTSEngineTests(TestCase):

    def setUp(self):
        # Create standard system config
        self.config = SystemConfig.objects.create(
            id=1,
            severity_wt=3,
            corroboration_wt=2,
            trust_wt=2,
            vulnerability_wt=1,
            time_wt=1,
            distance_threshold_km=15.0,
            time_threshold_hours=24.0
        )

    def test_nlp_extractor(self):
        """
        Verify keyword classifications, life-threat overrides, and district geocoding.
        """
        text = "HELP! Multiple buildings collapsed in Khalanga, Jajarkot after a massive earthquake. People are trapped under rubble!"
        result = extract_from_text(text)

        self.assertEqual(result['disaster_type'], 'Earthquake')
        self.assertTrue(result['is_life_threat'])
        self.assertEqual(result['urgency'], 'high')
        self.assertIsNotNone(result['location'])
        self.assertEqual(result['location']['district'], 'jajarkot')
        self.assertEqual(result['location']['name'], 'Khalanga, Jajarkot')
        self.assertAlmostEqual(result['location']['lat'], 28.90, places=1)
        self.assertAlmostEqual(result['location']['lng'], 82.20, places=1)

    def test_record_linkage_and_fusion(self):
        """
        Verify that nearby similar hazards fuse, while distant hazards remain separate.
        """
        now = timezone.now()

        # Ingest call log in Melamchi
        sig1_data = normalize_signal_data({
            'needType': 'Flood',
            'description': 'Flooding in Melamchi Bazar, water rising',
            'lat': '27.83',
            'lng': '85.58',
            'district': 'sindhupalchok',
            'locationName': 'Melamchi Bazar',
            'operatorSeverity': 6,
            'isLifeThreat': False
        }, 'call_center')
        
        sig1 = Signal.objects.create(**sig1_data)
        inc1 = create_new_incident_from_signal(sig1)

        # Ingest social media post in Melamchi 30 mins later
        sig2_data = normalize_signal_data({
            'text': 'Flood near Melamchi bridge is getting worse!'
        }, 'social_media', (now + timedelta(minutes=30)).isoformat())
        
        sig2 = Signal.objects.create(**sig2_data)

        # Ingest sensor alarm in Kathmandu (approx 60km away)
        sig3_data = normalize_signal_data({
            'sensorId': 'station_kathmandu_rain',
            'sensorName': 'Kathmandu Rain Gauge',
            'hazardType': 'Flood',
            'value': 120,
            'threshold': 80,
            'lat': '27.698',
            'lng': '85.358',
            'district': 'kathmandu',
            'locationName': 'Kathmandu Airport'
        }, 'sensor')
        sig3 = Signal.objects.create(**sig3_data)

        # Proximity Check 1: Tweet in Melamchi should fuse with Incident 1
        self.assertTrue(should_fuse(sig2, inc1, self.config))
        fuse_signal_to_incident(sig2, inc1)
        
        # Proximity Check 2: Kathmandu Sensor should NOT fuse with Incident 1
        self.assertFalse(should_fuse(sig3, inc1, self.config))

        self.assertEqual(inc1.signals.count(), 2)
        self.assertAlmostEqual(inc1.lat, 27.83, places=2)

    def test_priority_triage_scoring_and_overrides(self):
        """
        Verify base priority scoring calculation and the +1000 override boost.
        """
        now = timezone.now()

        # Create normal flood incident
        sig_normal = Signal.objects.create(
            source_type='call_center',
            timestamp=now,
            description='Minor flooding on road',
            lat=27.7,
            lng=85.3,
            district='kathmandu',
            location_name='Kathmandu',
            severity=4,
            is_life_threat=False
        )
        inc_normal = create_new_incident_from_signal(sig_normal)
        score_normal = calculate_priority(inc_normal, self.config, now)

        # Expected score:
        # severity: 4 * 3 = 12
        # corroboration: 1 report = 1 * 2 = 2
        # trust: max_trust 1.0 (call center) * 10 = 10 * 2 = 20
        # vulnerability: Kathmandu (8) * 1 = 8
        # time waiting: 0 mins = 0 * 1 = 0
        # normalized score: min(100, round((42 / 90.0) * 100)) = 47
        self.assertEqual(score_normal['final_score'], 47)
        self.assertFalse(score_normal['is_overridden'])

        # Create critical earthquake incident (with life threat)
        sig_critical = Signal.objects.create(
            source_type='call_center',
            timestamp=now,
            description='People trapped under collapsed walls',
            lat=28.9,
            lng=82.2,
            district='jajarkot',
            location_name='Khalanga',
            severity=9,
            is_life_threat=True
        )
        inc_critical = create_new_incident_from_signal(sig_critical)
        score_critical = calculate_priority(inc_critical, self.config, now)

        # Expected score: base score + 1000 override boost
        # severity: 9 * 3 = 27
        # corroboration: 1 report = 1 * 2 = 2
        # trust: max_trust 1.0 (call center) * 10 = 10 * 2 = 20
        # vulnerability: Jajarkot (9) * 1 = 9
        # time waiting: 0 mins = 0 * 1 = 0
        # base: 27 + 2 + 20 + 9 + 0 = 58
        # final score: 0-100 scale triage score with override boost = 96
        self.assertEqual(score_critical['final_score'], 96)
        self.assertTrue(score_critical['is_overridden'])
