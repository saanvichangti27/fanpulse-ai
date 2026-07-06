"""Presentation-layer reference data for the locked emergent-ui frontend.

The frontend (frontend/src, LOCKED — never edited) consumes one data module
whose exports are defined by frontend/src/data/mock.js. The /ui/bootstrap
endpoint (routers/ui.py) rebuilds those exact shapes from the real engines;
this module holds the STATIC reference/lookup tables that mapping needs:

- app copy (brand name, nav labels, feature blurbs) — static UI text, not data;
- country/team reference (ISO codes, display names, flag codes, coordinates);
- display-label maps (stage number, event tag, archetype, industry slugs).

Nothing here is a metric. Every number the UI shows (volumes, sentiment,
demand, ROI, scores, ...) is computed live in routers/ui.py from the
ingestion/intelligence engines.
"""

# ---------------------------------------------------------------- app copy
BRAND = {
    "name": "FanPulseAI",
    "tagline": "Real-time marketing intelligence for the beautiful game.",
    "version": "v1.0",
}

NAV_LINKS = [
    {"path": "/", "label": "Home", "code": "00"},
    {"path": "/heatmap", "label": "Heatmap", "code": "01"},
    {"path": "/strategies", "label": "Strategies", "code": "02"},
    {"path": "/matches", "label": "Matches", "code": "03"},
]

FEATURES = [
    {"code": "F.01", "title": "Live Pulse",
     "body": "Rolling sentiment, emotion, and volume — refreshed every 2 seconds during kickoff."},
    {"code": "F.02", "title": "Moments Engine",
     "body": "Goals, red cards, VAR controversies and full-time turned into instant marketing triggers."},
    {"code": "F.03", "title": "Strategy Cards",
     "body": "Segment × channel × copy × ROI. Every card carries evidence, benchmark and confidence."},
    {"code": "F.04", "title": "Ticket Demand",
     "body": "0–100 demand index and sellout probability, re-forecast live when the match turns."},
]

# ------------------------------------------------------------ segment meta
# Colors are presentation attributes the UI's mock assigned per segment id;
# the segment ids themselves come from the real KMeans profiles.
SEGMENT_COLORS = {
    "superfans": "#a3e635",
    "traveling_ultras": "#ef4444",
    "casual_streamers": "#3b82f6",
    "deal_seekers": "#f59e0b",
    "lapsed_fans": "#8b5cf6",
}

# ------------------------------------------------------------ industry map
# The locked frontend's Icons.jsx only knows these five UI ids; the backend
# uses contract slugs. bootstrap emits UI ids and maps back on the way in.
INDUSTRY_TO_UI = {
    "food_delivery": {"id": "food_qsr", "label": "Food Delivery & QSR"},
    "merch_apparel": {"id": "sports_merch", "label": "Sports Merch & Apparel"},
    "beverages": {"id": "beverages", "label": "Beverages"},
    "streaming_ott": {"id": "streaming", "label": "Streaming / OTT"},
    "content_creator": {"id": "creators", "label": "Content Creators"},
}
UI_TO_INDUSTRY = {v["id"]: k for k, v in INDUSTRY_TO_UI.items()}

# ------------------------------------------------------------ event tags
# Exact strings the frontend's Icons.jsx MOMENT map keys on.
EVENT_TAG_UI = {
    "goal": "goal",
    "red_card": "red card",
    "var_controversy": "VAR controversy",
    "full_time": "full time",
    "kickoff": "kickoff",
    "surge_other": "other surge",
}

ARCHETYPE_DISPLAY = {
    "celebration_flash_offer": "Celebration Flash Offer",
    "consolation_offer": "Consolation Offer",
    "commemorative_drop": "Commemorative Drop",
    "tune_in_push": "Tune-In Push",
    "fan_trip_promo": "Fan Trip Promo",
    "watch_it_here": "Watch It Here",
    "install_play": "Install & Play",
    "flash_sale": "Flash Sale",
    "brand_awareness": "Brand Awareness",
    "content_idea": "Content Idea",
}

# Tournament stage int (training-data scale 0..5) -> display label.
STAGE_LABELS = {
    0: "Group Stage", 1: "Round of 32", 2: "Round of 16",
    3: "Quarter-Final", 4: "Semi-Final", 5: "Final",
}

# ---------------------------------------------------------- country lookup
# ISO2 (as produced by ingestion/geo.py or fixture files) ->
#   code:  3-letter display code (FIFA style, what the map labels show)
#   name:  display name
#   flag:  flagcdn iso2 path (lowercase; supports subdivisions like gb-eng)
#   coords: [longitude, latitude] for the map projection
# Football convention: GB/UK render as England (the fixtures' GB fans are
# EPL-context messages; a documented display choice, not a data claim).
COUNTRY_REF = {
    "BR": {"code": "BRA", "name": "Brazil", "flag": "br", "coords": [-51.9, -14.2]},
    "AR": {"code": "ARG", "name": "Argentina", "flag": "ar", "coords": [-63.6, -38.4]},
    "GB": {"code": "ENG", "name": "England", "flag": "gb-eng", "coords": [-1.5, 52.4]},
    "UK": {"code": "ENG", "name": "England", "flag": "gb-eng", "coords": [-1.5, 52.4]},
    "US": {"code": "USA", "name": "United States", "flag": "us", "coords": [-98.5, 39.8]},
    "ES": {"code": "ESP", "name": "Spain", "flag": "es", "coords": [-3.7, 40.4]},
    "DE": {"code": "GER", "name": "Germany", "flag": "de", "coords": [10.4, 51.2]},
    "FR": {"code": "FRA", "name": "France", "flag": "fr", "coords": [2.2, 46.6]},
    "IT": {"code": "ITA", "name": "Italy", "flag": "it", "coords": [12.6, 41.9]},
    "PT": {"code": "POR", "name": "Portugal", "flag": "pt", "coords": [-8.2, 39.4]},
    "MX": {"code": "MEX", "name": "Mexico", "flag": "mx", "coords": [-102.5, 23.6]},
    "JP": {"code": "JPN", "name": "Japan", "flag": "jp", "coords": [138.3, 36.2]},
    "KR": {"code": "KOR", "name": "South Korea", "flag": "kr", "coords": [127.8, 36.5]},
    "NL": {"code": "NED", "name": "Netherlands", "flag": "nl", "coords": [5.3, 52.1]},
    "BE": {"code": "BEL", "name": "Belgium", "flag": "be", "coords": [4.5, 50.5]},
    "MA": {"code": "MAR", "name": "Morocco", "flag": "ma", "coords": [-7.1, 31.8]},
    "SN": {"code": "SEN", "name": "Senegal", "flag": "sn", "coords": [-14.5, 14.5]},
    "UY": {"code": "URU", "name": "Uruguay", "flag": "uy", "coords": [-55.8, -32.5]},
    "HR": {"code": "CRO", "name": "Croatia", "flag": "hr", "coords": [15.2, 45.1]},
    "IN": {"code": "IND", "name": "India", "flag": "in", "coords": [78.9, 20.6]},
    "AU": {"code": "AUS", "name": "Australia", "flag": "au", "coords": [133.8, -25.3]},
    "SA": {"code": "SAU", "name": "Saudi Arabia", "flag": "sa", "coords": [45.1, 23.9]},
    "CA": {"code": "CAN", "name": "Canada", "flag": "ca", "coords": [-106.3, 56.1]},
    "EG": {"code": "EGY", "name": "Egypt", "flag": "eg", "coords": [30.8, 26.8]},
    "NG": {"code": "NGA", "name": "Nigeria", "flag": "ng", "coords": [8.7, 9.1]},
    "CO": {"code": "COL", "name": "Colombia", "flag": "co", "coords": [-74.3, 4.6]},
    "CL": {"code": "CHL", "name": "Chile", "flag": "cl", "coords": [-71.5, -35.6]},
    "TR": {"code": "TUR", "name": "Turkey", "flag": "tr", "coords": [35.2, 38.9]},
    "PL": {"code": "POL", "name": "Poland", "flag": "pl", "coords": [19.1, 51.9]},
    "RU": {"code": "RUS", "name": "Russia", "flag": "ru", "coords": [105.3, 61.5]},
    "ID": {"code": "IDN", "name": "Indonesia", "flag": "id", "coords": [113.9, -0.8]},
    "TH": {"code": "THA", "name": "Thailand", "flag": "th", "coords": [100.9, 15.9]},
    "VN": {"code": "VIE", "name": "Vietnam", "flag": "vn", "coords": [108.3, 14.1]},
}

# ------------------------------------------------------------- team lookup
# Team display name (as stored in the matches table) -> short code, flag,
# and the ISO2 whose fans "belong" to the team (used for goal attribution).
TEAM_REF = {
    "Brazil": {"short": "BRA", "iso2": "br", "fan_country": "BR"},
    "Argentina": {"short": "ARG", "iso2": "ar", "fan_country": "AR"},
    "France": {"short": "FRA", "iso2": "fr", "fan_country": "FR"},
    "England": {"short": "ENG", "iso2": "gb-eng", "fan_country": "GB"},
    "Spain": {"short": "ESP", "iso2": "es", "fan_country": "ES"},
    "Germany": {"short": "GER", "iso2": "de", "fan_country": "DE"},
    "USA": {"short": "USA", "iso2": "us", "fan_country": "US"},
    "Mexico": {"short": "MEX", "iso2": "mx", "fan_country": "MX"},
    "Japan": {"short": "JPN", "iso2": "jp", "fan_country": "JP"},
    "South Korea": {"short": "KOR", "iso2": "kr", "fan_country": "KR"},
    "Senegal": {"short": "SEN", "iso2": "sn", "fan_country": "SN"},
    "Morocco": {"short": "MAR", "iso2": "ma", "fan_country": "MA"},
}

# Forecast model feature names -> human-readable driver labels.
DRIVER_LABELS = {
    "buzz_index_train": "Live buzz",
    "stage": "Stage",
    "rank_gap": "Rank gap",
    "rivalry_flag": "Rivalry",
    "host_involved": "Host nation",
    "venue_capacity": "Venue capacity",
    "home_rank": "Home rank",
    "away_rank": "Away rank",
    "city_population_m": "City population",
    "day_of_week": "Day of week",
    "kickoff_hour_local": "Kickoff hour",
}
