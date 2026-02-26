#!/bin/bash
# QUICK TROUBLESHOOTING FOR COMFYUI DOWNLOAD ISSUES
# Run this to diagnose and fix the download problem

cd /home/stephen/Documents/www/songbird

echo "🔍 Diagnosing ComfyUI Download Issues..."
echo ""

# Step 1: Run diagnostic
echo "STEP 1: Running comprehensive diagnostic..."
echo "Command: python diagnose_download.py"
source venv/bin/activate
python diagnose_download.py

echo ""
echo "═════════════════════════════════════════════════════════════════"
echo "STEP 2: Testing with current configuration..."
echo "═════════════════════════════════════════════════════════════════"
echo ""
echo "Running: python app.py --suggest --verbose"
echo "(This will attempt actual generation)"
echo "Press Ctrl+C to stop if it takes too long"
echo ""
echo "⏳ Waiting 5 seconds before starting..."
sleep 5

# Run app with verbose logging to output and capture
python app.py --suggest --verbose 2>&1 | tee /tmp/comfyui_download_test.log

echo ""
echo "═════════════════════════════════════════════════════════════════"
echo "STEP 3: Analyzing results..."
echo "═════════════════════════════════════════════════════════════════"
echo ""

# Check the logs for key indicators
if grep -q "Using fallback download" /tmp/comfyui_download_test.log; then
    echo "✓ Fallback mechanism was activated"
fi

if grep -q "Successfully downloaded via fallback" /tmp/comfyui_download_test.log; then
    echo "✓ Audio file was downloaded via fallback!"
    ls -lh output/*.mp3 output/*.wav 2>/dev/null | tail -1
elif grep -q "Successfully saved and verified" /tmp/comfyui_download_test.log; then
    echo "✓ Audio file was downloaded!"
    ls -lh output/*.mp3 output/*.wav 2>/dev/null | tail -1
else
    echo "✗ Download may have failed"
    echo ""
    echo "TROUBLESHOOTING:"
    echo "1. Try disabling SSL verification:"
    echo "   Edit .env and change: COMFYUI_VERIFY_SSL=false"
    echo "   Then run: python app.py --suggest --verbose"
    echo ""
    echo "2. Check the error messages above"
    echo ""
fi

echo ""
echo "═════════════════════════════════════════════════════════════════"
echo "USEFUL COMMANDS:"
echo "═════════════════════════════════════════════════════════════════"
echo ""
echo "# See all error messages:"
echo "grep -i error /tmp/comfyui_download_test.log"
echo ""
echo "# See all download-related messages:"
echo "grep -i 'download\|history\|fallback' /tmp/comfyui_download_test.log"
echo ""
echo "# Check if files were created:"
echo "ls -lh output/"
echo ""
echo "# Run diagnostic again:"
echo "python diagnose_download.py"
echo ""
echo "# Test with SSL verification disabled:"
echo "COMFYUI_VERIFY_SSL=false python app.py --suggest --verbose"
echo ""
