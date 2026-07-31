# Nepal Administrative & Geographic Reference Database in Python

PROVINCES = {
    1: "Koshi",
    2: "Madhesh",
    3: "Bagmati",
    4: "Gandaki",
    5: "Lumbini",
    6: "Karnali",
    7: "Sudurpashchim"
}

DISTRICTS = [
    # Province 1: Koshi
    { "id": "taplejung", "name": "Taplejung", "nameNep": "ताप्लेजुङ", "province": 1, "lat": 27.35, "lng": 87.67, "population": 120590, "vulnerability": 7, "riskType": "Landslide/Snow" },
    { "id": "panchthar", "name": "Panchthar", "nameNep": "पाँचथर", "province": 1, "lat": 27.20, "lng": 87.85, "population": 174000, "vulnerability": 5, "riskType": "Landslide" },
    { "id": "ilam", "name": "Ilam", "nameNep": "इलाम", "province": 1, "lat": 26.91, "lng": 87.92, "population": 280000, "vulnerability": 4, "riskType": "Landslide" },
    { "id": "jhapa", "name": "Jhapa", "nameNep": "झापा", "province": 1, "lat": 26.63, "lng": 87.90, "population": 994090, "vulnerability": 6, "riskType": "Flood" },
    { "id": "morang", "name": "Morang", "nameNep": "मोरङ", "province": 1, "lat": 26.65, "lng": 87.35, "population": 1147186, "vulnerability": 7, "riskType": "Flood" },
    { "id": "sunsari", "name": "Sunsari", "nameNep": "सुनसरी", "province": 1, "lat": 26.60, "lng": 87.15, "population": 926962, "vulnerability": 7, "riskType": "Flood" },
    { "id": "dhankuta", "name": "Dhankuta", "nameNep": "धनकुटा", "province": 1, "lat": 26.98, "lng": 87.33, "population": 150000, "vulnerability": 4, "riskType": "Landslide" },
    { "id": "terhathum", "name": "Terhathum", "nameNep": "तेह्रथुम", "province": 1, "lat": 27.12, "lng": 87.55, "population": 89000, "vulnerability": 4, "riskType": "Landslide" },
    { "id": "sankhuwasabha", "name": "Sankhuwasabha", "nameNep": "संखुवासभा", "province": 1, "lat": 27.60, "lng": 87.30, "population": 159000, "vulnerability": 7, "riskType": "Landslide/Snow" },
    { "id": "bhojpur", "name": "Bhojpur", "nameNep": "भोजपुर", "province": 1, "lat": 27.17, "lng": 87.05, "population": 158000, "vulnerability": 5, "riskType": "Landslide" },
    { "id": "solukhumbu", "name": "Solukhumbu", "nameNep": "सोलुखुम्बु", "province": 1, "lat": 27.75, "lng": 86.73, "population": 104000, "vulnerability": 8, "riskType": "Glacier/Avalanche" },
    { "id": "okhaldhunga", "name": "Okhaldhunga", "nameNep": "ओखलढुङ्गा", "province": 1, "lat": 27.30, "lng": 86.50, "population": 140000, "vulnerability": 5, "riskType": "Landslide" },
    { "id": "khotang", "name": "Khotang", "nameNep": "खोटाङ", "province": 1, "lat": 27.20, "lng": 86.80, "population": 175000, "vulnerability": 5, "riskType": "Landslide" },
    { "id": "udayapur", "name": "Udayapur", "nameNep": "उदयपुर", "province": 1, "lat": 26.90, "lng": 86.50, "population": 340000, "vulnerability": 5, "riskType": "Flood/Landslide" },

    # Province 2: Madhesh
    { "id": "saptari", "name": "Saptari", "nameNep": "सप्तरी", "province": 2, "lat": 26.55, "lng": 86.75, "population": 706255, "vulnerability": 8, "riskType": "Flood/Heat" },
    { "id": "siraha", "name": "Siraha", "nameNep": "सिराहा", "province": 2, "lat": 26.65, "lng": 86.20, "population": 739953, "vulnerability": 7, "riskType": "Flood" },
    { "id": "dhanusha", "name": "Dhanusha", "nameNep": "धनुषा", "province": 2, "lat": 26.75, "lng": 86.00, "population": 867747, "vulnerability": 6, "riskType": "Flood/ColdWave" },
    { "id": "mahottari", "name": "Mahottari", "nameNep": "महोत्तरी", "province": 2, "lat": 26.85, "lng": 85.80, "population": 706994, "vulnerability": 7, "riskType": "Flood" },
    { "id": "sarlahi", "name": "Sarlahi", "nameNep": "सर्लाही", "province": 2, "lat": 26.95, "lng": 85.60, "population": 858512, "vulnerability": 7, "riskType": "Flood" },
    { "id": "bara", "name": "Bara", "nameNep": "बारा", "province": 2, "lat": 27.05, "lng": 85.00, "population": 763137, "vulnerability": 6, "riskType": "Windstorm/Flood" },
    { "id": "parsa", "name": "Parsa", "nameNep": "पर्सा", "province": 2, "lat": 27.15, "lng": 84.85, "population": 654471, "vulnerability": 5, "riskType": "Flood" },
    { "id": "rautahat", "name": "Rautahat", "nameNep": "रौतहट", "province": 2, "lat": 26.90, "lng": 85.30, "population": 813573, "vulnerability": 8, "riskType": "Flood" },

    # Province 3: Bagmati
    { "id": "sindhupalchok", "name": "Sindhupalchok", "nameNep": "सिन्धुपाल्चोक", "province": 3, "lat": 27.85, "lng": 85.75, "population": 262610, "vulnerability": 9, "riskType": "Landslide/Flood" },
    { "id": "rasuwa", "name": "Rasuwa", "nameNep": "रसुवा", "province": 3, "lat": 28.15, "lng": 85.35, "population": 46689, "vulnerability": 8, "riskType": "Landslide/Cold" },
    { "id": "dhading", "name": "Dhading", "nameNep": "धादिङ", "province": 3, "lat": 27.85, "lng": 84.90, "population": 325220, "vulnerability": 6, "riskType": "Landslide/Earthquake" },
    { "id": "nuwakot", "name": "Nuwakot", "nameNep": "नुवाकोट", "province": 3, "lat": 27.90, "lng": 85.25, "population": 263000, "vulnerability": 6, "riskType": "Landslide" },
    { "id": "kathmandu", "name": "Kathmandu", "nameNep": "काठमाडौँ", "province": 3, "lat": 27.70, "lng": 85.32, "population": 2041587, "vulnerability": 8, "riskType": "Earthquake/Inundation" },
    { "id": "bhaktapur", "name": "Bhaktapur", "nameNep": "भक्तपुर", "province": 3, "lat": 27.67, "lng": 85.43, "population": 432952, "vulnerability": 6, "riskType": "Earthquake/Inundation" },
    { "id": "lalitpur", "name": "Lalitpur", "nameNep": "ललितपुर", "province": 3, "lat": 27.60, "lng": 85.33, "population": 551667, "vulnerability": 6, "riskType": "Earthquake/Landslide" },
    { "id": "kavrepalanchok", "name": "Kavrepalanchok", "nameNep": "काभ्रेपलाञ्चोक", "province": 3, "lat": 27.60, "lng": 85.55, "population": 364039, "vulnerability": 6, "riskType": "Landslide" },
    { "id": "ramechhap", "name": "Ramechhap", "nameNep": "रामेछाप", "province": 3, "lat": 27.40, "lng": 86.05, "population": 170000, "vulnerability": 5, "riskType": "Landslide/Drought" },
    { "id": "dolakha", "name": "Dolakha", "nameNep": "दोलखा", "province": 3, "lat": 27.75, "lng": 86.15, "population": 172725, "vulnerability": 7, "riskType": "Landslide/Earthquake" },
    { "id": "sindhuli", "name": "Sindhuli", "nameNep": "सिन्धुली", "province": 3, "lat": 27.15, "lng": 85.90, "population": 300000, "vulnerability": 5, "riskType": "Landslide" },
    { "id": "makwanpur", "name": "Makwanpur", "nameNep": "मकवानपुर", "province": 3, "lat": 27.45, "lng": 85.05, "population": 466073, "vulnerability": 5, "riskType": "Landslide/Flood" },
    { "id": "chitwan", "name": "Chitwan", "nameNep": "चितवन", "province": 3, "lat": 27.53, "lng": 84.45, "population": 719859, "vulnerability": 6, "riskType": "Flood/Wildfire" },

    # Province 4: Gandaki
    { "id": "gorkha", "name": "Gorkha", "nameNep": "गोरखा", "province": 4, "lat": 28.25, "lng": 84.70, "population": 251000, "vulnerability": 7, "riskType": "Earthquake/Landslide" },
    { "id": "manang", "name": "Manang", "nameNep": "मनाङ", "province": 4, "lat": 28.65, "lng": 84.15, "population": 5650, "vulnerability": 8, "riskType": "FlashFlood/Snow" },
    { "id": "mustang", "name": "Mustang", "nameNep": "मुस्ताङ", "province": 4, "lat": 28.80, "lng": 83.85, "population": 14496, "vulnerability": 8, "riskType": "FlashFlood/Cold" },
    { "id": "myagdi", "name": "Myagdi", "nameNep": "म्याग्दी", "province": 4, "lat": 28.45, "lng": 83.50, "population": 107000, "vulnerability": 7, "riskType": "Landslide/Flood" },
    { "id": "kaski", "name": "Kaski", "nameNep": "कास्की", "province": 4, "lat": 28.25, "lng": 83.98, "population": 600631, "vulnerability": 6, "riskType": "Landslide/HeavyRain" },
    { "id": "lamjung", "name": "Lamjung", "nameNep": "लमजुङ", "province": 4, "lat": 28.20, "lng": 84.38, "population": 153000, "vulnerability": 6, "riskType": "Landslide" },
    { "id": "tanahu", "name": "Tanahu", "nameNep": "तनहुँ", "province": 4, "lat": 27.95, "lng": 84.25, "population": 312000, "vulnerability": 4, "riskType": "Landslide" },
    { "id": "nawalpur", "name": "Nawalpur", "nameNep": "नवलपुर", "province": 4, "lat": 27.65, "lng": 84.10, "population": 378000, "vulnerability": 5, "riskType": "Flood" },
    { "id": "syangja", "name": "Syangja", "nameNep": "स्याङ्जा", "province": 4, "lat": 28.10, "lng": 83.85, "population": 253000, "vulnerability": 5, "riskType": "Landslide" },
    { "id": "parbat", "name": "Parbat", "nameNep": "पर्वत", "province": 4, "lat": 28.20, "lng": 83.70, "population": 120000, "vulnerability": 5, "riskType": "Landslide" },
    { "id": "baglung", "name": "Baglung", "nameNep": "बागलुङ", "province": 4, "lat": 28.25, "lng": 83.40, "population": 250000, "vulnerability": 6, "riskType": "Landslide" },

    # Province 5: Lumbini
    { "id": "rukumeast", "name": "Rukum East", "nameNep": "पूर्वी रुकुम", "province": 5, "lat": 28.62, "lng": 82.85, "population": 53000, "vulnerability": 6, "riskType": "Landslide" },
    { "id": "rolpa", "name": "Rolpa", "nameNep": "रोल्पा", "province": 5, "lat": 28.30, "lng": 82.60, "population": 224000, "vulnerability": 6, "riskType": "Landslide" },
    { "id": "pyuthan", "name": "Pyuthan", "nameNep": "प्युठान", "province": 5, "lat": 28.10, "lng": 82.90, "population": 228000, "vulnerability": 5, "riskType": "Landslide" },
    { "id": "gulmi", "name": "Gulmi", "nameNep": "गुल्मी", "province": 5, "lat": 28.05, "lng": 83.25, "population": 246000, "vulnerability": 5, "riskType": "Landslide" },
    { "id": "arghakhanchi", "name": "Arghakhanchi", "nameNep": "अर्घाखाँची", "province": 5, "lat": 27.90, "lng": 83.15, "population": 177000, "vulnerability": 4, "riskType": "Landslide" },
    { "id": "palpa", "name": "Palpa", "nameNep": "पाल्पा", "province": 5, "lat": 27.85, "lng": 83.55, "population": 245000, "vulnerability": 5, "riskType": "Landslide" },
    { "id": "nawalparasiwest", "name": "Nawalparasi West", "nameNep": "पश्चिम नवलपरासी", "province": 5, "lat": 27.50, "lng": 83.70, "population": 387000, "vulnerability": 6, "riskType": "Flood" },
    { "id": "rupanadehi", "name": "Rupandehi", "nameNep": "रुपन्देही", "province": 5, "lat": 27.58, "lng": 83.45, "population": 1121957, "vulnerability": 6, "riskType": "Flood" },
    { "id": "kapilvastu", "name": "Kapilvastu", "nameNep": "कपिलवस्तु", "province": 5, "lat": 27.60, "lng": 83.00, "population": 686739, "vulnerability": 6, "riskType": "Flood/Fire" },
    { "id": "dang", "name": "Dang", "nameNep": "दाङ", "province": 5, "lat": 28.00, "lng": 82.40, "population": 674993, "vulnerability": 5, "riskType": "Flood/Fire" },
    { "id": "banke", "name": "Banke", "nameNep": "बाँके", "province": 5, "lat": 28.15, "lng": 81.65, "population": 610580, "vulnerability": 7, "riskType": "Flood/Heat" },
    { "id": "bardiya", "name": "Bardiya", "nameNep": "बर्दिया", "province": 5, "lat": 28.25, "lng": 81.30, "population": 487950, "vulnerability": 7, "riskType": "Flood" },

    # Province 6: Karnali
    { "id": "rukumwest", "name": "Rukum West", "nameNep": "पश्चिम रुकुम", "province": 6, "lat": 28.80, "lng": 82.45, "population": 166000, "vulnerability": 7, "riskType": "Earthquake/Landslide" },
    { "id": "salyan", "name": "Salyan", "nameNep": "सल्यान", "province": 6, "lat": 28.35, "lng": 82.15, "population": 238000, "vulnerability": 5, "riskType": "Landslide" },
    { "id": "dolpa", "name": "Dolpa", "nameNep": "डोल्पा", "province": 6, "lat": 29.10, "lng": 82.95, "population": 42766, "vulnerability": 7, "riskType": "Snow/Cold/Drought" },
    { "id": "jumla", "name": "Jumla", "nameNep": "जुम्ला", "province": 6, "lat": 29.27, "lng": 82.18, "population": 118000, "vulnerability": 6, "riskType": "Snow/Cold/Flood" },
    { "id": "mugu", "name": "Mugu", "nameNep": "मुगु", "province": 6, "lat": 29.60, "lng": 82.25, "population": 64000, "vulnerability": 7, "riskType": "Landslide/Snow/Drought" },
    { "id": "humla", "name": "Humla", "nameNep": "हुम्ला", "province": 6, "lat": 30.00, "lng": 81.80, "population": 55000, "vulnerability": 8, "riskType": "Snow/Isolation/Cold" },
    { "id": "kalikot", "name": "Kalikot", "nameNep": "कालिकोट", "province": 6, "lat": 29.15, "lng": 81.80, "population": 144000, "vulnerability": 8, "riskType": "Landslide/Flood" },
    { "id": "jajarkot", "name": "Jajarkot", "nameNep": "जाजरकोट", "province": 6, "lat": 28.90, "lng": 82.20, "population": 189365, "vulnerability": 9, "riskType": "Earthquake/Landslide" },
    { "id": "dailekh", "name": "Dailekh", "nameNep": "दैलेख", "province": 6, "lat": 28.85, "lng": 81.70, "population": 252000, "vulnerability": 6, "riskType": "Landslide" },
    { "id": "surkhet", "name": "Surkhet", "nameNep": "सुर्खेत", "province": 6, "lat": 28.60, "lng": 81.63, "population": 415126, "vulnerability": 6, "riskType": "Flood/Landslide" },

    # Province 7: Sudurpashchim
    { "id": "bajura", "name": "Bajura", "nameNep": "बाजुरा", "province": 7, "lat": 29.45, "lng": 81.55, "population": 138000, "vulnerability": 8, "riskType": "Landslide/Earthquake" },
    { "id": "bajhang", "name": "Bajhang", "nameNep": "बझाङ", "province": 7, "lat": 29.75, "lng": 81.25, "population": 189000, "vulnerability": 8, "riskType": "Earthquake/Landslide" },
    { "id": "darchula", "name": "Darchula", "nameNep": "दार्चुला", "province": 7, "lat": 29.85, "lng": 80.60, "population": 135000, "vulnerability": 7, "riskType": "Landslide/FlashFlood" },
    { "id": "baitadi", "name": "Baitadi", "nameNep": "बैतडी", "province": 7, "lat": 29.50, "lng": 80.50, "population": 242000, "vulnerability": 6, "riskType": "Landslide/Earthquake" },
    { "id": "dadeldhura", "name": "Dadeldhura", "nameNep": "डडेल्धुरा", "province": 7, "lat": 29.30, "lng": 80.60, "population": 139000, "vulnerability": 5, "riskType": "Landslide" },
    { "id": "kanchanpur", "name": "Kanchanpur", "nameNep": "कञ्चनपुर", "province": 7, "lat": 28.90, "lng": 80.20, "population": 513757, "vulnerability": 6, "riskType": "Flood" },
    { "id": "kailali", "name": "Kailali", "nameNep": "कैलाली", "province": 7, "lat": 28.75, "lng": 80.90, "population": 911155, "vulnerability": 7, "riskType": "Flood/Heat" },
    { "id": "doti", "name": "Doti", "nameNep": "डोटी", "province": 7, "lat": 29.20, "lng": 80.95, "population": 205000, "vulnerability": 6, "riskType": "Earthquake/Landslide" },
    { "id": "achham", "name": "Achham", "nameNep": "अछाम", "province": 7, "lat": 29.10, "lng": 81.30, "population": 228000, "vulnerability": 7, "riskType": "Landslide" }
]

MUNICIPALITIES = [
    { "name": "Melamchi", "nameNep": "मेलम्ची", "district": "sindhupalchok", "lat": 27.83, "lng": 85.58, "pop": 45000, "note": "Sufferer of high flood events" },
    { "name": "Helambu", "nameNep": "हेलम्बु", "district": "sindhupalchok", "lat": 27.97, "lng": 85.53, "pop": 18000, "note": "Melamchi upstream flood origin" },
    { "name": "Barhabise", "nameNep": "बाह्रबिसे", "district": "sindhupalchok", "lat": 27.78, "lng": 85.90, "pop": 27000, "note": "Araniko Highway landslide area" },
    { "name": "Bhotekoshi", "nameNep": "भोटेकोशी", "district": "sindhupalchok", "lat": 27.94, "lng": 85.95, "pop": 19000, "note": "High flash flood vulnerability" },
    { "name": "Birendranagar", "nameNep": "वीरेन्द्रनगर", "district": "surkhet", "lat": 28.60, "lng": 81.63, "pop": 154000, "note": "Karnali regional hub" },
    { "name": "Khalanga", "nameNep": "खलङ्गा", "district": "jajarkot", "lat": 28.90, "lng": 82.20, "pop": 35000, "note": "Jajarkot earthquake epicenter" },
    { "name": "Athbiskot", "nameNep": "आठबिसकोट", "district": "rukumwest", "lat": 28.87, "lng": 82.35, "pop": 38000, "note": "Earthquake highly affected zone" },
    { "name": "Ramidanda", "nameNep": "रामिडाँडा", "district": "jajarkot", "lat": 28.93, "lng": 82.22, "pop": 5000, "note": "2023 Earthquake Epicenter" },
    { "name": "Balkhu", "nameNep": "बल्खु", "district": "kathmandu", "lat": 27.68, "lng": 85.29, "pop": 85000, "note": "Bagmati river overflow inundation risk" },
    { "name": "Kapan", "nameNep": "कपिला", "district": "kathmandu", "lat": 27.73, "lng": 85.36, "pop": 72000, "note": "Urban flooding/drainage block area" },
    { "name": "Lalitpur Pulchowk", "nameNep": "पुल्चोक", "district": "lalitpur", "lat": 27.67, "lng": 85.31, "pop": 98000, "note": "Urban response dispatch center" },
    { "name": "Bhaktapur Hanumante", "nameNep": "हनुमन्ते", "district": "bhaktapur", "lat": 27.67, "lng": 85.42, "pop": 64000, "note": "Hanumante river flood zone" },
    { "name": "Syabrubesi", "nameNep": "स्याफ्रुबेसी", "district": "rasuwa", "lat": 28.15, "lng": 85.30, "pop": 12000, "note": "Landslide blocking highway to Tibet border" },
    { "name": "Dhunche", "nameNep": "धुन्चे", "district": "rasuwa", "lat": 28.11, "lng": 85.30, "pop": 15000, "note": "District headquarter mountain risk" },
    { "name": "Tatopani", "nameNep": "तातोपानी", "district": "sindhupalchok", "lat": 27.94, "lng": 85.96, "pop": 8000, "note": "Border landslide and flood prone area" }
]

HOSPITALS = [
    { "name": "Tribhuvan University Teaching Hospital (TUTH)", "lat": 27.737, "lng": 85.331, "city": "Kathmandu", "capacity": "Large" },
    { "name": "Bir Hospital", "lat": 27.705, "lng": 85.314, "city": "Kathmandu", "capacity": "Large" },
    { "name": "Patan Hospital", "lat": 27.668, "lng": 85.321, "city": "Lalitpur", "capacity": "Large" },
    { "name": "Karnali Provincial Hospital", "lat": 28.595, "lng": 81.621, "city": "Birendranagar, Surkhet", "capacity": "Medium" },
    { "name": "Bheri Hospital", "lat": 28.056, "lng": 81.616, "city": "Nepalgunj, Banke", "capacity": "Medium" },
    { "name": "Gandaki Province Hospital", "lat": 28.217, "lng": 83.989, "city": "Pokhara, Kaski", "capacity": "Medium" },
    { "name": "Kosli Zonal Hospital", "lat": 26.458, "lng": 87.279, "city": "Biratnagar, Morang", "capacity": "Medium" }
]

SENSOR_STATIONS = [
    {
        "id": "station_bhotekoshi_1",
        "name": "Bhotekoshi River Gauge (Barhabise)",
        "lat": 27.785,
        "lng": 85.901,
        "type": "River Level",
        "unit": "meters",
        "warningLevel": 5.0,
        "dangerLevel": 6.0,
        "currentValue": 3.2,
        "district": "sindhupalchok"
    },
    {
        "id": "station_sunkoshi_1",
        "name": "Sunkoshi River Gauge (Pangretar)",
        "lat": 27.712,
        "lng": 85.875,
        "type": "River Level",
        "unit": "meters",
        "warningLevel": 6.0,
        "dangerLevel": 8.0,
        "currentValue": 4.1,
        "district": "sindhupalchok"
    },
    {
        "id": "station_jajarkot_seismic",
        "name": "Jajarkot Seismic Sensor",
        "lat": 28.905,
        "lng": 82.205,
        "type": "Seismic (Magnitude)",
        "unit": "Richter Scale",
        "warningLevel": 4.0,
        "dangerLevel": 5.0,
        "currentValue": 0.8,
        "district": "jajarkot"
    },
    {
        "id": "station_syabru_rain",
        "name": "Syabrubesi Rain Gauge",
        "lat": 28.151,
        "lng": 85.302,
        "type": "Rainfall (24h)",
        "unit": "mm",
        "warningLevel": 100,
        "dangerLevel": 140,
        "currentValue": 45,
        "district": "rasuwa"
    },
    {
        "id": "station_kathmandu_rain",
        "name": "Kathmandu Airport Met Station",
        "lat": 27.698,
        "lng": 85.358,
        "type": "Rainfall (24h)",
        "unit": "mm",
        "warningLevel": 80,
        "dangerLevel": 120,
        "currentValue": 20,
        "district": "kathmandu"
    }
]
