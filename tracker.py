import os
import json
from datetime import datetime
from threading import Lock

BASE_DIR = os.path.dirname(__file__)
TRACKER_FILE = os.path.join(BASE_DIR, "song_usage.json")

_lock = Lock()


# ---------------------------------------------------------
# Core File Handling
# ---------------------------------------------------------

def _load_tracker():
    if not os.path.exists(TRACKER_FILE):
        return {"songs": {}}

    with open(TRACKER_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def _save_tracker(data):
    temp_file = TRACKER_FILE + ".tmp"

    with open(temp_file, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)

    os.replace(temp_file, TRACKER_FILE)


# ---------------------------------------------------------
# Public API
# ---------------------------------------------------------

def update_tracker(song_number, verses):
    """
    song_number: int or str
    verses: list of verse numbers (ints)
    """

    with _lock:
        data = _load_tracker()

        song_number = str(song_number)

        # Initialize song entry if missing
        if song_number not in data["songs"]:
            data["songs"][song_number] = {
                "total_sung": 0,
                "verses": {}
            }

        song_entry = data["songs"][song_number]

        # Increment song count
        song_entry["total_sung"] += 1

        # Track verse usage
        for verse in verses:
            verse = str(verse)

            if verse not in song_entry["verses"]:
                song_entry["verses"][verse] = 0

            song_entry["verses"][verse] += 1

        # Optional metadata
        song_entry["last_sung"] = datetime.now().strftime("%Y-%m-%d")

        _save_tracker(data)


def get_tracker_data():
    return _load_tracker()