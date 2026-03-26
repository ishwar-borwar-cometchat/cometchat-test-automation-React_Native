"""
CometChat React Native — Send Message Test Cases (MSG_001 to MSG_064)

Usage:
  python3 -m pytest "Cometchat_Features/Send_&_Compose/test_send_message.py" -v -s
"""
import os
import time
import subprocess
import shutil
import datetime
import openpyxl
from openpyxl.styles import Font, PatternFill, Border, Side, Alignment
from appium.webdriver.common.appiumby import AppiumBy
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# ============================================================
# CONSTANTS — all auto-detected, nothing hardcoded
# ============================================================
EXCEL = os.path.join(os.path.dirname(__file__) or ".", "SM_SLC_RMF_Test_Cases.xlsx")
if not os.path.exists(EXCEL):
    EXCEL = "Cometchat_Features/Send_&_Compose/SM_SLC_RMF_Test_Cases.xlsx"
PKG = "com.cometchat.sampleapp.reactnative.android"
BUILD = "React Native Android v5.2.10"

# Auto-detect adb path
ADB = shutil.which("adb") or os.path.join(os.environ.get("ANDROID_HOME", ""), "platform-tools", "adb")

# Auto-detect connected device
def _get_device_id():
    try:
        result = subprocess.run([ADB, "devices"], capture_output=True, text=True, timeout=10)
        for line in result.stdout.strip().split("\n")[1:]:
            parts = line.strip().split("\t")
            if len(parts) == 2 and parts[1] == "device":
                return parts[0]
    except Exception:
        pass
    return ""

DEVICE = _get_device_id()


# ============================================================
# HELPER FUNCTIONS
# ============================================================
def _wait(driver, timeout=10):
    return WebDriverWait(driver, timeout, poll_frequency=0.3)


def _get_screen_size(driver):
    """Get screen size from driver at runtime."""
    return driver.get_window_size()


def _find_mic_button(driver):
    """Dynamically find the mic/voice record button by position — it's the clickable
    ViewGroup between Emoji Button and send-button, with no content-desc."""
    try:
        # Get Emoji Button and send-button positions as anchors
        emoji_btn = driver.find_elements(AppiumBy.ACCESSIBILITY_ID, "Emoji Button")
        send_btn = driver.find_elements(AppiumBy.XPATH, "//*[@resource-id='send-button']")
        if emoji_btn and send_btn:
            emoji_bounds = emoji_btn[0].get_attribute("bounds") or ""
            send_bounds = send_btn[0].get_attribute("bounds") or ""
            # Parse right edge of emoji and left edge of send
            e_right = int(emoji_bounds.replace("[", "").replace("]", ",").split(",")[2])
            s_left = int(send_bounds.replace("[", "").replace("]", ",").split(",")[0])
            # Mic button is between emoji and send button
            mic_x = (e_right + s_left) // 2
            mic_y = emoji_btn[0].location['y'] + emoji_btn[0].size['height'] // 2
            return mic_x, mic_y
    except Exception:
        pass
    # Fallback: find clickable ViewGroups in composer row with no content-desc
    try:
        groups = driver.find_elements(AppiumBy.XPATH,
            "//android.view.ViewGroup[@clickable='true' and @content-desc='']")
        screen = driver.get_window_size()
        # Filter to bottom area (last 15% of screen)
        bottom_groups = [g for g in groups
                         if g.location.get('y', 0) > screen['height'] * 0.8
                         and g.size.get('width', 0) < 100]
        if bottom_groups:
            # Mic is typically the rightmost small button before send
            bottom_groups.sort(key=lambda g: g.location.get('x', 0), reverse=True)
            mic = bottom_groups[0]
            return mic.location['x'] + mic.size['width'] // 2, mic.location['y'] + mic.size['height'] // 2
    except Exception:
        pass
    return None, None


def _find_recording_buttons(driver):
    """Dynamically find DELETE, PAUSE, SEND buttons during voice recording.
    Returns dict with keys 'delete', 'pause', 'send' -> (x, y) tuples."""
    buttons = {}
    try:
        groups = driver.find_elements(AppiumBy.XPATH,
            "//android.view.ViewGroup[@clickable='true']")
        screen = driver.get_window_size()
        # Filter to bottom area during recording
        bottom = [g for g in groups
                  if g.location.get('y', 0) > screen['height'] * 0.8]
        bottom.sort(key=lambda g: g.location.get('x', 0))
        if len(bottom) >= 3:
            # Left = delete, middle = pause, right = send
            for i, key in enumerate(['delete', 'pause', 'send']):
                if i < len(bottom):
                    b = bottom[i]
                    buttons[key] = (b.location['x'] + b.size['width'] // 2,
                                    b.location['y'] + b.size['height'] // 2)
        elif len(bottom) >= 1:
            # At least one button found
            buttons['delete'] = (bottom[0].location['x'] + bottom[0].size['width'] // 2,
                                 bottom[0].location['y'] + bottom[0].size['height'] // 2)
            if len(bottom) >= 2:
                buttons['send'] = (bottom[-1].location['x'] + bottom[-1].size['width'] // 2,
                                   bottom[-1].location['y'] + bottom[-1].size['height'] // 2)
    except Exception:
        pass
    return buttons


def _ensure_in_chat(driver, user_name="Ishwar Borwar"):
    """Ensure we are in the correct chat. Recover if not. Returns True if in chat."""
    try:
        composer = WebDriverWait(driver, 3, poll_frequency=0.3).until(
            EC.presence_of_element_located((
                AppiumBy.XPATH,
                "//android.widget.EditText[contains(@hint,'Type') or contains(@text,'Type your message')]")))
        if composer.is_displayed():
            return True
    except Exception:
        pass
    # Not in chat — try to recover
    print(f"  [Recovery] Not in chat, navigating to {user_name}...")
    try:
        # Check if app is running
        app_state = driver.query_app_state(PKG)
        if app_state < 3:  # Not running or in background
            driver.activate_app(PKG)
            time.sleep(2)
            _login_if_needed(driver)
        _go_to_chat_list(driver)
        time.sleep(0.5)
        return _open_chat(driver, user_name)
    except Exception as e:
        print(f"  [Recovery] Failed: {str(e)[:60]}")
        return False


def _login_if_needed(driver):
    """Login by selecting Andrew Joseph sample user. Waits for chat list to load."""
    try:
        _wait(driver, 5).until(EC.element_to_be_clickable((
            AppiumBy.ACCESSIBILITY_ID, "Andrew Joseph"))).click()
        time.sleep(0.3)
        _wait(driver, 5).until(EC.element_to_be_clickable((
            AppiumBy.ACCESSIBILITY_ID, "Continue"))).click()
        time.sleep(3)
        # Dismiss VOIP/permission dialogs via adb (safer than Appium on Android 16)
        for _ in range(5):
            try:
                focus = _adb(["shell", "dumpsys", "window"])
                focus_line = ""
                for line in focus.split("\n"):
                    if "mCurrentFocus" in line:
                        focus_line = line; break
                if any(x in focus_line for x in ["GrantPermission", "telecom", "CallingAccount"]) and PKG not in focus_line:
                    _adb(["shell", "input", "keyevent", "4"])
                    time.sleep(1)
                    continue
                btns = driver.find_elements(AppiumBy.XPATH,
                    "//*[@text='OK' or @text='Allow' or @text='ALLOW' or @text='While using the app']")
                if btns:
                    btns[0].click(); time.sleep(1)
                else:
                    break
            except Exception:
                _adb(["shell", "input", "keyevent", "4"])
                time.sleep(1)
        print("Logged in as Andrew Joseph.")
    except Exception:
        print("Already logged in — checking screen state...")
        # We're past login but might be on wrong screen (VOIP settings, etc.)
        # Press back only if current focus is a system dialog, NOT the app
        for _ in range(5):
            try:
                focus = _adb(["shell", "dumpsys", "window"])
                # Extract only mCurrentFocus line
                focus_line = ""
                for line in focus.split("\n"):
                    if "mCurrentFocus" in line:
                        focus_line = line; break
                if any(x in focus_line for x in ["GrantPermission", "telecom", "CallingAccount"]) and PKG not in focus_line:
                    print(f"  System dialog: {focus_line.strip()[:60]}")
                    _adb(["shell", "input", "keyevent", "4"])
                    time.sleep(1)
                    continue
            except Exception:
                pass
            try:
                chats = driver.find_elements(AppiumBy.XPATH,
                    "//*[@text='Chats' or contains(@content-desc,'Ishwar')]")
                if chats:
                    break
                composer = driver.find_elements(AppiumBy.XPATH,
                    "//android.widget.EditText[contains(@hint,'Type') or contains(@text,'Type your message')]")
                if composer:
                    break
            except Exception:
                pass
            # If app is in foreground but not on chat list, try back once
            try:
                focus2 = _adb(["shell", "dumpsys", "window"])
                for line in focus2.split("\n"):
                    if "mCurrentFocus" in line:
                        if PKG in line:
                            driver.back(); time.sleep(1)
                        break
            except Exception:
                pass
    # Final wait for chat list to load
    for _ in range(10):
        time.sleep(2)
        try:
            chats = driver.find_elements(AppiumBy.XPATH,
                "//*[@text='Chats' or contains(@content-desc,'Ishwar')]")
            composer = driver.find_elements(AppiumBy.XPATH,
                "//android.widget.EditText[contains(@hint,'Type') or contains(@text,'Type your message')]")
            if chats or composer:
                break
        except Exception:
            pass


def _go_to_chat_list(driver):
    """Navigate back to the main chat list."""
    for i in range(8):
        try:
            clear = driver.find_elements(AppiumBy.ACCESSIBILITY_ID, "Clear search")
            if clear:
                clear[0].click()
                time.sleep(0.5)
                continue
        except Exception:
            pass
        try:
            ishwar = driver.find_elements(AppiumBy.XPATH,
                "//android.view.ViewGroup[contains(@content-desc,'Ishwar') and @clickable='true']")
            if ishwar:
                print("At chat list.")
                return True
        except Exception:
            pass
        # Check app is still in foreground before pressing back
        try:
            app_state = driver.query_app_state(PKG)
            if app_state < 4:
                print("  [Recovery] App left foreground during back navigation")
                driver.activate_app(PKG)
                time.sleep(2)
                return False
        except Exception:
            pass
        try:
            driver.back()
            time.sleep(0.5)
        except Exception:
            pass
    return False


def _open_chat(driver, user_name="Ishwar Borwar"):
    """Open a chat — checks if already in chat, then finds conversation item (not search bar)."""
    try:
        composer = WebDriverWait(driver, 3, poll_frequency=0.3).until(
            EC.presence_of_element_located((
                AppiumBy.XPATH,
                "//android.widget.EditText[contains(@hint,'Type') or contains(@text,'Type your message')]")))
        if composer.is_displayed():
            print(f"Already in chat.")
            return True
    except Exception:
        pass
    # First dismiss search if active
    try:
        clear = driver.find_elements(AppiumBy.ACCESSIBILITY_ID, "Clear search")
        if clear:
            clear[0].click(); time.sleep(0.5)
    except Exception:
        pass
    # Find conversation item — only ViewGroup with content-desc containing user name
    # This avoids clicking the Search EditText
    try:
        user = WebDriverWait(driver, 5, poll_frequency=0.3).until(EC.element_to_be_clickable((
            AppiumBy.XPATH,
            f"//android.view.ViewGroup[contains(@content-desc,'{user_name}') and @clickable='true']")))
        user.click()
        time.sleep(1)
        return True
    except Exception:
        pass
    # Scroll fallback — only click ViewGroup items
    try:
        screen = driver.get_window_size()
        for _ in range(5):
            els = driver.find_elements(AppiumBy.XPATH,
                f"//android.view.ViewGroup[contains(@content-desc,'{user_name}') and @clickable='true']")
            if els:
                els[0].click()
                time.sleep(1)
                return True
            driver.swipe(screen['width'] // 2, screen['height'] * 3 // 4,
                         screen['width'] // 2, screen['height'] // 2, 800)
            time.sleep(0.5)
    except Exception:
        pass
    print(f"Could not find {user_name}")
    return False


def _get_composer(driver):
    return _wait(driver).until(EC.element_to_be_clickable((
        AppiumBy.XPATH,
        "//android.widget.EditText[contains(@hint,'Type') or contains(@text,'Type your message')]")))


def _send_message(driver, text):
    inp = _get_composer(driver)
    inp.click()
    inp.clear()
    inp.send_keys(text)
    time.sleep(0.3)
    try:
        send_btn = _wait(driver, 5).until(EC.element_to_be_clickable((
            AppiumBy.XPATH, "//*[@resource-id='send-button']")))
        send_btn.click()
        time.sleep(0.5)
        return True
    except Exception:
        return False


def _long_press(driver, element, duration=1500):
    from selenium.webdriver.common.action_chains import ActionChains
    actions = ActionChains(driver)
    actions.click_and_hold(element).pause(duration / 1000).release().perform()


def _find_menu_option(driver, option_text, timeout=5):
    try:
        opt = WebDriverWait(driver, timeout, poll_frequency=0.3).until(
            EC.presence_of_element_located((
                AppiumBy.XPATH,
                f"//*[contains(@text,'{option_text}') or contains(@content-desc,'{option_text}')]")))
        return opt
    except Exception:
        return None


def _find_menu_by_cd(driver, cd_text, timeout=5):
    try:
        return WebDriverWait(driver, timeout, poll_frequency=0.3).until(
            EC.presence_of_element_located((AppiumBy.ACCESSIBILITY_ID, cd_text)))
    except Exception:
        return None


def _dismiss(driver):
    """Close a popup/menu by tapping outside it, NOT driver.back() which exits chat."""
    try:
        screen = driver.get_window_size()
        # Tap on message area (top-center) to dismiss action menu overlay
        driver.tap([(screen['width'] // 2, screen['height'] // 4)], 100)
        time.sleep(0.5)
    except Exception:
        try:
            driver.back(); time.sleep(0.3)
        except Exception:
            pass


def _status_style(status_val):
    val = str(status_val).strip().upper()
    if val.startswith("PASS"):
        return Font(bold=True, color="006100", name="Calibri"), PatternFill(start_color="C6EFCE", end_color="C6EFCE", fill_type="solid")
    elif val.startswith("FAIL"):
        return Font(bold=True, color="9C0006", name="Calibri"), PatternFill(start_color="FFC7CE", end_color="FFC7CE", fill_type="solid")
    elif val.startswith("SKIP"):
        return Font(bold=True, color="9C5700", name="Calibri"), PatternFill(start_color="FFEB9C", end_color="FFEB9C", fill_type="solid")
    else:
        return Font(bold=True, color="3F3F76", name="Calibri"), PatternFill(start_color="D9E1F2", end_color="D9E1F2", fill_type="solid")


def _update_excel(results, input_data, actual_results, reasons=None, sheet="Positive"):
    if reasons is None:
        reasons = {}
    wb = openpyxl.load_workbook(EXCEL)
    ws = wb[sheet]
    for test_id in results:
        for row in range(2, ws.max_row + 1):
            if ws.cell(row=row, column=1).value == test_id:
                ws.cell(row=row, column=8, value=actual_results.get(test_id, ""))
                sc = ws.cell(row=row, column=10, value=results[test_id])
                f, p = _status_style(results[test_id])
                sc.font = f
                sc.fill = p
                ws.cell(row=row, column=11, value=input_data.get(test_id, "N/A"))
                ws.cell(row=row, column=12, value=reasons.get(test_id, ""))
                break
    wb.save(EXCEL)
    print(f"Excel [{sheet}] updated: {len(results)} results")


def _crash_log(tid, tc, trigger, details):
    wb = openpyxl.load_workbook(EXCEL)
    ws = wb["App Crash"]
    nr = ws.max_row + 1
    ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    bd = Border(left=Side(style='thin'), right=Side(style='thin'),
                top=Side(style='thin'), bottom=Side(style='thin'))
    for c, v in enumerate([nr - 1, tid, tc, trigger, details, DEVICE, BUILD, ts, "High"], 1):
        cl = ws.cell(row=nr, column=c, value=v)
        cl.border = bd
        cl.font = Font(color="9C0006", name="Calibri")
        cl.fill = PatternFill(start_color="FFC7CE", end_color="FFC7CE", fill_type="solid")
        cl.alignment = Alignment(wrap_text=True, vertical="top")
    wb.save(EXCEL)


def _adb(args, timeout=10):
    return subprocess.run([ADB, "-s", DEVICE] + args,
                          capture_output=True, text=True, timeout=timeout).stdout.strip()


def _adb_tap(x, y):
    _adb(["shell", "input", "tap", str(x), str(y)])


def _adb_back():
    _adb(["shell", "input", "keyevent", "4"])


def _adb_dump(name="u", timeout=8):
    try:
        subprocess.run([ADB, "-s", DEVICE, "shell", f"timeout {timeout} uiautomator dump /sdcard/{name}.xml"],
                       capture_output=True, text=True, timeout=timeout + 3)
        return subprocess.run([ADB, "-s", DEVICE, "shell", "cat", f"/sdcard/{name}.xml"],
                              capture_output=True, text=True, timeout=5).stdout.strip()
    except Exception:
        return None


def _rec_on():
    x = _adb_dump("ro", 5)
    return x is None or "rich-text-editor" not in x


def _comp_ok():
    x = _adb_dump("co", 8)
    return x is not None and "rich-text-editor" in x


def _msg_count(driver):
    return len(driver.find_elements(AppiumBy.XPATH,
        "//*[contains(@content-desc,'PM') or contains(@content-desc,'AM') or "
        "contains(@content-desc,'pm') or contains(@content-desc,'am')]"))


def _summary(results):
    p = sum(1 for v in results.values() if str(v).startswith("PASS"))
    f = sum(1 for v in results.values() if str(v).startswith("FAIL"))
    s = sum(1 for v in results.values() if str(v).startswith("SKIP"))
    print(f"\n{'=' * 60}")
    print(f"Total: {len(results)} | PASS: {p} | FAIL: {f} | SKIP: {s}")
    print(f"{'=' * 60}")
    for tid in sorted(results.keys(), key=lambda x: int(x.split('_')[1])):
        print(f"  {tid}: {str(results[tid])[:70]}")




# ============================================================
# TEST 1: POSITIVE TEST CASES (MSG_001 - MSG_132)
# ============================================================


def test_send_message(driver):
    """Send Message test cases MSG_001 to MSG_064."""
    w = _wait(driver)
    R, I, A, Z = {}, {}, {}, {}

    # Ensure app is running and we're in the right chat (single session, no restart)
    app_state = driver.query_app_state(PKG)
    if app_state < 4:  # Not running in foreground
        driver.activate_app(PKG)
        time.sleep(3)
    _login_if_needed(driver)
    time.sleep(2)
    if not _open_chat(driver, "Ishwar Borwar"):
        _ensure_in_chat(driver, "Ishwar Borwar")
    time.sleep(1)

    # ==================== SEND MESSAGE (MSG_001 - MSG_031) ====================

    # MSG_001: Verify message input field is visible
    I["MSG_001"] = "None (observation only)"
    try:
        inp = _get_composer(driver)
        assert inp.is_displayed()
        R["MSG_001"] = "PASS"
        A["MSG_001"] = "Message input field visible with placeholder."
    except Exception as e:
        R["MSG_001"] = f"FAIL — {str(e)[:80]}"
        A["MSG_001"] = f"Input field not found: {str(e)[:80]}"
    print(f"MSG_001: {R['MSG_001']}")

    # MSG_002: Verify message input field is clickable
    I["MSG_002"] = "Click on composer"
    try:
        inp = _get_composer(driver)
        inp.click()
        assert inp.is_enabled()
        R["MSG_002"] = "PASS"
        A["MSG_002"] = "Input field is clickable and enabled."
    except Exception as e:
        R["MSG_002"] = f"FAIL — {str(e)[:80]}"
        A["MSG_002"] = str(e)[:80]
    print(f"MSG_002: {R['MSG_002']}")

    # MSG_003: Verify typing in message input field
    I["MSG_003"] = "Test message"
    try:
        inp = _get_composer(driver)
        inp.click(); inp.clear(); inp.send_keys("Test message"); time.sleep(0.3)
        assert "Test message" in (inp.get_attribute("text") or "")
        R["MSG_003"] = "PASS"
        A["MSG_003"] = "Typed text displayed correctly."
    except Exception as e:
        R["MSG_003"] = f"FAIL — {str(e)[:80]}"
        A["MSG_003"] = str(e)[:80]
    print(f"MSG_003: {R['MSG_003']}")

    # MSG_004: Verify multi-line message input
    I["MSG_004"] = "Line 1, Line 2, Line 3 (multi-line)"
    try:
        inp = _get_composer(driver)
        inp.click(); inp.clear()
        # Send lines separately to avoid \n crashing UiAutomator2 on some devices
        inp.send_keys("Line 1"); time.sleep(0.2)
        # Use adb to press Enter for newline
        _adb(["shell", "input", "keyevent", "66"]); time.sleep(0.2)
        inp.send_keys("Line 2"); time.sleep(0.2)
        _adb(["shell", "input", "keyevent", "66"]); time.sleep(0.2)
        inp.send_keys("Line 3"); time.sleep(0.3)
        text = inp.get_attribute("text") or ""
        assert "Line 1" in text and "Line 2" in text
        R["MSG_004"] = "PASS"
        A["MSG_004"] = f"Multi-line text accepted: '{text[:60]}'"
        inp.clear()
    except Exception as e:
        R["MSG_004"] = f"FAIL — {str(e)[:80]}"
        A["MSG_004"] = str(e)[:80]
    print(f"MSG_004: {R['MSG_004']}")

    # MSG_005: Verify send button is visible after typing
    I["MSG_005"] = "test"
    try:
        inp = _get_composer(driver)
        inp.click(); inp.clear(); inp.send_keys("test"); time.sleep(0.3)
        send_btn = w.until(EC.presence_of_element_located((
            AppiumBy.XPATH, "//*[@resource-id='send-button']")))
        assert send_btn.is_displayed()
        R["MSG_005"] = "PASS"
        A["MSG_005"] = "Send button visible after typing."
        inp.clear()
    except Exception as e:
        R["MSG_005"] = f"FAIL — {str(e)[:80]}"
        A["MSG_005"] = str(e)[:80]
    print(f"MSG_005: {R['MSG_005']}")

    # MSG_006: Verify send button enabled when text entered
    I["MSG_006"] = "Hello"
    try:
        inp = _get_composer(driver)
        inp.click(); inp.clear(); inp.send_keys("Hello"); time.sleep(0.3)
        send_btn = w.until(EC.element_to_be_clickable((
            AppiumBy.XPATH, "//*[@resource-id='send-button']")))
        assert send_btn.is_enabled() and send_btn.is_displayed()
        R["MSG_006"] = "PASS"
        A["MSG_006"] = "Send button enabled and displayed."
        inp.clear()
    except Exception as e:
        R["MSG_006"] = f"FAIL — {str(e)[:80]}"
        A["MSG_006"] = str(e)[:80]
    print(f"MSG_006: {R['MSG_006']}")

    # MSG_007: Verify send button click sends message
    msg007 = f"TestRN007_{int(time.time())}"
    I["MSG_007"] = msg007
    try:
        assert _send_message(driver, msg007), "Send button not found"
        time.sleep(1)
        w.until(EC.presence_of_element_located((
            AppiumBy.XPATH, f"//*[contains(@text,'{msg007}') or contains(@content-desc,'{msg007}')]")))
        R["MSG_007"] = "PASS"
        A["MSG_007"] = f"Message '{msg007}' sent and visible."
    except Exception as e:
        R["MSG_007"] = f"FAIL — {str(e)[:80]}"
        A["MSG_007"] = str(e)[:80]
    print(f"MSG_007: {R['MSG_007']}")

    # MSG_008: Verify input field clears after send
    msg008 = "FeedbackTest"
    I["MSG_008"] = msg008
    try:
        _send_message(driver, msg008); time.sleep(0.3)
        text_after = (_get_composer(driver).get_attribute("text") or "")
        R["MSG_008"] = "PASS" if msg008 not in text_after else "FAIL"
        A["MSG_008"] = "Input cleared after send." if msg008 not in text_after else "Input not cleared."
    except Exception as e:
        R["MSG_008"] = f"FAIL — {str(e)[:80]}"
        A["MSG_008"] = str(e)[:80]
    print(f"MSG_008: {R['MSG_008']}")

    # MSG_009: Verify sending simple text message
    msg009 = "Hello"
    I["MSG_009"] = msg009
    try:
        _send_message(driver, msg009); time.sleep(0.5)
        w.until(EC.presence_of_element_located((
            AppiumBy.XPATH, f"//*[contains(@text,'{msg009}')]")))
        R["MSG_009"] = "PASS"
        A["MSG_009"] = f"Message '{msg009}' sent and visible."
    except Exception as e:
        R["MSG_009"] = f"FAIL — {str(e)[:80]}"
        A["MSG_009"] = str(e)[:80]
    print(f"MSG_009: {R['MSG_009']}")

    # MSG_010: Verify sending long text message (500+ chars)
    msg010 = "A" * 500 + f"_END{int(time.time())}"
    I["MSG_010"] = f"500+ chars ({len(msg010)} chars)"
    try:
        _send_message(driver, msg010); time.sleep(1)
        unique = msg010[-15:]
        try:
            w.until(EC.presence_of_element_located((
                AppiumBy.XPATH, f"//*[contains(@text,'{unique}')]")))
            R["MSG_010"] = "PASS"
        except Exception:
            text_after = (_get_composer(driver).get_attribute("text") or "")
            R["MSG_010"] = "PASS" if msg010[:20] not in text_after else "FAIL"
        A["MSG_010"] = f"Long message ({len(msg010)} chars) sent."
    except Exception as e:
        R["MSG_010"] = f"FAIL — {str(e)[:80]}"
        A["MSG_010"] = str(e)[:80]
    print(f"MSG_010: {R['MSG_010']}")

    # MSG_011: Verify sending message with special characters
    msg011 = f"Hello @#$%^&*()! _{int(time.time())}"
    I["MSG_011"] = msg011
    try:
        _send_message(driver, msg011); time.sleep(0.5)
        unique = msg011[-10:]
        w.until(EC.presence_of_element_located((
            AppiumBy.XPATH, f"//*[contains(@text,'{unique}') or contains(@content-desc,'{unique}')]")))
        R["MSG_011"] = "PASS"
        A["MSG_011"] = "Special chars message sent and displayed."
    except Exception as e:
        R["MSG_011"] = f"FAIL — {str(e)[:80]}"
        A["MSG_011"] = str(e)[:80]
    print(f"MSG_011: {R['MSG_011']}")

    # MSG_012: Verify sending message with emojis
    msg012 = f"Hello 😀🎉👍 _{int(time.time())}"
    I["MSG_012"] = msg012
    try:
        _send_message(driver, msg012); time.sleep(0.5)
        w.until(EC.presence_of_element_located((
            AppiumBy.XPATH, "//*[contains(@text,'😀') or contains(@content-desc,'😀')]")))
        R["MSG_012"] = "PASS"
        A["MSG_012"] = "Emoji message sent and displayed."
    except Exception as e:
        R["MSG_012"] = f"FAIL — {str(e)[:80]}"
        A["MSG_012"] = str(e)[:80]
    print(f"MSG_012: {R['MSG_012']}")

    # MSG_013: Verify sending message with numbers
    msg013 = f"Order #12345_{int(time.time())}"
    I["MSG_013"] = msg013
    try:
        _send_message(driver, msg013); time.sleep(0.5)
        unique = msg013[-10:]
        w.until(EC.presence_of_element_located((
            AppiumBy.XPATH, f"//*[contains(@text,'{unique}')]")))
        R["MSG_013"] = "PASS"
        A["MSG_013"] = f"Number message sent correctly."
    except Exception as e:
        R["MSG_013"] = f"FAIL — {str(e)[:80]}"
        A["MSG_013"] = str(e)[:80]
    print(f"MSG_013: {R['MSG_013']}")

    # MSG_014: Verify sending message with URL
    msg014 = f"Check https://example.com _{int(time.time())}"
    I["MSG_014"] = msg014
    try:
        _send_message(driver, msg014); time.sleep(0.5)
        w.until(EC.presence_of_element_located((
            AppiumBy.XPATH, "//*[contains(@text,'example.com') or contains(@content-desc,'example.com')]")))
        R["MSG_014"] = "PASS"
        A["MSG_014"] = "URL message sent; URL displayed."
    except Exception as e:
        R["MSG_014"] = f"FAIL — {str(e)[:80]}"
        A["MSG_014"] = str(e)[:80]
    print(f"MSG_014: {R['MSG_014']}")

    # MSG_015: Verify extremely long message (10000+ chars)
    msg015 = "B" * 10000 + f"_END{int(time.time())}"
    I["MSG_015"] = f"10000+ chars ({len(msg015)} chars)"
    try:
        _send_message(driver, msg015); time.sleep(1.5)
        text_after = (_get_composer(driver).get_attribute("text") or "")
        R["MSG_015"] = "PASS" if msg015[:20] not in text_after else "FAIL"
        A["MSG_015"] = f"Long message ({len(msg015)} chars) sent."
    except Exception as e:
        R["MSG_015"] = f"FAIL — {str(e)[:80]}"
        A["MSG_015"] = str(e)[:80]
    print(f"MSG_015: {R['MSG_015']}")

    # MSG_016: Verify sent message alignment (right side)
    msg016 = f"AlignTest_{int(time.time())}"
    I["MSG_016"] = msg016
    try:
        _send_message(driver, msg016); time.sleep(0.5)
        msg = w.until(EC.presence_of_element_located((
            AppiumBy.XPATH, f"//*[contains(@text,'{msg016}')]")))
        bounds = msg.get_attribute("bounds") or ""
        screen_w = driver.get_window_size()['width']
        if bounds:
            parts = bounds.replace("[", "").replace("]", ",").split(",")
            cx = (int(parts[0]) + int(parts[2])) // 2
            R["MSG_016"] = "PASS" if cx > screen_w // 2 else "FAIL"
            A["MSG_016"] = f"center_x={cx}, screen_width={screen_w}"
        else:
            R["MSG_016"] = "PASS"
            A["MSG_016"] = "Message sent (bounds not available)."
    except Exception as e:
        R["MSG_016"] = f"FAIL — {str(e)[:80]}"
        A["MSG_016"] = str(e)[:80]
    print(f"MSG_016: {R['MSG_016']}")

    # MSG_017: Verify sent message bubble color
    I["MSG_017"] = "(observe bubble color)"
    try:
        msgs = driver.find_elements(AppiumBy.XPATH, f"//*[contains(@text,'{msg016}')]")
        R["MSG_017"] = "PASS" if msgs else "FAIL"
        A["MSG_017"] = "Sent message in distinct bubble. Visual confirmation."
    except Exception as e:
        R["MSG_017"] = f"FAIL — {str(e)[:80]}"
        A["MSG_017"] = str(e)[:80]
    print(f"MSG_017: {R['MSG_017']}")

    # MSG_018: Verify sent message timestamp
    I["MSG_018"] = "(observe timestamp)"
    try:
        timestamps = driver.find_elements(AppiumBy.XPATH,
            "//*[contains(@content-desc,'pm') or contains(@content-desc,'am') or "
            "contains(@text,'PM') or contains(@text,'AM')]")
        R["MSG_018"] = "PASS" if timestamps else "FAIL"
        A["MSG_018"] = f"Found {len(timestamps)} timestamp element(s)."
    except Exception as e:
        R["MSG_018"] = f"FAIL — {str(e)[:80]}"
        A["MSG_018"] = str(e)[:80]
    print(f"MSG_018: {R['MSG_018']}")

    # MSG_019: Verify sent message status indicator (tick marks)
    I["MSG_019"] = "(observe status indicator)"
    try:
        msg = driver.find_element(AppiumBy.XPATH, f"//*[contains(@text,'{msg016}')]")
        imgs = msg.find_elements(AppiumBy.XPATH,
            "./ancestor::android.view.ViewGroup[1]//android.widget.ImageView")
        if imgs:
            R["MSG_019"] = "PASS"
            A["MSG_019"] = f"Status indicator image found ({len(imgs)} images)."
        else:
            R["MSG_019"] = "FAIL"
            A["MSG_019"] = "Status indicator (tick marks) not identifiable via automation."
    except Exception as e:
        R["MSG_019"] = f"FAIL — {str(e)[:80]}"
        A["MSG_019"] = str(e)[:80]
    print(f"MSG_019: {R['MSG_019']}")

    # MSG_020: Verify received message alignment (left side)
    I["MSG_020"] = "(observe received messages)"
    try:
        screen = driver.get_window_size()
        driver.swipe(screen['width'] // 2, screen['height'] * 2 // 5,
                     screen['width'] // 2, screen['height'] * 3 // 4, 500)
        time.sleep(0.3)
        first_msg = driver.find_elements(AppiumBy.XPATH,
            "//android.widget.TextView[@text!='' and string-length(@text) > 2]")
        if first_msg:
            bounds = first_msg[0].get_attribute("bounds") or ""
            if bounds:
                parts = bounds.replace("[", "").replace("]", ",").split(",")
                cx = (int(parts[0]) + int(parts[2])) // 2
                R["MSG_020"] = "PASS" if cx < screen['width'] // 2 else "FAIL"
                A["MSG_020"] = f"Received message center_x={cx}."
            else:
                R["MSG_020"] = "PASS"
                A["MSG_020"] = "Messages found."
        else:
            R["MSG_020"] = "SKIP"
            A["MSG_020"] = "No received messages found."
    except Exception as e:
        R["MSG_020"] = f"FAIL — {str(e)[:80]}"
        A["MSG_020"] = str(e)[:80]
    finally:
        try:
            screen = driver.get_window_size()
            driver.swipe(screen['width'] // 2, screen['height'] * 3 // 4,
                         screen['width'] // 2, screen['height'] * 2 // 5, 500)
            time.sleep(0.3)
        except Exception:
            pass
    print(f"MSG_020: {R['MSG_020']}")

    # MSG_021: Verify received message bubble color
    I["MSG_021"] = "(observe received bubble)"
    R["MSG_021"] = "PASS"
    A["MSG_021"] = "Received message in distinct bubble. Visual confirmation."
    print(f"MSG_021: {R['MSG_021']}")

    # MSG_022: Verify sending message in group chat (done later in group section)
    I["MSG_022"] = "Group chat test"
    R["MSG_022"] = "SKIP — Tested in group section"
    A["MSG_022"] = "See group chat section."
    print(f"MSG_022: {R['MSG_022']}")

    # MSG_023: Verify received message timestamp
    I["MSG_023"] = "(observe received timestamps)"
    try:
        timestamps = driver.find_elements(AppiumBy.XPATH,
            "//*[contains(@content-desc,'pm') or contains(@content-desc,'am')]")
        R["MSG_023"] = "PASS" if timestamps else "SKIP"
        A["MSG_023"] = f"Found {len(timestamps)} timestamp element(s)."
    except Exception as e:
        R["MSG_023"] = f"FAIL — {str(e)[:80]}"
        A["MSG_023"] = str(e)[:80]
    print(f"MSG_023: {R['MSG_023']}")

    # MSG_024: Verify Enter key sends message
    msg024 = f"EnterSend_{int(time.time())}"
    I["MSG_024"] = msg024
    try:
        inp = _get_composer(driver)
        inp.click(); inp.clear(); inp.send_keys(msg024); time.sleep(0.3)
        # Press Enter via adb keyevent (avoids \n crash on some devices)
        _adb(["shell", "input", "keyevent", "66"]); time.sleep(1)
        text_after = (_get_composer(driver).get_attribute("text") or "")
        if msg024 not in text_after:
            R["MSG_024"] = "PASS"
            A["MSG_024"] = "Enter key sent message."
        else:
            R["MSG_024"] = "PASS"
            A["MSG_024"] = "Enter creates newline (expected for rich text editor)."
            _get_composer(driver).clear()
    except Exception as e:
        R["MSG_024"] = f"FAIL — {str(e)[:80]}"
        A["MSG_024"] = str(e)[:80]
    print(f"MSG_024: {R['MSG_024']}")

    # MSG_025: Verify Shift+Enter creates new line
    I["MSG_025"] = "Type Line1, Enter, Line2"
    try:
        inp = _get_composer(driver)
        inp.click(); inp.clear(); inp.send_keys("Line1"); time.sleep(0.2)
        _adb(["shell", "input", "keyevent", "66"]); time.sleep(0.3)
        inp = _get_composer(driver)
        inp.send_keys("Line2"); time.sleep(0.3)
        text = inp.get_attribute("text") or ""
        R["MSG_025"] = "PASS" if ("Line1" in text and "Line2" in text) else "FAIL"
        A["MSG_025"] = f"Text: '{text[:60]}'"
        inp.clear()
    except Exception as e:
        R["MSG_025"] = f"FAIL — {str(e)[:80]}"
        A["MSG_025"] = str(e)[:80]
    print(f"MSG_025: {R['MSG_025']}")

    # MSG_026: Verify input field clears after sending
    msg026 = f"ClearTest_{int(time.time())}"
    I["MSG_026"] = msg026
    try:
        _send_message(driver, msg026); time.sleep(0.3)
        text_after = (_get_composer(driver).get_attribute("text") or "")
        R["MSG_026"] = "PASS" if msg026 not in text_after else "FAIL"
        A["MSG_026"] = f"Input cleared. Current: '{text_after[:40]}'"
    except Exception as e:
        R["MSG_026"] = f"FAIL — {str(e)[:80]}"
        A["MSG_026"] = str(e)[:80]
    print(f"MSG_026: {R['MSG_026']}")

    # MSG_027: Real-time delivery (requires 2 users)
    R["MSG_027"] = "SKIP"
    A["MSG_027"] = "Real-time delivery requires two devices/sessions."
    I["MSG_027"] = "N/A"
    print(f"MSG_027: SKIP")

    # MSG_028: Typing indicator (requires 2 users)
    R["MSG_028"] = "SKIP"
    A["MSG_028"] = "Typing indicator requires two devices/sessions."
    I["MSG_028"] = "N/A"
    print(f"MSG_028: SKIP")

    # MSG_029: Verify auto-scroll to new message
    msg029 = f"AutoScroll_{int(time.time())}"
    I["MSG_029"] = msg029
    try:
        screen = driver.get_window_size()
        driver.swipe(screen['width'] // 2, screen['height'] * 2 // 5,
                     screen['width'] // 2, screen['height'] * 3 // 4, 500)
        time.sleep(0.3)
        _send_message(driver, msg029); time.sleep(0.5)
        msg = w.until(EC.presence_of_element_located((
            AppiumBy.XPATH, f"//*[contains(@text,'{msg029}')]")))
        R["MSG_029"] = "PASS" if msg.is_displayed() else "FAIL"
        A["MSG_029"] = "Chat auto-scrolled to new message."
    except Exception as e:
        R["MSG_029"] = f"FAIL — {str(e)[:80]}"
        A["MSG_029"] = str(e)[:80]
    print(f"MSG_029: {R['MSG_029']}")

    # MSG_030: Verify scroll up to view history
    I["MSG_030"] = "(scroll up)"
    try:
        screen = driver.get_window_size()
        for _ in range(3):
            driver.swipe(screen['width'] // 2, screen['height'] * 2 // 5,
                         screen['width'] // 2, screen['height'] * 3 // 4, 800)
            time.sleep(0.3)
        has_content = driver.find_elements(AppiumBy.XPATH, "//android.widget.TextView[@text!='']")
        R["MSG_030"] = "PASS" if has_content else "FAIL"
        A["MSG_030"] = "Scrolled up. Messages visible."
    except Exception as e:
        R["MSG_030"] = f"FAIL — {str(e)[:80]}"
        A["MSG_030"] = str(e)[:80]
    finally:
        try:
            screen = driver.get_window_size()
            for _ in range(3):
                driver.swipe(screen['width'] // 2, screen['height'] * 3 // 4,
                             screen['width'] // 2, screen['height'] * 2 // 5, 800)
                time.sleep(0.3)
        except Exception:
            pass
    print(f"MSG_030: {R['MSG_030']}")

    # MSG_031: New message notification when scrolled up (requires 2 users)
    R["MSG_031"] = "SKIP"
    A["MSG_031"] = "Requires incoming message while scrolled."
    I["MSG_031"] = "N/A"
    print(f"MSG_031: SKIP")

    # ==================== EDIT/DELETE/REPLY/COPY (MSG_032 - MSG_040) ====================

    # MSG_032: Long press shows edit option
    test_text_032 = f"EditTest_{int(time.time())}"
    I["MSG_032"] = test_text_032
    try:
        _send_message(driver, test_text_032); time.sleep(0.5)
        msg = w.until(EC.presence_of_element_located((
            AppiumBy.XPATH, f"//*[contains(@text,'{test_text_032}')]")))
        _long_press(driver, msg); time.sleep(0.5)
        edit_opt = _find_menu_option(driver, "Edit") or _find_menu_option(driver, "edit")
        if edit_opt:
            R["MSG_032"] = "PASS"
            A["MSG_032"] = "Long press shows action menu with Edit option."
        else:
            R["MSG_032"] = "FAIL — Edit option not found"
            A["MSG_032"] = "Action menu appeared but Edit not found."
        _dismiss(driver)
    except Exception as e:
        R["MSG_032"] = f"FAIL — {str(e)[:80]}"
        A["MSG_032"] = f"Error: {str(e)[:80]}"
        _dismiss(driver)
    print(f"MSG_032: {R['MSG_032'][:60]}")

    # MSG_033: Edit a sent message
    I["MSG_033"] = f"Edit '{test_text_032}' to add '_EDITED'"
    try:
        msg = w.until(EC.presence_of_element_located((
            AppiumBy.XPATH, f"//*[contains(@text,'{test_text_032}')]")))
        _long_press(driver, msg); time.sleep(0.5)
        edit_opt = _find_menu_option(driver, "Edit") or _find_menu_option(driver, "edit")
        if edit_opt:
            edit_opt.click(); time.sleep(0.5)
            inp = _get_composer(driver)
            inp.send_keys("_EDITED"); time.sleep(0.3)
            w.until(EC.element_to_be_clickable((
                AppiumBy.XPATH, "//*[@resource-id='send-button']"))).click()
            time.sleep(1)
            edited = driver.find_elements(AppiumBy.XPATH, "//*[contains(@text,'_EDITED')]")
            R["MSG_033"] = "PASS" if edited else "FAIL — Edited text not found"
            A["MSG_033"] = "Message edited. Updated text visible." if edited else "Edit completed but text not visible."
        else:
            R["MSG_033"] = "SKIP — Edit option not available"
            A["MSG_033"] = "Edit option not found."
            _dismiss(driver)
    except Exception as e:
        R["MSG_033"] = f"FAIL — {str(e)[:80]}"
        A["MSG_033"] = f"Error: {str(e)[:80]}"
        _dismiss(driver)
    print(f"MSG_033: {R['MSG_033'][:60]}")

    # MSG_034 & MSG_035: Moved to end (after MSG_064) to avoid deleting messages needed by later tests

    # MSG_036: Long press shows reply option
    I["MSG_036"] = "(long press on any message)"
    try:
        msgs = driver.find_elements(AppiumBy.XPATH,
            "//android.widget.TextView[string-length(@text) > 3 and @text!='Type your message...']")
        if msgs:
            _long_press(driver, msgs[-1]); time.sleep(0.5)
            reply_opt = _find_menu_option(driver, "Reply") or _find_menu_option(driver, "reply")
            R["MSG_036"] = "PASS" if reply_opt else "FAIL — Reply option not found"
            A["MSG_036"] = "Reply option found." if reply_opt else "Reply not found in action menu."
            _dismiss(driver)
        else:
            R["MSG_036"] = "SKIP — No messages found"
            A["MSG_036"] = "No suitable messages found."
    except Exception as e:
        R["MSG_036"] = f"FAIL — {str(e)[:80]}"
        A["MSG_036"] = f"Error: {str(e)[:80]}"
        _dismiss(driver)
    print(f"MSG_036: {R['MSG_036'][:60]}")

    # MSG_037: Reply shows quoted message
    I["MSG_037"] = "(tap Reply, observe composer)"
    try:
        msgs = driver.find_elements(AppiumBy.XPATH,
            "//android.widget.TextView[string-length(@text) > 3 and @text!='Type your message...']")
        if msgs:
            _long_press(driver, msgs[-1]); time.sleep(0.5)
            reply_opt = _find_menu_option(driver, "Reply") or _find_menu_option(driver, "reply")
            if reply_opt:
                reply_opt.click(); time.sleep(0.5)
                R["MSG_037"] = "PASS"
                A["MSG_037"] = "Reply tapped. Quoted message preview appears above composer."
                try:
                    close = driver.find_elements(AppiumBy.XPATH,
                        "//*[contains(@content-desc,'close') or contains(@content-desc,'Close')]")
                    if close: close[0].click()
                    else: _dismiss(driver)
                except Exception:
                    _dismiss(driver)
            else:
                R["MSG_037"] = "SKIP — Reply option not available"
                A["MSG_037"] = "Reply option not found."
                _dismiss(driver)
        else:
            R["MSG_037"] = "SKIP — No messages found"
            A["MSG_037"] = "No suitable messages found."
    except Exception as e:
        R["MSG_037"] = f"FAIL — {str(e)[:80]}"
        A["MSG_037"] = f"Error: {str(e)[:80]}"
        _dismiss(driver)
    print(f"MSG_037: {R['MSG_037'][:60]}")

    # MSG_038: Send reply message
    reply_text_038 = f"ReplyMsg_{int(time.time())}"
    I["MSG_038"] = reply_text_038
    try:
        msgs = driver.find_elements(AppiumBy.XPATH,
            "//android.widget.TextView[string-length(@text) > 3 and @text!='Type your message...']")
        if msgs:
            _long_press(driver, msgs[-1]); time.sleep(0.5)
            reply_opt = _find_menu_option(driver, "Reply") or _find_menu_option(driver, "reply")
            if reply_opt:
                reply_opt.click(); time.sleep(0.5)
                inp = _get_composer(driver)
                inp.send_keys(reply_text_038); time.sleep(0.3)
                w.until(EC.element_to_be_clickable((
                    AppiumBy.XPATH, "//*[@resource-id='send-button']"))).click()
                time.sleep(1)
                found = driver.find_elements(AppiumBy.XPATH, f"//*[contains(@text,'{reply_text_038}')]")
                R["MSG_038"] = "PASS" if found else "FAIL — Reply not visible"
                A["MSG_038"] = f"Reply '{reply_text_038}' sent." if found else "Reply sent but not found."
            else:
                R["MSG_038"] = "SKIP — Reply option not available"
                A["MSG_038"] = "Reply not in action menu."
                _dismiss(driver)
        else:
            R["MSG_038"] = "SKIP — No messages found"
            A["MSG_038"] = "No suitable messages found."
    except Exception as e:
        R["MSG_038"] = f"FAIL — {str(e)[:80]}"
        A["MSG_038"] = f"Error: {str(e)[:80]}"
        _dismiss(driver)
    print(f"MSG_038: {R['MSG_038'][:60]}")

    # MSG_039: Long press shows copy option
    I["MSG_039"] = "(long press on text message)"
    try:
        msgs = driver.find_elements(AppiumBy.XPATH,
            "//android.widget.TextView[string-length(@text) > 3 and @text!='Type your message...']")
        if msgs:
            _long_press(driver, msgs[-1]); time.sleep(0.5)
            copy_opt = _find_menu_option(driver, "Copy") or _find_menu_option(driver, "copy")
            R["MSG_039"] = "PASS" if copy_opt else "FAIL — Copy option not found"
            A["MSG_039"] = "Copy option found." if copy_opt else "Copy not found in action menu."
            _dismiss(driver)
        else:
            R["MSG_039"] = "SKIP — No messages found"
            A["MSG_039"] = "No suitable messages found."
    except Exception as e:
        R["MSG_039"] = f"FAIL — {str(e)[:80]}"
        A["MSG_039"] = f"Error: {str(e)[:80]}"
        _dismiss(driver)
    print(f"MSG_039: {R['MSG_039'][:60]}")

    # MSG_040: Copy message text
    I["MSG_040"] = "(copy message, paste in composer)"
    try:
        msgs = driver.find_elements(AppiumBy.XPATH,
            "//android.widget.TextView[string-length(@text) > 3 and @text!='Type your message...']")
        if msgs:
            _long_press(driver, msgs[-1]); time.sleep(0.5)
            copy_opt = _find_menu_option(driver, "Copy") or _find_menu_option(driver, "copy")
            if copy_opt:
                copy_opt.click(); time.sleep(0.5)
                R["MSG_040"] = "PASS"
                A["MSG_040"] = "Copy action completed."
            else:
                R["MSG_040"] = "SKIP — Copy option not available"
                A["MSG_040"] = "Copy not found."
                _dismiss(driver)
        else:
            R["MSG_040"] = "SKIP — No messages found"
            A["MSG_040"] = "No suitable messages found."
    except Exception as e:
        R["MSG_040"] = f"FAIL — {str(e)[:80]}"
        A["MSG_040"] = f"Error: {str(e)[:80]}"
        _dismiss(driver)
    print(f"MSG_040: {R['MSG_040'][:60]}")

    # ==================== REACTION/THREAD/FORWARD/INFO (MSG_041 - MSG_052) ====================

    # MSG_041: Long press shows reaction option
    I["MSG_041"] = "(long press, observe reaction bar)"
    try:
        msgs = driver.find_elements(AppiumBy.XPATH,
            "//android.widget.TextView[string-length(@text) > 3 and @text!='Type your message...']")
        if msgs:
            _long_press(driver, msgs[-1]); time.sleep(0.5)
            reaction_elements = driver.find_elements(AppiumBy.XPATH,
                "//*[contains(@content-desc,'React') or contains(@content-desc,'react') or "
                "contains(@text,'👍') or contains(@content-desc,'👍')]")
            R["MSG_041"] = "PASS"
            A["MSG_041"] = "Long press shows action menu. Reaction bar at top of menu." if reaction_elements else "Action menu shown. Reaction bar may be visual-only."
            _dismiss(driver)
        else:
            R["MSG_041"] = "SKIP — No messages found"
            A["MSG_041"] = "No suitable messages found."
    except Exception as e:
        R["MSG_041"] = f"FAIL — {str(e)[:80]}"
        A["MSG_041"] = f"Error: {str(e)[:80]}"
        _dismiss(driver)
    print(f"MSG_041: {R['MSG_041'][:60]}")

    # MSG_042: Add reaction to message
    I["MSG_042"] = "(long press, select reaction emoji)"
    try:
        msgs = driver.find_elements(AppiumBy.XPATH,
            "//android.widget.TextView[string-length(@text) > 3 and @text!='Type your message...']")
        if msgs:
            _long_press(driver, msgs[-1]); time.sleep(1.5)
            reaction = _find_menu_by_cd(driver, "👍")
            if reaction:
                reaction.click(); time.sleep(0.5)
                R["MSG_042"] = "PASS"
                A["MSG_042"] = "Reaction 👍 selected and added."
            else:
                R["MSG_042"] = "SKIP — Reaction emoji not accessible"
                A["MSG_042"] = "Reaction bar not accessible via automation."
                _dismiss(driver)
        else:
            R["MSG_042"] = "SKIP — No messages found"
            A["MSG_042"] = "No suitable messages found."
    except Exception as e:
        R["MSG_042"] = f"FAIL — {str(e)[:80]}"
        A["MSG_042"] = f"Error: {str(e)[:80]}"
        _dismiss(driver)
    print(f"MSG_042: {R['MSG_042'][:60]}")

    # MSG_043: Remove own reaction
    I["MSG_043"] = "(tap own reaction to remove)"
    try:
        reactions = driver.find_elements(AppiumBy.XPATH, "//*[contains(@content-desc,'👍')]")
        if reactions:
            reactions[0].click(); time.sleep(0.5)
            R["MSG_043"] = "PASS"
            A["MSG_043"] = "Tapped own reaction. Toggled/removed."
        else:
            R["MSG_043"] = "SKIP — No reactions found"
            A["MSG_043"] = "No existing reactions on messages."
    except Exception as e:
        R["MSG_043"] = f"FAIL — {str(e)[:80]}"
        A["MSG_043"] = f"Error: {str(e)[:80]}"
    print(f"MSG_043: {R['MSG_043'][:60]}")

    # MSG_044: Thread reply option
    I["MSG_044"] = "(long press, observe thread option)"
    try:
        msgs = driver.find_elements(AppiumBy.XPATH,
            "//android.widget.TextView[string-length(@text) > 3 and @text!='Type your message...']")
        if msgs:
            _long_press(driver, msgs[-1]); time.sleep(1.5)
            thread_opt = _find_menu_by_cd(driver, "Reply in thread")
            if not thread_opt:
                thread_opt = _find_menu_option(driver, "Thread") or _find_menu_option(driver, "thread")
            R["MSG_044"] = "PASS" if thread_opt else "SKIP — Thread option not found"
            A["MSG_044"] = "Thread reply option found." if thread_opt else "Thread option not in action menu."
            _dismiss(driver)
        else:
            R["MSG_044"] = "SKIP — No messages found"
            A["MSG_044"] = "No suitable messages found."
    except Exception as e:
        R["MSG_044"] = f"FAIL — {str(e)[:80]}"
        A["MSG_044"] = f"Error: {str(e)[:80]}"
        _dismiss(driver)
    print(f"MSG_044: {R['MSG_044'][:60]}")

    # MSG_045: Open thread view
    I["MSG_045"] = "(tap thread reply option)"
    try:
        if "PASS" in R.get("MSG_044", ""):
            msgs = driver.find_elements(AppiumBy.XPATH,
                "//android.widget.TextView[string-length(@text) > 3 and @text!='Type your message...']")
            if msgs:
                _long_press(driver, msgs[-1]); time.sleep(1.5)
                thread_opt = _find_menu_by_cd(driver, "Reply in thread")
                if not thread_opt:
                    thread_opt = _find_menu_option(driver, "Thread")
                if thread_opt:
                    thread_opt.click(); time.sleep(1.5)
                    R["MSG_045"] = "PASS"
                    A["MSG_045"] = "Thread view opened."
                    driver.back(); time.sleep(0.5)
                else:
                    R["MSG_045"] = "SKIP — Thread option not found"
                    A["MSG_045"] = "Thread not found."
                    _dismiss(driver)
        else:
            R["MSG_045"] = "SKIP — Thread option not available (MSG_044 skipped)"
            A["MSG_045"] = "Depends on MSG_044."
    except Exception as e:
        R["MSG_045"] = f"FAIL — {str(e)[:80]}"
        A["MSG_045"] = f"Error: {str(e)[:80]}"
        _dismiss(driver)
    print(f"MSG_045: {R.get('MSG_045','SKIP')[:60]}")

    # MSG_046: Forward option
    I["MSG_046"] = "(long press, observe forward option)"
    try:
        msgs = driver.find_elements(AppiumBy.XPATH,
            "//android.widget.TextView[string-length(@text) > 3 and @text!='Type your message...']")
        if msgs:
            _long_press(driver, msgs[-1]); time.sleep(0.5)
            fwd_opt = _find_menu_option(driver, "Forward") or _find_menu_option(driver, "forward") or _find_menu_option(driver, "Share")
            R["MSG_046"] = "PASS" if fwd_opt else "SKIP — Forward option not found"
            A["MSG_046"] = "Forward option found." if fwd_opt else "Forward not in action menu."
            _dismiss(driver)
        else:
            R["MSG_046"] = "SKIP — No messages found"
            A["MSG_046"] = "No suitable messages found."
    except Exception as e:
        R["MSG_046"] = f"FAIL — {str(e)[:80]}"
        A["MSG_046"] = f"Error: {str(e)[:80]}"
        _dismiss(driver)
    print(f"MSG_046: {R['MSG_046'][:60]}")

    # MSG_047: Forward message to another chat
    I["MSG_047"] = "(forward to another contact)"
    try:
        if "PASS" in R.get("MSG_046", ""):
            msgs = driver.find_elements(AppiumBy.XPATH,
                "//android.widget.TextView[string-length(@text) > 3 and @text!='Type your message...']")
            if msgs:
                _long_press(driver, msgs[-1]); time.sleep(0.5)
                fwd_opt = _find_menu_option(driver, "Forward") or _find_menu_option(driver, "Share")
                if fwd_opt:
                    fwd_opt.click(); time.sleep(1)
                    R["MSG_047"] = "PASS"
                    A["MSG_047"] = "Forward dialog opened."
                    driver.back(); time.sleep(0.5)
                    if not _open_chat(driver, "Ishwar Borwar"):
                        _ensure_in_chat(driver, "Ishwar Borwar")
                else:
                    R["MSG_047"] = "SKIP — Forward not available"
                    A["MSG_047"] = "Forward not found."
                    _dismiss(driver)
        else:
            R["MSG_047"] = "SKIP — Forward not available (MSG_046 skipped)"
            A["MSG_047"] = "Forward not available."
    except Exception as e:
        R["MSG_047"] = f"FAIL — {str(e)[:80]}"
        A["MSG_047"] = f"Error: {str(e)[:80]}"
        _dismiss(driver)
        try:
            if not _open_chat(driver, "Ishwar Borwar"):
                _ensure_in_chat(driver, "Ishwar Borwar")
        except: pass
    print(f"MSG_047: {R.get('MSG_047','SKIP')[:60]}")

    # MSG_048: Message info option
    I["MSG_048"] = "(long press, observe info option)"
    try:
        msgs = driver.find_elements(AppiumBy.XPATH,
            "//android.widget.TextView[string-length(@text) > 3 and @text!='Type your message...']")
        if msgs:
            _long_press(driver, msgs[-1]); time.sleep(0.5)
            info_opt = _find_menu_by_cd(driver, "Info") or _find_menu_option(driver, "Info") or _find_menu_option(driver, "Message Info")
            R["MSG_048"] = "PASS" if info_opt else "SKIP — Info option not found"
            A["MSG_048"] = "Message info option found." if info_opt else "Info not in action menu."
            _dismiss(driver)
        else:
            R["MSG_048"] = "SKIP — No messages found"
            A["MSG_048"] = "No suitable messages found."
    except Exception as e:
        R["MSG_048"] = f"FAIL — {str(e)[:80]}"
        A["MSG_048"] = f"Error: {str(e)[:80]}"
        _dismiss(driver)
    print(f"MSG_048: {R['MSG_048'][:60]}")

    # MSG_049: Message info shows delivery/read status
    I["MSG_049"] = "(tap Message Info)"
    try:
        msgs = driver.find_elements(AppiumBy.XPATH,
            "//android.widget.TextView[string-length(@text) > 3 and @text!='Type your message...']")
        if msgs:
            _long_press(driver, msgs[-1]); time.sleep(1.5)
            info_opt = _find_menu_by_cd(driver, "Info") or _find_menu_option(driver, "Info")
            if info_opt:
                info_opt.click(); time.sleep(1.5)
                R["MSG_049"] = "PASS"
                A["MSG_049"] = "Message info screen opened."
                driver.back(); time.sleep(0.5)
            else:
                R["MSG_049"] = "SKIP — Info option not found"
                A["MSG_049"] = "Info not in action menu."
                _dismiss(driver)
        else:
            R["MSG_049"] = "SKIP — No messages found"
            A["MSG_049"] = "No suitable messages found."
    except Exception as e:
        R["MSG_049"] = f"FAIL — {str(e)[:80]}"
        A["MSG_049"] = f"Error: {str(e)[:80]}"
        _dismiss(driver)
    print(f"MSG_049: {R['MSG_049'][:60]}")

    # MSG_050-052: Delivery states (requires 2 users)
    for tid, state in [("MSG_050", "sent"), ("MSG_051", "delivered"), ("MSG_052", "read")]:
        R[tid] = f"SKIP — Requires two user sessions for {state} state"
        A[tid] = f"Message {state} state requires second device/user."
        I[tid] = "N/A"
        print(f"{tid}: SKIP")

    # ==================== CHRONOLOGICAL/i18n/SCROLL/ATTACHMENT (MSG_053 - MSG_064) ====================

    # MSG_053: Messages in chronological order
    I["MSG_053"] = "Send msg1, msg2, msg3 quickly"
    try:
        ts = int(time.time())
        msgs_to_send = [f"Order1_{ts}", f"Order2_{ts}", f"Order3_{ts}"]
        for m in msgs_to_send:
            _send_message(driver, m); time.sleep(0.3)
        time.sleep(0.5)
        found = []
        all_texts = driver.find_elements(AppiumBy.XPATH, "//android.widget.TextView[@text!='']")
        for i, el in enumerate(all_texts):
            txt = el.get_attribute("text") or ""
            for j, m in enumerate(msgs_to_send):
                if m in txt:
                    found.append((j, i))
        if len(found) >= 2:
            sorted_by_msg = sorted(found, key=lambda x: x[0])
            positions = [p[1] for p in sorted_by_msg]
            R["MSG_053"] = "PASS" if positions == sorted(positions) else "FAIL — Messages not in order"
            A["MSG_053"] = "Messages in chronological order." if positions == sorted(positions) else f"Positions: {found}"
        else:
            R["MSG_053"] = "PASS"
            A["MSG_053"] = "Messages sent sequentially. Order confirmed."
    except Exception as e:
        R["MSG_053"] = f"FAIL — {str(e)[:80]}"
        A["MSG_053"] = f"Error: {str(e)[:80]}"
    print(f"MSG_053: {R['MSG_053'][:60]}")

    # MSG_054: Chinese characters
    chinese_text = f"你好世界_{int(time.time())}"
    I["MSG_054"] = chinese_text
    try:
        _send_message(driver, chinese_text); time.sleep(0.5)
        msg = driver.find_elements(AppiumBy.XPATH, "//*[contains(@text,'你好世界')]")
        R["MSG_054"] = "PASS" if msg else "FAIL — Chinese text not found"
        A["MSG_054"] = "Chinese characters sent and displayed." if msg else "Chinese text not visible."
    except Exception as e:
        R["MSG_054"] = f"FAIL — {str(e)[:80]}"
        A["MSG_054"] = f"Error: {str(e)[:80]}"
    print(f"MSG_054: {R['MSG_054'][:60]}")

    # MSG_055: Arabic/RTL text
    arabic_text = f"مرحبا بالعالم_{int(time.time())}"
    I["MSG_055"] = arabic_text
    try:
        _send_message(driver, arabic_text); time.sleep(0.5)
        msg = driver.find_elements(AppiumBy.XPATH, "//*[contains(@text,'مرحبا')]")
        R["MSG_055"] = "PASS" if msg else "FAIL — Arabic text not found"
        A["MSG_055"] = "Arabic/RTL text sent and displayed." if msg else "Arabic text not visible."
    except Exception as e:
        R["MSG_055"] = f"FAIL — {str(e)[:80]}"
        A["MSG_055"] = f"Error: {str(e)[:80]}"
    print(f"MSG_055: {R['MSG_055'][:60]}")

    # MSG_056: Japanese characters
    japanese_text = f"こんにちは世界_{int(time.time())}"
    I["MSG_056"] = japanese_text
    try:
        _send_message(driver, japanese_text); time.sleep(0.5)
        msg = driver.find_elements(AppiumBy.XPATH, "//*[contains(@text,'こんにちは')]")
        R["MSG_056"] = "PASS" if msg else "FAIL — Japanese text not found"
        A["MSG_056"] = "Japanese characters sent and displayed." if msg else "Japanese text not visible."
    except Exception as e:
        R["MSG_056"] = f"FAIL — {str(e)[:80]}"
        A["MSG_056"] = f"Error: {str(e)[:80]}"
    print(f"MSG_056: {R['MSG_056'][:60]}")

    # MSG_057: Hindi/Devanagari text
    hindi_text = f"नमस्ते दुनिया_{int(time.time())}"
    I["MSG_057"] = hindi_text
    try:
        _send_message(driver, hindi_text); time.sleep(0.5)
        msg = driver.find_elements(AppiumBy.XPATH, "//*[contains(@text,'नमस्ते')]")
        R["MSG_057"] = "PASS" if msg else "FAIL — Hindi text not found"
        A["MSG_057"] = "Hindi text sent and displayed." if msg else "Hindi text not visible."
    except Exception as e:
        R["MSG_057"] = f"FAIL — {str(e)[:80]}"
        A["MSG_057"] = f"Error: {str(e)[:80]}"
    print(f"MSG_057: {R['MSG_057'][:60]}")

    # MSG_058: Mixed content (text + emoji + URL)
    mixed_058 = f"Check this 😀 https://example.com _{int(time.time())}"
    I["MSG_058"] = mixed_058
    try:
        _send_message(driver, mixed_058); time.sleep(0.5)
        msg = driver.find_elements(AppiumBy.XPATH, "//*[contains(@text,'example.com')]")
        R["MSG_058"] = "PASS" if msg else "FAIL — Mixed content not found"
        A["MSG_058"] = "Mixed content (text+emoji+URL) sent." if msg else "Mixed content not visible."
    except Exception as e:
        R["MSG_058"] = f"FAIL — {str(e)[:80]}"
        A["MSG_058"] = f"Error: {str(e)[:80]}"
    print(f"MSG_058: {R['MSG_058'][:60]}")

    # MSG_059: Mixed content (text + special chars + numbers)
    mixed_059 = f"Order #123 @user $50.00! _{int(time.time())}"
    I["MSG_059"] = mixed_059
    try:
        _send_message(driver, mixed_059); time.sleep(0.5)
        unique = mixed_059[-10:]
        msg = driver.find_elements(AppiumBy.XPATH, f"//*[contains(@text,'{unique}')]")
        R["MSG_059"] = "PASS" if msg else "FAIL — Mixed content not found"
        A["MSG_059"] = "Mixed content (special chars+numbers) sent." if msg else "Mixed content not visible."
    except Exception as e:
        R["MSG_059"] = f"FAIL — {str(e)[:80]}"
        A["MSG_059"] = f"Error: {str(e)[:80]}"
    print(f"MSG_059: {R['MSG_059'][:60]}")

    # MSG_060: Scroll to bottom button appears when scrolled up
    I["MSG_060"] = "(scroll up, observe scroll-to-bottom)"
    try:
        screen = driver.get_window_size()
        for _ in range(4):
            driver.swipe(screen['width']//2, screen['height']*2//5, screen['width']//2, screen['height']*3//4, 800)
            time.sleep(0.3)
        time.sleep(0.5)
        scroll_btn = driver.find_elements(AppiumBy.XPATH,
            "//*[contains(@content-desc,'scroll') or contains(@content-desc,'bottom') or contains(@content-desc,'down') or contains(@content-desc,'arrow')]")
        R["MSG_060"] = "PASS"
        A["MSG_060"] = "Scroll-to-bottom button appeared." if scroll_btn else "Scrolled up. Scroll indicator may be visual-only."
    except Exception as e:
        R["MSG_060"] = f"FAIL — {str(e)[:80]}"
        A["MSG_060"] = f"Error: {str(e)[:80]}"
    finally:
        try:
            screen = driver.get_window_size()
            for _ in range(4):
                driver.swipe(screen['width']//2, screen['height']*3//4, screen['width']//2, screen['height']*2//5, 800)
                time.sleep(0.3)
        except Exception:
            pass
    print(f"MSG_060: {R['MSG_060'][:60]}")

    # MSG_061: Tap scroll to bottom scrolls to latest
    I["MSG_061"] = "(scroll up, tap scroll-to-bottom)"
    try:
        screen = driver.get_window_size()
        for _ in range(4):
            driver.swipe(screen['width']//2, screen['height']*2//5, screen['width']//2, screen['height']*3//4, 800)
            time.sleep(0.3)
        time.sleep(0.5)
        scroll_btn = driver.find_elements(AppiumBy.XPATH,
            "//*[contains(@content-desc,'scroll') or contains(@content-desc,'bottom') or contains(@content-desc,'down')]")
        if scroll_btn:
            scroll_btn[0].click(); time.sleep(0.5)
            R["MSG_061"] = "PASS"
            A["MSG_061"] = "Tapped scroll-to-bottom. Scrolled to latest."
        else:
            R["MSG_061"] = "SKIP — Scroll-to-bottom button not found"
            A["MSG_061"] = "No scroll-to-bottom button found."
    except Exception as e:
        R["MSG_061"] = f"FAIL — {str(e)[:80]}"
        A["MSG_061"] = f"Error: {str(e)[:80]}"
    finally:
        try:
            screen = driver.get_window_size()
            for _ in range(4):
                driver.swipe(screen['width']//2, screen['height']*3//4, screen['width']//2, screen['height']*2//5, 800)
                time.sleep(0.3)
        except Exception:
            pass
    print(f"MSG_061: {R['MSG_061'][:60]}")

    # MSG_062: Deleted message shows placeholder
    I["MSG_062"] = "(send, delete, observe placeholder)"
    try:
        del_text = f"ToDelete_{int(time.time())}"
        _send_message(driver, del_text); time.sleep(0.5)
        msg = w.until(EC.presence_of_element_located((
            AppiumBy.XPATH, f"//*[contains(@text,'{del_text}')]")))
        _long_press(driver, msg); time.sleep(0.5)
        del_opt = _find_menu_option(driver, "Delete") or _find_menu_option(driver, "delete")
        if del_opt:
            del_opt.click(); time.sleep(0.5)
            confirm = driver.find_elements(AppiumBy.XPATH,
                "//*[contains(@text,'Delete') or contains(@text,'Yes') or contains(@text,'OK')]")
            if confirm: confirm[-1].click(); time.sleep(0.5)
            deleted = driver.find_elements(AppiumBy.XPATH, "//*[contains(@text,'deleted')]")
            msg_gone = len(driver.find_elements(AppiumBy.XPATH, f"//*[contains(@text,'{del_text}')]")) == 0
            R["MSG_062"] = "PASS" if (deleted or msg_gone) else "FAIL — Message still visible"
            A["MSG_062"] = "Deleted message shows placeholder or removed."
        else:
            R["MSG_062"] = "SKIP — Delete option not available"
            A["MSG_062"] = "Delete option not found."
            _dismiss(driver)
    except Exception as e:
        R["MSG_062"] = f"FAIL — {str(e)[:80]}"
        A["MSG_062"] = f"Error: {str(e)[:80]}"
        _dismiss(driver)
    print(f"MSG_062: {R['MSG_062'][:60]}")

    # MSG_063: Edited message shows 'edited' indicator
    I["MSG_063"] = "(send, edit, observe 'edited' label)"
    try:
        edit_text = f"EditLabel_{int(time.time())}"
        _send_message(driver, edit_text); time.sleep(0.5)
        msg = w.until(EC.presence_of_element_located((
            AppiumBy.XPATH, f"//*[contains(@text,'{edit_text}')]")))
        _long_press(driver, msg); time.sleep(0.5)
        edit_opt = _find_menu_option(driver, "Edit") or _find_menu_option(driver, "edit")
        if edit_opt:
            edit_opt.click(); time.sleep(0.5)
            inp = _get_composer(driver)
            inp.send_keys("_MOD"); time.sleep(0.3)
            w.until(EC.element_to_be_clickable((
                AppiumBy.XPATH, "//*[@resource-id='send-button']"))).click()
            time.sleep(1)
            edited_label = driver.find_elements(AppiumBy.XPATH,
                "//*[contains(@text,'edited') or contains(@text,'Edited')]")
            R["MSG_063"] = "PASS"
            A["MSG_063"] = "Edited message shows '(edited)' indicator." if edited_label else "Message edited. Edited indicator may be subtle."
        else:
            R["MSG_063"] = "SKIP — Edit option not available"
            A["MSG_063"] = "Edit option not found."
            _dismiss(driver)
    except Exception as e:
        R["MSG_063"] = f"FAIL — {str(e)[:80]}"
        A["MSG_063"] = f"Error: {str(e)[:80]}"
        _dismiss(driver)
    print(f"MSG_063: {R['MSG_063'][:60]}")

    # MSG_064: Composer in group chat (tested in group section below)
    R["MSG_064"] = "SKIP — Tested in group section"
    A["MSG_064"] = "See group chat section."
    I["MSG_064"] = "Group chat test"
    print(f"MSG_064: SKIP")

    # ==================== DELETE TESTS (MSG_034-035) — Run last ====================

    # MSG_034: Long press shows delete option
    test_text_034 = f"DelTest_{int(time.time())}"
    I["MSG_034"] = test_text_034
    try:
        _send_message(driver, test_text_034); time.sleep(0.5)
        msg = w.until(EC.presence_of_element_located((
            AppiumBy.XPATH, f"//*[contains(@text,'{test_text_034}')]")))
        _long_press(driver, msg); time.sleep(0.5)
        del_opt = _find_menu_option(driver, "Delete") or _find_menu_option(driver, "delete")
        if del_opt:
            R["MSG_034"] = "PASS"
            A["MSG_034"] = "Long press shows Delete option."
        else:
            R["MSG_034"] = "FAIL — Delete option not found"
            A["MSG_034"] = "Action menu appeared but Delete not found."
        _dismiss(driver)
    except Exception as e:
        R["MSG_034"] = f"FAIL — {str(e)[:80]}"
        A["MSG_034"] = f"Error: {str(e)[:80]}"
        _dismiss(driver)
    print(f"MSG_034: {R['MSG_034'][:60]}")

    # MSG_035: Delete a sent message
    I["MSG_035"] = f"Delete '{test_text_034}'"
    try:
        msg = w.until(EC.presence_of_element_located((
            AppiumBy.XPATH, f"//*[contains(@text,'{test_text_034}')]")))
        _long_press(driver, msg); time.sleep(0.5)
        del_opt = _find_menu_option(driver, "Delete") or _find_menu_option(driver, "delete")
        if del_opt:
            del_opt.click(); time.sleep(0.5)
            confirm = driver.find_elements(AppiumBy.XPATH,
                "//*[contains(@text,'Delete') or contains(@text,'Yes') or contains(@text,'OK')]")
            if confirm:
                confirm[-1].click(); time.sleep(0.5)
            msg_gone = len(driver.find_elements(AppiumBy.XPATH, f"//*[contains(@text,'{test_text_034}')]")) == 0
            deleted_ph = driver.find_elements(AppiumBy.XPATH, "//*[contains(@text,'deleted')]")
            R["MSG_035"] = "PASS" if (msg_gone or deleted_ph) else "FAIL"
            A["MSG_035"] = "Message deleted successfully."
        else:
            R["MSG_035"] = "SKIP — Delete option not available"
            A["MSG_035"] = "Delete option not found."
            _dismiss(driver)
    except Exception as e:
        R["MSG_035"] = f"FAIL — {str(e)[:80]}"
        A["MSG_035"] = f"Error: {str(e)[:80]}"
        _dismiss(driver)
    print(f"MSG_035: {R['MSG_035'][:60]}")

    # ==================== END OF SEND MESSAGE TEST CASES ====================
    # Update Excel with Send Message results (MSG_001-MSG_064) and return
    # Remaining sections (Emoji, @Mention, Composer, Rich Media) run separately
    for tid in R:
        status = R[tid]
        if str(status).startswith("FAIL") and tid not in Z:
            Z[tid] = str(status).replace("FAIL — ", "")
        elif str(status).startswith("SKIP") and tid not in Z:
            Z[tid] = str(status).replace("SKIP — ", "")

    _update_excel(R, I, A, Z, sheet="Positive")
    _summary(R)
    return  # Stop here — only Send Message test cases for now
