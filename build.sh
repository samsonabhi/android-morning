#!/bin/bash

set -euo pipefail

# ==============================
# CONFIGURATION
# ==============================
LOG_DIR="$HOME/build_logs"
LOG_FILE="$LOG_DIR/build.log"
MAX_LOG_SIZE=$((5 * 1024 * 1024))   # 5 MB
MAX_LOG_FILES=5                     # keep last 5 logs

# ==============================
# LOG SETUP
# ==============================
mkdir -p "$LOG_DIR"

rotate_logs() {
  if [ -f "$LOG_FILE" ]; then
    FILE_SIZE=$(stat -c%s "$LOG_FILE")
    if [ "$FILE_SIZE" -ge "$MAX_LOG_SIZE" ]; then
      echo "Rotating logs..."
      for ((i=MAX_LOG_FILES-1; i>=1; i--)); do
        [ -f "$LOG_FILE.$i" ] && mv "$LOG_FILE.$i" "$LOG_FILE.$((i+1))"
      done
      mv "$LOG_FILE" "$LOG_FILE.1"
    fi
  fi
}

rotate_logs
exec > >(tee -a "$LOG_FILE") 2>&1

echo "========================================"
echo "Script started at $(date)"
echo "========================================"

# ==============================
# INPUT VALIDATION
# ==============================
if [ -z "${1:-}" ]; then
  echo "Usage: $0 <directory_name> [--clean]"
  exit 1
fi

DIR_NAME="$1"
CLEAN_BUILD="${2:-}"
SOURCE_DIR="/media/sf_GitHub/$DIR_NAME"
TARGET_DIR="$HOME/$DIR_NAME"

echo "Processing directory: $DIR_NAME"

if [ ! -d "$SOURCE_DIR" ]; then
  echo "ERROR: Source directory not found: $SOURCE_DIR"
  exit 1
fi

# ==============================
# SYNC SOURCE FILES ONLY
# Preserve .buildozer/ cache between runs — this is what makes
# incremental builds fast (skips recompiling Kivy, Pillow, NDK, etc.)
# ==============================
echo "Syncing source files (preserving .buildozer cache)..."
mkdir -p "$TARGET_DIR"

rsync -a --delete \
  --exclude='.buildozer/' \
  --exclude='bin/' \
  --exclude='.git/' \
  --exclude='__pycache__/' \
  --exclude='*.pyc' \
  --exclude='dataset/' \
  "$SOURCE_DIR/" "$TARGET_DIR/"

cd "$TARGET_DIR"

# ==============================
# OPTIONAL CLEAN BUILD
# Pass --clean as second argument to force a full rebuild
# e.g.: ./build.sh android-morning --clean
# ==============================
if [ "$CLEAN_BUILD" = "--clean" ]; then
  echo "Running: buildozer android clean  (forced via --clean flag)"
  buildozer android clean
fi

# ==============================
# BUILD
# ==============================
echo "Running: buildozer android debug"
buildozer android debug

# ==============================
# COPY APK BACK TO SOURCE
# ==============================
BIN_DIR="$TARGET_DIR/bin"

if [ ! -d "$BIN_DIR" ]; then
  echo "ERROR: bin directory not found after build"
  exit 1
fi

APK_FILE=$(ls "$BIN_DIR"/*.apk 2>/dev/null | head -n 1)

if [ -z "$APK_FILE" ]; then
  echo "ERROR: No APK file found in $BIN_DIR"
  exit 1
fi

echo "APK found: $APK_FILE"
echo "Copying APK to $SOURCE_DIR"
cp "$APK_FILE" "$SOURCE_DIR/"

# NOTE: $TARGET_DIR is intentionally NOT deleted so the .buildozer cache
# survives for the next incremental build.

echo "========================================"
echo "Script completed successfully at $(date)"
echo "========================================"
