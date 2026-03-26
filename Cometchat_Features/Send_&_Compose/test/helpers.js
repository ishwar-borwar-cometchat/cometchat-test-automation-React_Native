/**
 * Shared helpers for CometChat Send Message & Composer tests.
 */
const { execSync } = require('child_process');
const XLSX = require('xlsx');
const path = require('path');

const PKG = 'com.cometchat.sampleapp.reactnative.android';
const EXCEL_PATH = path.resolve(__dirname, '../SM_SLC_RMF_Test_Cases.xlsx');

// Auto-detect adb
const ADB = (() => {
    try { return execSync('which adb').toString().trim(); } catch {}
    const home = process.env.ANDROID_HOME || process.env.ANDROID_SDK_ROOT || '';
    return path.join(home, 'platform-tools', 'adb');
})();

// Auto-detect device
const DEVICE = (() => {
    try {
        const out = execSync(`${ADB} devices`).toString();
        const lines = out.trim().split('\n').slice(1);
        for (const line of lines) {
            const parts = line.trim().split('\t');
            if (parts.length === 2 && parts[1] === 'device') return parts[0];
        }
    } catch {}
    return '';
})();

function adb(args) {
    try {
        return execSync(`${ADB} -s ${DEVICE} ${args}`, { timeout: 10000 }).toString().trim();
    } catch { return ''; }
}

function adbTap(x, y) { adb(`shell input tap ${x} ${y}`); }
function adbBack() { adb('shell input keyevent 4'); }
function adbEnter() { adb('shell input keyevent 66'); }

async function sleep(ms) { return new Promise(r => setTimeout(r, ms)); }

async function loginIfNeeded(driver) {
    try {
        const aj = await driver.$('~Andrew Joseph');
        if (await aj.isDisplayed()) {
            await aj.click();
            await sleep(500);
            const cont = await driver.$('~Continue');
            await cont.click();
            await sleep(3000);
            // Dismiss dialogs
            for (let i = 0; i < 5; i++) {
                const focus = adb('shell dumpsys window');
                const focusLine = focus.split('\n').find(l => l.includes('mCurrentFocus')) || '';
                if (['GrantPermission', 'telecom', 'CallingAccount'].some(x => focusLine.includes(x)) && !focusLine.includes(PKG)) {
                    adbBack(); await sleep(1000); continue;
                }
                try {
                    const btn = await driver.$('//*[@text="OK" or @text="Allow" or @text="ALLOW" or @text="While using the app"]');
                    if (await btn.isDisplayed()) { await btn.click(); await sleep(1000); }
                    else break;
                } catch { break; }
            }
            console.log('Logged in as Andrew Joseph.');
        }
    } catch {
        console.log('Already logged in — checking screen state...');
        for (let i = 0; i < 5; i++) {
            const focus = adb('shell dumpsys window');
            const focusLine = focus.split('\n').find(l => l.includes('mCurrentFocus')) || '';
            if (['GrantPermission', 'telecom', 'CallingAccount'].some(x => focusLine.includes(x)) && !focusLine.includes(PKG)) {
                adbBack(); await sleep(1000); continue;
            }
            try {
                const chats = await driver.$$('//*[@text="Chats"]');
                const composer = await driver.$$('//android.widget.EditText[contains(@hint,"Type") or contains(@text,"Type your message")]');
                if (chats.length || composer.length) break;
            } catch {}
            try { await driver.back(); await sleep(1000); } catch {}
        }
    }
    // Wait for chat list
    for (let i = 0; i < 10; i++) {
        await sleep(2000);
        try {
            const chats = await driver.$$('//*[@text="Chats" or contains(@content-desc,"Ishwar")]');
            const composer = await driver.$$('//android.widget.EditText[contains(@hint,"Type") or contains(@text,"Type your message")]');
            if (chats.length || composer.length) break;
        } catch {}
    }
}

async function openChat(driver, userName = 'Ishwar Borwar') {
    // Already in chat?
    try {
        const composer = await driver.$('//android.widget.EditText[contains(@hint,"Type") or contains(@text,"Type your message")]');
        if (await composer.isDisplayed()) { console.log('Already in chat.'); return true; }
    } catch {}
    // Dismiss search if active
    try {
        const clear = await driver.$$('~Clear search');
        if (clear.length) { await clear[0].click(); await sleep(500); }
    } catch {}
    // Find conversation ViewGroup
    try {
        const user = await driver.$(`//android.view.ViewGroup[contains(@content-desc,"${userName}") and @clickable="true"]`);
        await user.waitForDisplayed({ timeout: 5000 });
        await user.click();
        await sleep(1000);
        return true;
    } catch {}
    // Scroll fallback
    try {
        const sz = await driver.getWindowSize();
        for (let i = 0; i < 5; i++) {
            const els = await driver.$$(`//android.view.ViewGroup[contains(@content-desc,"${userName}") and @clickable="true"]`);
            if (els.length) { await els[0].click(); await sleep(1000); return true; }
            await driver.touchAction([
                { action: 'press', x: sz.width / 2, y: sz.height * 3 / 4 },
                { action: 'wait', ms: 800 },
                { action: 'moveTo', x: sz.width / 2, y: sz.height / 2 },
                { action: 'release' },
            ]);
            await sleep(500);
        }
    } catch {}
    console.log(`Could not find ${userName}`);
    return false;
}

async function ensureInChat(driver, userName = 'Ishwar Borwar') {
    try {
        const composer = await driver.$('//android.widget.EditText[contains(@hint,"Type") or contains(@text,"Type your message")]');
        if (await composer.isDisplayed()) return true;
    } catch {}
    console.log(`  [Recovery] Not in chat, navigating to ${userName}...`);
    try {
        const state = await driver.queryAppState(PKG);
        if (state < 3) { await driver.activateApp(PKG); await sleep(2000); await loginIfNeeded(driver); }
        await goToChatList(driver);
        await sleep(500);
        return await openChat(driver, userName);
    } catch (e) {
        console.log(`  [Recovery] Failed: ${String(e).slice(0, 60)}`);
        return false;
    }
}

async function goToChatList(driver) {
    for (let i = 0; i < 8; i++) {
        try {
            const clear = await driver.$$('~Clear search');
            if (clear.length) { await clear[0].click(); await sleep(500); continue; }
        } catch {}
        try {
            const ishwar = await driver.$$('//android.view.ViewGroup[contains(@content-desc,"Ishwar") and @clickable="true"]');
            if (ishwar.length) { console.log('At chat list.'); return true; }
        } catch {}
        try {
            const state = await driver.queryAppState(PKG);
            if (state < 4) { await driver.activateApp(PKG); await sleep(2000); return false; }
        } catch {}
        try { await driver.back(); await sleep(500); } catch {}
    }
    return false;
}

async function getComposer(driver) {
    return driver.$('//android.widget.EditText[contains(@hint,"Type") or contains(@text,"Type your message")]');
}

async function sendMessage(driver, text) {
    const inp = await getComposer(driver);
    await inp.click(); await inp.clearValue(); await inp.setValue(text);
    await sleep(300);
    try {
        const send = await driver.$('//*[@resource-id="send-button"]');
        await send.waitForClickable({ timeout: 5000 });
        await send.click();
        await sleep(500);
        return true;
    } catch { return false; }
}

async function longPress(driver, element, duration = 1500) {
    await driver.touchAction([
        { action: 'press', element },
        { action: 'wait', ms: duration },
        { action: 'release' },
    ]);
}

async function findMenuOption(driver, optionText, timeout = 5000) {
    try {
        const opt = await driver.$(`//*[contains(@text,"${optionText}") or contains(@content-desc,"${optionText}")]`);
        await opt.waitForDisplayed({ timeout });
        return opt;
    } catch { return null; }
}

async function dismiss(driver) {
    try {
        const sz = await driver.getWindowSize();
        await driver.touchAction([{ action: 'tap', x: sz.width / 2, y: sz.height / 4 }]);
        await sleep(500);
    } catch {
        try { await driver.back(); await sleep(300); } catch {}
    }
}

// Results tracking
const results = {};
const inputs = {};
const actuals = {};
const reasons = {};

function record(tid, status, actual, input = 'N/A', reason = '') {
    results[tid] = status;
    actuals[tid] = actual;
    inputs[tid] = input;
    if (reason) reasons[tid] = reason;
    const short = String(status).slice(0, 60);
    console.log(`${tid}: ${short}`);
}

function updateExcel() {
    const wb = XLSX.readFile(EXCEL_PATH);
    const ws = wb.Sheets['Positive'];
    const range = XLSX.utils.decode_range(ws['!ref']);

    for (let row = range.s.r + 1; row <= range.e.r; row++) {
        const cellA = ws[XLSX.utils.encode_cell({ r: row, c: 0 })];
        if (!cellA || !String(cellA.v).startsWith('MSG_')) continue;
        const tid = cellA.v;
        if (!(tid in results)) continue;

        // Col H (7) = Actual Result
        ws[XLSX.utils.encode_cell({ r: row, c: 7 })] = { v: actuals[tid] || '', t: 's' };
        // Col J (9) = Status
        ws[XLSX.utils.encode_cell({ r: row, c: 9 })] = { v: results[tid], t: 's' };
        // Col K (10) = Input_Data
        ws[XLSX.utils.encode_cell({ r: row, c: 10 })] = { v: inputs[tid] || 'N/A', t: 's' };
        // Col L (11) = Reason
        ws[XLSX.utils.encode_cell({ r: row, c: 11 })] = { v: reasons[tid] || '', t: 's' };
    }

    XLSX.writeFile(wb, EXCEL_PATH);
    const p = Object.values(results).filter(v => String(v).startsWith('PASS')).length;
    const f = Object.values(results).filter(v => String(v).startsWith('FAIL')).length;
    const s = Object.values(results).filter(v => String(v).startsWith('SKIP')).length;
    console.log(`\nExcel updated: ${Object.keys(results).length} results | PASS: ${p} | FAIL: ${f} | SKIP: ${s}`);
}

module.exports = {
    PKG, ADB, DEVICE, EXCEL_PATH,
    adb, adbTap, adbBack, adbEnter, sleep,
    loginIfNeeded, openChat, ensureInChat, goToChatList,
    getComposer, sendMessage, longPress, findMenuOption, dismiss,
    record, updateExcel, results, inputs, actuals, reasons,
};
