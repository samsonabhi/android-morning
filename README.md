# Daily Events & Quote App (Android Morning)

An Android app that fetches images from the web for events, holidays, and birthdays based on the current date, and displays them with inspiring quotes.

## Features

- **Date-Based Events**: Automatically detects today's date and fetches relevant historical events from Wikipedia
- **Holiday & Birthday Support**: Displays special events like Christmas, New Year, Valentine's Day, Halloween, and personal birthdays
- **Dynamic Image Fetching**: Retrieves relevant images from Pexels API based on event keywords
- **Inspiring Quotes**: Shows rotating quotes related to each event
- **Navigation**: Cycle through multiple events and quotes for the day
- **Offline Fallback**: Works with cached data if internet unavailable
- **Portrait Mode**: Optimized for mobile viewing

## How It Works

1. **Event Detection**: On app launch, it queries Wikipedia's "On this day" API to fetch historical events for today's date
2. **Image Matching**: Extracts keywords from each event and fetches corresponding images
3. **Quote Generation**: Creates relevant quotes for each event
4. **Interactive Display**: Users can tap "Next Event / Quote" to cycle through all events and their associated quotes

## Running on PC

To run the app on your computer:

1. Install dependencies: `pip install kivy pillow requests`
2. Run: `python main.py`

A window will open displaying today's events with images and quotes. Click "Next Event / Quote" to navigate through the day's events.

## Dependencies

- **Python 3.7+**
- **Kivy** - UI framework
- **Pillow** - Image processing
- **Requests** - HTTP library (optional, urllib used as fallback)
- **Internet connection** - Required for:
  - Fetching historical events from Wikipedia API
  - Downloading images from Pexels
  - Fetching quotes from Quotable API (quotable.io)

## External APIs Used

1. **Wikipedia "On this day"** - `https://en.wikipedia.org/api/rest_v1/feed/onthisday/`
   - Historical events for any date
   - No authentication required

2. **Quotable API** - `https://api.quotable.io/`
   - Random inspirational quotes
   - Quote filtering by length and tags
   - No authentication required

3. **Google Images Search** - `https://www.google.com/search?tbm=isch&q=`
   - Uses Google image search results for event keywords
   - No API key required for basic usage
   - Uses a browser-style User-Agent for better access
   - Falls back to curated high-quality image URLs if Google search is blocked

4. **Fallback Image Sources**
   - Curated high-quality image URLs for when Unsplash search unavailable
   - Default celebration image as ultimate fallback

## Features in Detail

### Event Sources
1. **Wikipedia "On this day"** - Fetches historical events for the current date
2. **Built-in Holidays Database** - Pre-configured holidays (New Year, Valentine's Day, Christmas, Halloween, etc.)
3. **Fallback Events** - If APIs are unavailable, shows generic celebratory content

### Image Management
- **High-quality image fetching** from Unsplash (1200x800 resolution)
- **Smart keyword-based search** - Searches for images matching event keywords
- **Intelligent caching** - Stores downloaded images locally to save bandwidth
- **Fallback system** - Uses curated high-quality images if search fails
- **Automatic retry** - Retries failed downloads up to 3 times
- **Better user experience** - No re-downloading same images, faster load times

### Quote System
- **Real quotes from Quotable API** - Fetches authentic quotes from quotable.io
- Displays 3 different quotes per event, fetched dynamically
- Includes author attribution for each quote
- Graceful fallback to pre-configured quotes if API is unavailable
- Updates quotes automatically as user navigates through events

## Building for Android

Building Kivy apps for Android requires Linux tools. Since you're on Windows, you'll need to use Windows Subsystem for Linux (WSL).

### Prerequisites
- Windows 11 or Windows 10 (with WSL 2)
- At least 15GB free space (for Android SDK/NDK)
- 30 minutes for initial setup

### Steps to set up WSL and build:

1. **Install WSL**:
   - Open PowerShell as Administrator
   - Run: `wsl --install`
   - Restart your computer if prompted

2. **Set up the build environment in WSL**:
   - Open WSL terminal: `wsl`
   - Update packages: `sudo apt update && sudo apt upgrade -y`
   - Install dependencies:
     ```bash
     sudo apt install -y python3 python3-pip openjdk-11-jdk git
     pip3 install kivy buildozer cython
     ```

3. **Copy project to WSL**:
   - `cd ~`
   - Create project directory: `mkdir projects`
   - Copy: `cp -r /mnt/c/Users/slim7/Documents/GitHub/android-morning projects/`
   - Navigate: `cd projects/android-morning`

4. **Build the APK**:
   - Initialize buildozer: `buildozer init` (if needed)
   - Build: `buildozer android debug`
   - First build takes 20-30 minutes (downloads Android SDK/NDK)
   - APK location: `bin/dailyquote-0.1-debug.apk`

5. **Install on Android device**:
   - Enable USB Debugging on your Android phone
   - Connect phone via USB
   - Run: `adb install bin/dailyquote-0.1-debug.apk`

## Image Caching

The app uses keyword-based image caching in the `dataset/` folder, but it clears old cached files before each fresh download. This means:
- First app launch loads images from the web
- Each run forces a fresh image fetch for the current event keywords
- Cache only stores the latest fetched file for convenience
- You can delete the `dataset/` folder anytime to force a full refresh

## Network & Performance

### Network Requirements
The app works best with:
- **Good internet connection** - For first launch and API calls
- **Offline support** - Falls back to cached images if internet unavailable
- **Timeout handling** - API calls have 5-10 second timeouts to prevent app freezing

### Performance Tips
1. **First Launch**: Allow ~30 seconds for initial image/quote downloads
2. **Subsequent Launches**: Images load from cache (instant)
3. **Quotes**: Refreshed on each app launch for variety
4. **Images**: Reused if keyword matches previous event (via caching)

## Troubleshooting

### Images Not Loading
- Check your internet connection
- Try deleting `dataset/` folder and restarting the app
- Check if Unsplash API is accessible from your location

### Quotes Not Appearing
- Verify internet connection
- The Quotable API requires outbound HTTPS connections
- Fallback generic quotes will display if API unavailable

### App Freezing
- This shouldn't happen due to background threading
- All network operations run in separate threads
- If it does freeze, close and reopen the app