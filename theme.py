"""
Shared visual theme for the AI Smart Attendance System.

Palette: ivory paper, deep midnight-navy ink, antique-gold accents.
Typography: a serif face (Georgia) for headings, a clean sans for body text.

Every screen imports its colours and fonts from here, so the look of the
whole application can be changed in this single file.
"""

import sys

import customtkinter as ctk


# =========================================================
# APPEARANCE
# =========================================================

ctk.set_appearance_mode("light")
ctk.set_default_color_theme("blue")


# =========================================================
# TYPOGRAPHY
# =========================================================

if sys.platform.startswith("win"):
    FONT_HEAD = "Georgia"
    FONT_BODY = "Segoe UI"
elif sys.platform == "darwin":
    FONT_HEAD = "Georgia"
    FONT_BODY = "Helvetica Neue"
else:
    FONT_HEAD = "DejaVu Serif"
    FONT_BODY = "DejaVu Sans"


# =========================================================
# CORE PALETTE
# =========================================================

BG_COLOR = "#F8F5EF"        # ivory page background
WHITE = "#FFFDFA"           # warm white card surface
INK = "#111A2E"             # midnight navy: headers, headings
PRIMARY = "#1B2B4B"         # navy: primary buttons
PRIMARY_HOVER = "#2B416E"
PRIMARY_DARK = "#111A2E"
PRIMARY_LIGHT = "#3B568A"
TINT = "#F1EADB"            # champagne tint: soft panels, hover rows
BORDER_COLOR = "#DDD2BD"    # sand: hairline borders

GOLD = "#B8934A"            # antique gold accent
GOLD_DEEP = "#8A6A2F"       # gold readable as text on ivory
GOLD_LIGHT = "#D9C28F"      # gold readable as text on navy

TEXT_COLOR = "#1E2230"
MUTED_TEXT = "#6F6A60"
PLACEHOLDER = "#9B9486"

SUCCESS = "#2F6B4F"
LIGHT_GREEN = "#E3EFE8"
DANGER = "#8E2F3A"
LIGHT_RED = "#F6E4E4"
WARNING = "#A8671F"
LIGHT_AMBER = "#F7EBD6"

LIGHT_GREY = "#F1EEE8"
GREY_HOVER = "#E7E2D8"
DARK_GREY = "#3A3F4B"
DARK_HOVER = "#24365C"

# Aliases used by individual screens
GREEN = SUCCESS
RED = DANGER
BLUE = "#2F5D8A"
ORANGE = "#B8742A"

BACKGROUND = BG_COLOR
TEXT = TEXT_COLOR
TEXT_LIGHT = MUTED_TEXT
BORDER = BORDER_COLOR
ERROR = DANGER


# =========================================================
# OPENCV (BGR) COLOURS FOR CAMERA OVERLAYS
# =========================================================

def _bgr(hex_color):
    hex_color = hex_color.lstrip("#")
    r, g, b = (int(hex_color[i:i + 2], 16) for i in (0, 2, 4))
    return (b, g, r)


CV_GOLD = _bgr(GOLD)
CV_GOLD_LIGHT = _bgr(GOLD_LIGHT)
CV_INK = _bgr(INK)
CV_IVORY = _bgr(BG_COLOR)
CV_OK = _bgr("#4FA37A")
CV_BAD = _bgr("#C9505F")
CV_WARN = _bgr("#D9A441")
CV_WHITE = (255, 255, 255)


# =========================================================
# MODERN UI HELPERS (gradients, glow, motion)
# =========================================================

import math
import tkinter as tk

from PIL import Image, ImageDraw, ImageFilter, ImageTk


def _rgb(hex_color):
    hex_color = hex_color.lstrip("#")
    return tuple(int(hex_color[i:i + 2], 16) for i in (0, 2, 4))


def _lerp(c1, c2, t):
    return tuple(int(c1[i] + (c2[i] - c1[i]) * t) for i in range(3))


def gradient_image(width, height, stops, vertical=False):
    """Linear gradient through `stops` (list of hex colours)."""
    width, height = max(1, int(width)), max(1, int(height))
    stops = [_rgb(s) for s in stops]
    length = height if vertical else width
    strip = Image.new("RGB", (1, length) if vertical else (length, 1))
    segments = len(stops) - 1
    for i in range(length):
        pos = (i / max(1, length - 1)) * segments
        k = min(int(pos), segments - 1)
        strip.putpixel((0, i) if vertical else (i, 0),
                       _lerp(stops[k], stops[k + 1], pos - k))
    return strip.resize((width, height))


class GradientLine(tk.Canvas):
    """A thin, full-width gradient rule (e.g. the gold line under a header)."""

    def __init__(self, parent, height=3, stops=None, bg=BG_COLOR):
        super().__init__(parent, height=height, bg=bg,
                         highlightthickness=0, bd=0)
        self._stops = stops or [INK, GOLD, GOLD_LIGHT, GOLD, INK]
        self._photo = None
        self._after = None
        self.bind("<Configure>", self._schedule)

    def _schedule(self, event):
        if self._after:
            self.after_cancel(self._after)
        self._after = self.after(30, lambda: self._draw(event.width, event.height))

    def _draw(self, w, h):
        self._after = None
        self._photo = ImageTk.PhotoImage(gradient_image(w, h, self._stops))
        self.delete("all")
        self.create_image(0, 0, anchor="nw", image=self._photo)


def gold_rule(parent, height=3, bg=BG_COLOR):
    return GradientLine(parent, height=height, bg=bg)


def card_accent(card, inset=22, height=3):
    """Place a short gold gradient stripe along the top edge of a card."""
    line = GradientLine(card, height=height,
                        stops=[GOLD, GOLD_LIGHT, WHITE], bg=WHITE)
    line.place(x=inset, y=0, relwidth=1.0, width=-2 * inset)
    return line


def fade_in(window, duration=450, steps=18):
    """Smoothly fade a window in on start-up (silently skipped if unsupported)."""
    try:
        window.attributes("-alpha", 0.0)
    except Exception:
        return

    def step(i=0):
        try:
            window.attributes("-alpha", min(1.0, (i + 1) / steps))
        except Exception:
            return
        if i + 1 < steps:
            window.after(max(1, duration // steps), lambda: step(i + 1))

    window.after(40, step)


def pulse(widget, color_a=GOLD, color_b=GOLD_LIGHT, period=900, attr="text_color"):
    """Gently pulse a CTk widget's colour (used for 'LIVE' indicators)."""
    state = {"on": True}

    def tick():
        try:
            widget.configure(**{attr: color_a if state["on"] else color_b})
        except Exception:
            return
        state["on"] = not state["on"]
        widget.after(period // 2, tick)

    tick()


class ScannerCanvas(tk.Canvas):
    """Animated 'face scan' illustration: glowing backdrop, silhouette,
    gold corner brackets, a sweeping scan beam and a live match readout."""

    def __init__(self, parent, width=350, height=320, bg=INK):
        super().__init__(parent, width=width, height=height, bg=bg,
                         highlightthickness=0, bd=0)
        self.w, self.h = width, height
        self._t = 0.0
        self._running = True
        self._build_backdrop()
        self._build_overlay()
        self.bind("<Destroy>", lambda e: setattr(self, "_running", False))
        self._animate()

    # ---- static art -------------------------------------------------
    def _build_backdrop(self):
        w, h = self.w, self.h
        base = gradient_image(w, h, ["#16254A", "#0E1630", "#1A1530"], vertical=True)
        glow = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        d = ImageDraw.Draw(glow)
        d.ellipse((w * 0.15, h * 0.05, w * 0.85, h * 0.75), fill=(184, 147, 74, 110))
        d.ellipse((w * 0.55, h * 0.55, w * 1.1, h * 1.1), fill=(70, 100, 190, 90))
        glow = glow.filter(ImageFilter.GaussianBlur(38))
        base = base.convert("RGBA")
        base.alpha_composite(glow)

        sil = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        s = ImageDraw.Draw(sil)
        cx = w / 2
        s.ellipse((cx - 52, h * 0.20, cx + 52, h * 0.20 + 128), fill=(255, 253, 250, 34),
                  outline=(217, 194, 143, 150), width=2)
        s.pieslice((cx - 98, h * 0.20 + 124, cx + 98, h * 0.20 + 124 + 190),
                   180, 360, fill=(255, 253, 250, 26), outline=(217, 194, 143, 110), width=2)
        for ex in (cx - 20, cx + 20):
            s.ellipse((ex - 5, h * 0.20 + 52, ex + 5, h * 0.20 + 60), fill=(217, 194, 143, 190))
        base.alpha_composite(sil)
        self._bg = ImageTk.PhotoImage(base.convert("RGB"))
        self.create_image(0, 0, anchor="nw", image=self._bg)

    def _build_overlay(self):
        w, h = self.w, self.h
        m, L = 26, 34
        for (x, y, dx, dy) in ((m, m, 1, 1), (w - m, m, -1, 1),
                               (m, h - m - 34, 1, -1), (w - m, h - m - 34, -1, -1)):
            self.create_line(x, y + dy * L, x, y, x + dx * L, y,
                             fill=GOLD, width=3, capstyle="round", joinstyle="round")
        self.beam_halo = self.create_line(m, 0, w - m, 0, fill="#2A2C3E", width=22)
        self.beam_glow = self.create_line(m, 0, w - m, 0, fill="#5A4E3A", width=9)
        self.beam = self.create_line(m, 0, w - m, 0, fill=GOLD_LIGHT, width=2)
        self.chip_bg = self.create_rectangle(0, 0, 0, 0, fill=INK, outline=GOLD, width=1)
        self.chip_text = self.create_text(w / 2, h - 30, text="", fill=GOLD_LIGHT,
                                          font=(FONT_BODY, 10, "bold"))
        self.dots = [self.create_oval(0, 0, 0, 0, fill=GOLD_LIGHT, width=0) for _ in range(14)]

    # ---- motion -----------------------------------------------------
    def _animate(self):
        if not self._running:
            return
        self._t += 0.016
        w, h = self.w, self.h
        top, bottom = 34, h - 70
        phase = (math.sin(self._t * 1.7) + 1) / 2
        y = top + (bottom - top) * phase
        self.coords(self.beam, 26, y, w - 26, y)
        self.coords(self.beam_glow, 26, y, w - 26, y)
        self.coords(self.beam_halo, 26, y, w - 26, y)

        cycle = int(self._t * 1.7 / math.pi) % 3
        label = ("SCANNING…", "ANALYSING FACE…", "MATCH VERIFIED  ✓")[cycle]
        self.itemconfigure(self.chip_text, text=label,
                           fill=("#8FD3A9" if cycle == 2 else GOLD_LIGHT))
        x1, y1, x2, y2 = self.bbox(self.chip_text)
        self.coords(self.chip_bg, x1 - 14, y1 - 6, x2 + 14, y2 + 6)

        for i, dot in enumerate(self.dots):
            ang = self._t * (0.4 + (i % 5) * 0.12) + i * 1.9
            rx, ry = 70 + (i % 4) * 26, 55 + (i % 3) * 30
            px = w / 2 + math.cos(ang) * rx
            py = h * 0.38 + math.sin(ang * 1.3) * ry
            r = 1.5 + (i % 3)
            self.coords(dot, px - r, py - r, px + r, py + r)
        self.after(33, self._animate)


# =========================================================
# WINDOW SIZING (fit any screen, behave like a normal app)
# =========================================================

def maximize(window, delay=150):
    """Open a main window maximised, like a regular desktop application."""
    def go():
        try:
            window.state("zoomed")                    # Windows / macOS
        except Exception:
            try:
                window.attributes("-zoomed", True)    # Linux
            except Exception:
                pass
    window.after(delay, go)


def fit_geometry(window, width, height, parent=None, margin=90):
    """Size a dialog to `width` x `height`, but never taller/wider than the
    screen (margin leaves room for the taskbar), centred on screen."""
    window.update_idletasks()
    sw, sh = window.winfo_screenwidth(), window.winfo_screenheight()
    width = min(width, sw - 40)
    height = min(height, sh - margin)
    x = max(0, (sw - width) // 2)
    y = max(0, (sh - height) // 2 - 15)
    window.geometry(f"{width}x{height}+{x}+{y}")
    return width, height


def cascade_path(name):
    """Locate an OpenCV Haar cascade file across OpenCV versions/installs."""
    import os
    import cv2
    folders = []
    try:
        folders.append(cv2.data.haarcascades)
    except Exception:
        pass
    pkg = os.path.dirname(cv2.__file__)
    folders += [os.path.join(pkg, "data"), pkg]
    for folder in folders:
        path = os.path.join(folder, name)
        if os.path.exists(path):
            return path
    raise RuntimeError(f"OpenCV data file {name} not found. "
                       "Reinstall with: pip install opencv-python==4.10.0.84")