import time
import queue
import keyboard
import pyperclip
import ctypes

from dictionary_loader import Dictionary
from translator import Translator
from main import print_results
from ui_helpers import format_result_for_popup, PopupWindow, get_cursor_position

import sys, os #for exe export
def resource_path(relative_path: str):
    """Get absolute path to resource (works for dev & PyInstaller)."""
    if hasattr(sys, "_MEIPASS"):
        base = sys._MEIPASS  # PyInstaller temp folder
    else:
        base = os.path.abspath(".")
    return os.path.join(base, relative_path)


VK_CAPITAL = 0x14  # virtual key code for CapsLock
HOTKEY = "caps lock"   # or whatever you like
def ensure_caps_off():
    """If CapsLock is currently ON, turn it OFF."""
    state = ctypes.windll.user32.GetKeyState(VK_CAPITAL)
    if state & 1:  # low bit = toggle state
        # Toggle caps back off
        keyboard.press_and_release("caps lock")

def create_hotkey_handler(translator: Translator, popup: PopupWindow):
    def on_hotkey():
        print("\n[DEBUG] Hotkey pressed, sending Ctrl+C to active window...")
        keyboard.press_and_release("ctrl+c")
        time.sleep(0.2)

        text = pyperclip.paste()
        print(f"[DEBUG] Clipboard after Ctrl+C: {repr(text)}")

        text = text.strip()
        if not text:
            print("[Hotkey] No text selected or clipboard empty.")
            # DO NOT force caps here → let CapsLock behave normally
            return

        result = translator.translate_word(text)

        print("\n=== Hotkey triggered ===")
        print_results(result)
        print("=======================\n")

        popup_text = format_result_for_popup(result)
        x, y = get_cursor_position()
        popup.show(popup_text, x, y)
        # No ensure_caps_off here either – handled when popup closes

    return on_hotkey




def main():
    dict_path = resource_path("data/jmdict.json") # was dict_path = "data/jmdict.json"
    dictionary = Dictionary(dict_path)
    translator = Translator(dictionary)

    popup = PopupWindow()
    on_hotkey = create_hotkey_handler(translator, popup)
    ui_actions = queue.SimpleQueue()

    def process_ui_actions():
        while not ui_actions.empty():
            ui_actions.get()()
        popup.root.after(25, process_ui_actions)

    print("JP↔EN hotkey translator running.")
    print("Highlight text, press CapsLock to translate.")
    print("Press Alt+Shift+Q to quit.\n")

    popup.root.after(25, process_ui_actions)

    # Keyboard callbacks run on a listener thread; keep Tk operations on its main thread.
    keyboard.add_hotkey("caps lock", lambda: ui_actions.put(on_hotkey), suppress=False)

    keyboard.add_hotkey("alt+shift+q", lambda: ui_actions.put(popup.root.destroy))
    popup.run()


if __name__ == "__main__":
    main()
