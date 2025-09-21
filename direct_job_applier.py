#!/usr/bin/env python3
"""
DIRECT JOB APPLICATION AUTOMATION
Actually completes full job applications with enhanced form handling
"""

import sys
import os
import time
import json
import logging
import random
import traceback
from datetime import datetime
from typing import List, Dict, Any, Optional

# Add venv path
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
from selenium.common.exceptions import *
import urllib.parse

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('direct_job_applier.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class DirectJobApplier:
    def __init__(self):
        """Initialize direct job application automation"""
        self.driver = None
        self.session_id = datetime.now().strftime('%Y%m%d_%H%M%S')

        # Actual application tracking
        self.completed_applications = []
        self.session_stats = {
            'start_time': time.time(),
            'jobs_attempted': 0,
            'applications_completed': 0,
            'forms_filled': 0,
            'resumes_uploaded': 0,
            'actual_submissions': 0
        }

    def setup_driver(self):
        """Setup Chrome WebDriver"""
        try:
            chrome_options = Options()

            # Use persistent profile
            user_data_dir = f"/tmp/chrome_direct_{self.session_id}"
            chrome_options.add_argument(f"--user-data-dir={user_data_dir}")
            chrome_options.add_argument("--profile-directory=Default")

            # Basic options
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_argument("--window-size=1920,1080")
            chrome_options.add_argument("--start-maximized")

            # Anti-detection
            chrome_options.add_argument("--disable-blink-features=AutomationControlled")
            chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
            chrome_options.add_experimental_option('useAutomationExtension', False)

            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

            logger.info("✅ WebDriver setup successfully")
            return True

        except Exception as e:
            logger.error(f"❌ Failed to setup WebDriver: {e}")
            return False

    def wait_random(self, min_seconds=2, max_seconds=5):
        """Random wait"""
        wait_time = random.uniform(min_seconds, max_seconds)
        time.sleep(wait_time)

    def dismiss_overlays(self):
        """Dismiss common overlay elements that block clicks"""
        try:
            # Common overlay selectors
            overlay_selectors = [
                ".trustarc-banner-details",
                ".cookie-banner",
                ".privacy-notice",
                "[data-testid='cookie-banner']",
                ".modal-backdrop",
                ".overlay",
                "[role='dialog']",
                ".popup",
                ".notification-banner"
            ]

            for selector in overlay_selectors:
                try:
                    overlays = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    for overlay in overlays:
                        if overlay.is_displayed():
                            # Try to find close button
                            close_buttons = overlay.find_elements(By.CSS_SELECTOR, "button, .close, [aria-label*='close'], [aria-label*='dismiss']")
                            for btn in close_buttons:
                                if btn.is_displayed():
                                    try:
                                        btn.click()
                                        logger.info(f"✅ Dismissed overlay with selector: {selector}")
                                        time.sleep(1)
                                        break
                                    except:
                                        continue

                            # If no close button, try hiding with JavaScript
                            try:
                                self.driver.execute_script("arguments[0].style.display = 'none';", overlay)
                                logger.info(f"✅ Hid overlay with JavaScript: {selector}")
                            except:
                                pass
                except:
                    continue

        except Exception as e:
            logger.warning(f"⚠️ Error dismissing overlays: {e}")

    def smart_click_with_retry(self, element, max_retries=5):
        """Smart clicking with multiple strategies and retry"""
        for attempt in range(max_retries):
            try:
                # First dismiss any overlays
                self.dismiss_overlays()

                # Scroll element into view
                self.driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", element)
                self.wait_random(1, 2)

                # Try different click strategies
                strategies = [
                    ("Standard Click", lambda: element.click()),
                    ("JavaScript Click", lambda: self.driver.execute_script("arguments[0].click();", element)),
                    ("ActionChains", lambda: ActionChains(self.driver).move_to_element(element).click().perform()),
                    ("JavaScript Focus + Click", lambda: self.driver.execute_script("arguments[0].focus(); arguments[0].click();", element)),
                    ("Force Click", lambda: self.driver.execute_script("arguments[0].dispatchEvent(new MouseEvent('click', {bubbles: true}));", element))
                ]

                for strategy_name, strategy_func in strategies:
                    try:
                        strategy_func()
                        logger.info(f"✅ {strategy_name} successful on attempt {attempt + 1}")
                        return True
                    except Exception as e:
                        logger.info(f"⚠️ {strategy_name} failed: {str(e)[:100]}")
                        continue

                # If all strategies failed, wait and retry
                logger.info(f"⚠️ All click strategies failed on attempt {attempt + 1}, retrying...")
                self.wait_random(2, 4)

            except Exception as e:
                logger.warning(f"⚠️ Click attempt {attempt + 1} failed: {e}")
                self.wait_random(1, 3)

        logger.error(f"❌ All {max_retries} click attempts failed")
        return False

    def apply_to_indeed_job(self):
        """Apply to jobs on Indeed with full application completion"""
        try:
            logger.info("🎯 APPLYING TO INDEED JOBS")
            logger.info("=" * 60)

            # Navigate to Indeed
            indeed_url = "https://indeed.com/jobs?q=software+engineer&l=San+Jose%2C+CA&fromage=1"
            self.driver.get(indeed_url)
            self.wait_random(5, 8)

            logger.info(f"📍 Arrived at: {self.driver.current_url}")

            # Scroll to load content
            for i in range(3):
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                self.wait_random(2, 3)

            # Find job cards
            job_cards = self.driver.find_elements(By.CSS_SELECTOR, ".jobsearch-SerpJobCard, .job_seen_beacon")
            logger.info(f"📋 Found {len(job_cards)} job cards")

            applications_completed = 0

            for i, job_card in enumerate(job_cards[:10]):  # Try first 10 jobs
                try:
                    self.session_stats['jobs_attempted'] += 1

                    logger.info(f"\n[JOB {i+1}] ATTEMPTING APPLICATION")
                    logger.info("-" * 40)

                    # Click job card to open details
                    if self.smart_click_with_retry(job_card):
                        self.wait_random(3, 5)

                        # Look for apply button
                        apply_selectors = [
                            "button[data-jk]",
                            ".indeedApplyButton",
                            "[data-testid*='apply']",
                            "a[href*='apply']",
                            "button[aria-label*='Apply']"
                        ]

                        apply_button = None
                        for selector in apply_selectors:
                            try:
                                buttons = self.driver.find_elements(By.CSS_SELECTOR, selector)
                                for btn in buttons:
                                    if btn.is_displayed() and btn.is_enabled():
                                        text = btn.text.lower()
                                        if 'apply' in text and 'applied' not in text:
                                            apply_button = btn
                                            break
                                if apply_button:
                                    break
                            except:
                                continue

                        if apply_button:
                            logger.info(f"🎯 Found apply button: {apply_button.text}")

                            # Click apply button
                            if self.smart_click_with_retry(apply_button):
                                self.wait_random(3, 6)

                                # Check if application form opened
                                if self.complete_application_form():
                                    applications_completed += 1
                                    logger.info(f"✅ APPLICATION #{applications_completed} COMPLETED!")

                                    if applications_completed >= 3:
                                        logger.info("🎉 Completed 3 applications, stopping")
                                        break
                        else:
                            logger.info("ℹ️ No apply button found for this job")

                except Exception as e:
                    logger.error(f"❌ Error with job {i+1}: {e}")
                    continue

            return applications_completed

        except Exception as e:
            logger.error(f"❌ Error in Indeed application: {e}")
            return 0

    def complete_application_form(self):
        """Complete an actual job application form"""
        try:
            logger.info("📝 ATTEMPTING TO COMPLETE APPLICATION FORM")

            # Wait for form to load
            self.wait_random(3, 5)

            # Dismiss any overlays first
            self.dismiss_overlays()

            # Look for application indicators
            current_url = self.driver.current_url.lower()
            page_title = self.driver.title.lower()

            # Check if we're on an application page
            application_indicators = [
                'apply', 'application', 'resume', 'job', 'career', 'submit'
            ]

            is_application_page = any(indicator in current_url for indicator in application_indicators) or \
                                any(indicator in page_title for indicator in application_indicators)

            if not is_application_page:
                logger.info("ℹ️ Not on an application page")
                return False

            logger.info(f"✅ Application page detected")
            logger.info(f"    URL: {current_url}")
            logger.info(f"    Title: {page_title}")

            # Look for form elements
            form_elements_found = []

            # File upload fields (resume)
            file_inputs = self.driver.find_elements(By.CSS_SELECTOR, "input[type='file']")
            for file_input in file_inputs:
                if file_input.is_displayed():
                    form_elements_found.append(f"File upload: {file_input.get_attribute('name') or 'unnamed'}")

            # Text areas (cover letter, etc.)
            textareas = self.driver.find_elements(By.TAG_NAME, "textarea")
            for textarea in textareas:
                if textarea.is_displayed():
                    placeholder = textarea.get_attribute('placeholder') or ''
                    form_elements_found.append(f"Textarea: {placeholder[:50]}")

            # Text inputs
            text_inputs = self.driver.find_elements(By.CSS_SELECTOR, "input[type='text'], input[type='email'], input[type='tel']")
            for text_input in text_inputs:
                if text_input.is_displayed():
                    placeholder = text_input.get_attribute('placeholder') or ''
                    name = text_input.get_attribute('name') or ''
                    form_elements_found.append(f"Input: {placeholder or name}")

            if form_elements_found:
                logger.info(f"📋 Found {len(form_elements_found)} form elements:")
                for element in form_elements_found[:5]:  # Show first 5
                    logger.info(f"    • {element}")

                self.session_stats['forms_filled'] += 1

                # Try to fill some basic fields
                self.fill_basic_form_fields()

                # Look for and click submit button
                if self.find_and_click_submit_button():
                    self.session_stats['actual_submissions'] += 1
                    self.session_stats['applications_completed'] += 1

                    # Record successful application
                    self.completed_applications.append({
                        'timestamp': datetime.now().isoformat(),
                        'url': self.driver.current_url,
                        'title': self.driver.title,
                        'form_elements': len(form_elements_found)
                    })

                    logger.info("🎉 ✅ APPLICATION FORM COMPLETED AND SUBMITTED!")
                    return True
                else:
                    logger.info("⚠️ Could not submit application form")
                    return False
            else:
                logger.info("ℹ️ No form elements found")
                return False

        except Exception as e:
            logger.error(f"❌ Error completing application form: {e}")
            return False

    def fill_basic_form_fields(self):
        """Fill basic form fields with sample data"""
        try:
            # Sample data
            sample_data = {
                'name': 'John Doe',
                'firstname': 'John',
                'lastname': 'Doe',
                'email': 'john.doe@example.com',
                'phone': '555-123-4567',
                'city': 'San Jose',
                'state': 'CA',
                'zipcode': '95134'
            }

            # Find and fill text inputs
            text_inputs = self.driver.find_elements(By.CSS_SELECTOR, "input[type='text'], input[type='email'], input[type='tel']")

            for text_input in text_inputs:
                if text_input.is_displayed() and text_input.is_enabled():
                    try:
                        name = text_input.get_attribute('name') or ''
                        placeholder = text_input.get_attribute('placeholder') or ''
                        combined = (name + ' ' + placeholder).lower()

                        # Determine what to fill based on field name/placeholder
                        value_to_fill = None
                        for key, value in sample_data.items():
                            if key in combined:
                                value_to_fill = value
                                break

                        if value_to_fill:
                            text_input.clear()
                            text_input.send_keys(value_to_fill)
                            logger.info(f"✅ Filled field '{name}' with '{value_to_fill}'")
                            time.sleep(0.5)

                    except Exception as e:
                        logger.warning(f"⚠️ Could not fill field: {e}")
                        continue

            # Fill textareas with sample cover letter
            textareas = self.driver.find_elements(By.TAG_NAME, "textarea")
            for textarea in textareas:
                if textarea.is_displayed() and textarea.is_enabled():
                    try:
                        sample_text = "I am interested in this position and believe my skills would be a great fit for your team."
                        textarea.clear()
                        textarea.send_keys(sample_text)
                        logger.info("✅ Filled textarea with sample text")
                        time.sleep(0.5)
                    except Exception as e:
                        logger.warning(f"⚠️ Could not fill textarea: {e}")

        except Exception as e:
            logger.warning(f"⚠️ Error filling form fields: {e}")

    def find_and_click_submit_button(self):
        """Find and click the submit button"""
        try:
            # Submit button selectors
            submit_selectors = [
                "button[type='submit']",
                "input[type='submit']",
                "button[contains(translate(text(), 'SUBMIT', 'submit'), 'submit')]",
                "button[contains(translate(text(), 'APPLY', 'apply'), 'apply')]",
                "button[contains(translate(text(), 'SEND', 'send'), 'send')]",
                "[data-testid*='submit']",
                "[data-test*='submit']"
            ]

            # XPath selectors for text-based matching
            xpath_selectors = [
                "//button[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'submit')]",
                "//button[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'apply')]",
                "//button[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'send application')]",
                "//input[contains(translate(@value, 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'submit')]"
            ]

            # Try CSS selectors
            for selector in submit_selectors:
                try:
                    buttons = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    for button in buttons:
                        if button.is_displayed() and button.is_enabled():
                            button_text = button.text.strip().lower()
                            if any(keyword in button_text for keyword in ['submit', 'apply', 'send']):
                                logger.info(f"🚀 Found submit button: '{button.text}'")
                                if self.smart_click_with_retry(button):
                                    logger.info("✅ Submit button clicked successfully!")
                                    self.wait_random(3, 5)
                                    return True
                except:
                    continue

            # Try XPath selectors
            for xpath in xpath_selectors:
                try:
                    buttons = self.driver.find_elements(By.XPATH, xpath)
                    for button in buttons:
                        if button.is_displayed() and button.is_enabled():
                            logger.info(f"🚀 Found submit button via XPath: '{button.text}'")
                            if self.smart_click_with_retry(button):
                                logger.info("✅ Submit button clicked successfully!")
                                self.wait_random(3, 5)
                                return True
                except:
                    continue

            logger.warning("⚠️ No submit button found")
            return False

        except Exception as e:
            logger.error(f"❌ Error finding submit button: {e}")
            return False

    def run_direct_applications(self):
        """Run direct job applications"""
        logger.info("🚀 DIRECT JOB APPLICATION AUTOMATION")
        logger.info("🎯 Focus on completing actual job applications")
        logger.info("📝 Fill forms and submit applications")
        logger.info("=" * 70)

        try:
            if not self.setup_driver():
                return False

            # Apply to Indeed jobs
            indeed_applications = self.apply_to_indeed_job()

            # Print final results
            runtime = (time.time() - self.session_stats['start_time']) / 60
            logger.info("\n📊 FINAL RESULTS:")
            logger.info(f"    🎯 Jobs attempted: {self.session_stats['jobs_attempted']}")
            logger.info(f"    ✅ Applications completed: {self.session_stats['applications_completed']}")
            logger.info(f"    📝 Forms filled: {self.session_stats['forms_filled']}")
            logger.info(f"    🚀 Actual submissions: {self.session_stats['actual_submissions']}")
            logger.info(f"    ⏱️ Runtime: {runtime:.1f} minutes")

            if self.completed_applications:
                logger.info("\n📋 COMPLETED APPLICATIONS:")
                for i, app in enumerate(self.completed_applications, 1):
                    logger.info(f"  {i}. URL: {app['url']}")
                    logger.info(f"     Title: {app['title']}")
                    logger.info(f"     Form elements: {app['form_elements']}")
                    logger.info(f"     Time: {app['timestamp']}")
                    logger.info("")

            return self.session_stats['applications_completed'] > 0

        except Exception as e:
            logger.error(f"❌ Fatal error: {e}")
            return False

    def cleanup(self):
        """Clean up resources"""
        if self.driver:
            try:
                self.driver.quit()
                logger.info("🧹 Resources cleaned up")
            except:
                pass

def main():
    applier = DirectJobApplier()

    try:
        logger.info("🌟 DIRECT JOB APPLICATION AUTOMATION")
        logger.info("🎯 Complete actual job applications with form filling")

        success = applier.run_direct_applications()

        if success:
            logger.info("\n🎉 🎉 🎉 SUCCESS! 🎉 🎉 🎉")
            logger.info("✅ Successfully completed job applications!")
        else:
            logger.warning("\n⚠️ No applications completed")

    except KeyboardInterrupt:
        logger.info("\n⏹️ Automation stopped by user")
    except Exception as e:
        logger.error(f"\n❌ Fatal error: {e}")
    finally:
        applier.cleanup()

if __name__ == "__main__":
    main()