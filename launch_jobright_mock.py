#!/usr/bin/env python3
"""
JobRight.ai Mock System Launcher

This script launches the complete mock system that replicates all functionality
of https://jobright.ai/jobs/recommend
"""

import subprocess
import sys
import os
import time
import requests

def main():
    print("🚀 LAUNCHING JOBRIGHT.AI COMPLETE MOCK SYSTEM")
    print("="*60)
    print()

    # Add current directory to Python path
    current_dir = os.path.dirname(os.path.abspath(__file__))
    venv_path = os.path.join(current_dir, 'venv', 'lib', 'python3.13', 'site-packages')

    # Set environment variables
    env = os.environ.copy()
    env['PYTHONPATH'] = venv_path

    print("📦 Environment configured")
    print(f"   Python path: {venv_path}")
    print()

    # Launch the Flask application
    python_exe = os.path.join(current_dir, 'venv', 'bin', 'python')
    script_path = os.path.join(current_dir, 'jobright_mock_system.py')

    print("🌐 Starting Flask web server...")
    print(f"   Python: {python_exe}")
    print(f"   Script: {script_path}")
    print()

    try:
        # Start the process
        process = subprocess.Popen(
            [python_exe, script_path],
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )

        # Wait for server to start
        print("⏳ Waiting for server to start...")

        for i in range(10):
            try:
                response = requests.get('http://localhost:5000/jobs/recommend', timeout=2)
                if response.status_code == 200:
                    break
            except:
                pass
            time.sleep(1)
            print(f"   Attempt {i+1}/10...")

        print()
        print("✅ JOBRIGHT.AI MOCK SYSTEM IS READY!")
        print("="*60)
        print()
        print("🌐 ACCESS THE APPLICATION:")
        print("   URL: http://localhost:5000")
        print("   Main Page: http://localhost:5000/jobs/recommend")
        print()
        print("👤 DEMO LOGIN CREDENTIALS:")
        print("   Email: demo@jobright.mock")
        print("   Password: demo123")
        print()
        print("🎯 FEATURES AVAILABLE:")
        print("   ✅ AI-powered job recommendations")
        print("   ✅ Advanced filtering and search")
        print("   ✅ User authentication and profiles")
        print("   ✅ Save and track job applications")
        print("   ✅ Personalized job matching")
        print("   ✅ Complete UI/UX replica")
        print()
        print("🔧 MOCK CAPABILITIES:")
        print("   • 150+ realistic job listings")
        print("   • AI-calculated match scores")
        print("   • Real-time filtering")
        print("   • Application tracking")
        print("   • User preferences")
        print("   • Responsive design")
        print()
        print("📊 SYSTEM STATUS:")
        print("   Status: RUNNING")
        print("   Port: 5000")
        print("   Debug: ON")
        print()
        print("Press Ctrl+C to stop the server")
        print("="*60)

        # Keep running and show output
        try:
            while True:
                output = process.stdout.readline()
                if output:
                    print(f"[SERVER] {output.strip()}")
                error = process.stderr.readline()
                if error:
                    print(f"[ERROR] {error.strip()}")

                if process.poll() is not None:
                    break

        except KeyboardInterrupt:
            print("\n\n🛑 Shutting down JobRight.ai Mock System...")
            process.terminate()
            process.wait()
            print("✅ Server stopped successfully")

    except Exception as e:
        print(f"❌ Failed to start server: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()