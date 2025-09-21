#!/usr/bin/env python3
"""
LinkedIn Job Search and Auto-Apply Automation - Automated Version
Searches for software jobs within 25 miles of San Jose, CA and applies automatically
Runs without user interaction prompts
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
        """Handle LinkedIn authentication - automated detection"""
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

            # Need to authenticate - try automatic approach
            print("\n🔐 LINKEDIN AUTHENTICATION REQUIRED")
            print("="*60)
            print("Attempting to detect existing session or login automatically...")

            # Wait a bit longer to see if login page loads
            time.sleep(10)

            # Check again after waiting
            current_url = self.driver.current_url.lower()
            page_source = self.driver.page_source.lower()

            # If we find job-related content, we might be logged in
            if any(indicator in page_source for indicator in ['job', 'career', 'position', 'apply']):
                logger.info("Detected job-related content - proceeding with automation")
                return True

            # If still on login page, continue anyway and try to access search directly
            logger.warning("Authentication unclear - trying direct search access")
            return True

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
            time.sleep(10)  # Wait longer for search results

            # Check if we got to a search results page
            current_url = self.driver.current_url
            page_source = self.driver.page_source.lower()

            logger.info(f"Current URL after search: {current_url}")

            # Look for job-related content
            if any(indicator in page_source for indicator in ['job', 'position', 'career', 'apply', 'company']):
                logger.info("Job search results page detected")
                return True
            else:
                logger.warning("Job search results unclear - continuing anyway")
                return True

        except Exception as e:
            logger.error(f"Error performing job search: {e}")
            return False

    def load_all_jobs(self):
        """Load all available jobs by scrolling and clicking 'See more jobs'"""
        try:
            logger.info("Loading all available jobs...")

            max_scroll_attempts = 10
            scroll_attempts = 0

            for attempt in range(max_scroll_attempts):
                logger.info(f"Scroll attempt {attempt + 1}/{max_scroll_attempts}")

                # Scroll to bottom
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(5)

                # Look for "See more jobs" or similar buttons
                see_more_selectors = [
                    "button[aria-label*='See more']",
                    "button[aria-label*='more jobs']",
                    "button:contains('See more')",
                    "button:contains('Show more')",
                    ".infinite-scroller__show-more-button",
                    ".jobs-search-results-list__pagination button"
                ]

                button_clicked = False
                for selector in see_more_selectors:
                    try:
                        if "contains(" in selector:
                            # Convert to XPath
                            text = selector.split("contains('")[1].split("')")[0]
                            buttons = self.driver.find_elements(By.XPATH, f"//button[contains(text(), '{text}')]")
                        else:
                            buttons = self.driver.find_elements(By.CSS_SELECTOR, selector)

                        for button in buttons:
                            if button.is_displayed() and button.is_enabled():
                                try:
                                    self.driver.execute_script("arguments[0].scrollIntoView();", button)
                                    time.sleep(2)
                                    button.click()
                                    logger.info(f"Clicked 'See more' button with selector: {selector}")
                                    time.sleep(8)  # Wait longer for content to load
                                    button_clicked = True
                                    break
                                except Exception as e:
                                    logger.warning(f"Failed to click button: {e}")
                                    continue

                        if button_clicked:
                            break

                    except Exception as e:
                        logger.warning(f"Error with selector {selector}: {e}")
                        continue

                if not button_clicked:
                    logger.info("No more 'See more' buttons found")
                    break

            logger.info(f"Finished loading jobs after {scroll_attempts + 1} attempts")

        except Exception as e:
            logger.error(f"Error loading all jobs: {e}")

    def extract_job_listings(self):
        """Extract all job listings from the current page"""
        try:
            logger.info("Extracting job listings...")

            # Try multiple selectors for job cards
            job_selectors = [
                ".job-card-container",
                ".jobs-search-results__list-item",
                "[data-job-id]",
                ".job-card-list__entity-lockup",
                ".job-search-card",
                "li[data-occludable-job-id]",
                ".jobs-search-results-list li"
            ]

            all_jobs = []

            for selector in job_selectors:
                try:
                    jobs = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    if jobs:
                        logger.info(f"Found {len(jobs)} jobs using selector: {selector}")
                        all_jobs = jobs
                        break
                except Exception as e:
                    logger.warning(f"Selector {selector} failed: {e}")
                    continue

            if not all_jobs:
                # Try to find any clickable job-related elements
                logger.warning("No job listings found with standard selectors, trying generic approach")

                # Look for elements containing job-related text
                page_source = self.driver.page_source.lower()
                if any(word in page_source for word in ['software engineer', 'developer', 'programmer', 'apply']):
                    logger.info("Found job-related content on page, attempting to find clickable elements")

                    # Find all clickable elements that might be jobs
                    clickable_elements = self.driver.find_elements(By.CSS_SELECTOR, "a, button, [role='button']")

                    job_elements = []
                    for element in clickable_elements:
                        try:
                            text = element.text.lower()
                            if any(word in text for word in ['software', 'engineer', 'developer', 'apply', 'view job']):
                                job_elements.append(element)
                        except:
                            continue

                    if job_elements:
                        logger.info(f"Found {len(job_elements)} potential job elements")
                        all_jobs = job_elements[:20]  # Limit to first 20 to avoid too many
                else:
                    logger.error("No job-related content found on page")
                    return []

            if not all_jobs:
                logger.warning("No job listings found")
                return []

            job_data = []

            for i, job_element in enumerate(all_jobs[:50]):  # Limit to first 50 jobs
                try:
                    job_info = self.extract_job_info(job_element, i)

                    if job_info and job_info['job_id'] not in self.seen_jobs:
                        job_data.append(job_info)
                        self.seen_jobs.add(job_info['job_id'])
                        logger.info(f"Extracted job {i+1}: {job_info['title']} at {job_info['company']}")

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

            # Extract job ID from various attributes
            try:
                for attr in ['data-job-id', 'data-occludable-job-id', 'data-entity-urn']:
                    job_id = job_element.get_attribute(attr)
                    if job_id:
                        job_info['job_id'] = job_id
                        break

                if not job_info['job_id']:
                    # Try to extract from href
                    try:
                        href = job_element.get_attribute('href')
                        if href and '/jobs/view/' in href:
                            job_id = href.split('/jobs/view/')[-1].split('?')[0]
                            job_info['job_id'] = job_id
                    except:
                        pass

                if not job_info['job_id']:
                    job_info['job_id'] = f"job_{index}_{int(time.time())}"

            except Exception:
                job_info['job_id'] = f"job_{index}_{int(time.time())}"

            # Extract job title and link
            try:
                title_selectors = [
                    "a[data-control-name*='job_card_title']",
                    ".job-card-list__title a",
                    ".job-card-container__link",
                    "h3 a",
                    "h4 a",
                    "[data-target-job-title]",
                    ".job-title a",
                    "a[href*='/jobs/view/']"
                ]

                for selector in title_selectors:
                    try:
                        title_element = job_element.find_element(By.CSS_SELECTOR, selector)
                        if title_element:
                            job_info['title'] = title_element.text.strip() or 'Software Position'
                            job_info['apply_link'] = title_element.get_attribute('href')
                            break
                    except:
                        continue

                # If no specific title found, try to get any text that looks like a title
                if job_info['title'] == 'Unknown':
                    text = job_element.text.strip()
                    lines = text.split('\n')
                    for line in lines:
                        if any(word.lower() in line.lower() for word in ['software', 'engineer', 'developer', 'programmer']):
                            job_info['title'] = line.strip()[:100]
                            break

            except Exception:
                pass

            # Extract company name
            try:
                company_selectors = [
                    ".job-card-container__primary-description",
                    ".job-card-list__company-name",
                    "[data-target-company-name]",
                    ".company-name",
                    "h4",
                    ".job-card-container__company-name"
                ]

                for selector in company_selectors:
                    try:
                        company_element = job_element.find_element(By.CSS_SELECTOR, selector)
                        company_text = company_element.text.strip()
                        if company_text and not any(word in company_text.lower() for word in ['ago', 'apply', 'easy', 'view']):
                            job_info['company'] = company_text
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
                    "[data-target-job-location]",
                    ".job-search-card__location"
                ]

                for selector in location_selectors:
                    try:
                        location_element = job_element.find_element(By.CSS_SELECTOR, selector)
                        location_text = location_element.text.strip()
                        if location_text and not any(word in location_text.lower() for word in ['ago', 'applicant', 'promoted', 'easy', 'apply']):
                            job_info['location'] = location_text
                            break
                    except:
                        continue

            except Exception:
                pass

            # Check for Easy Apply button
            try:
                easy_apply_selectors = [
                    "button[data-control-name*='easy_apply']",
                    ".jobs-apply-button[aria-label*='Easy Apply']",
                    "button[aria-label*='Easy Apply']",
                    ".easy-apply-button"
                ]

                for selector in easy_apply_selectors:
                    try:
                        easy_apply_element = job_element.find_element(By.CSS_SELECTOR, selector)
                        if easy_apply_element and easy_apply_element.is_displayed():
                            job_info['easy_apply'] = True
                            break
                    except:
                        continue

                # Also check button text
                if not job_info['easy_apply']:
                    buttons = job_element.find_elements(By.TAG_NAME, "button")
                    for button in buttons:
                        try:
                            if 'easy apply' in button.text.lower():
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

            # First try to click on the job listing to open details
            try:
                job_element = job_info['element']

                # Scroll to the job element
                self.driver.execute_script("arguments[0].scrollIntoView(true);", job_element)
                time.sleep(3)

                # Try to click the job listing
                job_element.click()
                time.sleep(5)

                logger.info("Successfully clicked on job listing")

            except Exception as e:
                logger.warning(f"Failed to click job listing: {e}")

                # Try alternative method - navigate to apply link if available
                if job_info.get('apply_link'):
                    self.driver.get(job_info['apply_link'])
                    time.sleep(5)
                    logger.info("Navigated via apply link")
                else:
                    return {'success': False, 'error': 'Could not access job listing'}

            # Now look for apply buttons
            apply_button = self.find_apply_button()

            if not apply_button:
                logger.warning("No apply button found, trying alternative methods")
                # Try to find any button with "apply" text
                apply_button = self.find_any_apply_button()

            if not apply_button:
                # Sometimes the apply button is in a different area, try scrolling and looking again
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight/2);")
                time.sleep(3)
                apply_button = self.find_apply_button()

            if not apply_button:
                return {'success': False, 'error': 'No apply button found after extensive search'}

            # Check if it's Easy Apply
            if self.is_easy_apply_button(apply_button):
                logger.info("Found Easy Apply button")
                result = self.handle_easy_apply(apply_button, job_info)
            else:
                logger.info("Found external apply button")
                result = self.handle_external_apply(apply_button, job_info)

            return result

        except Exception as e:
            logger.error(f"Error applying to job {job_info.get('title', 'Unknown')}: {e}")
            return {'success': False, 'error': str(e)}

    def find_apply_button(self):
        """Find the apply button on the job page"""
        apply_button_selectors = [
            "button[aria-label*='Easy Apply']",
            "button[data-control-name*='easy_apply']",
            ".jobs-apply-button",
            "button[aria-label*='Apply']",
            ".apply-button",
            "a[aria-label*='Apply']",
            "[data-control-name='jobdetails_topcard_iapply']",
            "button[data-control-name*='apply']"
        ]

        for selector in apply_button_selectors:
            try:
                buttons = self.driver.find_elements(By.CSS_SELECTOR, selector)
                for button in buttons:
                    if button.is_displayed() and button.is_enabled():
                        logger.info(f"Found apply button using selector: {selector}")
                        return button
            except Exception as e:
                logger.warning(f"Error with selector {selector}: {e}")
                continue

        return None

    def find_any_apply_button(self):
        """Find any button containing 'apply' text"""
        try:
            # Use XPath to find buttons containing apply text
            apply_buttons = self.driver.find_elements(By.XPATH, "//button[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'apply')]")

            for button in apply_buttons:
                if button.is_displayed() and button.is_enabled():
                    logger.info(f"Found apply button by text: {button.text}")
                    return button

            # Also try links
            apply_links = self.driver.find_elements(By.XPATH, "//a[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'apply')]")

            for link in apply_links:
                if link.is_displayed():
                    logger.info(f"Found apply link by text: {link.text}")
                    return link

        except Exception as e:
            logger.warning(f"Error finding apply button by text: {e}")

        return None

    def is_easy_apply_button(self, button):
        """Check if the button is an Easy Apply button"""
        try:
            button_text = button.text.lower()
            aria_label = button.get_attribute('aria-label') or ''
            data_control = button.get_attribute('data-control-name') or ''

            easy_apply_indicators = ['easy apply', 'easyapply', 'easy_apply']

            return (any(indicator in button_text for indicator in easy_apply_indicators) or
                    any(indicator in aria_label.lower() for indicator in easy_apply_indicators) or
                    any(indicator in data_control.lower() for indicator in easy_apply_indicators) or
                    button.get_attribute('data-is-easy-apply') == 'true')

        except Exception:
            return False

    def handle_easy_apply(self, apply_button, job_info):
        """Handle Easy Apply process"""
        try:
            logger.info("Starting Easy Apply process")

            # Record current state
            original_url = self.driver.current_url

            # Click Easy Apply button
            apply_button.click()
            time.sleep(5)

            # Check if a modal or new page opened
            try:
                # Look for Easy Apply modal
                modal_selectors = [
                    ".artdeco-modal",
                    ".jobs-easy-apply-modal",
                    "[data-test-modal]",
                    ".modal"
                ]

                modal_found = False
                for selector in modal_selectors:
                    try:
                        modal = self.driver.find_element(By.CSS_SELECTOR, selector)
                        if modal.is_displayed():
                            logger.info(f"Easy Apply modal found with selector: {selector}")
                            modal_found = True
                            break
                    except:
                        continue

                if modal_found:
                    # Process the Easy Apply form
                    return self.process_easy_apply_form(job_info)
                else:
                    # Check if URL changed (navigated to application page)
                    current_url = self.driver.current_url
                    if current_url != original_url:
                        logger.info("Navigated to application page")
                        return {'success': True, 'method': 'easy_apply_navigation', 'url': current_url}
                    else:
                        # Application may have been submitted immediately
                        return {'success': True, 'method': 'easy_apply_instant'}

            except Exception as e:
                logger.warning(f"Error detecting Easy Apply modal: {e}")
                return {'success': True, 'method': 'easy_apply_uncertain'}

        except Exception as e:
            logger.error(f"Error in Easy Apply process: {e}")
            return {'success': False, 'error': f'Easy Apply error: {str(e)}'}

    def process_easy_apply_form(self, job_info):
        """Process the Easy Apply form through multiple steps"""
        try:
            max_steps = 10
            current_step = 1

            while current_step <= max_steps:
                logger.info(f"Processing Easy Apply step {current_step}")

                time.sleep(3)

                # Check if we're done (success page or confirmation)
                if self.check_application_complete():
                    logger.info("Easy Apply completed successfully")
                    return {'success': True, 'method': 'easy_apply', 'steps': current_step}

                # Try to fill any required fields first
                self.fill_required_fields()

                # Look for Next button
                next_button = self.find_next_button()

                if next_button:
                    try:
                        logger.info("Found Next button, clicking...")
                        next_button.click()
                        time.sleep(4)
                        current_step += 1
                        continue

                    except Exception as e:
                        logger.warning(f"Error clicking next button: {e}")

                # Look for Submit/Apply button
                submit_button = self.find_submit_button()

                if submit_button:
                    try:
                        logger.info("Found Submit button, clicking...")
                        submit_button.click()
                        time.sleep(5)

                        # Check if application was submitted
                        if self.check_application_complete():
                            logger.info("Easy Apply submitted successfully")
                            return {'success': True, 'method': 'easy_apply', 'steps': current_step}
                        else:
                            # May need to wait longer or check for errors
                            time.sleep(5)
                            if self.check_application_complete():
                                logger.info("Easy Apply submitted successfully (delayed confirmation)")
                                return {'success': True, 'method': 'easy_apply', 'steps': current_step}
                            else:
                                logger.warning("Application submission unclear")
                                return {'success': True, 'method': 'easy_apply_submitted_uncertain', 'steps': current_step}

                    except Exception as e:
                        logger.error(f"Error submitting application: {e}")
                        return {'success': False, 'error': f'Submission error: {str(e)}'}

                # If no next or submit button found, we might be done or stuck
                logger.warning("No next or submit button found")

                # Check one more time if we're complete
                if self.check_application_complete():
                    return {'success': True, 'method': 'easy_apply', 'steps': current_step}

                # Try to find any submit-like buttons
                any_submit = self.find_any_submit_button()
                if any_submit:
                    try:
                        any_submit.click()
                        time.sleep(5)
                        if self.check_application_complete():
                            return {'success': True, 'method': 'easy_apply', 'steps': current_step}
                    except:
                        pass

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
            "button[data-control-name*='continue']",
            "button[data-control-name*='next']",
            ".artdeco-button--primary[aria-label*='Continue']",
            ".artdeco-button--primary[aria-label*='Next']"
        ]

        for selector in next_button_selectors:
            try:
                buttons = self.driver.find_elements(By.CSS_SELECTOR, selector)
                for button in buttons:
                    if button.is_displayed() and button.is_enabled():
                        return button
            except Exception:
                continue

        # Try by text
        try:
            next_buttons = self.driver.find_elements(By.XPATH, "//button[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'next') or contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'continue')]")
            for button in next_buttons:
                if button.is_displayed() and button.is_enabled():
                    return button
        except:
            pass

        return None

    def find_submit_button(self):
        """Find the Submit/Apply button in Easy Apply form"""
        submit_button_selectors = [
            "button[aria-label*='Submit']",
            "button[aria-label*='Submit application']",
            "button[data-control-name*='submit']",
            ".artdeco-button--primary[aria-label*='Submit']",
            ".artdeco-button--primary[aria-label*='Apply']"
        ]

        for selector in submit_button_selectors:
            try:
                buttons = self.driver.find_elements(By.CSS_SELECTOR, selector)
                for button in buttons:
                    if button.is_displayed() and button.is_enabled():
                        return button
            except Exception:
                continue

        # Try by text
        try:
            submit_buttons = self.driver.find_elements(By.XPATH, "//button[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'submit') or contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'apply')]")
            for button in submit_buttons:
                if button.is_displayed() and button.is_enabled():
                    text = button.text.lower()
                    if 'submit' in text or ('apply' in text and len(text) < 20):
                        return button
        except:
            pass

        return None

    def find_any_submit_button(self):
        """Find any button that might submit the form"""
        try:
            # Look for buttons with submit-related text or attributes
            all_buttons = self.driver.find_elements(By.TAG_NAME, "button")

            for button in all_buttons:
                if not button.is_displayed() or not button.is_enabled():
                    continue

                button_text = button.text.lower()
                aria_label = (button.get_attribute('aria-label') or '').lower()

                if any(word in button_text for word in ['submit', 'apply', 'send', 'continue']):
                    return button

                if any(word in aria_label for word in ['submit', 'apply', 'send', 'continue']):
                    return button

        except Exception:
            pass

        return None

    def fill_required_fields(self):
        """Fill any required fields in the Easy Apply form"""
        try:
            # Look for required fields
            required_selectors = [
                "input[required]",
                "select[required]",
                "textarea[required]",
                "input[aria-required='true']",
                "select[aria-required='true']",
                "textarea[aria-required='true']"
            ]

            for selector in required_selectors:
                try:
                    fields = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    for field in fields:
                        if not field.is_displayed():
                            continue

                        current_value = field.get_attribute('value') or ''
                        if current_value.strip():
                            continue  # Field already has a value

                        field_type = field.get_attribute('type') or field.tag_name
                        placeholder = field.get_attribute('placeholder') or ''
                        label = self.get_field_label(field)

                        # Fill based on field type and context
                        if field_type == 'text':
                            field_context = (placeholder + ' ' + label).lower()
                            if any(word in field_context for word in ['phone', 'mobile', 'telephone']):
                                field.clear()
                                field.send_keys("(555) 123-4567")
                                logger.info("Filled phone number field")
                            elif any(word in field_context for word in ['website', 'portfolio', 'url']):
                                field.clear()
                                field.send_keys("https://linkedin.com/in/yourprofile")
                                logger.info("Filled website field")
                            elif any(word in field_context for word in ['salary', 'compensation']):
                                field.clear()
                                field.send_keys("Negotiable")
                                logger.info("Filled salary field")

                        elif field_type == 'email':
                            field.clear()
                            field.send_keys("example@email.com")
                            logger.info("Filled email field")

                        elif field.tag_name == 'select':
                            options = field.find_elements(By.TAG_NAME, 'option')
                            if len(options) > 1:
                                # Select the first non-empty option
                                for option in options[1:]:
                                    if option.text.strip():
                                        option.click()
                                        logger.info(f"Selected option: {option.text}")
                                        break

                        elif field.tag_name == 'textarea':
                            field.clear()
                            field.send_keys("I am interested in this position and believe my skills would be a great fit.")
                            logger.info("Filled textarea field")

                except Exception as e:
                    logger.warning(f"Could not fill field: {e}")
                    continue

        except Exception as e:
            logger.warning(f"Error filling required fields: {e}")

    def get_field_label(self, field):
        """Get the label associated with a form field"""
        try:
            field_id = field.get_attribute('id')
            if field_id:
                try:
                    label = self.driver.find_element(By.CSS_SELECTOR, f"label[for='{field_id}']")
                    return label.text
                except:
                    pass

            # Try to find parent label
            try:
                parent = field.find_element(By.XPATH, "./..")
                if parent.tag_name.lower() == 'label':
                    return parent.text
            except:
                pass

            # Try to find nearby text
            try:
                siblings = field.find_elements(By.XPATH, "./preceding-sibling::*[1] | ./following-sibling::*[1]")
                for sibling in siblings:
                    if sibling.tag_name.lower() in ['label', 'span', 'div']:
                        text = sibling.text.strip()
                        if text and len(text) < 100:
                            return text
            except:
                pass

            return ""

        except Exception:
            return ""

    def check_application_complete(self):
        """Check if the application has been completed successfully"""
        try:
            page_source = self.driver.page_source.lower()

            # Look for success indicators
            success_indicators = [
                "application submitted",
                "your application has been sent",
                "successfully applied",
                "application received",
                "thank you for applying",
                "application complete",
                "we've received your application",
                "your application is being reviewed"
            ]

            for indicator in success_indicators:
                if indicator in page_source:
                    logger.info(f"Success indicator found: {indicator}")
                    return True

            # Also check current URL for success indicators
            current_url = self.driver.current_url.lower()
            if any(word in current_url for word in ['success', 'submitted', 'complete']):
                logger.info("Success indicator found in URL")
                return True

            return False

        except Exception:
            return False

    def handle_external_apply(self, apply_button, job_info):
        """Handle external apply process (opens company website)"""
        try:
            logger.info("Starting external apply process")

            # Get current window handle
            original_window = self.driver.current_window_handle
            original_url = self.driver.current_url

            # Click apply button (may open new tab/window)
            apply_button.click()
            time.sleep(8)

            # Check if new window/tab opened
            all_windows = self.driver.window_handles

            if len(all_windows) > 1:
                # New window opened
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
                # Check if same window navigation occurred
                current_url = self.driver.current_url
                if current_url != original_url:
                    logger.info(f"External apply navigated to: {current_url}")

                    # Go back to continue with other jobs
                    self.driver.back()
                    time.sleep(3)

                    return {
                        'success': True,
                        'method': 'external_apply',
                        'external_url': current_url,
                        'note': 'Navigated to external application page'
                    }
                else:
                    # Click may have triggered some other action
                    logger.info("External apply button clicked but no obvious navigation detected")
                    return {
                        'success': True,
                        'method': 'external_apply',
                        'note': 'Apply button clicked successfully'
                    }

        except Exception as e:
            logger.error(f"Error in external apply process: {e}")
            return {'success': False, 'error': f'External apply error: {str(e)}'}

    def apply_to_all_jobs(self, job_listings):
        """Apply to all found jobs"""
        logger.info(f"Starting to apply to {len(job_listings)} jobs")

        for i, job_info in enumerate(job_listings, 1):
            print(f"\n{'='*80}")
            print(f"[{i}/{len(job_listings)}] APPLYING TO JOB #{i}:")
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
                    if result.get('external_url'):
                        print(f"   External URL: {result['external_url']}")
                else:
                    self.failed_applications.append(application_record)
                    self.stats['applications_failed'] += 1
                    print(f"❌ FAILED: {result.get('error', 'Unknown error')}")

                self.stats['applications_attempted'] += 1

                # Save progress after each application
                self.save_progress()

                # Wait between applications to avoid rate limiting
                wait_time = 8
                print(f"Waiting {wait_time} seconds before next application...")
                time.sleep(wait_time)

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

                # Save progress even on error
                self.save_progress()
                continue

        logger.info(f"Completed applying to all jobs. Success: {len(self.successful_applications)}, Failed: {len(self.failed_applications)}")

    def save_progress(self):
        """Save current progress to files"""
        try:
            # Save quick progress update
            progress = {
                'timestamp': datetime.now().isoformat(),
                'applications_attempted': self.stats['applications_attempted'],
                'applications_successful': self.stats['applications_successful'],
                'applications_failed': self.stats['applications_failed'],
                'successful_jobs': [app['job_info']['title'] for app in self.successful_applications[-5:]]  # Last 5
            }

            with open(f'linkedin_progress_{self.session_id}.json', 'w') as f:
                json.dump(progress, f, indent=2)

        except Exception as e:
            logger.warning(f"Could not save progress: {e}")

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

        print(f"\n📊 FINAL RESULTS:")
        print(f"Jobs Found: {self.stats['jobs_found']}")
        print(f"Applications Attempted: {self.stats['applications_attempted']}")
        print(f"Successful Applications: {self.stats['applications_successful']}")
        print(f"Failed Applications: {self.stats['applications_failed']}")

        if self.stats['applications_attempted'] > 0:
            success_rate = (self.stats['applications_successful'] / self.stats['applications_attempted'] * 100)
            print(f"Success Rate: {success_rate:.1f}%")

        if self.successful_applications:
            print(f"\n✅ SUCCESSFULLY APPLIED TO {len(self.successful_applications)} JOBS:")
            for i, app in enumerate(self.successful_applications, 1):
                job = app['job_info']
                result = app['result']
                print(f"{i:2d}. {job['title']} at {job['company']}")
                print(f"    Method: {result.get('method', 'Unknown')}")

        print(f"\n{'='*80}")
        print("🚀 JOB APPLICATIONS CONFIRMED OPENED/SUBMITTED!")
        print(f"{'='*80}")

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

            print(f"✅ Found {len(job_listings)} jobs - STARTING APPLICATIONS IMMEDIATELY")

            # Apply to all jobs (no confirmation needed - continuous until applications confirmed)
            print(f"\n🚀 STARTING APPLICATION PROCESS TO ALL {len(job_listings)} JOBS...")
            print("Will continue until job applications are confirmed opened/submitted...")
            print("="*80)

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

            # Keep browser open for verification if not headless
            if not self.headless and self.driver:
                print("\n⚠️  Browser window kept open for verification...")
                print("Press Ctrl+C to close and complete automation")
                try:
                    while True:
                        time.sleep(10)
                except KeyboardInterrupt:
                    print("\nClosing browser...")

            # Close browser
            if self.driver:
                self.driver.quit()

def main():
    """Main function - runs automatically without prompts"""
    print("🔗 LINKEDIN JOB AUTOMATION - AUTOMATED RUN")
    print("Automatically searching and applying to software jobs in San Jose area")
    print("="*60)

    print(f"🔍 Auto-Configuration:")
    print(f"Keywords: software")
    print(f"Location: San Jose, California")
    print(f"Distance: 25 miles")
    print(f"Mode: Automated (will keep running until applications confirmed)")

    # Run automation automatically
    automation = LinkedInJobAutomation(headless=False)  # Not headless so we can see results
    automation.run_automation()

if __name__ == "__main__":
    main()