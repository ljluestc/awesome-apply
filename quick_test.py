#!/usr/bin/env python3
"""
Quick test to validate the automation works
"""

import sys
import os
sys.path.append('/home/calelin/awesome-apply/venv/lib/python3.13/site-packages')

from jobright_fixed_automation import JobRightFixedAutomation

def quick_test():
    print("🔧 Quick Test - Apply Button Detection")
    print("="*50)

    automation = JobRightFixedAutomation(headless=False)

    try:
        # Setup
        if not automation.setup_driver():
            print("❌ WebDriver setup failed")
            return

        # Auth
        if not automation.handle_authentication():
            print("❌ Authentication failed")
            return

        # Navigate
        if not automation.navigate_to_jobs_page():
            print("❌ Navigation failed")
            return

        # Load content
        automation.scroll_and_load_all_content()

        # Find buttons
        buttons = automation.find_all_apply_buttons_comprehensive()

        if buttons:
            print(f"✅ SUCCESS: Found {len(buttons)} apply buttons!")

            # Show first few
            print("\nFirst 5 buttons found:")
            for i, btn in enumerate(buttons[:5]):
                print(f"{i+1}. {btn['text'][:60]}...")

            # Test clicking first button
            if len(buttons) > 0:
                print(f"\n🧪 Testing click on first button...")
                result = automation.click_apply_button_safe(buttons[0])
                if result['success']:
                    print(f"✅ Click test successful: {result.get('action')}")
                else:
                    print(f"❌ Click test failed: {result.get('error')}")
        else:
            print("❌ No buttons found")

    except Exception as e:
        print(f"❌ Test failed: {e}")

    finally:
        if automation.driver:
            input("Press Enter to close...")
            automation.driver.quit()

if __name__ == "__main__":
    quick_test()