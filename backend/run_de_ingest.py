import asyncio
from app.services.eu.ingest import ingest_germany
asyncio.run(ingest_germany())
