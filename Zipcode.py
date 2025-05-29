# PURPOSE OF SCRIPT
# SO we wanted to make a world map but only had address and no latitude and longitude.
# We did hours of research and decided to use geopy library to find the latitude and longitude of the address.
# Again this was big since we have more data to help clients find where they're homes of potential interest are located


# Import libraries
import pandas as pd
import re
import requests
from geopy.geocoders import Nominatim
from geopy.extra.rate_limiter import RateLimiter

# Helper functions
def normalize_address(addr):
    """
    Basic cleaning: expand directional abbreviations,
    strip suite/unit info, ensure city + state present.
    """
    # Expand “ E ” → “ East ”
    addr = re.sub(r'\bN\b',  'North',  addr)
    addr = re.sub(r'\bS\b',  'South',  addr)
    addr = re.sub(r'\bE\b',  'East',   addr)
    addr = re.sub(r'\bW\b',  'West',   addr)
    # Drop suite/apartment strings
    addr = re.sub(r',? *Apt.*', '', addr, flags=re.IGNORECASE)
    addr = re.sub(r',? *Unit.*', '', addr, flags=re.IGNORECASE)
    return addr.strip()

def census_geocode(addr):
    """
    Fall back to the U.S. Census Geocoder (free, batch-friendly).
    Returns (lat, lon) or (None, None).
    """
    url = "https://geocoding.geo.census.gov/geocoder/locations/onelineaddress"
    params = {
        "address": addr,
        "benchmark": "Public_AR_Census2020",
        "format": "json"
    }
    res = requests.get(url, params=params, timeout=10).json()
    matches = res.get("result", {}).get("addressMatches", [])
    if matches:
        coords = matches[0]["coordinates"]
        return coords["y"], coords["x"]
    return None, None

# 2) Load and detect address column ———

df = pd.read_csv("Final_SWFL_Cleaning.csv")
addr_cols = [c for c in df.columns if "address" in c.lower()]
if not addr_cols:
    raise ValueError("No column containing 'address' found.")
address_col = addr_cols[0]

# 3) Initialize primary geocoder ———

geolocator = Nominatim(user_agent="swfl_geocoder")
geocode    = RateLimiter(geolocator.geocode, min_delay_seconds=1, max_retries=2)

# 4) Geocode with fallbacks ———

results = []
for idx, raw_addr in df[address_col].dropna().items():
    addr = normalize_address(raw_addr)
    # 4A) Try OSM first
    loc = geocode(addr)
    if loc:
        lat, lon = loc.latitude, loc.longitude

    else:
        # 4B) Try Census
        lat, lon = census_geocode(addr)

    # 4C) Final fallback: log nothing found
    status = "OK" if lat is not None else "FAIL"
    print(f"[{idx}] {status}: {raw_addr!r} → ({lat}, {lon})")

    results.append({
        "original_address": raw_addr,
        "clean_address":    addr,
        "latitude":         lat,
        "longitude":        lon
    })

# Save Data ———
# Yea I merged this dataset later on. Again it's not in zip folder since we did not want to include a lot of redundant 
# # Mainly for debugging and verification 
out = pd.DataFrame(results)
out.to_csv("Final_SWFL_With_Fallback_Coords.csv", index=False)
print("\nDone — CSV with lat/lon plus fallbacks written.")
