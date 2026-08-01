# Mock Scenarios and Individual Test Signals for Django Seeding

PRESETS = {
    'prathamikta_default': {
        'name': "Prathamikta National Incident Triage",
        'description': "Default live dashboard scenario with 5 primary fused incidents and nationwide disaster monitoring nodes.",
        'signals': [
            # Incident 1: Bagmati River Flooding (Khokana, Lalitpur) - Rank 1, Score 98
            {
                'sourceType': 'sensor',
                'timestamp': '2025-05-10T14:22:00+05:45',
                'rawData': {
                    'sensorId': 'bagmati_gauge_01',
                    'sensorName': 'Bagmati River Gauge (Khokana)',
                    'hazardType': 'Flood',
                    'value': 7.8,
                    'unit': 'meters',
                    'threshold': 6.0,
                    'lat': 27.632,
                    'lng': 85.295,
                    'district': 'lalitpur',
                    'locationName': 'Khokana, Lalitpur'
                }
            },
            {
                'sourceType': 'call_center',
                'timestamp': '2025-05-10T14:25:00+05:45',
                'rawData': {
                    'callerName': "Ram Shrestha",
                    'callerContact': "9841234567",
                    'needType': 'Flood',
                    'lat': 27.632,
                    'lng': 85.295,
                    'district': 'lalitpur',
                    'locationName': 'Khokana, Lalitpur',
                    'operatorSeverity': 9,
                    'isLifeThreat': True,
                    'description': "Bagmati river overflowed into settlement. Trapped family on roof, life-threat drowning risk!"
                }
            },
            {
                'sourceType': 'call_center',
                'timestamp': '2025-05-10T14:28:00+05:45',
                'rawData': {
                    'callerName': "Sita Maharjan",
                    'callerContact': "9801987654",
                    'needType': 'Flood',
                    'lat': 27.633,
                    'lng': 85.296,
                    'district': 'lalitpur',
                    'locationName': 'Khokana, Lalitpur',
                    'operatorSeverity': 8,
                    'isLifeThreat': True,
                    'description': "Water level rising rapidly in lower Khokana near riverside."
                }
            },
            {
                'sourceType': 'social_media',
                'timestamp': '2025-05-10T14:31:00+05:45',
                'rawData': {
                    'username': 'lalitpur_alert',
                    'platform': 'X/Twitter',
                    'text': "Severe flooding at Khokana Bagmati bridge area! Houses inundated.",
                    'url': "https://x.com/lalitpur_alert/status/101"
                }
            },
            {
                'sourceType': 'social_media',
                'timestamp': '2025-05-10T14:33:00+05:45',
                'rawData': {
                    'username': 'nepal_flood_watch',
                    'platform': 'Facebook',
                    'text': "Bagmati river level crossing dangerous threshold in Khokana. Emergency rescue required.",
                    'url': "https://facebook.com/floodwatch"
                }
            },
            {
                'sourceType': 'news',
                'timestamp': '2025-05-10T14:35:00+05:45',
                'rawData': {
                    'sensorId': 'rss_onlinekhabar_khokana',
                    'sensorName': 'Onlinekhabar Emergency RSS',
                    'needType': 'Flood',
                    'lat': 27.632,
                    'lng': 85.295,
                    'district': 'lalitpur',
                    'locationName': 'Khokana, Lalitpur',
                    'operatorSeverity': 9,
                    'isLifeThreat': True,
                    'description': "Onlinekhabar RSS: Bagmati river overflows into Khokana settlements, trapped residents call for immediate rescue.",
                    'url': "https://english.onlinekhabar.com/bagmati-flood-khokana.html"
                }
            },

            # Incident 2: Building Collapsed (Thaiba, Kathmandu) - Rank 2, Score 94
            {
                'sourceType': 'call_center',
                'timestamp': '2025-05-10T14:27:00+05:45',
                'rawData': {
                    'callerName': "Kiran KC",
                    'callerContact': "9851122334",
                    'needType': 'Structural Collapse',
                    'lat': 27.625,
                    'lng': 85.342,
                    'district': 'kathmandu',
                    'locationName': 'Thaiba, Kathmandu',
                    'operatorSeverity': 9,
                    'isLifeThreat': True,
                    'description': "Old residential building structural collapse in Thaiba. 2 people trapped under debris!"
                }
            },
            {
                'sourceType': 'call_center',
                'timestamp': '2025-05-10T14:28:00+05:45',
                'rawData': {
                    'callerName': "Bikash Thapa",
                    'callerContact': "9841887766",
                    'needType': 'Structural Collapse',
                    'lat': 27.626,
                    'lng': 85.343,
                    'district': 'kathmandu',
                    'locationName': 'Thaiba, Kathmandu',
                    'operatorSeverity': 8,
                    'isLifeThreat': True,
                    'description': "Dust and debris blocking lane after house wall collapsed."
                }
            },
            {
                'sourceType': 'social_media',
                'timestamp': '2025-05-10T14:30:00+05:45',
                'rawData': {
                    'username': 'ktm_today',
                    'platform': 'X/Twitter',
                    'text': "House collapsed at Thaiba. Ambulance and police needed.",
                    'url': "https://x.com/ktm_today/status/202"
                }
            },
            {
                'sourceType': 'social_media',
                'timestamp': '2025-05-10T14:32:00+05:45',
                'rawData': {
                    'username': 'rescue_ktm',
                    'platform': 'X/Twitter',
                    'text': "Locals pulling trapped victims from collapsed building in Thaiba.",
                    'url': "https://x.com/rescue_ktm/status/203"
                }
            },

            # Incident 3: Landslide Reported (Sisneri, Sindhupalchok) - Rank 3, Score 87
            {
                'sourceType': 'sensor',
                'timestamp': '2025-05-10T14:20:00+05:45',
                'rawData': {
                    'sensorId': 'landslide_sens_03',
                    'sensorName': 'Sisneri Slope Inclinometer',
                    'hazardType': 'Landslide',
                    'value': 14.5,
                    'unit': 'mm/hr',
                    'threshold': 10.0,
                    'lat': 27.791,
                    'lng': 85.850,
                    'district': 'sindhupalchok',
                    'locationName': 'Sisneri, Sindhupalchok'
                }
            },
            {
                'sourceType': 'call_center',
                'timestamp': '2025-05-10T14:23:00+05:45',
                'rawData': {
                    'callerName': "Nabin Giri",
                    'callerContact': "9812345678",
                    'needType': 'Landslide',
                    'lat': 27.791,
                    'lng': 85.850,
                    'district': 'sindhupalchok',
                    'locationName': 'Sisneri, Sindhupalchok',
                    'operatorSeverity': 7,
                    'isLifeThreat': False,
                    'description': "Major mudslide blocking highway at Sisneri. Vehicles queueing."
                }
            },
            {
                'sourceType': 'social_media',
                'timestamp': '2025-05-10T14:26:00+05:45',
                'rawData': {
                    'username': 'sindhu_highway',
                    'platform': 'Facebook',
                    'text': "Highway completely blocked by massive landslide in Sisneri.",
                    'url': "https://facebook.com/sindhuhighway"
                }
            },

            # Incident 4: Heavy Rainfall Alert (Pokhara, Kaski) - Rank 4, Score 74
            {
                'sourceType': 'sensor',
                'timestamp': '2025-05-10T14:15:00+05:45',
                'rawData': {
                    'sensorId': 'rain_kaski_01',
                    'sensorName': 'Pokhara Airport Weather Gauge',
                    'hazardType': 'Heavy Rainfall',
                    'value': 95.0,
                    'unit': 'mm/3hr',
                    'threshold': 60.0,
                    'lat': 28.209,
                    'lng': 83.985,
                    'district': 'kaski',
                    'locationName': 'Pokhara, Kaski'
                }
            },
            {
                'sourceType': 'call_center',
                'timestamp': '2025-05-10T14:18:00+05:45',
                'rawData': {
                    'callerName': "Sunil Gurung",
                    'callerContact': "9806112233",
                    'needType': 'Heavy Rainfall',
                    'lat': 28.209,
                    'lng': 83.985,
                    'district': 'kaski',
                    'locationName': 'Pokhara, Kaski',
                    'operatorSeverity': 6,
                    'isLifeThreat': False,
                    'description': "Torrential rain causing waterlogging on main roads in Pokhara Lakeside."
                }
            },

            # Incident 5: Minor Flooding (Bharatpur, Chitwan) - Rank 5, Score 61
            {
                'sourceType': 'call_center',
                'timestamp': '2025-05-10T14:10:00+05:45',
                'rawData': {
                    'callerName': "Pooja Chaudhary",
                    'callerContact': "9856098765",
                    'needType': 'Flood',
                    'lat': 27.678,
                    'lng': 84.432,
                    'district': 'chitwan',
                    'locationName': 'Bharatpur, Chitwan',
                    'operatorSeverity': 5,
                    'isLifeThreat': False,
                    'description': "Minor drainage overflow in Ward 4, Bharatpur."
                }
            },
            {
                'sourceType': 'social_media',
                'timestamp': '2025-05-10T14:12:00+05:45',
                'rawData': {
                    'username': 'chitwan_live',
                    'platform': 'Facebook',
                    'text': "Street waterlogging in Bharatpur after continuous rain.",
                    'url': "https://facebook.com/chitwanlive"
                }
            }
        ]
    },
    'melamchi_flood': {
        'name': "2024 Melamchi River Flood",
        'description': "Simulation of upstream cloudburst triggering river gauge alarms, local emergency calls, and social media panic in Sindhupalchok district.",
        'signals': [
            {
                'sourceType': 'sensor',
                'timestamp': '2026-07-31T09:00:00+05:45',
                'rawData': {
                    'sensorId': 'station_bhotekoshi_1',
                    'sensorName': 'Bhotekoshi River Gauge (Barhabise)',
                    'hazardType': 'Flood',
                    'value': 6.2,
                    'unit': 'meters',
                    'threshold': 6.0,
                    'lat': 27.785,
                    'lng': 85.901,
                    'district': 'sindhupalchok',
                    'locationName': 'Barhabise, Sindhupalchok'
                }
            },
            {
                'sourceType': 'social_media',
                'timestamp': '2026-07-31T09:12:00+05:45',
                'rawData': {
                    'username': 'sindhu_updates',
                    'platform': 'X/Twitter',
                    'text': "Heavy rainfall in Helambu area. The Bhotekoshi river is rising extremely fast! Melamchi Bazar is on high alert. Hope everyone stays safe.",
                    'url': "https://x.com/sindhu_updates/status/188391283"
                }
            },
            {
                'sourceType': 'call_center',
                'timestamp': '2026-07-31T09:20:00+05:45',
                'rawData': {
                    'callerName': "Ramesh Shrestha",
                    'callerContact': "9841XXXXXX",
                    'needType': 'Flood',
                    'lat': 27.832,
                    'lng': 85.584,
                    'district': 'sindhupalchok',
                    'locationName': 'Melamchi Bazar, Sindhupalchok',
                    'operatorSeverity': 7,
                    'isLifeThreat': False,
                    'description': "Water has entered the lower ground level of shops near the bridge. Police are asking people to evacuate. Need security personnel for crowd control."
                }
            },
            {
                'sourceType': 'social_media',
                'timestamp': '2026-07-31T09:35:00+05:45',
                'rawData': {
                    'username': 'helambu_nature',
                    'platform': 'Facebook',
                    'text': "HELP! Flash flood swept away the suspension bridge in Helambu. Two children are trapped on the other side of the riverbank, water level is rising. They are screaming! Drowning danger!",
                    'url': "https://facebook.com/groups/helambu/posts/91283"
                }
            },
            {
                'sourceType': 'call_center',
                'timestamp': '2026-07-31T09:42:00+05:45',
                'rawData': {
                    'callerName': "Maya Tamang",
                    'callerContact': "9808XXXXXX",
                    'needType': 'Flood',
                    'lat': 27.971,
                    'lng': 85.532,
                    'district': 'sindhupalchok',
                    'locationName': 'Helambu Village, Sindhupalchok',
                    'operatorSeverity': 9,
                    'isLifeThreat': True,
                    'description': "Water has surrounded our house. We are on the roof, 3 of us including an elderly woman. We cannot cross the path, it is washed out. Drowning risk."
                }
            }
        ]
    },
    'jajarkot_earthquake': {
        'name': "2023 Jajarkot Earthquake",
        'description': "Simulation of a midnight seismic event with magnitude 6.4, triggering immediate sensor alarms, urgent calls regarding collapsed houses, and social media activity in Jajarkot and Rukum West.",
        'signals': [
            {
                'sourceType': 'sensor',
                'timestamp': '2026-07-31T23:47:00+05:45',
                'rawData': {
                    'sensorId': 'station_jajarkot_seismic',
                    'sensorName': 'Jajarkot Seismic Sensor',
                    'hazardType': 'Earthquake',
                    'value': 6.4,
                    'unit': 'Richter Scale',
                    'threshold': 5.0,
                    'lat': 28.905,
                    'lng': 82.205,
                    'district': 'jajarkot',
                    'locationName': 'Ramidanda, Jajarkot'
                }
            },
            {
                'sourceType': 'social_media',
                'timestamp': '2026-07-31T23:51:00+05:45',
                'rawData': {
                    'username': 'nepal_quakes',
                    'platform': 'X/Twitter',
                    'text': "Huge tremor felt in Surkhet and Jajarkot! Ground was shaking for almost 20 seconds. Power went out immediately. #earthquake #nepal",
                    'url': "https://x.com/nepal_quakes/status/72384"
                }
            },
            {
                'sourceType': 'call_center',
                'timestamp': '2026-07-31T23:55:00+05:45',
                'rawData': {
                    'callerName': "Hari Bahadur KC",
                    'callerContact': "9860XXXXXX",
                    'needType': 'Earthquake',
                    'lat': 28.902,
                    'lng': 82.201,
                    'district': 'jajarkot',
                    'locationName': 'Khalanga Bazar, Jajarkot',
                    'operatorSeverity': 9,
                    'isLifeThreat': True,
                    'description': "Multiple mud houses have collapsed in our ward. We hear people screaming from under the rubble. We need police and search & rescue right now. Some people are unconscious."
                }
            },
            {
                'sourceType': 'call_center',
                'timestamp': '2026-07-31T23:58:00+05:45',
                'rawData': {
                    'callerName': "Deepak Sharma",
                    'callerContact': "9848XXXXXX",
                    'needType': 'Earthquake',
                    'lat': 28.874,
                    'lng': 82.352,
                    'district': 'rukumwest',
                    'locationName': 'Athbiskot, Rukum West',
                    'operatorSeverity': 8,
                    'isLifeThreat': False,
                    'description': "Our local hospital building has suffered heavy cracks. We are moving patients outside. Need tents and medical supplies. Roads are blocked by small landslides."
                }
            },
            {
                'sourceType': 'social_media',
                'timestamp': '2026-08-01T00:05:00+05:45',
                'rawData': {
                    'username': 'karnali_news',
                    'platform': 'Web Portal',
                    'text': "Reports coming in from Jajarkot: Devastating damage in Ramidanda epicenter. Local school collapsed. At least 10 people trapped under rubble, residents digging with bare hands. Urgent need of heavy machinery.",
                    'url': "https://karnalinews.com/local/quake-damage"
                }
            }
        ]
    }
}
