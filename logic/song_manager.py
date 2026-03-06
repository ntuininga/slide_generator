import json
import os

class SongManager:
    def __init__(self, json_path="song_data/all_songs.json"):
        self.json_path = json_path
        self.songs = {}
        self.load_songs()

    def load_songs(self):
        try:
            with open(self.json_path, "r") as f:
                self.songs = json.load(f)
        except FileNotFoundError:
            self.songs = {}

    def save_songs(self):
        os.makedirs(os.path.dirname(self.json_path), exist_ok=True)
        with open(self.json_path, "w") as f:
            json.dump(self.songs, f, indent=4)

    # --- Song operations ---
    def add_song(self, number, title="New Song"):
        if number in self.songs:
            raise ValueError("Song number already exists")
        self.songs[number] = {
            "number": number,
            "title": title,
            "verses": [],
            "refrain": None,
            "copyright": []
        }

    def delete_song(self, number):
        if number in self.songs:
            del self.songs[number]

    # --- Verse operations ---
    def add_verse(self, song_number):
        song = self.songs[song_number]
        next_verse = len(song["verses"]) + 1
        song["verses"].append({"verse": next_verse, "text": ""})
        return next_verse - 1  # index

    def update_verse(self, song_number, idx, text=None, verse_number=None):
        verse = self.songs[song_number]["verses"][idx]
        if text is not None:
            verse["text"] = text
        if verse_number is not None:
            verse["verse"] = verse_number
        # sort after number change
        self.songs[song_number]["verses"].sort(key=lambda v: v["verse"])

    def delete_verse(self, song_number, idx):
        self.songs[song_number]["verses"].pop(idx)

    # --- Copyright operations ---
    def add_copyright(self, song_number, text):
        self.songs[song_number]["copyright"].append(text)

    def delete_copyright(self, song_number, idx):
        self.songs[song_number]["copyright"].pop(idx)

    # --- Sorting ---
    @staticmethod
    def song_sort_key(item):
        num_str = item[0]
        digits = ''.join(c for c in num_str if c.isdigit())
        letters = ''.join(c for c in num_str if c.isalpha())
        return (int(digits) if digits else 0, letters)

    def get_sorted_songs(self):
        return sorted(self.songs.items(), key=self.song_sort_key)