

# JPTool


JPTool is a lightweight Japanese-English desktop dictionary for Windows that makes looking up Japanese words quick and seamless, without interrupting what you're doing.

Simply **highlight any Japanese text and press Caps Lock** to instantly display its English definition in a convenient popup window.

For text that can't be selected, such as in video games, manga, or images, JPTool includes a built-in OCR tool. Press **Ctrl+Alt+O** to select an area of your screen, automatically recognize the Japanese text, and look up its meaning.

JPTool also features **Anki integration**, allowing you to easily create flashcards from words you encounter. Quickly add new vocabulary to your Anki decks as you read or play, making it easier to review and retain what you've learned.

Designed for Japanese learners, JPTool brings the convenience of browser-based dictionary extensions to your entire desktop, combining instant dictionary lookups, screen-based text recognition, and vocabulary flashcard creation into one convenient tool.

<img width="647" height="575" alt="jptool" src="https://github.com/user-attachments/assets/546a2137-9fd0-4160-b731-006750c241d5" />

<img width="997" height="780" alt="jptool2" src="https://github.com/user-attachments/assets/0fe02244-a77f-420f-a35a-09d68bd7f93b" />

## Download and run

1. Open the [GitHub Releases](https://github.com/Mujitora/jptool/releases) page and download `JPTool-windows-x64.zip` from the latest release.
2. Extract the ZIP to a folder. Keep the extracted files together.
3. Double-click `JPTool.exe` to start the app. Python does not need to be installed.
4. Highlight text in another application and press **Caps Lock**. Use **Alt+Shift+Q** to quit.

Windows may show a SmartScreen warning because early releases are not code-signed. Only run downloads from this repository's Releases page.

## OCR

The first OCR use may need internet access so MangaOCR can download its model files. OCR uses the Windows snipping overlay. Press **Ctrl+Alt+O**, select an image region, and wait for the recognized text to be translated.

## Anki

Anki is optional. To add a result, install and enable the AnkiConnect add-on, keep Anki running, open the popup's **Deck** control to select a deck, then use **+**. Cards use the Basic note type; the front contains the looked-up word and the back contains up to three meanings from the first result.

## Keyboard shortcuts

- **Caps Lock**: translate selected text
- **Ctrl+Alt+O**: translate a screen snip with OCR
- **Alt+Shift+Q**: quit the app
- **Esc**: hide the popup or cancel an OCR snip

## Build from source

Requires Windows and Python 3.12. Install dependencies and build with:

```powershell
python -m pip install -r requirements.txt pyinstaller
pyinstaller --noconfirm --clean hotkey_app.spec
```

The portable application folder is created at `dist/JPTool/`.
