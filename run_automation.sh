#!/bin/bash

echo "Jobright Apply with Autofill Automation Setup"
echo "============================================="

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Install requirements
echo "Installing requirements..."
pip install -r requirements.txt

# Make scripts executable
chmod +x jobright_autofill_automation.py
chmod +x jobright_autofill_enhanced.py

echo ""
echo "Setup complete! Choose an option:"
echo "1. Run basic automation (jobright_autofill_automation.py)"
echo "2. Run enhanced automation (jobright_autofill_enhanced.py)"
echo "3. Exit"
echo ""

read -p "Enter your choice (1-3): " choice

case $choice in
    1)
        echo "Running basic automation..."
        python jobright_autofill_automation.py
        ;;
    2)
        echo "Running enhanced automation..."
        python jobright_autofill_enhanced.py
        ;;
    3)
        echo "Exiting..."
        exit 0
        ;;
    *)
        echo "Invalid choice. Exiting..."
        exit 1
        ;;
esac
