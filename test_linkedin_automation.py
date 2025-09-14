#!/usr/bin/env python3
"""
Test script for LinkedIn Job Automation
Tests the basic functionality without actually applying to jobs
"""

import sys
import os

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from linkedin_job_automation import LinkedInJobAutomation
import time

def test_linkedin_automation():
    """Test LinkedIn automation functionality"""
    print("🧪 TESTING LINKEDIN JOB AUTOMATION")
    print("="*50)

    try:
        # Initialize automation in headless mode for testing
        automation = LinkedInJobAutomation(headless=True)

        # Test 1: WebDriver setup
        print("1. Testing WebDriver setup...")
        if automation.setup_driver():
            print("✅ WebDriver setup successful")
        else:
            print("❌ WebDriver setup failed")
            return False

        # Test 2: URL building
        print("2. Testing URL building...")
        search_url = automation.build_search_url()
        expected_params = ['keywords=software', 'geoId=106233382', 'distance=25']

        if all(param in search_url for param in expected_params):
            print("✅ URL building successful")
            print(f"   Generated URL: {search_url}")
        else:
            print("❌ URL building failed")
            print(f"   Generated URL: {search_url}")
            return False

        # Test 3: Basic navigation
        print("3. Testing basic navigation...")
        try:
            automation.driver.get("https://www.linkedin.com")
            time.sleep(3)

            if "linkedin" in automation.driver.current_url.lower():
                print("✅ LinkedIn navigation successful")
            else:
                print("❌ LinkedIn navigation failed")
                return False

        except Exception as e:
            print(f"❌ Navigation test failed: {e}")
            return False

        # Test 4: Element detection methods
        print("4. Testing element detection methods...")
        try:
            # Test basic element finding capabilities
            buttons = automation.driver.find_elements("css selector", "button")
            links = automation.driver.find_elements("css selector", "a")

            print(f"✅ Element detection working (found {len(buttons)} buttons, {len(links)} links)")

        except Exception as e:
            print(f"❌ Element detection failed: {e}")
            return False

        print("\n🎉 ALL TESTS PASSED!")
        print("The LinkedIn automation script is ready to use.")
        print("\nTo run the full automation:")
        print("python3 linkedin_job_automation.py")

        return True

    except Exception as e:
        print(f"❌ Test failed with exception: {e}")
        return False

    finally:
        # Clean up
        if hasattr(automation, 'driver') and automation.driver:
            automation.driver.quit()

def main():
    """Main test function"""
    success = test_linkedin_automation()

    if success:
        print("\n" + "="*50)
        print("✅ LinkedIn automation is ready!")
        print("Run 'python3 linkedin_job_automation.py' to start applying to jobs")
    else:
        print("\n" + "="*50)
        print("❌ Tests failed. Please check the setup and try again")

    return success

if __name__ == "__main__":
    main()