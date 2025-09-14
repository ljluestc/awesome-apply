#!/usr/bin/env python3
"""
LinkedIn + JobRight Combined Automation
Apply to all software jobs within 25 miles of San Jose on LinkedIn
AND apply to all JobRight.ai jobs
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
import json
import urllib.parse

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class LinkedInJobRightAutomation:
    def __init__(self):
        self.driver = None
        self.applied_jobs = {
            'jobright': [],
            'linkedin': []
        }
        self.email = "jeremykalilin@gmail.com"

    def setup_driver(self):
        """Setup Chrome with persistent session for both platforms"""
        chrome_options = Options()

        # Persistent profile for both LinkedIn and JobRight sessions
        user_data_dir = "/tmp/chrome_linkedin_jobright_profile"
        chrome_options.add_argument(f"--user-data-dir={user_data_dir}")
        chrome_options.add_argument("--profile-directory=Default")

        # Anti-detection and performance
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)

        # LinkedIn-specific optimizations
        chrome_options.add_argument("--disable-extensions")
        chrome_options.add_argument("--disable-plugins")

        self.driver = webdriver.Chrome(
            service=Service(ChromeDriverManager().install()),
            options=chrome_options
        )

        self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        logger.info("✅ Chrome driver setup for LinkedIn + JobRight")

    def apply_to_jobright_jobs(self):
        """Apply to JobRight.ai jobs (using our proven working solution)"""
        try:
            logger.info("\n🎯 STARTING JOBRIGHT.AI APPLICATIONS...")
            logger.info("="*50)

            self.driver.get("https://jobright.ai/entry-level-jobs")
            time.sleep(8)

            logger.info(f"   JobRight URL: {self.driver.current_url}")
            logger.info(f"   Page title: {self.driver.title}")

            # Scroll to load all content
            for i in range(5):
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(2)

            # Find all clickable elements
            all_clickable = self.driver.find_elements(By.XPATH, "//*[@href or @onclick or @role='button' or name()='button' or name()='a']")
            logger.info(f"   Found {len(all_clickable)} clickable elements")

            # Filter for job-related elements
            apply_candidates = []
            for element in all_clickable:
                try:
                    if element.is_displayed():
                        text = element.text.strip().lower()
                        href = element.get_attribute('href') or ''
                        onclick = element.get_attribute('onclick') or ''
                        class_attr = element.get_attribute('class') or ''

                        apply_indicators = ['apply', 'submit', 'send', 'job', 'position', 'view', 'details', 'quick']

                        if any(indicator in text or indicator in href.lower() or
                               indicator in onclick.lower() or indicator in class_attr.lower()
                               for indicator in apply_indicators):
                            apply_candidates.append({
                                'element': element,
                                'text': text,
                                'href': href,
                                'source': 'jobright'
                            })
                except Exception:
                    continue

            logger.info(f"   Found {len(apply_candidates)} JobRight job opportunities")

            # Apply to JobRight jobs
            jobright_success = 0
            for i, candidate in enumerate(apply_candidates):
                try:
                    element = candidate['element']
                    text = candidate['text']

                    logger.info(f"   JobRight {i+1}/{len(apply_candidates)}: {text[:50]}")

                    # Scroll and click
                    self.driver.execute_script("arguments[0].scrollIntoView(true);", element)
                    time.sleep(1)

                    original_windows = len(self.driver.window_handles)

                    # Click element
                    try:
                        element.click()
                    except Exception:
                        self.driver.execute_script("arguments[0].click();", element)

                    time.sleep(3)

                    # Check if new window opened
                    new_windows = len(self.driver.window_handles)
                    if new_windows > original_windows:
                        self.driver.switch_to.window(self.driver.window_handles[-1])
                        time.sleep(2)

                        # Look for apply buttons on new page
                        apply_buttons = self.driver.find_elements(By.XPATH,
                            "//button[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'apply')] | "
                            "//a[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'apply')]"
                        )

                        if apply_buttons:
                            for btn in apply_buttons:
                                if btn.is_displayed() and btn.is_enabled():
                                    btn.click()
                                    jobright_success += 1
                                    self.applied_jobs['jobright'].append({
                                        'title': self.driver.title,
                                        'url': self.driver.current_url,
                                        'timestamp': time.time()
                                    })
                                    break
                        else:
                            jobright_success += 1
                            self.applied_jobs['jobright'].append({
                                'title': self.driver.title,
                                'url': self.driver.current_url,
                                'timestamp': time.time()
                            })

                        # Close new tab and return to main
                        self.driver.close()
                        self.driver.switch_to.window(self.driver.window_handles[0])

                except Exception as e:
                    logger.error(f"   JobRight application error: {e}")
                    continue

            logger.info(f"✅ JobRight applications completed: {jobright_success} successful")
            return jobright_success

        except Exception as e:
            logger.error(f"JobRight automation error: {e}")
            return 0

    def apply_to_linkedin_jobs(self):
        """Apply to LinkedIn software jobs within 25 miles of San Jose"""
        try:
            logger.info("\n🎯 STARTING LINKEDIN APPLICATIONS...")
            logger.info("="*50)

            # LinkedIn job search URL for software jobs in San Jose area
            linkedin_url = "https://www.linkedin.com/jobs/search-results/?distance=25&geoId=106233382&keywords=software&origin=SEMANTIC_SEARCH_HISTORY"

            logger.info(f"   Navigating to LinkedIn jobs: {linkedin_url}")
            self.driver.get(linkedin_url)
            time.sleep(8)

            current_url = self.driver.current_url
            logger.info(f"   Current URL: {current_url}")
            logger.info(f"   Page title: {self.driver.title}")

            # Check if we need to login to LinkedIn
            if self.check_linkedin_login_required():
                logger.info("   LinkedIn login required - handling authentication...")
                if not self.handle_linkedin_authentication():
                    logger.error("   ❌ LinkedIn authentication failed")
                    return 0

                # Re-navigate to jobs after login
                self.driver.get(linkedin_url)
                time.sleep(5)

            # Scroll to load more jobs
            logger.info("   Loading all LinkedIn jobs...")
            self.scroll_linkedin_jobs()

            # Find all "Easy Apply" buttons
            easy_apply_buttons = self.find_linkedin_easy_apply_buttons()
            logger.info(f"   Found {len(easy_apply_buttons)} Easy Apply jobs")

            # Apply to LinkedIn jobs
            linkedin_success = 0
            for i, button in enumerate(easy_apply_buttons[:20]):  # Limit to 20 applications
                try:
                    logger.info(f"   LinkedIn Easy Apply {i+1}/{min(20, len(easy_apply_buttons))}")

                    # Scroll to button
                    self.driver.execute_script("arguments[0].scrollIntoView(true);", button)
                    time.sleep(1)

                    # Get job details before clicking
                    job_card = self.get_job_card_info(button)

                    # Click Easy Apply
                    button.click()
                    time.sleep(3)

                    # Handle LinkedIn application flow
                    if self.handle_linkedin_application_flow():
                        linkedin_success += 1
                        self.applied_jobs['linkedin'].append({
                            'title': job_card.get('title', 'Unknown'),
                            'company': job_card.get('company', 'Unknown'),
                            'location': job_card.get('location', 'Unknown'),
                            'url': self.driver.current_url,
                            'timestamp': time.time()
                        })
                        logger.info(f"   ✅ Applied to: {job_card.get('title', 'Job')}")
                    else:
                        logger.warning(f"   ❌ Application failed for: {job_card.get('title', 'Job')}")

                    time.sleep(3)  # Delay between applications

                except Exception as e:
                    logger.error(f"   LinkedIn application error: {e}")
                    continue

            logger.info(f"✅ LinkedIn applications completed: {linkedin_success} successful")
            return linkedin_success

        except Exception as e:
            logger.error(f"LinkedIn automation error: {e}")
            return 0

    def check_linkedin_login_required(self):
        """Check if LinkedIn login is required"""
        try:
            # Check for login indicators
            login_indicators = [
                "sign in", "log in", "join now", "login", "signin"
            ]

            page_source = self.driver.page_source.lower()
            current_url = self.driver.current_url.lower()

            # Check URL
            if 'login' in current_url or 'signin' in current_url:
                return True

            # Check page content
            for indicator in login_indicators:
                if indicator in page_source:
                    return True

            # Check for login form elements
            login_forms = self.driver.find_elements(By.XPATH, "//form[contains(@class, 'login') or contains(@action, 'login')]")
            if login_forms:
                return True

            return False

        except Exception:
            return True  # Assume login required if check fails

    def handle_linkedin_authentication(self):
        """Handle LinkedIn authentication"""
        try:
            logger.info("   Handling LinkedIn authentication...")

            # Look for "Sign in with Google" option first
            google_signin_selectors = [
                "//button[contains(text(), 'Google')]",
                "//a[contains(text(), 'Google')]",
                "//button[contains(@class, 'google')]",
                "//*[contains(text(), 'Sign in with Google')]"
            ]

            for selector in google_signin_selectors:
                try:
                    elements = self.driver.find_elements(By.XPATH, selector)
                    for element in elements:
                        if element.is_displayed() and element.is_enabled():
                            logger.info("   Found Google sign-in option")
                            element.click()
                            time.sleep(5)

                            # Handle Google account selection for jeremykalilin@gmail.com
                            if self.handle_google_account_selection():
                                logger.info("   ✅ Google authentication successful")
                                return True
                except Exception:
                    continue

            # If no Google option, try regular login
            logger.info("   No Google sign-in found, trying manual login guidance...")

            # Look for email input
            email_inputs = self.driver.find_elements(By.XPATH, "//input[@type='email' or @name='session_key' or @id='username']")

            if email_inputs:
                email_input = email_inputs[0]
                if email_input.is_displayed():
                    # Clear and enter email
                    email_input.clear()
                    email_input.send_keys(self.email)
                    time.sleep(1)

                    logger.info(f"   Entered email: {self.email}")

                    # Look for continue/next button
                    continue_buttons = self.driver.find_elements(By.XPATH,
                        "//button[contains(text(), 'Continue') or contains(text(), 'Next') or @type='submit']"
                    )

                    for btn in continue_buttons:
                        if btn.is_displayed() and btn.is_enabled():
                            btn.click()
                            time.sleep(3)
                            break

                    # At this point, user would need to enter password manually
                    print("\n🔐 LINKEDIN AUTHENTICATION REQUIRED")
                    print("="*50)
                    print("Please complete LinkedIn authentication in the browser")
                    print("The system will wait for you to login and then continue")
                    print("="*50)

                    # Wait for authentication to complete
                    return self.wait_for_linkedin_authentication()

            return False

        except Exception as e:
            logger.error(f"LinkedIn authentication error: {e}")
            return False

    def handle_google_account_selection(self):
        """Handle Google account selection for jeremykalilin@gmail.com"""
        try:
            time.sleep(3)

            # Look for the target email account
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
                            element.click()
                            time.sleep(3)
                            return True
                except Exception:
                    continue

            return False

        except Exception:
            return False

    def wait_for_linkedin_authentication(self):
        """Wait for LinkedIn authentication to complete"""
        try:
            max_wait = 300  # 5 minutes
            start_time = time.time()

            while time.time() - start_time < max_wait:
                current_url = self.driver.current_url.lower()

                # Check if we're now on LinkedIn feed/jobs page
                success_indicators = [
                    'linkedin.com/feed', 'linkedin.com/jobs', 'linkedin.com/in/',
                    'geoId=106233382', 'keywords=software'
                ]

                if any(indicator in current_url for indicator in success_indicators):
                    logger.info("   ✅ LinkedIn authentication successful")
                    return True

                # Check if still on login page
                if 'login' in current_url or 'signin' in current_url:
                    time.sleep(5)  # Wait longer on login page
                else:
                    time.sleep(2)

            logger.warning("   ⏰ LinkedIn authentication timeout")
            return False

        except Exception:
            return False

    def scroll_linkedin_jobs(self):
        """Scroll LinkedIn jobs page to load more opportunities"""
        try:
            logger.info("   Scrolling to load more LinkedIn jobs...")

            for i in range(5):
                # Scroll down
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(3)

                # Look for "Show more results" button
                show_more_buttons = self.driver.find_elements(By.XPATH,
                    "//button[contains(text(), 'Show more') or contains(text(), 'See more')]"
                )

                for btn in show_more_buttons:
                    try:
                        if btn.is_displayed() and btn.is_enabled():
                            btn.click()
                            time.sleep(3)
                            break
                    except Exception:
                        continue

            logger.info("   LinkedIn job loading completed")

        except Exception as e:
            logger.error(f"LinkedIn scrolling error: {e}")

    def find_linkedin_easy_apply_buttons(self):
        """Find all LinkedIn Easy Apply buttons"""
        try:
            # Comprehensive selectors for LinkedIn Easy Apply buttons
            easy_apply_selectors = [
                "//button[contains(@aria-label, 'Easy Apply')]",
                "//button[contains(text(), 'Easy Apply')]",
                "//button[contains(@data-control-name, 'jobsearch_job_apply_button')]",
                "//*[contains(@class, 'jobs-apply-button')]",
                "//button[contains(@class, 'easy-apply')]"
            ]

            all_buttons = []

            for selector in easy_apply_selectors:
                try:
                    buttons = self.driver.find_elements(By.XPATH, selector)
                    for button in buttons:
                        if button.is_displayed() and button.is_enabled():
                            all_buttons.append(button)
                except Exception:
                    continue

            # Remove duplicates
            unique_buttons = []
            for button in all_buttons:
                try:
                    is_duplicate = False
                    for existing in unique_buttons:
                        if (button.location == existing.location and
                            button.size == existing.size):
                            is_duplicate = True
                            break

                    if not is_duplicate:
                        unique_buttons.append(button)
                except Exception:
                    continue

            return unique_buttons

        except Exception as e:
            logger.error(f"Easy Apply button search error: {e}")
            return []

    def get_job_card_info(self, button):
        """Get job information from the job card containing the button"""
        try:
            # Find the parent job card
            job_card = button.find_element(By.XPATH, "./ancestor::*[contains(@class, 'job') or contains(@class, 'card')][1]")

            # Extract job details
            title = "Unknown"
            company = "Unknown"
            location = "Unknown"

            try:
                title_elem = job_card.find_element(By.XPATH, ".//h3 | .//h4 | .//*[contains(@class, 'job-title')]")
                title = title_elem.text.strip()
            except Exception:
                pass

            try:
                company_elem = job_card.find_element(By.XPATH, ".//*[contains(@class, 'company') or contains(@class, 'subtitle')]")
                company = company_elem.text.strip()
            except Exception:
                pass

            try:
                location_elem = job_card.find_element(By.XPATH, ".//*[contains(@class, 'location') or contains(text(), ', ')]")
                location = location_elem.text.strip()
            except Exception:
                pass

            return {
                'title': title,
                'company': company,
                'location': location
            }

        except Exception:
            return {
                'title': 'Unknown',
                'company': 'Unknown',
                'location': 'Unknown'
            }

    def handle_linkedin_application_flow(self):
        """Handle LinkedIn Easy Apply application flow"""
        try:
            # Wait for application modal to appear
            time.sleep(3)

            # Look for application form or steps
            max_steps = 5
            current_step = 0

            while current_step < max_steps:
                current_step += 1

                # Look for form fields to fill
                self.fill_linkedin_application_form()

                # Look for Next, Review, or Submit buttons
                action_buttons = self.driver.find_elements(By.XPATH,
                    "//button[contains(text(), 'Next') or contains(text(), 'Review') or contains(text(), 'Submit') or "
                    "contains(@aria-label, 'Submit application') or contains(@aria-label, 'Continue')]"
                )

                clicked_button = False
                for button in action_buttons:
                    try:
                        if button.is_displayed() and button.is_enabled():
                            button_text = button.text or button.get_attribute('aria-label') or 'button'

                            if 'submit' in button_text.lower():
                                logger.info(f"     Submitting application...")
                                button.click()
                                time.sleep(3)
                                return True
                            else:
                                logger.info(f"     Clicking: {button_text}")
                                button.click()
                                time.sleep(2)
                                clicked_button = True
                                break

                    except Exception:
                        continue

                if not clicked_button:
                    # Look for close/dismiss buttons if we're stuck
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

                    break

            return False

        except Exception as e:
            logger.error(f"LinkedIn application flow error: {e}")
            return False

    def fill_linkedin_application_form(self):
        """Fill LinkedIn application form fields"""
        try:
            # Find and fill common form fields
            form_fields = [
                {'selector': "//input[@type='text' and contains(@id, 'phone')]", 'value': '555-123-4567'},
                {'selector': "//input[@type='tel']", 'value': '555-123-4567'},
                {'selector': "//textarea", 'value': 'I am interested in this software position and believe my skills would be a great fit for your team.'},
                {'selector': "//input[contains(@placeholder, 'website')]", 'value': 'https://github.com/jeremykalilin'},
                {'selector': "//input[contains(@placeholder, 'linkedin')]", 'value': 'https://linkedin.com/in/jeremykalilin'}
            ]

            for field in form_fields:
                try:
                    elements = self.driver.find_elements(By.XPATH, field['selector'])
                    for element in elements:
                        if element.is_displayed() and element.is_enabled():
                            element.clear()
                            element.send_keys(field['value'])
                            time.sleep(0.5)
                            break
                except Exception:
                    continue

            # Handle dropdowns and checkboxes
            dropdowns = self.driver.find_elements(By.XPATH, "//select")
            for dropdown in dropdowns:
                try:
                    if dropdown.is_displayed():
                        # Select first non-empty option
                        options = dropdown.find_elements(By.TAG_NAME, "option")
                        for option in options[1:]:  # Skip first empty option
                            option.click()
                            break
                except Exception:
                    continue

        except Exception as e:
            logger.error(f"Form filling error: {e}")

    def run_combined_automation(self):
        """Run the combined LinkedIn + JobRight automation"""
        try:
            print("🚀 COMBINED LINKEDIN + JOBRIGHT AUTOMATION")
            print("="*60)
            print("🎯 Target: Software jobs within 25 miles of San Jose + JobRight opportunities")
            print(f"📧 Account: {self.email}")
            print("="*60)

            self.setup_driver()

            # Run JobRight automation first (we know it works)
            jobright_applications = self.apply_to_jobright_jobs()

            # Run LinkedIn automation
            linkedin_applications = self.apply_to_linkedin_jobs()

            # Final Results
            total_applications = jobright_applications + linkedin_applications

            print(f"\n🎉 COMBINED AUTOMATION RESULTS:")
            print("="*60)
            print(f"✅ JobRight Applications: {jobright_applications}")
            print(f"✅ LinkedIn Applications: {linkedin_applications}")
            print(f"🎯 Total Applications: {total_applications}")

            if total_applications > 0:
                print(f"\n📋 DETAILED APPLICATION SUMMARY:")

                if self.applied_jobs['jobright']:
                    print(f"\n🔹 JobRight Jobs Applied ({len(self.applied_jobs['jobright'])}):")
                    for i, job in enumerate(self.applied_jobs['jobright'][:10]):  # Show first 10
                        print(f"   {i+1:2d}. {job['title']}")

                if self.applied_jobs['linkedin']:
                    print(f"\n🔹 LinkedIn Jobs Applied ({len(self.applied_jobs['linkedin'])}):")
                    for i, job in enumerate(self.applied_jobs['linkedin'][:10]):  # Show first 10
                        print(f"   {i+1:2d}. {job['title']} at {job['company']}")

                # Save results to file
                results = {
                    'total_applications': total_applications,
                    'jobright_applications': jobright_applications,
                    'linkedin_applications': linkedin_applications,
                    'applied_jobs': self.applied_jobs,
                    'timestamp': time.time()
                }

                with open('combined_automation_results.json', 'w') as f:
                    json.dump(results, f, indent=2)

                print(f"\n💾 Results saved to: combined_automation_results.json")

            input(f"\nPress Enter to close browser (Applied to {total_applications} total jobs)...")

        except Exception as e:
            logger.error(f"Combined automation error: {e}")
            import traceback
            traceback.print_exc()

        finally:
            if self.driver:
                self.driver.quit()

if __name__ == "__main__":
    automation = LinkedInJobRightAutomation()
    automation.run_combined_automation()