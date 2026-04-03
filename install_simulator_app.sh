#!/bin/bash
# Install CometChat app on iOS Simulator
# Usage: ./install_simulator_app.sh <path_to_app>
#
# The .app file must be built for simulator (x86_64/arm64 simulator architecture)
# Get it from the developer: "Build for Simulator" in Xcode

SIMULATOR_UDID="EB083C07-4E79-428F-B2EA-DC61DF8254A5"  # iPhone 17 Pro
SIMULATOR_NAME="iPhone 17 Pro"

APP_PATH="${1:-}"

if [ -z "$APP_PATH" ]; then
    echo "Usage: ./install_simulator_app.sh <path_to_.app_file>"
    echo ""
    echo "Example: ./install_simulator_app.sh ~/Downloads/sampleapp.app"
    echo ""
    echo "The .app must be a simulator build (not a real device IPA)"
    exit 1
fi

if [ ! -e "$APP_PATH" ]; then
    echo "Error: File not found: $APP_PATH"
    exit 1
fi

echo "=== CometChat Simulator Setup ==="
echo "Simulator: $SIMULATOR_NAME ($SIMULATOR_UDID)"
echo "App: $APP_PATH"
echo ""

# Boot simulator if not already booted
echo "1. Booting simulator..."
xcrun simctl boot "$SIMULATOR_UDID" 2>/dev/null
sleep 2

# Check if booted
BOOTED=$(xcrun simctl list devices booted | grep "$SIMULATOR_UDID")
if [ -z "$BOOTED" ]; then
    echo "Error: Simulator failed to boot"
    exit 1
fi
echo "   ✓ Simulator booted"

# Install app
echo "2. Installing app..."
xcrun simctl install "$SIMULATOR_UDID" "$APP_PATH"
if [ $? -ne 0 ]; then
    echo "Error: Failed to install app. Make sure it's a simulator build."
    exit 1
fi
echo "   ✓ App installed"

# Launch app
echo "3. Launching app..."
xcrun simctl launch "$SIMULATOR_UDID" "com.cometchat.internal.reactnative.ios.565LF4C8NT" 2>/dev/null
if [ $? -ne 0 ]; then
    # Try without bundle ID suffix
    xcrun simctl launch "$SIMULATOR_UDID" "com.cometchat.internal.reactnative.ios" 2>/dev/null
fi
echo "   ✓ App launched"

# Open Simulator UI
open -a Simulator

echo ""
echo "=== Setup Complete ==="
echo "Simulator: $SIMULATOR_NAME"
echo "Appium server for simulator: http://localhost:4724"
echo "Appium server for real device: http://localhost:4723"
echo ""
echo "Next steps:"
echo "1. Login as a different user (e.g., Ishwar Borwar) on the simulator"
echo "2. Run call test scripts"
