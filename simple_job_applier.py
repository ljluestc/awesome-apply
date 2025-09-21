#!/usr/bin/env python3
"""
Simple Job Applier - Working automation with valid CSS selectors
Actually apply to real jobs with simple, reliable selectors
"""

import sys
import time
import logging
import random
from datetime import datetime

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

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('simple_job_applier.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class SimpleJobApplier:
    def __init__(self):
        """Initialize simple job applier"""
        self.driver = None
        self.applications_submitted = 0

    def setup_driver(self):
        """Setup Chrome WebDriver"""
        try:
            chrome_options = Options()
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')

            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            self.driver.set_window_size(1920, 1080)
            self.wait = WebDriverWait(self.driver, 10)

            logger.info("✅ WebDriver setup successfully")
            return True

        except Exception as e:
            logger.error(f"❌ WebDriver setup failed: {e}")
            return False

    def wait_random(self, min_sec=2, max_sec=4):
        """Random wait"""
        time.sleep(random.uniform(min_sec, max_sec))

    def safe_click(self, element):
        """Safely click element"""
        try:
            self.driver.execute_script("arguments[0].scrollIntoView(true);", element)
            self.wait_random(1, 2)
            element.click()
            return True
        except:
            try:
                self.driver.execute_script("arguments[0].click();", element)
                return True
            except:
                return False

    def apply_to_indeed_jobs(self):
        """Apply to Indeed jobs"""
        try:
            logger.info("🎯 Applying to Indeed jobs...")

            # Go to Indeed with software engineer jobs
            self.driver.get("https://indeed.com/jobs?q=software+engineer&l=San+Jose%2C+CA")
            self.wait_random(5, 8)

            applications = 0

            # Find job listings (simple selector)
            job_links = self.driver.find_elements(By.CSS_SELECTOR, "h2 a")
            logger.info(f"📝 Found {len(job_links)} job links")

            for i, link in enumerate(job_links[:5]):  # Limit to first 5
                try:
                    logger.info(f"🎯 Processing job {i+1}")

                    # Click on job link
                    if self.safe_click(link):
                        self.wait_random(3, 5)

                        # Look for apply button (simple selectors)
                        apply_selectors = [
                            "button[aria-label*='Apply']",
                            "a[aria-label*='Apply']",
                            ".indeedApplyButton",
                            ".jobsearch-ApplyButton"
                        ]

                        apply_button = None
                        for selector in apply_selectors:
                            try:
                                buttons = self.driver.find_elements(By.CSS_SELECTOR, selector)
                                for btn in buttons:
                                    if btn.is_displayed():
                                        apply_button = btn
                                        break
                                if apply_button:
                                    break
                            except:
                                continue

                        if apply_button:
                            logger.info(f"📝 Found apply button for job {i+1}")

                            if self.safe_click(apply_button):
                                self.wait_random(3, 5)

                                # Try to complete application
                                if self.complete_application_form():
                                    applications += 1
                                    logger.info(f"✅ Successfully applied to job {i+1}")
                                else:
                                    logger.warning(f"⚠️ Could not complete application for job {i+1}")
                        else:
                            logger.info(f"❌ No apply button found for job {i+1}")

                        self.wait_random(2, 3)

                except Exception as e:
                    logger.error(f"❌ Error processing job {i+1}: {e}")
                    continue

            return applications

        except Exception as e:
            logger.error(f"❌ Indeed automation failed: {e}")
            return 0

    def complete_application_form(self):
        """Complete application form with simple approach"""
        try:
            logger.info("📝 Completing application form...")

            # Fill simple form fields
            form_data = {
                "input[type='email']": "john.doe@example.com",
                "input[type='tel']": "+1-555-123-4567",
                "input[name*='name']": "John Doe",
                "textarea": "I am very interested in this position and believe I would be a great fit."
            }

            filled_fields = 0
            for selector, value in form_data.items():
                try:
                    fields = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    for field in fields:
                        if field.is_displayed() and field.is_enabled():
                            field.clear()
                            field.send_keys(value)
                            filled_fields += 1
                            logger.info(f"📝 Filled field: {selector}")
                            break
                except:
                    continue

            logger.info(f"📝 Filled {filled_fields} form fields")

            # Look for submit button
            submit_selectors = [
                "button[type='submit']",
                "input[type='submit']",
                "button[aria-label*='Submit']",
                "button[aria-label*='Apply']"
            ]

            for selector in submit_selectors:
                try:
                    buttons = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    for btn in buttons:
                        if btn.is_displayed() and btn.is_enabled():
                            if self.safe_click(btn):
                                self.wait_random(3, 5)
                                logger.info("✅ Application form submitted")
                                return True
                except:
                    continue

            logger.warning("⚠️ No submit button found")
            return False

        except Exception as e:
            logger.error(f"❌ Form completion failed: {e}")
            return False

    def run(self):
        """Run the automation"""
        try:
            logger.info("🚀 SIMPLE JOB APPLIER")
            logger.info("🎯 Applying to real jobs with reliable automation")
            logger.info("================================================================================")

            if not self.setup_driver():
                return

            # Apply to Indeed jobs
            applications = self.apply_to_indeed_jobs()

            logger.info("================================================================================")
            if applications > 0:
                logger.info(f"🎉 SUCCESS! {applications} job applications submitted")
            else:
                logger.warning("⚠️ No applications were submitted")

            logger.info("📱 Automation complete - check the browser for results")

        except Exception as e:
            logger.error(f"❌ Automation failed: {e}")
        finally:
            if self.driver:
                # Keep browser open to see results
                logger.info("🌐 Browser staying open - close manually when done")
                input("Press Enter to close...")
                self.driver.quit()

if __name__ == "__main__":
    automation = SimpleJobApplier()
    automation.run()