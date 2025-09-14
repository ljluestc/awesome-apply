#!/usr/bin/env python3
"""
LinkedIn Job Search and Auto-Apply Automation
Searches for software jobs within 25 miles of San Jose, CA and applies automatically
"""

import time
import json
import logging
import re
import os
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import TimeoutException, NoSuchElementException, ElementClickInterceptedException, StaleElementReferenceException
from webdriver_manager.chrome import ChromeDriverManager
import urllib.parse

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('linkedin_automation.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class LinkedInJobAutomation:
    def __init__(self, headless=False):
        """Initialize LinkedIn job automation"""
        self.driver = None
        self.headless = headless
        self.session_id = datetime.now().strftime('%Y%m%d_%H%M%S')

        # LinkedIn search parameters (San Jose area, 25 miles, software keyword)
        self.search_params = {
            'keywords': 'software',
            'location': 'San Jose, California, United States',
            'geoId': '106233382',  # San Jose geoId
            'distance': '25'
        }

        # Job tracking
        self.job_applications = []
        self.successful_applications = []
        self.failed_applications = []
        self.seen_jobs = set()

        # Statistics
        self.stats = {
            'start_time': time.time(),
            'jobs_found': 0,
            'jobs_processed': 0,
            'applications_attempted': 0,
            'applications_successful': 0,
            'applications_failed': 0,
            'pages_processed': 0
        }

    def setup_driver(self):
        """Setup Chrome WebDriver for LinkedIn automation"""
        chrome_options = Options()

        if self.headless:
            chrome_options.add_argument("--headless")

        # Essential options for stability
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("--start-maximized")

        # Anti-detection measures
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        chrome_options.add_argument("--user-agent=Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")

        # Performance optimization
        chrome_options.add_argument("--disable-extensions")
        chrome_options.add_argument("--disable-plugins")
        chrome_options.add_argument("--disable-background-timer-throttling")

        try:
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=chrome_options)

            # Anti-detection JavaScript
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            self.driver.execute_cdp_cmd('Network.setUserAgentOverride', {
                "userAgent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            })

            # Set timeouts
            self.driver.implicitly_wait(10)
            self.driver.set_page_load_timeout(60)

            logger.info("Chrome WebDriver initialized successfully")
            return True

        except Exception as e:
            logger.error(f"Failed to initialize WebDriver: {e}")
            return False

    def authenticate_linkedin(self):
        """Handle LinkedIn authentication"""
        try:
            logger.info("Starting LinkedIn authentication...")

            # Try to access LinkedIn jobs page directly
            self.driver.get("https://www.linkedin.com/jobs/")
            time.sleep(5)

            current_url = self.driver.current_url.lower()

            # Check if we're already logged in
            if "/jobs/" in current_url and "login" not in current_url and "signin" not in current_url:
                logger.info("Already authenticated with LinkedIn")
                return True

            # Need to authenticate
            print("\n🔐 LINKEDIN AUTHENTICATION REQUIRED")
            print("="*60)
            print("Please log in to LinkedIn in the browser window that opened.")
            print("After logging in, navigate to the Jobs section.")
            print("Then return here and press Enter to continue.")
            print("="*60)

            # Wait for manual authentication
            while True:
                input("Press Enter after logging in and navigating to LinkedIn Jobs...")

                current_url = self.driver.current_url.lower()
                page_source = self.driver.page_source.lower()

                # Check if we're on a jobs page
                if ("/jobs/" in current_url or "jobs" in page_source) and "login" not in current_url:
                    logger.info("LinkedIn authentication successful")
                    return True
                else:
                    print("❌ Not yet on LinkedIn jobs page. Please ensure you're logged in and on the jobs page.")
                    retry = input("Try again? (y/n): ").strip().lower()
                    if retry != 'y':
                        return False

        except Exception as e:
            logger.error(f"LinkedIn authentication error: {e}")
            return False

    def build_search_url(self):
        """Build LinkedIn job search URL with parameters"""
        base_url = "https://www.linkedin.com/jobs/search"

        params = {
            'keywords': self.search_params['keywords'],
            'location': self.search_params['location'],
            'geoId': self.search_params['geoId'],
            'distance': self.search_params['distance'],
            'f_TPR': 'r86400',  # Last 24 hours (optional)
            'sortBy': 'DD',  # Sort by date
            'f_JT': 'F',  # Full-time (optional, can be removed for all job types)
        }

        # Build query string
        query_string = urllib.parse.urlencode(params)
        search_url = f"{base_url}?{query_string}"

        logger.info(f"Built search URL: {search_url}")
        return search_url

    def perform_job_search(self):
        """Perform LinkedIn job search"""
        try:
            search_url = self.build_search_url()
            logger.info(f"Navigating to LinkedIn job search: {search_url}")

            self.driver.get(search_url)
            time.sleep(5)

            # Wait for search results to load
            try:
                WebDriverWait(self.driver, 15).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, ".jobs-search-results-list"))
                )
                logger.info("Job search results loaded successfully")
                return True
            except TimeoutException:
                logger.warning("Job search results took too long to load, continuing anyway...")
                return True

        except Exception as e:
            logger.error(f"Error performing job search: {e}")
            return False

    def load_all_jobs(self):
        """Load all available jobs by scrolling and clicking 'See more jobs'"""
        try:
            logger.info("Loading all available jobs...")

            max_scroll_attempts = 20
            scroll_attempts = 0
            no_new_jobs_count = 0

            while scroll_attempts < max_scroll_attempts and no_new_jobs_count < 3:
                # Get current job count
                current_jobs = self.driver.find_elements(By.CSS_SELECTOR, ".job-card-container, .jobs-search-results__list-item")
                jobs_before = len(current_jobs)

                # Scroll to bottom
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(3)

                # Look for "See more jobs" button
                try:
                    see_more_buttons = self.driver.find_elements(By.CSS_SELECTOR,
                        "button[aria-label*='See more'], .infinite-scroller__show-more-button, .jobs-search-results-list__pagination button")

                    for button in see_more_buttons:
                        if button.is_displayed() and button.is_enabled():
                            try:
                                self.driver.execute_script("arguments[0].scrollIntoView();", button)
                                time.sleep(1)
                                button.click()
                                logger.info("Clicked 'See more jobs' button")
                                time.sleep(5)
                                break
                            except Exception as e:
                                logger.warning(f"Failed to click see more button: {e}")
                                continue

                except Exception as e:
                    logger.warning(f"Error looking for 'See more jobs' button: {e}")

                # Check if new jobs loaded
                current_jobs = self.driver.find_elements(By.CSS_SELECTOR, ".job-card-container, .jobs-search-results__list-item")
                jobs_after = len(current_jobs)

                if jobs_after > jobs_before:
                    logger.info(f"Loaded {jobs_after - jobs_before} more jobs (total: {jobs_after})")
                    no_new_jobs_count = 0
                else:
                    no_new_jobs_count += 1
                    logger.info(f"No new jobs loaded (attempt {no_new_jobs_count}/3)")

                scroll_attempts += 1

            logger.info(f"Finished loading jobs. Total scroll attempts: {scroll_attempts}")

        except Exception as e:
            logger.error(f"Error loading all jobs: {e}")

    def extract_job_listings(self):
        """Extract all job listings from the current page"""
        try:
            # Try multiple selectors for job cards
            job_selectors = [
                ".job-card-container",
                ".jobs-search-results__list-item",
                "[data-job-id]",
                ".job-card-list__entity-lockup"
            ]

            all_jobs = []

            for selector in job_selectors:
                jobs = self.driver.find_elements(By.CSS_SELECTOR, selector)
                if jobs:
                    logger.info(f"Found {len(jobs)} jobs using selector: {selector}")
                    all_jobs = jobs
                    break

            if not all_jobs:
                logger.warning("No job listings found with any selector")
                return []

            job_data = []

            for i, job_element in enumerate(all_jobs):
                try:
                    # Extract job information
                    job_info = self.extract_job_info(job_element, i)

                    if job_info and job_info['job_id'] not in self.seen_jobs:
                        job_data.append(job_info)
                        self.seen_jobs.add(job_info['job_id'])

                except Exception as e:
                    logger.warning(f"Error extracting job {i}: {e}")
                    continue

            self.stats['jobs_found'] = len(job_data)
            logger.info(f"Successfully extracted {len(job_data)} unique job listings")
            return job_data

        except Exception as e:
            logger.error(f"Error extracting job listings: {e}")
            return []

    def extract_job_info(self, job_element, index):
        """Extract information from a single job listing"""
        try:
            job_info = {
                'index': index,
                'job_id': None,
                'title': 'Unknown',
                'company': 'Unknown',
                'location': 'Unknown',
                'apply_link': None,
                'easy_apply': False,
                'element': job_element
            }

            # Extract job ID
            try:
                job_id = job_element.get_attribute('data-job-id')
                if not job_id:
                    # Try to extract from other attributes or child elements
                    job_link = job_element.find_element(By.CSS_SELECTOR, "a[href*='/jobs/view/']")
                    if job_link:
                        href = job_link.get_attribute('href')
                        job_id = href.split('/jobs/view/')[-1].split('?')[0]

                job_info['job_id'] = job_id or f"job_{index}_{int(time.time())}"

            except Exception:
                job_info['job_id'] = f"job_{index}_{int(time.time())}"

            # Extract job title
            try:
                title_selectors = [
                    ".job-card-list__title a",
                    ".job-card-container__link",
                    "h3 a",
                    "[data-target-job-title]",
                    ".job-title a"
                ]

                for selector in title_selectors:
                    try:
                        title_element = job_element.find_element(By.CSS_SELECTOR, selector)
                        job_info['title'] = title_element.text.strip()
                        job_info['apply_link'] = title_element.get_attribute('href')
                        break
                    except:
                        continue

            except Exception:
                pass

            # Extract company name
            try:
                company_selectors = [
                    ".job-card-container__primary-description",
                    ".job-card-list__company-name",
                    "[data-target-company-name]",
                    ".company-name"
                ]

                for selector in company_selectors:
                    try:
                        company_element = job_element.find_element(By.CSS_SELECTOR, selector)
                        job_info['company'] = company_element.text.strip()
                        break
                    except:
                        continue

            except Exception:
                pass

            # Extract location
            try:
                location_selectors = [
                    ".job-card-container__metadata-item",
                    ".job-card-list__location",
                    "[data-target-job-location]"
                ]

                for selector in location_selectors:
                    try:
                        location_element = job_element.find_element(By.CSS_SELECTOR, selector)
                        location_text = location_element.text.strip()
                        if location_text and not any(word in location_text.lower() for word in ['ago', 'applicant', 'promoted']):
                            job_info['location'] = location_text
                            break
                    except:
                        continue

            except Exception:
                pass

            # Check for Easy Apply button
            try:
                easy_apply_selectors = [
                    ".jobs-apply-button[data-is-easy-apply='true']",
                    "button[aria-label*='Easy Apply']",
                    ".easy-apply-button",
                    "button:contains('Easy Apply')"
                ]

                for selector in easy_apply_selectors:
                    try:
                        if selector.startswith("button:contains"):
                            # Use XPath for text-based search
                            easy_apply_element = job_element.find_element(By.XPATH, ".//button[contains(text(), 'Easy Apply')]")
                        else:
                            easy_apply_element = job_element.find_element(By.CSS_SELECTOR, selector)

                        if easy_apply_element and easy_apply_element.is_displayed():
                            job_info['easy_apply'] = True
                            break
                    except:
                        continue

            except Exception:
                pass

            return job_info

        except Exception as e:
            logger.warning(f"Error extracting job info for index {index}: {e}")
            return None

    def apply_to_job(self, job_info):
        """Apply to a single job"""
        try:
            logger.info(f"Attempting to apply to: {job_info['title']} at {job_info['company']}")

            # Click on the job to open details
            try:
                job_element = job_info['element']

                # Scroll to job element
                self.driver.execute_script("arguments[0].scrollIntoView();", job_element)
                time.sleep(2)

                # Click on the job listing
                job_element.click()
                time.sleep(3)

            except Exception as e:
                logger.warning(f"Failed to click job listing: {e}")
                # Try alternative method - navigate to apply link
                if job_info['apply_link']:
                    self.driver.get(job_info['apply_link'])
                    time.sleep(3)
                else:
                    return {'success': False, 'error': 'Could not access job listing'}

            # Look for Apply button
            apply_button = self.find_apply_button()

            if not apply_button:
                return {'success': False, 'error': 'No apply button found'}

            # Check if it's Easy Apply
            if self.is_easy_apply_button(apply_button):
                result = self.handle_easy_apply(apply_button, job_info)
            else:
                result = self.handle_external_apply(apply_button, job_info)

            return result

        except Exception as e:
            logger.error(f"Error applying to job {job_info.get('title', 'Unknown')}: {e}")
            return {'success': False, 'error': str(e)}

    def find_apply_button(self):
        """Find the apply button on the job page"""
        apply_button_selectors = [
            "button[aria-label*='Easy Apply']",
            ".jobs-apply-button",
            "button:contains('Easy Apply')",
            "button:contains('Apply')",
            ".apply-button",
            "a[aria-label*='Apply']",
            "[data-control-name='jobdetails_topcard_iapply']"
        ]

        for selector in apply_button_selectors:
            try:
                if "contains(" in selector:
                    # Convert to XPath
                    if "Easy Apply" in selector:
                        xpath_selector = "//button[contains(text(), 'Easy Apply')]"
                    else:
                        xpath_selector = "//button[contains(text(), 'Apply')]"

                    buttons = self.driver.find_elements(By.XPATH, xpath_selector)
                else:
                    buttons = self.driver.find_elements(By.CSS_SELECTOR, selector)

                for button in buttons:
                    if button.is_displayed() and button.is_enabled():
                        logger.info(f"Found apply button using selector: {selector}")
                        return button

            except Exception as e:
                logger.warning(f"Error with selector {selector}: {e}")
                continue

        return None

    def is_easy_apply_button(self, button):
        """Check if the button is an Easy Apply button"""
        try:
            button_text = button.text.lower()
            aria_label = button.get_attribute('aria-label') or ''

            easy_apply_indicators = ['easy apply', 'easyapply']

            return (any(indicator in button_text for indicator in easy_apply_indicators) or
                    any(indicator in aria_label.lower() for indicator in easy_apply_indicators) or
                    button.get_attribute('data-is-easy-apply') == 'true')

        except Exception:
            return False

    def handle_easy_apply(self, apply_button, job_info):
        """Handle Easy Apply process"""
        try:
            logger.info("Starting Easy Apply process")

            # Click Easy Apply button
            apply_button.click()
            time.sleep(3)

            # Handle the Easy Apply modal/form
            return self.process_easy_apply_form(job_info)

        except Exception as e:
            logger.error(f"Error in Easy Apply process: {e}")
            return {'success': False, 'error': f'Easy Apply error: {str(e)}'}

    def process_easy_apply_form(self, job_info):
        """Process the Easy Apply form through multiple steps"""
        try:
            max_steps = 5
            current_step = 1

            while current_step <= max_steps:
                logger.info(f"Processing Easy Apply step {current_step}")

                # Wait for modal to load
                time.sleep(2)

                # Check if we're done (success page or confirmation)
                if self.check_application_complete():
                    logger.info("Easy Apply completed successfully")
                    return {'success': True, 'method': 'easy_apply', 'steps': current_step}

                # Look for Next button
                next_button = self.find_next_button()

                if next_button:
                    try:
                        # Fill any required fields if present
                        self.fill_required_fields()

                        # Click Next
                        next_button.click()
                        time.sleep(2)
                        current_step += 1

                    except Exception as e:
                        logger.warning(f"Error clicking next button: {e}")
                        break
                else:
                    # Look for Submit/Apply button
                    submit_button = self.find_submit_button()

                    if submit_button:
                        try:
                            # Fill any required fields
                            self.fill_required_fields()

                            # Click Submit
                            submit_button.click()
                            time.sleep(3)

                            # Check if application was submitted
                            if self.check_application_complete():
                                logger.info("Easy Apply submitted successfully")
                                return {'success': True, 'method': 'easy_apply', 'steps': current_step}
                            else:
                                return {'success': False, 'error': 'Application submission unclear'}

                        except Exception as e:
                            logger.error(f"Error submitting application: {e}")
                            return {'success': False, 'error': f'Submission error: {str(e)}'}
                    else:
                        # No next or submit button found
                        logger.warning("No next or submit button found in Easy Apply form")
                        break

            return {'success': False, 'error': 'Easy Apply process exceeded maximum steps'}

        except Exception as e:
            logger.error(f"Error processing Easy Apply form: {e}")
            return {'success': False, 'error': f'Form processing error: {str(e)}'}

    def find_next_button(self):
        """Find the Next button in Easy Apply form"""
        next_button_selectors = [
            "button[aria-label*='Continue']",
            "button[aria-label*='Next']",
            "button:contains('Next')",
            "button:contains('Continue')",
            ".artdeco-button--primary:contains('Next')"
        ]

        for selector in next_button_selectors:
            try:
                if "contains(" in selector:
                    if "Next" in selector:
                        buttons = self.driver.find_elements(By.XPATH, "//button[contains(text(), 'Next')]")
                    else:
                        buttons = self.driver.find_elements(By.XPATH, "//button[contains(text(), 'Continue')]")
                else:
                    buttons = self.driver.find_elements(By.CSS_SELECTOR, selector)

                for button in buttons:
                    if button.is_displayed() and button.is_enabled():
                        return button

            except Exception:
                continue

        return None

    def find_submit_button(self):
        """Find the Submit/Apply button in Easy Apply form"""
        submit_button_selectors = [
            "button[aria-label*='Submit']",
            "button[aria-label*='Submit application']",
            "button:contains('Submit application')",
            "button:contains('Apply')",
            "button:contains('Submit')",
            ".artdeco-button--primary:contains('Submit')",
            ".artdeco-button--primary:contains('Apply')"
        ]

        for selector in submit_button_selectors:
            try:
                if "contains(" in selector:
                    if "Submit application" in selector:
                        buttons = self.driver.find_elements(By.XPATH, "//button[contains(text(), 'Submit application')]")
                    elif "Submit" in selector:
                        buttons = self.driver.find_elements(By.XPATH, "//button[contains(text(), 'Submit')]")
                    else:
                        buttons = self.driver.find_elements(By.XPATH, "//button[contains(text(), 'Apply')]")
                else:
                    buttons = self.driver.find_elements(By.CSS_SELECTOR, selector)

                for button in buttons:
                    if button.is_displayed() and button.is_enabled():
                        return button

            except Exception:
                continue

        return None

    def fill_required_fields(self):
        """Fill any required fields in the Easy Apply form"""
        try:
            # Look for required fields that need attention
            required_fields = self.driver.find_elements(By.CSS_SELECTOR, "input[required], select[required], textarea[required]")

            for field in required_fields:
                try:
                    if not field.get_attribute('value'):
                        field_type = field.get_attribute('type') or field.tag_name

                        # Handle different field types
                        if field_type == 'text':
                            # For text fields, try to determine what they're asking for
                            placeholder = field.get_attribute('placeholder') or ''
                            label = self.get_field_label(field)

                            # Basic field filling logic (extend as needed)
                            if any(word in (placeholder + label).lower() for word in ['phone', 'mobile']):
                                field.send_keys("(555) 123-4567")  # Generic phone number
                            elif 'website' in (placeholder + label).lower():
                                field.send_keys("https://linkedin.com/in/yourprofile")

                        elif field_type == 'select':
                            # For select fields, try to select a reasonable option
                            options = field.find_elements(By.TAG_NAME, 'option')
                            if len(options) > 1:
                                options[1].click()  # Select first non-empty option

                except Exception as e:
                    logger.warning(f"Could not fill required field: {e}")
                    continue

        except Exception as e:
            logger.warning(f"Error filling required fields: {e}")

    def get_field_label(self, field):
        """Get the label associated with a form field"""
        try:
            # Try to find associated label
            field_id = field.get_attribute('id')
            if field_id:
                label = self.driver.find_element(By.CSS_SELECTOR, f"label[for='{field_id}']")
                return label.text

            # Try to find parent label
            parent = field.find_element(By.XPATH, "./..")
            if parent.tag_name.lower() == 'label':
                return parent.text

            return ""

        except Exception:
            return ""

    def check_application_complete(self):
        """Check if the application has been completed successfully"""
        try:
            # Look for success indicators
            success_indicators = [
                "application submitted",
                "your application has been sent",
                "successfully applied",
                "application received",
                "thank you for applying"
            ]

            page_text = self.driver.page_source.lower()

            return any(indicator in page_text for indicator in success_indicators)

        except Exception:
            return False

    def handle_external_apply(self, apply_button, job_info):
        """Handle external apply process (opens company website)"""
        try:
            logger.info("Starting external apply process")

            # Get current window handle
            original_window = self.driver.current_window_handle

            # Click apply button (may open new tab/window)
            apply_button.click()
            time.sleep(5)

            # Check if new window/tab opened
            all_windows = self.driver.window_handles

            if len(all_windows) > 1:
                # Switch to new window
                new_window = [w for w in all_windows if w != original_window][0]
                self.driver.switch_to.window(new_window)

                new_url = self.driver.current_url
                logger.info(f"External apply opened new window: {new_url}")

                # Close the new window and return to original
                self.driver.close()
                self.driver.switch_to.window(original_window)

                return {
                    'success': True,
                    'method': 'external_apply',
                    'external_url': new_url,
                    'note': 'Opened external application page'
                }
            else:
                # Same window navigation
                new_url = self.driver.current_url
                logger.info(f"External apply navigated to: {new_url}")

                # Go back to job search
                self.driver.back()
                time.sleep(2)

                return {
                    'success': True,
                    'method': 'external_apply',
                    'external_url': new_url,
                    'note': 'Navigated to external application page'
                }

        except Exception as e:
            logger.error(f"Error in external apply process: {e}")
            return {'success': False, 'error': f'External apply error: {str(e)}'}

    def apply_to_all_jobs(self, job_listings):
        """Apply to all found jobs"""
        logger.info(f"Starting to apply to {len(job_listings)} jobs")

        for i, job_info in enumerate(job_listings, 1):
            print(f"\n{'='*80}")
            print(f"[{i}/{len(job_listings)}] APPLYING TO:")
            print(f"Title: {job_info['title']}")
            print(f"Company: {job_info['company']}")
            print(f"Location: {job_info['location']}")
            print(f"Easy Apply: {'Yes' if job_info['easy_apply'] else 'No'}")
            print(f"{'='*80}")

            try:
                result = self.apply_to_job(job_info)

                # Record result
                application_record = {
                    'job_info': job_info,
                    'result': result,
                    'timestamp': time.time(),
                    'applied_at': datetime.now().isoformat()
                }

                if result['success']:
                    self.successful_applications.append(application_record)
                    self.stats['applications_successful'] += 1
                    print(f"✅ SUCCESS: {result.get('note', result.get('method', 'Applied'))}")
                else:
                    self.failed_applications.append(application_record)
                    self.stats['applications_failed'] += 1
                    print(f"❌ FAILED: {result.get('error', 'Unknown error')}")

                self.stats['applications_attempted'] += 1

                # Wait between applications
                time.sleep(5)

            except Exception as e:
                error_record = {
                    'job_info': job_info,
                    'result': {'success': False, 'error': str(e)},
                    'timestamp': time.time(),
                    'applied_at': datetime.now().isoformat()
                }
                self.failed_applications.append(error_record)
                self.stats['applications_failed'] += 1
                print(f"❌ EXCEPTION: {str(e)}")
                continue

    def save_results(self):
        """Save automation results to files"""
        try:
            timestamp = self.session_id

            # Complete results
            complete_results = {
                'session_info': {
                    'session_id': self.session_id,
                    'timestamp': timestamp,
                    'search_params': self.search_params,
                    'duration_seconds': time.time() - self.stats['start_time']
                },
                'statistics': self.stats,
                'successful_applications': self.successful_applications,
                'failed_applications': self.failed_applications
            }

            # Save detailed results
            results_file = f'linkedin_automation_results_{timestamp}.json'
            with open(results_file, 'w', encoding='utf-8') as f:
                json.dump(complete_results, f, indent=2, default=str)

            # Save summary text file
            summary_file = f'linkedin_applied_jobs_{timestamp}.txt'
            with open(summary_file, 'w', encoding='utf-8') as f:
                f.write(f"LinkedIn Job Application Results\n")
                f.write(f"Session ID: {self.session_id}\n")
                f.write(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"Search: {self.search_params['keywords']} jobs in {self.search_params['location']}\n")
                f.write(f"{'='*60}\n\n")

                f.write(f"STATISTICS:\n")
                f.write(f"Jobs Found: {self.stats['jobs_found']}\n")
                f.write(f"Applications Attempted: {self.stats['applications_attempted']}\n")
                f.write(f"Successful Applications: {self.stats['applications_successful']}\n")
                f.write(f"Failed Applications: {self.stats['applications_failed']}\n")

                success_rate = (self.stats['applications_successful'] / self.stats['applications_attempted'] * 100) if self.stats['applications_attempted'] > 0 else 0
                f.write(f"Success Rate: {success_rate:.1f}%\n\n")

                f.write(f"SUCCESSFUL APPLICATIONS:\n")
                f.write(f"{'='*40}\n")
                for i, app in enumerate(self.successful_applications, 1):
                    job = app['job_info']
                    result = app['result']
                    f.write(f"{i:2d}. {job['title']} at {job['company']}\n")
                    f.write(f"    Method: {result.get('method', 'Unknown')}\n")
                    f.write(f"    Location: {job['location']}\n")
                    if result.get('external_url'):
                        f.write(f"    External URL: {result['external_url']}\n")
                    f.write(f"\n")

            logger.info(f"Results saved to {results_file} and {summary_file}")

        except Exception as e:
            logger.error(f"Error saving results: {e}")

    def print_summary(self):
        """Print final summary"""
        print(f"\n{'='*80}")
        print(f"🎉 LINKEDIN JOB AUTOMATION COMPLETED")
        print(f"{'='*80}")

        duration = time.time() - self.stats['start_time']
        print(f"Session Duration: {duration:.1f} seconds ({duration/60:.1f} minutes)")
        print(f"Search Parameters: {self.search_params['keywords']} jobs in {self.search_params['location']}")

        print(f"\n📊 RESULTS:")
        print(f"Jobs Found: {self.stats['jobs_found']}")
        print(f"Applications Attempted: {self.stats['applications_attempted']}")
        print(f"Successful Applications: {self.stats['applications_successful']}")
        print(f"Failed Applications: {self.stats['applications_failed']}")

        if self.stats['applications_attempted'] > 0:
            success_rate = (self.stats['applications_successful'] / self.stats['applications_attempted'] * 100)
            print(f"Success Rate: {success_rate:.1f}%")

        if self.successful_applications:
            print(f"\n✅ SUCCESSFULLY APPLIED TO:")
            for i, app in enumerate(self.successful_applications, 1):
                job = app['job_info']
                result = app['result']
                print(f"{i:2d}. {job['title']} at {job['company']}")
                print(f"    Method: {result.get('method', 'Unknown')}")

        print(f"\n{'='*80}")

    def run_automation(self):
        """Run the complete LinkedIn job automation"""
        try:
            print("🚀 LINKEDIN JOB AUTOMATION STARTING")
            print(f"Searching for: {self.search_params['keywords']} jobs")
            print(f"Location: {self.search_params['location']}")
            print(f"Distance: {self.search_params['distance']} miles")
            print("="*60)

            # Setup WebDriver
            if not self.setup_driver():
                print("❌ Failed to setup WebDriver")
                return False

            # Authenticate with LinkedIn
            if not self.authenticate_linkedin():
                print("❌ LinkedIn authentication failed")
                return False

            # Perform job search
            if not self.perform_job_search():
                print("❌ Job search failed")
                return False

            # Load all jobs
            print("🔄 Loading all available jobs...")
            self.load_all_jobs()

            # Extract job listings
            print("🔍 Extracting job listings...")
            job_listings = self.extract_job_listings()

            if not job_listings:
                print("❌ No job listings found")
                return False

            print(f"✅ Found {len(job_listings)} jobs")

            # Confirm before applying
            print(f"\n⚠️  Ready to apply to {len(job_listings)} jobs!")
            confirm = input("Continue with applications? (type 'YES' to confirm): ").strip()

            if confirm != 'YES':
                print("Automation cancelled by user")
                return False

            # Apply to all jobs
            print(f"\n🚀 STARTING APPLICATION PROCESS...")
            self.apply_to_all_jobs(job_listings)

            return True

        except Exception as e:
            logger.error(f"Automation failed: {e}")
            print(f"❌ Automation failed: {e}")
            return False

        finally:
            # Save results
            self.save_results()

            # Print summary
            self.print_summary()

            # Close browser
            if self.driver:
                if not self.headless:
                    input("\nPress Enter to close browser...")
                self.driver.quit()

def main():
    """Main function"""
    print("🔗 LINKEDIN JOB AUTOMATION")
    print("Automatically search and apply to software jobs in San Jose area")
    print("="*60)

    # Configuration
    headless = input("Run in headless mode (no browser window)? (y/n): ").strip().lower() == 'y'

    if not headless:
        print("⚠️  Browser window will open for LinkedIn authentication")

    print(f"\n🔍 Search Configuration:")
    print(f"Keywords: software")
    print(f"Location: San Jose, California")
    print(f"Distance: 25 miles")

    confirm = input(f"\nStart automation? (y/n): ").strip().lower()
    if confirm != 'y':
        print("Automation cancelled")
        return

    # Run automation
    automation = LinkedInJobAutomation(headless=headless)
    automation.run_automation()

if __name__ == "__main__":
    main()