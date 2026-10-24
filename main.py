import logging
import json
import os
import queue
import sys
import threading
import time
import tkinter as tk
from tkinter import ttk

import keyboard
import pyperclip

from jp_tool.dictionary_loader import Dictionary, DictionaryEntry
from jp_tool.anki_connect import AnkiConnect, AnkiConnectError
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


def get_anki_definition(result) -> str:
    if not result.entries:
        return ""
    return ", ".join(result.entries[0].meanings[:3])


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
        definition = get_anki_definition(result)
        popup.show(popup_text, x, y, word=result.query, definition=definition)

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
    anki = AnkiConnect()
    settings_path = os.path.join(log_dir, "settings.json")

    try:
        with open(settings_path, "r", encoding="utf-8") as settings_file:
            settings = json.load(settings_file)
    except (OSError, json.JSONDecodeError):
        settings = {}
    selected_deck = settings.get("anki_deck", "")

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
        definition = get_anki_definition(result)
        ui_actions.put(
            lambda: popup.show(
                popup_text,
                x,
                y,
                word=result.query,
                definition=definition,
            )
        )

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

    def show_anki_settings():
        dialog = tk.Toplevel(popup.root)
        dialog.title("Anki deck")
        dialog.resizable(False, False)
        dialog.transient(popup.root)

        frame = ttk.Frame(dialog, padding=12)
        frame.grid(sticky="nsew")
        ttk.Label(frame, text="Add JPTool cards to:").grid(row=0, column=0, columnspan=2, sticky="w")

        deck_var = tk.StringVar(value=selected_deck)
        deck_box = ttk.Combobox(frame, textvariable=deck_var, state="readonly", width=32)
        if selected_deck:
            deck_box["values"] = [selected_deck]
        deck_box.grid(row=1, column=0, sticky="ew", pady=(6, 8))

        status_var = tk.StringVar(value="Loading decks..." if popup._anki_available else "Start Anki with AnkiConnect enabled.")
        ttk.Label(frame, textvariable=status_var).grid(row=2, column=0, columnspan=2, sticky="w")

        def load_decks():
            status_var.set("Loading decks...")

            def fetch():
                try:
                    decks = anki.get_decks()
                    ui_actions.put(lambda: update_decks(decks, None))
                except AnkiConnectError as error:
                    ui_actions.put(lambda message=str(error): update_decks([], message))

            threading.Thread(target=fetch, name="anki-deck-list", daemon=True).start()

        def update_decks(decks, error):
            if not dialog.winfo_exists():
                return
            if error:
                status_var.set(error)
                return
            deck_box["values"] = decks
            if selected_deck in decks:
                deck_var.set(selected_deck)
            elif decks:
                deck_var.set(decks[0])
            status_var.set(f"{len(decks)} deck(s) available")

        def save_deck():
            nonlocal selected_deck
            deck_name = deck_var.get().strip()
            if not deck_name:
                status_var.set("Choose a deck first.")
                return
            selected_deck = deck_name
            with open(settings_path, "w", encoding="utf-8") as settings_file:
                json.dump({"anki_deck": selected_deck}, settings_file, ensure_ascii=False, indent=2)
            popup.set_anki_state(popup._anki_available)
            popup.set_anki_message(f"Deck: {selected_deck}")
            dialog.destroy()

        ttk.Button(frame, text="Refresh", command=load_decks).grid(row=1, column=1, padx=(6, 0))
        ttk.Button(frame, text="Save", command=save_deck).grid(row=3, column=1, sticky="e", pady=(10, 0))
        dialog.bind("<Escape>", lambda _event: dialog.destroy())
        dialog.grab_set()
        dialog.update_idletasks()
        dialog.geometry(f"+{popup.root.winfo_rootx()}+{popup.root.winfo_rooty()}")
        load_decks()

    def request_add_card(word, definition):
        if not selected_deck:
            popup.set_anki_message("Choose a deck with Deck first")
            return
        popup.set_anki_message("Adding to Anki...")

        def add_card():
            try:
                anki.add_word(selected_deck, word, definition)
                ui_actions.put(lambda: popup.set_anki_message("Added to Anki"))
            except AnkiConnectError as error:
                ui_actions.put(lambda message=str(error): popup.set_anki_message(message))

        threading.Thread(target=add_card, name="anki-add-note", daemon=True).start()

    def check_anki_connection():
        def check():
            available = anki.is_available()
            message = "Choose a deck with Deck" if available and not selected_deck else None
            ui_actions.put(
                lambda: (
                    popup.set_anki_state(available, message),
                    popup.root.after(5000, check_anki_connection),
                )
            )

        threading.Thread(target=check, name="anki-availability", daemon=True).start()

    popup.set_anki_callbacks(request_add_card, show_anki_settings)
    check_anki_connection()

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
