from pathlib import Path
import feedparser
from transformers import pipeline
import asyncio
import edge_tts
from datetime import datetime
from datetime import date
import re
import random
import json
from src.utils import clean_text, slugify

# -------------------------------

DATA_DIR = Path("data")
RAW_DIR = DATA_DIR / "raw"
AUDIO_DIR = DATA_DIR / "audio"
SUMMARY_DIR = DATA_DIR / "summaries"

RAW_DIR.mkdir(parents=True, exist_ok=True)
AUDIO_DIR.mkdir(parents=True, exist_ok=True)
SUMMARY_DIR.mkdir(parents=True, exist_ok=True)

EPISODES_FILE = DATA_DIR / "episodes.json"

episodes = []

if EPISODES_FILE.exists():
    text = EPISODES_FILE.read_text().strip()
    try:
        episodes = json.loads(text)
    except json.JSONDecodeError:
        print("Warning: episodes.json is invalid. Starting with empty history.")
        episodes = []

used_urls = {entry["article_url"] for entry in episodes}

today_str = date.today().isoformat()
today_episode = None

for entry in episodes:
    if entry["timestamp"].startswith(today_str):
        today_episode = entry
        break

# -------------------------------

print("Loading summarizer model (BART-large-CNN)...")

summarizer = pipeline(
    "summarization",
    model="facebook/bart-large-cnn"
)

# -------------------------------

RSS_FEEDS = {
    "science": {
        "weight": 4,
        "feeds": [
            "https://www.quantamagazine.org/feed",
            "https://feeds.nature.com/nature/rss/current",
            "https://www.sciencedaily.com/rss/all.xml"
        ]
    },
    "ideas": {
        "weight": 1,
        "feeds": [
            "https://aeon.co/feed"
        ]
    },
    "history": {
        "weight": 1,
        "feeds": [
            "https://feeds.bbci.co.uk/history/rss.xml"
        ]
    },
    "psychology": {
        "weight": 2,
        "feeds": [
            "https://www.sciencedaily.com/rss/mind_brain.xml"
        ]
    }
}

# if today_episode:
#     print("Today's episode already exists.")
#     print("Title:", today_episode["title"])
#     print("Audio:", today_episode["audio_file"])
#     exit()

weighted_topics = []
for topic, info in RSS_FEEDS.items():
    weighted_topics.extend([topic] * info["weight"])

topic = random.choice(weighted_topics)
feed_url = random.choice(RSS_FEEDS[topic]["feeds"])

feed = feedparser.parse(feed_url)

if not feed.entries:
    raise Exception("No feed entries found. Check RSS URL.")

print(f"Topic: {topic}")
print(f"Feed: {feed_url}")

valid_entries = [
    entry for entry in feed.entries
    if entry.get("summary") 
    and entry.get("link") 
    and entry.link not in used_urls
]

if not valid_entries:
    raise Exception("No new usable entries found (all used or invalid).")

entry = random.choice(valid_entries)
title = entry.title
if "content" in entry:
    content = entry.content[0].value
else:
    content = entry.get("summary", "")
content = clean_text(content)

# Content quality will be solved later

print(f"\nUsing article: {title}\n")

# -------------------------------

timestamp = datetime.now().strftime("%Y-%m-%d")
title_slug = slugify(title)
base_name = f"{timestamp}_{topic}_{title_slug}"

raw_file = RAW_DIR / f"{base_name}_raw.txt"
raw_file.write_text(content, encoding="utf-8")
print(f"Saved raw article to {raw_file}")

# -------------------------------

print("Summarizing article...")

summary_text = summarizer(
    content,
    max_length=300,
    min_length=120,
    do_sample=False
)[0]["summary_text"]

print("\nSummary created!\n")

summary_file = SUMMARY_DIR / f"{base_name}_summary.txt"
summary_file.write_text(summary_text, encoding="utf-8")
print(f"Saved text to {summary_file}")

# -------------------------------

OUTPUT_AUDIO = str(AUDIO_DIR / f"{base_name}_lecture.mp3")

async def tts():
    communicate = edge_tts.Communicate(summary_text, voice="en-US-JennyNeural")
    await communicate.save(OUTPUT_AUDIO)

print("Generating audio...")
asyncio.run(tts())
print(f"Saved audio to {OUTPUT_AUDIO}")

# -------------------------------

episode_metadata = {
    "timestamp": timestamp,
    "title": title,
    "source": feed_url,
    "article_url": entry.link,
    "topic": topic,
    "summary_file": str(summary_file),
    "audio_file": OUTPUT_AUDIO
}

episodes.append(episode_metadata)

EPISODES_FILE.write_text(
    json.dumps(episodes, indent=2),
    encoding="utf-8"
)

