# CometChat React Native Android — Test Automation

Appium-based automated test suite for the **CometChat React Native Android** sample app (`v5.2.10`).

## Test Coverage

| Sheet | Total TCs | Description |
|-------|-----------|-------------|
| [Positive](https://github.com/ishwar-borwar-cometchat/cometchat-test-automation-React_Native/raw/main/Cometchat_Features/Send_%26_Compose/SM_SLC_RMF_Test_Cases.xlsx) | 132 | Send Message, Emoji/Sticker, @Mention, Composer, Rich Media Formatting |
| [Negative](https://github.com/ishwar-borwar-cometchat/cometchat-test-automation-React_Native/raw/main/Cometchat_Features/Send_%26_Compose/SM_SLC_RMF_Test_Cases.xlsx) | 22 | Empty/whitespace messages, injection attacks, voice edge cases |
| [App Crash](https://github.com/ishwar-borwar-cometchat/cometchat-test-automation-React_Native/raw/main/Cometchat_Features/Send_%26_Compose/SM_SLC_RMF_Test_Cases.xlsx) | — | Crash log with device, build, timestamp, severity |

### Execution Summary (Positive — 132 TCs)

| Status | Count |
|--------|-------|
| PASS | 100 |
| FAIL | 14 |
| SKIP | 18 |

### Execution Summary (Negative — 22 TCs)

| Status | Count |
|--------|-------|
| PASS | 7 |
| FAIL | 0 |
| SKIP | 7 |
| Not Executed | 8 |

## Project Structure

```
├── conftest.py                          # Appium driver setup (session-scoped)
├── test_all_send_message_composer.py    # All test cases (Positive + Negative + Voice)
├── React_Native_Android.apk            # App under test
├── requirements.txt                     # Python dependencies
├── Cometchat_Features/
│   ├── Send_&_Compose/
│   │   └── SM_SLC_RMF_Test_Cases.xlsx  # Test cases + results (3 sheets)
│   ├── Call_Module/
│   ├── Conversation_List/
│   ├── Group_Actions/
│   ├── Groups_Module/
│   └── User_Module/
└── MIME Types/                          # Test files for attachment MIME type testing
```

## Prerequisites

- **Python 3.8+**
- **Appium 2.x** with UiAutomator2 driver
- **Android device** connected via USB (USB debugging enabled)
- **Android SDK** with `adb` in PATH

## Setup

```bash
# Install Python dependencies
pip install -r requirements.txt

# Install Appium + driver
npm install -g appium
appium driver install uiautomator2

# Verify device connection
adb devices
```

## Running Tests

```bash
# Start Appium server (separate terminal)
appium

# Run all tests
python3 -m pytest test_all_send_message_composer.py -v -s

# Run only Positive tests (132 TCs)
python3 -m pytest test_all_send_message_composer.py -v -s -k "test_positive"

# Run only Negative tests (22 TCs)
python3 -m pytest test_all_send_message_composer.py -v -s -k "test_negative"

# Run only Voice Recording tests (5 TCs)
python3 -m pytest test_all_send_message_composer.py -v -s -k "test_voice"
```

## Configuration

Update `conftest.py` with your environment:

| Setting | Value |
|---------|-------|
| APK Path | `React_Native_Android.apk` |
| App Package | `com.cometchat.sampleapp.reactnative.android` |
| Appium Server | `http://127.0.0.1:4723` |
| Device | Connected Android device |
| Login User | Andrew Joseph (sample user) |
| Test Chat | Ishwar Borwar (1-on-1), test123 (group) |

## Test Sections (Positive)

| Section | IDs | Description |
|---------|-----|-------------|
| Send Message | MSG_001–MSG_031 | Input field, send, alignment, timestamps, scroll |
| Edit/Delete/Reply/Copy | MSG_032–MSG_040 | Long press actions on messages |
| Reaction/Thread/Forward/Info | MSG_041–MSG_052 | Emoji reactions, thread replies, forwarding |
| i18n & Chronological | MSG_053–MSG_064 | Chinese, Arabic, Japanese, Hindi, mixed content |
| Emoji & Sticker | MSG_065–MSG_096 | Emoji input, sticker picker, categories, sending |
| @Mention | MSG_097–MSG_110 | @all, member suggestions, filter, group vs direct |
| Composer Features | MSG_111–MSG_121 | Draft, focus, link preview, paste, accessibility |
| Rich Media Formatting | MSG_122–MSG_132 | Bold, italic, underline, strikethrough, lists, code |

## Excel Report

The test results are stored in [`SM_SLC_RMF_Test_Cases.xlsx`](https://github.com/ishwar-borwar-cometchat/cometchat-test-automation-React_Native/raw/main/Cometchat_Features/Send_%26_Compose/SM_SLC_RMF_Test_Cases.xlsx) with color-coded status:

- 🟢 **PASS** — Green (`#C6EFCE`)
- 🔴 **FAIL** — Red (`#FFC7CE`)
- 🟠 **SKIP** — Orange (`#FFEB9C`)

Each row includes: Test Case ID, Sentiment, Scenario, Precondition, Steps, Expected Result, Actual Result, Priority, Status, Input Data, Reason.

## Known Issues

- Voice recording DELETE/SEND buttons don't register via `adb shell input tap` on React Native recording UI
- Tapping mic button can crash UiAutomator2 instrumentation — tests use `adb` fallback
- Smart reply feature not available in React Native build v5.2.10
- Collaborative whiteboard messages not present in test chats
- Sticker panel has no search or recent emojis section
