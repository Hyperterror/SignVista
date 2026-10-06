"""
Download model files that are too large for git.

Usage (from backend/):  python scripts/download_models.py
"""

import hashlib
import os
import sys
import urllib.request

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

FILES = [
    {
        # YOLO hand detector used by the (optional) translation module.
        # Source: https://github.com/cansik/yolo-hand-detection (release "pretrained")
        "url": "https://github.com/cansik/yolo-hand-detection/releases/download/pretrained/cross-hands.weights",
        "path": os.path.join(REPO_ROOT, "ISL-Unified-Project", "config", "yolo", "cross-hands.weights"),
        "sha256": "f5a96b1cf9522ff74fdd48377d57e31b89e4ffd5fb3b7a3179a31bf985adf950",
    },
]


def sha256(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def main() -> int:
    for item in FILES:
        path = item["path"]
        if os.path.exists(path) and sha256(path) == item["sha256"]:
            print(f"[ok] {os.path.relpath(path, REPO_ROOT)} already present")
            continue
        os.makedirs(os.path.dirname(path), exist_ok=True)
        print(f"[download] downloading {item['url']}")
        tmp = path + ".part"
        urllib.request.urlretrieve(item["url"], tmp)
        digest = sha256(tmp)
        if digest != item["sha256"]:
            os.remove(tmp)
            print(f"[error] checksum mismatch for {path}: {digest}", file=sys.stderr)
            return 1
        os.replace(tmp, path)
        print(f"[ok] saved {os.path.relpath(path, REPO_ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
