# Daily Quote Generator

A Kivy app that shows historical events for today's date, each with a relevant image and rotating quotes. Runs on desktop (Windows/macOS/Linux) and builds to Android via Buildozer.

## How It Works

On launch the app:

1. Wipes the `dataset/` folder to start fresh
2. Checks today's date against a built-in holidays database
3. Fetches up to 5 historical events from Wikipedia's "On this day" API
4. For each event, resolves an image URL from the Wikipedia article and fetches 3 quotes from ZenQuotes
5. Displays the first event — title, image, and quote
6. Pressing **Click for fun** cycles through quotes for the current event; on the last quote it advances to the next event and loads a new image

All network work runs in background threads. The button disables itself and shows **"Loading image…"** while a download is in progress.

When the app closes `dataset/` is wiped again.

## Event Sources

Events are loaded from two places:

**Built-in holidays** (checked first):

| Date | Event |
|------|-------|
| Jan 1 | New Year's Day |
| Feb 14 | Valentine's Day |
| Mar 8 | International Women's Day |
| Mar 17 | St. Patrick's Day |
| Apr 22 | Earth Day |
| May 1 | International Labor Day |
| Jul 4 | Independence Day |
| Oct 31 | Halloween |
| Dec 25 | Christmas |

**Wikipedia "On this day"** — up to 5 events fetched from:

```
https://en.wikipedia.org/api/rest_v1/feed/onthisday/events/<MM>/<DD>
```

No API key required.

## Image Sources

For Wikipedia events, the app uses the `originalimage` from the first Wikipedia page attached to the event, falling back to `thumbnail` if no original is available. `.gif` and `.svg` files are skipped as Kivy cannot display them.

If no usable Wikipedia image is found, the app falls back to a curated Unsplash image matched by event keyword (e.g. "halloween" → pumpkin photo, "fireworks" → fireworks photo).

Each event's image is saved to `dataset/event_<N>.jpg` during the session. Returning to a previously viewed event reuses the saved file. The folder is capped to one file per event and is wiped on open and close.

## Quote Source

Quotes are fetched once per session from ZenQuotes:

```
https://zenquotes.io/api/quotes
```

The full response (50+ quotes) is cached in memory and sampled randomly for each event. If the request fails, a small set of built-in fallback quotes is used. No API key required.

## Running on Desktop

```bash
pip install kivy
python main.py
```

## Android Build

Requires Linux tooling. On Windows use WSL.

```powershell
wsl --install
```

```bash
sudo apt update
sudo apt install -y python3 python3-pip openjdk-11-jdk git
pip3 install buildozer cython
```

Copy the project and build:

```bash
cp -r /mnt/c/Users/slim7/Documents/GitHub/android-morning ~/projects/
cd ~/projects/android-morning
buildozer android debug
```

Output APK: `bin/dailyquote-0.1-debug.apk`

Install on a connected device with USB Debugging enabled:

```bash
adb install bin/dailyquote-0.1-debug.apk
```

### Buildozer config summary

| Setting | Value |
|---------|-------|
| Title | Daily Quote Generator |
| Package | `dailyquote` |
| Version | 0.1 |
| Orientation | portrait |
| Permission | `INTERNET` |
| Requirements | `python3, kivy, pillow, requests` |

## Troubleshooting

**Image stays blank** — The Wikipedia image failed validation (not a JPEG/PNG) and the curated fallback also failed. Check your internet connection.

**Quotes not showing** — ZenQuotes request failed; built-in fallback quotes will display instead.

**Button stays grey** — A download thread is still running. It will re-enable automatically when done or after 3 retries (~15 s maximum).
