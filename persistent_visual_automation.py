#!/usr/bin/env python3
"""
Persistent Visual Automation - Keep running until both platforms are authenticated and working
Shows actual browser windows, authentication process, and job application pages
"""

import sys
import os
sys.path.append('/home/calelin/awesome-apply/venv/lib/python3.13/site-packages')

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
import time
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class PersistentVisualAutomation:
    def __init__(self):
        self.driver = None
        self.email = "jeremykalilin@gmail.com"
        self.authenticated_platforms = {
            'jobright': False,
            'linkedin': False
        }
        self.applied_jobs = []

    def setup_visual_driver(self):
        """Setup Chrome with VISUAL interface - no headless mode"""
        chrome_options = Options()

        # CRITICAL: NO HEADLESS MODE - we want to see everything
        # chrome_options.add_argument("--headless")  # DISABLED

        # Persistent profile for sessions
        user_data_dir = "/tmp/chrome_persistent_visual_profile"
        chrome_options.add_argument(f"--user-data-dir={user_data_dir}")
        chrome_options.add_argument("--profile-directory=Default")

        # Anti-detection
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)

        # Make window large and visible
        chrome_options.add_argument("--window-size=1400,1000")
        chrome_options.add_argument("--start-maximized")

        self.driver = webdriver.Chrome(
            service=Service(ChromeDriverManager().install()),
            options=chrome_options
        )

        self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        logger.info("✅ Visual Chrome driver setup completed - browser window should be visible")

    def authenticate_jobright(self):
        """Authenticate and verify JobRight.ai access"""
        try:
            logger.info("\n🎯 AUTHENTICATING JOBRIGHT.AI...")
            logger.info("="*50)

            print("🌐 Opening JobRight.ai - you should see the browser window open...")
            self.driver.get("https://jobright.ai")
            time.sleep(5)

            current_url = self.driver.current_url
            page_title = self.driver.title

            print(f"   Current URL: {current_url}")
            print(f"   Page title: {page_title}")

            # Check if authentication is needed
            page_source = self.driver.page_source.lower()

            if any(indicator in page_source for indicator in ['sign in', 'login', 'authenticate']):
                print("🔐 JobRight authentication required...")

                # Look for Google SSO options
                google_buttons = self.driver.find_elements(By.XPATH,
                    "//button[contains(text(), 'Google')] | //a[contains(text(), 'Google')] | //*[contains(text(), 'Sign in with Google')]"
                )

                if google_buttons:
                    print("✅ Found Google SSO option - clicking...")
                    for btn in google_buttons:
                        if btn.is_displayed():
                            btn.click()
                            time.sleep(5)
                            break

                    # Handle Google account selection
                    self.handle_google_account_selection()

            # Navigate to jobs section
            print("🔍 Navigating to JobRight jobs section...")
            jobs_urls = [
                "https://jobright.ai/entry-level-jobs",
                "https://jobright.ai/jobs",
                "https://jobright.ai/jobs/recommend"
            ]

            for jobs_url in jobs_urls:
                print(f"   Trying: {jobs_url}")
                self.driver.get(jobs_url)
                time.sleep(5)

                if "job" in self.driver.current_url.lower() and "error" not in self.driver.page_source.lower():
                    print(f"✅ Successfully loaded JobRight jobs page!")
                    print(f"   URL: {self.driver.current_url}")
                    print(f"   Title: {self.driver.title}")
                    self.authenticated_platforms['jobright'] = True
                    return True

            print("⚠️ JobRight authentication may need manual intervention")
            print("   Please check the browser window and complete any required steps")

            # Wait for user to complete authentication
            input("   Press Enter after JobRight authentication is complete...")
            self.authenticated_platforms['jobright'] = True
            return True

        except Exception as e:
            logger.error(f"JobRight authentication error: {e}")
            return False

    def authenticate_linkedin(self):
        """Authenticate and verify LinkedIn access"""
        try:
            logger.info("\n🎯 AUTHENTICATING LINKEDIN...")
            logger.info("="*50)

            # LinkedIn job search URL
            linkedin_url = "https://www.linkedin.com/jobs/search-results/?distance=25&geoId=106233382&keywords=software&origin=SEMANTIC_SEARCH_HISTORY"

            print("🌐 Opening LinkedIn jobs page - you should see the browser...")
            print(f"   Target URL: {linkedin_url}")

            self.driver.get(linkedin_url)
            time.sleep(8)

            current_url = self.driver.current_url
            page_title = self.driver.title

            print(f"   Current URL: {current_url}")
            print(f"   Page title: {page_title}")

            # Check if we need to authenticate
            if any(indicator in current_url.lower() for indicator in ['login', 'signin', 'authwall']):
                print("🔐 LinkedIn authentication required...")

                # Look for email input
                email_inputs = self.driver.find_elements(By.XPATH,
                    "//input[@type='email'] | //input[@name='session_key'] | //input[@id='username']"
                )

                if email_inputs:
                    print(f"📧 Entering email: {self.email}")
                    email_input = email_inputs[0]
                    email_input.clear()
                    email_input.send_keys(self.email)
                    time.sleep(2)

                print("\n🔐 LINKEDIN AUTHENTICATION REQUIRED")
                print("="*60)
                print("Please complete LinkedIn login in the browser window:")
                print(f"1. Email should be filled: {self.email}")
                print("2. Enter your password")
                print("3. Complete any 2FA if required")
                print("4. You should reach the LinkedIn jobs page")
                print("="*60)

                # Wait for authentication to complete
                return self.wait_for_linkedin_authentication(linkedin_url)

            else:
                print("✅ LinkedIn already authenticated!")
                self.authenticated_platforms['linkedin'] = True
                return True

        except Exception as e:
            logger.error(f"LinkedIn authentication error: {e}")
            return False

    def wait_for_linkedin_authentication(self, target_url):
        """Wait for LinkedIn authentication to complete with visual feedback"""
        max_wait = 600  # 10 minutes
        start_time = time.time()

        print("⏳ Waiting for LinkedIn authentication...")
        print("   (You have up to 10 minutes to complete login)")

        while time.time() - start_time < max_wait:
            current_url = self.driver.current_url.lower()
            elapsed = int(time.time() - start_time)

            # Show progress every 30 seconds
            if elapsed % 30 == 0 and elapsed > 0:
                remaining = max_wait - elapsed
                print(f"   ⏰ Still waiting... {remaining}s remaining")
                print(f"   Current URL: {current_url}")

            # Check for success indicators
            success_indicators = [
                'linkedin.com/jobs', 'linkedin.com/feed', 'linkedin.com/in/',
                'geoId=106233382', 'keywords=software'
            ]

            if any(indicator in current_url for indicator in success_indicators):
                print("✅ LinkedIn authentication successful!")
                print(f"   Final URL: {self.driver.current_url}")
                print(f"   Page title: {self.driver.title}")
                self.authenticated_platforms['linkedin'] = True
                return True

            time.sleep(5)  # Check every 5 seconds

        print("⏰ LinkedIn authentication timeout")
        print("   Continuing anyway - you can manually complete later")
        return False

    def handle_google_account_selection(self):
        """Handle Google account selection for jeremykalilin@gmail.com"""
        try:
            print("👤 Looking for Google account selection...")
            time.sleep(3)

            # Look for account selection elements
            account_selectors = [
                f"//*[contains(text(), '{self.email}')]",
                f"//*[contains(text(), 'jeremykalilin')]",
                f"//*[contains(text(), 'Jeremy')]"
            ]

            for selector in account_selectors:
                try:
                    elements = self.driver.find_elements(By.XPATH, selector)
                    for element in elements:
                        if element.is_displayed():
                            print(f"✅ Found account: {element.text}")
                            element.click()
                            time.sleep(3)
                            return True
                except Exception:
                    continue

            print("⚠️ No specific account found - proceeding")
            return False

        except Exception:
            return False

    def test_job_applications(self):
        """Test opening job applications on both platforms"""
        try:
            logger.info("\n🎯 TESTING JOB APPLICATIONS...")
            logger.info("="*50)

            jobs_applied = 0

            # Test JobRight applications
            if self.authenticated_platforms['jobright']:
                print("\n📋 Testing JobRight job applications...")
                jobs_applied += self.test_jobright_applications()

            # Test LinkedIn applications
            if self.authenticated_platforms['linkedin']:
                print("\n📋 Testing LinkedIn job applications...")
                jobs_applied += self.test_linkedin_applications()

            return jobs_applied

        except Exception as e:
            logger.error(f"Job application testing error: {e}")
            return 0

    def test_jobright_applications(self):
        """Test JobRight job applications with visual confirmation"""
        try:
            print("🌐 Loading JobRight jobs page...")
            self.driver.get("https://jobright.ai/entry-level-jobs")
            time.sleep(5)

            print(f"   Current page: {self.driver.title}")

            # Find clickable job-related elements
            clickable_elements = self.driver.find_elements(By.XPATH,
                "//*[@href or @onclick or @role='button' or name()='button' or name()='a']"
            )

            job_elements = []
            for element in clickable_elements:
                try:
                    if element.is_displayed():
                        text = element.text.strip().lower()
                        href = element.get_attribute('href') or ''

                        if any(keyword in text or keyword in href.lower()
                               for keyword in ['job', 'apply', 'career', 'position']):
                            job_elements.append(element)
                except Exception:
                    continue

            print(f"   Found {len(job_elements)} job-related elements")

            applications = 0
            for i, element in enumerate(job_elements[:5]):  # Test first 5
                try:
                    text = element.text.strip()
                    print(f"\n   Testing element {i+1}: {text[:50]}")

                    # Get current window count
                    original_windows = len(self.driver.window_handles)

                    # Scroll to element and click
                    self.driver.execute_script("arguments[0].scrollIntoView(true);", element)
                    time.sleep(1)

                    element.click()
                    time.sleep(3)

                    # Check if new window opened
                    new_windows = len(self.driver.window_handles)
                    if new_windows > original_windows:
                        print("   ✅ New window opened - application page detected!")

                        # Switch to new window
                        self.driver.switch_to.window(self.driver.window_handles[-1])
                        print(f"   Application page: {self.driver.title}")
                        print(f"   URL: {self.driver.current_url}")

                        applications += 1

                        # Close new window and return
                        self.driver.close()
                        self.driver.switch_to.window(self.driver.window_handles[0])

                    elif self.driver.current_url != "https://jobright.ai/entry-level-jobs":
                        print("   ✅ Page navigation occurred!")
                        print(f"   New page: {self.driver.title}")
                        applications += 1

                        # Go back
                        self.driver.back()
                        time.sleep(2)

                    time.sleep(2)

                except Exception as e:
                    print(f"   ❌ Element test failed: {e}")
                    continue

            print(f"✅ JobRight applications tested: {applications} successful")
            return applications

        except Exception as e:
            logger.error(f"JobRight application testing error: {e}")
            return 0

    def test_linkedin_applications(self):
        """Test LinkedIn job applications with visual confirmation"""
        try:
            linkedin_url = "https://www.linkedin.com/jobs/search-results/?distance=25&geoId=106233382&keywords=software&origin=SEMANTIC_SEARCH_HISTORY"

            print("🌐 Loading LinkedIn jobs page...")
            self.driver.get(linkedin_url)
            time.sleep(5)

            print(f"   Current page: {self.driver.title}")

            # Look for Easy Apply buttons
            easy_apply_selectors = [
                "//button[contains(@aria-label, 'Easy Apply')]",
                "//button[contains(text(), 'Easy Apply')]",
                "//*[contains(@class, 'jobs-apply-button')]"
            ]

            easy_apply_buttons = []
            for selector in easy_apply_selectors:
                try:
                    buttons = self.driver.find_elements(By.XPATH, selector)
                    for button in buttons:
                        if button.is_displayed() and button.is_enabled():
                            easy_apply_buttons.append(button)
                except Exception:
                    continue

            print(f"   Found {len(easy_apply_buttons)} Easy Apply buttons")

            applications = 0
            for i, button in enumerate(easy_apply_buttons[:3]):  # Test first 3
                try:
                    print(f"\n   Testing Easy Apply {i+1}")

                    # Scroll to button
                    self.driver.execute_script("arguments[0].scrollIntoView(true);", button)
                    time.sleep(1)

                    button.click()
                    time.sleep(3)

                    # Check if application modal opened
                    modals = self.driver.find_elements(By.XPATH,
                        "//*[contains(@class, 'modal') or contains(@role, 'dialog')]"
                    )

                    if modals:
                        print("   ✅ Application modal opened!")
                        applications += 1

                        # Close modal
                        close_buttons = self.driver.find_elements(By.XPATH,
                            "//button[contains(@aria-label, 'Dismiss') or contains(@aria-label, 'Close')]"
                        )
                        for close_btn in close_buttons:
                            try:
                                if close_btn.is_displayed():
                                    close_btn.click()
                                    break
                            except Exception:
                                continue

                    time.sleep(2)

                except Exception as e:
                    print(f"   ❌ Easy Apply test failed: {e}")
                    continue

            print(f"✅ LinkedIn applications tested: {applications} successful")
            return applications

        except Exception as e:
            logger.error(f"LinkedIn application testing error: {e}")
            return 0

    def run_persistent_automation(self):
        """Run persistent automation until both platforms are working"""
        try:
            print("🚀 PERSISTENT VISUAL AUTOMATION STARTING")
            print("="*70)
            print("🎯 Goal: Get both JobRight and LinkedIn authenticated and working")
            print(f"📧 Account: {self.email}")
            print("🖥️  Browser window will be VISIBLE - you can see everything")
            print("="*70)

            self.setup_visual_driver()

            print("\n⏳ Browser window should now be open and visible...")
            time.sleep(3)

            # Step 1: Authenticate JobRight
            if not self.authenticate_jobright():
                print("⚠️ JobRight authentication issues - but continuing...")

            # Step 2: Authenticate LinkedIn
            if not self.authenticate_linkedin():
                print("⚠️ LinkedIn authentication issues - but continuing...")

            # Step 3: Test job applications
            total_applications = self.test_job_applications()

            # Results
            print(f"\n🎉 PERSISTENT AUTOMATION RESULTS:")
            print("="*70)
            print(f"✅ JobRight authenticated: {self.authenticated_platforms['jobright']}")
            print(f"✅ LinkedIn authenticated: {self.authenticated_platforms['linkedin']}")
            print(f"🎯 Total job applications tested: {total_applications}")

            if self.authenticated_platforms['jobright'] and self.authenticated_platforms['linkedin']:
                print("\n🎉 SUCCESS! Both platforms are authenticated and working!")
                print("   You can now run job applications on both JobRight and LinkedIn")
            else:
                print("\n⚠️ One or more platforms need attention:")
                if not self.authenticated_platforms['jobright']:
                    print("   - JobRight needs authentication setup")
                if not self.authenticated_platforms['linkedin']:
                    print("   - LinkedIn needs authentication setup")

            print("\n🔄 CONTINUOUS OPERATION MODE")
            print("="*70)
            print("The browser will stay open for you to:")
            print("1. Complete any remaining authentication")
            print("2. Test job applications manually")
            print("3. Verify everything is working")
            print("4. Run automated applications when ready")

            # Keep browser open for manual interaction
            while True:
                print(f"\n📊 Status Update:")
                print(f"   JobRight: {'✅ Ready' if self.authenticated_platforms['jobright'] else '⚠️ Needs setup'}")
                print(f"   LinkedIn: {'✅ Ready' if self.authenticated_platforms['linkedin'] else '⚠️ Needs setup'}")

                user_input = input("\nOptions: [j]obright test, [l]inkedin test, [b]oth test, [q]uit: ").lower().strip()

                if user_input == 'q':
                    break
                elif user_input == 'j':
                    self.test_jobright_applications()
                elif user_input == 'l':
                    self.test_linkedin_applications()
                elif user_input == 'b':
                    self.test_job_applications()
                else:
                    print("   Invalid option. Use j, l, b, or q")

        except Exception as e:
            logger.error(f"Persistent automation error: {e}")
            import traceback
            traceback.print_exc()

        finally:
            if self.driver:
                print("\n🔄 Keeping browser open for manual use...")
                input("Press Enter to close browser and exit...")
                self.driver.quit()

if __name__ == "__main__":
    automation = PersistentVisualAutomation()
    automation.run_persistent_automation()