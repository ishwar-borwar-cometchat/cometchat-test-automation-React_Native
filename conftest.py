import pytest
from appium import webdriver
from appium.options.common.base import AppiumOptions


# --- UPDATE THESE VALUES ---
APK_PATH = "/Users/admin/Documents/Kiro/Manual Test Script/React Native/React_Native_Android.apk"
APPIUM_SERVER = "http://127.0.0.1:4723"
# ----------------------------


@pytest.fixture(scope="session")
def driver():
    options = AppiumOptions()
    options.set_capability("platformName", "Android")
    options.set_capability("appium:automationName", "UiAutomator2")
    options.set_capability("appium:app", APK_PATH)
    options.set_capability("appium:noReset", True)
    options.set_capability("appium:adbExecTimeout", 60000)
    options.set_capability("appium:uiautomator2ServerInstallTimeout", 60000)
    options.set_capability("appium:uiautomator2ServerLaunchTimeout", 60000)
    options.set_capability("appium:appWaitActivity", "*")
    options.set_capability("appium:appWaitDuration", 30000)
    options.set_capability("appium:autoGrantPermissions", True)

    driver = webdriver.Remote(APPIUM_SERVER, options=options)
    driver.implicitly_wait(1)

    yield driver

    driver.quit()
