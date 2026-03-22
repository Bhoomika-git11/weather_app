# -*- coding: utf-8 -*-
import tkinter as tk
from tkinter import ttk
import requests
import threading
import datetime

# ─── CONFIG ───────────────────────────────────────────────
API_KEY = "6335e12d2bd338b04d092c6b79c6549a"

STATES = [
    "Andhra Pradesh","Arunachal Pradesh","Assam","Bihar","Chhattisgarh",
    "Goa","Gujarat","Haryana","Himachal Pradesh","Jharkhand","Karnataka",
    "Kerala","Madhya Pradesh","Maharashtra","Manipur","Meghalaya","Mizoram",
    "Nagaland","Odisha","Punjab","Rajasthan","Sikkim","Tamil Nadu","Telangana",
    "Tripura","Uttar Pradesh","Uttarakhand","West Bengal"
]

# ── Purple Galaxy Palette ─────────────────────────────────
BG_DARK   = "#0b0118"
BG_CARD   = "#160a2e"
BG_CARD2  = "#0f0720"
ACCENT    = "#c77dff"
ACCENT2   = "#7b2fff"
ACCENT3   = "#e0aaff"
TEXT_MAIN = "#e8d5ff"
TEXT_DIM  = "#9d7fbd"
BTN_BG    = "#1e0b3a"
RED_ERR   = "#ff6b9d"
GOLD      = "#ffd166"

WEATHER_ICONS = {
    "clear":   "☀️", "cloud":   "☁️",  "rain":    "🌧️",
    "thunder": "⛈️", "snow":    "❄️",  "mist":    "🌫️",
    "haze":    "🌫️", "drizzle": "🌦️", "smoke":   "🌫️",
    "default": "🌌",
}

def get_weather_icon(condition: str) -> str:
    c = condition.lower()
    for key, icon in WEATHER_ICONS.items():
        if key in c:
            return icon
    return WEATHER_ICONS["default"]


# ─── SPINNER ──────────────────────────────────────────────
class Spinner(tk.Canvas):
    def __init__(self, master, size=30, **kw):
        kw.pop("bg", None)
        super().__init__(master, width=size, height=size,
                         highlightthickness=0, bd=0, bg=BG_DARK, **kw)
        self._angle   = 0
        self._running = False
        self._arc = self.create_arc(3, 3, size-3, size-3,
                                    start=0, extent=270,
                                    outline=ACCENT, width=3, style="arc")

    def start(self):
        self._running = True
        self._spin()

    def stop(self):
        self._running = False

    def _spin(self):
        if not self._running:
            return
        self._angle = (self._angle + 9) % 360
        self.itemconfig(self._arc, start=self._angle)
        self.after(16, self._spin)


# ─── PULSE BUTTON ─────────────────────────────────────────
class PulseButton(tk.Canvas):
    def __init__(self, master, text="", command=None, **kw):
        kw.pop("bg", None)
        super().__init__(master, width=230, height=46,
                         highlightthickness=0, bd=0, bg=BG_DARK, **kw)
        self.command    = command
        self._text      = text
        self._animating = False
        self._pulse     = 0.0
        self._draw()
        self.bind("<Enter>",    lambda e: self._on_enter())
        self.bind("<Leave>",    lambda e: self._on_leave())
        self.bind("<Button-1>", lambda e: self._on_click())

    def _draw(self, glow=0.0):
        self.delete("all")
        w, h, r = 230, 46, 12
        for i in range(5, 0, -1):
            c = self._blend(BG_DARK, ACCENT2, glow * i * 0.12)
            self._rrect(i, i, w-i, h-i, r, fill="", outline=c)
        self._rrect(0, 0, w, h, r, fill=BTN_BG, outline=ACCENT)
        self.create_text(w//2, h//2, text=self._text,
                         fill=ACCENT3, font=("Courier New", 12, "bold"))

    def _rrect(self, x1, y1, x2, y2, r, **kw):
        pts = [x1+r,y1, x2-r,y1, x2,y1+r, x2,y2-r,
               x2-r,y2, x1+r,y2, x1,y2-r, x1,y1+r]
        self.create_polygon(pts, smooth=False, **kw)
        for cx1,cy1,cx2,cy2,s in [
            (x1,y1,x1+2*r,y1+2*r,90),(x2-2*r,y1,x2,y1+2*r,0),
            (x2-2*r,y2-2*r,x2,y2,270),(x1,y2-2*r,x1+2*r,y2,180)]:
            self.create_arc(cx1,cy1,cx2,cy2, start=s, extent=90,
                            style="pie", **kw)

    def _blend(self, c1, c2, t):
        t = max(0.0, min(1.0, t))
        r1,g1,b1 = int(c1[1:3],16),int(c1[3:5],16),int(c1[5:7],16)
        r2,g2,b2 = int(c2[1:3],16),int(c2[3:5],16),int(c2[5:7],16)
        return "#{:02x}{:02x}{:02x}".format(
            int(r1+(r2-r1)*t), int(g1+(g2-g1)*t), int(b1+(b2-b1)*t))

    def _on_enter(self):
        self._animating = True
        self._pulse = 0.0
        self._rise()

    def _on_leave(self):
        self._animating = False
        self._draw(0)

    def _rise(self):
        if not self._animating:
            return
        self._pulse = min(self._pulse + 0.08, 1.0)
        self._draw(self._pulse)
        if self._pulse < 1.0:
            self.after(16, self._rise)

    def _on_click(self):
        self._draw(1.0)
        self.after(120, lambda: self._draw(0))
        if self.command:
            self.command()

    def set_loading(self, loading: bool):
        if loading:
            self._orig  = self._text
            self._text  = "  Fetching..."
        else:
            self._text  = getattr(self, "_orig", self._text)
        self._draw(0)


# ─── STAT CARD ────────────────────────────────────────────
class StatCard(tk.Frame):
    def __init__(self, master, icon, label, **kw):
        super().__init__(master, bg=BG_CARD2,
                         highlightbackground=ACCENT2,
                         highlightthickness=1,
                         padx=10, pady=10, **kw)
        tk.Label(self, text=icon, bg=BG_CARD2,
                 font=("Segoe UI Emoji", 22), fg=ACCENT).pack()
        tk.Label(self, text=label, bg=BG_CARD2,
                 font=("Courier New", 8), fg=TEXT_DIM).pack()
        self.val = tk.Label(self, text="—", bg=BG_CARD2,
                            font=("Courier New", 16, "bold"), fg=TEXT_MAIN)
        self.val.pack()

    def set(self, value: str):
        self.val.config(text=value, fg=ACCENT)
        self.after(500, lambda: self.val.config(fg=TEXT_MAIN))


# ─── MAIN APP ─────────────────────────────────────────────
class WeatherApp:
    def __init__(self):
        self.win = tk.Tk()
        self.win.title("Weather Forecast - India")
        self.win.geometry("600x800")
        self.win.minsize(480, 680)
        self.win.configure(bg=BG_DARK)

        # Allow maximize / free resize
        self.win.resizable(True, True)

        # Make root grid stretch
        self.win.rowconfigure(0, weight=1)
        self.win.columnconfigure(0, weight=1)

        self._build_ui()
        self._tick_clock()
        self.win.mainloop()

    # ── BUILD UI ─────────────────────────────────────────
    def _build_ui(self):
        # Outer container that fills the whole window
        outer = tk.Frame(self.win, bg=BG_DARK)
        outer.grid(row=0, column=0, sticky="nsew")
        outer.rowconfigure(5, weight=1)   # stat cards row stretches
        outer.columnconfigure(0, weight=1)

        # ── Clock bar ────────────────────────────────────
        clock_bar = tk.Frame(outer, bg=BG_CARD2,
                             highlightbackground=ACCENT2,
                             highlightthickness=1)
        clock_bar.grid(row=0, column=0, sticky="ew", padx=0, pady=(0,0))
        clock_bar.columnconfigure(1, weight=1)

        self.clock_lbl = tk.Label(clock_bar, text="", bg=BG_CARD2,
                                  fg=ACCENT, font=("Courier New", 13, "bold"),
                                  padx=14, pady=6)
        self.clock_lbl.grid(row=0, column=0, sticky="w")

        self.date_lbl = tk.Label(clock_bar, text="", bg=BG_CARD2,
                                 fg=TEXT_DIM, font=("Courier New", 10),
                                 padx=14)
        self.date_lbl.grid(row=0, column=2, sticky="e")

        # ── Title block ───────────────────────────────────
        title_frame = tk.Frame(outer, bg=BG_DARK, pady=10)
        title_frame.grid(row=1, column=0, sticky="ew")
        title_frame.columnconfigure(0, weight=1)

        tk.Label(title_frame, text="WEATHER FORECAST",
                 bg=BG_DARK, fg=ACCENT,
                 font=("Courier New", 22, "bold")).pack()
        tk.Label(title_frame, text="India  -  State & City Monitor",
                 bg=BG_DARK, fg=TEXT_DIM,
                 font=("Courier New", 10)).pack()

        sep = tk.Frame(outer, bg=ACCENT2, height=1)
        sep.grid(row=2, column=0, sticky="ew", padx=20, pady=(0, 6))

        # ── Search + button ───────────────────────────────
        search_frame = tk.Frame(outer, bg=BG_DARK, padx=20)
        search_frame.grid(row=3, column=0, sticky="ew", pady=(0, 4))
        search_frame.columnconfigure(0, weight=1)

        tk.Label(search_frame, text="SELECT STATE / CITY",
                 bg=BG_DARK, fg=TEXT_DIM,
                 font=("Courier New", 8, "bold")).grid(
                     row=0, column=0, sticky="w")

        self.city_var = tk.StringVar()
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("G.TCombobox",
                        fieldbackground=BG_CARD, background=BTN_BG,
                        foreground=TEXT_MAIN, selectbackground=BTN_BG,
                        selectforeground=ACCENT, bordercolor=ACCENT2,
                        arrowcolor=ACCENT, font=("Courier New", 12))
        style.map("G.TCombobox",
                  fieldbackground=[("readonly", BG_CARD)],
                  foreground=[("readonly", TEXT_MAIN)])

        self.combo = ttk.Combobox(search_frame, values=STATES,
                                  textvariable=self.city_var,
                                  style="G.TCombobox",
                                  font=("Courier New", 12))
        self.combo.set("Choose a state or type a city...")
        self.combo.grid(row=1, column=0, sticky="ew", ipady=6, pady=(4, 8))

        # Button row (centred)
        btn_row = tk.Frame(search_frame, bg=BG_DARK)
        btn_row.grid(row=2, column=0)

        self.btn = PulseButton(btn_row, text=">>  CHECK WEATHER",
                               command=self._fetch_threaded)
        self.btn.pack(side="left")

        self.spinner = Spinner(btn_row, size=32)
        self.spinner.pack(side="left", padx=10)
        self.spinner.stop()

        # Status label
        self.status_var = tk.StringVar()
        self.status_lbl = tk.Label(search_frame, textvariable=self.status_var,
                                   bg=BG_DARK, fg=RED_ERR,
                                   font=("Courier New", 9))
        self.status_lbl.grid(row=3, column=0, pady=(2, 0))

        # ── Condition card ────────────────────────────────
        cond_outer = tk.Frame(outer, bg=BG_DARK, padx=20, pady=4)
        cond_outer.grid(row=4, column=0, sticky="ew")
        cond_outer.columnconfigure(0, weight=1)

        cond_frame = tk.Frame(cond_outer, bg=BG_CARD,
                              highlightbackground=ACCENT2,
                              highlightthickness=1)
        cond_frame.pack(fill="x")
        cond_frame.columnconfigure(1, weight=1)

        self.icon_lbl = tk.Label(cond_frame, text="🌌", bg=BG_CARD,
                                 font=("Segoe UI Emoji", 52), padx=10, pady=8)
        self.icon_lbl.grid(row=0, column=0, rowspan=3, sticky="ns")

        self.condition_lbl = tk.Label(cond_frame, text="--- ---",
                                      bg=BG_CARD, fg=ACCENT,
                                      font=("Courier New", 22, "bold"),
                                      anchor="w")
        self.condition_lbl.grid(row=0, column=1, sticky="sw", padx=8, pady=(10,0))

        self.desc_lbl = tk.Label(cond_frame, text="No data yet",
                                 bg=BG_CARD, fg=TEXT_DIM,
                                 font=("Courier New", 11, "italic"),
                                 anchor="w")
        self.desc_lbl.grid(row=1, column=1, sticky="w", padx=8)

        self.city_disp = tk.Label(cond_frame, text="",
                                  bg=BG_CARD, fg=GOLD,
                                  font=("Courier New", 10, "bold"),
                                  anchor="w")
        self.city_disp.grid(row=2, column=1, sticky="nw", padx=8, pady=(0,8))

        # ── Temperature card ──────────────────────────────
        temp_outer = tk.Frame(outer, bg=BG_DARK, padx=20, pady=4)
        temp_outer.grid(row=5, column=0, sticky="ew")
        temp_outer.columnconfigure(0, weight=1)

        temp_frame = tk.Frame(temp_outer, bg=BG_CARD,
                              highlightbackground=ACCENT,
                              highlightthickness=1)
        temp_frame.pack(fill="x")
        temp_frame.columnconfigure(2, weight=1)

        tk.Label(temp_frame, text="TEMPERATURE", bg=BG_CARD,
                 fg=TEXT_DIM, font=("Courier New", 8, "bold"),
                 padx=14, pady=8).grid(row=0, column=0,
                                       columnspan=3, sticky="w")

        self.temp_val = tk.Label(temp_frame, text="--", bg=BG_CARD,
                                 fg=ACCENT, font=("Courier New", 52, "bold"),
                                 padx=14)
        self.temp_val.grid(row=1, column=0, sticky="w", pady=(0,8))

        tk.Label(temp_frame, text="°C", bg=BG_CARD, fg=ACCENT2,
                 font=("Courier New", 22, "bold")).grid(
                     row=1, column=1, sticky="sw", pady=(0,14))

        self.feels_lbl = tk.Label(temp_frame, text="", bg=BG_CARD,
                                  fg=TEXT_DIM, font=("Courier New", 11))
        self.feels_lbl.grid(row=1, column=2, sticky="w", padx=20)

        # ── Stat cards ────────────────────────────────────
        cards_outer = tk.Frame(outer, bg=BG_DARK, padx=20, pady=4)
        cards_outer.grid(row=6, column=0, sticky="ew")
        cards_outer.columnconfigure((0,1,2,3), weight=1)

        self.card_hum  = StatCard(cards_outer, "💧", "HUMIDITY %")
        self.card_pres = StatCard(cards_outer, "🔵", "PRESSURE hPa")
        self.card_wind = StatCard(cards_outer, "💨", "WIND km/h")
        self.card_vis  = StatCard(cards_outer, "👁", "VISIBILITY km")

        for i, card in enumerate((self.card_hum, self.card_pres,
                                   self.card_wind, self.card_vis)):
            card.grid(row=0, column=i, sticky="nsew", padx=3)

        # ── Sunrise / Sunset ──────────────────────────────
        sun_outer = tk.Frame(outer, bg=BG_DARK, padx=20, pady=4)
        sun_outer.grid(row=7, column=0, sticky="ew")
        sun_outer.columnconfigure(0, weight=1)

        sun = tk.Frame(sun_outer, bg=BG_CARD2,
                       highlightbackground=ACCENT2, highlightthickness=1)
        sun.pack(fill="x")
        sun.columnconfigure((0,2), weight=1)

        self.sunrise_lbl = tk.Label(sun, text="Sunrise: --",
                                    bg=BG_CARD2, fg=GOLD,
                                    font=("Courier New", 11), pady=10)
        self.sunrise_lbl.grid(row=0, column=0)

        tk.Frame(sun, bg=ACCENT2, width=1).grid(
            row=0, column=1, sticky="ns", pady=8)

        self.sunset_lbl = tk.Label(sun, text="Sunset: --",
                                   bg=BG_CARD2, fg="#ff9a6c",
                                   font=("Courier New", 11), pady=10)
        self.sunset_lbl.grid(row=0, column=2)

        # ── Footer ────────────────────────────────────────
        tk.Label(outer, text="Powered by OpenWeatherMap API",
                 bg=BG_DARK, fg=TEXT_DIM,
                 font=("Courier New", 8), pady=6).grid(
                     row=8, column=0)

    # ── LIVE CLOCK ────────────────────────────────────────
    def _tick_clock(self):
        now = datetime.datetime.now()
        self.clock_lbl.config(text=now.strftime("  %I:%M:%S %p"))
        self.date_lbl.config(text=now.strftime("%A, %d %B %Y"))
        self.win.after(1000, self._tick_clock)

    # ── FETCH ─────────────────────────────────────────────
    def _fetch_threaded(self):
        city = self.city_var.get().strip()
        if not city or city.startswith("Choose"):
            self._set_status("  Please select or type a city / state.", RED_ERR)
            return
        self.btn.set_loading(True)
        self.spinner.start()
        self._set_status("Connecting to weather service...", ACCENT2)
        threading.Thread(target=self._get_data,
                         args=(city,), daemon=True).start()

    def _get_data(self, city: str):
        try:
            url = (f"https://api.openweathermap.org/data/2.5/weather"
                   f"?q={city},IN&appid={API_KEY}&units=metric")
            resp = requests.get(url, timeout=8)
            data = resp.json()
            if resp.status_code != 200:
                self.win.after(0, lambda: self._show_error(
                    data.get("message", "Unknown error")))
                return
            self.win.after(0, lambda: self._update_ui(data))
        except requests.exceptions.ConnectionError:
            self.win.after(0, lambda: self._show_error(
                "No internet connection."))
        except Exception as ex:
            self.win.after(0, lambda: self._show_error(str(ex)))

    def _update_ui(self, d: dict):
        condition   = d["weather"][0]["main"]
        description = d["weather"][0]["description"].title()
        temp        = d["main"]["temp"]
        feels       = d["main"]["feels_like"]
        humidity    = d["main"]["humidity"]
        pressure    = d["main"]["pressure"]
        wind_kmh    = round(d["wind"]["speed"] * 3.6, 1)
        vis_km      = round(d.get("visibility", 0) / 1000, 1)
        city_name   = d["name"]
        sunrise = datetime.datetime.fromtimestamp(
            d["sys"]["sunrise"]).strftime("%I:%M %p")
        sunset  = datetime.datetime.fromtimestamp(
            d["sys"]["sunset"]).strftime("%I:%M %p")

        self.icon_lbl.config(text=get_weather_icon(condition))
        self.condition_lbl.config(text=condition.upper())
        self.desc_lbl.config(text=description)
        self.city_disp.config(text=f"  {city_name}, India")
        self.temp_val.config(text=f"{temp:.1f}")
        self.feels_lbl.config(text=f"Feels like  {feels:.1f} C")

        self.card_hum.set(f"{humidity}%")
        self.card_pres.set(f"{pressure}")
        self.card_wind.set(f"{wind_kmh}")
        self.card_vis.set(f"{vis_km}")

        self.sunrise_lbl.config(text=f"Sunrise:  {sunrise}")
        self.sunset_lbl.config(text=f"Sunset:   {sunset}")

        self.spinner.stop()
        self.btn.set_loading(False)
        self._set_status(
            f"  Last updated: "
            f"{datetime.datetime.now().strftime('%I:%M %p')}", ACCENT)

    def _show_error(self, msg: str):
        self.spinner.stop()
        self.btn.set_loading(False)
        self._set_status(f"  Error: {msg}", RED_ERR)

    def _set_status(self, msg: str, color: str):
        self.status_var.set(msg)
        self.status_lbl.config(fg=color)


# ─── ENTRY POINT ──────────────────────────────────────────
if __name__ == "__main__":
    WeatherApp()
