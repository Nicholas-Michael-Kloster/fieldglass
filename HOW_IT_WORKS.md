# How Fieldglass Works (Build & Remix It Yourself)

Fieldglass looks like magic when a shaky phone clip turns into a flat museum print, a vector engraving, glowing Braille art, and a live CERN-style telemetry HUD—but under the hood it is **five small, approachable Python + FFmpeg techniques**. Once you know these five tricks, you can run them on *anything*: field notebooks, flowers, microscope slides, circuit boards, art sketches, or your own videos.

---

## Trick 1 — Auto-Picking the Sharpest 4K Frame (Laplacian Focus Score)

When you film by hand, 90% of frames have tiny motion blur and 10% are razor sharp. Instead of scrubbing frame-by-frame:

1. Ask `ffmpeg` to dump candidates inside a 1–2 second window (`fps=12`).
2. Convert each candidate to grayscale and run a **discrete 2D Laplacian filter** (`scipy.ndimage.laplace`), which measures how abruptly brightness changes at edges.
3. Take the **variance** (`.var()`). Blurry frames smear edges out (low variance); crisp ink strokes spike high!
4. Re-extract the single winning timestamp losslessly from the 4K source.

```python
import numpy as np
from PIL import Image
from scipy import ndimage

def sharpness_score(path: str) -> float:
    gray = np.asarray(Image.open(path).convert("L"), dtype=np.float32)
    return float(ndimage.laplace(gray).var())
```

Try it with the CLI:
```bash
fieldglass frame your_video.mp4 -o sharpest.png --start 14.5 --duration 2.0 --fps 15
```

---

## Trick 2 — Turning a Tilted Phone Photo into a Flat Museum Scan

Book photos taken under a desk lamp always have two problems: **perspective trapezoid tilt** and **uneven warm shadows**. Two classic image-processing steps fix both cleanly:

### 2a. Perspective Deskew (4-Corner Homography)
Pick the 4 normalized `(x, y)` corners of the page (Top-Left, Top-Right, Bottom-Right, Bottom-Left in `0.0..1.0`), solve an `8×8` linear system (`np.linalg.solve`), and pass the 8 coefficients to `PIL.Image.Transform.PERSPECTIVE`. The trapezoid snaps into a flat `1500×2250` botanical plate.

### 2b. Illumination Division (One-Line Shadow Eraser!)
This is one of the best tricks in all of computer vision:
1. Blur the grayscale page with a huge Gaussian kernel (`sigma=45`). Because the blur is much wider than any ink stroke, **the ink vanishes**, leaving a smooth map of the lamp's uneven lighting (`bg`).
2. **Divide** the original image by the blurred lighting map:
   ```python
   bg = ndimage.gaussian_filter(gray, sigma=45.0)
   norm = gray / np.maximum(bg, 15.0)
   ```
   Everywhere there is plain paper—whether brightly lit or in shadow—`gray / bg ≈ 1.0`! Everywhere there is ink, `gray / bg < 0.85`. Lamp shadows disappear instantaneously without losing delicate stippling.

---

## Trick 3 — Scalable Vector SVG & 2×4 Unicode Braille

Once `clean_illumination()` gives you a clean `ink` array in `[0.0, 1.0]`:

### 3a. Two-Tone Vector SVG (`matplotlib.contourf`)
You don't even need an external tracing tool like `potrace` to get crisp scalable vectors:
```python
ax.contourf(ink_smooth, levels=[0.075, 0.21, 1.2], colors=["#786f5f", "#1b1916"])
ax.set_ylim(height - 1, 0)  # keep right-side-up in SVG coordinates!
fig.savefig("specimen.svg", format="svg")
```
Contour level `0.075` captures delicate botanical shading/veins in warm gray-brown; level `0.21` traces bold core ink lines in rich charcoal. Every polygon is a true resolution-independent vector `<path>`.

### 3b. 2×4 Unicode Braille (`U+2800..U+28FF`)
Unicode reserves 256 consecutive codepoints starting at `0x2800` (`⠀`) for every possible `2 × 4` grid of 8 raised dots! Each dot corresponds to one bit:

```text
col 0   col 1
0x01    0x08    (row 0)
0x02    0x10    (row 1)
0x04    0x20    (row 2)
0x40    0x80    (row 3)
```

So turning any `2×4` pixel patch into a Braille character is literally:
```python
char = chr(0x2800 + mask)
```
Combining that with a `4×4` Bayer dithering matrix lets even subtle shading appear cleanly inside a plain terminal (`fieldglass braille photo.png --cols 64`).

---

## Trick 4 — Real-Time Kloster $A_{\tau}(p_t)$ Telemetry Overlay Video

Every video frame is just a NumPy array `(height, width, 3)`:

1. **Stream raw RGB frames out of `ffmpeg`** (`-f rawvideo -pix_fmt rgb24 -`).
2. For each frame $t$, compute grayscale luminance (`0..255`), normalize `np.bincount(lum, minlength=256)` into a discrete probability distribution $p_t(x)$, and measure:
   - **Accessible volume**: `A_tau = int(np.sum(p > tau))` — the exact count of luminance states whose probability strictly exceeds $\tau$.
   - **Momentum**: `M_tau = A_tau[t] - A_tau[t - fps]` (change per second).
   - **Entropy & purity**: Shannon $H_1$, collision entropy $H_2$, quartic purity $M_4^{1/4}$.
3. **Feed 1-second episode distributions into Causal Chiasm & Persistent Filtration Tomography** to separate *structural invariants* (tonal states that survive high $\tau$ across the whole clip, like `ink_linework`) from transient noise.
4. **Composite each 1280×720 HUD frame with Pillow (`ImageDraw`)**—coloring histogram bars gold whenever $p_t(x) > \tau$ so you can literally *see* $A_{\tau}(p_t)$ counted live—and pipe raw RGB bytes straight into a second `ffmpeg` process that muxes back the original stereo audio (`-map 0:v:0 -map 1:a:0`).

```bash
fieldglass overlay your_clip.mp4 -o my_run/ --nexus 15
```

---

## Trick 5 — Zero-Cloud USB Phone Showcase

To beam the interactive showcase straight to an Android / Pixel phone over a USB cable (no Wi-Fi router, no cloud upload):

1. Serve the showcase folder on `127.0.0.1:8776` with an HTTP **`Range` (`206 Partial Content`)** handler—this is crucial because mobile Chrome requires byte-range requests to scrub `<video>` tags smoothly.
2. Tunnel the phone's `127.0.0.1:8776` back to your computer over USB:
   ```bash
   adb reverse tcp:8776 tcp:8776
   ```
3. Pop it open on the phone screen:
   ```bash
   adb shell am start -a android.intent.action.VIEW -d http://127.0.0.1:8776/
   ```

Or in two Fieldglass commands:
```bash
fieldglass serve my_run/ --port 8776
fieldglass push  my_run/ --name my_run --port 8776
```

---

## 2-Minute Mini-Lab: Try It Right Now!

Grab any photo on your computer (`~/Downloads/anything.jpg`) and run:

```bash
# Print it in your terminal as 2x4 Braille right now
fieldglass braille ~/Downloads/anything.jpg --cols 60

# Generate a full archival print + framed vector SVG + Braille preview bundle
fieldglass plate ~/Downloads/anything.jpg -o ~/my_first_specimen --title "MY FIRST FIELDGLASS PLATE"
```

Open `~/my_first_specimen/` and inspect the `.svg` and `_braille_preview.png`—you're officially running the full Fieldglass optical pipeline!
