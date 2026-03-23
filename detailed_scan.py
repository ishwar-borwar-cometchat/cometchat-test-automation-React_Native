"""Detailed scan of recording UI to find exact button positions."""
from PIL import Image

img = Image.open("/tmp/explore_recording.png")
w, h = img.size

# Scan the toolbar/recording controls area (y=1860-1960) with fine resolution
print("=== DETAILED SCAN: Recording Controls Area (y=1860-1960) ===")
for y in range(1860, 1960, 5):
    row = []
    for x in range(40, 1060, 10):
        p = img.getpixel((x, y))
        r, g, b = p[0], p[1], p[2]
        # Classify color
        if r > 200 and g > 200 and b > 200:
            c = "."  # white/light gray
        elif r > 200 and g < 100 and b < 100:
            c = "R"  # red
        elif r < 130 and g < 100 and b > 180:
            c = "P"  # purple
        elif r < 50 and g < 50 and b < 50:
            c = "D"  # dark/black (text/icon)
        elif r > 130 and g > 130 and b > 130:
            c = "G"  # gray
        else:
            c = "?"  # other
        row.append(c)
    line = "".join(row)
    # Only print if not all dots
    if any(c != "." for c in row):
        print(f"  y={y}: {line}")

# Now scan the purple area above composer (y=1660-1760)
print("\n=== DETAILED SCAN: Purple Area Above Composer (y=1660-1760) ===")
for y in range(1660, 1760, 5):
    row = []
    for x in range(40, 1060, 10):
        p = img.getpixel((x, y))
        r, g, b = p[0], p[1], p[2]
        if r > 200 and g > 200 and b > 200:
            c = "."
        elif r > 200 and g < 100 and b < 100:
            c = "R"
        elif r < 130 and g < 100 and b > 180:
            c = "P"
        elif r < 50 and g < 50 and b < 50:
            c = "D"
        elif r > 130 and g > 130 and b > 130:
            c = "G"
        else:
            c = "?"
        row.append(c)
    line = "".join(row)
    if any(c != "." for c in row):
        print(f"  y={y}: {line}")

# Find exact boundaries of colored regions
print("\n=== BUTTON BOUNDARIES ===")

# Find purple regions
print("\nPurple regions (buttons):")
for y in [1700, 1710, 1720, 1900, 1910, 1920, 1930]:
    purple_start = None
    purple_end = None
    for x in range(0, w, 2):
        p = img.getpixel((x, y))
        is_purple = p[0] < 130 and p[1] < 100 and p[2] > 180
        if is_purple and purple_start is None:
            purple_start = x
        if is_purple:
            purple_end = x
    if purple_start:
        print(f"  y={y}: purple from x={purple_start} to x={purple_end} (center: {(purple_start+purple_end)//2})")

# Find red regions
print("\nRed regions (buttons):")
for y in [1900, 1910, 1920, 1930]:
    red_start = None
    red_end = None
    for x in range(0, w, 2):
        p = img.getpixel((x, y))
        is_red = p[0] > 200 and p[1] < 100 and p[2] < 100
        if is_red and red_start is None:
            red_start = x
        if is_red:
            red_end = x
    if red_start:
        print(f"  y={y}: red from x={red_start} to x={red_end} (center: {(red_start+red_end)//2})")

# Find gray/dark icon regions
print("\nGray/dark regions (icons/text):")
for y in [1900, 1910, 1920]:
    dark_regions = []
    in_dark = False
    dark_start = 0
    for x in range(0, w, 2):
        p = img.getpixel((x, y))
        is_dark = (p[0] < 180 and p[1] < 180 and p[2] < 180) and not (p[0] < 130 and p[2] > 180) and not (p[0] > 200 and p[1] < 100)
        if is_dark and not in_dark:
            dark_start = x
            in_dark = True
        elif not is_dark and in_dark:
            dark_regions.append((dark_start, x))
            in_dark = False
    if in_dark:
        dark_regions.append((dark_start, w))
    if dark_regions:
        for s, e in dark_regions:
            if e - s > 10:  # filter noise
                print(f"  y={y}: dark from x={s} to x={e} (center: {(s+e)//2}, width: {e-s})")
