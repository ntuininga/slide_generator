import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import json
import os

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
SONG_DIR = os.path.join(BASE_DIR, "song_data")
ALL_SONGS_PATH = os.path.join(SONG_DIR, "all_songs.json")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def load_songs():
    """Load all individual song_*.json files. Returns dict keyed by number."""
    songs = {}
    if not os.path.exists(SONG_DIR):
        return songs
    for fname in os.listdir(SONG_DIR):
        if fname.startswith("song_") and fname.endswith(".json"):
            path = os.path.join(SONG_DIR, fname)
            try:
                with open(path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                num = str(data.get("number", ""))
                if num:
                    songs[num] = data
            except Exception as e:
                print(f"[WARNING] Could not load {fname}: {e}")
    return songs


def save_songs(songs):
    """Save each song to its own file and regenerate all_songs.json."""
    os.makedirs(SONG_DIR, exist_ok=True)

    expected = set()
    for num, song in songs.items():
        fname = f"song_{num}.json"
        path = os.path.join(SONG_DIR, fname)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(song, f, indent=4, ensure_ascii=False)
        expected.add(fname)

    # Remove files for deleted songs
    for fname in os.listdir(SONG_DIR):
        if fname.startswith("song_") and fname.endswith(".json"):
            if fname not in expected:
                os.remove(os.path.join(SONG_DIR, fname))

    # Write combined index
    with open(ALL_SONGS_PATH, "w", encoding="utf-8") as f:
        json.dump(songs, f, indent=4, ensure_ascii=False)


def sort_key(num_str):
    digits  = ''.join(c for c in num_str if c.isdigit())
    letters = ''.join(c for c in num_str if c.isalpha())
    return (int(digits) if digits else 0, letters)


# ---------------------------------------------------------------------------
# Main window
# ---------------------------------------------------------------------------

class SongEditorWindow:
    def __init__(self, parent):
        self.win = tk.Toplevel(parent)
        self.win.title("Song Editor")
        self.win.minsize(900, 600)
        import platform
        if platform.system() == "Windows":
            self.win.state("zoomed")
        else:
            self.win.attributes("-zoomed", True)

        self.songs = load_songs()
        self._dirty = False          # unsaved changes flag
        self._current_num = None     # currently selected song number
        self._current_verse_idx = None  # index into song["verses"]

        self._build_ui()
        self._populate_song_list()

    # -----------------------------------------------------------------------
    # UI construction
    # -----------------------------------------------------------------------

    def _build_ui(self):
        # ── Top toolbar ────────────────────────────────────────────────────
        toolbar = tk.Frame(self.win, bd=1, relief="raised", pady=3)
        toolbar.pack(fill="x", side="top")

        tk.Button(toolbar, text="＋ New Song",  command=self._new_song,   width=12).pack(side="left", padx=4)
        tk.Button(toolbar, text="✕ Delete Song", command=self._delete_song, width=12).pack(side="left", padx=2)
        tk.Button(toolbar, text="💾 Save All",  command=self._save_all,
                  bg="#2e7d32", fg="white", width=12).pack(side="left", padx=10)

        self._status_var = tk.StringVar(value="")
        tk.Label(toolbar, textvariable=self._status_var, fg="#555").pack(side="right", padx=10)

        # ── Main area: left list | right detail ────────────────────────────
        pane = tk.PanedWindow(self.win, orient="horizontal", sashrelief="raised", sashwidth=5)
        pane.pack(fill="both", expand=True)

        # ── LEFT: song list ─────────────────────────────────────────────────
        left = tk.Frame(pane, width=380)
        pane.add(left, minsize=300)

        search_frame = tk.Frame(left)
        search_frame.pack(fill="x", padx=6, pady=6)
        tk.Label(search_frame, text="🔍").pack(side="left")
        self._search_var = tk.StringVar()
        self._search_var.trace_add("write", lambda *_: self._populate_song_list())
        tk.Entry(search_frame, textvariable=self._search_var).pack(side="left", fill="x", expand=True)

        self._song_list = tk.Listbox(left, activestyle="dotbox", selectbackground="#1565c0",
                                     selectforeground="white", font=("Courier", 10))
        sb = tk.Scrollbar(left, command=self._song_list.yview)
        self._song_list.config(yscrollcommand=sb.set)
        self._song_list.pack(side="left", fill="both", expand=True, padx=(6, 0), pady=(0, 6))
        sb.pack(side="left", fill="y", pady=(0, 6))
        self._song_list.bind("<<ListboxSelect>>", self._on_song_select)

        # ── RIGHT: song detail ──────────────────────────────────────────────
        right = tk.Frame(pane)
        pane.add(right, minsize=500)

        # Song metadata
        meta = tk.LabelFrame(right, text="Song Info", padx=8, pady=6)
        meta.pack(fill="x", padx=8, pady=(8, 4))

        tk.Label(meta, text="Number:").grid(row=0, column=0, sticky="w")
        self._num_var = tk.StringVar()
        tk.Entry(meta, textvariable=self._num_var, width=10).grid(row=0, column=1, sticky="w", padx=(4, 20))

        tk.Label(meta, text="Title:").grid(row=0, column=2, sticky="w")
        self._title_var = tk.StringVar()
        tk.Entry(meta, textvariable=self._title_var, width=40).grid(row=0, column=3, sticky="w", padx=4)

        tk.Label(meta, text="Refrain:").grid(row=1, column=0, sticky="nw", pady=(6, 0))
        self._refrain_text = tk.Text(meta, height=2, width=60, wrap="word")
        self._refrain_text.grid(row=1, column=1, columnspan=3, sticky="ew", padx=4, pady=(6, 0))

        tk.Button(meta, text="Apply Song Info", command=self._apply_song_info,
                  bg="#1565c0", fg="white").grid(row=2, column=3, sticky="e", pady=(6, 0))

        # Verses
        verse_area = tk.LabelFrame(right, text="Verses", padx=8, pady=6)
        verse_area.pack(fill="both", expand=True, padx=8, pady=4)

        # Left: verse list
        vlist_frame = tk.Frame(verse_area, width=280)
        vlist_frame.pack(side="left", fill="y")
        vlist_frame.pack_propagate(False)

        tk.Label(vlist_frame, text="Verse list:").pack(anchor="w")
        self._verse_list = tk.Listbox(vlist_frame, activestyle="dotbox",
                                      selectbackground="#1565c0", selectforeground="white")
        vsb = tk.Scrollbar(vlist_frame, command=self._verse_list.yview)
        self._verse_list.config(yscrollcommand=vsb.set)
        self._verse_list.pack(side="left", fill="both", expand=True)
        vsb.pack(side="left", fill="y")
        self._verse_list.bind("<<ListboxSelect>>", self._on_verse_select)

        vlist_btns = tk.Frame(vlist_frame)
        vlist_btns.pack(fill="x", pady=(4, 0))
        tk.Button(vlist_btns, text="＋ Add Verse", command=self._add_verse,
                  bg="#1565c0", fg="white").pack(side="left")
        tk.Button(vlist_btns, text="✕ Delete", command=self._delete_verse,
                  fg="red").pack(side="left", padx=4)

        # Right: verse editor
        vedit_frame = tk.Frame(verse_area)
        vedit_frame.pack(side="left", fill="both", expand=True, padx=(12, 0))

        tk.Label(vedit_frame, text="Verse number:").pack(anchor="w")
        self._verse_num_var = tk.StringVar()
        tk.Entry(vedit_frame, textvariable=self._verse_num_var, width=6).pack(anchor="w")

        tk.Label(vedit_frame, text="Verse text:").pack(anchor="w", pady=(8, 0))
        self._verse_text = tk.Text(vedit_frame, wrap="word", height=6)
        self._verse_text.pack(fill="both", expand=True)

        tk.Button(vedit_frame, text="✔ Update Verse", command=self._update_verse,
                  bg="#1565c0", fg="white", pady=4).pack(anchor="e", pady=(6, 0))

        # Copyright
        copy_area = tk.LabelFrame(right, text="Copyright", padx=8, pady=6)
        copy_area.pack(fill="x", padx=8, pady=(4, 8))

        self._copyright_list = tk.Listbox(copy_area, height=3)
        self._copyright_list.pack(fill="x")

        copy_btns = tk.Frame(copy_area)
        copy_btns.pack(fill="x", pady=(4, 0))
        tk.Button(copy_btns, text="＋ Add", command=self._add_copyright).pack(side="left")
        tk.Button(copy_btns, text="✕ Delete", command=self._delete_copyright, fg="red").pack(side="left", padx=4)

    # -----------------------------------------------------------------------
    # Song list
    # -----------------------------------------------------------------------

    def _populate_song_list(self, reselect=None):
        q = self._search_var.get().lower()
        self._song_list.delete(0, tk.END)
        self._filtered = []

        for num in sorted(self.songs.keys(), key=sort_key):
            song = self.songs[num]
            if q and q not in num.lower() and q not in (song.get("title") or "").lower():
                continue
            label = f"{num:>5}  {song.get('title', '')}"
            self._song_list.insert(tk.END, label)
            self._filtered.append(num)

        # Re-select
        target = reselect or self._current_num
        if target and target in self._filtered:
            idx = self._filtered.index(target)
            self._song_list.selection_set(idx)
            self._song_list.see(idx)

    def _on_song_select(self, _evt):
        sel = self._song_list.curselection()
        if not sel:
            return
        num = self._filtered[sel[0]]
        self._load_song(num)

    def _load_song(self, num):
        self._current_num = num
        self._current_verse_idx = None
        song = self.songs[num]

        self._num_var.set(str(song.get("number", num)))
        self._title_var.set(song.get("title", ""))

        self._refrain_text.delete("1.0", tk.END)
        self._refrain_text.insert(tk.END, song.get("refrain") or "")

        self._populate_verse_list()
        self._populate_copyright()
        self._clear_verse_editor()

    def _clear_verse_editor(self):
        self._verse_num_var.set("")
        self._verse_text.delete("1.0", tk.END)

    # -----------------------------------------------------------------------
    # Verse list
    # -----------------------------------------------------------------------

    def _populate_verse_list(self, reselect=None):
        self._verse_list.delete(0, tk.END)
        if not self._current_num:
            return
        for v in self.songs[self._current_num].get("verses", []):
            self._verse_list.insert(tk.END, f"v{v['verse']}  {v['text'][:30]}{'…' if len(v['text']) > 30 else ''}")

        if reselect is not None and reselect < self._verse_list.size():
            self._verse_list.selection_set(reselect)
            self._verse_list.see(reselect)
            self._current_verse_idx = reselect
            self._load_verse(reselect)

    def _on_verse_select(self, _evt):
        sel = self._verse_list.curselection()
        if not sel:
            return
        self._current_verse_idx = sel[0]
        self._load_verse(sel[0])

    def _load_verse(self, idx):
        verse = self.songs[self._current_num]["verses"][idx]
        self._verse_num_var.set(str(verse["verse"]))
        self._verse_text.delete("1.0", tk.END)
        self._verse_text.insert(tk.END, verse["text"])

    # -----------------------------------------------------------------------
    # Copyright
    # -----------------------------------------------------------------------

    def _populate_copyright(self):
        self._copyright_list.delete(0, tk.END)
        if not self._current_num:
            return
        for c in (self.songs[self._current_num].get("copyright") or []):
            self._copyright_list.insert(tk.END, c)

    # -----------------------------------------------------------------------
    # Apply / Update actions
    # -----------------------------------------------------------------------

    def _apply_song_info(self):
        if not self._current_num:
            return
        song = self.songs[self._current_num]
        new_num   = self._num_var.get().strip()
        new_title = self._title_var.get().strip()
        new_refrain = self._refrain_text.get("1.0", tk.END).strip() or None

        if not new_num:
            messagebox.showerror("Error", "Song number cannot be empty.", parent=self.win)
            return

        # Handle number change — rename key
        if new_num != self._current_num:
            if new_num in self.songs:
                messagebox.showerror("Error", f"Song #{new_num} already exists.", parent=self.win)
                return
            self.songs[new_num] = self.songs.pop(self._current_num)
            self._current_num = new_num

        song = self.songs[self._current_num]
        song["number"] = new_num
        song["title"]  = new_title
        song["refrain"] = new_refrain

        self._dirty = True
        self._set_status("Song info updated.")
        self._populate_song_list(reselect=self._current_num)

    def _update_verse(self):
        if self._current_num is None or self._current_verse_idx is None:
            messagebox.showinfo("No verse selected", "Select a verse from the list first.", parent=self.win)
            return

        try:
            new_vnum = int(self._verse_num_var.get().strip())
        except ValueError:
            messagebox.showerror("Error", "Verse number must be an integer.", parent=self.win)
            return

        new_text = self._verse_text.get("1.0", tk.END).strip()
        verse = self.songs[self._current_num]["verses"][self._current_verse_idx]
        verse["verse"] = new_vnum
        verse["text"]  = new_text

        # Keep verses sorted by number
        self.songs[self._current_num]["verses"].sort(key=lambda v: v["verse"])

        # Find new position of the updated verse after sort
        new_idx = next(
            (i for i, v in enumerate(self.songs[self._current_num]["verses"]) if v["verse"] == new_vnum),
            self._current_verse_idx
        )

        self._dirty = True
        self._set_status(f"Verse {new_vnum} updated.")
        self._populate_verse_list(reselect=new_idx)

    # -----------------------------------------------------------------------
    # Song CRUD
    # -----------------------------------------------------------------------

    def _new_song(self):
        num = simpledialog.askstring("New Song", "Enter song number (e.g. 27B):", parent=self.win)
        if not num:
            return
        num = num.strip()
        if num in self.songs:
            messagebox.showerror("Error", f"Song #{num} already exists.", parent=self.win)
            return
        self.songs[num] = {"number": num, "title": "New Song", "verses": [], "refrain": None, "copyright": []}
        self._dirty = True
        self._populate_song_list(reselect=num)
        self._load_song(num)
        self._set_status(f"Created song #{num}.")

    def _delete_song(self):
        if not self._current_num:
            return
        if not messagebox.askyesno("Delete", f"Delete song #{self._current_num}?", parent=self.win):
            return
        del self.songs[self._current_num]
        self._current_num = None
        self._dirty = True
        self._populate_song_list()
        self._clear_verse_editor()
        self._verse_list.delete(0, tk.END)
        self._copyright_list.delete(0, tk.END)
        self._num_var.set("")
        self._title_var.set("")
        self._refrain_text.delete("1.0", tk.END)
        self._set_status("Song deleted.")

    # -----------------------------------------------------------------------
    # Verse CRUD
    # -----------------------------------------------------------------------

    def _add_verse(self):
        if not self._current_num:
            return
        verses = self.songs[self._current_num]["verses"]
        next_num = max((v["verse"] for v in verses), default=0) + 1
        verses.append({"verse": next_num, "text": ""})
        self._dirty = True
        new_idx = len(verses) - 1
        self._populate_verse_list(reselect=new_idx)
        self._set_status(f"Added verse {next_num}.")

    def _delete_verse(self):
        if self._current_num is None or self._current_verse_idx is None:
            return
        verses = self.songs[self._current_num]["verses"]
        v_num = verses[self._current_verse_idx]["verse"]
        if not messagebox.askyesno("Delete", f"Delete verse {v_num}?", parent=self.win):
            return
        verses.pop(self._current_verse_idx)
        self._current_verse_idx = None
        self._dirty = True
        self._populate_verse_list()
        self._clear_verse_editor()
        self._set_status(f"Verse {v_num} deleted.")

    # -----------------------------------------------------------------------
    # Copyright CRUD
    # -----------------------------------------------------------------------

    def _add_copyright(self):
        if not self._current_num:
            return
        text = simpledialog.askstring("Copyright", "Enter copyright line:", parent=self.win)
        if text:
            self.songs[self._current_num].setdefault("copyright", []).append(text.strip())
            self._dirty = True
            self._populate_copyright()
            self._set_status("Copyright added.")

    def _delete_copyright(self):
        if not self._current_num:
            return
        sel = self._copyright_list.curselection()
        if not sel:
            return
        self.songs[self._current_num]["copyright"].pop(sel[0])
        self._dirty = True
        self._populate_copyright()
        self._set_status("Copyright deleted.")

    # -----------------------------------------------------------------------
    # Save
    # -----------------------------------------------------------------------

    def _save_all(self):
        count = len(self.songs)
        if not messagebox.askyesno("Save", f"Save all {count} songs to disk?", parent=self.win):
            return
        try:
            save_songs(self.songs)
            self._dirty = False
            self._set_status(f"✔ Saved {count} songs.")
        except Exception as e:
            messagebox.showerror("Save Error", str(e), parent=self.win)

    # -----------------------------------------------------------------------
    # Helpers
    # -----------------------------------------------------------------------

    def _set_status(self, msg):
        self._status_var.set(msg)
        self.win.after(4000, lambda: self._status_var.set(""))