import requests
from collections import defaultdict

API_KEY = "AIzaSyA3runJi0uovu7bEOL7E2HytrXXuHFqvOk"

TASHKENT_LOCATION = "41.311081,69.240562"
TASHKENT_RADIUS_METERS = 30000


# ---------------------------------------------------------
# 1. Reverse Geocoding to extract district name
# ---------------------------------------------------------
def get_district_from_coordinates(lat, lng):
    url = "https://maps.googleapis.com/maps/api/geocode/json"
    params = {
        "latlng": f"{lat},{lng}",
        "key": API_KEY,
        "language": "en"
    }
    data = requests.get(url, params=params).json()

    for result in data.get("results", []):
        for comp in result.get("address_components", []):
            if "sublocality" in comp["types"] or "locality" in comp["types"]:
                return comp["long_name"]       # district name

    return "Unknown district"


# ---------------------------------------------------------
# 2. Load all bus stops
# ---------------------------------------------------------
def get_bus_stops():
    url = "https://maps.googleapis.com/maps/api/place/nearbysearch/json"
    params = {
        "key": API_KEY,
        "location": TASHKENT_LOCATION,
        "radius": TASHKENT_RADIUS_METERS,
        "keyword": "avtobus bekat",
        "type": "bus_station"
    }

    results = []
    while True:
        data = requests.get(url, params=params).json()
        results.extend(data.get("results", []))

        if "next_page_token" not in data:
            break
        params["pagetoken"] = data["next_page_token"]

    return results


# ---------------------------------------------------------
# 3. Load all subway stations
# ---------------------------------------------------------
def get_subway_stations():
    url = "https://maps.googleapis.com/maps/api/place/nearbysearch/json"
    params = {
        "key": API_KEY,
        "location": TASHKENT_LOCATION,
        "radius": TASHKENT_RADIUS_METERS,
        "type": "subway_station"
    }

    results = []
    while True:
        data = requests.get(url, params=params).json()
        results.extend(data.get("results", []))

        if "next_page_token" not in data:
            break
        params["pagetoken"] = data["next_page_token"]

    return results


# ---------------------------------------------------------
# 4. Group data by district
# ---------------------------------------------------------
def group_by_district(places):
    grouped = defaultdict(list)

    for place in places:
        lat = place["geometry"]["location"]["lat"]
        lng = place["geometry"]["location"]["lng"]

        district = get_district_from_coordinates(lat, lng)

        grouped[district].append({
            "name": place.get("name", "Unknown"),
            "lat": lat,
            "lng": lng
        })

    return grouped


# ---------------------------------------------------------
# MAIN SCRIPT
# ---------------------------------------------------------
if __name__ == "__main__":
    print("Loading bus stops...")
    bus_stops = get_bus_stops()
    print(f"Total bus stops: {len(bus_stops)}")

    print("Loading subway stations...")
    subway_stations = get_subway_stations()
    print(f"Total subway stations: {len(subway_stations)}")

    print("Grouping bus stops by district...")
    bus_by_district = group_by_district(bus_stops)

    print("Grouping subway stations by district...")
    metro_by_district = group_by_district(subway_stations)

    # Print summary
    print("\n================= SUMMARY =================")
    for district, stops in bus_by_district.items():
        print(f"{district}: {len(stops)} bus stops")

    print("\n-------------------------------------------")
    for district, stations in metro_by_district.items():
        print(f"{district}: {len(stations)} subway stations")
