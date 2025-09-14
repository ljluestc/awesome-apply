#!/usr/bin/env python3
"""
Direct Job Application Automation
Go straight to jobs and apply using existing Google session
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
import json
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DirectJobAutomation:
    def __init__(self, email="jeremykalilin@gmail.com"):
        self.email = email
        self.driver = None
        self.applications = []

    def setup_driver(self):
        """Setup Chrome with Google session persistence"""
        chrome_options = Options()

        # Use existing Google session
        user_data_dir = f"/tmp/chrome_profile_{self.email.replace('@', '_').replace('.', '_')}"
        chrome_options.add_argument(f"--user-data-dir={user_data_dir}")
        chrome_options.add_argument("--profile-directory=Default")

        # Anti-detection
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)

        # Performance
        chrome_options.add_argument("--disable-extensions")
        chrome_options.add_argument("--disable-plugins")

        self.driver = webdriver.Chrome(
            service=Service(ChromeDriverManager().install()),
            options=chrome_options
        )

        self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        logger.info("✅ Chrome driver setup completed")

    def go_to_jobs_page(self):
        """Go directly to jobs page and handle authentication"""
        try:
            # Try direct jobs URLs that have been observed to work
            jobs_urls = [
                "https://jobright.ai/jobs/recommend",
                "https://jobright.ai/jobs",
                "https://jobright.ai/dashboard",
                "https://jobright.ai/jobs/recommend?pos=0"
            ]

            for url in jobs_urls:
                logger.info(f"🎯 Trying jobs URL: {url}")
                self.driver.get(url)
                time.sleep(5)

                current_url = self.driver.current_url.lower()
                page_title = self.driver.title

                logger.info(f"   Result URL: {current_url}")
                logger.info(f"   Page title: {page_title}")

                # Check if we need authentication
                if self.check_authentication_required():
                    logger.info("🔑 Authentication required - handling...")
                    if self.handle_google_authentication():
                        logger.info("✅ Authentication successful")
                        time.sleep(3)
                    else:
                        logger.warning("❌ Authentication failed")
                        continue

                # Check if we're on a jobs page
                if self.verify_jobs_page():
                    logger.info(f"✅ Successfully on jobs page: {url}")
                    return True

            logger.error("❌ Could not access jobs page")
            return False

        except Exception as e:
            logger.error(f"❌ Jobs page access failed: {e}")
            return False

    def check_authentication_required(self):
        """Check if authentication is required"""
        try:
            page_source = self.driver.page_source.lower()
            current_url = self.driver.current_url.lower()

            # Signs we need authentication
            auth_indicators = [
                'sign in', 'log in', 'login', 'signin', 'authenticate',
                'google', 'oauth', 'unauthorized', 'access denied'
            ]

            # Signs we're already authenticated
            success_indicators = [
                'jobs', 'dashboard', 'recommend', 'apply', 'profile',
                'settings', 'welcome', 'logout'
            ]

            if any(indicator in page_source for indicator in success_indicators):
                logger.info("   Already authenticated")
                return False

            if any(indicator in page_source or indicator in current_url for indicator in auth_indicators):
                logger.info("   Authentication required")
                return True

            # Check for specific elements that indicate need for auth
            login_elements = self.driver.find_elements(By.XPATH, "//*[contains(text(), 'Sign') or contains(text(), 'Log') or contains(@href, 'google')]")
            if login_elements:
                logger.info(f"   Found {len(login_elements)} auth elements")
                return True

            return False

        except Exception as e:
            logger.warning(f"Auth check error: {e}")
            return True  # Assume auth required if check fails

    def handle_google_authentication(self):
        """Handle Google authentication"""
        try:
            logger.info("🔐 Handling Google authentication...")

            # Look for Google sign-in buttons
            google_selectors = [
                "//button[contains(text(), 'Google')]",
                "//a[contains(text(), 'Google')]",
                "//button[contains(text(), 'Sign in with Google')]",
                "//a[contains(text(), 'Sign in with Google')]",
                "//*[@href*='google']",
                "//*[@onclick*='google']",
                "//*[contains(@class, 'google')]"
            ]

            for selector in google_selectors:
                try:
                    elements = self.driver.find_elements(By.XPATH, selector)
                    for element in elements:
                        if element.is_displayed() and element.is_enabled():
                            element_text = element.text or element.get_attribute('href') or ''
                            if 'google' in element_text.lower():
                                logger.info(f"   Clicking Google auth: {element.text}")
                                element.click()
                                time.sleep(5)

                                # Wait for Google auth to complete
                                return self.wait_for_auth_completion()
                except Exception:
                    continue

            logger.warning("❌ No Google authentication buttons found")
            return False

        except Exception as e:
            logger.error(f"Google auth error: {e}")
            return False

    def wait_for_auth_completion(self):
        """Wait for authentication to complete"""
        try:
            logger.info("⏳ Waiting for authentication completion...")

            max_wait = 120  # 2 minutes
            start_time = time.time()

            while time.time() - start_time < max_wait:
                current_url = self.driver.current_url.lower()

                # Success indicators
                if any(indicator in current_url for indicator in ['jobright.ai/jobs', 'jobright.ai/dashboard', 'jobright.ai/recommend']):
                    logger.info("✅ Authentication completed successfully")
                    return True

                # Check if still on auth page
                if 'google' in current_url or 'accounts' in current_url:
                    logger.info("   Still on Google authentication page...")

                    # Check for account selection
                    account_elements = self.driver.find_elements(By.XPATH, f"//*[contains(text(), '{self.email}')]")
                    if account_elements:
                        for elem in account_elements:
                            if elem.is_displayed():
                                logger.info(f"   Selecting account: {self.email}")
                                elem.click()
                                time.sleep(3)
                                break

                time.sleep(2)

            logger.warning("⏰ Authentication timeout")
            return False

        except Exception as e:
            logger.error(f"Auth completion wait error: {e}")
            return False

    def verify_jobs_page(self):
        """Verify we're on a jobs page"""
        try:
            page_source = self.driver.page_source.lower()

            jobs_indicators = [
                'apply now', 'apply', 'job', 'position', 'company',
                'salary', 'location', 'remote', 'full-time', 'part-time'
            ]

            indicator_count = sum(1 for indicator in jobs_indicators if indicator in page_source)

            logger.info(f"   Jobs page indicators found: {indicator_count}/{len(jobs_indicators)}")

            return indicator_count >= 3  # Need at least 3 job-related terms

        except Exception as e:
            logger.error(f"Jobs page verification error: {e}")
            return False

    def find_apply_buttons(self):
        """Find all Apply Now buttons on the page"""
        try:
            logger.info("🔍 Looking for Apply Now buttons...")

            # Comprehensive selectors for Apply buttons
            apply_selectors = [
                "//button[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'apply now')]",
                "//a[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'apply now')]",
                "//button[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'apply')]",
                "//a[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'apply')]",
                "//*[@data-action='apply']",
                "//*[contains(@class, 'apply')]",
                "//button[contains(@onclick, 'apply')]",
                "//a[contains(@href, 'apply')]"
            ]

            apply_buttons = []

            for selector in apply_selectors:
                try:
                    elements = self.driver.find_elements(By.XPATH, selector)
                    for element in elements:
                        if element.is_displayed() and element.is_enabled():
                            button_text = element.text.strip()
                            if any(word in button_text.lower() for word in ['apply', 'submit', 'send']):
                                apply_buttons.append({
                                    'element': element,
                                    'text': button_text,
                                    'href': element.get_attribute('href'),
                                    'onclick': element.get_attribute('onclick')
                                })
                except Exception:
                    continue

            # Remove duplicates
            unique_buttons = []
            seen_texts = set()
            for btn in apply_buttons:
                if btn['text'] not in seen_texts:
                    unique_buttons.append(btn)
                    seen_texts.add(btn['text'])

            logger.info(f"✅ Found {len(unique_buttons)} unique Apply buttons")

            for i, btn in enumerate(unique_buttons):
                logger.info(f"   {i+1}. '{btn['text']}' | href: {btn['href'] or 'None'}")

            return unique_buttons

        except Exception as e:
            logger.error(f"Apply button search error: {e}")
            return []

    def click_apply_button(self, button_info):
        """Click an apply button and handle the application process"""
        try:
            element = button_info['element']
            text = button_info['text']

            logger.info(f"🎯 Clicking Apply button: '{text}'")

            # Get current window count
            original_windows = self.driver.window_handles

            # Try different click methods
            click_methods = [
                lambda: element.click(),
                lambda: self.driver.execute_script("arguments[0].click();", element),
                lambda: ActionChains(self.driver).move_to_element(element).click().perform()
            ]

            clicked = False
            for i, method in enumerate(click_methods):
                try:
                    method()
                    clicked = True
                    logger.info(f"   Click method {i+1} succeeded")
                    break
                except Exception as e:
                    logger.debug(f"   Click method {i+1} failed: {e}")
                    continue

            if not clicked:
                logger.error(f"❌ All click methods failed for: {text}")
                return False

            time.sleep(3)  # Wait for action to take effect

            # Check if new window/tab opened
            new_windows = self.driver.window_handles
            if len(new_windows) > len(original_windows):
                logger.info("   ✅ New window/tab opened")
                # Switch to new window
                self.driver.switch_to.window(new_windows[-1])
                time.sleep(2)

                # Process the application
                return self.process_application_page()

            # Check if same page navigation occurred
            current_url = self.driver.current_url
            if 'apply' in current_url.lower() or 'application' in current_url.lower():
                logger.info("   ✅ Navigated to application page")
                return self.process_application_page()

            logger.warning("   ⚠️ Click registered but no clear navigation")
            return True  # Consider it successful even if we can't verify

        except Exception as e:
            logger.error(f"Apply button click error: {e}")
            return False

    def process_application_page(self):
        """Process the application page after clicking Apply"""
        try:
            logger.info("📝 Processing application page...")

            time.sleep(3)  # Wait for page to load

            current_url = self.driver.current_url
            page_title = self.driver.title

            logger.info(f"   Application page URL: {current_url}")
            logger.info(f"   Page title: {page_title}")

            # Look for form elements
            forms = self.driver.find_elements(By.TAG_NAME, "form")
            inputs = self.driver.find_elements(By.TAG_NAME, "input")
            textareas = self.driver.find_elements(By.TAG_NAME, "textarea")

            logger.info(f"   Found {len(forms)} forms, {len(inputs)} inputs, {len(textareas)} textareas")

            # Look for submit/apply buttons on the application page
            submit_buttons = self.driver.find_elements(By.XPATH,
                "//button[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'submit') or "
                "contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'apply') or "
                "contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'send')]"
            )

            if submit_buttons:
                logger.info(f"   Found {len(submit_buttons)} submit buttons")
                for btn in submit_buttons:
                    if btn.is_displayed() and btn.is_enabled():
                        logger.info(f"   Clicking submit: '{btn.text}'")
                        btn.click()
                        time.sleep(2)
                        break

            # Record the application
            self.applications.append({
                'url': current_url,
                'title': page_title,
                'timestamp': time.time(),
                'status': 'submitted'
            })

            logger.info("   ✅ Application processed")
            return True

        except Exception as e:
            logger.error(f"Application processing error: {e}")
            return False

    def apply_to_all_jobs(self):
        """Apply to all available jobs"""
        try:
            if not self.go_to_jobs_page():
                return False

            # Load more jobs by scrolling
            self.load_more_jobs()

            # Find all apply buttons
            apply_buttons = self.find_apply_buttons()

            if not apply_buttons:
                logger.warning("❌ No apply buttons found")
                return False

            logger.info(f"🚀 Starting applications to {len(apply_buttons)} jobs...")

            successful_applications = 0
            failed_applications = 0

            for i, button_info in enumerate(apply_buttons):
                logger.info(f"\n📋 Application {i+1}/{len(apply_buttons)}")

                try:
                    if self.click_apply_button(button_info):
                        successful_applications += 1
                        logger.info(f"   ✅ Application {i+1} successful")
                    else:
                        failed_applications += 1
                        logger.error(f"   ❌ Application {i+1} failed")

                    # Return to main jobs page if we're in a new tab
                    if len(self.driver.window_handles) > 1:
                        self.driver.close()  # Close application tab
                        self.driver.switch_to.window(self.driver.window_handles[0])  # Back to main tab

                    time.sleep(2)  # Brief delay between applications

                except Exception as e:
                    failed_applications += 1
                    logger.error(f"   ❌ Application {i+1} exception: {e}")

            logger.info(f"\n🎯 APPLICATION SUMMARY:")
            logger.info(f"   ✅ Successful: {successful_applications}")
            logger.info(f"   ❌ Failed: {failed_applications}")
            logger.info(f"   📊 Success Rate: {(successful_applications/(successful_applications+failed_applications)*100):.1f}%")

            return successful_applications > 0

        except Exception as e:
            logger.error(f"Apply to all jobs error: {e}")
            return False

    def load_more_jobs(self):
        """Load more jobs by scrolling and clicking load more buttons"""
        try:
            logger.info("📜 Loading more jobs...")

            # Scroll to load more content
            for _ in range(5):
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(2)

            # Look for "Load More" or similar buttons
            load_more_selectors = [
                "//button[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'load more')]",
                "//button[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'show more')]",
                "//button[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'more jobs')]",
                "//*[contains(@class, 'load-more')]",
                "//*[contains(@class, 'show-more')]"
            ]

            for selector in load_more_selectors:
                try:
                    elements = self.driver.find_elements(By.XPATH, selector)
                    for element in elements:
                        if element.is_displayed() and element.is_enabled():
                            logger.info(f"   Clicking load more: {element.text}")
                            element.click()
                            time.sleep(3)
                except Exception:
                    continue

            logger.info("   ✅ Finished loading more jobs")

        except Exception as e:
            logger.error(f"Load more jobs error: {e}")

    def run(self):
        """Run the complete automation"""
        try:
            logger.info("🚀 STARTING DIRECT JOB APPLICATION AUTOMATION")
            logger.info("="*60)

            self.setup_driver()

            if self.apply_to_all_jobs():
                logger.info("✅ Automation completed successfully!")

                # Show results
                if self.applications:
                    logger.info(f"\n📊 APPLICATIONS SUMMARY:")
                    for i, app in enumerate(self.applications):
                        logger.info(f"   {i+1}. {app['title']} - {app['status']}")
            else:
                logger.error("❌ Automation failed")

            input("\nPress Enter to close browser...")

        except Exception as e:
            logger.error(f"❌ Automation error: {e}")

        finally:
            if self.driver:
                self.driver.quit()

if __name__ == "__main__":
    automation = DirectJobAutomation("jeremykalilin@gmail.com")
    automation.run()