import logging
import os
import queue
import sys
import time

import keyboard
import pyperclip

from jp_tool.dictionary_loader import Dictionary, DictionaryEntry
from jp_tool.screen_snip_ocr import ScreenSnipOCR
from jp_tool.translator import Translator
from jp_tool.ui_helpers import (
    PopupWindow,
    ensure_caps_off,
    format_result_for_popup,
    get_cursor_position,
)

MAX_MEANINGS_SHOWN = 999


def resource_path(relative_path: str) -> str:
    """Get an absolute resource path for development and PyInstaller."""
    base = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base, relative_path)


def print_results(result) -> None:
    entries: list[DictionaryEntry] = result.entries

    print(f"\nDetected language: {result.language}")
    print(f"Query: {result.query!r}")

    if not entries:
        print("  (no matches)")
        return

    print(f"Showing {len(entries)} result(s):\n")

    for index, entry in enumerate(entries, start=1):
        kanji = entry.kanji if entry.kanji is not None else "(kana only)"
        pos = ", ".join(entry.pos) if entry.pos else "unknown"
        print(f"{index}) {kanji} ({entry.reading})  [{pos}]")

        if entry.meanings:
            for meaning in entry.meanings[:MAX_MEANINGS_SHOWN]:
                print(f"   - {meaning}")
            if len(entry.meanings) > MAX_MEANINGS_SHOWN:
                remaining = len(entry.meanings) - MAX_MEANINGS_SHOWN
                print(f"   ... (+{remaining} more meanings)")
        else:
            print("   - (no meanings)")


def create_hotkey_handler(translator: Translator, popup: PopupWindow):
    def on_hotkey():
        print("\n[DEBUG] Hotkey pressed, sending Ctrl+C to active window...")
        keyboard.press_and_release("ctrl+c")
        time.sleep(0.2)

        text = pyperclip.paste().strip()
        print(f"[DEBUG] Clipboard after Ctrl+C: {text!r}")
        if not text:
            print("[Hotkey] No text selected or clipboard empty.")
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


def main() -> None:
    log_dir = os.path.join(os.getenv("LOCALAPPDATA", os.path.expanduser("~")), "JPTool")
    os.makedirs(log_dir, exist_ok=True)
    logging.basicConfig(
        filename=os.path.join(log_dir, "hotkey_app.log"),
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
        encoding="utf-8",
    )
    logging.info("Starting hotkey translator")

    dictionary = Dictionary(resource_path("data/jmdict.json"))
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

    snip_ocr.warm_up(on_status=report_ocr_status, on_error=handle_ocr_error)

    print("JP↔EN hotkey translator running.")
    print("Highlight text, press CapsLock to translate.")
    print("Press Alt+Shift+Q to quit.\n")
    popup.root.after(25, process_ui_actions)

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
