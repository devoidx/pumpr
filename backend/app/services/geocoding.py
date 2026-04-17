import logging
import httpx

logger = logging.getLogger(__name__)

POSTCODES_API = "https://api.postcodes.io/postcodes"

COUNTRY_MAP = {
    "England": "England",
    "Scotland": "Scotland",
    "Wales": "Wales",
    "Northern Ireland": "Northern Ireland",
}

# Map admin_district -> ceremonial county for areas where admin_county is null
DISTRICT_TO_COUNTY = {
    # Greater London boroughs
    "CITY OF LONDON": "GREATER LONDON",
    "BARKING AND DAGENHAM": "GREATER LONDON",
    "BARNET": "GREATER LONDON",
    "BEXLEY": "GREATER LONDON",
    "BRENT": "GREATER LONDON",
    "BROMLEY": "GREATER LONDON",
    "CAMDEN": "GREATER LONDON",
    "CROYDON": "GREATER LONDON",
    "EALING": "GREATER LONDON",
    "ENFIELD": "GREATER LONDON",
    "GREENWICH": "GREATER LONDON",
    "HACKNEY": "GREATER LONDON",
    "HAMMERSMITH AND FULHAM": "GREATER LONDON",
    "HARINGEY": "GREATER LONDON",
    "HARROW": "GREATER LONDON",
    "HAVERING": "GREATER LONDON",
    "HILLINGDON": "GREATER LONDON",
    "HOUNSLOW": "GREATER LONDON",
    "ISLINGTON": "GREATER LONDON",
    "KENSINGTON AND CHELSEA": "GREATER LONDON",
    "KINGSTON UPON THAMES": "GREATER LONDON",
    "LAMBETH": "GREATER LONDON",
    "LEWISHAM": "GREATER LONDON",
    "MERTON": "GREATER LONDON",
    "NEWHAM": "GREATER LONDON",
    "REDBRIDGE": "GREATER LONDON",
    "RICHMOND UPON THAMES": "GREATER LONDON",
    "SOUTHWARK": "GREATER LONDON",
    "SUTTON": "GREATER LONDON",
    "TOWER HAMLETS": "GREATER LONDON",
    "WALTHAM FOREST": "GREATER LONDON",
    "WANDSWORTH": "GREATER LONDON",
    "WESTMINSTER": "GREATER LONDON",
    # Greater Manchester
    "BOLTON": "GREATER MANCHESTER",
    "BURY": "GREATER MANCHESTER",
    "MANCHESTER": "GREATER MANCHESTER",
    "OLDHAM": "GREATER MANCHESTER",
    "ROCHDALE": "GREATER MANCHESTER",
    "SALFORD": "GREATER MANCHESTER",
    "STOCKPORT": "GREATER MANCHESTER",
    "TAMESIDE": "GREATER MANCHESTER",
    "TRAFFORD": "GREATER MANCHESTER",
    "WIGAN": "GREATER MANCHESTER",
    # West Midlands
    "BIRMINGHAM": "WEST MIDLANDS",
    "COVENTRY": "WEST MIDLANDS",
    "DUDLEY": "WEST MIDLANDS",
    "SANDWELL": "WEST MIDLANDS",
    "SOLIHULL": "WEST MIDLANDS",
    "WALSALL": "WEST MIDLANDS",
    "WOLVERHAMPTON": "WEST MIDLANDS",
    # Merseyside
    "KNOWSLEY": "MERSEYSIDE",
    "LIVERPOOL": "MERSEYSIDE",
    "SEFTON": "MERSEYSIDE",
    "ST HELENS": "MERSEYSIDE",
    "WIRRAL": "MERSEYSIDE",
    # West Yorkshire
    "BRADFORD": "WEST YORKSHIRE",
    "CALDERDALE": "WEST YORKSHIRE",
    "KIRKLEES": "WEST YORKSHIRE",
    "LEEDS": "WEST YORKSHIRE",
    "WAKEFIELD": "WEST YORKSHIRE",
    # South Yorkshire
    "BARNSLEY": "SOUTH YORKSHIRE",
    "DONCASTER": "SOUTH YORKSHIRE",
    "ROTHERHAM": "SOUTH YORKSHIRE",
    "SHEFFIELD": "SOUTH YORKSHIRE",
    # Tyne and Wear
    "GATESHEAD": "TYNE AND WEAR",
    "NEWCASTLE UPON TYNE": "TYNE AND WEAR",
    "NORTH TYNESIDE": "TYNE AND WEAR",
    "SOUTH TYNESIDE": "TYNE AND WEAR",
    "SUNDERLAND": "TYNE AND WEAR",
    # Unitary authorities -> ceremonial counties
    "BATH AND NORTH EAST SOMERSET": "SOMERSET",
    "BLACKBURN WITH DARWEN": "LANCASHIRE",
    "BLACKPOOL": "LANCASHIRE",
    "BOURNEMOUTH, CHRISTCHURCH AND POOLE": "DORSET",
    "BRACKNELL FOREST": "BERKSHIRE",
    "BRIGHTON AND HOVE": "EAST SUSSEX",
    "BRISTOL, CITY OF": "GLOUCESTERSHIRE",
    "CENTRAL BEDFORDSHIRE": "BEDFORDSHIRE",
    "CHESHIRE EAST": "CHESHIRE",
    "CHESHIRE WEST AND CHESTER": "CHESHIRE",
    "CORNWALL": "CORNWALL",
    "CUMBERLAND": "CUMBRIA",
    "DARLINGTON": "COUNTY DURHAM",
    "DERBY": "DERBYSHIRE",
    "DURHAM": "COUNTY DURHAM",
    "EAST RIDING OF YORKSHIRE": "EAST RIDING OF YORKSHIRE",
    "HALTON": "CHESHIRE",
    "HARTLEPOOL": "COUNTY DURHAM",
    "HEREFORDSHIRE, COUNTY OF": "HEREFORDSHIRE",
    "ISLE OF WIGHT": "ISLE OF WIGHT",
    "KINGSTON UPON HULL, CITY OF": "EAST RIDING OF YORKSHIRE",
    "LEICESTER": "LEICESTERSHIRE",
    "LUTON": "BEDFORDSHIRE",
    "MEDWAY": "KENT",
    "MIDDLESBROUGH": "COUNTY DURHAM",
    "MILTON KEYNES": "BUCKINGHAMSHIRE",
    "NORTH LINCOLNSHIRE": "LINCOLNSHIRE",
    "NORTH EAST LINCOLNSHIRE": "LINCOLNSHIRE",
    "NORTH SOMERSET": "SOMERSET",
    "NORTH NORTHAMPTONSHIRE": "NORTHAMPTONSHIRE",
    "NOTTINGHAM": "NOTTINGHAMSHIRE",
    "PETERBOROUGH": "CAMBRIDGESHIRE",
    "PLYMOUTH": "DEVON",
    "PORTSMOUTH": "HAMPSHIRE",
    "READING": "BERKSHIRE",
    "REDCAR AND CLEVELAND": "COUNTY DURHAM",
    "RUTLAND": "RUTLAND",
    "SHROPSHIRE": "SHROPSHIRE",
    "SLOUGH": "BERKSHIRE",
    "SOUTH GLOUCESTERSHIRE": "GLOUCESTERSHIRE",
    "SOUTHAMPTON": "HAMPSHIRE",
    "SOUTHEND-ON-SEA": "ESSEX",
    "STOCKTON-ON-TEES": "COUNTY DURHAM",
    "STOKE-ON-TRENT": "STAFFORDSHIRE",
    "SWINDON": "WILTSHIRE",
    "TELFORD AND WREKIN": "SHROPSHIRE",
    "THURROCK": "ESSEX",
    "TORBAY": "DEVON",
    "WARRINGTON": "CHESHIRE",
    "WEST BERKSHIRE": "BERKSHIRE",
    "WEST NORTHAMPTONSHIRE": "NORTHAMPTONSHIRE",
    "WESTMORLAND AND FURNESS": "CUMBRIA",
    "WINDSOR AND MAIDENHEAD": "BERKSHIRE",
    "WOKINGHAM": "BERKSHIRE",
    "YORK": "NORTH YORKSHIRE",
    # Scotland - council areas -> regions
    "ABERDEEN CITY": "ABERDEENSHIRE",
    "ABERDEENSHIRE": "ABERDEENSHIRE",
    "ANGUS": "ANGUS",
    "ARGYLL AND BUTE": "ARGYLL AND BUTE",
    "CLACKMANNANSHIRE": "STIRLINGSHIRE",
    "DUMFRIES AND GALLOWAY": "DUMFRIES AND GALLOWAY",
    "DUNDEE CITY": "ANGUS",
    "EAST AYRSHIRE": "AYRSHIRE",
    "EAST DUNBARTONSHIRE": "DUNBARTONSHIRE",
    "EAST LOTHIAN": "LOTHIAN",
    "EAST RENFREWSHIRE": "RENFREWSHIRE",
    "EDINBURGH, CITY OF": "LOTHIAN",
    "CITY OF EDINBURGH": "LOTHIAN",
    "FALKIRK": "STIRLINGSHIRE",
    "FIFE": "FIFE",
    "GLASGOW CITY": "GLASGOW CITY",
    "HIGHLAND": "INVERNESS-SHIRE",
    "INVERCLYDE": "RENFREWSHIRE",
    "MIDLOTHIAN": "LOTHIAN",
    "MORAY": "MORAY",
    "NA H-EILEANAN AN IAR": "INVERNESS-SHIRE",
    "NORTH AYRSHIRE": "AYRSHIRE",
    "NORTH LANARKSHIRE": "LANARKSHIRE",
    "ORKNEY ISLANDS": "ORKNEY",
    "PERTH AND KINROSS": "PERTHSHIRE",
    "RENFREWSHIRE": "RENFREWSHIRE",
    "SCOTTISH BORDERS": "SCOTTISH BORDERS",
    "SHETLAND ISLANDS": "SHETLAND",
    "SOUTH AYRSHIRE": "AYRSHIRE",
    "SOUTH LANARKSHIRE": "LANARKSHIRE",
    "STIRLING": "STIRLINGSHIRE",
    "WEST DUNBARTONSHIRE": "DUNBARTONSHIRE",
    "WEST LOTHIAN": "LOTHIAN",
    # Wales - unitary authorities -> traditional counties
    "BLAENAU GWENT": "GWENT",
    "BRIDGEND": "MID GLAMORGAN",
    "CAERPHILLY": "MID GLAMORGAN",
    "CARDIFF": "SOUTH GLAMORGAN",
    "CARMARTHENSHIRE": "DYFED",
    "CEREDIGION": "DYFED",
    "CONWY": "CLWYD",
    "DENBIGHSHIRE": "CLWYD",
    "FLINTSHIRE": "CLWYD",
    "GWYNEDD": "GWYNEDD",
    "ISLE OF ANGLESEY": "GWYNEDD",
    "MERTHYR TYDFIL": "MID GLAMORGAN",
    "MONMOUTHSHIRE": "GWENT",
    "NEATH PORT TALBOT": "WEST GLAMORGAN",
    "NEWPORT": "GWENT",
    "PEMBROKESHIRE": "DYFED",
    "POWYS": "POWYS",
    "RHONDDA CYNON TAF": "MID GLAMORGAN",
    "SWANSEA": "WEST GLAMORGAN",
    "TORFAEN": "GWENT",
    "VALE OF GLAMORGAN": "SOUTH GLAMORGAN",
    "WREXHAM": "CLWYD",
    # Northern Ireland - districts -> counties
    "ANTRIM AND NEWTOWNABBEY": "COUNTY ANTRIM",
    "ARDS AND NORTH DOWN": "COUNTY DOWN",
    "ARMAGH CITY, BANBRIDGE AND CRAIGAVON": "COUNTY ARMAGH",
    "BELFAST": "COUNTY ANTRIM",
    "CAUSEWAY COAST AND GLENS": "COUNTY ANTRIM",
    "DERRY CITY AND STRABANE": "COUNTY LONDONDERRY",
    "FERMANAGH AND OMAGH": "COUNTY FERMANAGH",
    "LISBURN AND CASTLEREAGH": "COUNTY ANTRIM",
    "MID AND EAST ANTRIM": "COUNTY ANTRIM",
    "MID ULSTER": "COUNTY TYRONE",
    "NEWRY, MOURNE AND DOWN": "COUNTY DOWN",

}


async def lookup_postcodes_batch(postcodes: list[str]) -> dict[str, dict]:
    """Batch lookup postcodes via postcodes.io. Returns dict of clean_postcode -> {county, country}."""
    if not postcodes:
        return {}
    clean = [p.replace(" ", "").upper() for p in postcodes if p]
    if not clean:
        return {}
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.post(POSTCODES_API, json={"postcodes": clean})
            resp.raise_for_status()
            results = {}
            for item in resp.json().get("result", []):
                if item and item.get("result"):
                    r = item["result"]
                    pc = r.get("postcode", "").replace(" ", "").upper()
                    country = COUNTRY_MAP.get(r.get("country", ""))

                    # Use admin_county if available, otherwise map admin_district
                    admin_county = (r.get("admin_county") or "").upper().strip()
                    admin_district = (r.get("admin_district") or "").upper().strip()

                    if admin_county:
                        county = admin_county
                    elif admin_district in DISTRICT_TO_COUNTY:
                        county = DISTRICT_TO_COUNTY[admin_district]
                    else:
                        county = None  # Unknown — don't store bad data

                    results[pc] = {
                        "county": county,
                        "country": country,
                    }
            return results
    except Exception as e:
        logger.warning(f"postcodes.io lookup failed: {e}")
        return {}
