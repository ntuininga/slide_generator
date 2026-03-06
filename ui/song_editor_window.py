import tkinter as tk
from tkinter import simpledialog, messagebox
import json
from logic.song_manager import SongManager

class SongEditorWindow:
    def __init__(self, root):
        self.root = root
        self.root.title("Songs Editor")
        self.root.geometry("950x650")

        # Logic layer
        self.manager = SongManager()

        # Current selected verse mapping
        self.current_verse_map = []

        self.setup_ui()
        self.refresh_song_list()

    # -----------------------------
    # --- UI Setup ---------------
    # -----------------------------
    def setup_ui(self):
        # --- Left frame ---
        left_frame = tk.Frame(self.root)
        left_frame.pack(side=tk.LEFT, fill=tk.Y, padx=5, pady=5)

        tk.Label(left_frame, text="Search:").pack(anchor="w")
        self.search_var = tk.StringVar()
        search_entry = tk.Entry(left_frame, textvariable=self.search_var)
        search_entry.pack(fill=tk.X, pady=(0,5))
        self.search_var.trace_add("write", lambda *args: self.refresh_song_list())

        self.song_listbox = tk.Listbox(left_frame, width=35)
        self.song_listbox.pack(side=tk.TOP, fill=tk.BOTH, expand=True)
        self.song_listbox.bind("<<ListboxSelect>>", self.on_song_select)

        song_btn_frame = tk.Frame(left_frame)
        song_btn_frame.pack(fill=tk.X)
        tk.Button(song_btn_frame, text="Add Song", command=self.add_song).pack(side=tk.LEFT)
        tk.Button(song_btn_frame, text="Delete Song", command=self.delete_song).pack(side=tk.LEFT)
        tk.Button(song_btn_frame, text="Save", command=self.save_songs).pack(side=tk.LEFT)

        # --- Right frame ---
        right_frame = tk.Frame(self.root)
        right_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Title
        tk.Label(right_frame, text="Title:").pack(anchor="w")
        self.title_var = tk.StringVar()
        title_entry = tk.Entry(right_frame, textvariable=self.title_var)
        title_entry.pack(fill=tk.X)
        self.title_var.trace_add("write", lambda *args: self.update_title())

        # Refrain
        tk.Label(right_frame, text="Refrain:").pack(anchor="w")
        self.refrain_text = tk.Text(right_frame, height=3)
        self.refrain_text.pack(fill=tk.X)
        self.refrain_text.bind("<KeyRelease>", lambda e: self.update_refrain())

        # Verses
        tk.Label(right_frame, text="Verses:").pack(anchor="w")
        self.verse_listbox = tk.Listbox(right_frame, height=10)
        self.verse_listbox.pack(fill=tk.BOTH, expand=True)
        self.verse_listbox.bind("<<ListboxSelect>>", self.on_verse_select)

        self.verse_number_var = tk.StringVar()
        self.verse_number_entry = tk.Entry(right_frame, textvariable=self.verse_number_var, width=5)
        self.verse_number_entry.pack(anchor="w", pady=(2,0))
        tk.Label(right_frame, text="Edit verse number above").pack(anchor="w")
        self.verse_number_var.trace_add("write", lambda *args: self.update_verse_number())

        self.verse_text = tk.Text(right_frame, height=3)
        self.verse_text.pack(fill=tk.X)
        self.verse_text.bind("<KeyRelease>", lambda e: self.update_verse_text())

        # Verse buttons
        verse_btn_frame = tk.Frame(right_frame)
        verse_btn_frame.pack(fill=tk.X)
        tk.Button(verse_btn_frame, text="Add", command=self.add_verse).pack(side=tk.LEFT)
        tk.Button(verse_btn_frame, text="Update", command=self.update_verse).pack(side=tk.LEFT)
        tk.Button(verse_btn_frame, text="Delete", command=self.delete_verse).pack(side=tk.LEFT)

        # Copyright
        tk.Label(right_frame, text="Copyright:").pack(anchor="w")
        self.copyright_listbox = tk.Listbox(right_frame, height=4)
        self.copyright_listbox.pack(fill=tk.X)

        cr_btn_frame = tk.Frame(right_frame)
        cr_btn_frame.pack(fill=tk.X)
        tk.Button(cr_btn_frame, text="Add", command=self.add_copyright).pack(side=tk.LEFT)
        tk.Button(cr_btn_frame, text="Delete", command=self.delete_copyright).pack(side=tk.LEFT)

    # -----------------------------
    # --- UI Refresh Methods ------
    # -----------------------------
    def refresh_song_list(self):
        self.song_listbox.delete(0, tk.END)
        filter_text = self.search_var.get().lower()
        for num, song in self.manager.get_sorted_songs():
            if filter_text in num.lower() or filter_text in (song.get("title") or "").lower():
                self.song_listbox.insert(tk.END, f"{num}: {song.get('title')}")

    def refresh_verse_list(self):
        self.verse_listbox.delete(0, tk.END)
        self.current_verse_map.clear()
        if selected := self.song_listbox.get(tk.ACTIVE):
            num = selected.split(":")[0]
            for idx, v in enumerate(self.manager.songs[num]["verses"]):
                self.verse_listbox.insert(tk.END, f"{v['verse']}: {v['text'][:40]}...")
                self.current_verse_map.append(idx)

    def refresh_copyright(self):
        self.copyright_listbox.delete(0, tk.END)
        if selected := self.song_listbox.get(tk.ACTIVE):
            num = selected.split(":")[0]
            for c in self.manager.songs[num]["copyright"]:
                self.copyright_listbox.insert(tk.END, c)

    # -----------------------------
    # --- Selection Handlers ------
    # -----------------------------
    def on_song_select(self, evt):
        if not self.song_listbox.curselection():
            return
        idx = self.song_listbox.curselection()[0]
        num = self.manager.get_sorted_songs()[idx][0]
        song = self.manager.songs[num]
        self.title_var.set(song.get("title") or "")
        self.refrain_text.delete("1.0", tk.END)
        self.refrain_text.insert(tk.END, song.get("refrain") or "")
        self.refresh_verse_list()
        self.refresh_copyright()

    def on_verse_select(self, evt):
        if not self.verse_listbox.curselection():
            return
        idx = self.verse_listbox.curselection()[0]
        verse_idx = self.current_verse_map[idx]
        song_num = self.song_listbox.get(tk.ACTIVE).split(":")[0]
        verse = self.manager.songs[song_num]["verses"][verse_idx]
        self.verse_text.delete("1.0", tk.END)
        self.verse_text.insert(tk.END, verse["text"])
        self.verse_number_var.set(str(verse["verse"]))

    # -----------------------------
    # --- Update Handlers ---------
    # -----------------------------
    def update_title(self):
        if selected := self.song_listbox.get(tk.ACTIVE):
            num = selected.split(":")[0]
            self.manager.songs[num]["title"] = self.title_var.get()
            self.refresh_song_list()

    def update_refrain(self):
        if selected := self.song_listbox.get(tk.ACTIVE):
            num = selected.split(":")[0]
            self.manager.songs[num]["refrain"] = self.refrain_text.get("1.0", tk.END).strip() or None

    def update_verse_text(self):
        if selected := self.song_listbox.get(tk.ACTIVE):
            if self.verse_listbox.curselection():
                num = selected.split(":")[0]
                idx = self.verse_listbox.curselection()[0]
                verse_idx = self.current_verse_map[idx]
                self.manager.update_verse(num, verse_idx, text=self.verse_text.get("1.0", tk.END).strip())
                self.refresh_verse_list()
                self.verse_listbox.selection_set(idx)

    def update_verse_number(self):
        if selected := self.song_listbox.get(tk.ACTIVE):
            if self.verse_listbox.curselection():
                num = selected.split(":")[0]
                idx = self.verse_listbox.curselection()[0]
                verse_idx = self.current_verse_map[idx]
                try:
                    new_num = int(self.verse_number_var.get())
                    self.manager.update_verse(num, verse_idx, verse_number=new_num)
                    self.refresh_verse_list()
                    # re-select updated verse
                    for new_idx, v_idx in enumerate(self.current_verse_map):
                        if self.manager.songs[num]["verses"][v_idx]["text"] == self.verse_text.get("1.0", tk.END).strip():
                            self.verse_listbox.selection_set(new_idx)
                            break
                except ValueError:
                    pass

    # -----------------------------
    # --- Song CRUD ---------------
    # -----------------------------
    def add_song(self):
        new_num = simpledialog.askstring("New Song", "Enter song number:")
        if new_num:
            self.manager.add_song(new_num)
            self.refresh_song_list()
            # auto-select
            for idx, item in enumerate(self.song_listbox.get(0, tk.END)):
                if item.startswith(new_num + ":"):
                    self.song_listbox.selection_clear(0, tk.END)
                    self.song_listbox.selection_set(idx)
                    self.song_listbox.activate(idx)
                    self.on_song_select(None)
                    break

    def delete_song(self):
        if selected := self.song_listbox.get(tk.ACTIVE):
            num = selected.split(":")[0]
            self.manager.delete_song(num)
            self.refresh_song_list()

    # -----------------------------
    # --- Verse CRUD --------------
    # -----------------------------
    def add_verse(self):
        if selected := self.song_listbox.get(tk.ACTIVE):
            num = selected.split(":")[0]
            idx = self.manager.add_verse(num)
            self.refresh_verse_list()
            self.verse_listbox.selection_clear(0, tk.END)
            self.verse_listbox.selection_set(idx)
            self.verse_listbox.activate(idx)
            self.on_verse_select(None)

    def update_verse(self):
        self.update_verse_text()
        self.update_verse_number()

    def delete_verse(self):
        if selected := self.song_listbox.get(tk.ACTIVE):
            if self.verse_listbox.curselection():
                num = selected.split(":")[0]
                idx = self.verse_listbox.curselection()[0]
                verse_idx = self.current_verse_map[idx]
                self.manager.delete_verse(num, verse_idx)
                self.refresh_verse_list()

    # -----------------------------
    # --- Copyright CRUD ----------
    # -----------------------------
    def add_copyright(self):
        if selected := self.song_listbox.get(tk.ACTIVE):
            num = selected.split(":")[0]
            new_text = simpledialog.askstring("New Copyright", "Enter copyright text:")
            if new_text:
                self.manager.add_copyright(num, new_text)
                self.refresh_copyright()

    def delete_copyright(self):
        if selected := self.song_listbox.get(tk.ACTIVE):
            if self.copyright_listbox.curselection():
                num = selected.split(":")[0]
                idx = self.copyright_listbox.curselection()[0]
                self.manager.delete_copyright(num, idx)
                self.refresh_copyright()

    # -----------------------------
    # --- Save -------------------
    # -----------------------------
    def save_songs(self):
        popup = tk.Toplevel(self.root)
        popup.title("Confirm Save")
        popup.geometry("1000x700")
        tk.Label(popup, text="Confirm the data to save:").pack(anchor="w")
        text_widget = tk.Text(popup)
        text_widget.pack(fill=tk.BOTH, expand=True)
        text_widget.insert(tk.END, json.dumps(self.manager.songs, indent=4))
        text_widget.config(state=tk.DISABLED)

        def confirm_save():
            self.manager.save_songs()
            messagebox.showinfo("Saved", f"Songs saved to {self.manager.json_path}")
            popup.destroy()

        def cancel_save():
            popup.destroy()

        btn_frame = tk.Frame(popup)
        btn_frame.pack(fill=tk.X)
        tk.Button(btn_frame, text="Confirm Save", command=confirm_save).pack(side=tk.LEFT)
        tk.Button(btn_frame, text="Cancel", command=cancel_save).pack(side=tk.LEFT)