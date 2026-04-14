# Fun Couple Generator App with Kivy

This is a creative and fun Python app built with Kivy and Pillow. It features a button that, when tapped, generates a fun image of a couple (two smiley faces with a heart) and displays a random positive message. Perfect for spreading joy!

## Features

- Interactive button that generates new content
- Dynamically generated couple images using Pillow
- Random positive messages
- Simple and engaging UI with image display

## How It Works

The app generates images on-the-fly:
- Two colorful smiley faces
- A red heart between them
- Golden sparkles for extra fun
- Each button press creates a fresh image and message

## Running on PC

To run the app on your computer:

1. Ensure you have Python and Kivy installed (already done in the virtual environment).
2. Run: `python main.py`

A window will open with a label and a button. Tap the button to see the magic!

## Building for Android

Building Kivy apps for Android requires Linux tools. Since you're on Windows, you'll need to use Windows Subsystem for Linux (WSL).

### Steps to set up WSL and build:

1. **Install WSL**:
   - Open PowerShell or Command Prompt as Administrator.
   - Run: `wsl --install`
   - This installs Ubuntu by default. Restart your computer if prompted.

2. **Set up the environment in WSL**:
   - Open the WSL terminal (search for "Ubuntu" in Start menu).
   - Update packages: `sudo apt update && sudo apt upgrade`
   - Install Python and pip: `sudo apt install python3 python3-pip`
   - Install Java JDK (required for Android builds): `sudo apt install openjdk-11-jdk`
   - Install Kivy and Buildozer: `pip3 install kivy buildozer`

3. **Copy your project to WSL**:
   - In WSL terminal, navigate to a directory, e.g., `cd ~`
   - Copy from Windows: `cp -r /mnt/c/Users/slim7/Python/appTest .`
   - Or clone if using git.

4. **Build the APK**:
   - Navigate to the project: `cd appTest`
   - Initialize buildozer (if needed): `buildozer init`
   - Build in debug mode: `buildozer android debug`
   - This will download Android SDK, NDK, etc. (first time, takes time and ~10GB space).
   - The APK will be in `bin/` directory.

5. **Install on Android**:
   - Transfer the APK to your phone.
   - Enable "Install from unknown sources" in settings.
   - Install and run the app.

## Learning Android Development

While Python with Kivy allows you to create Android apps, the standard and most powerful way to develop Android apps is using Java or Kotlin with Android Studio. For learning Android development properly, I recommend:

- Download Android Studio from https://developer.android.com/studio
- Follow the official Android tutorials
- Learn Java or Kotlin

Kivy is great for cross-platform apps, but for deep Android integration, native development is better.

## Next Steps

To expand this app:
- Add buttons, layouts, etc.
- Learn Kivy documentation: https://kivy.org/doc/stable/
- For more complex apps, consider BeeWare or other frameworks.