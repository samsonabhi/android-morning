# Daily Quote Generator

A Kivy app that shows date-based events, a related image, and rotating quotes. The app is configured for portrait orientation in Android builds and can also run as a desktop Python application.

## What the Current Code Does

On startup, the app builds a simple vertical layout with:

- An event title label
- An image area
- A quote label
- A `Next Event / Quote` button

It then loads content in the background using the current local date.

## Event Sources

The app collects events from two places:

1. A built-in `SPECIAL_EVENTS` dictionary in `main.py`
2. Wikipedia's "On this day" events API

The built-in holidays currently include:

- New Year's Day
- Valentine's Day
- International Women's Day
- St. Patrick's Day
- Earth Day
- International Labor Day
- Independence Day
- Halloween
- Christmas

If today's date matches one of those entries, the app adds that holiday first.

It then tries to fetch up to 5 historical events from:

`https://en.wikipedia.org/api/rest_v1/feed/onthisday/events/<month>/<day>`

For each Wikipedia event, the app:

- Builds a short display name from the event text
- Extracts up to 3 keywords from the event description
- Fetches 3 quotes for that event

If event loading fails completely, the app falls back to generic built-in events.

## Quote Behavior

Quotes are fetched from the Quotable API:

`https://api.quotable.io/random?minLength=50&maxLength=150`

For each event, the app attempts to fetch 3 quotes. Each successful quote is stored in the form:

`"<quote>" - <author>`

If quote requests fail, the app uses a small built-in fallback quote list.

## Image Behavior

Images are loaded per event keyword.

The current code tries image sources in this order:

1. Google Images search HTML results for the keyword
2. A built-in dictionary of curated Unsplash image URLs
3. A default Unsplash celebration image

The image lookup is implemented by scraping the Google Images results page for a direct image URL. There is no Pexels integration in the current code.

## Caching Behavior

Images are saved under the `dataset/` folder using an MD5 hash of the keyword, for example:

`dataset/image_<hash>.jpg`

However, the current implementation deletes any existing cached file for that keyword before downloading a fresh copy. In practice, this means:

- The app writes images to `dataset/`
- The cache is not reused across loads for the same keyword
- The code prefers a fresh download each time an event image is loaded

## Navigation Behavior

The `Next Event / Quote` button cycles through quotes first, then moves to the next event.

For a given event:

- The app shows one quote initially
- Repeated button presses advance through the event's quote list
- After the last quote, the app moves to the next event and loads its image
- When it reaches the end of the event list, it wraps back to the first event

## Threading

Network work runs in background threads:

- Event loading runs in a daemon thread
- Image downloading runs in a daemon thread

UI updates are pushed back to the main Kivy thread using `@mainthread`.

## Desktop Run

The app can be run directly with Python.

### Requirements

- Python 3
- Kivy

The Buildozer config currently lists these Android/package requirements:

- `python3`
- `kivy`
- `pillow`
- `requests`

The main application code itself currently imports Kivy and Python standard-library modules such as `urllib`, `json`, `threading`, and `hashlib`.

### Run Command

```bash
python main.py
```

If Kivy is not installed yet:

```bash
pip install kivy
```

## Android Build Configuration

The existing `buildozer.spec` is configured as follows:

- Title: `Daily Quote Generator`
- Package name: `dailyquote`
- Version: `0.1`
- Orientation: `portrait`
- Permission: `INTERNET`

Buildozer-based Android builds require Linux tooling. On Windows, use WSL.

## Build on Windows with WSL

1. Install WSL from an elevated PowerShell:

   ```powershell
   wsl --install
   ```

2. Open your Linux shell and install basic tooling:

   ```bash
   sudo apt update
   sudo apt install -y python3 python3-pip openjdk-11-jdk git
   pip3 install buildozer cython
   ```

3. Copy the project into the Linux filesystem and build:

   ```bash
   mkdir -p ~/projects
   cp -r /mnt/c/Users/slim7/Documents/GitHub/android-morning ~/projects/
   cd ~/projects/android-morning
   buildozer android debug
   ```

4. The generated APK should be created under:

   ```text
   bin/dailyquote-0.1-debug.apk
   ```

## External Services Used

- Wikipedia "On this day" API for historical events
- Quotable API for quotes
- Google Images search page for image discovery
- Unsplash image URLs as curated fallbacks

None of these services require API keys in the current code.

## Failure and Fallback Behavior

- If Wikipedia loading fails, the app falls back to generic built-in events
- If quote loading fails, the app falls back to built-in quotes
- If image download fails after 3 retries, the image widget is pointed at a fallback Unsplash URL

## Notes About the Current Implementation

- The code does not include birthdays
- The code does not use Pexels
- The code does not currently provide a true offline image mode
- The code includes a `generate_quotes_for_event()` method that is not used by the current event-loading flow