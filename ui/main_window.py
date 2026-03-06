import tkinter as tk
from tkinter import ttk, messagebox
from tkcalendar import DateEntry
from logic.parse_bulletin import parse_bulletin
from slide_generator import generate_powerpoint_slides
import os
import json
import platform

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
SONG_DIR = os.path.join(BASE_DIR, "song_data")


def load_all_songs():
    """Load all song JSONs from song_data/ into a dict keyed by number."""
    songs = {}
    if not os.path.exists(SONG_DIR):
        return songs
    for filename in os.listdir(SONG_DIR):
        if filename.endswith(".json"):
            path = os.path.join(SONG_DIR, filename)
            try:
                with open(path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    number = str(data.get("number", ""))
                    if number:
                        songs[number] = data
            except Exception as e:
                print(f"[WARNING] Could not load {filename}: {e}")
    return songs


class SongRow:
    """A single song row inside a service frame, with search + verse checkboxes."""

    def __init__(self, parent_frame, row_index, song_data, all_songs, on_delete):
        self.parent_frame = parent_frame
        self.all_songs = all_songs
        self.on_delete = on_delete
        self.row_index = row_index

        self.resolved_song = all_songs.get(str(song_data.get("number", "")))

        self.frame = tk.LabelFrame(parent_frame, padx=4, pady=4)
        self.frame.pack(fill="x", padx=8, pady=2)

        # Top row: index + search box + title label + delete button
        top = tk.Frame(self.frame)
        top.pack(fill="x")

        self.index_label = tk.Label(top, text=f"{row_index}.", width=2)
        self.index_label.pack(side="left")

        self.search_var = tk.StringVar(value=str(song_data.get("number", "")))
        self.search_var.trace_add("write", self._on_search_change)
        self.search_entry = tk.Entry(top, textvariable=self.search_var, width=8)
        self.search_entry.pack(side="left", padx=(0, 4))

        self.title_label = tk.Label(top, text="", anchor="w", fg="#333333")
        self.title_label.pack(side="left", fill="x", expand=True)

        tk.Button(top, text="✕", fg="red", width=2,
                  command=self._delete).pack(side="right")

        self.suggestion_frame = None

        # Verse checkboxes row
        self.verse_frame = tk.Frame(self.frame)
        self.verse_frame.pack(fill="x", pady=(2, 0))
        self.verse_vars = {}

        self._render_song(song_data.get("verses"))

    def _on_search_change(self, *args):
        query = self.search_var.get().strip()
        self._clear_suggestions()

        if not query:
            self.title_label.config(text="")
            self._clear_verse_checkboxes()
            return

        # Exact match (case-insensitive)
        exact = self.all_songs.get(query) or self.all_songs.get(query.upper())
        if exact:
            self._select_song(exact)
            return

        # Partial matches
        q = query.lower()
        matches = [
            s for num, s in self.all_songs.items()
            if q in num.lower() or q in s.get("title", "").lower()
        ][:8]

        if matches:
            self._show_suggestions(matches)
        else:
            self.title_label.config(text="No match found", fg="red")
            self._clear_verse_checkboxes()

    def _show_suggestions(self, matches):
        self._clear_suggestions()
        self.suggestion_frame = tk.Frame(self.frame, relief="solid", bd=1, bg="white")
        self.suggestion_frame.pack(fill="x", padx=2)

        for song in matches:
            label_text = f"#{song['number']} — {song['title']}"
            tk.Button(
                self.suggestion_frame,
                text=label_text,
                anchor="w",
                bg="white",
                relief="flat",
                command=lambda s=song: self._pick_suggestion(s)
            ).pack(fill="x")

    def _pick_suggestion(self, song):
        self._clear_suggestions()
        # Temporarily pause trace to avoid re-triggering search
        self.search_var.trace_remove("write", self.search_var.trace_info()[0][1])
        self.search_var.set(song["number"])
        self.search_var.trace_add("write", self._on_search_change)
        self._select_song(song)

    def _clear_suggestions(self):
        if self.suggestion_frame:
            self.suggestion_frame.destroy()
            self.suggestion_frame = None

    def _select_song(self, song):
        self.resolved_song = song
        self.title_label.config(text=song.get("title", ""), fg="#333333")
        self._render_verse_checkboxes(song, selected_verses=None)

    def _render_song(self, selected_verses):
        if self.resolved_song:
            self.title_label.config(text=self.resolved_song.get("title", ""), fg="#333333")
            self._render_verse_checkboxes(self.resolved_song, selected_verses)
        else:
            number = self.search_var.get().strip()
            if number:
                self.title_label.config(text="Song not found", fg="red")

    def _clear_verse_checkboxes(self):
        for widget in self.verse_frame.winfo_children():
            widget.destroy()
        self.verse_vars = {}

    def _render_verse_checkboxes(self, song, selected_verses):
        self._clear_verse_checkboxes()
        verses = song.get("verses", [])

        tk.Label(self.verse_frame, text="Verses:").pack(side="left")

        all_var = tk.BooleanVar(value=(selected_verses is None))
        tk.Checkbutton(
            self.verse_frame, text="All", variable=all_var,
            command=lambda: self._toggle_all(all_var)
        ).pack(side="left", padx=(0, 6))
        self.verse_vars["__all__"] = all_var

        for v in verses:
            v_num = v["verse"]
            checked = (selected_verses is None) or (v_num in selected_verses)
            var = tk.BooleanVar(value=checked)
            tk.Checkbutton(
                self.verse_frame,
                text=str(v_num),
                variable=var,
                command=self._sync_all_checkbox
            ).pack(side="left")
            self.verse_vars[v_num] = var

    def _toggle_all(self, all_var):
        state = all_var.get()
        for key, var in self.verse_vars.items():
            if key != "__all__":
                var.set(state)

    def _sync_all_checkbox(self):
        individual = [var.get() for key, var in self.verse_vars.items() if key != "__all__"]
        if "__all__" in self.verse_vars:
            self.verse_vars["__all__"].set(all(individual))

    def _delete(self):
        self.frame.destroy()
        self.on_delete(self)

    def get_song_data(self):
        if not self.resolved_song:
            return None
        number = self.resolved_song["number"]
        all_selected = self.verse_vars.get("__all__", tk.BooleanVar(value=True)).get()
        if all_selected:
            verses = None
        else:
            verses = [k for k, var in self.verse_vars.items() if k != "__all__" and var.get()]
            if not verses:
                verses = None
        return {"number": number, "verses": verses}


class ServiceFrame:
    """Full service section with fields + inline song rows."""

    def __init__(self, parent, service_name, service, all_songs):
        self.service_name = service_name
        self.all_songs = all_songs
        self.song_rows = []

        self.frame = tk.LabelFrame(parent, text=service['service_label'], padx=5, pady=5)
        self.frame.pack(fill="x", padx=8, pady=6)

        fields = tk.Frame(self.frame)
        fields.pack(fill="x")

        tk.Label(fields, text="Date:").grid(row=0, column=0, sticky="w")
        self.date_var = tk.StringVar(value=service.get('date', ''))
        DateEntry(fields, textvariable=self.date_var, width=12).grid(row=0, column=1, sticky="w")

        tk.Label(fields, text="Title:").grid(row=1, column=0, sticky="w")
        self.title_var = tk.StringVar(value=service.get('title', ''))
        tk.Entry(fields, textvariable=self.title_var, width=50).grid(row=1, column=1, columnspan=3, sticky="w")

        tk.Label(fields, text="Scripture:").grid(row=2, column=0, sticky="w")
        self.scripture_var = tk.StringVar(value=service.get('scripture', ''))
        tk.Entry(fields, textvariable=self.scripture_var, width=50).grid(row=2, column=1, columnspan=3, sticky="w")

        tk.Label(fields, text="Offering:").grid(row=3, column=0, sticky="w")
        self.offering_var = tk.StringVar(value=service.get('offering', ''))
        tk.Entry(fields, textvariable=self.offering_var, width=50).grid(row=3, column=1, columnspan=3, sticky="w")

        tk.Label(fields, text="Nicene Creed:").grid(row=4, column=0, sticky="w")
        self.nicene_var = tk.BooleanVar(value=service.get('isNicene', False))
        tk.Checkbutton(fields, variable=self.nicene_var).grid(row=4, column=1, sticky="w")

        tk.Label(fields, text="Lord's Supper:").grid(row=5, column=0, sticky="w")
        self.lords_var = tk.BooleanVar(value=service.get('isLordsSupper', False))
        tk.Checkbutton(fields, variable=self.lords_var).grid(row=5, column=1, sticky="w")

        # Creed slide — checked by default for evening, unchecked for morning
        tk.Label(fields, text="Include Creed Slide:").grid(row=6, column=0, sticky="w")
        default_creed = service.get('service_type', 'morning') == 'evening'
        self.creed_var = tk.BooleanVar(value=service.get('includeCreed', default_creed))
        tk.Checkbutton(fields, variable=self.creed_var).grid(row=6, column=1, sticky="w")

        # Songs
        tk.Label(self.frame, text="Songs:", font=("TkDefaultFont", 10, "bold")).pack(anchor="w", pady=(8, 2))
        self.songs_container = tk.Frame(self.frame)
        self.songs_container.pack(fill="x")

        for song in service.get('songs', []):
            self._add_song_row(song)

        tk.Button(self.frame, text="+ Add Song",
                  command=lambda: self._add_song_row({})).pack(anchor="w", pady=(4, 0))

    def _add_song_row(self, song_data):
        row = SongRow(
            self.songs_container,
            len(self.song_rows) + 1,
            song_data,
            self.all_songs,
            on_delete=self._remove_song_row
        )
        self.song_rows.append(row)

    def _remove_song_row(self, row):
        if row in self.song_rows:
            self.song_rows.remove(row)
        for i, r in enumerate(self.song_rows):
            r.index_label.config(text=f"{i + 1}.")

    def get_service_data(self, original_service):
        service = dict(original_service)
        service['date'] = self.date_var.get()
        service['title'] = self.title_var.get()
        service['scripture'] = self.scripture_var.get()
        service['offering'] = self.offering_var.get()
        service['isNicene'] = self.nicene_var.get()
        service['isLordsSupper'] = self.lords_var.get()
        service['includeCreed'] = self.creed_var.get()
        service['songs'] = [r.get_song_data() for r in self.song_rows if r.get_song_data()]
        return service


class MainWindow:
    def __init__(self, root, bulletin_folder):
        self.root = root
        self.root.title("Bulletin Viewer / Editor")
        self.root.minsize(650, 500)
        self.bulletin_folder = bulletin_folder

        if platform.system() == "Windows":
            self.root.state("zoomed")
        else:
            self.root.attributes("-zoomed", True)

        self.all_songs = load_all_songs()

        # Scrollable canvas
        self.canvas = tk.Canvas(root)
        self.scrollbar = tk.Scrollbar(root, orient="vertical", command=self.canvas.yview)
        self.scroll_frame = tk.Frame(self.canvas)
        self.scroll_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )
        self.canvas.create_window((0, 0), window=self.scroll_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        self.canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")

        # Mousewheel support
        self.canvas.bind_all(
            "<MouseWheel>",
            lambda e: self.canvas.yview_scroll(int(-1 * (e.delta / 120)), "units")
        )

        self.bulletin = parse_bulletin(self.bulletin_folder)
        self.service_frames = {}

        if self.bulletin:
            self._build_ui()
        else:
            tk.Label(self.scroll_frame, text="No bulletin found for today").pack()

        # Fit window to content
        # self.root.update_idletasks()
        # self.root.geometry(f"{self.root.winfo_reqwidth()}x{self.root.winfo_reqheight()}")

    def _build_ui(self):
        services_row = tk.Frame(self.scroll_frame)
        services_row.pack(fill="both", expand=True, padx=4, pady=4)

        for service_name, service in self.bulletin.items():
            sf = ServiceFrame(services_row, service_name, service, self.all_songs)
            sf.frame.pack(side="left", fill="both", expand=True, padx=4, pady=4)
            self.service_frames[service_name] = sf

        button_row = tk.Frame(self.scroll_frame)
        button_row.pack(fill="x", pady=14)
        tk.Button(
            button_row,
            text="💾  Save All & Generate Slides",
            command=self.save_all,
            bg="#2e7d32", fg="white",
            font=("TkDefaultFont", 11, "bold"),
            padx=10, pady=6
        ).pack()

    def save_all(self):
        updated_bulletin = {
            name: sf.get_service_data(self.bulletin[name])
            for name, sf in self.service_frames.items()
        }

        text = ""
        for s_name, s in updated_bulletin.items():
            text += f"--- {s['service_label']} ---\n"
            text += f"Date: {s['date']}\n"
            text += f"Title: {s['title']}\n"
            text += f"Scripture: {s['scripture']}\n"
            text += f"Offering: {s['offering'] or '(none)'}\n"
            text += f"Nicene: {'Yes' if s['isNicene'] else 'No'}\n"
            text += f"Lord's Supper: {'Yes' if s['isLordsSupper'] else 'No'}\n"
            text += f"Creed Slide: {'Yes' if s.get('includeCreed') else 'No'}\n"
            text += "Songs:\n"
            for i, song in enumerate(s.get('songs', []), 1):
                verses = song.get('verses')
                verse_str = "all verses" if verses is None else "vs. " + ", ".join(str(v) for v in verses)
                text += f"  {i}. #{song['number']} — {verse_str}\n"
            text += "\n"

        if messagebox.askyesno("Confirm Save", f"Confirm saving the following?\n\n{text}"):
            self.bulletin = updated_bulletin
            for service in self.bulletin.values():
                generate_powerpoint_slides(service)
            messagebox.showinfo("Done", "Slides generated successfully!")