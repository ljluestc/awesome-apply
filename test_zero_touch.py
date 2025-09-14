#!/usr/bin/env python3
"""
Test Zero-Touch SSO Automation
Quick test to validate the zero-touch automation works
"""

import sys
import os
sys.path.append('/home/calelin/awesome-apply/venv/lib/python3.13/site-packages')

from zero_touch_sso_automation import ZeroTouchSSoAutomation
import time

def test_zero_touch():
    print("🧪 TESTING ZERO-TOUCH SSO AUTOMATION")
    print("="*60)

    email = "jeremykalilin@gmail.com"
    automation = ZeroTouchSSoAutomation(email=email, headless=False)

    try:
        print("1. Setting up advanced driver...")
        if not automation.setup_advanced_driver():
            print("❌ Driver setup failed")
            return

        print("✅ Driver setup successful")

        print("\n2. Testing session management...")
        session_loaded = automation.load_advanced_session()
        print(f"Session loaded: {'✅ Yes' if session_loaded else '❌ No'}")

        if session_loaded:
            if automation.verify_complete_session():
                print("✅ Session is valid and working")
                print("🎉 TEST PASSED - Existing session works!")

                # Quick button test
                print("\n3. Quick button detection test...")
                buttons = automation.find_all_apply_buttons_ultimate()
                print(f"Found {len(buttons)} apply buttons")

                if buttons:
                    print("✅ Button detection working")

                    # Show first few buttons
                    for i, btn in enumerate(buttons[:3]):
                        print(f"  {i+1}. {btn['text'][:50]}...")

                else:
                    print("⚠️ No buttons found in current page")

                return True
            else:
                print("❌ Session invalid, will need fresh auth")

        print("\n3. Testing SSO flow initiation...")
        automation.driver.get("https://jobright.ai")
        time.sleep(3)

        # Test SSO detection
        if automation.smart_sso_initiation():
            print("✅ SSO initiation successful")
        else:
            print("❌ SSO initiation failed")

        print(f"\nCurrent URL: {automation.driver.current_url}")

        print("\n4. Testing Google account detection...")
        if automation.detect_existing_google_session():
            print("✅ Google account detected")
        else:
            print("❌ No Google account detected")

    except Exception as e:
        print(f"❌ Test failed with error: {e}")

    finally:
        if automation.driver:
            input("Press Enter to close browser...")
            automation.driver.quit()

if __name__ == "__main__":
    test_zero_touch()