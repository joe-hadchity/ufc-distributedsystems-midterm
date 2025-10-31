from __future__ import annotations
import re
from bs4 import BeautifulSoup
from typing import Dict, Any


def clean_html_to_text(html: str) -> str:
    soup = BeautifulSoup(html, "lxml")
    for tag in soup(["script", "style", "noscript"]):
        tag.decompose()
    text = soup.get_text(" ", strip=True)
    text = re.sub(r"\s+", " ", text)
    return text


def parse_fighter_schema(html: str, url: str) -> Dict[str, Any]:
    soup = BeautifulSoup(html, "lxml")
    schema: Dict[str, Any] = {
        "url": url,
        "name": None,
        "nickname": None,
        "weight_class": None,
        "record": None,
        "stance": None,
        "reach": None,
        "height": None,
        "dob": None,
        "country": None,
        "fights": [],
    }

    # Heuristics based on UFC athlete pages; robust to small variations
    name = soup.select_one("h1, .hero__headline")
    if name:
        schema["name"] = name.get_text(strip=True)

    # Common labels and data extraction
    def find_label(label: str):
        el = soup.find(string=re.compile(label, re.I))
        if el and el.parent:
            return el.parent.get_text(" ", strip=True)
        return None

    schema["nickname"] = find_label("Nickname") or None
    schema["weight_class"] = find_label("Weight class|Division") or None
    schema["record"] = find_label("Record") or None
    schema["stance"] = find_label("Stance") or None
    schema["reach"] = find_label("Reach") or None
    schema["height"] = find_label("Height") or None
    schema["dob"] = find_label("Born|DOB|Date of Birth") or None

    # Country: often appears near flag or location
    country = None
    for sel in [".hero__flag-title", ".field--name-country", "[data-country]"]:
        n = soup.select_one(sel)
        if n:
            country = n.get_text(strip=True)
            break
    schema["country"] = country

    # Recent fights table parsing (best-effort)
    fights = []
    for row in soup.select("table tr"):
        cells = [c.get_text(" ", strip=True) for c in row.select("td")]
        if len(cells) >= 5 and any(k in " ".join(cells).lower() for k in ["round", "method", "time"]):
            fights.append({
                "opponent": cells[0],
                "method": cells[2] if len(cells) > 2 else None,
                "round": cells[3] if len(cells) > 3 else None,
                "time": cells[4] if len(cells) > 4 else None,
            })
    if fights:
        schema["fights"] = fights

    return schema

