import customtkinter as ctk
import asyncio
import threading
import json
import os
from io import BytesIO
from PIL import Image

# --- External Libraries ---
from pynput import keyboard
from winrt.windows.media.control import GlobalSystemMediaTransportControlsSessionManager as MediaManager
from winrt.windows.storage.streams import DataReader, Buffer, InputStreamOptions

# --- Constants ---
CONFIG_FILE = "ghost_config.json"
DEFAULT_CONFIG = {"x": 50, "y": 50, "always_on_top": True}


class GhostPlayer(ctk.CTk):
    def __init__(self):
        super().__init__()

        # --- 1. Load Config & Rescue Logic ---
        self.config = self.load_config()
        self.perform_screen_rescue()  # <--- NEW: Rescue Logic

        # --- 2. Window Setup ---
        self.title("GhostPlayer")
        self.geometry(f"260x60+{self.config['x']}+{self.config['y']}")
        self.overrideredirect(True)
        self.attributes('-topmost', self.config['always_on_top'])

        # --- 3. Opacity & States ---
        self.idle_opacity = 0.60
        self.active_opacity = 0.95
        self.is_hidden = False
        self.attributes('-alpha', self.idle_opacity)
        self.configure(fg_color="#050505")

        # --- 4. Variables & Backend ---
        self.current_song = ""
        self.is_playing = False
        self.manager = None
        self.session = None

        # --- 5. UI Layout ---
        self.grid_columnconfigure(0, weight=0)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # Album Art
        self.album_image = ctk.CTkImage(Image.new("RGB", (50, 50), "#111"), size=(50, 50))
        self.art_label = ctk.CTkLabel(self, text="", image=self.album_image)
        self.art_label.grid(row=0, column=0, rowspan=2, padx=5, pady=5)

        # Info Frame
        self.info_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.info_frame.grid(row=0, column=1, sticky="nswe", padx=5)

        # Title
        self.title_label = ctk.CTkLabel(self.info_frame, text="System Ready",
                                        font=("Segoe UI", 11, "bold"),
                                        text_color="#00E5FF", anchor="w")
        self.title_label.pack(side="top", fill="x", pady=(8, 0))

        # Controls
        self.controls_frame = ctk.CTkFrame(self.info_frame, fg_color="transparent")
        self.controls_frame.pack(side="top", fill="x", pady=(0, 5))

        self.btn_prev = ctk.CTkButton(self.controls_frame, text="I<", width=25, height=20,
                                      fg_color="transparent", text_color="#aaa", hover_color="#222",
                                      font=("Arial", 10, "bold"), command=self.prev_song)
        self.btn_prev.pack(side="left")

        self.btn_play = ctk.CTkButton(self.controls_frame, text="▶", width=30, height=20,
                                      fg_color="transparent", text_color="#FFF", hover_color="#222",
                                      font=("Arial", 14), command=self.toggle_play)
        self.btn_play.pack(side="left", padx=5)

        self.btn_next = ctk.CTkButton(self.controls_frame, text=">I", width=25, height=20,
                                      fg_color="transparent", text_color="#aaa", hover_color="#222",
                                      font=("Arial", 10, "bold"), command=self.next_song)
        self.btn_next.pack(side="left")

        # Close Button
        self.close_btn = ctk.CTkButton(self, text="×", width=15, height=15,
                                       fg_color="transparent", hover_color="#330000",
                                       text_color="#666", command=self.safe_close)
        self.close_btn.place(relx=0.92, rely=0.05)

        # --- 6. Event Bindings ---
        self.bind("<Enter>", self.wake_up)
        self.bind("<Leave>", self.ghost_mode)

        for w in [self.art_label, self.info_frame, self.title_label, self.controls_frame,
                  self.btn_play, self.btn_prev, self.btn_next]:
            w.bind("<Enter>", self.wake_up)

        self.bind("<ButtonPress-1>", self.start_move)
        self.bind("<ButtonRelease-1>", self.stop_move)
        self.bind("<B1-Motion>", self.do_move)

        # --- 7. Threads ---
        self.loop = asyncio.new_event_loop()
        threading.Thread(target=self.start_media_loop, daemon=True).start()
        threading.Thread(target=self.start_hotkey_listener, daemon=True).start()

        self.after(500, self.update_ui_trigger)

    # --- Configuration & Rescue ---
    def load_config(self):
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, 'r') as f:
                    return json.load(f)
            except:
                pass
        return DEFAULT_CONFIG.copy()

    def perform_screen_rescue(self):
        # Get primary screen dimensions
        screen_w = self.winfo_screenwidth()
        screen_h = self.winfo_screenheight()

        x = self.config.get('x', 50)
        y = self.config.get('y', 50)

        # Logic: If top-left corner is off-screen (negative or beyond width/height)
        # Note: This aggressively resets to Primary Monitor if it was on a disconnected Secondary.
        if x < 0 or x > (screen_w - 50):
            print(f"Rescue: x={x} is out of bounds. Resetting.")
            self.config['x'] = 50

        if y < 0 or y > (screen_h - 50):
            print(f"Rescue: y={y} is out of bounds. Resetting.")
            self.config['y'] = 50

    def save_config(self):
        self.config['x'] = self.winfo_x()
        self.config['y'] = self.winfo_y()
        with open(CONFIG_FILE, 'w') as f:
            json.dump(self.config, f)

    def safe_close(self):
        self.save_config()
        self.destroy()
        os._exit(0)

    # --- Core Logic (Unchanged) ---
    def start_hotkey_listener(self):
        with keyboard.GlobalHotKeys({'<ctrl>+<alt>+h': self.toggle_visibility}) as h:
            h.join()

    def toggle_visibility(self):
        self.after(0, self._toggle_visibility_ui)

    def _toggle_visibility_ui(self):
        if self.is_hidden:
            self.deiconify();
            self.is_hidden = False
        else:
            self.withdraw();
            self.is_hidden = True

    def wake_up(self, event):
        if not self.is_hidden:
            self.attributes('-alpha', self.active_opacity)
            self.title_label.configure(text_color="#00E5FF")

    def ghost_mode(self, event):
        if not self.is_hidden:
            self.attributes('-alpha', self.idle_opacity)
            self.title_label.configure(text_color="#999")

    def start_move(self, event):
        self.x = event.x;
        self.y = event.y

    def stop_move(self, event):
        self.x = None;
        self.y = None

    def do_move(self, event):
        x = self.winfo_x() + (event.x - self.x)
        y = self.winfo_y() + (event.y - self.y)
        self.geometry(f"+{x}+{y}")

    def start_media_loop(self):
        asyncio.set_event_loop(self.loop)
        self.loop.run_until_complete(self.media_loop())

    async def media_loop(self):
        while True:
            await self.sync_media_session()
            await asyncio.sleep(1)

    async def sync_media_session(self):
        try:
            if not self.manager: self.manager = await MediaManager.request_async()
            current_session = self.manager.get_current_session()
            if current_session:
                self.session = current_session
                info = await current_session.try_get_media_properties_async()
                title = info.title if info.title else "Unknown"
                artist = info.artist if info.artist else ""

                new_song_id = f"{title}-{artist}"
                if new_song_id != self.current_song:
                    self.current_song = new_song_id
                    if info.thumbnail:
                        stream = await info.thumbnail.open_read_async()
                        buffer = Buffer(stream.size)
                        await stream.read_async(buffer, stream.size, InputStreamOptions.NONE)
                        self.new_image_data = bytes(buffer)
                    else:
                        self.new_image_data = None

                status = current_session.get_playback_info().playback_status
                self.is_playing = (status == 4)
                self.ui_data = {"title": title, "artist": artist, "playing": self.is_playing}
            else:
                self.ui_data = {"title": "Idle", "artist": "", "playing": False}
        except:
            pass

    def update_ui_trigger(self):
        if hasattr(self, 'ui_data'):
            full = f"{self.ui_data['title']}"
            if self.ui_data['artist']: full += f" • {self.ui_data['artist']}"
            self.title_label.configure(text=self.truncate(full, 35))
            self.btn_play.configure(text="||" if self.ui_data["playing"] else "▶")

        if hasattr(self, 'new_image_data'):
            if self.new_image_data:
                try:
                    pil_img = Image.open(BytesIO(self.new_image_data))
                    self.art_label.configure(image=ctk.CTkImage(pil_img, size=(50, 50)))
                except:
                    pass
            del self.new_image_data
        self.after(500, self.update_ui_trigger)

    def truncate(self, text, limit):
        return text if len(text) < limit else text[:limit] + "..."

    def run_async(self, coro):
        asyncio.run_coroutine_threadsafe(coro, self.loop)

    def toggle_play(self):
        if self.session: self.run_async(self.session.try_toggle_play_pause_async())

    def next_song(self):
        if self.session: self.run_async(self.session.try_skip_next_async())

    def prev_song(self):
        if self.session: self.run_async(self.session.try_skip_previous_async())


if __name__ == "__main__":
    app = GhostPlayer()
    app.mainloop()