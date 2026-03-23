"""Precise button detection in recording UI."""
from PIL import Image

img = Image.open("/tmp/explore_recording.png")
w, h = img.size

# Scan y=1900 row pixel by pixel to find distinct button regions
print("=== PIXEL-BY-PIXEL SCAN at y=1910 ===")
prev_type = None
regions = []
region_start = 0

for x in range(40, 1040):
    p = img.getpixel((x, 1910))
    r, g, b = p[0], p[1], p[2]
    
    if r > 220 and g > 220 and b > 220:
        t = "white"
    elif r > 200 and g < 100 and b < 100:
        t = "RED"
    elif r < 130 and g < 100 and b > 180:
        t = "PURPLE"
    elif r < 80 and g < 80 and b < 80:
        t = "DARK"
    elif r > 130 and g > 130 and b > 130 and r < 200:
        t = "GRAY"
    else:
        t = f"other({r},{g},{b})"
    
    if t != prev_type:
        if prev_type and prev_type != "white":
            regions.append((region_start, x, prev_type))
        region_start = x
        prev_type = t

if prev_type and prev_type != "white":
    regions.append((region_start, 1040, prev_type))

for start, end, typ in regions:
    if end - start > 5:
        print(f"  x={start}-{end} ({end-start}px): {typ} (center: {(start+end)//2})")

# Also scan the purple area above (y=1700)
print("\n=== PURPLE AREA ABOVE COMPOSER (y=1700) ===")
prev_type = None
regions = []
region_start = 0

for x in range(40, 1040):
    p = img.getpixel((x, 1700))
    r, g, b = p[0], p[1], p[2]
    
    if r > 220 and g > 220 and b > 220:
        t = "white"
    elif r < 130 and g < 100 and b > 180:
        t = "PURPLE"
    elif r > 200 and g > 200 and b > 200:
        t = "light"
    else:
        t = f"other({r},{g},{b})"
    
    if t != prev_type:
        if prev_type and prev_type not in ("white", "light"):
            regions.append((region_start, x, prev_type))
        region_start = x
        prev_type = t

if prev_type and prev_type not in ("white", "light"):
    regions.append((region_start, 1040, prev_type))

for start, end, typ in regions:
    if end - start > 5:
        print(f"  x={start}-{end} ({end-start}px): {typ} (center: {(start+end)//2})")

# Scan at y=1730 to see if there are distinct elements inside the purple area
print("\n=== INSIDE PURPLE AREA (y=1730) - looking for icons/text ===")
for x in range(700, 1040, 2):
    p = img.getpixel((x, 1730))
    r, g, b = p[0], p[1], p[2]
    is_purple = r < 130 and g < 100 and b > 180
    if not is_purple:
        print(f"  x={x}: ({r},{g},{b})")

# Check what's at the very bottom of the recording UI
print("\n=== BOTTOM AREA (y=1830-1870) ===")
for y in range(1830, 1870, 5):
    row_info = []
    for x in range(40, 1040, 20):
        p = img.getpixel((x, y))
        r, g, b = p[0], p[1], p[2]
        if not (r > 220 and g > 220 and b > 220):
            row_info.append(f"x={x}:({r},{g},{b})")
    if row_info:
        print(f"  y={y}: {' | '.join(row_info)}")

# Scan the gray icon area more precisely
print("\n=== GRAY ICON AREA (x=60-120, y=1890-1940) ===")
for y in range(1885, 1945, 3):
    for x in range(50, 130, 2):
        p = img.getpixel((x, y))
        r, g, b = p[0], p[1], p[2]
        if r < 200 and not (r > 220 and g > 220 and b > 220):
            print(f"  x={x}, y={y}: ({r},{g},{b})")
            break

# Scan the dark text area (timer?) more precisely
print("\n=== DARK TEXT AREA (x=760-840, y=1900-1930) ===")
for y in range(1895, 1935, 3):
    dark_pixels = []
    for x in range(700, 900, 2):
        p = img.getpixel((x, y))
        r, g, b = p[0], p[1], p[2]
        if r < 80 and g < 80 and b < 80:
            dark_pixels.append(x)
    if dark_pixels:
        print(f"  y={y}: dark at x={min(dark_pixels)}-{max(dark_pixels)}")
