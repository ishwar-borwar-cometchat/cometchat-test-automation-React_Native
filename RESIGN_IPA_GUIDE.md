# How to Re-sign the IPA Without Developer

## ✅ What You Have
- ✓ Xcode 26.4
- ✓ Apple Development certificate
- ✓ Device UDID: `00008020-0003353E3E82002E`
- ✓ Original IPA: `masterapp.ipa`

## 🎯 Simplest Method: Using Xcode

### Step 1: Extract the IPA
```bash
mkdir -p ~/Desktop/resign_app
cd ~/Desktop/resign_app
unzip "/Users/admin/Documents/Kiro/Manual Test Script/React Native/masterapp.ipa"
```

### Step 2: Create a New Xcode Project
1. Open Xcode
2. Create New Project → iOS → App
3. Product Name: `masterapp`
4. Bundle Identifier: `com.cometchat.internal.reactnative.ios`
5. Team: Select your development team (QA27GDTM42)
6. Save anywhere (e.g., Desktop)

### Step 3: Enable Automatic Signing
1. In Xcode, select the project in navigator
2. Select the target
3. Go to "Signing & Capabilities" tab
4. Check "Automatically manage signing"
5. Select your Team
6. Xcode will create a provisioning profile with your device

### Step 4: Replace App Bundle
```bash
# Find the Xcode project's derived data
DERIVED_DATA=$(ls -td ~/Library/Developer/Xcode/DerivedData/masterapp-* | head -1)

# Build the project once in Xcode (Cmd+B) to generate the app structure

# Then replace the built app with the extracted one
# (After building in Xcode, the app will be in DerivedData)
```

### Step 5: Use Sideloadly (EASIEST - RECOMMENDED)

**Download Sideloadly:**
```bash
open https://sideloadly.io/
```

**Steps:**
1. Download and install Sideloadly
2. Connect your iPhone
3. Drag `masterapp.ipa` into Sideloadly
4. Enter your Apple ID (free account works!)
5. Click "Start"
6. Sideloadly will:
   - Re-sign the IPA with your certificate
   - Add your device to provisioning profile
   - Install directly to your device

**This is the EASIEST method!** ✨

---

## 🔧 Alternative: Using AltStore

**Download AltStore:**
```bash
open https://altstore.io/
```

**Steps:**
1. Install AltStore on your Mac
2. Install AltStore app on your iPhone (via WiFi)
3. Open AltStore on iPhone
4. Tap "+" and select `masterapp.ipa`
5. AltStore will re-sign and install automatically

---

## 🛠️ Alternative: Manual Re-signing (Advanced)

If you want to do it manually:

```bash
# 1. Extract IPA
mkdir resign_temp
unzip masterapp.ipa -d resign_temp

# 2. Remove old signature
rm -rf resign_temp/Payload/masterapp.app/_CodeSignature
rm -f resign_temp/Payload/masterapp.app/embedded.mobileprovision

# 3. Get your certificate identity
security find-identity -v -p codesigning

# 4. Create entitlements.plist
cat > entitlements.plist <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>get-task-allow</key>
    <true/>
</dict>
</plist>
EOF

# 5. Sign frameworks
find resign_temp/Payload/masterapp.app/Frameworks -name "*.dylib" -o -name "*.framework" | while read f; do
    codesign -f -s "Apple Development: 917057818389 (QA27GDTM42)" "$f"
done

# 6. Sign the app
codesign -f -s "Apple Development: 917057818389 (QA27GDTM42)" \
    --entitlements entitlements.plist \
    resign_temp/Payload/masterapp.app

# 7. Repackage
cd resign_temp
zip -qr ../masterapp_resigned.ipa Payload
cd ..

# 8. Install
xcrun devicectl device install app --device 23DBD81D-9E92-50AA-865C-E20D9766A7A5 masterapp_resigned.ipa
```

**Note:** Manual signing often fails due to provisioning profile issues. Use Sideloadly or AltStore instead.

---

## 🎯 RECOMMENDED: Use Sideloadly

**Why Sideloadly?**
- ✓ Free
- ✓ Handles all signing complexity
- ✓ Works with free Apple ID
- ✓ Automatic provisioning profile creation
- ✓ Direct installation to device
- ✓ No command line needed

**Download:** https://sideloadly.io/

This is the easiest and most reliable method! 🚀
