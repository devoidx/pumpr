"""
Maps each country's native fuel-type labels onto Pumpr's existing
fuel_type enum values (E10, E5, Diesel, SuperDiesel).
None = explicitly dropped (not in our enum).
"""

FUEL_TYPE_MAP: dict[str, dict[str, str | None]] = {
    "ES": {
        "Precio Gasolina 95 E5": "E5",
        "Precio Gasolina 95 E10": "E10",
        "Precio Gasoleo A": "Diesel",
        "Precio Gasoleo Premium": None,
        "Precio Gasolina 98 E5": None,
        "Precio Gasoleo B": None,
    },
    "IT": {
        "Benzina": "E5",
        "Gasolio": "Diesel",
        "GPL": None,
        "Metano": None,
        "Blue Super": None,   # premium branded fuel, not in enum
        "Benzina speciale": None,
        "Gasolio speciale": None,
    },
    "FR": {
        "Gazole": "Diesel",
        "SP95": "E5",
        "SP98": "E5",
        "E10": "E10",
        "E85": None,
        "GPLc": None,
    },
}
