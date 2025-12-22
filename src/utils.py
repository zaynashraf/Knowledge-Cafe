import re

def slugify(text, max_length=60):
    text = text.lower()
    text = re.sub(r'[^a-z0-9]+', '-', text)
    text = re.sub(r"\s+", "-", text).strip("-")
    return text[:max_length]

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