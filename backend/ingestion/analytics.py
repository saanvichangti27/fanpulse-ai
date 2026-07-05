import json
from datetime import datetime, timezone, timedelta
from sqlalchemy import text
from ..contracts import MOMENTUM_MIN_MESSAGES_5M, AROUSAL

def get_kpis(session, match_id: str):
    # kpis: total_mentions, positive_pct, negative_pct, neutral_pct
    # top_emotion, excitement_score, most_active_region, mentions_per_min
    sql = text("""
        SELECT 
            COUNT(*) as total,
            SUM(CASE WHEN sentiment = 'positive' THEN 1 ELSE 0 END) as pos,
            SUM(CASE WHEN sentiment = 'negative' THEN 1 ELSE 0 END) as neg,
            SUM(CASE WHEN sentiment = 'neutral' THEN 1 ELSE 0 END) as neu
        FROM messages 
        WHERE match_id = :match_id
    """)
    res = session.execute(sql, {"match_id": match_id}).fetchone()
    if not res or res.total == 0:
        return None
        
    total = res.total
    
    # Emotion counts to find top emotion
    sql_emo = text("""
        SELECT emotion, COUNT(*) as cnt 
        FROM messages 
        WHERE match_id = :match_id 
        GROUP BY emotion 
        ORDER BY cnt DESC LIMIT 1
    """)
    top_emo = session.execute(sql_emo, {"match_id": match_id}).fetchone()
    top_emotion = top_emo.emotion if top_emo else "neutral"
    
    # Region
    sql_reg = text("""
        SELECT country, COUNT(*) as cnt
        FROM messages
        WHERE match_id = :match_id AND country IS NOT NULL
        GROUP BY country
        ORDER BY cnt DESC LIMIT 1
    """)
    top_reg = session.execute(sql_reg, {"match_id": match_id}).fetchone()
    most_active_region = top_reg.country if top_reg else "Unknown"
    
    # Mentions per min
    sql_time = text("""
        SELECT MIN(created_at) as min_t, MAX(created_at) as max_t
        FROM messages WHERE match_id = :match_id
    """)
    t_res = session.execute(sql_time, {"match_id": match_id}).fetchone()
    mentions_per_min = 0
    if t_res and t_res.min_t and t_res.max_t:
        min_dt = datetime.fromisoformat(t_res.min_t.replace('Z', '+00:00'))
        max_dt = datetime.fromisoformat(t_res.max_t.replace('Z', '+00:00'))
        mins = (max_dt - min_dt).total_seconds() / 60.0
        mentions_per_min = int(total / mins) if mins > 1 else total

    # Momentum for excitement score
    mom = get_momentum(session, match_id)
    if mom:
        excitement_score = 100 * (0.6 * mom["arousal"] + 0.4 * min(mom["volume_ratio"]/3.0, 1.0))
    else:
        excitement_score = 0.0

    return {
        "match_id": match_id,
        "total_mentions": total,
        "positive_pct": round(res.pos / total * 100, 1),
        "negative_pct": round(res.neg / total * 100, 1),
        "neutral_pct": round(res.neu / total * 100, 1),
        "top_emotion": top_emotion,
        "excitement_score": round(excitement_score, 1),
        "most_active_region": most_active_region,
        "mentions_per_min": mentions_per_min,
        "computed_at": datetime.now(timezone.utc).isoformat() + "Z"
    }

def get_timeline(session, match_id: str, bucket_s: int = 30):
    sql = text("""
        SELECT 
            strftime('%Y-%m-%dT%H:%M:00Z', created_at) as ts_minute,
            (CAST(strftime('%S', created_at) AS INTEGER) / :bucket_s) * :bucket_s as ts_sec,
            COUNT(*) as total,
            SUM(CASE WHEN sentiment = 'positive' THEN 1 ELSE 0 END) as pos,
            SUM(CASE WHEN sentiment = 'negative' THEN 1 ELSE 0 END) as neg,
            SUM(CASE WHEN sentiment = 'neutral' THEN 1 ELSE 0 END) as neu
        FROM messages
        WHERE match_id = :match_id
        GROUP BY ts_minute, ts_sec
        ORDER BY ts_minute, ts_sec
    """)
    # (SQLite lacks full date_trunc, using strftime grouping approximation)
    # A cleaner python-side aggregation is safer for small datasets.
    
    # We will fetch all and group in python for perfect 30s buckets
    sql_all = text("SELECT created_at, sentiment, emotion FROM messages WHERE match_id = :match_id ORDER BY created_at")
    rows = session.execute(sql_all, {"match_id": match_id}).fetchall()
    
    if not rows:
        return []
        
    buckets = {}
    for r in rows:
        dt = datetime.fromisoformat(r.created_at.replace('Z', '+00:00'))
        # Round down to nearest bucket_s
        secs = (dt.minute * 60 + dt.second) // bucket_s * bucket_s
        b_dt = dt.replace(minute=(secs // 60) % 60, second=secs % 60, microsecond=0)
        b_str = b_dt.isoformat().replace("+00:00", "Z")
        
        if b_str not in buckets:
            buckets[b_str] = {"total": 0, "pos": 0, "neg": 0, "neu": 0, "emotions": {}}
        b = buckets[b_str]
        b["total"] += 1
        if r.sentiment == "positive": b["pos"] += 1
        elif r.sentiment == "negative": b["neg"] += 1
        else: b["neu"] += 1
        b["emotions"][r.emotion] = b["emotions"].get(r.emotion, 0) + 1
        
    # Get moments
    sql_mom = text("SELECT event_tag, detected_at FROM moments WHERE match_id = :match_id")
    moments = session.execute(sql_mom, {"match_id": match_id}).fetchall()
    
    points = []
    for ts, b in buckets.items():
        top_emo = max(b["emotions"].keys(), key=lambda k: b["emotions"][k])
        
        # Check if a moment falls in this bucket
        tag = None
        b_dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
        for m in moments:
            m_dt = datetime.fromisoformat(m.detected_at.replace("Z", "+00:00"))
            if b_dt <= m_dt < b_dt + timedelta(seconds=bucket_s):
                tag = m.event_tag
                break
                
        points.append({
            "ts": ts,
            "positive_pct": round(b["pos"]/b["total"]*100, 1),
            "negative_pct": round(b["neg"]/b["total"]*100, 1),
            "neutral_pct": round(b["neu"]/b["total"]*100, 1),
            "mentions": b["total"],
            "top_emotion": top_emo,
            "event_tag": tag
        })
    return points

def get_heatmap(session, match_id: str):
    sql = text("""
        SELECT country, 
               COUNT(*) as cnt,
               SUM(CASE WHEN sentiment = 'positive' THEN sentiment_score WHEN sentiment = 'negative' THEN -sentiment_score ELSE 0 END) as sent_sum
        FROM messages
        WHERE match_id = :match_id AND country IS NOT NULL
        GROUP BY country
    """)
    rows = session.execute(sql, {"match_id": match_id}).fetchall()
    if not rows:
        return None
        
    countries = []
    for r in rows:
        # Get dominant emotion for this country
        sql_emo = text("SELECT emotion, COUNT(*) as e_cnt FROM messages WHERE match_id = :match_id AND country = :c GROUP BY emotion ORDER BY e_cnt DESC LIMIT 1")
        e_row = session.execute(sql_emo, {"match_id": match_id, "c": r.country}).fetchone()
        
        countries.append({
            "country_code": r.country,
            "avg_sentiment": round(r.sent_sum / r.cnt, 2),
            "dominant_emotion": e_row.emotion if e_row else "neutral",
            "mentions": r.cnt
        })
    return {"match_id": match_id, "computed_at": datetime.now(timezone.utc).isoformat() + "Z", "countries": countries}

def get_topics(session, match_id: str):
    sql = text("SELECT topics_json, created_at FROM messages WHERE match_id = :match_id")
    rows = session.execute(sql, {"match_id": match_id}).fetchall()
    
    now = datetime.now(timezone.utc)
    recent_counts = {}
    old_counts = {}
    
    for r in rows:
        dt = datetime.fromisoformat(r.created_at.replace("Z", "+00:00"))
        topics = json.loads(r.topics_json)
        
        is_recent = (now - dt).total_seconds() <= 300 # last 5 mins
        for t in topics:
            if is_recent:
                recent_counts[t] = recent_counts.get(t, 0) + 1
            else:
                old_counts[t] = old_counts.get(t, 0) + 1
                
    results = []
    for t, cnt in sorted(recent_counts.items(), key=lambda x: x[1], reverse=True)[:10]:
        old_cnt = old_counts.get(t, 0)
        trend = "flat"
        if cnt > old_cnt * 1.2: trend = "up"
        elif cnt < old_cnt * 0.8: trend = "down"
        
        results.append({
            "label": t,
            "mentions": cnt,
            "trend": trend
        })
    return results

def get_momentum(session, match_id: str):
    now = datetime.now(timezone.utc)
    m1 = now - timedelta(minutes=1)
    m5 = now - timedelta(minutes=5)
    
    sql = text("""
        SELECT created_at, emotion, sentiment
        FROM messages 
        WHERE match_id = :match_id AND created_at >= :m5
    """)
    rows = session.execute(sql, {"match_id": match_id, "m5": m5.isoformat().replace("+00:00", "Z")}).fetchall()
    
    total_5m = len(rows)
    if total_5m < MOMENTUM_MIN_MESSAGES_5M:
        return None
        
    vol_1m = sum(1 for r in rows if datetime.fromisoformat(r.created_at.replace("Z", "+00:00")) >= m1)
    
    trailing_5m_avg = max(total_5m / 5.0, 1.0)
    volume_ratio = vol_1m / trailing_5m_avg
    
    # Emotion distribution in 1m for dominant emotion
    emos_1m = {}
    pos_1m = 0
    arousal_sum = 0
    for r in rows:
        if datetime.fromisoformat(r.created_at.replace("Z", "+00:00")) >= m1:
            emos_1m[r.emotion] = emos_1m.get(r.emotion, 0) + 1
            arousal_sum += AROUSAL.get(r.emotion, 0.1)
            if r.sentiment == "positive":
                pos_1m += 1
                
    dominant_emotion = max(emos_1m.keys(), key=lambda k: emos_1m[k]) if emos_1m else "neutral"
    arousal = arousal_sum / vol_1m if vol_1m > 0 else 0.0
    positive_pct_1m = (pos_1m / vol_1m * 100) if vol_1m > 0 else 0.0
    
    # previous 2 mins for delta (simplified vs strictly exactly 2 min ago slice, just taking older half of 5m)
    m2 = now - timedelta(minutes=2)
    m4 = now - timedelta(minutes=4)
    pos_old = 0
    vol_old = 0
    for r in rows:
        dt = datetime.fromisoformat(r.created_at.replace("Z", "+00:00"))
        if m4 <= dt < m2:
            vol_old += 1
            if r.sentiment == "positive": pos_old += 1
    
    pos_pct_old = (pos_old / vol_old * 100) if vol_old > 0 else positive_pct_1m
    sentiment_delta_pp = positive_pct_1m - pos_pct_old
    
    # Top topics and countries for snapshot
    sql_tc = text("""
        SELECT topics_json, country
        FROM messages 
        WHERE match_id = :match_id AND created_at >= :m1
    """)
    tc_rows = session.execute(sql_tc, {"match_id": match_id, "m1": m1.isoformat().replace("+00:00", "Z")}).fetchall()
    topics_count = {}
    country_count = {}
    for r in tc_rows:
        for t in json.loads(r.topics_json):
            topics_count[t] = topics_count.get(t, 0) + 1
        if r.country:
            country_count[r.country] = country_count.get(r.country, 0) + 1
            
    top_topics = [k for k, v in sorted(topics_count.items(), key=lambda x: x[1], reverse=True)[:5]]
    top_countries = [k for k, v in sorted(country_count.items(), key=lambda x: x[1], reverse=True)[:5]]
    
    return {
        "match_id": match_id,
        "volume_1m": vol_1m,
        "volume_5m": total_5m,
        "volume_ratio": round(volume_ratio, 2),
        "dominant_emotion": dominant_emotion,
        "arousal": round(arousal, 2),
        "positive_pct": round(positive_pct_1m, 1),
        "sentiment_delta_pp": round(sentiment_delta_pp, 1),
        "top_topics": top_topics,
        "top_countries": top_countries,
        "computed_at": now.isoformat().replace("+00:00", "Z")
    }

def get_country_volumes(session, match_id: str):
    sql = text("""
        SELECT country, COUNT(*) as cnt
        FROM messages
        WHERE match_id = :match_id AND country IS NOT NULL
        GROUP BY country
    """)
    rows = session.execute(sql, {"match_id": match_id}).fetchall()
    return {r.country: r.cnt for r in rows}
