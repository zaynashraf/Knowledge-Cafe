import json

def load_episodes(path):
    episodes = []

    if path.exists():
        text = path.read_text().strip()
        try:
            episodes = json.loads(text)
        except json.JSONDecodeError:
            print("Warning: episodes.json is invalid. Starting with empty history.")
            episodes = []

    return episodes

def save_episodes(path, episodes, episode_metadata):
    episodes.append(episode_metadata)
    path.write_text(json.dumps(episodes, indent=2), encoding="utf-8")