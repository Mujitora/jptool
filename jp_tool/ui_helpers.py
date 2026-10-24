# ui_helpers.py

import tkinter as tk
import ctypes
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
        if event.widget.winfo_toplevel() is not self.root:
            return

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

        self.text_widget = tk.Text(
            self.root,
            width=52,
            height=1,
            wrap="word",
            borderwidth=0,
            highlightthickness=0,
            font=("Segoe UI", 10),
            state="disabled",
        )
        self.text_widget.pack(padx=8, pady=8)

        controls = tk.Frame(self.root)
        controls.pack(fill="x", padx=8, pady=(0, 8))

        self.anki_status = tk.StringVar(value="Anki unavailable")
        status_label = tk.Label(controls, textvariable=self.anki_status, anchor="w")
        status_label.pack(side="left", fill="x", expand=True)

        self.deck_button = tk.Button(
            controls,
            text="Deck",
            command=self._open_anki_settings,
        )
        self.add_button = tk.Button(
            controls,
            text="+",
            width=3,
            state="disabled",
            command=self._add_to_anki,
        )
        self.add_button.pack(side="right")

        self.deck_button.pack(side="right", padx=(4, 0))

        self._anki_available = False
        self._current_word = ""
        self._current_definition = ""
        self._on_add = None
        self._on_settings = None

        # Hide on Esc or click anywhere in the window
        # Hide on ESC
        self.root.bind("<Escape>", lambda e: self.hide())

        # Bind a global click detection
        self.root.bind_all("<Button-1>", self._on_global_click)

    def set_anki_callbacks(self, on_add, on_settings):
        self._on_add = on_add
        self._on_settings = on_settings

    def set_anki_state(self, available: bool, message: str | None = None):
        self._anki_available = available
        self.anki_status.set(message or ("Anki ready" if available else "Anki unavailable"))
        can_add = available and bool(self._current_word and self._current_definition)
        self.add_button.configure(state="normal" if can_add else "disabled")

    def set_anki_message(self, message: str):
        self.anki_status.set(message)

    def _add_to_anki(self):
        if self._on_add and self._anki_available:
            self._on_add(self._current_word, self._current_definition)

    def _open_anki_settings(self):
        if self._on_settings:
            self._on_settings()


    def show(
        self,
        text: str,
        x: int | None = None,
        y: int | None = None,
        word: str = "",
        definition: str = "",
    ):
        self._current_word = word
        self._current_definition = definition
        self.set_anki_state(self._anki_available)
        self.text_widget.configure(state="normal")
        self.text_widget.delete("1.0", tk.END)
        self.text_widget.insert("1.0", text)
        self.text_widget.configure(
            state="disabled",
            height=max(1, min(text.count("\n") + 1, 18)),
        )
        self.root.update_idletasks()

        if x is not None and y is not None:
            offset_x, offset_y = 16, 16
            width = self.root.winfo_reqwidth()
            height = self.root.winfo_reqheight()
            screen_width = self.root.winfo_screenwidth()
            screen_height = self.root.winfo_screenheight()

            popup_x = x + offset_x
            popup_y = y + offset_y
            if popup_y + height > screen_height:
                popup_y = y - height - offset_y

            popup_x = max(0, min(popup_x, screen_width - width))
            popup_y = max(0, min(popup_y, screen_height - height))
            self.root.geometry(f"+{popup_x}+{popup_y}")

        self.root.deiconify()
        self.root.lift()
        self.root.attributes("-topmost", True)

    def hide(self):
        self.root.withdraw()

        # Only runs when a popup actually existed → safe place to "clean up" CapsLock
        ensure_caps_off()


    def run(self):
        self.root.mainloop()
