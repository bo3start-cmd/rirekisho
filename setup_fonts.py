"""クラウド環境でのフォントセットアップスクリプト"""
import os, shutil, subprocess, sys

FONTS_DIR = os.path.join(os.path.dirname(__file__), "fonts")
os.makedirs(FONTS_DIR, exist_ok=True)

JP_FONT  = os.path.join(FONTS_DIR, "DroidSansFallbackFull.ttf")
LAT_FONT = os.path.join(FONTS_DIR, "DejaVuSans.ttf")

# DejaVu Sans（Ubuntuに標準搭載）
DEJAVU_CANDIDATES = [
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    "/usr/share/fonts/dejavu/DejaVuSans.ttf",
]
# Droid Sans Fallback（Ubuntuに標準搭載）
DROID_CANDIDATES = [
    "/usr/share/fonts/truetype/droid/DroidSansFallbackFull.ttf",
    "/usr/share/fonts/droid/DroidSansFallbackFull.ttf",
]

def copy_first_existing(candidates, dest):
    for path in candidates:
        if os.path.exists(path):
            shutil.copy(path, dest)
            print(f"Copied: {path} -> {dest}")
            return True
    return False

if not os.path.exists(JP_FONT):
    if not copy_first_existing(DROID_CANDIDATES, JP_FONT):
        print("Droid font not found. Installing...")
        subprocess.run(["apt-get", "install", "-y", "fonts-droid-fallback"], check=False)
        copy_first_existing(DROID_CANDIDATES, JP_FONT)

if not os.path.exists(LAT_FONT):
    if not copy_first_existing(DEJAVU_CANDIDATES, LAT_FONT):
        print("DejaVu font not found. Installing...")
        subprocess.run(["apt-get", "install", "-y", "fonts-dejavu-core"], check=False)
        copy_first_existing(DEJAVU_CANDIDATES, LAT_FONT)

print("Font setup complete.")
