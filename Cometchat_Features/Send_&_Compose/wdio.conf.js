const path = require('path');
const fs = require('fs');

// Auto-detect APK
const apkPath = path.resolve(__dirname, '../../React_Native_Android.apk');

exports.config = {
    runner: 'local',
    port: 4723,
    specs: ['./test/*.spec.js'],
    maxInstances: 1,
    capabilities: [{
        platformName: 'Android',
        'appium:automationName': 'UiAutomator2',
        'appium:app': apkPath,
        'appium:noReset': false,
        'appium:fullReset': false,
        'appium:newCommandTimeout': 600,
        'appium:adbExecTimeout': 60000,
        'appium:uiautomator2ServerInstallTimeout': 120000,
        'appium:uiautomator2ServerLaunchTimeout': 120000,
        'appium:uiautomator2ServerReadTimeout': 60000,
        'appium:appWaitActivity': '*',
        'appium:appWaitDuration': 30000,
        'appium:autoGrantPermissions': true,
        'appium:disableWindowAnimation': true,
        'appium:skipUnlock': true,
    }],
    services: [],
    hostname: '127.0.0.1',
    framework: 'mocha',
    reporters: ['spec'],
    mochaOpts: {
        ui: 'bdd',
        timeout: 600000,  // 10 min per test
    },
};
