"""Fetch real Halifax restaurants from OpenStreetMap (Overpass API)."""
from __future__ import annotations

import json
import math
import urllib.request
from collections import Counter
from pathlib import Path

OUT = Path(__file__).resolve().parents[1] / "instance" / "osm_raw.json"

QUERY = """
[out:json][timeout:90];
(
  node["amenity"="restaurant"](44.58,-63.72,44.78,-63.48);
  way["amenity"="restaurant"](44.58,-63.72,44.78,-63.48);
  node["amenity"="fast_food"]["cuisine"~"indian|italian|japanese|sushi|chinese|mexican|thai|seafood|lebanese|middle_eastern|kebab|ramen|pizza",i](44.58,-63.72,44.78,-63.48);
);
out center tags;
"""


def main():
    req = urllib.request.Request(
        "https://overpass-api.de/api/interpreter",
        data=QUERY.encode(),
        headers={"User-Agent": "DineDiscover/1.0 (HCI course project)"},
    )
    with urllib.request.urlopen(req, timeout=120) as resp:
        data = json.load(resp)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(data), encoding="utf-8")
    named = [e for e in data["elements"] if e.get("tags", {}).get("name")]
    cuisines = Counter(e["tags"].get("cuisine", "(none)") for e in named)
    print(f"elements={len(data['elements'])} named={len(named)}")
    for k, v in cuisines.most_common(30):
        print(f"  {v:3d} {k}")
    print(f"saved {OUT}")


if __name__ == "__main__":
    main()
