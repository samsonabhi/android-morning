# Daily Quote Generator

A Kivy app that shows historical events for today's date, each with a fresh random image and an inspiring quote. Runs on desktop (Windows/macOS/Linux) and builds to Android via Buildozer.

## How It Works

On launch the app:

1. Wipes the `dataset/` folder to start fresh
2. Checks today's date against a built-in holidays database
3. Fetches up to 5 historical events from Wikipedia's "On this day" API
4. For each event fetches 3 quotes from ZenQuotes
5. Displays the first event — a 5-word summarised title prefixed with "On this day:", a random image, and a quote

Pressing **Click for fun**:
- Picks a random event each time with no limit on clicks
- Downloads a brand-new random image from [picsum.photos](https://picsum.photos) on every click
- Shows a different quote each click (never repeats the last one)
- Disables itself and shows **"Loading image…"** until the download finishes, then re-enables

All network work runs in background threads. When the app closes `dataset/` is wiped.

## UI Details

| Element | Behaviour |
|---------|-----------|
| Title | Summarised to 5 key words, prefixed "On this day:", font size 22, wraps automatically |
| Image | Fresh random image on every click via `picsum.photos/1200/800` |
| Quote | Never repeats the previous quote; drawn from a 50+ quote ZenQuotes cache |
| Button | Disabled while image is loading; re-enabled on completion |

## Event Sources

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

## Image Source

Every click fetches a new image from:

```
https://picsum.photos/1200/800
```

This URL redirects to a different random photo on every request. The image is saved to `dataset/event_<N>.jpg` and the cache file is deleted before each new download to prevent Kivy serving a stale texture.

## Quote Source

Quotes are fetched once per session from ZenQuotes:

```
https://zenquotes.io/api/quotes
```

The full response (50+ quotes) is cached in memory. Each click samples a quote that differs from the one currently displayed. If the request fails, a small set of built-in fallback quotes is used. No API key required.

## Running on Desktop

```bash
pip install kivy
python main.py
```

## Building the Android APK

Buildozer (the build tool) only runs on Linux. On Windows you have two options.

---

### Option A — VirtualBox / OsBoxes VM

1. Download an Ubuntu OsBoxes image and open it in VirtualBox.
2. On **Windows**, serve the project over HTTP so the VM can download it:

```powershell
cd C:\Users\slim7\Documents\GitHub\android-morning
python -m http.server 8000
```

3. In the **VM terminal**, download the project files:

```bash
mkdir -p ~/android-morning && cd ~/android-morning
wget http://10.0.2.2:8000/main.py
wget http://10.0.2.2:8000/buildozer.spec
```

> If `10.0.2.2` doesn't work, find the actual host IP in PowerShell:
> ```powershell
> (Get-NetIPAddress -AddressFamily IPv4 | Where-Object {$_.InterfaceAlias -notmatch 'Loopback'}).IPAddress
> ```

4. Install all build dependencies:

```bash
sudo apt update && sudo apt install -y \
    git zip unzip openjdk-17-jdk python3-pip \
    autoconf libtool pkg-config libssl-dev libffi-dev \
    build-essential cmake ninja-build zlib1g-dev
```

5. Install Buildozer — **Cython must be pinned below 3.0** (Cython 3 breaks pyjnius):

```bash
pip3 install --user "cython<3.0" buildozer
echo 'export PATH=$HOME/.local/bin:$PATH' >> ~/.bashrc
source ~/.bashrc
```

6. Build:

```bash
cd ~/android-morning
buildozer android debug
```

The first build downloads the Android SDK and NDK (~1 GB) and takes 20–40 minutes. Subsequent builds are much faster.

7. Output APK is at:

```
~/android-morning/bin/dailyquote-0.1-debug.apk
```

8. Serve the APK back to Windows:

```bash
cd ~/android-morning/bin
python3 -m http.server 8000
```

Then open `http://<vm-ip>:8000` in a Windows browser and download the APK. Get the VM IP with:

```bash
hostname -I
```

---

### Option B — WSL 2

```powershell
# In Windows PowerShell (run once)
wsl --install
```

```bash
# In the Ubuntu WSL terminal
sudo apt update && sudo apt install -y \
    git zip unzip openjdk-17-jdk python3-pip \
    autoconf libtool pkg-config libssl-dev libffi-dev \
    build-essential cmake ninja-build zlib1g-dev

pip3 install --user "cython<3.0" buildozer
echo 'export PATH=$HOME/.local/bin:$PATH' >> ~/.bashrc
source ~/.bashrc

# Copy project into WSL filesystem (faster builds than /mnt/c)
cp -r /mnt/c/Users/slim7/Documents/GitHub/android-morning ~/android-morning
cd ~/android-morning
buildozer android debug
```

APK will be at `~/android-morning/bin/dailyquote-0.1-debug.apk`. Copy it back:

```bash
cp ~/android-morning/bin/*.apk /mnt/c/Users/slim7/Documents/GitHub/android-morning/bin/
```

---

### Installing on your Android phone

1. Transfer the `.apk` file to your phone (USB, Google Drive, email, etc.)
2. On the phone go to **Settings → Security → Install unknown apps** and allow installs from your file manager or browser
3. Open the `.apk` file on the phone and tap **Install**

### Common Build Errors

| Error | Fix |
|-------|-----|
| `cmake: command not found` | `sudo apt install -y cmake ninja-build` |
| `undeclared name not builtin: long` | `pip3 install "cython<3.0"` then `buildozer android clean && buildozer android debug` |
| `buildozer: command not found` | `echo 'export PATH=$HOME/.local/bin:$PATH' >> ~/.bashrc && source ~/.bashrc` |

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
