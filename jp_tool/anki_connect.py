import json
import urllib.error
import urllib.request


class AnkiConnectError(RuntimeError):
    pass


class AnkiConnect:
    def __init__(self, url: str = "http://127.0.0.1:8765", timeout: float = 1.0):
        self.url = url
        self.timeout = timeout

    def invoke(self, action: str, **params):
        request_data = json.dumps(
            {"action": action, "version": 6, "params": params}
        ).encode("utf-8")
        request = urllib.request.Request(
            self.url,
            data=request_data,
            headers={"Content-Type": "application/json"},
            method="POST",
        )

        try:
            with urllib.request.urlopen(request, timeout=self.timeout) as response:
                payload = json.loads(response.read().decode("utf-8"))
        except (urllib.error.URLError, TimeoutError, OSError, json.JSONDecodeError) as error:
            raise AnkiConnectError("Anki is unavailable. Start Anki with AnkiConnect installed.") from error

        if payload.get("error"):
            raise AnkiConnectError(str(payload["error"]))
        return payload.get("result")

    def is_available(self) -> bool:
        try:
            return isinstance(self.invoke("version"), int)
        except AnkiConnectError:
            return False

    def get_decks(self) -> list[str]:
        decks = self.invoke("deckNames")
        if not isinstance(decks, list):
            raise AnkiConnectError("AnkiConnect returned an invalid deck list.")
        return [deck for deck in decks if isinstance(deck, str)]

    def add_word(self, deck_name: str, word: str, definition: str) -> None:
        note = {
            "deckName": deck_name,
            "modelName": "Basic",
            "fields": {"Front": word, "Back": definition},
            "options": {"allowDuplicate": False},
            "tags": [],
        }
        can_add = self.invoke("canAddNotes", notes=[note])
        if not isinstance(can_add, list) or not can_add or not can_add[0]:
            raise AnkiConnectError("That word is already in the selected deck, or the Basic note type is unavailable.")

        note_id = self.invoke("addNote", note=note)
        if note_id is None:
            raise AnkiConnectError("Anki did not add the note.")
