import json
import math
import time
import requests
import random
from google.adk.tools import FunctionTool

MAJOR_COASTAL_HUBS = [
    {"name": "Mandvi Beach, Gujarat", "lat": 22.8271, "lon": 69.3496, "vibe": "Serene & Historic", "food": "Double Rotlo"},
    {"name": "Puri Beach, Odisha", "lat": 19.7983, "lon": 85.8249, "vibe": "Spiritual & Golden Sands", "food": "Khaja"},
    {"name": "Baga Beach, Goa", "lat": 15.5553, "lon": 73.7517, "vibe": "Party & Nightlife", "food": "Bebinca"},
    {"name": "Marina Beach, Chennai", "lat": 13.0418, "lon": 80.2850, "vibe": "Urban & Iconic", "food": "Sundal"}
]

MAJOR_HILLS = [
    {"name": "Mussoorie, Uttarakhand", "lat": 30.4599, "lon": 78.0664, "vibe": "Colonial Charm", "food": "Garhwali Maggi"},
    {"name": "Nainital, Uttarakhand", "lat": 29.3919, "lon": 79.4542, "vibe": "Lakeside Relaxation", "food": "Baal Mithai"},
    {"name": "Manali, Himachal", "lat": 32.2432, "lon": 77.1892, "vibe": "Adventure Hub", "food": "Siddu"}
]

OVERPASS_MIRRORS = [
    "https://overpass.private.coffee/api/interpreter",
    "https://overpass.osm.ch/api/interpreter",
    "https://overpass.kumi.systems/api/interpreter"
]



def haversine_distance(lat1, lon1, lat2, lon2):
    R = 6371
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi, dlambda = math.radians(lat2 - lat1), math.radians(lon2 - lon1)
    a = math.sin(dphi/2)**2 + math.cos(phi1)*math.cos(phi2)*math.sin(dlambda/2)**2
    return round(2 * R * math.asin(math.sqrt(a)), 1)

def get_travel_advice(distance_km):
    if distance_km < 350:
        return "Road Trip", "🚗"
    elif distance_km < 750:
        return "Overnight Train", "🚂"
    else:
        return "Flight Recommended", "✈️"

def estimate_travel_time(distance_km):
    minutes = int((distance_km / 55) * 60)
    hours, mins = divmod(minutes, 60)
    return f"{hours}h {mins}m" if hours > 0 else f"{mins}m"

def geocode_city(city_name):
    url = "https://nominatim.openstreetmap.org/search"
    params = {"q": city_name, "format": "json", "limit": 1}
    headers = {"User-Agent": "TravelAgentPro/1.1"}
    try:
        response = requests.get(url, params=params, headers=headers, timeout=10)
        data = response.json()
        return (float(data[0]['lat']), float(data[0]['lon'])) if data else (None, None)
    except Exception: return None, None

def find_nearby_places(lat, lon, category, radius_m=300000, limit=3):
    url = random.choice(OVERPASS_MIRRORS)
    tag = 'node["tourism"="mountain_pass"]' if category == "hill station" else 'node["natural"="beach"]'
    query = f'[out:json][timeout:30];(node{tag}(around:{radius_m},{lat},{lon}););out center {limit};'
    try:
        response = requests.post(url, data=query, timeout=25)
        if response.status_code == 200:
            return response.json().get("elements", [])
    except Exception: pass
    return []


def get_current_weather(city_name: str) -> str:
    """Fetch real-time weather to provide better travel suggestions."""
    
    api_key = "YOUR_API_KEY" 
    if api_key == "YOUR_API_KEY":
        return json.dumps({"temp": 22, "condition": "Cloudy", "note": "Add API Key for real data"})
    
    url = f"http://api.openweathermap.org/data/2.5/weather?q={city_name}&appid={api_key}&units=metric"
    try:
        data = requests.get(url, timeout=5).json()
        return json.dumps({"temp": data["main"]["temp"], "condition": data["weather"][0]["main"]})
    except: return json.dumps({"temp": "Unknown", "condition": "Unavailable"})

def find_travel_destinations(origin_city: str) -> str:
    """Finds destinations and returns enriched travel data."""
    print(f"DEBUG: Searching destinations near {origin_city}...")
    orig_lat, orig_lon = geocode_city(origin_city)
    if orig_lat is None: return json.dumps({"error": f"City '{origin_city}' not found."})

    results = {"city": origin_city.title(), "origin": {"lat": orig_lat, "lon": orig_lon}, "mountains": [], "beaches": []}

   
    hill_elements = find_nearby_places(orig_lat, orig_lon, "hill station", radius_m=300000, limit=3)
    if not hill_elements: hill_elements = MAJOR_HILLS[:2]
    for p in hill_elements:
        p_lat, p_lon = p.get('lat') or p.get('center', {}).get('lat'), p.get('lon') or p.get('center', {}).get('lon')
        name = p.get('tags', {}).get('name', p.get('name', 'Mountain Peak'))
        dist = haversine_distance(orig_lat, orig_lon, p_lat, p_lon)
        mode, icon = get_travel_advice(dist)
        results["mountains"].append({
            "name": name, "lat": p_lat, "lon": p_lon, "distance": f"{dist} km", 
            "drive_time": estimate_travel_time(dist), "transport": mode, "icon": icon,
            "vibe": p.get("vibe", "Scenic"), "food": p.get("food", "Local Snacks")
        })

    
    api_beaches = find_nearby_places(orig_lat, orig_lon, "beach", radius_m=100000, limit=3)
    beach_list = api_beaches if api_beaches else MAJOR_COASTAL_HUBS
    for b in beach_list:
        b_lat, b_lon = b.get('lat') or b.get('center', {}).get('lat'), b.get('lon') or b.get('center', {}).get('lon')
        name = b.get('tags', {}).get('name', b.get('name', 'Coastline'))
        dist = haversine_distance(orig_lat, orig_lon, b_lat, b_lon)
        mode, icon = get_travel_advice(dist)
        results["beaches"].append({
            "name": name, "lat": b_lat, "lon": b_lon, "distance": f"{dist} km", 
            "drive_time": estimate_travel_time(dist), "transport": mode, "icon": icon,
            "vibe": b.get("vibe", "Relaxing"), "food": b.get("food", "Fresh Seafood")
        })
    return json.dumps(results)

maps_tool = FunctionTool(find_travel_destinations)
weather_tool = FunctionTool(get_current_weather)