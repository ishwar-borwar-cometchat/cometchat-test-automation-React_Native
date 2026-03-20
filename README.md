# React Native - Appium Android Automation

## Prerequisites

1. **Appium server** installed and running:
   ```bash
   npm install -g appium
   appium driver install uiautomator2
   appium
   ```

2. **Android device** connected via USB with USB debugging enabled:
   ```bash
   adb devices   # should list your device
   ```

3. **Python 3.8+** with dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Setup

1. Place your APK file in this folder (or note its absolute path)
2. Update `APK_PATH` in `conftest.py` to point to your APK

## Running Tests

```bash
# Start Appium server first (in a separate terminal)
appium

# Run tests
cd "React Native"
pytest -v
```
