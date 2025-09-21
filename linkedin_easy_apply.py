#!/usr/bin/env python3
"""
LinkedIn Easy Apply Automation
Direct automation to apply to LinkedIn Easy Apply jobs
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
        logging.FileHandler('linkedin_easy_apply.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class LinkedInEasyApply:
    def __init__(self):
        """Initialize LinkedIn Easy Apply automation"""
        self.driver = None
        self.applications_submitted = 0
        self.session_id = datetime.now().strftime('%Y%m%d_%H%M%S')

    def setup_driver(self):
        """Setup Chrome WebDriver"""
        try:
            chrome_options = Options()
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--disable-blink-features=AutomationControlled')
            chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
            chrome_options.add_experimental_option('useAutomationExtension', False)

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
            element.click()
            return True
        except ElementClickInterceptedException:
            try:
                self.driver.execute_script("arguments[0].click();", element)
                return True
            except:
                return False

    def apply_to_jobs(self):
        """Apply to LinkedIn Easy Apply jobs"""
        try:
            logger.info("🎯 Starting LinkedIn Easy Apply automation")

            # Go to LinkedIn jobs with Easy Apply filter
            url = "https://www.linkedin.com/jobs/search/?f_AL=true&keywords=software%20engineer&location=San%20Jose%2C%20CA"
            self.driver.get(url)
            self.wait_random(5, 8)

            applications = 0

            # Scroll to load more jobs
            for i in range(3):
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                self.wait_random(2, 3)

            # Find Easy Apply buttons
            easy_apply_selectors = [
                "button[aria-label*='Easy Apply']",
                ".jobs-apply-button",
                "button:contains('Easy Apply')"
            ]

            apply_buttons = []
            for selector in easy_apply_selectors:
                buttons = self.driver.find_elements(By.CSS_SELECTOR, selector)
                apply_buttons.extend([btn for btn in buttons if btn.is_displayed()])

            logger.info(f"📝 Found {len(apply_buttons)} Easy Apply jobs")

            for i, button in enumerate(apply_buttons[:5]):  # Limit to 5 applications
                try:
                    logger.info(f"🎯 Applying to job {i+1}")

                    # Scroll to button
                    self.driver.execute_script("arguments[0].scrollIntoView(true);", button)
                    self.wait_random(1, 2)

                    # Click Easy Apply button
                    if self.safe_click(button):
                        self.wait_random(3, 5)

                        # Complete the application
                        if self.complete_easy_apply_form():
                            applications += 1
                            logger.info(f"✅ Successfully applied to job {i+1}")
                        else:
                            logger.warning(f"⚠️ Failed to complete application for job {i+1}")

                        # Close any open modal
                        self.close_modal()
                        self.wait_random(2, 3)

                except Exception as e:
                    logger.error(f"❌ Error applying to job {i+1}: {e}")
                    continue

            logger.info(f"🎉 Applications completed: {applications}")
            return applications

        except Exception as e:
            logger.error(f"❌ LinkedIn automation failed: {e}")
            return 0

    def complete_easy_apply_form(self):
        """Complete Easy Apply form"""
        try:
            max_steps = 5

            for step in range(max_steps):
                logger.info(f"📝 Processing form step {step + 1}")

                # Fill phone number if requested
                phone_inputs = self.driver.find_elements(By.CSS_SELECTOR,
                    "input[name*='phoneNumber'], input[id*='phone'], input[aria-label*='phone']")
                for phone_input in phone_inputs:
                    if phone_input.is_displayed() and phone_input.is_enabled():
                        phone_input.clear()
                        phone_input.send_keys("+1-555-123-4567")
                        logger.info("📞 Filled phone number")
                        break

                # Fill cover letter/message
                message_areas = self.driver.find_elements(By.CSS_SELECTOR,
                    "textarea[name*='message'], textarea[aria-label*='cover'], textarea[id*='coverLetter']")
                for textarea in message_areas:
                    if textarea.is_displayed() and textarea.is_enabled():
                        textarea.clear()
                        textarea.send_keys("I am very interested in this position and believe my experience would be a great fit for this role.")
                        logger.info("📝 Filled cover letter")
                        break

                # Handle any dropdown questions (select first option)
                dropdowns = self.driver.find_elements(By.CSS_SELECTOR, "select")
                for dropdown in dropdowns:
                    if dropdown.is_displayed() and dropdown.is_enabled():
                        options = dropdown.find_elements(By.TAG_NAME, "option")
                        if len(options) > 1:
                            options[1].click()  # Select first real option (not placeholder)
                            logger.info("📋 Selected dropdown option")

                # Fill text inputs with reasonable answers
                text_inputs = self.driver.find_elements(By.CSS_SELECTOR,
                    "input[type='text']:not([name*='name']):not([name*='email'])")
                for input_field in text_inputs:
                    if input_field.is_displayed() and input_field.is_enabled() and not input_field.get_attribute('value'):
                        input_field.send_keys("Yes")
                        logger.info("📝 Filled text input")

                # Look for action buttons
                button_selectors = [
                    "button[aria-label*='Submit application']",
                    "button[aria-label*='Review your application']",
                    "button[aria-label*='Continue to next step']",
                    "button:contains('Submit application')",
                    "button:contains('Review')",
                    "button:contains('Next')"
                ]

                action_button = None
                for selector in button_selectors:
                    buttons = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    for btn in buttons:
                        if btn.is_displayed() and btn.is_enabled():
                            action_button = btn
                            break
                    if action_button:
                        break

                if action_button:
                    button_text = action_button.text.lower()
                    aria_label = action_button.get_attribute('aria-label') or ''

                    if 'submit' in button_text or 'submit' in aria_label.lower():
                        # This is the final submit button
                        if self.safe_click(action_button):
                            self.wait_random(3, 5)
                            logger.info("✅ Application submitted!")
                            return True
                    elif 'next' in button_text or 'continue' in button_text or 'review' in button_text:
                        # Continue to next step
                        if self.safe_click(action_button):
                            self.wait_random(2, 3)
                            continue
                        else:
                            break
                else:
                    logger.warning("⚠️ No action button found")
                    break

            return False

        except Exception as e:
            logger.error(f"❌ Form completion failed: {e}")
            return False

    def close_modal(self):
        """Close any open modal dialogs"""
        try:
            close_selectors = [
                "button[aria-label*='Dismiss']",
                "button[aria-label*='Close']",
                ".artdeco-modal__dismiss",
                "button:contains('×')"
            ]

            for selector in close_selectors:
                close_buttons = self.driver.find_elements(By.CSS_SELECTOR, selector)
                for btn in close_buttons:
                    if btn.is_displayed():
                        self.safe_click(btn)
                        self.wait_random(1, 2)
                        break

        except Exception as e:
            pass

    def run(self):
        """Run the automation"""
        try:
            logger.info("🚀 LINKEDIN EASY APPLY AUTOMATION")
            logger.info("🎯 Applying to real LinkedIn jobs")
            logger.info("================================================================================")

            if not self.setup_driver():
                return

            applications = self.apply_to_jobs()

            logger.info("================================================================================")
            if applications > 0:
                logger.info(f"🎉 SUCCESS! {applications} job applications submitted")
            else:
                logger.warning("⚠️ No applications were submitted")

        except Exception as e:
            logger.error(f"❌ Automation failed: {e}")
        finally:
            if self.driver:
                input("Press Enter to close browser...")
                self.driver.quit()

if __name__ == "__main__":
    automation = LinkedInEasyApply()
    automation.run()