import json
import os

BASE_DIR = os.path.dirname(os.path.dirname(__file__))  # out of logic/ folder
SONG_DIR = os.path.join(BASE_DIR, "song_data")
ALL_SONGS_PATH = os.path.join(SONG_DIR, "all_songs.json")


class SongManager:
    def __init__(self):
        self.song_dir = SONG_DIR
        self.all_songs_path = ALL_SONGS_PATH
        self.songs = {}
        self.load_songs()

    # -----------------------------
    # --- Load / Save -------------
    # -----------------------------
    def load_songs(self):
        """Load all songs from individual song JSONs, then sync all_songs.json."""
        self.songs = {}
        os.makedirs(self.song_dir, exist_ok=True)

        for filename in os.listdir(self.song_dir):
            if not filename.startswith("song_") or not filename.endswith(".json"):
                continue
            path = os.path.join(self.song_dir, filename)
            try:
                with open(path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                number = str(data.get("number", ""))
                if number:
                    self.songs[number] = data
            except Exception as e:
                print(f"[WARNING] Could not load {filename}: {e}")

    def save_songs(self):
        """Save each song to its own JSON file and update all_songs.json."""
        os.makedirs(self.song_dir, exist_ok=True)

        # Track which files should exist after save
        expected_files = set()

        for number, song in self.songs.items():
            filename = f"song_{number}.json"
            path = os.path.join(self.song_dir, filename)
            with open(path, "w", encoding="utf-8") as f:
                json.dump(song, f, indent=4, ensure_ascii=False)
            expected_files.add(filename)

        # Remove individual JSONs for deleted songs
        for filename in os.listdir(self.song_dir):
            if filename.startswith("song_") and filename.endswith(".json"):
                if filename not in expected_files:
                    os.remove(os.path.join(self.song_dir, filename))
                    print(f"[INFO] Deleted removed song file: {filename}")

        # Write all_songs.json as a combined index
        with open(self.all_songs_path, "w", encoding="utf-8") as f:
            json.dump(self.songs, f, indent=4, ensure_ascii=False)

        print(f"[INFO] Saved {len(self.songs)} songs.")

    # -----------------------------
    # --- Song CRUD ---------------
    # -----------------------------
    def add_song(self, number, title="New Song"):
        if number in self.songs:
            raise ValueError(f"Song number {number} already exists.")
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

    # -----------------------------
    # --- Verse CRUD --------------
    # -----------------------------
    def add_verse(self, song_number):
        song = self.songs[song_number]
        next_verse = len(song["verses"]) + 1
        song["verses"].append({"verse": next_verse, "text": ""})
        return next_verse - 1  # return index

    def update_verse(self, song_number, idx, text=None, verse_number=None):
        verse = self.songs[song_number]["verses"][idx]
        if text is not None:
            verse["text"] = text
        if verse_number is not None:
            verse["verse"] = verse_number
            self.songs[song_number]["verses"].sort(key=lambda v: v["verse"])

    def delete_verse(self, song_number, idx):
        self.songs[song_number]["verses"].pop(idx)

    # -----------------------------
    # --- Copyright CRUD ----------
    # -----------------------------
    def add_copyright(self, song_number, text):
        self.songs[song_number]["copyright"].append(text)

    def delete_copyright(self, song_number, idx):
        self.songs[song_number]["copyright"].pop(idx)

    # -----------------------------
    # --- Sorting -----------------
    # -----------------------------
    @staticmethod
    def song_sort_key(item):
        num_str = item[0]
        digits = ''.join(c for c in num_str if c.isdigit())
        letters = ''.join(c for c in num_str if c.isalpha())
        return (int(digits) if digits else 0, letters)

    def get_sorted_songs(self):
        return sorted(self.songs.items(), key=self.song_sort_key)