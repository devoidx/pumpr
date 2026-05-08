#!/usr/bin/env python3
"""
Fetch brand logos from Google favicon service and store as base64 in the brands table.
Run once (or periodically to refresh).
"""
import asyncio
import base64
import os
from datetime import datetime

import httpx
import psycopg2

DATABASE_URL = os.environ["DATABASE_URL"].replace("postgresql+asyncpg://", "postgresql://")

BRANDS = {
    "ESSO":               ("Esso",            "esso.co.uk"),
    "BP":                 ("BP",              "bp.com"),
    "SHELL":              ("Shell",           "shell.co.uk"),
    "TESCO":              ("Tesco",           "tesco.com"),
    "TEXACO":             ("Texaco",          "texaco.co.uk"),
    "ASDA":               ("Asda",            "asda.com"),
    "MORRISONS":          ("Morrisons",       "morrisons.com"),
    "SAINSBURY'S":        ("Sainsbury's",     "sainsburys.co.uk"),
    "JET":                ("Jet",             "jet.co.uk"),
    "GULF":               ("Gulf",            "gulf-oil.co.uk"),
    "COSTCO WHOLESALE":   ("Costco",          "costco.co.uk"),
    "CIRCLE K":           ("Circle K",        "circlek.com"),
    "APPLEGREEN":         ("Applegreen",      "applegreenstores.com"),
    "SPAR":               ("Spar",            "spar.co.uk"),
    "WELCOME BREAK":      ("Welcome Break",   "welcomebreak.co.uk"),
    "MAXOL":              ("Maxol",           "maxol.ie"),
    "VALERO":             ("Valero",          "valero.com"),
    "TOTAL ENERGIES":     ("TotalEnergies",   "totalenergies.com"),
    "MURCO":              ("Murco",           "murco.co.uk"),
    "EG ON THE MOVE":     ("EG On the Move",  "eg.group"),
    "HARVEST ENERGY":     ("Harvest Energy",  "harvestenergy.co.uk"),
    "GO":                 ("Go",              "gogasoline.co.uk"),
    "ESSAR":              ("Essar",           "essaroil.co.uk"),
}

def fetch_logo(domain: str) -> bytes | None:
    url = f"https://www.google.com/s2/favicons?domain={domain}&sz=64"
    try:
        with httpx.Client(follow_redirects=True, timeout=10) as client:
            r = client.get(url)
            if r.status_code == 200 and len(r.content) > 100:
                return r.content
    except Exception as e:
        print(f"  Error fetching {domain}: {e}")
    return None

def main():
    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()
    now = datetime.now()

    for brand_key, (display_name, domain) in BRANDS.items():
        print(f"Fetching {display_name} ({domain})...", end=" ")
        logo_bytes = fetch_logo(domain)
        if logo_bytes:
            b64 = base64.b64encode(logo_bytes).decode()
            # Detect image type
            if logo_bytes[:4] == b'\x89PNG':
                mime = "image/png"
            elif logo_bytes[:2] == b'\xff\xd8':
                mime = "image/jpeg"
            elif logo_bytes[:6] in (b'GIF87a', b'GIF89a'):
                mime = "image/gif"
            elif logo_bytes[:4] == b'RIFF':
                mime = "image/webp"
            else:
                mime = "image/png"
            data_url = f"data:{mime};base64,{b64}"
            cur.execute("""
                INSERT INTO brands (name, display_name, logo_b64, logo_updated_at)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (name) DO UPDATE SET
                    display_name = EXCLUDED.display_name,
                    logo_b64 = EXCLUDED.logo_b64,
                    logo_updated_at = EXCLUDED.logo_updated_at
            """, (brand_key, display_name, data_url, now))
            conn.commit()
            print(f"OK ({len(logo_bytes)} bytes, {mime})")
        else:
            # Insert without logo so display_name is at least stored
            cur.execute("""
                INSERT INTO brands (name, display_name, logo_b64, logo_updated_at)
                VALUES (%s, %s, NULL, %s)
                ON CONFLICT (name) DO UPDATE SET
                    display_name = EXCLUDED.display_name,
                    logo_updated_at = EXCLUDED.logo_updated_at
            """, (brand_key, display_name, now))
            conn.commit()
            print("No logo found")

    cur.close()
    conn.close()
    print("Done.")

if __name__ == "__main__":
    main()
