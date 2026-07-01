"""
Maps each country's native fuel-type labels onto Pumpr's existing
fuel_type enum values (E10, E5, Diesel, SuperDiesel).
None = explicitly dropped (not in our enum).
"""

FUEL_TYPE_MAP: dict[str, dict[str, str | None]] = {
    "FR": {
        "Gazole": "Diesel",
        "SP95": "E5",
        "SP98": "E5",
        "E10": "E10",
        "E85": None,
        "GPLc": None,
    },
}
