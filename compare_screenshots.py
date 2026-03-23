"""
Compare baseline and recording screenshots to find new UI elements.
Analyzes pixel differences in the composer/bottom area to locate buttons.
"""
from PIL import Image
import sys

baseline = Image.open("/tmp/explore_baseline.png")
recording = Image.open("/tmp/explore_recording.png")

w, h = baseline.size
print(f"Image size: {w}x{h}")

# Focus on the bottom area where recording UI would appear
# Composer was at y≈1761-1827, toolbar at y≈1889-1988
# Check from y=1600 to y=2028 (bottom of screen)
y_start = 1600
y_end = min(h, 2028)

print(f"\nAnalyzing region y={y_start} to y={y_end}")

# Divide into horizontal strips and check for differences
strip_height = 20
for y in range(y_start, y_end, strip_height):
    diff_pixels = 0
    total_pixels = 0
    for x in range(0, w, 5):  # sample every 5 pixels
        for dy in range(min(strip_height, y_end - y)):
            p1 = baseline.getpixel((x, y + dy))
            p2 = recording.getpixel((x, y + dy))
            total_pixels += 1
            # Check if significantly different
            if abs(p1[0]-p2[0]) + abs(p1[1]-p2[1]) + abs(p1[2]-p2[2]) > 50:
                diff_pixels += 1
    pct = (diff_pixels / total_pixels * 100) if total_pixels > 0 else 0
    if pct > 5:
        print(f"  y={y}-{y+strip_height}: {pct:.1f}% different")

# Now do column analysis in the changed rows
print(f"\nColumn analysis (x regions) in y=1700-1900:")
col_width = 60
for x in range(0, w, col_width):
    diff_pixels = 0
    total_pixels = 0
    for xx in range(x, min(x + col_width, w), 3):
        for y in range(1700, min(1900, y_end), 3):
            p1 = baseline.getpixel((xx, y))
            p2 = recording.getpixel((xx, y))
            total_pixels += 1
            if abs(p1[0]-p2[0]) + abs(p1[1]-p2[1]) + abs(p1[2]-p2[2]) > 50:
                diff_pixels += 1
    pct = (diff_pixels / total_pixels * 100) if total_pixels > 0 else 0
    if pct > 5:
        print(f"  x={x}-{x+col_width}: {pct:.1f}% different")

# Detailed pixel analysis - find distinct colored regions (buttons)
print(f"\nSampling recording screenshot colors in composer area (y=1750-1840):")
for y in [1760, 1770, 1780, 1790, 1800, 1810, 1820, 1830]:
    colors = []
    for x in range(0, w, 40):
        p = recording.getpixel((x, y))
        colors.append(f"x={x}:({p[0]},{p[1]},{p[2]})")
    print(f"  y={y}: {' | '.join(colors[:15])}")

# Also check the area above composer (y=1700-1760) for timer/waveform
print(f"\nSampling recording screenshot colors above composer (y=1700-1760):")
for y in [1700, 1720, 1740]:
    colors = []
    for x in range(0, w, 80):
        p = recording.getpixel((x, y))
        colors.append(f"x={x}:({p[0]},{p[1]},{p[2]})")
    print(f"  y={y}: {' | '.join(colors[:15])}")

# Check toolbar area too (y=1880-2000)
print(f"\nSampling recording screenshot colors in toolbar area (y=1880-1990):")
for y in [1880, 1900, 1920, 1940, 1960, 1980]:
    colors = []
    for x in range(0, w, 80):
        p = recording.getpixel((x, y))
        colors.append(f"x={x}:({p[0]},{p[1]},{p[2]})")
    print(f"  y={y}: {' | '.join(colors[:15])}")
