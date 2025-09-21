#!/usr/bin/env python3
"""
JobRight.ai Clone Launcher
Complete job search and auto-application system
"""

import sys
import os
import subprocess
import webbrowser
import time
import threading
from pathlib import Path

def check_dependencies():
    """Check if required dependencies are installed"""
    print("🔍 Checking dependencies...")

    try:
        import selenium
        import flask
        import requests
        import sqlite3
        from bs4 import BeautifulSoup
        print("✅ All Python dependencies found")
    except ImportError as e:
        print(f"❌ Missing dependency: {e}")
        print("📦 Installing dependencies...")
        subprocess.run([sys.executable, "-m", "pip", "install", "-r", "requirements_jobright_clone.txt"])

def check_chromedriver():
    """Check if ChromeDriver is available"""
    print("🔍 Checking ChromeDriver...")

    try:
        from selenium import webdriver
        from selenium.webdriver.chrome.options import Options

        options = Options()
        options.add_argument("--headless")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")

        driver = webdriver.Chrome(options=options)
        driver.quit()
        print("✅ ChromeDriver is working")
        return True
    except Exception as e:
        print(f"❌ ChromeDriver issue: {e}")
        print("📥 Installing ChromeDriver...")

        try:
            from webdriver_manager.chrome import ChromeDriverManager
            ChromeDriverManager().install()
            print("✅ ChromeDriver installed successfully")
            return True
        except Exception as install_error:
            print(f"❌ Failed to install ChromeDriver: {install_error}")
            print("💡 Please install ChromeDriver manually from https://chromedriver.chromium.org/")
            return False

def setup_database():
    """Initialize the database"""
    print("🗄️ Setting up database...")

    try:
        from jobright_clone_backend import JobDatabase
        db = JobDatabase()
        print("✅ Database initialized successfully")
        return True
    except Exception as e:
        print(f"❌ Database setup failed: {e}")
        return False

def start_backend():
    """Start the Flask backend server"""
    print("🚀 Starting backend server...")

    def run_server():
        try:
            from jobright_clone_backend import app
            app.run(debug=False, host='0.0.0.0', port=5000, use_reloader=False)
        except Exception as e:
            print(f"❌ Backend server error: {e}")

    server_thread = threading.Thread(target=run_server, daemon=True)
    server_thread.start()

    # Wait for server to start
    time.sleep(3)

    # Check if server is running
    try:
        import requests
        response = requests.get("http://localhost:5000", timeout=5)
        print("✅ Backend server is running")
        return True
    except:
        print("❌ Backend server failed to start")
        return False

def open_browser():
    """Open the web application in browser"""
    print("🌐 Opening web application...")

    try:
        webbrowser.open("http://localhost:5000")
        print("✅ Application opened in browser")
        return True
    except Exception as e:
        print(f"❌ Failed to open browser: {e}")
        print("💡 Please manually navigate to http://localhost:5000")
        return False

def print_banner():
    """Print application banner"""
    banner = """
╔══════════════════════════════════════════════════════════════════════════════╗
║                           🤖 JobRight.ai Clone                              ║
║                     AI-Powered Job Search & Auto-Apply                      ║
╠══════════════════════════════════════════════════════════════════════════════╣
║                                                                              ║
║  Features:                                                                   ║
║  ✅ LinkedIn Job Scraping with Advanced Filters                             ║
║  ✅ Intelligent Auto-Application System                                     ║
║  ✅ Form Pattern Recognition & Analysis                                     ║
║  ✅ Real-time Application Analytics                                         ║
║  ✅ Beautiful UI Matching JobRight.ai Design                               ║
║                                                                              ║
║  Supported Platforms:                                                       ║
║  • LinkedIn Easy Apply                                                      ║
║  • Greenhouse                                                               ║
║  • Workday                                                                  ║
║  • Generic Application Forms                                                ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝
    """
    print(banner)

def print_usage_instructions():
    """Print usage instructions"""
    instructions = """
🎯 Getting Started:

1. 📋 Configure Your Profile:
   - Edit config.py to set your personal information
   - Update resume path and cover letter template
   - Set your preferred job criteria

2. 🔍 Search for Jobs:
   - Enter job keywords (e.g., "Software Engineer")
   - Specify location or select "Remote"
   - Set experience level and job type filters
   - Click "Search Jobs"

3. 🤖 Auto-Apply:
   - Review search results
   - Click "Auto Apply" on individual jobs
   - Or use "Auto-Apply All" for bulk applications
   - Monitor progress in real-time

4. 📊 Track Progress:
   - View application analytics
   - Monitor success rates
   - Analyze form patterns
   - Export results

⚠️  Important Notes:
   • Always review job applications before submitting
   • Customize your profile in config.py for better results
   • Use responsibly and respect platform terms of service
   • Monitor application limits to avoid rate limiting

🌐 Access the application at: http://localhost:5000
📝 Logs are saved to: jobright_clone.log
🗄️ Database: jobright_clone.db

Press Ctrl+C to stop the application.
    """
    print(instructions)

def main():
    """Main launcher function"""
    print_banner()

    # Check if we're in the right directory
    if not Path("jobright_clone_backend.py").exists():
        print("❌ Please run this script from the awesome-apply directory")
        sys.exit(1)

    # Setup steps
    steps = [
        ("Checking Dependencies", check_dependencies),
        ("Checking ChromeDriver", check_chromedriver),
        ("Setting Up Database", setup_database),
        ("Starting Backend Server", start_backend),
        ("Opening Browser", open_browser)
    ]

    print("🔧 Starting JobRight.ai Clone setup...\n")

    for step_name, step_func in steps:
        print(f"📍 {step_name}...")
        success = step_func()

        if not success:
            print(f"\n❌ Setup failed at: {step_name}")
            print("💡 Please check the error messages above and try again.")
            sys.exit(1)

        print()

    print("🎉 JobRight.ai Clone is now running!")
    print_usage_instructions()

    try:
        # Keep the main thread alive
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n\n👋 Shutting down JobRight.ai Clone...")
        print("Thank you for using our job automation system!")

if __name__ == "__main__":
    main()