from __future__ import annotations
from flask import Flask, request, jsonify
import csv, io, re
from typing import List, Dict, Any
from datetime import datetime

app = Flask(__name__)



RISKY_KEYWORDS = [
    "boycott", "hate", "genocide", "terror", "traitor", "anti-india", "anti india",
    "separatist", "attack", "riot", "fake news", "propaganda", "kill", "burn",
    "target", "spam", "troll farm", "bot network", "phishing", "scam", "giveaway",
    "win iphone", "free crypto", "login to claim"
]

SAFE_KEYWORDS = [
    "education", "research", "awareness", "help", "support", "donate", "neutral",
    "balanced", "fact-check", "informative", "clarification", "community", "event",
    "job", "weather", "update", "review", "positive"
]

PLATFORM_KEYWORDS = {
    "Twitter": ["twitter", "tweet", "x "],
    "Facebook": ["facebook", "fb"],
    "Instagram": ["instagram", "insta"],
    "Reddit": ["reddit", "r/"],
    "LinkedIn": ["linkedin"],
    "YouTube": ["youtube", "youtu.be"]
}

# Weights
W_RISKY = 2.0
W_SAFE = -1.0
W_HAS_LINK = 1.5
W_MANY_HASHTAGS = 1.0
W_ALLCAPS_STREAK = 1.0
W_REPEAT_WORD = 0.5
W_LONG_POST = 0.5

THRESHOLDS = {"safe": -0.5, "neutral_upper": 1.5}


RECENT_LOGS: List[Dict[str, Any]] = []    
LAST_SUMMARY: Dict[str, Any] = {}         

MAX_LOGS = 200


def normalize_text(t: str) -> str:
    if not isinstance(t, str): return ""
    t = t.strip()
    t = re.sub(r"\s+", " ", t)
    return t

def count_occurrences(text: str, lexicon: List[str]) -> int:
    text_l = text.lower()
    return sum(text_l.count(w) for w in lexicon)

def suspicious_signals(text: str):
    score = 0.0
    details = {"link": False, "hashtags": 0, "allcaps_streak": False, "repeat_word": False, "long_post": False}

    if re.search(r"https?://", text):
        score += W_HAS_LINK
        details["link"] = True

    hashtags = len(re.findall(r"[#@]", text))
    details["hashtags"] = hashtags
    if hashtags >= 3:
        score += W_MANY_HASHTAGS

    if re.search(r"([A-Z]{4,}\s*){3,}", text):
        score += W_ALLCAPS_STREAK
        details["allcaps_streak"] = True

    if re.search(r"\b(\w+)\b\s*\1\b", text, flags=re.I):
        score += W_REPEAT_WORD
        details["repeat_word"] = True

    if len(text) > 280:
        score += W_LONG_POST
        details["long_post"] = True

    return score, details

def classify_text(text: str) -> Dict[str, Any]:
    t = normalize_text(text)
    base = 0.0

    risky_hits = count_occurrences(t, RISKY_KEYWORDS)
    safe_hits = count_occurrences(t, SAFE_KEYWORDS)
    base += risky_hits * W_RISKY
    base += safe_hits * W_SAFE

    sig_score, sig_detail = suspicious_signals(t)
    total = base + sig_score

    if total <= THRESHOLDS["safe"]:
        label = "SAFE"
    elif total < THRESHOLDS["neutral_upper"]:
        label = "NEUTRAL"
    else:
        label = "SUSPICIOUS"

    return {
        "text": (t[:200] + "…") if len(t) > 200 else t,
        "score": round(total, 2),
        "risky_hits": risky_hits,
        "safe_hits": safe_hits,
        "signals": sig_detail,
        "label": label
    }

def detect_platforms(text: str) -> List[str]:
    found = []
    tl = text.lower()
    for p, kw_list in PLATFORM_KEYWORDS.items():
        for kw in kw_list:
            if kw in tl:
                found.append(p)
                break
    return found


def parse_csv(file_bytes: bytes):
    try:
        decoded = file_bytes.decode("utf-8")
    except UnicodeDecodeError:
        decoded = file_bytes.decode("latin-1", errors="ignore")
    buf = io.StringIO(decoded)
    reader = csv.DictReader(buf)
    candidates = ["text", "message", "post", "content", "body"]
    rows = []
    for i, row in enumerate(reader, start=1):
        text_val = None
        for c in candidates:
            if c in row and row[c] and row[c].strip():
                text_val = row[c]
                break
        if text_val is None:
            if row:
                text_val = next(iter(row.values()))
            else:
                text_val = ""
        rows.append({"id": row.get("id", i), "text": text_val, "raw": row})
    return rows

def aggregate_and_store(rows: List[Dict[str, Any]]):
    global RECENT_LOGS, LAST_SUMMARY
    safe = suspicious = neutral = 0
    platform_counts = {k: 0 for k in PLATFORM_KEYWORDS.keys()}

    results = []
    for r in rows:
        text = r.get("text", "") or ""
        cls = classify_text(text)
        label = cls["label"]
        if label == "SAFE":
            safe += 1
        elif label == "SUSPICIOUS":
            suspicious += 1
        else:
            neutral += 1

        
        plats = detect_platforms(text)
        if plats:
            for p in plats:
                platform_counts[p] = platform_counts.get(p, 0) + 1
        else:
            pass

       
        RECENT_LOGS.append({
            "ts": datetime.utcnow().isoformat() + "Z",
            "text": cls["text"],
            "label": label
        })
        results.append({**cls, "id": r.get("id")})

   
    if len(RECENT_LOGS) > MAX_LOGS:
        RECENT_LOGS = RECENT_LOGS[-MAX_LOGS:]

    
    total_platform_hits = sum(platform_counts.values()) or 1
    platform_pct = {k: round((v / total_platform_hits) * 100) for k, v in platform_counts.items()}

    LAST_SUMMARY = {
        "total": safe + suspicious + neutral,
        "safe": safe,
        "suspicious": suspicious,
        "neutral": neutral,
        "platforms": platform_pct,
        "results": results
    }
    return LAST_SUMMARY


@app.get("/health")
def health():
    return {"ok": True, "service": "csv-analyzer", "version": "1.1"}

@app.post("/analyze")
def analyze():
    """
    Accepts:
     - multipart/form-data: file=<csv>
     - JSON: {"rows": [{"id":1,"text":"..."} , ...]}
    Returns: summary (safe/suspicious/neutral counts, platforms, results)
    """
    payload_rows = []
    if "file" in request.files:
        f = request.files["file"]
        data = f.read()
        payload_rows = parse_csv(data)
    else:
        data = request.get_json(silent=True) or {}
        rows_in = data.get("rows", [])
        for i, r in enumerate(rows_in, start=1):
            payload_rows.append({"id": r.get("id", i), "text": r.get("text", ""), "raw": r})

    if not payload_rows:
        return jsonify({"ok": False, "error": "No data provided. Upload CSV as 'file' or JSON {rows:[...]}" }), 400

    summary = aggregate_and_store(payload_rows)
    return jsonify({"ok": True, "summary": summary})

@app.get("/stats")
def stats():
    """Return last computed summary in frontend-friendly shape."""
    if not LAST_SUMMARY:
        
        return jsonify({"ok": True, "safe": 0, "suspicious": 0, "neutral": 0, "platforms": {}, "results": []})
    
    platforms = LAST_SUMMARY.get("platforms", {})
    for k in PLATFORM_KEYWORDS.keys():
        platforms.setdefault(k, 0)
    return jsonify({
        "ok": True,
        "safe": LAST_SUMMARY["safe"],
        "suspicious": LAST_SUMMARY["suspicious"],
        "neutral": LAST_SUMMARY["neutral"],
        "platforms": platforms,
        "results": LAST_SUMMARY.get("results", [])
    })

@app.get("/logs")
def logs():
    """Return recent log lines (most recent last)."""
    return jsonify({"ok": True, "logs": RECENT_LOGS[-100:]})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=True)
