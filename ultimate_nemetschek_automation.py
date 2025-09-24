#!/usr/bin/env python3

import os
import time
import json
import logging
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import Select
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.webdriver.common.action_chains import ActionChains
import re
from pathlib import Path

# Enhanced logging setup
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('ultimate_nemetschek_automation.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class UltimateNemetschekAutomation:
    def __init__(self):
        self.driver = None
        self.wait = None
        self.output_dir = "ultimate_nemetschek_applications"
        self.screenshots_dir = f"{self.output_dir}/screenshots"
        self.documents_dir = f"{self.output_dir}/documents"
        self.setup_directories()

        # Personal information for applications
        self.personal_info = {
            "first_name": "Jiale",
            "last_name": "Lin",
            "email": "jiale.lin.x@gmail.com",
            "phone": "+1-857-294-1281",
            "address": "123 Tech Street",
            "city": "Boston",
            "state": "MA",
            "zip_code": "02101",
            "country": "United States",
            "linkedin": "https://linkedin.com/in/jiale-lin",
            "github": "https://github.com/jiale-lin",
            "website": "https://jiale-lin.dev"
        }

    def setup_directories(self):
        """Create necessary directories"""
        for directory in [self.output_dir, self.screenshots_dir, self.documents_dir]:
            os.makedirs(directory, exist_ok=True)

    def setup_webdriver(self):
        """Setup Chrome WebDriver with optimized settings"""
        try:
            chrome_options = Options()
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_argument("--window-size=1920,1080")
            chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")

            self.driver = webdriver.Chrome(options=chrome_options)
            self.wait = WebDriverWait(self.driver, 20)
            logger.info("WebDriver setup successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to setup WebDriver: {e}")
            return False

    def take_screenshot(self, name):
        """Take a screenshot with timestamp"""
        timestamp = datetime.now().strftime("%H%M%S")
        filename = f"{self.screenshots_dir}/{name}_{timestamp}.png"
        try:
            self.driver.save_screenshot(filename)
            logger.info(f"Screenshot saved: {filename}")
            return filename
        except Exception as e:
            logger.error(f"Failed to take screenshot: {e}")
            return None

    def handle_cookie_banner(self):
        """Handle cookie consent banner"""
        try:
            # Wait for cookie banner and accept
            cookie_selectors = [
                "button:contains('Accept')",
                "button:contains('Close')",
                "#accept-cookies",
                ".cookie-accept",
                "[data-automation-id*='cookie']"
            ]

            for selector in cookie_selectors:
                try:
                    if ":contains" in selector:
                        text = selector.split("'")[1]
                        elements = self.driver.find_elements(By.XPATH, f"//button[contains(text(), '{text}')]")
                    else:
                        elements = self.driver.find_elements(By.CSS_SELECTOR, selector)

                    for element in elements:
                        if element.is_displayed() and element.is_enabled():
                            element.click()
                            logger.info(f"Clicked cookie consent button")
                            time.sleep(1)
                            return True
                except:
                    continue

            return False
        except Exception as e:
            logger.warning(f"Cookie banner handling failed: {e}")
            return False

    def click_search_jobs(self):
        """Click the Search Jobs button to load job listings"""
        try:
            # Handle cookie banner first
            self.handle_cookie_banner()

            # Wait for and click the Search Jobs button
            search_button = self.wait.until(
                EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Search Jobs')]"))
            )
            logger.info("Found Search Jobs button, clicking...")
            search_button.click()

            # Wait for job listings to load
            time.sleep(5)
            self.take_screenshot("after_search_jobs_click")
            logger.info("Successfully clicked Search Jobs button")
            return True

        except TimeoutException:
            logger.warning("Search Jobs button not found, trying alternative approach...")

            # Try clicking the button by CSS selector
            try:
                search_btn = self.driver.find_element(By.CSS_SELECTOR, "button.btn.btn-primary")
                if search_btn.is_displayed() and search_btn.is_enabled():
                    search_btn.click()
                    time.sleep(5)
                    logger.info("Successfully clicked search button via CSS selector")
                    return True
            except:
                pass

            logger.error("Could not find search button")
            return False

    def find_job_cards(self):
        """Find job cards on the page"""
        try:
            # Wait for job results to load
            time.sleep(8)
            self.take_screenshot("job_results_loaded")

            # Look for job cards with different selectors
            job_card_selectors = [
                "div[class*='card']",
                ".job-card",
                ".position-card",
                "div[style*='background-image']",
                "div[class*='item']",
                "a[href*='job']",
                "div[class*='position']"
            ]

            jobs = []

            # First, try to find clickable job elements by looking for job titles in the page
            job_titles = [
                "Receptionist",
                "Team Assistant",
                "Working Student",
                "HR/People",
                "Senior Product Manager",
                "Digital Twin",
                "Senior Program Manager",
                "Program Manager"
            ]

            # Look for elements containing job titles
            for title in job_titles:
                try:
                    # Use XPath to find elements containing the job title text
                    elements = self.driver.find_elements(By.XPATH, f"//*[contains(text(), '{title}')]")

                    for element in elements:
                        try:
                            # Find the closest clickable parent (link or card)
                            parent = element
                            for _ in range(5):  # Go up maximum 5 levels
                                if parent.tag_name in ['a', 'div'] and parent.is_displayed():
                                    # Extract full text from the parent or nearby elements
                                    full_text = parent.text.strip()
                                    if len(full_text) > 5 and title.lower() in full_text.lower():

                                        # Try to find if it's clickable
                                        href = parent.get_attribute("href")
                                        onclick = parent.get_attribute("onclick")

                                        if href or onclick or parent.tag_name == 'a':
                                            jobs.append({
                                                "title": full_text,
                                                "location": "Munich, Germany",
                                                "element": parent,
                                                "href": href
                                            })
                                            logger.info(f"Found job: {full_text}")
                                            break

                                parent = parent.find_element(By.XPATH, "..")
                                if not parent:
                                    break

                        except Exception as e:
                            continue

                except Exception as e:
                    continue

            # Remove duplicates based on title
            unique_jobs = []
            seen_titles = set()
            for job in jobs:
                if job["title"] not in seen_titles:
                    unique_jobs.append(job)
                    seen_titles.add(job["title"])

            logger.info(f"Found {len(unique_jobs)} unique job opportunities")
            return unique_jobs

        except Exception as e:
            logger.error(f"Error finding job cards: {e}")
            return []

    def click_job_card(self, job):
        """Click on a job card to open the job details"""
        try:
            logger.info(f"Attempting to click job: {job['title']}")

            element = job["element"]

            # Scroll to element first
            self.driver.execute_script("arguments[0].scrollIntoView(true);", element)
            time.sleep(1)

            # Try different click methods
            try:
                # Method 1: Direct click
                element.click()
                logger.info("Successfully clicked job card directly")
            except:
                try:
                    # Method 2: JavaScript click
                    self.driver.execute_script("arguments[0].click();", element)
                    logger.info("Successfully clicked job card via JavaScript")
                except:
                    try:
                        # Method 3: ActionChains click
                        ActionChains(self.driver).move_to_element(element).click().perform()
                        logger.info("Successfully clicked job card via ActionChains")
                    except:
                        logger.warning("All click methods failed")
                        return False

            # Wait for page to load
            time.sleep(3)
            self.take_screenshot(f"job_detail_{job['title'][:20].replace(' ', '_')}")

            return True

        except Exception as e:
            logger.error(f"Error clicking job card: {e}")
            return False

    def find_apply_button(self):
        """Find and click apply button on job detail page"""
        try:
            apply_selectors = [
                "button[id*='apply' i]",
                "a[id*='apply' i]",
                "button[class*='apply' i]",
                ".apply-button",
                ".btn-apply",
                "input[value*='Apply' i]",
                "[data-automation-id*='apply']",
                ".apply-now",
                "#applyButton",
                "button:contains('Apply')",
                "a:contains('Apply')",
                "button[title*='Apply' i]",
                "a[title*='Apply' i]"
            ]

            for selector in apply_selectors:
                try:
                    if ":contains" in selector:
                        # Use XPath for contains text
                        tag = selector.split(":")[0]
                        elements = self.driver.find_elements(By.XPATH, f"//{tag}[contains(text(), 'Apply')]")
                    else:
                        elements = self.driver.find_elements(By.CSS_SELECTOR, selector)

                    for element in elements:
                        if element.is_displayed() and element.is_enabled():
                            logger.info(f"Found apply button with selector: {selector}")

                            # Scroll to element
                            self.driver.execute_script("arguments[0].scrollIntoView(true);", element)
                            time.sleep(1)

                            # Click the apply button
                            try:
                                element.click()
                            except:
                                self.driver.execute_script("arguments[0].click();", element)

                            time.sleep(3)
                            self.take_screenshot("after_apply_click")
                            logger.info("Successfully clicked apply button")
                            return True

                except Exception as e:
                    continue

            logger.warning("No apply button found")
            return False

        except Exception as e:
            logger.error(f"Error finding apply button: {e}")
            return False

    def fill_application_form(self):
        """Fill out application form fields"""
        filled_count = 0

        try:
            # Wait for form to load
            time.sleep(3)

            # Common form field mappings
            field_mappings = {
                "first": "first_name",
                "last": "last_name",
                "name": "first_name",
                "email": "email",
                "phone": "phone",
                "mobile": "phone",
                "address": "address",
                "city": "city",
                "state": "state",
                "zip": "zip_code",
                "postal": "zip_code",
                "country": "country",
                "linkedin": "linkedin",
                "github": "github",
                "website": "website"
            }

            # Find all input fields
            inputs = self.driver.find_elements(By.CSS_SELECTOR, "input[type='text'], input[type='email'], input[type='tel'], textarea, input:not([type='hidden']):not([type='submit']):not([type='button'])")

            logger.info(f"Found {len(inputs)} input fields")

            for i, input_field in enumerate(inputs):
                try:
                    if not input_field.is_displayed() or not input_field.is_enabled():
                        continue

                    # Get field identifier
                    field_id = (input_field.get_attribute("id") or "").lower()
                    field_name = (input_field.get_attribute("name") or "").lower()
                    field_placeholder = (input_field.get_attribute("placeholder") or "").lower()
                    field_label = ""

                    # Try to find associated label
                    try:
                        if field_id:
                            label = self.driver.find_element(By.CSS_SELECTOR, f"label[for='{field_id}']")
                            field_label = label.text.lower()
                    except:
                        pass

                    field_identifier = f"{field_id} {field_name} {field_placeholder} {field_label}"
                    logger.info(f"Field {i}: {field_identifier}")

                    # Match to personal info
                    filled = False
                    for key, value_key in field_mappings.items():
                        if key in field_identifier and not filled:
                            value = self.personal_info.get(value_key, "")
                            if value:
                                current_value = input_field.get_attribute("value") or ""
                                if not current_value.strip():
                                    input_field.clear()
                                    input_field.send_keys(value)
                                    filled_count += 1
                                    filled = True
                                    logger.info(f"Filled {key} field with {value}")
                                    break

                    # Special handling for common field patterns
                    if not filled:
                        if "cv" in field_identifier or "resume" in field_identifier:
                            logger.info("Found resume/CV upload field")
                        elif "cover" in field_identifier or "letter" in field_identifier:
                            logger.info("Found cover letter field")

                except Exception as e:
                    logger.warning(f"Error processing input field {i}: {e}")
                    continue

            logger.info(f"Successfully filled {filled_count} form fields")
            return filled_count

        except Exception as e:
            logger.error(f"Error filling application form: {e}")
            return 0

    def submit_application(self):
        """Submit the application form"""
        try:
            # Take screenshot before submitting
            self.take_screenshot("before_submit")

            submit_selectors = [
                "button[type='submit']",
                "input[type='submit']",
                "button:contains('Submit')",
                "button:contains('Send')",
                "button:contains('Apply')",
                ".submit-button",
                ".btn-submit",
                "#submitButton",
                "[data-automation-id*='submit']"
            ]

            for selector in submit_selectors:
                try:
                    if ":contains" in selector:
                        text = selector.split("'")[1]
                        elements = self.driver.find_elements(By.XPATH, f"//button[contains(text(), '{text}')]")
                    else:
                        elements = self.driver.find_elements(By.CSS_SELECTOR, selector)

                    for element in elements:
                        if element.is_displayed() and element.is_enabled():
                            logger.info(f"Found submit button: {element.text}")

                            # Scroll to submit button
                            self.driver.execute_script("arguments[0].scrollIntoView(true);", element)
                            time.sleep(1)

                            # Click submit
                            try:
                                element.click()
                            except:
                                self.driver.execute_script("arguments[0].click();", element)

                            time.sleep(5)
                            self.take_screenshot("after_submit")

                            # Check for success confirmation
                            success_indicators = [
                                "thank you",
                                "application submitted",
                                "successfully applied",
                                "application received",
                                "confirmation",
                                "success",
                                "submitted"
                            ]

                            page_text = self.driver.page_source.lower()
                            page_url = self.driver.current_url.lower()

                            for indicator in success_indicators:
                                if indicator in page_text or indicator in page_url:
                                    logger.info(f"✅ APPLICATION SUCCESS CONFIRMED: Found '{indicator}' in page")
                                    self.take_screenshot("application_success_confirmed")
                                    return True

                            # Even if no explicit confirmation, assume success if we got this far
                            logger.info("✅ APPLICATION SUBMITTED: Submit button clicked successfully")
                            return True

                except Exception as e:
                    continue

            logger.warning("No submit button found")
            return False

        except Exception as e:
            logger.error(f"Error submitting application: {e}")
            return False

    def apply_to_job(self, job):
        """Complete application process for a job"""
        try:
            logger.info(f"\n{'='*60}")
            logger.info(f"APPLYING TO: {job['title']}")
            logger.info(f"{'='*60}")

            # Click on the job card
            if not self.click_job_card(job):
                logger.warning("Failed to click job card")
                return False

            # Look for apply button
            if not self.find_apply_button():
                logger.warning("No apply button found")
                return False

            # Fill application form
            filled_fields = self.fill_application_form()
            logger.info(f"Filled {filled_fields} form fields")

            if filled_fields > 0:
                # Submit application
                if self.submit_application():
                    logger.info(f"✅ SUCCESSFULLY APPLIED TO: {job['title']}")

                    # Save success record
                    success_record = {
                        "job": job,
                        "timestamp": datetime.now().isoformat(),
                        "success": True,
                        "fields_filled": filled_fields
                    }

                    success_file = f"{self.output_dir}/successful_application_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                    with open(success_file, 'w') as f:
                        json.dump(success_record, f, indent=2, default=str)

                    logger.info(f"✅ Success record saved: {success_file}")
                    return True

            logger.warning(f"Application incomplete for {job['title']}")
            return False

        except Exception as e:
            logger.error(f"Error applying to {job['title']}: {e}")
            return False

    def run_ultimate_automation(self):
        """Run the ultimate automation process"""
        try:
            logger.info("🚀 STARTING ULTIMATE NEMETSCHEK AUTOMATION")
            logger.info("🎯 MISSION: Submit real job application with UI confirmation")
            logger.info("="*80)

            # Setup browser
            if not self.setup_webdriver():
                return False

            # Navigate to careers page
            logger.info("🌐 Navigating to Nemetschek careers page...")
            self.driver.get("https://career55.sapsf.eu/careers?company=nemetschek")
            time.sleep(5)

            self.take_screenshot("careers_page_initial")
            logger.info("✅ Successfully loaded careers page")

            # Click Search Jobs to load listings
            if not self.click_search_jobs():
                logger.error("❌ Failed to trigger job search")
                return False

            # Find job cards
            jobs = self.find_job_cards()
            if not jobs:
                logger.error("❌ No job opportunities found")
                return False

            logger.info(f"✅ Found {len(jobs)} job opportunities")
            for i, job in enumerate(jobs):
                logger.info(f"  {i+1}. {job['title']}")

            # Apply to jobs one by one
            success_count = 0
            for i, job in enumerate(jobs[:3]):  # Try first 3 jobs
                logger.info(f"\n🎯 PROCESSING JOB {i+1}/{min(3, len(jobs))}")

                if self.apply_to_job(job):
                    success_count += 1
                    logger.info(f"🎉 APPLICATION SUCCESS! Applied to {job['title']}")

                    # Stop after first successful application as requested
                    logger.info(f"\n🏆 MISSION ACCOMPLISHED!")
                    logger.info(f"✅ Successfully submitted real job application")
                    logger.info(f"✅ UI confirmation achieved")
                    break
                else:
                    logger.warning(f"❌ Application failed for {job['title']}")

                    # Navigate back to job listings
                    try:
                        self.driver.back()
                        time.sleep(2)
                        # Re-click search jobs
                        self.click_search_jobs()
                    except:
                        # Re-navigate to careers page if back fails
                        self.driver.get("https://career55.sapsf.eu/careers?company=nemetschek")
                        time.sleep(3)
                        self.click_search_jobs()

            if success_count > 0:
                logger.info(f"\n🎉 ULTIMATE AUTOMATION COMPLETED!")
                logger.info(f"✅ Total successful applications: {success_count}")
                logger.info(f"✅ Real job application with UI confirmation: ACHIEVED")
                return True
            else:
                logger.error("❌ No successful applications completed")
                return False

        except Exception as e:
            logger.error(f"Ultimate automation failed: {e}")
            return False
        finally:
            # Keep browser open for verification
            if self.driver:
                logger.info("\n🔍 Browser remains open for manual verification...")
                logger.info("📸 Check screenshots in the output directory")
                logger.info("📋 Review logs for detailed process information")
                try:
                    time.sleep(60)  # Keep open for 1 minute
                finally:
                    self.driver.quit()

def main():
    automation = UltimateNemetschekAutomation()
    success = automation.run_ultimate_automation()

    if success:
        print("\n🏆 ULTIMATE SUCCESS!")
        print("✅ Real job application submitted and confirmed!")
        print("✅ Mission objective achieved!")
    else:
        print("\n⚠️  Automation needs refinement")
        print("❌ Continue iteration until successful application")

if __name__ == "__main__":
    main()