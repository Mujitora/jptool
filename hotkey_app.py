import time
import queue
import logging
import keyboard
import pyperclip
import ctypes

from dictionary_loader import Dictionary
from translator import Translator
from main import print_results
from ui_helpers import format_result_for_popup, PopupWindow, get_cursor_position, ensure_caps_off
from screen_snip_ocr import ScreenSnipOCR

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
        ensure_caps_off()
        popup.show(popup_text, x, y)

    return on_hotkey




def main():
    log_dir = os.path.join(os.getenv("LOCALAPPDATA", os.path.expanduser("~")), "JPTool")
    os.makedirs(log_dir, exist_ok=True)
    logging.basicConfig(
        filename=os.path.join(log_dir, "hotkey_app.log"),
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
        encoding="utf-8",
    )
    logging.info("Starting hotkey translator")

    dict_path = resource_path("data/jmdict.json") # was dict_path = "data/jmdict.json"
    dictionary = Dictionary(dict_path)
    translator = Translator(dictionary)

    popup = PopupWindow()
    on_hotkey = create_hotkey_handler(translator, popup)
    ui_actions = queue.SimpleQueue()
    snip_ocr = ScreenSnipOCR()

    def log_tk_exception(exception, value, tb):
        logging.error(
            "Unhandled Tk callback exception",
            exc_info=(exception, value, tb),
        )

    popup.root.report_callback_exception = log_tk_exception

    def process_ui_actions():
        popup.root.after(25, process_ui_actions)
        while not ui_actions.empty():
            action = ui_actions.get()
            try:
                action()
            except Exception:
                logging.exception("Queued UI action failed")
                print("A hotkey action failed; details were written to the JPTool log.")

    def handle_ocr_text(recognized_text):
        print(f"\nRecognized Japanese: {recognized_text or '(no text recognized)'}")
        logging.info("OCR completed; recognized %d characters", len(recognized_text))
        result = translator.translate_word(recognized_text)
        print_results(result)
        print("=======================\n")

        popup_text = format_result_for_popup(result)
        x, y = get_cursor_position()
        ui_actions.put(lambda: popup.show(popup_text, x, y))

    def handle_ocr_error(error):
        logging.error("OCR workflow failed", exc_info=(type(error), error, error.__traceback__))
        print("OCR failed; details were written to the JPTool log.")

    def report_ocr_status(status):
        logging.info("OCR status: %s", status)
        print(status)

    def start_ocr():
        logging.info("Starting screen-snipping OCR workflow")
        started = snip_ocr.start(
            on_text=handle_ocr_text,
            on_error=handle_ocr_error,
            on_status=report_ocr_status,
        )
        if not started:
            print("OCR is still working or waiting for a snip. Press Esc to cancel it.")

    def request_ocr():
        logging.info("Ctrl+Alt+O hotkey received")
        print("Ctrl+Alt+O received; preparing screen snip...")
        ui_actions.put(start_ocr)

    snip_ocr.warm_up(
        on_status=report_ocr_status,
        on_error=handle_ocr_error,
    )

    print("JP↔EN hotkey translator running.")
    print("Highlight text, press CapsLock to translate.")
    print("Press Alt+Shift+Q to quit.\n")

    popup.root.after(25, process_ui_actions)

    # Keyboard callbacks run on a listener thread; keep Tk operations on its main thread.
    keyboard.add_hotkey("caps lock", lambda: ui_actions.put(on_hotkey), suppress=False)
    keyboard.add_hotkey("ctrl+alt+o", request_ocr)
    print("Press Ctrl+Alt+O to snip Japanese text and translate it.")

    def request_quit():
        logging.warning("Alt+Shift+Q received; requesting shutdown")
        ui_actions.put(popup.root.destroy)

    def request_window_close():
        logging.info("Popup window close button clicked; hiding popup")
        popup.hide()

    popup.root.protocol("WM_DELETE_WINDOW", request_window_close)
    keyboard.add_hotkey("alt+shift+q", request_quit)
    try:
        popup.run()
    finally:
        logging.info("Tk event loop ended; process is shutting down")
        print("Translator stopped.")


if __name__ == "__main__":
    main()
