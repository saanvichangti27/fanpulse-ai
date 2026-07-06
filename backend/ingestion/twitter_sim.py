"""SIMULATED Twitter/X stream generator -> Replay Engine file.

WHY SIMULATED: X removed its free API tier (pay-per-read, no hackathon-viable
access), so this source is an explicitly-labeled simulation (`source:
"twitter_sim"`). The tweet TEXT is synthetic; everything downstream is earned —
the same real NLP models classify it, the same SQL analytics aggregate it, and
no sentiment/emotion labels are smuggled into the data. Swapping in the paid X
API later is just another connector.

The generated timeline follows realistic match phases, aligned by default with
the beats of replay_dev_fixture.json so both files can be replayed TOGETHER for
a multi-source demo:

    pre-match buzz -> kickoff spike -> first-half chatter -> VAR anger burst
    -> mid-half chatter -> GOAL explosion -> full-time wave

Usage (from repo root):
    backend/venv/Scripts/python -m backend.ingestion.twitter_sim
        [--match-id m_001] [--home Brazil] [--away Argentina]
        [--tweets 600] [--markers] [--out FILE]

Then replay it (optionally at the same time as the YouTube replay):
    POST /api/v1/replay/control
    {"action":"start","match_id":"m_001","file":"replay_twitter_sim.json","speed":60}
"""
import argparse
import json
import os
import random
from datetime import datetime, timezone

from ..contracts import RANDOM_SEED

# Beats aligned with replay_dev_fixture.json (t_offsets in seconds)
BEATS = {"kickoff": 105, "var": 320, "goal": 660, "full_time": 750, "end": 780}

PLAYERS = {
    "Brazil": ["Vinicius", "Rodrygo", "Raphinha", "Endrick"],
    "Argentina": ["Messi", "Alvarez", "Lautaro", "Enzo"],
    "France": ["Mbappe", "Griezmann", "Camavinga"],
    "England": ["Kane", "Bellingham", "Saka", "Foden"],
    "_default": ["the number 10", "the striker", "their keeper", "the captain"],
}

FAN_COUNTRIES = {"home_pool": None, "away_pool": None,
                 "neutral": ["US", "GB", "IN", "MX", "DE", "FR", "JP", "NG", "ES", "IT"]}
TEAM_COUNTRY = {"Brazil": "BR", "Argentina": "AR", "France": "FR", "England": "GB",
                "Spain": "ES", "Germany": "DE", "USA": "US", "Mexico": "MX",
                "Japan": "JP", "South Korea": "KR", "Senegal": "SN", "Morocco": "MA"}
FLAGS = {"BR": "🇧🇷", "AR": "🇦🇷", "FR": "🇫🇷", "GB": "🇬🇧", "ES": "🇪🇸", "DE": "🇩🇪",
         "US": "🇺🇸", "MX": "🇲🇽", "IN": "🇮🇳", "JP": "🇯🇵", "NG": "🇳🇬", "IT": "🇮🇹"}

# Template banks per phase. Slots: {home} {away} {player} {tag} {flag}
T_PRE = [
    "Can't wait for {home} vs {away} tonight!! {tag}",
    "Match day!!! {flag} {tag}",
    "Who's winning this? {home} or {away}? {tag}",
    "Lineups are out and {player} starts. Big call. {tag}",
    "Bar is packed already, everyone here for {home} {away} {flag}",
    "predicting 2-1 {home}, {player} to score first {tag}",
    "nervous about this one ngl {tag}",
    "The atmosphere in the city is unreal right now {flag} {tag}",
]
T_PLAY = [
    "{player} is everywhere today, what a game so far {tag}",
    "midfield battle is intense {tag}",
    "we need to press higher, too passive {tag}",
    "{player} with a great run! so close {tag}",
    "this ref is letting a lot go {tag}",
    "possession stats crazy for {home} rn {tag}",
    "someone mark {player} PLEASE {tag}",
    "great save!! heart attack material {tag}",
    "half chances everywhere, one goal changes this {tag}",
]
T_VAR = [
    "NO WAY that's not a penalty?? VAR is a joke {tag}",
    "absolute robbery by the referee, disgraceful {tag}",
    "VAR took 4 minutes for THAT decision??? scandal {tag}",
    "the ref just ruined this match, I'm fuming 😡 {tag}",
    "how is that not a red card?! shocking officiating {tag}",
    "VAR strikes again... this is why fans hate it {tag}",
    "screaming at my TV, terrible terrible call {tag}",
]
T_GOAL = [
    "GOOOOOOOAL!!!! {player}!!!! 🔥🔥🔥 {tag}",
    "WHAT A GOAL BY {player}!! unbelievable scenes {flag} {tag}",
    "I'M SHAKING, {player} you beauty!!! {tag}",
    "that finish from {player} was pure class 😍 {tag}",
    "THE WHOLE BAR JUST EXPLODED {flag} {tag}",
    "goal of the tournament, no debate. {player}!! {tag}",
    "my neighbours definitely heard me scream {tag}",
    "{player} SIUUUU 🔥 {tag}",
    "crying actual tears of joy right now 😭 {flag} {tag}",
]
T_FT = [
    "Full time. What a match. Football is beautiful {tag}",
    "gutted... we go again next match 😭 {tag}",
    "WE WON!! never a doubt {flag} {tag}",
    "proud of this team regardless of the result {tag}",
    "that result changes the whole group, wow {tag}",
    "heading home hoarse and happy {flag} {tag}",
]

HANDLE_WORDS = ["footy", "gol", "fan", "ultra", "kop", "casa", "torcida", "hincha",
                "elclasico", "matchday", "tiki", "taka", "9", "10", "keeper", "vamos"]


def _phases(total: int) -> list[tuple[str, int, int, list]]:
    """(name, t_start, t_end, templates) with tweet counts per phase."""
    return [
        ("pre",   0,                BEATS["kickoff"],  T_PRE,  int(total * 0.10)),
        ("half1", BEATS["kickoff"], BEATS["var"],      T_PLAY, int(total * 0.18)),
        ("var",   BEATS["var"],     BEATS["var"] + 60, T_VAR,  int(total * 0.17)),
        ("mid",   BEATS["var"] + 60, BEATS["goal"],    T_PLAY, int(total * 0.15)),
        ("goal",  BEATS["goal"],    BEATS["goal"] + 60, T_GOAL, int(total * 0.30)),
        ("ft",    BEATS["full_time"], BEATS["end"],    T_FT,   int(total * 0.10)),
    ]


def generate(match_id: str, home: str, away: str, tweets: int,
             markers: bool, out_path: str | None) -> str:
    rng = random.Random(RANDOM_SEED)
    home_cc = TEAM_COUNTRY.get(home, "US")
    away_cc = TEAM_COUNTRY.get(away, "GB")
    tags = [f"#{home}{away}", f"#{home}vs{away}", "#WorldCup2026", f"#{home}", f"#{away}"]

    items = []
    n = 0
    for name, t0, t1, bank, count in _phases(tweets):
        for _ in range(count):
            t = round(rng.uniform(t0, t1), 1)
            # 45% home fan, 30% away fan, 25% neutral
            r = rng.random()
            cc = home_cc if r < 0.45 else (away_cc if r < 0.75 else rng.choice(FAN_COUNTRIES["neutral"]))
            team = home if cc == home_cc else (away if cc == away_cc else rng.choice([home, away]))
            player = rng.choice(PLAYERS.get(team, PLAYERS["_default"]))
            text = rng.choice(bank).format(
                home=home, away=away, player=player,
                tag=rng.choice(tags), flag=FLAGS.get(cc, ""),
            ).strip()
            if rng.random() < 0.12:  # retweet-style
                text = f"RT @{rng.choice(HANDLE_WORDS)}{rng.randint(1, 999)}: {text}"

            # country signal mix: 40% explicit, else None -> geo.py infers from
            # flags in the text where present, exercising the real inference path
            country = cc if rng.random() < 0.40 else None
            n += 1
            items.append({
                "t_offset": t,
                "external_id": f"tw_sim_{match_id}_{n:05d}",
                "source": "twitter_sim",
                "author": f"@{rng.choice(HANDLE_WORDS)}_{rng.choice(HANDLE_WORDS)}{rng.randint(1, 99)}",
                "text": text,
                "country": country,
            })

    if markers:  # only when replayed standalone (the YouTube fixture already has them)
        items += [{"t_offset": float(BEATS["kickoff"]), "marker": "kickoff"},
                  {"t_offset": float(BEATS["var"]), "marker": "var_controversy"},
                  {"t_offset": float(BEATS["goal"]), "marker": "goal"},
                  {"t_offset": float(BEATS["full_time"]), "marker": "full_time"}]

    items.sort(key=lambda i: i["t_offset"])

    repo_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    out_path = out_path or os.path.join(repo_root, "data", "replay", "replay_twitter_sim.json")
    payload = {
        "meta": {
            "match_id": match_id,
            "captured_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            "description": (f"SIMULATED Twitter/X stream for {home} vs {away} "
                            f"({len([i for i in items if 'text' in i])} tweets; X API has no free tier — "
                            f"synthetic text, real downstream NLP). Seeded, reproducible."),
            "simulated": True,
        },
        "items": items,
    }
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=1)
    print(f"Generated {n} simulated tweets -> {out_path}")
    print("Replay alongside YouTube data with two /replay/control start calls (same speed).")
    return out_path


if __name__ == "__main__":
    p = argparse.ArgumentParser(description="Generate a labeled simulated Twitter stream replay file")
    p.add_argument("--match-id", default="m_001")
    p.add_argument("--home", default="Brazil")
    p.add_argument("--away", default="Argentina")
    p.add_argument("--tweets", type=int, default=600)
    p.add_argument("--markers", action="store_true",
                   help="embed moment markers (use when replaying this file alone)")
    p.add_argument("--out", default=None)
    a = p.parse_args()
    generate(a.match_id, a.home, a.away, a.tweets, a.markers, a.out)
