# system library

Desktop and OS-control functions, backed by Python. Imported with `import "system"`.

Most functions are cross-platform; anything that's macOS-only (`setVolume`, `getVolume`) returns `False` / `-1` on other operating systems instead of crashing.

## Wallpaper

### `setWallpaper(imagePath) -> bool`
Change the desktop wallpaper to the image at `imagePath`. Relative paths are resolved against the current working directory. Returns `True` if it worked.

- **macOS** — AppleScript against System Events (multi-display: sets the picture of `desktop 1`).
- **Windows** — calls `SystemParametersInfo(SPI_SETDESKWALLPAPER)` via PowerShell.
- **Linux** — tries `gsettings org.gnome.desktop.background picture-uri` (also sets `picture-uri-dark` for dark themes), and falls back to `feh --bg-fill` if `gsettings` isn't available.

Returns `False` if the file doesn't exist or the OS isn't recognized.

## Notifications

### `notify(title, message, subtitle=None, sound=False) -> bool`
Post a native OS notification.

- **macOS** — `display notification ... with title ...` via `osascript`. `subtitle` is optional; `sound=True` adds `sound name "Glass"` so the notification makes a sound.
- **Linux** — `notify-send`. `sound=True` uses `urgency=critical`, which makes most desktops play a sound.
- **Windows** — `New-BurntToastNotification` via PowerShell (requires the BurntToast module to be installed; otherwise returns `False`).

## Dialogs (blocking)

These open a real modal window and **block until the user closes it**. Don't call them from inside a tight loop.

### `alert(message, title="") -> bool`
OK button only.

### `confirm(message, title="") -> bool`
Yes/No. Returns `True` for Yes, `False` for No or cancellation.

### `prompt(question, default="", title="") -> str`
Text input field with `default` pre-filled. Returns the entered string, or `""` if cancelled.

- **macOS** — `display dialog ... default answer ...`
- **Linux** — `zenity --entry`
- **Windows** — currently returns `""` (no native equivalent without bringing in WinForms).

## Openers

### `openUrl(url) -> bool`
Hand `url` to the OS — uses `open` on macOS, `os.startfile` on Windows, `xdg-open` on Linux. Works for `http://`, `https://`, `mailto:`, `spotify:`, and any other URL scheme the OS has a default handler for.

### `openFile(path) -> bool`
Same thing, but for a local file path. Opens it in the OS default app for its type.

### `openBrowserTab(url) -> bool`
Open `url` as a new tab in the user's **front browser**, not a new browser window.

- **macOS** — AppleScript finds the frontmost browser process (Safari / Chrome / Firefox / Brave / Edge / Arc) and tells it to `open location`. If no browser is running, it falls back to opening Safari.
- **Linux** — same as `openUrl` (Linux DEs typically route URLs to the browser by default).
- **Windows** — uses `webbrowser.open_new_tab`.

## Clipboard

### `clipboardGet() -> str`
Read the current clipboard contents. Returns `""` if the clipboard is empty or the call fails.

### `clipboardSet(text) -> bool`
Replace the clipboard contents with `text`. Returns `True` on success.

- **macOS** — `pbcopy`
- **Windows** — `Set-Clipboard`
- **Linux** — `xclip` (with `xsel` fallback)

## Speech

### `say(text, voice=None) -> bool`
Speak `text` aloud using the OS's text-to-speech engine.

- **macOS** — `say` (pass `voice` like `"Alex"` or `"Samantha"`).
- **Linux** — `espeak -v <voice>`, falls back to `spd-say` (no voice choice there).
- **Windows** — `System.Speech.Synthesis.SpeechSynthesizer` via PowerShell.

## Volume (macOS only)

### `getVolume() -> int`
Return system output volume 0..100. Returns `-1` on non-macOS platforms.

### `setVolume(level) -> bool`
Set system output volume (0..100). Clamped to that range. Returns `False` on non-macOS platforms.

## Misc

### `beep() -> bool`
Make the OS default beep. macOS uses `osascript beep`; Linux tries `paplay`, then `speaker-test`, then a terminal bell; Windows uses a terminal bell.

### `systemInfo() -> dict`
Return a dict with `os`, `version`, `release`, `arch`, `hostname`, `user`, `cwd`, `python`. Handy for logging / debugging from a script.

## Example

```
import "system"

run(systemInfo())                           # {os: "darwin", ...}
run(notify("Done", "Build finished"))       # posts a notification
run(openBrowserTab("https://example.com"))  # opens a tab in front browser
run(clipboardSet("hello!"))                 # -> True
run(clipboardGet())                         # -> "hello!"
run(say("Build complete."))                 # speaks
run(getVolume())                            # 25
run(setVolume(50))                          # -> True
run(beep())                                 # ding
```
