import os
import glob
import pytest
from appium import webdriver
from appium.options.common.base import AppiumOptions


# Auto-detect APK path — looks in current dir and common locations
def _find_apk():
    candidates = glob.glob("*.apk") + glob.glob("**/*.apk", recursive=False)
    for c in candidates:
        if "React_Native" in c or "cometchat" in c.lower():
            return os.path.abspath(c)
    if candidates:
        return os.path.abspath(candidates[0])
    return os.path.abspath("React_Native_Android.apk")

APK_PATH = _find_apk()
APPIUM_SERVER = os.environ.get("APPIUM_SERVER", "http://127.0.0.1:4723")


@pytest.fixture(scope="session")
def driver():
    options = AppiumOptions()
    options.set_capability("platformName", "Android")
    options.set_capability("appium:automationName", "UiAutomator2")
    options.set_capability("appium:app", APK_PATH)
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
