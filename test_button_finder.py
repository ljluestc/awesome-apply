#!/usr/bin/env python3
"""
Quick test script to find and list all Apply Now buttons
"""

import sys
import os
sys.path.append('/home/calelin/awesome-apply/venv/lib/python3.13/site-packages')

from jobright_complete_automation import JobRightCompleteAutomation
import json

def test_button_finder():
    """Test just the button finding functionality"""
    print("🔍 Testing Apply Now Button Finder...")
    print("="*60)

    # Create automation instance
    automation = JobRightCompleteAutomation(headless=False, auto_apply=False)

    try:
        # Setup driver
        if not automation.setup_driver():
            print("❌ Failed to setup WebDriver")
            return

        # Navigate to JobRight
        if not automation.navigate_to_jobright():
            print("❌ Failed to navigate to JobRight")
            return

        # Find buttons
        buttons = automation.find_all_apply_buttons()

        if buttons:
            print(f"\n✅ SUCCESS: Found {len(buttons)} Apply Now buttons!")

            # Display buttons
            automation.display_found_buttons(buttons)

            # Save to JSON for inspection
            with open('found_buttons.json', 'w', encoding='utf-8') as f:
                json.dump(buttons, f, indent=2, default=str)
            print(f"\n💾 Button details saved to found_buttons.json")

        else:
            print("❌ No Apply Now buttons found")

            # Save debug info
            with open('debug_page_source.html', 'w', encoding='utf-8') as f:
                f.write(automation.driver.page_source)
            print("🐛 Debug: Page source saved to debug_page_source.html")

            try:
                automation.driver.save_screenshot('debug_screenshot.png')
                print("🐛 Debug: Screenshot saved to debug_screenshot.png")
            except:
                pass

    finally:
        if automation.driver:
            input("Press Enter to close browser...")
            automation.driver.quit()

if __name__ == "__main__":
    test_button_finder()