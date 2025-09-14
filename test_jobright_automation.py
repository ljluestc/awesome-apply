#!/usr/bin/env python3
"""
Test script for JobRight automation
This script tests the automation without actually applying to jobs
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from jobright_google_sso_bypass import JobRightGoogleSSOBypass
import time

def test_automation():
    """Test the automation without applying"""
    print("🧪 Testing JobRight Automation (No Apply Mode)")
    print("="*60)
    
    automation = JobRightGoogleSSOBypass()
    
    try:
        # Setup driver
        print("1. Setting up Chrome with Google profile...")
        if not automation.setup_driver_with_google_profile():
            print("❌ Failed to setup Chrome")
            return False
        print("✅ Chrome setup successful")
        
        # Test Google authentication
        print("\n2. Testing Google authentication...")
        if automation.test_google_signin():
            print("✅ Google authentication working")
        else:
            print("⚠️  Google authentication test failed, but continuing...")
        
        # Navigate to JobRight
        print("\n3. Navigating to JobRight...")
        if not automation.navigate_to_jobright():
            print("❌ Failed to navigate to JobRight")
            return False
        print("✅ Successfully loaded JobRight")
        
        # Find apply buttons
        print("\n4. Searching for apply buttons...")
        apply_buttons = automation.find_apply_buttons()
        
        if not apply_buttons:
            print("❌ No apply buttons found!")
            print("Debug: Saving page source...")
            with open('/home/calelin/awesome-apply/debug_page_source_test.html', 'w', encoding='utf-8') as f:
                f.write(automation.driver.page_source)
            print("Page source saved to debug_page_source_test.html")
            return False
        
        print(f"✅ Found {len(apply_buttons)} apply buttons:")
        for i, button in enumerate(apply_buttons, 1):
            print(f"  {i}. '{button['text']}' ({button['tag']})")
        
        print(f"\n🎉 Test completed successfully!")
        print(f"Found {len(apply_buttons)} apply buttons ready for automation")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False
    
    finally:
        if automation.driver:
            input("\nPress Enter to close the browser...")
            automation.driver.quit()

if __name__ == "__main__":
    test_automation()
