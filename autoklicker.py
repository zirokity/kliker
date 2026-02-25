import sys
import threading
import time
import random
import webbrowser
import urllib.request
import json as _json
import math

try:
    import customtkinter as ctk
except ImportError:
    print("BRAK: pip install customtkinter")
    input("Enter aby wyjsc...")
    sys.exit(1)

try:
    import pydirectinput
except ImportError:
    print("BRAK: pip install pydirectinput")
    input("Enter aby wyjsc...")
    sys.exit(1)

try:
    import keyboard
except ImportError:
    print("BRAK: pip install keyboard")
    input("Enter aby wyjsc...")
    sys.exit(1)

# ══════════════════════════════════════════════════════════════
#  KONFIGURACJA
# ══════════════════════════════════════════════════════════════
CURRENT_VERSION = "1.0.0"
GITHUB_USER     = "TWOJ_NICK"
GITHUB_REPO     = "NAZWA_REPO"
VERSION_URL     = f"https://raw.githubusercontent.com/{GITHUB_USER}/{GITHUB_REPO}/main/version.json"
RELEASE_URL     = f"https://github.com/{GITHUB_USER}/{GITHUB_REPO}/releases/latest"

# ── Domyślne kolory ────────────────────────────────────────────
DEFAULTS = {
    "BG":         "#0d0d0d",
    "BG_CARD":    "#111111",
    "BG_ENTRY":   "#171717",
    "BG_SIDEBAR": "#0f0f0f",
    "ACCENT":     "#00ff88",
    "BORDER":     "#222222",
    "TEXT_DIM":   "#3a3a3a",
}

PRESETS = {
    "GREEN  (domyślny)": {"ACCENT": "#00ff88"},
    "BLUE":              {"ACCENT": "#00aaff"},
    "PURPLE":            {"ACCENT": "#aa44ff"},
    "RED":               {"ACCENT": "#ff3355"},
    "ORANGE":            {"ACCENT": "#ff8800"},
    "WHITE":             {"ACCENT": "#ffffff"},
    "YELLOW":            {"ACCENT": "#ffcc00"},
}

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("dark-blue")


def check_for_update():
    if "TWOJ_NICK" in VERSION_URL:
        return False, None
    try:
        req = urllib.request.Request(VERSION_URL, headers={"User-Agent": "AutoClicker"})
        with urllib.request.urlopen(req, timeout=3) as r:
            data = _json.loads(r.read().decode())
        latest = data.get("version", "0.0.0")
        if latest != CURRENT_VERSION:
            return True, latest
    except Exception:
        pass
    return False, None


def hex_to_rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))


def rgb_to_hex(r, g, b):
    return f"#{int(r):02x}{int(g):02x}{int(b):02x}"


class App(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.F_TITLE   = ctk.CTkFont("Consolas", 13, "bold")
        self.F_LABEL   = ctk.CTkFont("Consolas", 10)
        self.F_ENTRY   = ctk.CTkFont("Consolas", 11)
        self.F_BTN     = ctk.CTkFont("Consolas", 11, "bold")
        self.F_SMALL   = ctk.CTkFont("Consolas", 8)
        self.F_NAV     = ctk.CTkFont("Consolas", 11, "bold")
        self.F_UPDATE  = ctk.CTkFont("Consolas", 9, "bold")

        self.title("AUTOCLICKER")
        self.geometry("720x400")
        self.resizable(False, False)
        self.attributes("-topmost", True)
        self.configure(fg_color=DEFAULTS["BG"])

        # aktywne kolory
        self.colors = dict(DEFAULTS)

        self.visible       = True
        self.mouse_running = False
        self.kb_running    = False
        self.active_tab    = "MYSZ"

        # RGB cycle
        self._rgb_running  = False
        self._rgb_thread   = None
        self._rgb_hue      = 0.0

        self._build()

        threading.Thread(target=self._check_update_thread, daemon=True).start()
        threading.Thread(target=self._mouse_loop,          daemon=True).start()
        threading.Thread(target=self._kb_loop,             daemon=True).start()
        threading.Thread(target=self._hotkey_loop,         daemon=True).start()

    # ─────────────────────────────────────────────
    #  UPDATE
    # ─────────────────────────────────────────────
    def _check_update_thread(self):
        has_update, new_ver = check_for_update()
        if has_update:
            self.after(0, lambda: self._show_update_banner(new_ver))

    def _show_update_banner(self, new_ver):
        banner = ctk.CTkFrame(self._sidebar, fg_color="#1a1400",
                              corner_radius=0, border_color="#ffcc00",
                              border_width=1, height=60)
        banner.pack(fill="x", side="bottom", padx=4, pady=4)
        banner.pack_propagate(False)
        ctk.CTkLabel(banner, text=f"⬆ v{new_ver} dostępna",
                     font=self.F_UPDATE, text_color="#ffcc00").pack(pady=(6, 2))
        ctk.CTkButton(banner, text="POBIERZ", font=self.F_UPDATE,
                      fg_color="#ffcc00", hover_color="#ccaa00",
                      text_color="#000", corner_radius=0, height=20,
                      command=lambda: webbrowser.open(RELEASE_URL)
                      ).pack(fill="x", padx=6, pady=2)

    # ─────────────────────────────────────────────
    #  BUILD
    # ─────────────────────────────────────────────
    def _build(self):
        # topbar
        self._topbar = ctk.CTkFrame(self, fg_color=self.colors["BG_CARD"],
                                    corner_radius=0, height=36)
        self._topbar.pack(fill="x")
        self._topbar.pack_propagate(False)
        self._topbar_title = ctk.CTkLabel(
            self._topbar, text="[ AUTOCLICKER ]",
            font=self.F_TITLE, text_color=self.colors["ACCENT"])
        self._topbar_title.place(relx=0.02, rely=0.5, anchor="w")
        ctk.CTkLabel(self._topbar, text=f"v{CURRENT_VERSION}  •  F1=hide  •  ADMIN",
                     font=self.F_SMALL, text_color=self.colors["TEXT_DIM"]
                     ).place(relx=0.98, rely=0.5, anchor="e")

        self._accent_line = ctk.CTkFrame(self, fg_color=self.colors["ACCENT"],
                                         height=2, corner_radius=0)
        self._accent_line.pack(fill="x")

        main = ctk.CTkFrame(self, fg_color=self.colors["BG"], corner_radius=0)
        main.pack(fill="both", expand=True)

        # sidebar
        self._sidebar = ctk.CTkFrame(main, fg_color=self.colors["BG_SIDEBAR"],
                                     corner_radius=0, width=120)
        self._sidebar.pack(side="left", fill="y")
        self._sidebar.pack_propagate(False)

        ctk.CTkFrame(main, fg_color=self.colors["BORDER"], width=1,
                     corner_radius=0).pack(side="left", fill="y")

        self._nav_btns = {}
        nav_items = [("MYSZ", "🖱  MYSZ"), ("KB", "⌨  KLAW"), ("SET", "⚙  SET")]
        for key, label in nav_items:
            is_active = key == "MYSZ"
            btn = ctk.CTkButton(
                self._sidebar, text=label,
                font=self.F_NAV, corner_radius=0, height=44,
                fg_color=self.colors["ACCENT"] if is_active else self.colors["BG_ENTRY"],
                text_color="#000" if is_active else self.colors["TEXT_DIM"],
                hover_color=self.colors["BG_ENTRY"],
                border_width=0,
                command=lambda k=key: self._switch_tab(k)
            )
            btn.pack(fill="x", pady=(8 if key == "MYSZ" else 2, 0), padx=6)
            self._nav_btns[key] = btn

        ctk.CTkLabel(self._sidebar, text=f"v{CURRENT_VERSION}",
                     font=self.F_SMALL, text_color=self.colors["TEXT_DIM"]
                     ).pack(side="bottom", pady=6)

        # content
        self._content = ctk.CTkFrame(main, fg_color=self.colors["BG"], corner_radius=0)
        self._content.pack(side="left", fill="both", expand=True)

        self._panels = {}
        self._panels["MYSZ"] = ctk.CTkFrame(self._content, fg_color=self.colors["BG"], corner_radius=0)
        self._panels["KB"]   = ctk.CTkFrame(self._content, fg_color=self.colors["BG"], corner_radius=0)
        self._panels["SET"]  = ctk.CTkFrame(self._content, fg_color=self.colors["BG"], corner_radius=0)

        self._build_mouse_panel(self._panels["MYSZ"])
        self._build_kb_panel(self._panels["KB"])
        self._build_settings_panel(self._panels["SET"])

        self._panels["MYSZ"].pack(fill="both", expand=True)

    # ─────────────────────────────────────────────
    #  NAWIGACJA
    # ─────────────────────────────────────────────
    def _switch_tab(self, tab):
        self.active_tab = tab
        for k, p in self._panels.items():
            p.pack_forget()
        self._panels[tab].pack(fill="both", expand=True)
        for k, btn in self._nav_btns.items():
            if k == tab:
                btn.configure(fg_color=self.colors["ACCENT"], text_color="#000")
            else:
                btn.configure(fg_color=self.colors["BG_ENTRY"],
                              text_color=self.colors["TEXT_DIM"])

    # ─────────────────────────────────────────────
    #  HELPERS
    # ─────────────────────────────────────────────
    def _row(self, parent, label, default, placeholder=""):
        row = ctk.CTkFrame(parent, fg_color="transparent", corner_radius=0)
        row.pack(fill="x", padx=14, pady=3)
        ctk.CTkLabel(row, text=label, font=self.F_LABEL,
                     text_color=self.colors["TEXT_DIM"], width=200, anchor="w"
                     ).pack(side="left")
        e = ctk.CTkEntry(row, placeholder_text=placeholder,
                         fg_color=self.colors["BG_ENTRY"],
                         border_color=self.colors["BORDER"], border_width=1,
                         text_color=self.colors["ACCENT"],
                         placeholder_text_color=self.colors["TEXT_DIM"],
                         font=self.F_ENTRY, corner_radius=0, height=30)
        e.insert(0, default)
        e.pack(side="left", fill="x", expand=True)
        return e

    def _sep(self, parent):
        ctk.CTkFrame(parent, fg_color=self.colors["BORDER"],
                     height=1, corner_radius=0).pack(fill="x", padx=14, pady=5)

    # ─────────────────────────────────────────────
    #  PANEL MYSZ
    # ─────────────────────────────────────────────
    def _build_mouse_panel(self, p):
        self._sep(p)
        self.mouse_cps   = self._row(p, "CPS", "10", "np. 10")
        self.mouse_human = self._row(p, "HUMANIZER  (% losowości, 0=wył)", "0", "0-100")
        self.mouse_delay = self._row(p, "OPÓŹNIENIE STARTU  (s)", "0", "np. 3")

        row = ctk.CTkFrame(p, fg_color="transparent", corner_radius=0)
        row.pack(fill="x", padx=14, pady=3)
        ctk.CTkLabel(row, text="PRZYCISK MYSZY", font=self.F_LABEL,
                     text_color=self.colors["TEXT_DIM"], width=200, anchor="w"
                     ).pack(side="left")
        self.mouse_btn_var = ctk.StringVar(value="left")
        ctk.CTkOptionMenu(
            row, variable=self.mouse_btn_var,
            values=["left", "right", "middle"],
            fg_color=self.colors["BG_ENTRY"],
            button_color=self.colors["ACCENT"],
            button_hover_color=self.colors["ACCENT"],
            text_color="#000",
            dropdown_fg_color=self.colors["BG_ENTRY"],
            dropdown_text_color=self.colors["TEXT_DIM"],
            dropdown_hover_color=self.colors["BG_CARD"],
            font=self.F_ENTRY, corner_radius=0, height=30,
        ).pack(side="left", fill="x", expand=True)

        self.mouse_bind = self._row(p, "KLAWISZ AKTYWACJI", "f6", "np. f6")
        self._sep(p)

        self.mouse_btn = ctk.CTkButton(
            p, text="[ START ]", font=self.F_BTN,
            fg_color=self.colors["BG_ENTRY"], hover_color="#1e1e1e",
            text_color=self.colors["ACCENT"],
            border_color=self.colors["ACCENT"], border_width=1,
            corner_radius=0, height=36,
            command=self.toggle_mouse,
        )
        self.mouse_btn.pack(fill="x", padx=14, pady=(0, 10))

    # ─────────────────────────────────────────────
    #  PANEL KLAWIATURA
    # ─────────────────────────────────────────────
    def _build_kb_panel(self, p):
        self._sep(p)
        self.key_entry      = self._row(p, "KLAWISZ DO KLIKANIA", "space", "np. space, e, q")
        self.interval_entry = self._row(p, "ODSTĘP  (sekundy)", "0.5", "np. 0.1")
        self.kb_human       = self._row(p, "HUMANIZER  (% losowości, 0=wył)", "0", "0-100")
        self.kb_delay       = self._row(p, "OPÓŹNIENIE STARTU  (s)", "0", "np. 3")
        self.kb_bind_entry  = self._row(p, "KLAWISZ AKTYWACJI", "f7", "np. f7")
        self._sep(p)

        self.kb_btn = ctk.CTkButton(
            p, text="[ START ]", font=self.F_BTN,
            fg_color=self.colors["BG_ENTRY"], hover_color="#1e1e1e",
            text_color=self.colors["ACCENT"],
            border_color=self.colors["ACCENT"], border_width=1,
            corner_radius=0, height=36,
            command=self.toggle_kb,
        )
        self.kb_btn.pack(fill="x", padx=14, pady=(0, 10))

    # ─────────────────────────────────────────────
    #  PANEL USTAWIENIA
    # ─────────────────────────────────────────────
    def _build_settings_panel(self, p):
        self._sep(p)

        # ── Presety kolorów ───────────────────────
        ctk.CTkLabel(p, text="KOLOR AKCENTU", font=self.F_LABEL,
                     text_color=self.colors["TEXT_DIM"], anchor="w"
                     ).pack(fill="x", padx=14, pady=(4, 4))

        preset_frame = ctk.CTkFrame(p, fg_color="transparent", corner_radius=0)
        preset_frame.pack(fill="x", padx=14, pady=(0, 6))

        self._preset_btns = []
        for name, vals in PRESETS.items():
            color = vals["ACCENT"]
            btn = ctk.CTkButton(
                preset_frame, text="", width=32, height=32,
                fg_color=color, hover_color=color,
                corner_radius=0, border_width=2,
                border_color=self.colors["BORDER"],
                command=lambda c=color: self._apply_accent(c)
            )
            btn.pack(side="left", padx=3)
            self._preset_btns.append((btn, color))

        self._sep(p)

        # ── RGB Mode ──────────────────────────────
        rgb_row = ctk.CTkFrame(p, fg_color="transparent", corner_radius=0)
        rgb_row.pack(fill="x", padx=14, pady=4)
        ctk.CTkLabel(rgb_row, text="RGB MODE  (cycling rainbow)",
                     font=self.F_LABEL, text_color=self.colors["TEXT_DIM"],
                     width=200, anchor="w").pack(side="left")

        self._rgb_btn = ctk.CTkButton(
            rgb_row, text="[ WŁĄCZ ]", font=self.F_BTN,
            fg_color=self.colors["BG_ENTRY"], hover_color="#1e1e1e",
            text_color=self.colors["ACCENT"],
            border_color=self.colors["ACCENT"], border_width=1,
            corner_radius=0, height=30, width=120,
            command=self.toggle_rgb,
        )
        self._rgb_btn.pack(side="left", padx=(0, 8))

        # ── Własny kolor hex ──────────────────────
        self._sep(p)
        ctk.CTkLabel(p, text="WŁASNY KOLOR  (hex np. #ff0080)",
                     font=self.F_LABEL, text_color=self.colors["TEXT_DIM"],
                     anchor="w").pack(fill="x", padx=14, pady=(4, 4))

        hex_row = ctk.CTkFrame(p, fg_color="transparent", corner_radius=0)
        hex_row.pack(fill="x", padx=14, pady=(0, 6))
        self._custom_hex = ctk.CTkEntry(
            hex_row, placeholder_text="#rrggbb",
            fg_color=self.colors["BG_ENTRY"],
            border_color=self.colors["BORDER"], border_width=1,
            text_color=self.colors["ACCENT"],
            placeholder_text_color=self.colors["TEXT_DIM"],
            font=self.F_ENTRY, corner_radius=0, height=30, width=140,
        )
        self._custom_hex.pack(side="left", padx=(0, 8))
        ctk.CTkButton(
            hex_row, text="ZASTOSUJ", font=self.F_BTN,
            fg_color=self.colors["BG_ENTRY"], hover_color="#1e1e1e",
            text_color=self.colors["ACCENT"],
            border_color=self.colors["ACCENT"], border_width=1,
            corner_radius=0, height=30,
            command=self._apply_custom_hex,
        ).pack(side="left")

        # podgląd aktualnego koloru
        self._sep(p)
        preview_row = ctk.CTkFrame(p, fg_color="transparent", corner_radius=0)
        preview_row.pack(fill="x", padx=14, pady=4)
        ctk.CTkLabel(preview_row, text="AKTUALNY AKCENT:",
                     font=self.F_LABEL, text_color=self.colors["TEXT_DIM"],
                     width=160, anchor="w").pack(side="left")
        self._preview_box = ctk.CTkFrame(preview_row,
                                          fg_color=self.colors["ACCENT"],
                                          width=60, height=26, corner_radius=0)
        self._preview_box.pack(side="left", padx=(0, 10))
        self._preview_label = ctk.CTkLabel(preview_row,
                                            text=self.colors["ACCENT"],
                                            font=self.F_ENTRY,
                                            text_color=self.colors["ACCENT"])
        self._preview_label.pack(side="left")

    # ─────────────────────────────────────────────
    #  KOLOR – APPLY
    # ─────────────────────────────────────────────
    def _apply_accent(self, color):
        # zatrzymaj RGB jeśli było włączone
        self._rgb_running = False
        self.colors["ACCENT"] = color
        self._repaint(color)

    def _apply_custom_hex(self):
        val = self._custom_hex.get().strip()
        if not val.startswith("#") or len(val) not in (4, 7):
            return
        try:
            hex_to_rgb(val)  # walidacja
        except Exception:
            return
        self._apply_accent(val)

    def _repaint(self, color):
        """Przerysuj wszystkie elementy z nowym kolorem akcentu"""
        c = color
        dim = self._dim(c)

        self._topbar_title.configure(text_color=c)
        self._accent_line.configure(fg_color=c)

        # nav btns
        for k, btn in self._nav_btns.items():
            if k == self.active_tab:
                btn.configure(fg_color=c, text_color="#000")

        # mouse
        self.mouse_btn.configure(text_color=c, border_color=c)
        if self.mouse_running:
            self.mouse_btn.configure(fg_color=c, text_color="#000")

        # kb
        self.kb_btn.configure(text_color=c, border_color=c)
        if self.kb_running:
            self.kb_btn.configure(fg_color=c, text_color="#000")

        # rgb btn
        self._rgb_btn.configure(text_color=c, border_color=c)

        # preview
        self._preview_box.configure(fg_color=c)
        self._preview_label.configure(text=c, text_color=c)

    def _dim(self, hex_color):
        r, g, b = hex_to_rgb(hex_color)
        return rgb_to_hex(r * 0.8, g * 0.8, b * 0.8)

    # ─────────────────────────────────────────────
    #  RGB MODE
    # ─────────────────────────────────────────────
    def toggle_rgb(self):
        self._rgb_running = not self._rgb_running
        if self._rgb_running:
            self._rgb_btn.configure(text="[ WYŁĄCZ ]",
                                    fg_color=self.colors["ACCENT"],
                                    text_color="#000")
            t = threading.Thread(target=self._rgb_loop, daemon=True)
            t.start()
        else:
            self._rgb_btn.configure(text="[ WŁĄCZ ]",
                                    fg_color=self.colors["BG_ENTRY"],
                                    text_color=self.colors["ACCENT"])

    def _rgb_loop(self):
        hue = 0.0
        while self._rgb_running:
            r, g, b = self._hsv_to_rgb(hue, 1.0, 1.0)
            color = rgb_to_hex(r, g, b)
            self.colors["ACCENT"] = color
            self.after(0, lambda c=color: self._repaint(c))
            hue = (hue + 0.005) % 1.0
            time.sleep(0.03)

    @staticmethod
    def _hsv_to_rgb(h, s, v):
        i = int(h * 6)
        f = h * 6 - i
        p = v * (1 - s)
        q = v * (1 - f * s)
        t = v * (1 - (1 - f) * s)
        i %= 6
        if i == 0: r, g, b = v, t, p
        elif i == 1: r, g, b = q, v, p
        elif i == 2: r, g, b = p, v, t
        elif i == 3: r, g, b = p, q, v
        elif i == 4: r, g, b = t, p, v
        elif i == 5: r, g, b = v, p, q
        return int(r * 255), int(g * 255), int(b * 255)

    # ─────────────────────────────────────────────
    #  TOGGLE CLICKERS
    # ─────────────────────────────────────────────
    def toggle_mouse(self):
        self.mouse_running = not self.mouse_running
        c = self.colors["ACCENT"]
        if self.mouse_running:
            self.mouse_btn.configure(text="[ STOP ]", fg_color=c,
                                     hover_color=self._dim(c), text_color="#000")
        else:
            self.mouse_btn.configure(text="[ START ]",
                                     fg_color=self.colors["BG_ENTRY"],
                                     hover_color="#1e1e1e", text_color=c)

    def toggle_kb(self):
        self.kb_running = not self.kb_running
        c = self.colors["ACCENT"]
        if self.kb_running:
            self.kb_btn.configure(text="[ STOP ]", fg_color=c,
                                  hover_color=self._dim(c), text_color="#000")
        else:
            self.kb_btn.configure(text="[ START ]",
                                  fg_color=self.colors["BG_ENTRY"],
                                  hover_color="#1e1e1e", text_color=c)

    def toggle_visibility(self):
        if self.visible:
            self.after(0, self.withdraw)
        else:
            self.after(0, self.deiconify)
        self.visible = not self.visible

    # ─────────────────────────────────────────────
    #  HUMANIZER
    # ─────────────────────────────────────────────
    def _humanize(self, delay, entry):
        try:
            pct = float(entry.get())
            if pct > 0:
                delta = delay * (pct / 100)
                delay += random.uniform(-delta, delta)
        except Exception:
            pass
        return max(delay, 0.001)

    # ─────────────────────────────────────────────
    #  LOOPS
    # ─────────────────────────────────────────────
    def _mouse_loop(self):
        while True:
            if self.mouse_running:
                try:
                    sd = float(self.mouse_delay.get())
                    if sd > 0:
                        time.sleep(sd)
                except Exception:
                    pass
                while self.mouse_running:
                    try:
                        cps   = float(self.mouse_cps.get())
                        delay = self._humanize(1.0 / max(cps, 0.01), self.mouse_human)
                        btn   = self.mouse_btn_var.get()
                        t0    = time.perf_counter()
                        pydirectinput.click(button=btn)
                        rest = delay - (time.perf_counter() - t0)
                        if rest > 0:
                            time.sleep(rest)
                    except Exception:
                        time.sleep(0.5)
            else:
                time.sleep(0.05)

    def _kb_loop(self):
        while True:
            if self.kb_running:
                try:
                    sd = float(self.kb_delay.get())
                    if sd > 0:
                        time.sleep(sd)
                except Exception:
                    pass
                while self.kb_running:
                    key = self.key_entry.get().strip()
                    try:
                        interval = self._humanize(
                            float(self.interval_entry.get()), self.kb_human)
                        if key:
                            pydirectinput.press(key)
                        time.sleep(interval)
                    except Exception:
                        time.sleep(1)
            else:
                time.sleep(0.1)

    def _check_update_thread(self):
        has_update, new_ver = check_for_update()
        if has_update:
            self.after(0, lambda: self._show_update_banner(new_ver))

    # ─────────────────────────────────────────────
    #  HOTKEYS
    # ─────────────────────────────────────────────
    def _hotkey_loop(self):
        while True:
            try:
                mk = self.mouse_bind.get().strip()
                kk = self.kb_bind_entry.get().strip()
                if mk and keyboard.is_pressed(mk):
                    self.after(0, self.toggle_mouse)
                    time.sleep(0.3)
                if kk and keyboard.is_pressed(kk):
                    self.after(0, self.toggle_kb)
                    time.sleep(0.3)
                if keyboard.is_pressed("f1"):
                    self.toggle_visibility()
                    time.sleep(0.3)
            except Exception:
                pass
            time.sleep(0.01)


if __name__ == "__main__":
    App().mainloop()