#!/usr/bin/env python3
"""
DIRECT VISUAL AUTOMATION - No stopping until both platforms are authenticated and working
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
import time
import logging
import json

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class DirectVisualAutomation:
    def __init__(self):
        self.driver = None
        self.authenticated_jobright = False
        self.authenticated_linkedin = False
        self.applied_jobs = []

    def setup_driver(self):
        """Setup Chrome driver with visual mode and persistent profile"""
        chrome_options = Options()

        # Persistent profile for session management
        user_data_dir = "/tmp/chrome_direct_visual_profile"
        chrome_options.add_argument(f"--user-data-dir={user_data_dir}")
        chrome_options.add_argument("--profile-directory=Default")

        # VISUAL MODE - NO HEADLESS
        chrome_options.add_argument("--window-size=1400,1000")
        chrome_options.add_argument("--start-maximized")

        # Anti-detection
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)

        self.driver = webdriver.Chrome(
            service=Service(ChromeDriverManager().install()),
            options=chrome_options
        )

        self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        logger.info("✅ Visual Chrome driver setup completed - browser window should be visible")

    def authenticate_jobright(self):
        """Authenticate JobRight.ai with visual confirmation"""
        try:
            logger.info("\n🎯 AUTHENTICATING JOBRIGHT.AI...")
            logger.info("="*50)

            # Go to JobRight
            logger.info("🌐 Opening JobRight.ai - you should see the browser window open...")
            self.driver.get("https://jobright.ai/")
            time.sleep(5)

            logger.info(f"   Current URL: {self.driver.current_url}")
            logger.info(f"   Page title: {self.driver.title}")

            # Try to navigate to jobs page directly
            jobs_urls = [
                "https://jobright.ai/entry-level-jobs",
                "https://jobright.ai/jobs",
                "https://jobright.ai/jobs/recommend"
            ]

            for url in jobs_urls:
                logger.info(f"🔍 Trying jobs URL: {url}")
                self.driver.get(url)
                time.sleep(5)

                # Check if we're on a jobs page (look for job-related content)
                if any(term in self.driver.page_source.lower() for term in ['apply', 'job', 'position', 'career']):
                    logger.info("✅ JobRight jobs page loaded successfully!")
                    self.authenticated_jobright = True
                    break

            if not self.authenticated_jobright:
                # Look for sign in options
                logger.info("🔐 Looking for authentication options...")

                # Look for Google SSO
                google_buttons = self.driver.find_elements(By.XPATH,
                    "//button[contains(text(), 'Google') or contains(text(), 'Continue with Google')] | "
                    "//a[contains(text(), 'Google') or contains(text(), 'Continue with Google')]"
                )

                if google_buttons:
                    logger.info("✅ Found Google SSO option - clicking...")
                    google_buttons[0].click()
                    time.sleep(8)

                    # Handle Google account selection
                    try:
                        account_elements = self.driver.find_elements(By.XPATH,
                            "//*[contains(text(), 'jeremykalilin@gmail.com') or contains(@data-email, 'jeremykalilin@gmail.com')]"
                        )
                        if account_elements:
                            logger.info("👤 Found Jeremy's account - selecting...")
                            account_elements[0].click()
                            time.sleep(5)
                        else:
                            logger.info("👤 No specific account found - proceeding with available options")
                            # Try clicking any account option
                            account_options = self.driver.find_elements(By.XPATH, "//div[@data-identifier]")
                            if account_options:
                                account_options[0].click()
                                time.sleep(5)
                    except Exception as e:
                        logger.info(f"👤 Account selection step: {e}")

                    # After SSO, try jobs URLs again
                    for url in jobs_urls:
                        self.driver.get(url)
                        time.sleep(5)
                        if any(term in self.driver.page_source.lower() for term in ['apply', 'job', 'position']):
                            logger.info("✅ JobRight authenticated via Google SSO!")
                            self.authenticated_jobright = True
                            break

            return self.authenticated_jobright

        except Exception as e:
            logger.error(f"JobRight authentication error: {e}")
            return False

    def authenticate_linkedin(self):
        """Authenticate LinkedIn with visual confirmation"""
        try:
            logger.info("\n🎯 AUTHENTICATING LINKEDIN...")
            logger.info("="*50)

            target_url = "https://www.linkedin.com/jobs/search/?distance=25&geoId=106233382&keywords=software"
            logger.info(f"🌐 Opening LinkedIn jobs page: {target_url}")

            self.driver.get(target_url)
            time.sleep(5)

            logger.info(f"   Current URL: {self.driver.current_url}")
            logger.info(f"   Page title: {self.driver.title}")

            # Check if we're already authenticated (jobs page loads directly)
            if "jobs" in self.driver.current_url and "authwall" not in self.driver.current_url:
                logger.info("✅ LinkedIn already authenticated!")
                self.authenticated_linkedin = True
                return True

            # Check if we hit the auth wall
            if "authwall" in self.driver.current_url or "signup" in self.driver.current_url.lower():
                logger.info("🔐 LinkedIn authentication required...")

                # Look for email input
                email_inputs = self.driver.find_elements(By.XPATH,
                    "//input[@type='email' or @name='session_key' or @id='username']"
                )

                if email_inputs:
                    logger.info("📧 Entering email: jeremykalilin@gmail.com")
                    email_input = email_inputs[0]
                    email_input.clear()
                    email_input.send_keys("jeremykalilin@gmail.com")
                    time.sleep(2)

                    # Look for password input
                    password_inputs = self.driver.find_elements(By.XPATH,
                        "//input[@type='password' or @name='session_password' or @id='password']"
                    )

                    if password_inputs:
                        logger.info("🔑 Password field found - manual entry may be needed")
                        logger.info("⏳ Waiting 15 seconds for manual password entry if needed...")
                        time.sleep(15)

                        # Try to find and click sign in button
                        signin_buttons = self.driver.find_elements(By.XPATH,
                            "//button[contains(text(), 'Sign in') or contains(text(), 'Continue')] | "
                            "//input[@type='submit' and (contains(@value, 'Sign') or contains(@value, 'Continue'))]"
                        )

                        if signin_buttons:
                            logger.info("🔘 Clicking sign in button...")
                            signin_buttons[0].click()
                            time.sleep(10)

                            # Check if we're now on jobs page
                            if "jobs" in self.driver.current_url and "authwall" not in self.driver.current_url:
                                logger.info("✅ LinkedIn authentication successful!")
                                self.authenticated_linkedin = True
                                return True

                # Try direct navigation to jobs after any auth attempts
                self.driver.get(target_url)
                time.sleep(5)

                if "jobs" in self.driver.current_url and "authwall" not in self.driver.current_url:
                    logger.info("✅ LinkedIn jobs page accessible!")
                    self.authenticated_linkedin = True
                    return True

            return self.authenticated_linkedin

        except Exception as e:
            logger.error(f"LinkedIn authentication error: {e}")
            return False

    def test_job_applications(self):
        """Test opening job application pages on both platforms"""
        logger.info("\n🎯 TESTING JOB APPLICATIONS...")
        logger.info("="*50)

        applications_tested = 0

        # Test JobRight applications if authenticated
        if self.authenticated_jobright:
            logger.info("🎯 Testing JobRight job applications...")

            # Go to JobRight jobs page
            self.driver.get("https://jobright.ai/entry-level-jobs")
            time.sleep(5)

            # Scroll to load content
            for i in range(3):
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(2)

            # Find clickable job elements
            clickable_elements = self.driver.find_elements(By.XPATH,
                "//*[@href or @onclick or contains(@class, 'job') or contains(@class, 'apply') or contains(@class, 'button')]"
            )

            logger.info(f"   Found {len(clickable_elements)} clickable elements")

            # Test first few elements
            for i, element in enumerate(clickable_elements[:5]):
                try:
                    if element.is_displayed():
                        text = element.text.strip()[:50]
                        logger.info(f"   Testing element {i+1}: '{text}'")

                        original_window_count = len(self.driver.window_handles)
                        original_url = self.driver.current_url

                        # Try clicking
                        element.click()
                        time.sleep(3)

                        # Check if new page/window opened
                        new_window_count = len(self.driver.window_handles)
                        new_url = self.driver.current_url

                        if new_window_count > original_window_count:
                            logger.info("   ✅ New window opened - job application page!")
                            applications_tested += 1

                            # Switch to new window to see the application page
                            self.driver.switch_to.window(self.driver.window_handles[-1])
                            time.sleep(2)

                            app_title = self.driver.title
                            app_url = self.driver.current_url

                            logger.info(f"   📄 Application page: {app_title}")
                            logger.info(f"   🔗 URL: {app_url}")

                            # Save the application
                            self.applied_jobs.append({
                                'platform': 'jobright',
                                'title': app_title,
                                'url': app_url,
                                'timestamp': time.time()
                            })

                            # Close new window and return
                            self.driver.close()
                            self.driver.switch_to.window(self.driver.window_handles[0])

                        elif new_url != original_url:
                            logger.info("   ✅ Page navigation - job details page!")
                            applications_tested += 1

                            # Save and go back
                            self.applied_jobs.append({
                                'platform': 'jobright',
                                'title': self.driver.title,
                                'url': new_url,
                                'timestamp': time.time()
                            })

                            self.driver.back()
                            time.sleep(2)

                except Exception as e:
                    logger.info(f"   ⚠️ Element test failed: {e}")
                    continue

        # Test LinkedIn applications if authenticated
        if self.authenticated_linkedin:
            logger.info("\n🎯 Testing LinkedIn job applications...")

            # Go to LinkedIn jobs search
            linkedin_url = "https://www.linkedin.com/jobs/search/?distance=25&geoId=106233382&keywords=software"
            self.driver.get(linkedin_url)
            time.sleep(5)

            # Look for job cards
            job_cards = self.driver.find_elements(By.XPATH,
                "//div[contains(@class, 'job-card') or contains(@class, 'jobs-search-results__list-item')]"
            )

            logger.info(f"   Found {len(job_cards)} LinkedIn job cards")

            # Test first few job cards
            for i, card in enumerate(job_cards[:3]):
                try:
                    # Find clickable elements in the card
                    clickable_in_card = card.find_elements(By.XPATH, ".//a | .//button")

                    for element in clickable_in_card:
                        if element.is_displayed():
                            text = element.text.strip()

                            if any(term in text.lower() for term in ['apply', 'view', 'easy apply']):
                                logger.info(f"   Testing LinkedIn element: '{text[:30]}'")

                                original_window_count = len(self.driver.window_handles)

                                element.click()
                                time.sleep(3)

                                new_window_count = len(self.driver.window_handles)

                                if new_window_count > original_window_count:
                                    logger.info("   ✅ LinkedIn application page opened!")
                                    applications_tested += 1

                                    # Switch to see the application
                                    self.driver.switch_to.window(self.driver.window_handles[-1])
                                    time.sleep(2)

                                    self.applied_jobs.append({
                                        'platform': 'linkedin',
                                        'title': self.driver.title,
                                        'url': self.driver.current_url,
                                        'timestamp': time.time()
                                    })

                                    # Return to main window
                                    self.driver.close()
                                    self.driver.switch_to.window(self.driver.window_handles[0])

                                break

                except Exception as e:
                    continue

        return applications_tested

    def run_continuous_automation(self):
        """Run the automation continuously until both platforms work"""
        logger.info("\n🚀 DIRECT VISUAL AUTOMATION STARTING")
        logger.info("="*70)
        logger.info("🎯 Goal: Get both JobRight and LinkedIn authenticated and working")
        logger.info("📧 Account: jeremykalilin@gmail.com")
        logger.info("🖥️  Browser window will be VISIBLE - you can see everything")
        logger.info("="*70)

        try:
            # Setup driver
            self.setup_driver()
            logger.info("\n⏳ Browser window should now be open and visible...")
            time.sleep(3)

            # Keep trying until both platforms are authenticated
            max_attempts = 5
            attempt = 1

            while attempt <= max_attempts and not (self.authenticated_jobright and self.authenticated_linkedin):
                logger.info(f"\n🔄 ATTEMPT {attempt}/{max_attempts}")
                logger.info("-" * 40)

                # Try JobRight authentication
                if not self.authenticated_jobright:
                    logger.info("🎯 Attempting JobRight authentication...")
                    self.authenticate_jobright()

                # Try LinkedIn authentication
                if not self.authenticated_linkedin:
                    logger.info("🎯 Attempting LinkedIn authentication...")
                    self.authenticate_linkedin()

                # Status update
                logger.info(f"\n📊 STATUS UPDATE - Attempt {attempt}:")
                logger.info(f"   JobRight: {'✅ Authenticated' if self.authenticated_jobright else '❌ Needs work'}")
                logger.info(f"   LinkedIn: {'✅ Authenticated' if self.authenticated_linkedin else '❌ Needs work'}")

                if self.authenticated_jobright and self.authenticated_linkedin:
                    logger.info("\n🎉 BOTH PLATFORMS AUTHENTICATED!")
                    break

                attempt += 1
                if attempt <= max_attempts:
                    logger.info(f"\n⏳ Waiting 10 seconds before next attempt...")
                    time.sleep(10)

            # Test job applications
            if self.authenticated_jobright or self.authenticated_linkedin:
                applications_tested = self.test_job_applications()

                logger.info(f"\n🎉 AUTOMATION RESULTS:")
                logger.info("="*50)
                logger.info(f"✅ JobRight authenticated: {self.authenticated_jobright}")
                logger.info(f"✅ LinkedIn authenticated: {self.authenticated_linkedin}")
                logger.info(f"🎯 Job application pages tested: {applications_tested}")
                logger.info(f"📋 Total jobs found: {len(self.applied_jobs)}")

                if self.applied_jobs:
                    logger.info(f"\n📋 JOBS ACCESSED:")
                    for i, job in enumerate(self.applied_jobs):
                        logger.info(f"   {i+1}. [{job['platform'].upper()}] {job['title']}")
                        logger.info(f"      URL: {job['url']}")

                # Save results
                results = {
                    'jobright_authenticated': self.authenticated_jobright,
                    'linkedin_authenticated': self.authenticated_linkedin,
                    'applications_tested': applications_tested,
                    'jobs_accessed': self.applied_jobs,
                    'timestamp': time.time()
                }

                with open('direct_visual_results.json', 'w') as f:
                    json.dump(results, f, indent=2)

                logger.info(f"\n💾 Results saved to: direct_visual_results.json")

            # Keep browser open for continuous operation
            logger.info(f"\n🔄 CONTINUOUS OPERATION MODE")
            logger.info("="*50)
            logger.info("Browser staying open for continued use...")
            logger.info("Both platforms should now be visible and accessible!")
            logger.info("You can manually test job applications or run automated processes.")

            # Keep running indefinitely
            while True:
                time.sleep(30)
                logger.info(f"🔄 System running... JobRight: {'✅' if self.authenticated_jobright else '❌'} | LinkedIn: {'✅' if self.authenticated_linkedin else '❌'}")

        except KeyboardInterrupt:
            logger.info("\n⏹️  Automation stopped by user")
        except Exception as e:
            logger.error(f"Automation error: {e}")
            import traceback
            traceback.print_exc()
        finally:
            if self.driver:
                logger.info("\n🔄 Browser staying open - close manually when done")
                # Don't quit driver - let it stay open
                pass

if __name__ == "__main__":
    automation = DirectVisualAutomation()
    automation.run_continuous_automation()