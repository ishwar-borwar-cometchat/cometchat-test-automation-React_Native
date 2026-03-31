import os
import glob
import subprocess
import pytest
from appium import webdriver
from appium.options.common.base import AppiumOptions


APPIUM_SERVER = os.environ.get("APPIUM_SERVER", "http://127.0.0.1:4723")


def _detect_platform():
    """Auto-detect whether an Android or iOS device is connected."""
    # Check Android first
    adb = os.path.join(os.environ.get("ANDROID_HOME", ""), "platform-tools", "adb")
    if not os.path.exists(adb):
        import shutil
        adb = shutil.which("adb") or ""
    if adb:
        try:
            out = subprocess.run([adb, "devices"], capture_output=True, text=True, timeout=5).stdout
            for line in out.strip().split("\n")[1:]:
                parts = line.strip().split("\t")
                if len(parts) == 2 and parts[1] == "device":
                    return "android"
        except Exception:
            pass
    # Check iOS
    try:
        out = subprocess.run(["xcrun", "xctrace", "list", "devices"],
                             capture_output=True, text=True, timeout=10).stdout
        for line in out.split("\n"):
            if "iPhone" in line and "Simulator" not in line and "(" in line:
                return "ios"
    except Exception:
        pass
    return "android"  # default


def _find_apk():
    candidates = glob.glob("*.apk") + glob.glob("**/*.apk", recursive=False)
    for c in candidates:
        if "React_Native" in c or "cometchat" in c.lower():
            return os.path.abspath(c)
    return os.path.abspath(candidates[0]) if candidates else ""


def _find_ipa():
    candidates = glob.glob("*.ipa") + glob.glob("**/*.ipa", recursive=False)
    for c in candidates:
        return os.path.abspath(c)
    return ""


def _get_ios_udid():
    try:
        out = subprocess.run(["xcrun", "xctrace", "list", "devices"],
                             capture_output=True, text=True, timeout=10).stdout
        for line in out.split("\n"):
            if "iPhone" in line and "Simulator" not in line:
                # Extract UDID from parentheses
                parts = line.strip().split("(")
                if len(parts) >= 3:
                    udid = parts[-1].rstrip(")")
                    return udid
    except Exception:
        pass
    return ""


@pytest.fixture(scope="session")
def driver():
    platform = os.environ.get("PLATFORM", _detect_platform())
    print(f"\nPlatform detected: {platform}")

    options = AppiumOptions()

    if platform == "ios":
        ipa_path = _find_ipa()
        udid = _get_ios_udid()
        print(f"iOS device UDID: {udid}")
        print(f"IPA: {ipa_path}")

        options.set_capability("platformName", "iOS")
        options.set_capability("appium:automationName", "XCUITest")
        options.set_capability("appium:udid", udid)
        if ipa_path:
            options.set_capability("appium:app", ipa_path)
        options.set_capability("appium:noReset", False)
        options.set_capability("appium:fullReset", False)
        options.set_capability("appium:newCommandTimeout", 600)
        options.set_capability("appium:wdaLaunchTimeout", 120000)
        options.set_capability("appium:wdaConnectionTimeout", 120000)
        options.set_capability("appium:autoAcceptAlerts", True)
    else:
        apk_path = _find_apk()
        print(f"APK: {apk_path}")

        options.set_capability("platformName", "Android")
        options.set_capability("appium:automationName", "UiAutomator2")
        options.set_capability("appium:app", apk_path)
        options.set_capability("appium:noReset", False)
        options.set_capability("appium:fullReset", False)
        options.set_capability("appium:newCommandTimeout", 600)
        options.set_capability("appium:adbExecTimeout", 60000)
        options.set_capability("appium:uiautomator2ServerInstallTimeout", 120000)
        options.set_capability("appium:uiautomator2ServerLaunchTimeout", 120000)
        options.set_capability("appium:uiautomator2ServerReadTimeout", 60000)
        options.set_capability("appium:appWaitActivity", "*")
        options.set_capability("appium:appWaitDuration", 30000)
        options.set_capability("appium:autoGrantPermissions", True)
        options.set_capability("appium:disableWindowAnimation", True)
        options.set_capability("appium:skipUnlock", True)

    driver = webdriver.Remote(APPIUM_SERVER, options=options)
    driver.implicitly_wait(1)

    yield driver

    driver.quit()
