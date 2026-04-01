#!/bin/bash
# Install Sideloadly - the easiest way to re-sign and install IPA

echo "🎯 Installing Sideloadly - Easy IPA Re-signing Tool"
echo ""
echo "Sideloadly will:"
echo "  ✓ Re-sign the IPA with your certificate"
echo "  ✓ Add your device to provisioning profile"
echo "  ✓ Install directly to your iPhone"
echo ""

# Check if Homebrew is installed
if ! command -v brew &> /dev/null; then
    echo "📦 Installing Homebrew first..."
    /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
fi

# Install Sideloadly using Homebrew Cask
echo "📥 Downloading Sideloadly..."
brew install --cask sideloadly 2>/dev/null || {
    echo ""
    echo "⚠️  Homebrew installation not available."
    echo ""
    echo "📥 Please download manually from:"
    echo "   https://sideloadly.io/"
    echo ""
    echo "After installing Sideloadly:"
    echo "  1. Open Sideloadly"
    echo "  2. Connect your iPhone"
    echo "  3. Drag masterapp.ipa into Sideloadly"
    echo "  4. Enter your Apple ID"
    echo "  5. Click 'Start'"
    echo ""
    open "https://sideloadly.io/"
    exit 0
}

echo ""
echo "✅ Sideloadly installed!"
echo ""
echo "📱 Next steps:"
echo "  1. Open Sideloadly (check Applications folder)"
echo "  2. Connect your iPhone (already connected ✓)"
echo "  3. Drag masterapp.ipa into Sideloadly"
echo "  4. Enter your Apple ID (free account works!)"
echo "  5. Click 'Start'"
echo ""
echo "Opening Sideloadly..."
open -a Sideloadly 2>/dev/null || open /Applications/Sideloadly.app 2>/dev/null || {
    echo "Please open Sideloadly from Applications folder"
}
