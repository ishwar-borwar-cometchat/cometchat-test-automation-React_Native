"""iOS helper — connect, dump, click. Reusable between commands."""
from appium import webdriver
from appium.options.common.base import AppiumOptions
from appium.webdriver.common.appiumby import AppiumBy
import subprocess, time, sys, json, os

SESSION_FILE = "/tmp/ios_session_id.txt"
DERIVED_DATA = subprocess.run(
    "ls -d ~/Library/Developer/Xcode/DerivedData/WebDriverAgent-* 2>/dev/null | head -1",
    shell=True, capture_output=True, text=True).stdout.strip()

def connect():
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
    d = webdriver.Remote("http://127.0.0.1:4723", options=options)
    with open(SESSION_FILE, "w") as f:
        f.write(d.session_id)
    return d

def dump(d):
    els = d.find_elements(AppiumBy.XPATH, '//*[@visible="true"]')
    print(f"\n--- {len(els)} visible elements ---")
    for e in els:
        try:
            t = (e.get_attribute("type") or "")[-30:]
            l = e.get_attribute("label") or ""
            n = e.get_attribute("name") or ""
            v = e.get_attribute("value") or ""
            y = e.location.get("y", 0)
            if l or n or v:
                print(f"  y={y:4d} | {t:30} | label={repr(l[:45]):47} | name={repr(n[:35])}")
        except:
            pass

if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "dump"
    
    print("Connecting...")
    d = connect()
    time.sleep(3)
    print(f"Session: {d.session_id}")
    
    if cmd == "dump":
        dump(d)
    elif cmd.startswith("click:"):
        label = cmd.split(":", 1)[1]
        print(f"Clicking: '{label}'")
        el = d.find_elements(AppiumBy.XPATH, f'//*[@label="{label}" or contains(@label,"{label}")]')
        if el:
            el[0].click()
            time.sleep(3)
            print("Clicked. Dumping new screen:")
            dump(d)
        else:
            print(f"NOT FOUND: '{label}'")
            dump(d)
    elif cmd == "back":
        d.back()
        time.sleep(2)
        dump(d)
    
    # Don't quit — keep session alive
    print(f"\nSession alive: {d.session_id}")
