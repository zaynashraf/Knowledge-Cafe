import random
import feedparser

def select_feed(rss_feeds):
    weighted_topics = []
    for topic, info in rss_feeds.items():
        weighted_topics.extend([topic] * info["weight"])

    topic = random.choice(weighted_topics)
    feed_url = random.choice(rss_feeds[topic]["feeds"])

    feed = feedparser.parse(feed_url)

    return topic, feed_url, feed