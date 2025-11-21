"""
System 7 UI Component Library for Tkinter
Pixel-perfect recreation of Apple System 7 interface elements.

This module provides custom widgets that manually draw the Platinum aesthetic:
- Beveled buttons with 3D effects
- Striped title bars with close boxes
- Inset frames for text fields
- Font fallbacks for Chicago, Monaco, Geneva
"""

import tkinter as tk
from tkinter import font as tkfont

# System 7 Palette
c_WHITE = "#FFFFFF"
c_BLACK = "#000000"
c_PLATINUM = "#C0C0C0"  # Main UI
c_DK_GRAY = "#808080"   # Shadows
c_LT_GRAY = "#FFFFFF"   # Highlights (often white in Sys7)
c_BLUE_HILI = "#000080" # Highlight for selection


class S7Font:
    """Font management with fallbacks to ensure retro look."""

    @staticmethod
    def chicago(size=10):
        """Try to find a font that looks like Chicago."""
        avail = tkfont.families()
        for f in ["Chicago", "Charcoal", "Impact", "Haettenschweiler", "Helvetica", "Arial"]:
            if f in avail:
                return (f, size, "bold" if f not in ["Chicago", "Charcoal"] else "normal")
        return ("Sans", size, "bold")

    @staticmethod
    def monaco(size=9):
        """Monospaced font for chat text."""
        return ("Monaco", size, "normal") if "Monaco" in tkfont.families() else ("Courier New", size, "normal")

    @staticmethod
    def geneva(size=9):
        """Secondary UI font."""
        return ("Geneva", size, "normal") if "Geneva" in tkfont.families() else ("Arial", size, "normal")


class S7Frame(tk.Frame):
    """Standard Platinum background."""

    def __init__(self, parent, **kwargs):
        super().__init__(parent, bg=c_PLATINUM, **kwargs)


class S7Button(tk.Canvas):
    """
    Pixel-perfect System 7 Button drawn on a Canvas.

    Features:
    - 3D beveled appearance
    - Default button gets extra black border
    - Press effect inverts colors
    - Manual pixel drawing for cross-platform consistency
    """

    def __init__(self, parent, text, command=None, width=80, height=22, default=False):
        super().__init__(parent, width=width, height=height, bg=c_PLATINUM, highlightthickness=0)
        self.command = command
        self.text_str = text
        self.is_default = default
        self.width = width
        self.height = height
        self.state = "up"

        self.bind("<Button-1>", self._on_press)
        self.bind("<ButtonRelease-1>", self._on_release)
        self.draw()

    def _on_press(self, event):
        self.state = "down"
        self.draw()

    def _on_release(self, event):
        if self.state == "down":
            self.state = "up"
            self.draw()
            if self.command:
                self.command()

    def draw(self):
        """Draw the button with bevels and text."""
        self.delete("all")
        w, h = self.width, self.height

        # Outer border (if default button, it has an extra black ring)
        offset = 0
        if self.is_default:
            self.create_rectangle(0, 0, w-1, h-1, outline=c_BLACK, width=1)
            offset = 3
            # Inner rect
            self.create_rectangle(offset, offset, w-offset-1, h-offset-1, outline=c_BLACK, width=1)
        else:
            self.create_rectangle(0, 0, w-1, h-1, outline=c_BLACK, width=1)

        # Fill
        bg = c_BLACK if self.state == "down" else c_PLATINUM
        fg = c_WHITE if self.state == "down" else c_BLACK

        # If not default, simple bevel
        if not self.is_default:
            self.create_rectangle(1, 1, w-2, h-2, fill=bg, outline="")
            if self.state == "up":
                # Highlights
                self.create_line(1, 1, w-2, 1, fill=c_WHITE)
                self.create_line(1, 1, 1, h-2, fill=c_WHITE)
                # Shadows
                self.create_line(w-2, 1, w-2, h-2, fill=c_DK_GRAY)
                self.create_line(1, h-2, w-2, h-2, fill=c_DK_GRAY)
        else:
            # Default button fill
            inner_w = w - (offset*2)
            inner_h = h - (offset*2)
            self.create_rectangle(offset+1, offset+1, w-offset-2, h-offset-2, fill=bg, outline="")

        # Text
        self.create_text(w/2, h/2, text=self.text_str, fill=fg, font=S7Font.chicago(10))


class S7Window(tk.Toplevel):
    """
    A custom window with the striped title bar.

    Features:
    - Removes OS chrome (overrideredirect)
    - Draws custom striped title bar
    - Close box in top-left corner
    - Draggable by title bar
    - Black border for drop shadow effect
    """

    def __init__(self, parent, title, width=400, height=300):
        super().__init__(parent)
        self.overrideredirect(True)  # Remove OS chrome
        self.geometry(f"{width}x{height}")
        self.configure(bg=c_PLATINUM)

        # Drop shadow (simulated with a border)
        self.configure(highlightbackground=c_BLACK, highlightthickness=1)

        # Title Bar
        self.title_bar = tk.Canvas(self, height=20, bg=c_WHITE, highlightthickness=0)
        self.title_bar.pack(fill="x", side="top", pady=1, padx=1)

        # Stripes
        for i in range(2, 20, 2):
            self.title_bar.create_line(0, i, width, i, fill=c_PLATINUM)

        # Title Text Box
        self.title_bar.create_rectangle(width//2 - 60, 2, width//2 + 60, 18, fill=c_WHITE, outline="")
        self.title_bar.create_text(width//2, 10, text=title, font=S7Font.chicago(10))

        # Close Box
        self.close_btn = self.title_bar.create_rectangle(4, 4, 16, 16, outline=c_BLACK, fill=c_WHITE)

        # Drag logic
        self.title_bar.bind("<Button-1>", self.start_move)
        self.title_bar.bind("<B1-Motion>", self.do_move)
        self.title_bar.bind("<ButtonRelease-1>", self.check_close)

    def start_move(self, event):
        self.x = event.x
        self.y = event.y

    def do_move(self, event):
        deltax = event.x - self.x
        deltay = event.y - self.y
        x = self.winfo_x() + deltax
        y = self.winfo_y() + deltay
        self.geometry(f"+{x}+{y}")

    def check_close(self, event):
        """Check if click was on close box."""
        if 4 <= event.x <= 16 and 4 <= event.y <= 16:
            self.destroy()


class S7InsetFrame(tk.Frame):
    """
    Used for text fields and lists to look 'sunken'.
    Creates the classic inset appearance for input areas.
    """

    def __init__(self, parent, **kwargs):
        super().__init__(parent, bd=1, relief="sunken", bg=c_WHITE, **kwargs)
