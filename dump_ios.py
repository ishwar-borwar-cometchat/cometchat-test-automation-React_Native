"""Dump all visible iOS elements on current screen. Run while app is open."""
from appium import webdriver
from appium.options.common.base import AppiumOptions
from appium.webdriver.common.appiumby import AppiumBy
import subprocess, sys

DERIVED_DATA = subprocess.run(
    "ls -d ~/Library/Developer/Xcode/DerivedData/WebDriverAgent-* 2>/dev/null | head -1",
    shell=True, capture_output=True, text=True).stdout.strip()

options = AppiumOptions()
options.set_capability("platformName", "iOS")
options.set_capability("appium:automationName", "XCUITest")
options.set_capability("appium:udid", "00008020-0003353E3E82002E")
options.set_capability("appium:bundleId", "com.cometchat.internal.reactnative.ios")
options.set_capability("appium:noReset", True)
options.set_capability("appium:shouldTerminateApp", False)
options.set_capability("appium:forceAppLaunch", False)
options.set_capability("appium:newCommandTimeout", 600)
options.set_capability("appium:wdaLaunchTimeout", 120000)
options.set_capability("appium:wdaConnectionTimeout", 120000)
options.set_capability("appium:autoAcceptAlerts", True)
options.set_capability("appium:updatedWDABundleId", "com.ishwarborwar.WebDriverAgentRunner")
options.set_capability("appium:usePrebuiltWDA", True)
options.set_capability("appium:derivedDataPath", DERIVED_DATA)

print("Connecting to iPhone...")
d = webdriver.Remote("http://127.0.0.1:4723", options=options)
print(f"Connected. Session: {d.session_id}\n")

print("Navigate the app on your iPhone. Type 'dump' to see elements, 'quit' to exit.\n")

while True:
    cmd = input("> ").strip().lower()
    if cmd == "quit" or cmd == "q":
        break
    elif cmd == "dump" or cmd == "d":
        els = d.find_elements(AppiumBy.XPATH, '//*[@visible="true"]')
        print(f"\n--- {len(els)} visible elements ---")
        for e in els:
            try:
                t = (e.get_attribute("type") or "")
                l = e.get_attribute("label") or ""
                n = e.get_attribute("name") or ""
                v = e.get_attribute("value") or ""
                y = e.location.get("y", 0)
                w = e.size.get("width", 0)
                h = e.size.get("height", 0)
                if l or n or v:
                    print(f"  y={y:4d} w={w:4d} h={h:3d} | {t[-30:]:30} | label='{l[:45]}' | name='{n[:35]}' | val='{v[:20]}'")
            except:
                pass
        print()
    else:
        print("Commands: dump (d), quit (q)")

d.quit()
print("Done.")
