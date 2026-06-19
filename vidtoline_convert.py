# Required packages: opencv-python, numpy

import sys
from pathlib import Path

import cv2
import numpy as np

INPUT_FILE = "badapple.mp4"
OUTPUT_FILE = "badapple.plot"
WIDTH = 50
HEIGHT = 37
FPS = 12.0
INVERT = True
THRESHOLD = 128


def extract_gray_frames(cap, target_fps):
    orig_fps = cap.get(cv2.CAP_PROP_FPS) or 25.0
    frame_interval = 1.0 / target_fps
    frames = []
    pos = 0
    next_t = 0.0
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        t = pos / orig_fps if orig_fps > 0 else 0.0
        pos += 1
        if t + 1e-6 < next_t:
            continue
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        frames.append(gray)
        next_t += frame_interval
    return frames


def frame_to_dark(gray, w, h, threshold, invert=False):
    resized = cv2.resize(gray, (w, h), interpolation=cv2.INTER_AREA)
    return (resized > threshold) if invert else (resized < threshold)


def encode_frame(dark):
    h, w = dark.shape
    light = (~dark).astype(np.int32)
    col_cum = np.cumsum(light, axis=0)
    row_cum = np.cumsum(light, axis=1)

    def col_light(c, lo, hi):
        lo = max(lo, 0)
        hi = min(hi, h - 1)
        if lo > hi:
            return 0
        above = int(col_cum[lo - 1, c]) if lo > 0 else 0
        return int(col_cum[hi, c]) - above

    def row_light(L, c0, c1):
        before = int(row_cum[L, c0 - 1]) if c0 > 0 else 0
        return int(row_cum[L, c1]) - before

    out = np.empty((h, w), dtype=np.int32)
    for r in range(h):
        out[r, :] = (h - r - 1)
        c = 0
        while c < w:
            if dark[r, c]:
                c += 1
                continue
            c0 = c
            while c < w and not dark[r, c]:
                c += 1
            c1 = c - 1
            riser_cols = {c0, c1}
            best_L, best_cost, best_dist = None, None, None
            for L in range(0, h):
                if L == r:
                    continue
                parked = row_light(L, c0, c1)
                lo, hi = (r + 1, L - 1) if L > r else (L + 1, r - 1)
                risers = sum(col_light(col, lo, hi) for col in riser_cols)
                cost = parked + risers
                dist = abs(L - r)
                if (best_cost is None or cost < best_cost
                        or (cost == best_cost and dist < best_dist)):
                    best_L, best_cost, best_dist = L, cost, dist
            out[r, c0:c1 + 1] = (h - best_L - 1) if best_cost == 0 else -1
    return out


def write_plot(path, frames_grids, w, h, fps):
    with path.open("w", encoding="utf-8") as f:
        f.write(f"{w} {h} {len(frames_grids)} {int(fps)}\n")
        for grid in frames_grids:
            f.write("".join(chr(int(v) + 34) for v in grid.reshape(-1)))
            f.write("~\n")


def main():
    inp = Path(INPUT_FILE)
    if not inp.exists():
        print(f"Input not found: {inp}")
        sys.exit(2)

    cap = cv2.VideoCapture(str(inp))
    if not cap.isOpened():
        print("Failed to open video")
        sys.exit(2)

    gray_frames = extract_gray_frames(cap, FPS)
    cap.release()
    if not gray_frames:
        print("No frames were extracted from the video")
        sys.exit(2)

    total = len(gray_frames)
    print(f"Encoding {total} frames at {WIDTH}x{HEIGHT}...")

    frames_grids = []
    for i, gray in enumerate(gray_frames):
        frames_grids.append(
            encode_frame(frame_to_dark(gray, WIDTH, HEIGHT, THRESHOLD, INVERT))
        )
        if (i + 1) % 200 == 0 or i + 1 == total:
            print(f"  {i + 1}/{total}", end="\r", flush=True)
    print()

    out = Path(OUTPUT_FILE)
    write_plot(out, frames_grids, WIDTH, HEIGHT, FPS)
    print(f"Wrote {total} frames to {out}")


if __name__ == "__main__":
    main()
