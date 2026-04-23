# Abhi Good Morning

A Kivy-based morning companion app that shows celebrity birthdays, historical events, and inspiring quotes — all paired with fresh morning-themed photography from Pexels. Runs on desktop (Windows/macOS/Linux) and builds to Android via Buildozer.

## How It Works

On launch the app:

1. Wipes the `dataset/` folder to start fresh
2. Fetches **celebrity birthdays** for today from Wikipedia's births feed, enriched with occupation data from the API Ninjas Celebrity API
3. Checks today's date against a built-in holidays database
4. Fetches up to 5 **historical events** from Wikipedia's "On this day" API
5. For each event fetches 3 quotes from ZenQuotes
6. Displays the first event — a 5-word summarised title burned onto a morning-themed Pexels photo, with a quote overlaid at the bottom

Pressing **Refresh**:
- Picks a random event each time
- Downloads a fresh morning-themed image from Pexels on every click
- Composites the title and quote directly onto the image using Pillow
- Shows a loading animation (spinning coffee GIF) while the image downloads
- Disables itself and shows **"Loading image..."** until the download finishes, then re-enables

All network work runs in background threads. When the app closes `dataset/` is wiped.

## UI Details

| Element | Behaviour |
|---------|-----------|
| Image | Full-screen composite photo with title and quote burned in via Pillow |
| Title | Summarised to 5 key words, prefixed "On this day:", rendered in yellow bold text on the image |
| Quote | White text overlaid on a semi-transparent dark banner at the bottom of the image |
| Loading animation | `loading.gif` displayed at 8× its natural size, centred on screen while image downloads |
| Refresh button | Full-width blue bar at the bottom; disabled while loading |
| Share button | Icon button (`share_icon.png`) at the bottom-right; opens Android system share sheet with the composited image and title + quote as caption; falls back to text-only if no image is ready |

## Composite Image

Text is rendered directly onto the downloaded photo using **Pillow** (`PIL`):

- **Title**: bold, yellow (`#FFE632`), with a 1px black drop shadow, sized at `h ÷ 27` px (minimum 16 px)
- **Quote**: white, with a 1px black drop shadow, sized at `h ÷ 39` px (minimum 12 px)
- A semi-transparent black banner (`rgba(0,0,0,160)`) is drawn behind the text block
- Text is word-wrapped to fit within the image width minus padding
- Font loaded from Kivy's bundled `DroidSans.ttf` / `DroidSans-Bold.ttf` (guaranteed present on Android)

## Share Feature

Tapping the share button on Android:

1. Reads the already-composited image from `dataset/event_N_composite.jpg`
2. Inserts it into the Android **MediaStore** via `MediaStore.Images.Media.insertImage()` — returns a `content://` URI that any app can read without FileProvider
3. Fires an `ACTION_SEND` intent with `image/jpeg` MIME type, the image URI, and the title + quote as text
4. Opens the system share sheet (includes Quick Share, WhatsApp, Gmail, etc.)

No `FileProvider`, no XML resource configuration needed.

## Event Sources

**Celebrity birthdays** (shown first) — fetched from:
```
https://en.wikipedia.org/api/rest_v1/feed/onthisday/births/<MM>/<DD>
```
Sorted by most recent birth year. Each entry is enriched by name lookup via:
```
https://api.api-ninjas.com/v1/celebrity?name=<name>
```
Requires an [API Ninjas](https://api-ninjas.com) key set in `API_NINJAS_KEY`.

**Built-in holidays** (checked after birthdays):

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

## Image Source

Every image is fetched from the **Pexels API** using a rotating pool of morning-themed search queries:

> sunrise · morning coffee · good morning · sunrise sky · morning light · morning mist · dawn landscape · morning breakfast · golden hour morning · peaceful morning · morning routine · coffee cup morning

```
https://api.pexels.com/v1/search?query=<query>&per_page=15&orientation=landscape
```

A random query is chosen per request; a random photo is picked from the results. Images are saved to `user_data_dir/dataset/event_<N>.jpg` and the cache file is deleted before each Refresh to force a fresh download.

Requires a [Pexels API](https://www.pexels.com/api/) key set in `PEXELS_API_KEY`.

## Quote Source

Quotes are fetched once per session from ZenQuotes:
```
https://zenquotes.io/api/quotes
```
The full response (50+ quotes) is cached in memory. Each click samples a quote that differs from the one currently displayed. If the request fails, built-in fallback quotes are used. No API key required.

## API Keys

Set these constants near the top of `main.py`:

| Constant | Service | Where to get one |
|----------|---------|-----------------|
| `API_NINJAS_KEY` | API Ninjas (celebrity data) | https://api-ninjas.com |
| `PEXELS_API_KEY` | Pexels (morning photos) | https://www.pexels.com/api/ |

## Running on Desktop

```bash
pip install kivy certifi pillow
python main.py
```

## Building the Android APK

Buildozer (the build tool) only runs on Linux. On Windows you have two options.

---

### Option A — VirtualBox / OsBoxes VM

1. Download an Ubuntu OsBoxes image and open it in VirtualBox.
2. Set up a **VirtualBox Shared Folder** pointing to `C:\Users\slim7\Documents\GitHub` (name it `GitHub`, check **Auto-mount**).
3. In the VM, add your user to the `vboxsf` group so you can access it, then reboot:

```bash
sudo adduser $USER vboxsf
sudo reboot
```

4. Use the provided `build.sh` script for all builds (see [Automated Build Script](#automated-build-script) below).

> **Important:** Buildozer must run from the VM's native filesystem — **not** from the shared folder. The vboxsf filesystem does not support symlinks, which causes the SDL2 build step to fail.

5. Install all build dependencies:

```bash
sudo apt update && sudo apt install -y \
    git zip unzip openjdk-17-jdk python3-pip rsync \
    autoconf libtool pkg-config libssl-dev libffi-dev \
    build-essential cmake ninja-build zlib1g-dev
```

6. Install Buildozer — **Cython must be pinned below 3.0** (Cython 3 breaks pyjnius):

```bash
sudo apt install -y python-is-python3
pip3 install --user "cython<3.0" buildozer
echo 'export PATH=$HOME/.local/bin:$PATH' >> ~/.bashrc
source ~/.bashrc
```

7. Build using the script:

```bash
chmod +x /media/sf_GitHub/android-morning/build.sh
/media/sf_GitHub/android-morning/build.sh android-morning
```

The first build downloads the Android SDK and NDK (~1 GB) and takes 20–40 minutes. Subsequent builds are incremental and take 1–3 minutes.

8. The APK is automatically copied back to `C:\Users\slim7\Documents\GitHub\android-morning\` on the Windows side.

---

### Option B — WSL 2

```powershell
# In Windows PowerShell (run once)
wsl --install
```

```bash
# In the Ubuntu WSL terminal
sudo apt update && sudo apt install -y \
    git zip unzip openjdk-17-jdk python3-pip rsync \
    autoconf libtool pkg-config libssl-dev libffi-dev \
    build-essential cmake ninja-build zlib1g-dev

pip3 install --user "cython<3.0" buildozer
echo 'export PATH=$HOME/.local/bin:$PATH' >> ~/.bashrc
source ~/.bashrc

chmod +x /mnt/c/Users/slim7/Documents/GitHub/android-morning/build.sh
/mnt/c/Users/slim7/Documents/GitHub/android-morning/build.sh android-morning
```

---

## Automated Build Script

`build.sh` handles syncing, building, and copying the APK back in one command.

```bash
# Normal incremental build (fast — preserves .buildozer cache)
./build.sh android-morning

# Force a full clean rebuild
./build.sh android-morning --clean
```

**Why it's fast:** Instead of deleting and re-copying the whole project directory on every run, it uses `rsync` to sync only changed source files while preserving the `.buildozer/` cache directory. This means compiled NDK objects, Kivy, and Pillow are never recompiled unless you pass `--clean`.

| Phase | First build | Subsequent builds |
|---|---|---|
| NDK/SDK download | ~10 min | 0 (cached) |
| Compile Kivy/Pillow | ~20-30 min | 0 (cached) |
| Package your Python code | ~1-2 min | ~1-2 min |

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
| `Command 'python' not found` | `sudo apt install -y python-is-python3` |
| Can't access VM IP from Windows browser | Set up VirtualBox port forwarding (Host `127.0.0.1:8000` → Guest `10.0.2.15:8000`) |
| `Permission denied` on `/media/sf_*` | `sudo adduser $USER vboxsf` then reboot the VM |
| `Cannot create symlink` / SDL2 tar errors | Build from `~/android-morning`, not from the shared folder (vboxsf has no symlink support) |

### Buildozer config summary

| Setting | Value |
|---------|-------|
| Title | Abhi Good Morning |
| Package | `dailyquote` |
| Version | 0.1 |
| Orientation | portrait |
| Target API | 34 (Android 14) |
| Min API | 26 (Android 8.0) |
| Permissions | `INTERNET`, `WRITE_EXTERNAL_STORAGE` (API ≤ 28 only) |
| Requirements | `python3, kivy, pillow, certifi` |
| Gradle dep | `androidx.core:core:1.12.0` |
| Icon | `icon.png` (512×512 sunrise, project root) |
| Manifest | `AndroidManifest.xml` (custom; package visibility for share sheet) |
| SDK update | Skipped (`android.skip_update = True`) |
| SDK licence | Auto-accepted (`android.accept_sdk_license = True`) |

## App Icon

The icon (`icon.png`) is a 512×512 early morning sunrise scene — a golden sun rising between dark hills against a deep blue-to-orange sky, with rounded corners matching Android's icon shape. It is generated by running:

```powershell
python icon_gen.py
```

Or it is already present in the project root. Buildozer picks it up automatically via `icon.filename` and `icon.adaptive_foreground.filename` in `buildozer.spec`.

## Troubleshooting

**Image stays blank** — The Pexels request failed or returned a non-image response. Check your `PEXELS_API_KEY` and internet connection.

**No celebrity birthdays showing** — Check that `API_NINJAS_KEY` is set correctly. The app will still show historical events and holidays without it.

**Quotes not showing** — ZenQuotes request failed; built-in fallback quotes will display instead.

**Button stays grey** — A download thread is still running. It will re-enable automatically when done or after 3 retries (~15 s maximum).

**"App was built for an older version of Android"** — Rebuild the APK from a clean state (`buildozer android clean && buildozer android debug`).

**SSL / network errors on Android 14+** — The app uses `certifi` to provide its own CA bundle. Ensure `certifi` is in `requirements` in `buildozer.spec` and rebuild.

**Writable storage crash on Android 14+** — The app uses `self.user_data_dir` (Kivy's private storage path) for image caching. Do not point file writes at `__file__`'s directory — that path is inside the read-only APK zip on newer Android.

**Share button does nothing** — The share button is Android-only; it has no effect on desktop. On Android, if a toast error message appears, check `adb logcat` for `[Share error]` lines. Ensure the APK was built after the latest `AndroidManifest.xml` changes (the `<queries>` block for WhatsApp package visibility is required on Android 11+).


A Kivy-based morning companion app that shows celebrity birthdays, historical events, and inspiring quotes — all paired with fresh morning-themed photography from Pexels. Runs on desktop (Windows/macOS/Linux) and builds to Android via Buildozer.

## How It Works

On launch the app:

1. Wipes the `dataset/` folder to start fresh
2. Fetches **celebrity birthdays** for today from Wikipedia's births feed, enriched with occupation and net worth data from the API Ninjas Celebrity API
3. Checks today's date against a built-in holidays database
4. Fetches up to 5 **historical events** from Wikipedia's "On this day" API
5. For each event fetches 3 quotes from ZenQuotes
6. Displays the first event — a 5-word summarised title, a morning-themed Pexels photo, and a quote

Pressing **Refresh**:
- Picks a random event each time
- Downloads a fresh morning-themed image from Pexels on every click
- Shows a different quote each click (never repeats the last one)
- Disables itself and shows **"Loading imageâ€¦"** until the download finishes, then re-enables

All network work runs in background threads. When the app closes `dataset/` is wiped.

## UI Details

| Element | Behaviour |
|---------|-----------|
| Title | Summarised to 5 key words, prefixed "On this day:", wraps automatically |
| Image | Fresh morning-themed photo from Pexels on every load |
| Quote | Never repeats the previous quote; drawn from a 50+ quote ZenQuotes cache |
| Button | Disabled while image is loading; re-enabled on completion |
| Share | Bottom-right WhatsApp button sends the current title, image and quote directly to WhatsApp |

## Event Sources

**Celebrity birthdays** (shown first) — fetched from:
```
https://en.wikipedia.org/api/rest_v1/feed/onthisday/births/<MM>/<DD>
```
Sorted by most recent birth year. Each entry is enriched by name lookup via:
```
https://api.api-ninjas.com/v1/celebrity?name=<name>
```
Requires an [API Ninjas](https://api-ninjas.com) key set in `API_NINJAS_KEY`.

**Built-in holidays** (checked after birthdays):

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

## Image Source

Every image is fetched from the **Pexels API** using a rotating pool of morning-themed search queries:

> sunrise Â· morning coffee Â· good morning Â· sunrise sky Â· morning light Â· morning mist Â· dawn landscape Â· morning breakfast Â· golden hour morning Â· peaceful morning Â· morning routine Â· coffee cup morning

```
https://api.pexels.com/v1/search?query=<query>&per_page=15&orientation=landscape
```

A random query is chosen per request; a random photo is picked from the results. Images are saved to `dataset/event_<N>.jpg` and the cache file is deleted before each Refresh to force a fresh download.

Requires a [Pexels API](https://www.pexels.com/api/) key set in `PEXELS_API_KEY`.

## Quote Source

Quotes are fetched once per session from ZenQuotes:
```
https://zenquotes.io/api/quotes
```
The full response (50+ quotes) is cached in memory. Each click samples a quote that differs from the one currently displayed. If the request fails, built-in fallback quotes are used. No API key required.

## API Keys

Set these constants near the top of `main.py`:

| Constant | Service | Where to get one |
|----------|---------|-----------------|
| `API_NINJAS_KEY` | API Ninjas (celebrity data) | https://api-ninjas.com |
| `PEXELS_API_KEY` | Pexels (morning photos) | https://www.pexels.com/api/ |

## Running on Desktop

```bash
pip install kivy certifi
python main.py
```

## Building the Android APK

Buildozer (the build tool) only runs on Linux. On Windows you have two options.

---

### Option A — VirtualBox / OsBoxes VM

1. Download an Ubuntu OsBoxes image and open it in VirtualBox.
2. Set up a **VirtualBox Shared Folder** pointing to `C:\Users\slim7\Documents\GitHub` (name it `GitHub`, check **Auto-mount**).
3. In the VM, add your user to the `vboxsf` group so you can access it, then reboot:

```bash
sudo adduser $USER vboxsf
sudo reboot
```

4. After reboot, copy the project to your home directory.

> **Important:** Buildozer must run from the VM's native filesystem — **not** from the shared folder. The vboxsf filesystem does not support symlinks, which causes the SDL2 build step to fail.

```bash
cp -r /media/sf_GitHub/android-morning ~/android-morning
cd ~/android-morning
```

5. Install all build dependencies:

```bash
sudo apt update && sudo apt install -y \
    git zip unzip openjdk-17-jdk python3-pip \
    autoconf libtool pkg-config libssl-dev libffi-dev \
    build-essential cmake ninja-build zlib1g-dev
```

6. Install Buildozer — **Cython must be pinned below 3.0** (Cython 3 breaks pyjnius):

```bash
sudo apt install -y python-is-python3
pip3 install --user "cython<3.0" buildozer
echo 'export PATH=$HOME/.local/bin:$PATH' >> ~/.bashrc
source ~/.bashrc
```

7. Build:

```bash
cd ~/android-morning
buildozer android debug
```

The first build downloads the Android SDK and NDK (~1 GB) and takes 20â€“40 minutes. Subsequent builds are much faster.

8. Output APK is at:

```
~/android-morning/bin/dailyquote-0.1-debug.apk
```

9. Copy the APK back to the shared folder so it's accessible on Windows:

```bash
cp ~/android-morning/bin/*.apk /media/sf_GitHub/android-morning/bin/
```

10. Alternatively, serve the APK to Windows over HTTP:

```bash
cd ~/android-morning/bin
python3 -m http.server 8000
```

Set up VirtualBox port forwarding (Host `127.0.0.1:8000` â†’ Guest `10.0.2.15:8000`), then open `http://127.0.0.1:8000` in a Windows browser and download the `.apk`.

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
2. On the phone go to **Settings â†’ Security â†’ Install unknown apps** and allow installs from your file manager or browser
3. Open the `.apk` file on the phone and tap **Install**

### Common Build Errors

| Error | Fix |
|-------|-----|
| `cmake: command not found` | `sudo apt install -y cmake ninja-build` |
| `undeclared name not builtin: long` | `pip3 install "cython<3.0"` then `buildozer android clean && buildozer android debug` |
| `buildozer: command not found` | `echo 'export PATH=$HOME/.local/bin:$PATH' >> ~/.bashrc && source ~/.bashrc` |
| `Command 'python' not found` | `sudo apt install -y python-is-python3` |
| Can't access VM IP from Windows browser | Set up VirtualBox port forwarding (Host `127.0.0.1:8000` â†’ Guest `10.0.2.15:8000`) |
| `Permission denied` on `/media/sf_*` | `sudo adduser $USER vboxsf` then reboot the VM |
| `Cannot create symlink` / SDL2 tar errors | Build from `~/android-morning`, not from the shared folder (vboxsf has no symlink support) |

### Buildozer config summary

| Setting | Value |
|---------|-------|
| Title | Abhi Good Morning |
| Package | `dailyquote` |
| Version | 0.1 |
| Orientation | portrait |
| Target API | 34 (Android 14) |
| Min API | 26 (Android 8.0) |
| Permission | `INTERNET` |
| Requirements | `python3, kivy, pillow, certifi` |
| Icon | `icon.png` (512×512 sunrise, project root) |
| Manifest | `AndroidManifest.xml` (custom, includes FileProvider for image sharing) |

## App Icon

The icon (`icon.png`) is a 512Ã—512 early morning sunrise scene — a golden sun rising between dark hills against a deep blue-to-orange sky, with rounded corners matching Android's icon shape. It is generated by running:

```powershell
python icon_gen.py
```

Or it is already present in the project root. Buildozer picks it up automatically via `icon.filename` and `icon.adaptive_foreground.filename` in `buildozer.spec`.

## Troubleshooting

**Image stays blank** — The Pexels request failed or returned a non-image response. Check your `PEXELS_API_KEY` and internet connection.

**No celebrity birthdays showing** — Check that `API_NINJAS_KEY` is set correctly. The app will still show historical events and holidays without it.

**Quotes not showing** — ZenQuotes request failed; built-in fallback quotes will display instead.

**Button stays grey** — A download thread is still running. It will re-enable automatically when done or after 3 retries (~15 s maximum).

**"App was built for an older version of Android"** — Rebuild the APK from a clean state (`buildozer android clean && buildozer android debug`).

**SSL / network errors on Android 14+** — The app uses `certifi` to provide its own CA bundle. Ensure `certifi` is in `requirements` in `buildozer.spec` and rebuild.

**Writable storage crash on Android 14+** — The app uses `self.user_data_dir` (Kivy's private storage path) for image caching. Do not point file writes at `__file__`'s directory — that path is inside the read-only APK zip on newer Android.

