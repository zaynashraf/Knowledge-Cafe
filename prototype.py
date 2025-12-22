from pathlib import Path
from datetime import datetime
from datetime import date
import random
from src.utils import clean_text, slugify
from src.memory import load_episodes, save_episodes
from src.feeds import select_feed
from src.summarize import summarize
from src.tts import speak

# -------------------------------

DATA_DIR = Path("data")
RAW_DIR = DATA_DIR / "raw"
AUDIO_DIR = DATA_DIR / "audio"
SUMMARY_DIR = DATA_DIR / "summaries"

RAW_DIR.mkdir(parents=True, exist_ok=True)
AUDIO_DIR.mkdir(parents=True, exist_ok=True)
SUMMARY_DIR.mkdir(parents=True, exist_ok=True)

EPISODES_FILE = DATA_DIR / "episodes.json"

episodes = load_episodes(EPISODES_FILE)

used_urls = {entry["article_url"] for entry in episodes}

today_str = date.today().isoformat()
today_episode = None

for entry in episodes:
    if entry["timestamp"].startswith(today_str):
        today_episode = entry
        break

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

topic, feed_url, feed = select_feed(RSS_FEEDS)

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

summary_text = summarize(content)

print("\nSummary created!\n")

summary_file = SUMMARY_DIR / f"{base_name}_summary.txt"
summary_file.write_text(summary_text, encoding="utf-8")
print(f"Saved text to {summary_file}")

# -------------------------------

OUTPUT_AUDIO = str(AUDIO_DIR / f"{base_name}_lecture.mp3")

print("Generating audio...")
speak(summary_text, OUTPUT_AUDIO)
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

save_episodes(EPISODES_FILE, episodes, episode_metadata)

