#!/usr/bin/env python3
"""
Prepare a portrait for ASCII conversion:
  1. cut the subject out with rembg (busy backgrounds turn into noise otherwise)
  2. boost local contrast with OpenCV CLAHE so the face keeps its detail
  3. composite onto pure white, so the background maps to blank characters
  4. crop to the subject with a little headroom

Usage: python scripts/prep_photo.py [source-photo.jpg] [source-prepped.png]
"""
import os
import sys

import cv2
import numpy as np
from PIL import Image
from rembg import remove

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "..", "source-photo.jpg")
OUT = sys.argv[2] if len(sys.argv) > 2 else os.path.join(HERE, "..", "source-prepped.png")

PAD_FRAC = 0.04  # breathing room around the subject's bounding box

rgba = remove(Image.open(SRC).convert("RGB"))  # RGBA, background alpha = 0
arr = np.array(rgba)
alpha = arr[:, :, 3].astype(np.float32) / 255.0

gray = cv2.cvtColor(arr[:, :, :3], cv2.COLOR_RGB2GRAY)
clahe = cv2.createCLAHE(clipLimit=2.4, tileGridSize=(8, 8))
gray = clahe.apply(gray).astype(np.float32)

# subject over white: background -> 255 (blank end of the ramp)
out = gray * alpha + 255.0 * (1.0 - alpha)
out = np.clip(out, 0, 255).astype(np.uint8)

ys, xs = np.where(alpha > 0.1)
h, w = out.shape
pad = int(max(h, w) * PAD_FRAC)
top = max(0, ys.min() - pad)
left = max(0, xs.min() - pad)
right = min(w, xs.max() + pad)
out = out[top:h, left:right]  # keep everything below the head: shoulders run off the bottom

Image.fromarray(out).save(OUT)
print(f"wrote {OUT} ({out.shape[1]}x{out.shape[0]})")
