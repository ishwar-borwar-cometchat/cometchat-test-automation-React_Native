"""
Explore the voice recording UI in CometChat React Native Android.
Since uiautomator dump hangs during recording (animations),
we use screenshots + adb taps to discover button positions.

Strategy:
1. Take screenshot BEFORE tapping mic (baseline)
2. Tap mic button to start recording
3. Take screenshot DURING recording
4. Compare pixel differences to find new UI elements
5. Try tapping at various positions to discover buttons
"""
import subprocess
import time
import sys

ADB = "/Users/admin/android-sdk/platform-tools/adb"
DEVICE = "HZC90Q76"
SCREEN_W, SCREEN_H = 1080, 2160
MIC_X, MIC_Y = 858, 1794  # mic button center on this device

def adb(args, timeout=10):
    r = subprocess.run([ADB, "-s", DEVICE] + args, capture_output=True, text=True, timeout=timeout)
    return r.stdout.strip()

def tap(x, y):
    adb(["shell", "input", "tap", str(x), str(y)])

def long_press(x, y, ms=2000):
    adb(["shell", "input", "swipe", str(x), str(y), str(x), str(y), str(ms)])

def screenshot(name):
    adb(["shell", "screencap", "-p", f"/sdcard/{name}.png"])
    adb(["pull", f"/sdcard/{name}.png", f"/tmp/{name}.png"])
    print(f"  Screenshot saved: /tmp/{name}.png")

def check_app():
    out = adb(["shell", "pidof", "com.cometchat.sampleapp.reactnative.android"])
    return len(out.strip()) > 0

def try_dump(name, timeout_sec=5):
    """Try uiautomator dump with timeout."""
    try:
        r = subprocess.run(
            [ADB, "-s", DEVICE, "shell", f"timeout {timeout_sec} uiautomator dump /sdcard/{name}.xml"],
            capture_output=True, text=True, timeout=timeout_sec + 2
        )
        if "dumped" in r.stdout.lower():
            xml = adb(["shell", "cat", f"/sdcard/{name}.xml"])
            return xml
    except:
        pass
    return None

print("=== VOICE RECORDING UI EXPLORATION ===")
print(f"Device: {DEVICE}, Screen: {SCREEN_W}x{SCREEN_H}")
print(f"Mic button at: ({MIC_X}, {MIC_Y})")

# Wait for chat to load
time.sleep(3)

# Step 1: Verify we're in chat
print("\n--- Step 1: Verify chat is open ---")
xml = try_dump("explore_pre", 8)
if xml:
    if "rich-text-editor" in xml:
        print("  ✓ In chat with composer visible")
    else:
        print("  ✗ Not in chat! Exiting.")
        sys.exit(1)
else:
    print("  ⚠ Could not dump UI, proceeding anyway")

# Step 2: Take baseline screenshot
print("\n--- Step 2: Baseline screenshot (before recording) ---")
screenshot("explore_baseline")

# Step 3: Tap mic button to start recording
print("\n--- Step 3: Tapping mic button ---")
tap(MIC_X, MIC_Y)
time.sleep(2)

# Step 4: Check app still running
if not check_app():
    print("  ✗ APP CRASHED after mic tap!")
    sys.exit(1)
print("  ✓ App still running after mic tap")

# Step 5: Take recording screenshot
print("\n--- Step 4: Recording screenshot ---")
screenshot("explore_recording")

# Step 6: Try uiautomator dump (likely will timeout)
print("\n--- Step 5: Trying uiautomator dump during recording ---")
xml = try_dump("explore_during", 5)
if xml:
    print(f"  ✓ Got UI dump! Length: {len(xml)}")
    # Extract content-desc
    import re
    descs = re.findall(r'content-desc="([^"]+)"', xml)
    descs = [d for d in descs if d.strip()]
    print(f"  Content descriptions: {descs[:20]}")
    # Extract clickable elements
    clickables = re.findall(r'clickable="true"[^>]*bounds="(\[[^\]]+\]\[[^\]]+\])"', xml)
    print(f"  Clickable elements: {clickables}")
else:
    print("  ⚠ uiautomator dump timed out (expected during recording)")

# Step 7: Try to find buttons by tapping at common positions
# Recording UI typically has: pause/stop button, delete/trash button, send button, timer
# These are usually in the composer area (bottom of screen)
# Let's take screenshots at different moments

print("\n--- Step 6: Taking more screenshots to capture recording UI ---")
time.sleep(1)
screenshot("explore_recording_2")
time.sleep(2)
screenshot("explore_recording_3")

# Step 8: Try pause button - likely where the mic button was or nearby
# Common recording UI layouts:
# [delete/trash] [timer/waveform] [pause/stop] [send]
# Or: [pause] [timer] [send]
# The composer area was at y≈1761-1827
# Let's check if there are buttons at similar y positions

print("\n--- Step 7: Exploring button positions ---")
print("  Composer row was at y≈1761-1827")
print("  Toolbar was at y≈1889-1988")
print("  Possible recording UI positions:")
print("    Left area (delete?): ~100, 1794")
print("    Center-left (timer?): ~400, 1794")
print("    Center-right (pause?): ~700, 1794")
print("    Right area (send?): ~950, 1794")

# Step 9: Try tapping pause (likely near center or where mic was)
# First let's try tapping at the mic position again (might be pause now)
print("\n--- Step 8: Tapping at mic position (might be pause/stop now) ---")
tap(MIC_X, MIC_Y)
time.sleep(2)

# Check if recording stopped (uiautomator should work now)
print("  Trying uiautomator dump after tap...")
xml = try_dump("explore_after_pause", 8)
if xml:
    print(f"  ✓ Got UI dump! Recording likely paused/stopped")
    import re
    descs = re.findall(r'content-desc="([^"]+)"', xml)
    descs = [d for d in descs if d.strip()]
    print(f"  Content descriptions: {descs[:20]}")
    clickables = re.findall(r'clickable="true"[^>]*bounds="(\[[^\]]+\]\[[^\]]+\])"', xml)
    print(f"  Clickable bounds: {clickables}")
    # Look for new elements
    texts = re.findall(r'text="([^"]+)"', xml)
    texts = [t for t in texts if t.strip()]
    print(f"  Text elements: {texts[:20]}")
else:
    print("  ⚠ Still can't dump - recording still active")
    # Take another screenshot
    screenshot("explore_after_tap")

# Check app
if check_app():
    print("  ✓ App still running")
else:
    print("  ✗ APP CRASHED!")

print("\n=== EXPLORATION COMPLETE ===")
print("Check screenshots in /tmp/explore_*.png to see the recording UI")
