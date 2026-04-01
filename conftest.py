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
    """Get iOS device UDID using devicectl (newer method)."""
    try:
        # Try newer devicectl first
        out = subprocess.run(["xcrun", "devicectl", "list", "devices"],
                             capture_output=True, text=True, timeout=10).stdout
        for line in out.split("\n"):
            if "iPhone" in line and "available" in line:
                # Extract identifier from the line
                parts = line.split()
                for i, part in enumerate(parts):
                    if len(part) == 36 and '-' in part:  # UUID format
                        return part
    except Exception:
        pass
    
    # Fallback to xctrace
    try:
        out = subprocess.run(["xcrun", "xctrace", "list", "devices"],
                             capture_output=True, text=True, timeout=10).stdout
        for line in out.split("\n"):
            if "iPhone" in line and "Simulator" not in line:
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

    # Kill app if already running (Requirement #5: Fresh start on every execution)
    if platform == "ios":
        try:
            print("Checking if app is running and killing it for fresh start...")
            bundle_id = "com.cometchat.internal.reactnative.ios.565LF4C8NT"
            udid = _get_ios_udid()
            # Use devicectl to kill app without needing WDA
            try:
                subprocess.run(
                    ["xcrun", "devicectl", "device", "process", "terminate",
                     "--device", udid, bundle_id],
                    capture_output=True, text=True, timeout=10)
                print("✓ App terminated successfully. Starting fresh...")
            except Exception:
                # Fallback: try idevicedebug
                try:
                    subprocess.run(["idevicedebug", "-u", udid, "kill", bundle_id],
                                   capture_output=True, text=True, timeout=5)
                    print("✓ App terminated via idevicedebug. Starting fresh...")
                except Exception:
                    print("✓ App not running or already terminated. Starting fresh...")
        except Exception as e:
            print(f"Note: Could not check app state: {e}")

    options = AppiumOptions()

    if platform == "ios":
        # Try devicectl first for newer format
        udid_devicectl = None
        try:
            out = subprocess.run(["xcrun", "devicectl", "list", "devices"],
                                 capture_output=True, text=True, timeout=10).stdout
            for line in out.split("\n"):
                if "iPhone" in line and "available" in line:
                    parts = line.split()
                    for part in parts:
                        if len(part) == 36 and '-' in part:
                            udid_devicectl = part
                            break
        except Exception:
            pass
        
        # Get xctrace UDID (for XCUITest compatibility)
        udid = _get_ios_udid()
        
        # Use devicectl UDID if xctrace shows offline
        if not udid or "Offline" in str(udid):
            udid = udid_devicectl if udid_devicectl else udid
        
        derived_data = subprocess.run(
            "ls -d ~/Library/Developer/Xcode/DerivedData/WebDriverAgent-* 2>/dev/null | head -1",
            shell=True, capture_output=True, text=True).stdout.strip()
        print(f"iOS device UDID: {udid}")

        options.set_capability("platformName", "iOS")
        options.set_capability("appium:automationName", "XCUITest")
        options.set_capability("appium:udid", udid)
        options.set_capability("appium:bundleId", "com.cometchat.internal.reactnative.ios.565LF4C8NT")
        options.set_capability("appium:noReset", True)
        options.set_capability("appium:shouldTerminateApp", False)
        options.set_capability("appium:forceAppLaunch", False)
        options.set_capability("appium:newCommandTimeout", 600)
        options.set_capability("appium:wdaLaunchTimeout", 180000)
        options.set_capability("appium:wdaConnectionTimeout", 180000)
        options.set_capability("appium:autoAcceptAlerts", True)
        options.set_capability("appium:updatedWDABundleId", "com.ishwarborwar.WebDriverAgentRunner")
        options.set_capability("appium:usePrebuiltWDA", True)
        options.set_capability("appium:useNewWDA", False)
        options.set_capability("appium:showXcodeLog", True)
        if derived_data:
            options.set_capability("appium:derivedDataPath", derived_data)
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

    # Kill app after test completion (Requirement #4: App reset between runs)
    try:
        print("\n✓ Terminating app for clean state...")
        driver.terminate_app("com.cometchat.internal.reactnative.ios.565LF4C8NT" if platform == "ios" else None)
    except Exception as e:
        print(f"Note: Could not terminate app: {e}")
    
    driver.quit()
