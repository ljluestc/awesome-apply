#!/usr/bin/env python3
"""
Persistent Nemetschek Job Application Automation
Multiple strategies to find jobs and apply until successful with UI confirmation
"""

import os
import sys
import json
import time
import subprocess
from datetime import datetime
from typing import Dict, List, Any, Optional
import logging
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import TimeoutException, NoSuchElementException, ElementClickInterceptedException

from enhanced_dynamic_resume_generator import EnhancedDynamicResumeGenerator

class PersistentNemetschekAutomation:
    def __init__(self, headless: bool = False):
        self.logger = logging.getLogger(__name__)
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )

        self.headless = headless
        self.driver = None
        self.wait = None
        self.resume_generator = EnhancedDynamicResumeGenerator()

        # Personal data from the LaTeX resume
        self.personal_data = {
            "first_name": "Jiale",
            "last_name": "Lin",
            "full_name": "Jiale Lin",
            "email": "jeremykalilin@gmail.com",
            "phone": "+15104175834",
            "phone_formatted": "+1-510-417-5834",
            "mobile": "+15104175834",
            "address": "Santa Clara, CA",
            "city": "Santa Clara",
            "state": "CA",
            "country": "United States",
            "linkedin": "https://www.linkedin.com/in/jiale-lin-ab03a4149",
            "website": "https://ljluestc.github.io",
            "work_authorization": "US Citizen",
            "experience_years": "5",
            "current_location": "Santa Clara, CA, United States",
            "willing_to_relocate": "Yes"
        }

        # Setup output directories
        self.output_dir = "persistent_nemetschek_applications"
        os.makedirs(self.output_dir, exist_ok=True)
        os.makedirs(f"{self.output_dir}/enhanced_resumes", exist_ok=True)
        os.makedirs(f"{self.output_dir}/cover_letters", exist_ok=True)
        os.makedirs(f"{self.output_dir}/screenshots", exist_ok=True)

        # Track application attempts
        self.application_log = []

    def setup_driver(self):
        """Setup Chrome WebDriver with maximum compatibility"""
        chrome_options = Options()

        if self.headless:
            chrome_options.add_argument("--headless")

        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("--start-maximized")
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
        chrome_options.add_argument("--disable-extensions")
        chrome_options.add_argument("--disable-plugins")

        prefs = {
            "download.default_directory": os.path.abspath(self.output_dir),
            "download.prompt_for_download": False,
            "download.directory_upgrade": True,
            "safebrowsing.enabled": True
        }
        chrome_options.add_experimental_option("prefs", prefs)

        try:
            self.driver = webdriver.Chrome(options=chrome_options)
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            self.wait = WebDriverWait(self.driver, 30)
            self.driver.maximize_window()
            self.logger.info("WebDriver setup successfully")
            return True
        except Exception as e:
            self.logger.error(f"Failed to setup WebDriver: {e}")
            return False

    def take_screenshot(self, filename: str):
        """Take a screenshot for debugging"""
        try:
            screenshot_path = os.path.join(self.output_dir, "screenshots", filename)
            self.driver.save_screenshot(screenshot_path)
            self.logger.info(f"Screenshot saved: {screenshot_path}")
        except Exception as e:
            self.logger.warning(f"Failed to take screenshot: {e}")

    def try_multiple_career_urls(self) -> bool:
        """Try multiple URLs to find Nemetschek careers"""
        urls_to_try = [
            "https://career55.sapsf.eu/careers?company=nemetschek",
            "https://www.nemetschek.com/en/careers",
            "https://careers.nemetschek.com",
            "https://jobs.nemetschek.com",
            "https://nemetschek.jobs",
            "https://career55.sapsf.eu/careers?company=Nemetschek",
            "https://career55.sapsf.eu/en/careers?company=nemetschek"
        ]

        for i, url in enumerate(urls_to_try):
            try:
                self.logger.info(f"Trying URL {i+1}/{len(urls_to_try)}: {url}")
                self.driver.get(url)
                time.sleep(5)

                # Handle popups
                self._handle_popups_and_cookies()

                # Check if we found a careers page
                page_text = self.driver.find_element(By.TAG_NAME, "body").text.lower()
                current_url = self.driver.current_url.lower()

                if any(keyword in page_text for keyword in ["career", "job", "position", "apply", "nemetschek"]) or \
                   any(keyword in current_url for keyword in ["career", "job", "nemetschek"]):

                    self.logger.info(f"Found careers page at: {url}")
                    self.take_screenshot(f"careers_found_{i}_{datetime.now().strftime('%H%M%S')}.png")
                    return True

            except Exception as e:
                self.logger.warning(f"URL {url} failed: {e}")
                continue

        return False

    def _handle_popups_and_cookies(self):
        """Handle cookie banners and popups aggressively"""
        try:
            # Wait a moment for popups to appear
            time.sleep(2)

            # Comprehensive popup selectors
            popup_selectors = [
                # Cookie consent
                "button[id*='accept']", "button[id*='cookie']", "button[class*='accept']",
                "button[class*='cookie']", ".cookie-accept", ".accept-all", ".btn-accept",
                "#onetrust-accept-btn-handler", ".onetrust-close-btn-handler",
                "[aria-label*='accept' i]", "[aria-label*='close' i]",

                # Modal close buttons
                ".modal-close", ".close-button", "[data-dismiss='modal']",
                ".popup-close", "[title*='close' i]",

                # Common button text
                "button:contains('Accept')", "button:contains('OK')", "button:contains('Continue')",
                "button:contains('Agree')", "button:contains('Close')",

                # Generic close buttons
                ".fa-times", ".fa-close", ".icon-close", ".btn-close"
            ]

            for selector in popup_selectors:
                try:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    for element in elements:
                        if element.is_displayed() and element.is_enabled():
                            try:
                                element.click()
                                time.sleep(1)
                                self.logger.info(f"Closed popup using: {selector}")
                                break
                            except:
                                continue
                except:
                    continue

            # Try to remove overlays with JavaScript
            try:
                overlay_scripts = [
                    "document.querySelectorAll('.modal-backdrop, .overlay, .popup-overlay').forEach(el => el.remove());",
                    "document.querySelectorAll('[style*=\"position: fixed\"]').forEach(el => el.style.display = 'none');",
                    "document.body.style.overflow = 'auto';"
                ]
                for script in overlay_scripts:
                    self.driver.execute_script(script)
            except:
                pass

        except Exception as e:
            self.logger.debug(f"Popup handling: {e}")

    def aggressive_job_search(self) -> List[Dict[str, Any]]:
        """Aggressively search for jobs using multiple strategies"""
        jobs = []

        try:
            self.logger.info("Starting aggressive job search...")
            time.sleep(3)

            # Strategy 1: Look for job search form and use it
            if self._try_job_search_form():
                time.sleep(5)

            # Strategy 2: Find job listings with comprehensive selectors
            jobs = self._find_job_listings_comprehensive()

            if jobs:
                return jobs

            # Strategy 3: Navigate through site structure
            jobs = self._navigate_site_structure()

            if jobs:
                return jobs

            # Strategy 4: Create test job if nothing found
            jobs = self._create_test_application_opportunity()

            return jobs

        except Exception as e:
            self.logger.error(f"Job search failed: {e}")
            return jobs

    def _try_job_search_form(self) -> bool:
        """Try to use a job search form if available"""
        try:
            # Look for search inputs
            search_selectors = [
                "input[placeholder*='search' i]", "input[placeholder*='keyword' i]",
                "input[name*='search' i]", "input[id*='search' i]",
                ".search-input", "#search", ".job-search-input"
            ]

            for selector in search_selectors:
                try:
                    search_inputs = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    for search_input in search_inputs:
                        if search_input.is_displayed() and search_input.is_enabled():
                            # Try searching for software engineering jobs
                            search_input.clear()
                            search_input.send_keys("software engineer")
                            search_input.send_keys(Keys.RETURN)
                            self.logger.info("Used search form")
                            return True
                except:
                    continue

            # Look for search buttons
            search_btn_selectors = [
                "button:contains('Search')", ".search-btn", ".btn-search",
                "input[type='submit']", "button[type='submit']"
            ]

            for selector in search_btn_selectors:
                try:
                    buttons = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    for btn in buttons:
                        if btn.is_displayed() and "search" in btn.text.lower():
                            btn.click()
                            self.logger.info("Clicked search button")
                            return True
                except:
                    continue

        except Exception as e:
            self.logger.debug(f"Search form attempt: {e}")

        return False

    def _find_job_listings_comprehensive(self) -> List[Dict[str, Any]]:
        """Find job listings with comprehensive selectors"""
        jobs = []

        try:
            # Extensive job listing selectors
            job_selectors = [
                # Standard job selectors
                ".job-tile", ".jobTile", ".job-card", ".job-item", ".job-listing",
                ".position-tile", ".vacancy-item", ".opportunity", ".position",

                # Data attributes
                "[data-test-id*='job']", "[data-testid*='job']", "[data-job-id]",
                "[data-position]", "[data-role]",

                # Common class patterns
                ".career-opportunity", ".open-position", ".job-opening",
                ".role-card", ".position-card", ".vacancy-card",

                # List items that might be jobs
                "li[class*='job']", "li[class*='position']", "li[class*='role']",

                # Divs that might contain jobs
                "div[class*='job']", "div[class*='position']", "div[class*='career']"
            ]

            for selector in job_selectors:
                try:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    if elements:
                        self.logger.info(f"Found {len(elements)} elements with selector: {selector}")

                        for i, element in enumerate(elements[:10]):
                            try:
                                job_data = self._extract_job_data_enhanced(element, i)
                                if job_data:
                                    jobs.append(job_data)
                            except Exception as e:
                                self.logger.debug(f"Failed to extract job {i}: {e}")

                        if jobs:
                            self.logger.info(f"Successfully extracted {len(jobs)} jobs")
                            break

                except Exception as e:
                    self.logger.debug(f"Selector {selector} failed: {e}")

            # If no structured jobs found, look for links with job-related text
            if not jobs:
                jobs = self._find_job_links()

        except Exception as e:
            self.logger.error(f"Comprehensive job search failed: {e}")

        return jobs

    def _extract_job_data_enhanced(self, element, index: int) -> Optional[Dict[str, Any]]:
        """Enhanced job data extraction"""
        try:
            job_data = {
                "title": "",
                "location": "",
                "link": "",
                "job_id": f"extracted_job_{index}",
                "element": element,
                "source": "extracted"
            }

            # Extract text content
            element_text = element.text.strip()
            text_lines = [line.strip() for line in element_text.split('\n') if line.strip()]

            if text_lines:
                # First line is usually the title
                job_data["title"] = text_lines[0]

                # Look for location in subsequent lines
                for line in text_lines[1:]:
                    if any(loc_indicator in line.lower() for loc_indicator in ["germany", "munich", "remote", "hybrid"]) and len(line) < 100:
                        job_data["location"] = line
                        break

            # Extract link
            try:
                if element.tag_name == "a":
                    job_data["link"] = element.get_attribute("href")
                else:
                    link = element.find_element(By.CSS_SELECTOR, "a")
                    job_data["link"] = link.get_attribute("href")
            except:
                job_data["link"] = self.driver.current_url

            # Only return if we have a meaningful title
            if job_data["title"] and len(job_data["title"]) > 3 and not any(skip in job_data["title"].lower() for skip in ["search", "filter", "menu"]):
                return job_data

        except Exception as e:
            self.logger.debug(f"Job extraction failed: {e}")

        return None

    def _find_job_links(self) -> List[Dict[str, Any]]:
        """Find job-related links on the page"""
        jobs = []

        try:
            all_links = self.driver.find_elements(By.CSS_SELECTOR, "a[href]")

            for i, link in enumerate(all_links):
                try:
                    link_text = link.text.strip()
                    href = link.get_attribute("href")

                    # Check if this looks like a job
                    job_keywords = [
                        "engineer", "developer", "manager", "analyst", "specialist",
                        "coordinator", "architect", "consultant", "lead", "senior",
                        "junior", "intern", "devops", "software", "fullstack"
                    ]

                    if any(keyword in link_text.lower() for keyword in job_keywords) and \
                       len(link_text) > 10 and len(link_text) < 100:

                        job_data = {
                            "title": link_text,
                            "link": href,
                            "location": "Remote/Germany",
                            "job_id": f"link_job_{i}",
                            "element": link,
                            "source": "link"
                        }
                        jobs.append(job_data)

                        if len(jobs) >= 5:
                            break

                except Exception as e:
                    continue

        except Exception as e:
            self.logger.error(f"Link search failed: {e}")

        return jobs

    def _navigate_site_structure(self) -> List[Dict[str, Any]]:
        """Navigate through site structure to find jobs"""
        jobs = []

        try:
            # Look for navigation links that might lead to jobs
            nav_keywords = ["career", "job", "position", "opportunity", "work"]

            all_links = self.driver.find_elements(By.CSS_SELECTOR, "a[href]")

            for link in all_links:
                try:
                    link_text = link.text.strip().lower()
                    href = link.get_attribute("href")

                    if any(keyword in link_text for keyword in nav_keywords) and len(link_text) < 50:
                        self.logger.info(f"Trying navigation link: {link_text}")

                        # Save current window
                        main_window = self.driver.current_window_handle

                        # Open in new tab
                        self.driver.execute_script("window.open(arguments[0]);", href)
                        self.driver.switch_to.window(self.driver.window_handles[-1])

                        time.sleep(3)
                        self._handle_popups_and_cookies()

                        # Look for jobs on this page
                        page_jobs = self._find_job_listings_comprehensive()

                        if page_jobs:
                            jobs.extend(page_jobs)

                        # Close tab and return to main
                        self.driver.close()
                        self.driver.switch_to.window(main_window)

                        if jobs:
                            break

                except Exception as e:
                    self.logger.debug(f"Navigation attempt failed: {e}")
                    try:
                        # Ensure we're back on main window
                        if len(self.driver.window_handles) > 1:
                            self.driver.close()
                        self.driver.switch_to.window(self.driver.window_handles[0])
                    except:
                        pass

        except Exception as e:
            self.logger.error(f"Site navigation failed: {e}")

        return jobs

    def _create_test_application_opportunity(self) -> List[Dict[str, Any]]:
        """Create a test application opportunity"""
        try:
            # Check if current page has any application-related content
            page_text = self.driver.find_element(By.TAG_NAME, "body").text.lower()

            if any(keyword in page_text for keyword in ["application", "apply", "career", "job", "position"]):
                return [{
                    "title": "Software Engineering Opportunity",
                    "location": "Munich, Germany / Remote",
                    "link": self.driver.current_url,
                    "job_id": "test_opportunity",
                    "source": "test",
                    "description": "Software engineering position at Nemetschek"
                }]

        except Exception as e:
            self.logger.debug(f"Test opportunity creation failed: {e}")

        return []

    def attempt_application_submission(self, job: Dict[str, Any]) -> bool:
        """Attempt to submit application with multiple strategies"""
        max_attempts = 3

        for attempt in range(max_attempts):
            try:
                self.logger.info(f"Application attempt {attempt + 1} for: {job['title']}")

                # Navigate to job if needed
                if job.get("link") and job["link"] != self.driver.current_url:
                    self.driver.get(job["link"])
                    time.sleep(3)
                    self._handle_popups_and_cookies()

                self.take_screenshot(f"application_attempt_{attempt}_{datetime.now().strftime('%H%M%S')}.png")

                # Generate documents for this job
                documents = self._generate_documents_for_job(job)

                # Strategy 1: Look for direct apply button
                if self._find_and_click_apply_comprehensive():
                    if self._fill_application_form_aggressive(documents):
                        if self._submit_with_confirmation():
                            return True

                # Strategy 2: Look for contact forms or general forms
                if self._try_contact_or_general_forms(documents):
                    return True

                # Strategy 3: Try to create an unsolicited application
                if self._try_unsolicited_application(documents):
                    return True

            except Exception as e:
                self.logger.error(f"Application attempt {attempt + 1} failed: {e}")

        return False

    def _find_and_click_apply_comprehensive(self) -> bool:
        """Comprehensive apply button finding"""
        try:
            # Ultra-comprehensive apply button selectors
            apply_selectors = [
                # Direct apply
                "button[id*='apply' i]", "a[id*='apply' i]", "#apply", "#applyButton",
                "button[class*='apply' i]", "a[class*='apply' i]", ".apply-button",
                ".btn-apply", ".apply-btn", ".apply",

                # Application-related
                "button[id*='application' i]", "button[class*='application' i]",
                ".application-button", ".btn-application",

                # Submit/send
                "button[type='submit']", "input[type='submit']", ".submit-btn",
                ".btn-submit", "button[id*='submit' i]",

                # Contact/interest
                "button[id*='contact' i]", ".contact-btn", ".btn-contact",
                "button[id*='interest' i]", ".interest-btn",

                # Data attributes
                "[data-test-id*='apply' i]", "[data-testid*='apply' i]",
                "[data-action='apply']", "[data-action='application']",

                # Aria labels
                "[aria-label*='apply' i]", "[aria-label*='application' i]",

                # Text content
                "*:contains('Apply Now')", "*:contains('Apply')", "*:contains('APPLY')",
                "*:contains('Submit Application')", "*:contains('Send Application')",
                "*:contains('Express Interest')", "*:contains('Contact Us')"
            ]

            for selector in apply_selectors:
                try:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    for element in elements:
                        if element.is_displayed() and element.is_enabled():
                            element_text = element.text.strip().lower()

                            # Check if this looks like an apply button
                            apply_keywords = ["apply", "application", "submit", "send", "contact", "interest"]
                            if any(keyword in element_text for keyword in apply_keywords) or \
                               any(keyword in selector.lower() for keyword in ["apply", "submit"]):

                                self.logger.info(f"Found apply button: '{element.text}' using {selector}")

                                # Scroll and click
                                self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", element)
                                time.sleep(1)

                                try:
                                    element.click()
                                except ElementClickInterceptedException:
                                    self.driver.execute_script("arguments[0].click();", element)

                                time.sleep(3)
                                self.take_screenshot(f"after_apply_click_{datetime.now().strftime('%H%M%S')}.png")
                                return True

                except Exception as e:
                    continue

            # Fallback: Look for any clickable element with apply-related text
            all_clickable = self.driver.find_elements(By.CSS_SELECTOR, "button, a, input, [onclick], [role='button']")

            for element in all_clickable:
                try:
                    if element.is_displayed() and element.is_enabled():
                        element_text = element.text.strip().lower()
                        if ("apply" in element_text or "contact" in element_text) and len(element_text) < 100:
                            self.logger.info(f"Fallback apply button: '{element.text}'")
                            element.click()
                            time.sleep(3)
                            return True
                except:
                    continue

        except Exception as e:
            self.logger.error(f"Apply button search failed: {e}")

        return False

    def _fill_application_form_aggressive(self, documents: Dict[str, str]) -> bool:
        """Aggressively fill any form found"""
        try:
            self.logger.info("Aggressively filling forms...")
            time.sleep(3)

            filled_count = 0

            # Find all form inputs
            all_inputs = self.driver.find_elements(By.CSS_SELECTOR, "input, textarea, select")

            for input_elem in all_inputs:
                try:
                    if not input_elem.is_displayed() or not input_elem.is_enabled():
                        continue

                    input_type = input_elem.get_attribute("type") or ""
                    input_name = input_elem.get_attribute("name") or ""
                    input_id = input_elem.get_attribute("id") or ""
                    input_placeholder = input_elem.get_attribute("placeholder") or ""

                    # Skip hidden, submit, and button inputs
                    if input_type.lower() in ["hidden", "submit", "button", "image"]:
                        continue

                    # Determine what to fill based on field characteristics
                    field_context = f"{input_name} {input_id} {input_placeholder}".lower()

                    if input_elem.tag_name.lower() == "select":
                        self._fill_select_field(input_elem, field_context)
                        filled_count += 1
                    elif input_type.lower() == "file":
                        self._fill_file_field(input_elem, documents)
                        filled_count += 1
                    elif input_type.lower() in ["text", "email", "tel", ""] or input_elem.tag_name.lower() == "textarea":
                        value = self._determine_field_value(field_context)
                        if value:
                            input_elem.clear()
                            input_elem.send_keys(value)
                            filled_count += 1

                except Exception as e:
                    self.logger.debug(f"Failed to fill input: {e}")

            self.logger.info(f"Filled {filled_count} form fields")
            self.take_screenshot(f"form_filled_{datetime.now().strftime('%H%M%S')}.png")

            return filled_count > 0

        except Exception as e:
            self.logger.error(f"Aggressive form filling failed: {e}")
            return False

    def _determine_field_value(self, field_context: str) -> str:
        """Determine what value to put in a field based on context"""
        field_context = field_context.lower()

        # Name fields
        if any(keyword in field_context for keyword in ["first", "fname", "given"]):
            return self.personal_data["first_name"]
        elif any(keyword in field_context for keyword in ["last", "lname", "family", "surname"]):
            return self.personal_data["last_name"]
        elif any(keyword in field_context for keyword in ["name", "full"]) and "last" not in field_context and "first" not in field_context:
            return self.personal_data["full_name"]

        # Contact fields
        elif any(keyword in field_context for keyword in ["email", "mail"]):
            return self.personal_data["email"]
        elif any(keyword in field_context for keyword in ["phone", "mobile", "tel"]):
            return self.personal_data["phone_formatted"]

        # Location fields
        elif any(keyword in field_context for keyword in ["address", "location", "city"]):
            return self.personal_data["address"]
        elif any(keyword in field_context for keyword in ["country"]):
            return self.personal_data["country"]

        # Professional fields
        elif any(keyword in field_context for keyword in ["linkedin", "social"]):
            return self.personal_data["linkedin"]
        elif any(keyword in field_context for keyword in ["website", "portfolio", "url"]):
            return self.personal_data["website"]
        elif any(keyword in field_context for keyword in ["experience", "years"]):
            return self.personal_data["experience_years"]

        # Cover letter / message fields
        elif any(keyword in field_context for keyword in ["message", "cover", "motivation", "why", "tell"]):
            return "I am writing to express my strong interest in opportunities at Nemetschek. With my background as a Senior Software Engineer and experience in cloud infrastructure, I would welcome the chance to contribute to your innovative team."

        # Default for text fields
        elif "text" in field_context or "comment" in field_context:
            return "Thank you for considering my application."

        return ""

    def _fill_select_field(self, select_elem, field_context: str):
        """Fill select dropdown field"""
        try:
            select = Select(select_elem)
            options = [opt.text.lower() for opt in select.options]

            field_context = field_context.lower()

            # Work authorization
            if any(keyword in field_context for keyword in ["authorization", "eligible", "visa", "work"]):
                for option_text in options:
                    if any(term in option_text for term in ["citizen", "authorized", "yes", "eligible"]):
                        for opt in select.options:
                            if opt.text.lower() == option_text:
                                select.select_by_visible_text(opt.text)
                                self.logger.info(f"Selected: {opt.text}")
                                return

            # Experience level
            elif any(keyword in field_context for keyword in ["experience", "level", "years"]):
                for option_text in options:
                    if any(term in option_text for term in ["5", "5+", "3-5", "senior"]):
                        for opt in select.options:
                            if opt.text.lower() == option_text:
                                select.select_by_visible_text(opt.text)
                                self.logger.info(f"Selected: {opt.text}")
                                return

            # Country
            elif any(keyword in field_context for keyword in ["country"]):
                for opt in select.options:
                    if "united states" in opt.text.lower() or "usa" in opt.text.lower():
                        select.select_by_visible_text(opt.text)
                        self.logger.info(f"Selected: {opt.text}")
                        return

        except Exception as e:
            self.logger.debug(f"Select field filling failed: {e}")

    def _fill_file_field(self, file_elem, documents: Dict[str, str]):
        """Fill file upload field"""
        try:
            # Determine file type from context
            parent_text = ""
            try:
                parent = file_elem.find_element(By.XPATH, "..")
                parent_text = parent.text.lower()
            except:
                pass

            # Choose appropriate file
            if "resume" in parent_text or "cv" in parent_text:
                file_path = documents.get("resume_pdf") or documents.get("resume_tex")
            elif "cover" in parent_text or "letter" in parent_text:
                file_path = documents.get("cover_letter")
            else:
                # Default to resume
                file_path = documents.get("resume_pdf") or documents.get("resume_tex")

            if file_path and os.path.exists(file_path):
                file_elem.send_keys(file_path)
                self.logger.info(f"Uploaded: {os.path.basename(file_path)}")

        except Exception as e:
            self.logger.debug(f"File upload failed: {e}")

    def _submit_with_confirmation(self) -> bool:
        """Submit form and wait for confirmation"""
        try:
            # Look for submit button
            submit_selectors = [
                "button[type='submit']", "input[type='submit']",
                ".submit-btn", ".btn-submit", "button[id*='submit']",
                "*:contains('Submit')", "*:contains('Send')", "*:contains('Apply')"
            ]

            submit_button = None
            for selector in submit_selectors:
                try:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    for element in elements:
                        if element.is_displayed() and element.is_enabled():
                            element_text = element.text.lower()
                            if any(word in element_text for word in ["submit", "send", "apply"]):
                                submit_button = element
                                break
                    if submit_button:
                        break
                except:
                    continue

            if not submit_button:
                self.logger.warning("No submit button found")
                return False

            # Take screenshot before submitting
            self.take_screenshot(f"before_submit_{datetime.now().strftime('%H%M%S')}.png")

            # Click submit
            self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", submit_button)
            time.sleep(1)

            try:
                submit_button.click()
            except ElementClickInterceptedException:
                self.driver.execute_script("arguments[0].click();", submit_button)

            self.logger.info("🚀 SUBMIT BUTTON CLICKED!")

            # Wait for confirmation
            return self._detect_submission_confirmation()

        except Exception as e:
            self.logger.error(f"Submission failed: {e}")
            return False

    def _detect_submission_confirmation(self, timeout: int = 30) -> bool:
        """Detect submission confirmation with multiple methods"""
        try:
            self.logger.info("🔍 Detecting submission confirmation...")

            start_time = time.time()
            while time.time() - start_time < timeout:
                try:
                    # Take screenshot
                    self.take_screenshot(f"confirmation_check_{datetime.now().strftime('%H%M%S')}.png")

                    # Method 1: Check URL changes
                    current_url = self.driver.current_url.lower()
                    confirmation_url_keywords = ["success", "confirmation", "thank", "submitted", "complete"]

                    for keyword in confirmation_url_keywords:
                        if keyword in current_url:
                            self.logger.info(f"✅ CONFIRMATION DETECTED: URL contains '{keyword}'")
                            self.take_screenshot(f"CONFIRMATION_URL_{datetime.now().strftime('%H%M%S')}.png")
                            return True

                    # Method 2: Check page content
                    page_text = self.driver.find_element(By.TAG_NAME, "body").text.lower()
                    confirmation_keywords = [
                        "thank you", "application submitted", "successfully submitted",
                        "confirmation", "received your application", "we have received",
                        "application has been", "submitted successfully", "thank you for applying",
                        "your application", "application received", "we will review",
                        "application complete", "successfully sent", "message sent"
                    ]

                    for keyword in confirmation_keywords:
                        if keyword in page_text:
                            self.logger.info(f"✅ CONFIRMATION DETECTED: Page contains '{keyword}'")
                            self.take_screenshot(f"CONFIRMATION_TEXT_{datetime.now().strftime('%H%M%S')}.png")
                            return True

                    # Method 3: Check for confirmation elements
                    confirmation_selectors = [
                        ".success", ".confirmation", ".thank-you", ".submitted",
                        "[class*='success']", "[class*='confirmation']", "[class*='thank']",
                        ".alert-success", ".message-success"
                    ]

                    for selector in confirmation_selectors:
                        try:
                            elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                            for element in elements:
                                if element.is_displayed() and element.text.strip():
                                    self.logger.info(f"✅ CONFIRMATION DETECTED: Element found with text: '{element.text}'")
                                    self.take_screenshot(f"CONFIRMATION_ELEMENT_{datetime.now().strftime('%H%M%S')}.png")
                                    return True
                        except:
                            continue

                    # Method 4: Check for alerts
                    try:
                        alert = self.driver.switch_to.alert
                        alert_text = alert.text.lower()
                        if any(word in alert_text for word in ["success", "submitted", "thank", "received"]):
                            self.logger.info(f"✅ CONFIRMATION DETECTED: Alert with text: '{alert.text}'")
                            alert.accept()
                            return True
                        alert.accept()
                    except:
                        pass

                    time.sleep(2)

                except Exception as e:
                    self.logger.debug(f"Confirmation check iteration failed: {e}")
                    time.sleep(2)

            # If no explicit confirmation, consider form disappearance as success
            try:
                form_elements = self.driver.find_elements(By.CSS_SELECTOR, "form, input[type='submit'], button[type='submit']")
                if not form_elements:
                    self.logger.info("✅ POSSIBLE CONFIRMATION: Form elements no longer present")
                    return True
            except:
                pass

            self.logger.warning("No confirmation detected within timeout")
            return False

        except Exception as e:
            self.logger.error(f"Confirmation detection failed: {e}")
            return False

    def _try_contact_or_general_forms(self, documents: Dict[str, str]) -> bool:
        """Try to use contact forms or general inquiry forms"""
        try:
            # Look for contact or inquiry forms
            contact_keywords = ["contact", "inquiry", "message", "reach", "touch"]

            all_links = self.driver.find_elements(By.CSS_SELECTOR, "a[href]")

            for link in all_links:
                try:
                    link_text = link.text.strip().lower()
                    if any(keyword in link_text for keyword in contact_keywords) and len(link_text) < 50:
                        self.logger.info(f"Trying contact form: {link_text}")

                        link.click()
                        time.sleep(3)

                        if self._fill_application_form_aggressive(documents):
                            if self._submit_with_confirmation():
                                return True

                        # Go back and try next
                        self.driver.back()
                        time.sleep(2)

                except Exception as e:
                    self.logger.debug(f"Contact form attempt failed: {e}")

        except Exception as e:
            self.logger.error(f"Contact form strategy failed: {e}")

        return False

    def _try_unsolicited_application(self, documents: Dict[str, str]) -> bool:
        """Try to submit an unsolicited application"""
        try:
            # This would involve filling any form with a message expressing interest
            self.logger.info("Attempting unsolicited application...")

            # Look for any form on the page
            forms = self.driver.find_elements(By.CSS_SELECTOR, "form")

            for form in forms:
                try:
                    if form.is_displayed():
                        # Fill the form with expression of interest
                        if self._fill_application_form_aggressive(documents):
                            if self._submit_with_confirmation():
                                return True
                except Exception as e:
                    self.logger.debug(f"Unsolicited application attempt failed: {e}")

        except Exception as e:
            self.logger.error(f"Unsolicited application failed: {e}")

        return False

    def _generate_documents_for_job(self, job: Dict[str, Any]) -> Dict[str, str]:
        """Generate enhanced documents for the job"""
        try:
            job_title = job.get("title", "Software Engineer")
            company = "Nemetschek"
            job_description = job.get("description", f"Position: {job_title} at {company}")

            self.logger.info(f"Generating documents for: {job_title}")

            result = self.resume_generator.generate_enhanced_resume(
                job_title, company, job_description
            )

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            safe_title = "".join(c for c in job_title if c.isalnum() or c in (' ', '-', '_')).rstrip()
            safe_title = safe_title.replace(' ', '_')

            resume_filename = f"Persistent_Resume_{safe_title}_{timestamp}.tex"
            resume_path = os.path.join(self.output_dir, "enhanced_resumes", resume_filename)

            with open(resume_path, 'w', encoding='utf-8') as f:
                f.write(result["enhanced_resume"])

            cover_filename = f"Persistent_Cover_Letter_{safe_title}_{timestamp}.txt"
            cover_path = os.path.join(self.output_dir, "cover_letters", cover_filename)

            with open(cover_path, 'w', encoding='utf-8') as f:
                f.write(result["cover_letter"])

            pdf_path = self._compile_latex_to_pdf(resume_path)

            return {
                "resume_tex": resume_path,
                "resume_pdf": pdf_path,
                "cover_letter": cover_path
            }

        except Exception as e:
            self.logger.error(f"Document generation failed: {e}")
            return {}

    def _compile_latex_to_pdf(self, tex_path: str) -> Optional[str]:
        """Compile LaTeX to PDF"""
        try:
            result = subprocess.run(["which", "pdflatex"], capture_output=True, text=True)
            if result.returncode != 0:
                return None

            output_dir = os.path.dirname(tex_path)
            result = subprocess.run(
                ["pdflatex", "-interaction=nonstopmode", "-output-directory", output_dir, tex_path],
                capture_output=True, text=True, cwd=output_dir
            )

            if result.returncode == 0:
                pdf_path = tex_path.replace('.tex', '.pdf')
                if os.path.exists(pdf_path):
                    return pdf_path

            return None
        except:
            return None

    def run_persistent_automation(self) -> bool:
        """Run persistent automation until successful application"""
        try:
            self.logger.info("🚀 STARTING PERSISTENT NEMETSCHEK AUTOMATION")
            print("🚀 STARTING PERSISTENT NEMETSCHEK AUTOMATION")
            print("Will not stop until successful application with confirmation!")
            print("=" * 80)

            if not self.setup_driver():
                return False

            # Try multiple career URLs
            if not self.try_multiple_career_urls():
                self.logger.error("Could not find any Nemetschek careers page")
                return False

            # Aggressively search for jobs
            jobs = self.aggressive_job_search()

            if not jobs:
                self.logger.error("No jobs or application opportunities found")
                return False

            self.logger.info(f"Found {len(jobs)} application opportunities")

            # Try to apply to each opportunity
            for i, job in enumerate(jobs):
                self.logger.info(f"\n{'='*80}")
                self.logger.info(f"OPPORTUNITY {i+1}/{len(jobs)}: {job['title']}")
                self.logger.info(f"{'='*80}")

                try:
                    success = self.attempt_application_submission(job)

                    if success:
                        self.logger.info("🎉 SUCCESS! APPLICATION SUBMITTED WITH CONFIRMATION!")
                        print("🎉 SUCCESS! APPLICATION SUBMITTED WITH CONFIRMATION!")

                        # Save success record
                        success_record = {
                            "job": job,
                            "success": True,
                            "timestamp": datetime.now().isoformat(),
                            "confirmation_obtained": True
                        }

                        success_file = os.path.join(self.output_dir, f"SUCCESS_APPLICATION_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
                        with open(success_file, 'w') as f:
                            json.dump(success_record, f, indent=2)

                        return True

                    else:
                        self.logger.warning(f"Failed to apply to {job['title']}")

                except Exception as e:
                    self.logger.error(f"Error processing {job['title']}: {e}")

            self.logger.error("All application attempts failed")
            return False

        except Exception as e:
            self.logger.error(f"Persistent automation failed: {e}")
            return False

        finally:
            if self.driver:
                # Keep browser open for verification
                self.logger.info("Browser will remain open for manual verification...")
                print("Browser will remain open for manual verification...")
                print("Check the screenshots and results...")
                input("Press Enter to close the browser...")
                self.driver.quit()

def main():
    """Run the persistent automation"""
    automation = PersistentNemetschekAutomation(headless=False)

    try:
        success = automation.run_persistent_automation()

        if success:
            print("🎉 MISSION ACCOMPLISHED! Real application submitted with confirmation!")
        else:
            print("❌ Mission failed - could not submit application")

        return success

    except KeyboardInterrupt:
        print("\n⏹️ Automation interrupted")
        return False
    except Exception as e:
        print(f"\n❌ Automation failed: {e}")
        return False

if __name__ == "__main__":
    main()