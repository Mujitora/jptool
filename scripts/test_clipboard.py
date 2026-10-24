import pyperclip

print("Copy something manually (Ctrl+C), then press Enter here.")
input()

text = pyperclip.paste()
print("Clipboard contents:", repr(text))
