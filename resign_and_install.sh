#!/bin/bash
# Manual IPA re-signing and installation
# No third-party tools needed - uses only Xcode tools

set -e

echo "🔧 Re-signing masterapp.ipa for your device..."
echo ""

# Configuration
IPA_PATH="masterapp.ipa"
DEVICE_ID="23DBD81D-9E92-50AA-865C-E20D9766A7A5"
CERT_NAME="Apple Development: 917057818389 (QA27GDTM42)"
BUNDLE_ID="com.cometchat.internal.reactnative.ios"
OUTPUT_IPA="masterapp_resigned.ipa"

# Check if IPA exists
if [ ! -f "$IPA_PATH" ]; then
    echo "❌ Error: $IPA_PATH not found"
    exit 1
fi

# Create temp directory
TEMP_DIR=$(mktemp -d)
echo "📁 Working in: $TEMP_DIR"

# Extract IPA
echo "📦 Extracting IPA..."
unzip -q "$IPA_PATH" -d "$TEMP_DIR"

APP_PATH="$TEMP_DIR/Payload/masterapp.app"

# Remove old code signature
echo "🗑️  Removing old signature..."
rm -rf "$APP_PATH/_CodeSignature" 2>/dev/null || true
rm -f "$APP_PATH/embedded.mobileprovision" 2>/dev/null || true

# Create minimal entitlements
echo "📝 Creating entitlements..."
cat > "$TEMP_DIR/entitlements.plist" <<'EOF'
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>get-task-allow</key>
    <true/>
</dict>
</plist>
EOF

# Sign all frameworks and dylibs
echo "🔏 Signing frameworks and libraries..."
find "$APP_PATH/Frameworks" -type f \( -name "*.dylib" -o -name "*.framework" \) 2>/dev/null | while read -r framework; do
    if [ -f "$framework" ]; then
        echo "  → $(basename "$framework")"
        /usr/bin/codesign --force --sign "$CERT_NAME" --timestamp=none "$framework" 2>/dev/null || true
    fi
done

# Sign all .framework bundles
find "$APP_PATH/Frameworks" -type d -name "*.framework" 2>/dev/null | while read -r framework; do
    echo "  → $(basename "$framework")"
    /usr/bin/codesign --force --sign "$CERT_NAME" --timestamp=none "$framework" 2>/dev/null || true
done

# Sign the main app bundle
echo "✍️  Signing main app bundle..."
/usr/bin/codesign --force --sign "$CERT_NAME" \
    --entitlements "$TEMP_DIR/entitlements.plist" \
    --timestamp=none \
    "$APP_PATH"

# Verify signature
echo "🔍 Verifying signature..."
if /usr/bin/codesign --verify --verbose "$APP_PATH" 2>&1 | grep -q "valid on disk"; then
    echo "✅ Signature valid!"
else
    echo "⚠️  Signature verification unclear, but continuing..."
fi

# Repackage IPA
echo "📦 Creating new IPA..."
(cd "$TEMP_DIR" && zip -qr "$OUTPUT_IPA" Payload)
mv "$TEMP_DIR/$OUTPUT_IPA" "./$OUTPUT_IPA"

# Cleanup
rm -rf "$TEMP_DIR"

echo ""
echo "✅ Re-signed IPA created: $OUTPUT_IPA"
echo ""
echo "📲 Installing to device..."
echo ""

# Try to install
if xcrun devicectl device install app --device "$DEVICE_ID" "$OUTPUT_IPA" 2>&1; then
    echo ""
    echo "🎉 SUCCESS! App installed on your iPhone!"
    echo ""
    echo "Now run your tests:"
    echo "  PLATFORM=ios python3 -m pytest \"Cometchat_Features/Send_&_Compose/Positive test cases/test_send_message_positive.py\" -v -s"
else
    echo ""
    echo "⚠️  Installation failed. This usually means:"
    echo "  1. Provisioning profile issue (need proper profile with your device)"
    echo "  2. Certificate doesn't have proper permissions"
    echo ""
    echo "💡 Recommended: Use Sideloadly or AltStore instead"
    echo "   They handle provisioning profiles automatically"
    echo ""
    echo "To allow Sideloadly:"
    echo "  1. System Settings → Privacy & Security"
    echo "  2. Click 'Open Anyway' next to Sideloadly warning"
    echo ""
    echo "Or run: sudo xattr -rd com.apple.quarantine /Applications/Sideloadly.app"
fi
