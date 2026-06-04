#!/bin/bash
set -e
mkdir -p fonts
DEJAVU_PATHS=("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf" "/usr/share/fonts/dejavu/DejaVuSans.ttf")
DROID_PATHS=("/usr/share/fonts/truetype/droid/DroidSansFallbackFull.ttf" "/usr/share/fonts/droid/DroidSansFallbackFull.ttf")
for p in "${DEJAVU_PATHS[@]}"; do [ -f "$p" ] && cp "$p" fonts/DejaVuSans.ttf && break; done
for p in "${DROID_PATHS[@]}"; do [ -f "$p" ] && cp "$p" fonts/DroidSansFallbackFull.ttf && break; done
if [ ! -f fonts/DejaVuSans.ttf ] || [ ! -f fonts/DroidSansFallbackFull.ttf ]; then
  apt-get update -q && apt-get install -y -q fonts-dejavu-core fonts-droid-fallback
  for p in "${DEJAVU_PATHS[@]}"; do [ -f "$p" ] && cp "$p" fonts/DejaVuSans.ttf && break; done
  for p in "${DROID_PATHS[@]}"; do [ -f "$p" ] && cp "$p" fonts/DroidSansFallbackFull.ttf && break; done
fi
