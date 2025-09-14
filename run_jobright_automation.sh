#!/bin/bash

echo "🚀 JobRight.ai Automation Launcher"
echo "=================================="
echo ""

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "❌ Virtual environment not found. Please run setup first."
    exit 1
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Check if required packages are installed
echo "📦 Checking dependencies..."
python -c "import selenium, webdriver_manager" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "❌ Missing dependencies. Installing..."
    pip install -r requirements.txt
fi

echo ""
echo "Choose an option:"
echo "1. Test automation (find buttons, don't apply)"
echo "2. Run full automation (find and apply to all jobs)"
echo "3. Run enhanced automation (with Google SSO bypass)"
echo ""

read -p "Enter your choice (1-3): " choice

case $choice in
    1)
        echo "🧪 Running test automation..."
        python test_jobright_automation.py
        ;;
    2)
        echo "🎯 Running full automation..."
        python jobright_complete_automation.py
        ;;
    3)
        echo "🔐 Running Google SSO bypass automation..."
        python jobright_google_sso_bypass.py
        ;;
    *)
        echo "❌ Invalid choice. Exiting."
        exit 1
        ;;
esac

echo ""
echo "✅ Automation completed!"
