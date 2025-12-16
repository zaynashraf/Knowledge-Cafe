from pathlib import Path
import feedparser
from transformers import pipeline
import asyncio
import edge_tts
from datetime import datetime
import re
import random


def clean_text(text):
    text = re.sub(r"http\S+", "", text)

    boilerplate_phrases = [
        "Read more",
        "Continue reading",
        "Visit the full article",
        "Click here"
    ]

    for phrase in boilerplate_phrases:
        text = text.replace(phrase, "")

    return text.strip()



DATA_DIR = Path("data")
RAW_DIR = DATA_DIR / "raw"
AUDIO_DIR = DATA_DIR / "audio"
SUMMARY_DIR = DATA_DIR / "summaries"

RAW_DIR.mkdir(parents=True, exist_ok=True)
AUDIO_DIR.mkdir(parents=True, exist_ok=True)
SUMMARY_DIR.mkdir(parents=True, exist_ok=True)

# -------------------------------

print("Loading summarizer model (BART-large-CNN)...")

summarizer = pipeline(
    "summarization",
    model="facebook/bart-large-cnn"
)

# -------------------------------

RSS_FEEDS = {
    "science": [
        "https://www.quantamagazine.org/feed",
        "https://feeds.nature.com/nature/rss/current"
        "https://www.sciencedaily.com/rss/all.xml"
    ],
    "philosophy": [
        "https://aeon.co/feed"
    ],
    "history": [
        "https://feeds.bbci.co.uk/history/rss.xml"
    ],
    "psychology": [
        "https://www.sciencedaily.com/rss/mind_brain.xml"
    ]
}

topic = random.choice(list(RSS_FEEDS.keys()))
feed_url = random.choice(RSS_FEEDS[topic])

feed = feedparser.parse(feed_url)

if not feed.entries:
    raise Exception("No feed entries found. Check RSS URL.")

print(f"Topic: {topic}")
print(f"Feed: {feed_url}")

valid_entries = [
    entry for entry in feed.entries
    if entry.get("summary") or entry.get("content")
]

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

timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
raw_file = RAW_DIR / f"{timestamp}_raw.txt"
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

summary_file = SUMMARY_DIR / f"{timestamp}_summary.txt"
summary_file.write_text(summary_text, encoding="utf-8")
print(f"Saved text to {summary_file}")


# -------------------------------

OUTPUT_AUDIO = str(AUDIO_DIR / f"{timestamp}_lecture.mp3")

async def tts():
    communicate = edge_tts.Communicate(summary_text, voice="en-US-JennyNeural")
    await communicate.save(OUTPUT_AUDIO)

print("Generating audio...")
asyncio.run(tts())
print(f"Saved audio to {OUTPUT_AUDIO}")
