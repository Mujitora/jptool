import os
import threading
import time
from collections.abc import Callable

import keyboard


def launch_snipping_overlay() -> None:
    os.startfile("ms-screenclip:")


class ScreenSnipOCR:
    def __init__(self, timeout_seconds: int = 30, model_timeout_seconds: int = 180):
        self.timeout_seconds = timeout_seconds
        self.model_timeout_seconds = model_timeout_seconds
        self._engine = None
        self._lock = threading.Lock()
        self._model_lock = threading.Lock()
        self._model_ready = threading.Event()
        self._model_error = None

    def warm_up(
        self,
        on_status: Callable[[str], None] | None = None,
        on_error: Callable[[Exception], None] | None = None,
    ) -> None:
        with self._model_lock:
            if self._model_ready.is_set():
                return

            def load_model():
                try:
                    from manga_ocr import MangaOcr

                    if on_status:
                        on_status("Loading MangaOCR model in the background...")
                    self._engine = MangaOcr()
                    if on_status:
                        on_status("MangaOCR model is ready.")
                except Exception as error:
                    self._model_error = error
                    if on_error:
                        on_error(error)
                finally:
                    self._model_ready.set()

            threading.Thread(
                target=load_model,
                name="manga-ocr-warmup",
                daemon=True,
            ).start()

    def start(
        self,
        on_text: Callable[[str], None],
        on_error: Callable[[Exception], None],
        on_status: Callable[[str], None] | None = None,
    ) -> bool:
        if not self._lock.acquire(blocking=False):
            return False

        try:
            worker = threading.Thread(
                target=self._run,
                args=(on_text, on_error, on_status),
                name="manga-ocr",
                daemon=True,
            )
            worker.start()
        except Exception:
            self._lock.release()
            raise
        return True

    def _run(self, on_text, on_error, on_status):
        try:
            recognized_text = self._recognize(on_status)
            if recognized_text:
                on_text(recognized_text)
        except Exception as error:
            on_error(error)
        finally:
            self._lock.release()
            if on_status:
                on_status("OCR ready for the next snip.")

    def _recognize(self, on_status):
        import ctypes

        from PIL import Image, ImageGrab

        sequence_before_snip = ctypes.windll.user32.GetClipboardSequenceNumber()
        if on_status:
            on_status("Opening Windows snipping overlay...")
        launch_snipping_overlay()
        if on_status:
            on_status("Select Japanese text in the snipping overlay...")

        deadline = time.monotonic() + self.timeout_seconds
        while time.monotonic() < deadline:
            if keyboard.is_pressed("esc"):
                if on_status:
                    on_status("Snip cancelled.")
                return ""

            if ctypes.windll.user32.GetClipboardSequenceNumber() != sequence_before_snip:
                clipboard_content = ImageGrab.grabclipboard()
                if isinstance(clipboard_content, Image.Image):
                    if not self._model_ready.is_set():
                        if on_status:
                            on_status("Preparing MangaOCR model...")
                        if not self._model_ready.wait(self.model_timeout_seconds):
                            raise TimeoutError("MangaOCR model did not finish loading")
                    if self._model_error:
                        raise RuntimeError("MangaOCR model failed to load") from self._model_error
                    return self._engine(clipboard_content.copy()).strip()
            time.sleep(0.25)

        if on_status:
            on_status("No snip image received before timeout. Try Ctrl+Alt+O again.")
        return ""