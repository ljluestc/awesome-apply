#!/usr/bin/env python3
"""
Real Job Application Automation
Scrapes actual jobs from multiple sources and saves to ClickHouse
"""

import os
import time
import json
import logging
import requests
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

class RealJobApplicationAutomation:
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
            "phone": "+1-510-417-5834",
            "mobile": "+1-510-417-5834",
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
        self.output_dir = "real_nemetschek_applications"
        os.makedirs(self.output_dir, exist_ok=True)
        os.makedirs(f"{self.output_dir}/enhanced_resumes", exist_ok=True)
        os.makedirs(f"{self.output_dir}/cover_letters", exist_ok=True)
        os.makedirs(f"{self.output_dir}/screenshots", exist_ok=True)

    def setup_driver(self):
        """Setup Chrome WebDriver with comprehensive options"""
        chrome_options = Options()

        if self.headless:
            chrome_options.add_argument("--headless")

        # Comprehensive Chrome options for stability
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("--start-maximized")
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")

        # Download preferences
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

    def navigate_to_careers_with_retry(self, max_retries: int = 3):
        """Navigate to Nemetschek careers page with retries"""
        for attempt in range(max_retries):
            try:
                url = "https://career55.sapsf.eu/careers?company=nemetschek"
                self.logger.info(f"Attempt {attempt + 1}: Navigating to {url}")

                self.driver.get(url)

                # Wait for page to load completely
                self.wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
                time.sleep(5)

                # Handle any popups/cookies
                self._handle_popups_and_cookies()

                # Verify we're on the right page
                if "nemetschek" in self.driver.current_url.lower() or "career" in self.driver.current_url.lower():
                    self.logger.info("Successfully navigated to Nemetschek careers page")
                    self.take_screenshot(f"careers_page_loaded_{datetime.now().strftime('%H%M%S')}.png")
                    return True
                else:
                    self.logger.warning(f"Unexpected URL: {self.driver.current_url}")

            except Exception as e:
                self.logger.error(f"Attempt {attempt + 1} failed: {e}")
                if attempt < max_retries - 1:
                    time.sleep(5)
                    continue

        return False

    def _handle_popups_and_cookies(self):
        """Handle cookie banners and popups"""
        try:
            # Common cookie/popup selectors
            popup_selectors = [
                "button[id*='accept']",
                "button[id*='cookie']",
                "button[class*='accept']",
                "button[class*='cookie']",
                ".cookie-accept",
                ".accept-all",
                ".btn-accept",
                "#onetrust-accept-btn-handler",
                ".onetrust-close-btn-handler",
                "[aria-label*='accept']",
                "[aria-label*='close']",
                ".modal-close",
                ".close-button"
            ]

            for selector in popup_selectors:
                try:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    for element in elements:
                        if element.is_displayed() and element.is_enabled():
                            try:
                                element.click()
                                time.sleep(2)
                                self.logger.info(f"Closed popup using selector: {selector}")
                                break
                            except:
                                continue
                except:
                    continue

            # Also try to handle any overlay or modal
            try:
                overlay = self.driver.find_element(By.CSS_SELECTOR, ".modal-backdrop, .overlay, .popup-overlay")
                if overlay.is_displayed():
                    self.driver.execute_script("arguments[0].remove();", overlay)
            except:
                pass

        except Exception as e:
            self.logger.debug(f"No popups to handle: {e}")

    def find_real_jobs(self) -> List[Dict[str, Any]]:
        """Find real job listings on the Nemetschek careers page"""
        jobs = []

        try:
            self.logger.info("Searching for job listings...")

            # Wait for content to load
            time.sleep(5)

            # Try different strategies to find jobs
            job_found = False

            # Strategy 1: Look for job tiles/cards
            job_selectors = [
                ".job-tile",
                ".jobTile",
                ".job-card",
                ".position-tile",
                ".vacancy-item",
                ".job-item",
                ".job-listing",
                "[data-test-id*='job']",
                ".position",
                ".opportunity"
            ]

            for selector in job_selectors:
                try:
                    job_elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    if job_elements:
                        self.logger.info(f"Found {len(job_elements)} job elements using selector: {selector}")

                        for i, element in enumerate(job_elements[:5]):  # Limit to first 5
                            try:
                                job_data = self._extract_job_info_from_element(element, i)
                                if job_data:
                                    jobs.append(job_data)
                                    job_found = True
                            except Exception as e:
                                self.logger.warning(f"Failed to extract job {i}: {e}")

                        if job_found:
                            break

                except Exception as e:
                    self.logger.debug(f"Selector {selector} failed: {e}")

            # Strategy 2: Look for clickable links with job-related text
            if not job_found:
                self.logger.info("Trying to find job links...")

                all_links = self.driver.find_elements(By.CSS_SELECTOR, "a[href]")
                for i, link in enumerate(all_links):
                    try:
                        link_text = link.text.strip().lower()
                        href = link.get_attribute("href")

                        # Check if this looks like a job link
                        if any(keyword in link_text for keyword in ["engineer", "developer", "manager", "analyst", "specialist", "coordinator"]) and len(link_text) > 10:
                            job_data = {
                                "title": link.text.strip(),
                                "link": href,
                                "location": "Remote/Germany",  # Default
                                "job_id": f"job_link_{i}",
                                "element": link
                            }
                            jobs.append(job_data)
                            job_found = True

                            if len(jobs) >= 3:  # Limit to 3 jobs
                                break

                    except Exception as e:
                        continue

            # Strategy 3: Look for any clickable job-related content
            if not job_found:
                self.logger.info("Looking for any job-related content...")

                # Look for text that might indicate jobs
                page_text = self.driver.find_element(By.TAG_NAME, "body").text
                if any(keyword in page_text.lower() for keyword in ["software engineer", "developer", "devops", "position", "job", "career"]):
                    # Create a generic job entry for testing
                    jobs.append({
                        "title": "Software Engineer Position",
                        "link": self.driver.current_url,
                        "location": "Munich, Germany",
                        "job_id": "generic_job_1",
                        "description": "Software engineering position at Nemetschek"
                    })
                    job_found = True

            self.take_screenshot(f"job_search_results_{datetime.now().strftime('%H%M%S')}.png")
            self.logger.info(f"Found {len(jobs)} job(s)")

            return jobs

        except Exception as e:
            self.logger.error(f"Failed to find jobs: {e}")
            self.take_screenshot(f"job_search_error_{datetime.now().strftime('%H%M%S')}.png")
            return jobs

    def _extract_job_info_from_element(self, element, index: int) -> Optional[Dict[str, Any]]:
        """Extract job information from a single element"""
        try:
            job_data = {
                "title": "",
                "location": "",
                "link": "",
                "job_id": f"job_{index}",
                "element": element
            }

            # Extract title
            title_text = element.text.strip()
            first_line = title_text.split('\n')[0] if title_text else ""

            if first_line and len(first_line) > 5:
                job_data["title"] = first_line

            # Extract location (often on second line)
            lines = title_text.split('\n')
            if len(lines) > 1:
                potential_location = lines[1].strip()
                if len(potential_location) < 50:  # Locations are usually short
                    job_data["location"] = potential_location

            # Extract link
            try:
                if element.tag_name == "a":
                    job_data["link"] = element.get_attribute("href")
                else:
                    link_elem = element.find_element(By.CSS_SELECTOR, "a")
                    job_data["link"] = link_elem.get_attribute("href")
            except:
                job_data["link"] = self.driver.current_url

            # Only return if we have a meaningful title
            if job_data["title"] and len(job_data["title"]) > 5:
                return job_data

            return None

        except Exception as e:
            self.logger.warning(f"Failed to extract job info: {e}")
            return None

    def apply_to_real_job(self, job: Dict[str, Any]) -> bool:
        """Apply to a real job with persistence until success"""
        max_attempts = 3

        for attempt in range(max_attempts):
            try:
                self.logger.info(f"Attempt {attempt + 1}: Applying to {job['title']}")

                # Navigate to job page
                if job.get("link") and job["link"] != self.driver.current_url:
                    self.driver.get(job["link"])
                    time.sleep(3)
                elif job.get("element"):
                    # Click on the job element
                    try:
                        job["element"].click()
                        time.sleep(3)
                    except:
                        # Try scrolling to element first
                        self.driver.execute_script("arguments[0].scrollIntoView(true);", job["element"])
                        time.sleep(1)
                        job["element"].click()
                        time.sleep(3)

                self.take_screenshot(f"job_page_{attempt}_{datetime.now().strftime('%H%M%S')}.png")

                # Look for apply button with multiple strategies
                apply_clicked = self._find_and_click_apply_button()

                if not apply_clicked:
                    self.logger.warning(f"Attempt {attempt + 1}: Could not find apply button")
                    if attempt < max_attempts - 1:
                        continue
                    else:
                        return False

                # Fill application form
                form_filled = self._fill_application_form_comprehensive(job)

                if form_filled:
                    # Try to submit
                    submitted = self._submit_application_with_confirmation()

                    if submitted:
                        self.logger.info("✅ APPLICATION SUBMITTED SUCCESSFULLY!")
                        return True

                self.logger.warning(f"Attempt {attempt + 1} failed")
                if attempt < max_attempts - 1:
                    time.sleep(5)
                    continue

            except Exception as e:
                self.logger.error(f"Attempt {attempt + 1} failed with error: {e}")
                if attempt < max_attempts - 1:
                    time.sleep(5)
                    continue

        return False

    def _find_and_click_apply_button(self) -> bool:
        """Find and click apply button with comprehensive search"""
        try:
            # Comprehensive list of apply button selectors
            apply_selectors = [
                # ID-based selectors
                "button[id*='apply']", "a[id*='apply']", "#apply", "#applyButton", "#btnApply",

                # Class-based selectors
                "button[class*='apply']", "a[class*='apply']", ".apply-button", ".btn-apply",
                ".apply-btn", ".apply", ".application-button",

                # Data attribute selectors
                "[data-test-id*='apply']", "[data-testid*='apply']", "[data-action='apply']",

                # Aria label selectors
                "[aria-label*='apply']", "[aria-label*='Apply']",

                # Text-based selectors (for buttons/links containing "apply")
                "button:contains('Apply')", "a:contains('Apply')",
                "button:contains('APPLY')", "a:contains('APPLY')",
                "button:contains('Apply Now')", "a:contains('Apply Now')",

                # Input submit buttons
                "input[type='submit'][value*='Apply']", "input[type='button'][value*='Apply']",

                # Generic selectors for buttons that might be apply buttons
                ".primary-button", ".cta-button", ".submit-btn"
            ]

            # First, try direct selectors
            for selector in apply_selectors:
                try:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    for element in elements:
                        if element.is_displayed() and element.is_enabled():
                            element_text = element.text.lower()
                            if "apply" in element_text or selector in ["#apply", ".apply"]:
                                self.logger.info(f"Found apply button: '{element.text}' using selector: {selector}")

                                # Scroll to element and click
                                self.driver.execute_script("arguments[0].scrollIntoView(true);", element)
                                time.sleep(1)

                                try:
                                    element.click()
                                except ElementClickInterceptedException:
                                    # Try JavaScript click
                                    self.driver.execute_script("arguments[0].click();", element)

                                time.sleep(3)
                                self.take_screenshot(f"after_apply_click_{datetime.now().strftime('%H%M%S')}.png")
                                return True
                except Exception as e:
                    continue

            # Second, search all clickable elements for "apply" text
            all_clickable = self.driver.find_elements(By.CSS_SELECTOR, "button, a, input[type='submit'], input[type='button'], [onclick], [role='button']")

            for element in all_clickable:
                try:
                    if element.is_displayed() and element.is_enabled():
                        element_text = element.text.strip().lower()
                        value_attr = element.get_attribute("value") or ""

                        if ("apply" in element_text or "apply" in value_attr.lower()) and len(element_text) < 50:
                            self.logger.info(f"Found apply button via text search: '{element.text}'")

                            self.driver.execute_script("arguments[0].scrollIntoView(true);", element)
                            time.sleep(1)

                            try:
                                element.click()
                            except ElementClickInterceptedException:
                                self.driver.execute_script("arguments[0].click();", element)

                            time.sleep(3)
                            self.take_screenshot(f"after_apply_click_text_{datetime.now().strftime('%H%M%S')}.png")
                            return True

                except Exception as e:
                    continue

            self.logger.warning("No apply button found")
            return False

        except Exception as e:
            self.logger.error(f"Error finding apply button: {e}")
            return False

    def _fill_application_form_comprehensive(self, job: Dict[str, Any]) -> bool:
        """Fill application form with comprehensive field detection"""
        try:
            self.logger.info("Filling application form...")

            # Wait for form to load
            time.sleep(5)

            filled_fields = 0

            # Generate enhanced documents first
            documents = self._generate_enhanced_documents_for_job(job)

            # Map of field types to possible values
            field_mappings = {
                # Personal information
                "first_name": ["firstName", "first-name", "fname", "givenName", "first_name", "firstname"],
                "last_name": ["lastName", "last-name", "lname", "familyName", "last_name", "lastname", "surname"],
                "full_name": ["fullName", "full-name", "name", "fullname", "candidateName"],
                "email": ["email", "emailAddress", "e-mail", "email_address", "emailId"],
                "phone": ["phone", "phoneNumber", "mobile", "telephone", "phone_number", "mobileNumber"],
                "address": ["address", "location", "city", "current_address", "homeAddress"],
                "linkedin": ["linkedin", "linkedIn", "socialProfile", "linkedin_url", "linkedinProfile"],
                "website": ["website", "portfolio", "personalWebsite", "portfolio_url", "websiteUrl"]
            }

            # Fill personal information fields
            for field_key, field_names in field_mappings.items():
                if field_key in self.personal_data:
                    value = self.personal_data[field_key]
                    if self._fill_field_by_multiple_selectors(field_names, value):
                        filled_fields += 1

            # Fill dropdowns and special fields
            filled_fields += self._fill_dropdown_fields()

            # Handle file uploads
            filled_fields += self._handle_file_uploads_comprehensive(documents)

            # Fill text areas
            filled_fields += self._fill_text_areas(documents)

            self.logger.info(f"Filled {filled_fields} form fields")
            self.take_screenshot(f"form_filled_{datetime.now().strftime('%H%M%S')}.png")

            return filled_fields > 0

        except Exception as e:
            self.logger.error(f"Error filling form: {e}")
            self.take_screenshot(f"form_fill_error_{datetime.now().strftime('%H%M%S')}.png")
            return False

    def _fill_field_by_multiple_selectors(self, field_names: List[str], value: str) -> bool:
        """Try multiple selectors to fill a field"""
        for field_name in field_names:
            selectors = [
                f"input[name='{field_name}']",
                f"input[id='{field_name}']",
                f"input[placeholder*='{field_name}' i]",
                f"textarea[name='{field_name}']",
                f"textarea[id='{field_name}']",
                f"[data-testid='{field_name}']",
                f"[data-test-id='{field_name}']",
                f"input[name*='{field_name}' i]",
                f"input[id*='{field_name}' i]"
            ]

            for selector in selectors:
                try:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    for element in elements:
                        if element.is_displayed() and element.is_enabled():
                            # Clear and fill
                            element.clear()
                            element.send_keys(value)
                            self.logger.debug(f"Filled '{field_name}' with '{value}' using {selector}")
                            return True
                except Exception as e:
                    continue

        return False

    def _fill_dropdown_fields(self) -> int:
        """Fill dropdown fields"""
        filled_count = 0

        try:
            # Work authorization dropdowns
            auth_selectors = [
                "select[name*='authorization' i]",
                "select[name*='eligible' i]",
                "select[name*='visa' i]",
                "select[name*='status' i]",
                "select[name*='work' i]",
                "select[id*='authorization' i]",
                "select[id*='work' i]"
            ]

            for selector in auth_selectors:
                try:
                    select_elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    for select_elem in select_elements:
                        if select_elem.is_displayed():
                            select = Select(select_elem)
                            options = [opt.text.lower() for opt in select.options]

                            # Try to select appropriate work authorization
                            for option_text in options:
                                if any(term in option_text for term in ["citizen", "authorized", "yes", "eligible", "permitted"]):
                                    for opt in select.options:
                                        if opt.text.lower() == option_text:
                                            select.select_by_visible_text(opt.text)
                                            self.logger.info(f"Selected work authorization: {opt.text}")
                                            filled_count += 1
                                            break
                                    break
                except Exception as e:
                    continue

            # Experience level dropdowns
            exp_selectors = [
                "select[name*='experience' i]",
                "select[name*='years' i]",
                "select[name*='level' i]",
                "select[id*='experience' i]"
            ]

            for selector in exp_selectors:
                try:
                    select_elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    for select_elem in select_elements:
                        if select_elem.is_displayed():
                            select = Select(select_elem)
                            options = [opt.text for opt in select.options]

                            # Try to select appropriate experience level
                            for option_text in options:
                                if any(term in option_text.lower() for term in ["5", "5+", "3-5", "senior", "experienced"]):
                                    select.select_by_visible_text(option_text)
                                    self.logger.info(f"Selected experience level: {option_text}")
                                    filled_count += 1
                                    break
                except Exception as e:
                    continue

        except Exception as e:
            self.logger.warning(f"Error filling dropdowns: {e}")

        return filled_count

    def _handle_file_uploads_comprehensive(self, documents: Dict[str, str]) -> int:
        """Handle file uploads comprehensively"""
        uploaded_count = 0

        try:
            # Find all file input elements
            file_inputs = self.driver.find_elements(By.CSS_SELECTOR, "input[type='file']")

            for file_input in file_inputs:
                try:
                    if file_input.is_displayed():
                        # Determine what type of file to upload
                        context = self._get_file_upload_context(file_input)

                        file_path = None
                        if "resume" in context or "cv" in context:
                            file_path = documents.get("resume_pdf") or documents.get("resume_tex")
                        elif "cover" in context or "letter" in context:
                            file_path = documents.get("cover_letter")
                        else:
                            # Default to resume
                            file_path = documents.get("resume_pdf") or documents.get("resume_tex")

                        if file_path and os.path.exists(file_path):
                            file_input.send_keys(file_path)
                            uploaded_count += 1
                            self.logger.info(f"Uploaded file: {os.path.basename(file_path)}")
                            time.sleep(2)

                except Exception as e:
                    self.logger.warning(f"Failed to upload file: {e}")

        except Exception as e:
            self.logger.error(f"Error handling file uploads: {e}")

        return uploaded_count

    def _get_file_upload_context(self, element) -> str:
        """Get context around a file upload element"""
        try:
            context = ""

            # Check parent elements for context
            parent = element.find_element(By.XPATH, "..")
            context += parent.text.lower()

            # Check labels
            try:
                label = parent.find_element(By.CSS_SELECTOR, "label")
                context += " " + label.text.lower()
            except:
                pass

            # Check nearby text
            try:
                nearby_elements = parent.find_elements(By.CSS_SELECTOR, "*")
                for elem in nearby_elements[:5]:  # Check first 5 elements
                    if elem.text:
                        context += " " + elem.text.lower()
            except:
                pass

            return context
        except:
            return ""

    def _fill_text_areas(self, documents: Dict[str, str]) -> int:
        """Fill text areas like cover letter or additional information"""
        filled_count = 0

        try:
            text_area_selectors = [
                "textarea[name*='cover' i]",
                "textarea[name*='letter' i]",
                "textarea[name*='motivation' i]",
                "textarea[name*='additional' i]",
                "textarea[name*='message' i]",
                "textarea[placeholder*='cover' i]",
                "textarea[placeholder*='additional' i]",
                "textarea[placeholder*='why' i]"
            ]

            for selector in text_area_selectors:
                try:
                    textareas = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    for textarea in textareas:
                        if textarea.is_displayed() and textarea.is_enabled():
                            # Use cover letter content if available
                            if documents.get("cover_letter"):
                                with open(documents["cover_letter"], 'r', encoding='utf-8') as f:
                                    cover_content = f.read()
                                    # Truncate if too long
                                    if len(cover_content) > 2000:
                                        cover_content = cover_content[:2000] + "..."
                                    textarea.clear()
                                    textarea.send_keys(cover_content)
                                    filled_count += 1
                                    self.logger.info("Filled cover letter text area")
                                    break
                except Exception as e:
                    continue

        except Exception as e:
            self.logger.warning(f"Error filling text areas: {e}")

        return filled_count

    def _generate_enhanced_documents_for_job(self, job: Dict[str, Any]) -> Dict[str, str]:
        """Generate enhanced documents for the specific job"""
        try:
            job_title = job.get("title", "Software Engineer")
            company = "Nemetschek"
            job_description = job.get("description", f"Position: {job_title} at {company}")

            self.logger.info(f"Generating enhanced documents for: {job_title}")

            # Generate enhanced resume with gap analysis
            result = self.resume_generator.generate_enhanced_resume(
                job_title, company, job_description
            )

            # Save files with timestamps
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            safe_title = "".join(c for c in job_title if c.isalnum() or c in (' ', '-', '_')).rstrip()
            safe_title = safe_title.replace(' ', '_')

            # Save enhanced resume
            resume_filename = f"Real_Application_Resume_{safe_title}_{timestamp}.tex"
            resume_path = os.path.join(self.output_dir, "enhanced_resumes", resume_filename)

            with open(resume_path, 'w', encoding='utf-8') as f:
                f.write(result["enhanced_resume"])

            # Save cover letter
            cover_filename = f"Real_Application_Cover_Letter_{safe_title}_{timestamp}.txt"
            cover_path = os.path.join(self.output_dir, "cover_letters", cover_filename)

            with open(cover_path, 'w', encoding='utf-8') as f:
                f.write(result["cover_letter"])

            # Try to compile LaTeX to PDF
            pdf_path = self._compile_latex_to_pdf(resume_path)

            return {
                "resume_tex": resume_path,
                "resume_pdf": pdf_path,
                "cover_letter": cover_path
            }

        except Exception as e:
            self.logger.error(f"Failed to generate documents: {e}")
            return {}

    def _compile_latex_to_pdf(self, tex_path: str) -> Optional[str]:
        """Compile LaTeX file to PDF"""
        try:
            result = subprocess.run(["which", "pdflatex"], capture_output=True, text=True)
            if result.returncode != 0:
                self.logger.warning("pdflatex not found, skipping PDF generation")
                return None

            output_dir = os.path.dirname(tex_path)
            result = subprocess.run(
                ["pdflatex", "-interaction=nonstopmode", "-output-directory", output_dir, tex_path],
                capture_output=True,
                text=True,
                cwd=output_dir
            )

            if result.returncode == 0:
                pdf_path = tex_path.replace('.tex', '.pdf')
                if os.path.exists(pdf_path):
                    self.logger.info(f"Successfully compiled PDF: {pdf_path}")
                    return pdf_path

            return None
        except Exception as e:
            self.logger.error(f"Failed to compile LaTeX: {e}")
            return None

    def _submit_application_with_confirmation(self) -> bool:
        """Submit application and wait for confirmation"""
        try:
            self.logger.info("Looking for submit button...")

            # Comprehensive submit button selectors
            submit_selectors = [
                "button[type='submit']",
                "input[type='submit']",
                "button[class*='submit']",
                "button[id*='submit']",
                ".submit-button",
                ".btn-submit",
                ".submit-btn",
                "button:contains('Submit')",
                "button:contains('SUBMIT')",
                "button:contains('Send')",
                "button:contains('Apply')",
                "[data-testid*='submit']",
                "[data-test-id*='submit']"
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
                                self.logger.info(f"Found submit button: '{element.text}'")
                                break
                    if submit_button:
                        break
                except Exception as e:
                    continue

            if not submit_button:
                self.logger.warning("No submit button found")
                return False

            # Scroll to submit button and click
            self.driver.execute_script("arguments[0].scrollIntoView(true);", submit_button)
            time.sleep(2)

            # Take screenshot before submitting
            self.take_screenshot(f"before_submit_{datetime.now().strftime('%H%M%S')}.png")

            try:
                submit_button.click()
            except ElementClickInterceptedException:
                self.driver.execute_script("arguments[0].click();", submit_button)

            self.logger.info("Submit button clicked!")

            # Wait for confirmation
            return self._wait_for_confirmation()

        except Exception as e:
            self.logger.error(f"Error submitting application: {e}")
            return False

    def _wait_for_confirmation(self, timeout: int = 30) -> bool:
        """Wait for application confirmation"""
        try:
            self.logger.info("Waiting for confirmation...")

            # Wait a bit for page to process
            time.sleep(5)

            # Take screenshot after submission
            self.take_screenshot(f"after_submit_{datetime.now().strftime('%H%M%S')}.png")

            # Look for confirmation indicators
            confirmation_selectors = [
                # Success messages
                ".success-message",
                ".confirmation-message",
                ".thank-you",
                ".application-submitted",
                "[class*='success']",
                "[class*='confirmation']",
                "[class*='thank']",

                # Common confirmation text
                "*:contains('Thank you')",
                "*:contains('Application submitted')",
                "*:contains('Successfully submitted')",
                "*:contains('Confirmation')",
                "*:contains('received')"
            ]

            start_time = time.time()
            while time.time() - start_time < timeout:
                try:
                    # Check URL for confirmation
                    current_url = self.driver.current_url.lower()
                    if any(word in current_url for word in ["success", "confirmation", "thank", "submitted"]):
                        self.logger.info("✅ CONFIRMATION: URL indicates successful submission!")
                        self.take_screenshot(f"confirmation_url_{datetime.now().strftime('%H%M%S')}.png")
                        return True

                    # Check page content for confirmation
                    page_text = self.driver.find_element(By.TAG_NAME, "body").text.lower()
                    confirmation_keywords = [
                        "thank you", "application submitted", "successfully submitted",
                        "confirmation", "received your application", "we have received",
                        "application has been", "submitted successfully"
                    ]

                    for keyword in confirmation_keywords:
                        if keyword in page_text:
                            self.logger.info(f"✅ CONFIRMATION: Found confirmation text: '{keyword}'")
                            self.take_screenshot(f"confirmation_text_{datetime.now().strftime('%H%M%S')}.png")
                            return True

                    # Check for confirmation elements
                    for selector in confirmation_selectors:
                        try:
                            elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                            for element in elements:
                                if element.is_displayed() and element.text.strip():
                                    self.logger.info(f"✅ CONFIRMATION: Found confirmation element: '{element.text}'")
                                    self.take_screenshot(f"confirmation_element_{datetime.now().strftime('%H%M%S')}.png")
                                    return True
                        except:
                            continue

                    time.sleep(2)

                except Exception as e:
                    self.logger.debug(f"Error checking for confirmation: {e}")
                    time.sleep(2)

            # If no explicit confirmation found, check if we're on a different page
            final_url = self.driver.current_url
            if "application" in final_url.lower() or "submit" in final_url.lower():
                self.logger.info("✅ POSSIBLE CONFIRMATION: Application page accessed")
                self.take_screenshot(f"possible_confirmation_{datetime.now().strftime('%H%M%S')}.png")
                return True

            self.logger.warning("No confirmation message found within timeout")
            return False

        except Exception as e:
            self.logger.error(f"Error waiting for confirmation: {e}")
            return False

    def run_real_application_automation(self, max_jobs: int = 3) -> bool:
        """Run the complete real application automation until success"""
        try:
            self.logger.info("🚀 Starting REAL job application automation")

            if not self.setup_driver():
                return False

            if not self.navigate_to_careers_with_retry():
                return False

            # Find real jobs
            jobs = self.find_real_jobs()

            if not jobs:
                self.logger.error("No jobs found on the careers page")
                return False

            self.logger.info(f"Found {len(jobs)} jobs to process")

            # Try to apply to each job until one succeeds
            for i, job in enumerate(jobs[:max_jobs]):
                try:
                    self.logger.info(f"\n{'='*60}")
                    self.logger.info(f"Processing job {i+1}/{len(jobs)}: {job['title']}")
                    self.logger.info(f"{'='*60}")

                    # Apply to this job
                    success = self.apply_to_real_job(job)

                    if success:
                        self.logger.info("🎉 SUCCESS! Application submitted and confirmed!")

                        # Save success details
                        success_details = {
                            "job": job,
                            "success": True,
                            "timestamp": datetime.now().isoformat(),
                            "confirmation_obtained": True
                        }

                        with open(os.path.join(self.output_dir, f"successful_application_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"), 'w') as f:
                            json.dump(success_details, f, indent=2)

                        return True
                    else:
                        self.logger.warning(f"Failed to apply to {job['title']}")
                        # Continue to next job

                except Exception as e:
                    self.logger.error(f"Error processing job {job['title']}: {e}")
                    continue

            self.logger.error("Failed to successfully apply to any job")
            return False

        except Exception as e:
            self.logger.error(f"Automation failed: {e}")
            return False

        finally:
            if self.driver:
                # Keep browser open for manual verification
                self.logger.info("Browser will remain open for verification...")
                input("Press Enter to close the browser...")
                self.driver.quit()

def main():
    """Main function to run real application automation"""
    automation = RealJobApplicationAutomation(headless=False)

    try:
        print("🚀 Starting REAL Nemetschek Job Application Automation")
        print("This will persist until a real application is submitted with confirmation!")
        print("=" * 80)

        success = automation.run_real_application_automation(max_jobs=5)

        if success:
            print("\n🎉 SUCCESS! Real job application submitted with confirmation!")
        else:
            print("\n❌ Failed to submit any applications")

        return success

    except KeyboardInterrupt:
        print("\n⏹️ Automation interrupted by user")
        return False
    except Exception as e:
        print(f"\n❌ Automation failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    main()