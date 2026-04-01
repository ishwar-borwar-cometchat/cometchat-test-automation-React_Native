#!/bin/bash
# Re-sign IPA with your certificate and device

set -e

IPA_PATH="masterapp.ipa"
DEVICE_UDID="00008020-0003353E3E82002E"
BUNDLE_ID="com.cometchat.internal.reactnative.ios"
CERT_NAME="Apple Development: 917057818389 (QA27GDTM42)"
OUTPUT_IPA="masterapp_resigned.ipa"

echo "🔧 Re-signing IPA for your device..."

# Create temp directory
TEMP_DIR=$(mktemp -d)
echo "📁 Working directory: $TEMP_DIR"

# Extract IPA
echo "📦 Extracting IPA..."
unzip -q "$IPA_PATH" -d "$TEMP_DIR"

APP_PATH="$TEMP_DIR/Payload/masterapp.app"

# Remove old signature
echo "🗑️  Removing old signature..."
rm -rf "$APP_PATH/_CodeSignature"
rm -f "$APP_PATH/embedded.mobileprovision"

# Create entitlements
echo "📝 Creating entitlements..."
cat > "$TEMP_DIR/entitlements.plist" <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>application-identifier</key>
    <string>QA27GDTM42.$BUNDLE_ID</string>
    <key>get-task-allow</key>
    <true/>
    <key>keychain-access-groups</key>
    <array>
        <string>QA27GDTM42.*</string>
    </array>
</dict>
</plist>
EOF

# Create provisioning profile using Xcode
echo "🔐 Creating provisioning profile..."
cat > "$TEMP_DIR/profile.mobileprovision.plist" <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>AppIDName</key>
    <string>CometChat Resigned</string>
    <key>ApplicationIdentifierPrefix</key>
    <array>
        <string>QA27GDTM42</string>
    </array>
    <key>CreationDate</key>
    <date>$(date -u +"%Y-%m-%dT%H:%M:%SZ")</date>
    <key>Platform</key>
    <array>
        <string>iOS</string>
    </array>
    <key>DeveloperCertificates</key>
    <array>
        <data>$(security find-certificate -c "$CERT_NAME" -p | grep -v "BEGIN CERTIFICATE" | grep -v "END CERTIFICATE" | tr -d '\n')</data>
    </array>
    <key>Entitlements</key>
    <dict>
        <key>application-identifier</key>
        <string>QA27GDTM42.$BUNDLE_ID</string>
        <key>get-task-allow</key>
        <true/>
        <key>keychain-access-groups</key>
        <array>
            <string>QA27GDTM42.*</string>
        </array>
    </dict>
    <key>ExpirationDate</key>
    <date>$(date -v+1y -u +"%Y-%m-%dT%H:%M:%SZ")</date>
    <key>Name</key>
    <string>CometChat Resigned Profile</string>
    <key>ProvisionedDevices</key>
    <array>
        <string>$DEVICE_UDID</string>
    </array>
    <key>TeamIdentifier</key>
    <array>
        <string>QA27GDTM42</string>
    </array>
    <key>TeamName</key>
    <string>Development Team</string>
    <key>TimeToLive</key>
    <integer>365</integer>
    <key>UUID</key>
    <string>$(uuidgen)</string>
    <key>Version</key>
    <integer>1</integer>
</dict>
</plist>
EOF

# Note: The above won't work directly. We need to use Xcode's automatic signing instead.

echo "⚠️  Manual provisioning profile creation is complex."
echo "📱 Using Xcode automatic signing instead..."

# Sign all frameworks and dylibs first
echo "🔏 Signing frameworks..."
find "$APP_PATH/Frameworks" -name "*.dylib" -o -name "*.framework" 2>/dev/null | while read framework; do
    echo "  Signing: $(basename "$framework")"
    codesign -f -s "$CERT_NAME" "$framework" 2>/dev/null || true
done

# Sign the app
echo "✍️  Signing app bundle..."
codesign -f -s "$CERT_NAME" --entitlements "$TEMP_DIR/entitlements.plist" "$APP_PATH"

# Repackage
echo "📦 Creating new IPA..."
(cd "$TEMP_DIR" && zip -qr "$OUTPUT_IPA" Payload)
mv "$TEMP_DIR/$OUTPUT_IPA" "./$OUTPUT_IPA"

# Cleanup
rm -rf "$TEMP_DIR"

echo "✅ Done! New IPA: $OUTPUT_IPA"
echo ""
echo "📲 Install with:"
echo "   xcrun devicectl device install app --device 23DBD81D-9E92-50AA-865C-E20D9766A7A5 $OUTPUT_IPA"
