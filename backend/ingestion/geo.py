# backend/ingestion/geo.py

def get_country_from_source(source: str, external_id: str, author: str | None = None, raw_country: str | None = None) -> str | None:
    """
    Attempt to infer user country.
    """
    if raw_country:
        return raw_country
        
    return None
