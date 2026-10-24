# ui_helpers.py

import tkinter as tk
import ctypes
import pyperclip
import keyboard

from .dictionary_loader import DictionaryEntry


VK_CAPITAL = 0x14  # virtual key code for CapsLock

def ensure_caps_off():
    """If CapsLock is currently ON at OS level, turn it OFF."""
    state = ctypes.windll.user32.GetKeyState(VK_CAPITAL)
    if state & 1:  # low bit = toggle state
        keyboard.press_and_release("caps lock")



# ---------- Formatting ----------

def format_result_for_popup(result, max_entries: int = 3, max_meanings: int = 3) -> str:
    entries: list[DictionaryEntry] = result.entries
    lang = result.language
    query = result.query

    if not entries:
        return f"{query}\n\n(no matches)"

    lines: list[str] = []
    lines.append(f"{query}  ({'JP' if lang == 'ja' else 'EN'})")
    lines.append("")

    for i, entry in enumerate(entries[:max_entries], start=1):
        kanji = entry.kanji if entry.kanji else entry.reading
        reading = entry.reading or ""

        lines.append(f"{i}) {kanji}（{reading}）")

        for m in entry.meanings[:max_meanings]:
            lines.append(f"   - {m}")

        if len(entry.meanings) > max_meanings:
            lines.append("   ...")

        lines.append("")

    return "\n".join(lines).strip()


# ---------- Mouse position helper (Win32) ----------

class _POINT(ctypes.Structure):
    _fields_ = [("x", ctypes.c_long), ("y", ctypes.c_long)]


def get_cursor_position() -> tuple[int, int]:
    pt = _POINT()
    ctypes.windll.user32.GetCursorPos(ctypes.byref(pt))
    return pt.x, pt.y


# ---------- Popup window ----------

class PopupWindow:
    def _on_global_click(self, event):
        # Get popup window position
        x1 = self.root.winfo_rootx()
        y1 = self.root.winfo_rooty()
        x2 = x1 + self.root.winfo_width()
        y2 = y1 + self.root.winfo_height()

        # If click is outside the popup → hide it
        if not (x1 <= event.x_root <= x2 and y1 <= event.y_root <= y2):
            self.hide()

    def __init__(self, title: str = "JP↔EN"):
        self.root = tk.Tk()
        self.root.title(title)
        self.root.attributes("-topmost", True)
        self.root.withdraw()  # start hidden

        self.text_var = tk.StringVar()
        label = tk.Label(
            self.root,
            textvariable=self.text_var,
            justify="left",
            anchor="w",
            font=("Segoe UI", 10),
        )
        label.pack(padx=8, pady=8)

        # Hide on Esc or click anywhere in the window
        # Hide on ESC
        self.root.bind("<Escape>", lambda e: self.hide())

        # Hide when clicking outside the popup
        self.root.bind("<FocusOut>", lambda e: self.hide())

        # Bind a global click detection
        self.root.bind_all("<Button-1>", self._on_global_click)


    def show(self, text: str, x: int | None = None, y: int | None = None):
        self.text_var.set(text)
        self.root.update_idletasks()

        if x is not None and y is not None:
            # Small offset so we don't cover the cursor exactly
            offset_x, offset_y = 16, 16
            self.root.geometry(f"+{x + offset_x}+{y + offset_y}")

        self.root.deiconify()
        self.root.lift()
        self.root.attributes("-topmost", True)

    def hide(self):
        self.root.withdraw()

        # Clear clipboard so stale text doesn't get reused
        try:
            pyperclip.copy("")
        except pyperclip.PyperclipException:
            pass

        # Only runs when a popup actually existed → safe place to "clean up" CapsLock
        ensure_caps_off()


    def run(self):
        self.root.mainloop()
