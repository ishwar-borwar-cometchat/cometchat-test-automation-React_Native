"""Explore iOS CometChat app — handle login or already logged in."""
from appium import webdriver
from appium.options.common.base import AppiumOptions
from appium.webdriver.common.appiumby import AppiumBy
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time, subprocess

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
options.set_capability("appium:newCommandTimeout", 300)
options.set_capability("appium:wdaLaunchTimeout", 120000)
options.set_capability("appium:wdaConnectionTimeout", 120000)
options.set_capability("appium:autoAcceptAlerts", True)
options.set_capability("appium:updatedWDABundleId", "com.ishwarborwar.WebDriverAgentRunner")
options.set_capability("appium:usePrebuiltWDA", True)
options.set_capability("appium:derivedDataPath", DERIVED_DATA)

print("Connecting...")
d = webdriver.Remote("http://127.0.0.1:4723", options=options)
print(f"Session: {d.session_id}")
time.sleep(5)

def dump(label):
    print(f"\n=== {label} ===")
    els = d.find_elements(AppiumBy.XPATH, '//*[@visible="true"]')
    for e in els:
        try:
            t = (e.get_attribute("type") or "")[-25:]
            l = e.get_attribute("label") or ""
            n = e.get_attribute("name") or ""
            v = e.get_attribute("value") or ""
            y = e.location.get("y", 0)
            if l or n or v:
                print(f"  y={y:4d} | {t:25} | label='{l[:45]}' | name='{n[:30]}' | val='{v[:15]}'")
        except:
            pass

# Check current screen
dump("CURRENT SCREEN")

# Try login if on login screen
aj = d.find_elements(AppiumBy.XPATH, '//*[@label="Andrew Joseph"]')
if aj:
    print("\n--- On login screen, clicking Andrew Joseph ---")
    aj[0].click(); time.sleep(1)
    cont = d.find_elements(AppiumBy.XPATH, '//*[@label="Continue"]')
    if cont:
        cont[0].click(); time.sleep(5)
    for _ in range(5):
        btns = d.find_elements(AppiumBy.XPATH, '//*[@label="Allow" or @label="OK"]')
        if btns: btns[0].click(); time.sleep(1)
        else: break
    time.sleep(3)
    dump("AFTER LOGIN")
else:
    print("\n--- Already logged in ---")

# Find Ishwar
print("\n--- Finding Ishwar ---")
ishwar = d.find_elements(AppiumBy.XPATH, '//*[contains(@label,"Ishwar Borwar")]')
if not ishwar:
    for i in range(5):
        d.execute_script("mobile: scroll", {"direction": "down"})
        time.sleep(1)
        ishwar = d.find_elements(AppiumBy.XPATH, '//*[contains(@label,"Ishwar Borwar")]')
        if ishwar:
            print(f"Found after {i+1} scrolls"); break

if ishwar:
    ishwar[0].click(); time.sleep(3)
    print("Opened Ishwar chat")
    dump("CHAT SCREEN")

    # Test composer
    print("\n--- Composer ---")
    composer = d.find_elements(AppiumBy.XPATH, '//*[@name="rich-text-editor"]')
    print(f"rich-text-editor: {len(composer)}")
    if composer:
        composer[0].click(); time.sleep(0.5)
        composer[0].send_keys("iOS test 123")
        time.sleep(1)
        print(f"Typed. Checking send button...")
        send = d.find_elements(AppiumBy.XPATH, '//*[@name="send-button"]')
        print(f"Send button: {len(send)}")
        if send:
            send[0].click(); time.sleep(2)
            print("Sent!")
            msg = d.find_elements(AppiumBy.XPATH, '//*[contains(@label,"iOS test 123")]')
            print(f"Message visible: {len(msg) > 0}")

    # Long press
    print("\n--- Long Press ---")
    msgs = d.find_elements(AppiumBy.XPATH, '//XCUIElementTypeOther[contains(@label,"pm") or contains(@label,"am")]')
    print(f"Messages: {len(msgs)}")
    if msgs:
        d.execute_script("mobile: touchAndHold", {"element": msgs[-1], "duration": 2})
        time.sleep(2)
        dump("LONG PRESS MENU")
        d.tap([(200, 200)])
        time.sleep(0.5)
else:
    print("Ishwar NOT found")
    dump("CURRENT SCREEN AFTER SEARCH")

d.quit()
print("\nDONE")
