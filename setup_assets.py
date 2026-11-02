import os
import shutil
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
ASSETS_DIR = BASE_DIR / "assets"
ASSETS_DIR.mkdir(parents=True, exist_ok=True)

SOURCE_DIRS = [
    Path(r"c:\RIYAS\Sharp INtell\Test Cafe QR\Test CafeQR Oracle\landing\public"),
    Path(r"c:\RIYAS\Sharp INtell\Test Cafe QR\Test CafeQR Oracle\TestCafeQRFrontend\public")
]

ASSET_FILES = [
    "logo.png",
    "printer-3inch.png",
    "printer-2inch.png",
    "favicon.svg",
    "cafe_warm_high_end_interior_1769345033566.png",
    "product-sample.jpg"
]

copied = 0
for src_dir in SOURCE_DIRS:
    if not src_dir.exists():
        continue
    for fname in ASSET_FILES:
        target = ASSETS_DIR / fname
        source = src_dir / fname
        if source.exists() and not target.exists():
            shutil.copy2(source, target)
            print(f"Copied: {fname}")
            copied += 1

print(f"Asset setup complete. Total assets in Studio: {len(list(ASSETS_DIR.glob('*')))}")
