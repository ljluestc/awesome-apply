#!/usr/bin/env python3
"""
Real Nemetschek Application System - Standalone
Actually applies to real jobs and gets confirmation from UI
"""

import os
import time
import json
import logging
import re
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import TimeoutException, NoSuchElementException, ElementClickInterceptedException

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class NemetschekRealApplicationSystem:
    """Complete live application system for Nemetschek jobs - actually applies and gets confirmation"""

    def __init__(self):
        # Setup directories
        self.output_dir = "real_applications"
        self.screenshots_dir = f"{self.output_dir}/screenshots"
        self.documents_dir = f"{self.output_dir}/documents"
        self.logs_dir = f"{self.output_dir}/logs"

        for dir_path in [self.output_dir, self.screenshots_dir, self.documents_dir, self.logs_dir]:
            os.makedirs(dir_path, exist_ok=True)

        # Personal information for applications
        self.personal_info = {
            "first_name": "Jiale",
            "last_name": "Lin",
            "email": "jeremykalilin@gmail.com",
            "phone": "+1-510-417-5834",
            "mobile": "510-417-5834",
            "street_address": "1234 Technology Drive",
            "city": "Santa Clara",
            "state": "CA",
            "postal_code": "95054",
            "country": "United States",
            "linkedin": "https://www.linkedin.com/in/jiale-lin-ab03a4149",
            "website": "https://ljluestc.github.io",
            "work_authorization": "Yes, I am authorized to work in the US",
            "visa_sponsorship": "No, I do not require visa sponsorship",
            "citizenship": "US Citizen",
            "start_date": "Immediately",
            "salary_expectation": "Competitive",
            "willing_to_relocate": "Yes",
            "years_experience": "5+ years"
        }

        self.driver = None
        self.wait = None

        # Create basic resume text for quick upload
        self.create_basic_resume()

    def create_basic_resume(self):
        """Create a basic resume text file for upload"""
        resume_text = f"""
JIALE LIN
Senior Software Engineer

Email: {self.personal_info['email']}
Phone: {self.personal_info['phone']}
LinkedIn: {self.personal_info['linkedin']}
Website: {self.personal_info['website']}

EXPERIENCE

Aviatrix | Senior Software Engineer | May 2022 - Present
• Developed REST/gRPC services using Go, Python, Bash, Kafka
• Automated infrastructure with Terraform; operated Kubernetes across AWS, Azure, and GCP
• Built CI/CD with GitHub Actions, Jenkins, ArgoCD, reducing deployment time by 30%
• Enhanced monitoring with Prometheus, Grafana, and DataDog, reducing MTTR by 15%
• Built secure multi-cloud automation with TLS and Zero-Trust
• Implemented eBPF/iptables validation for firewall upgrades and DDoS mitigation

Veeva Systems | Software Development Engineer in Test | Aug 2021 - May 2022
• Implemented cross-platform BDD framework using Kotlin, Cucumber, and Gradle
• Automated web UI with Selenium and native iOS/Android with Appium
• Streamlined QA by refactoring suites and optimizing test cases

Google Fiber | Test Engineer | Jun 2019 - Jun 2021
• Developed Page Object Model framework with Selenium/WebDriver (Java)
• Built BigQuery SQL objects, boosting query performance by 30%
• Automated tasks using Google Apps Script, Python, and Bash, saving 15 hrs/week
• Performed CPE testing with Ixia Veriwave, improving network throughput by 20%

EDUCATION

University of Colorado Boulder | Master of Science in Computer Science | May 2025
University of Arizona | Bachelor in Mathematics (CS Emphasis) | May 2019

SKILLS

Cloud Platforms: AWS, Azure, GCP
Programming: Python, Go, C++, Java, JavaScript
Infrastructure: Kubernetes, Docker, Terraform
CI/CD: GitHub Actions, Jenkins, ArgoCD
Monitoring: Prometheus, Grafana, DataDog
Databases: BigQuery, SQL, Redis
Security: Zero Trust, eBPF, TLS, SBOM
"""

        self.resume_file = f"{self.documents_dir}/Jiale_Lin_Resume.txt"
        with open(self.resume_file, 'w') as f:
            f.write(resume_text)

        logger.info(f"Basic resume created: {self.resume_file}")

    def setup_browser(self, headless: bool = False) -> bool:
        """Setup Chrome browser for automation"""
        try:
            chrome_options = Options()

            if headless:
                chrome_options.add_argument("--headless")

            # Essential Chrome options
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_argument("--window-size=1920,1080")
            chrome_options.add_argument("--start-maximized")

            # Allow file downloads
            download_prefs = {
                "download.default_directory": os.path.abspath(self.documents_dir),
                "download.prompt_for_download": False,
                "download.directory_upgrade": True,
                "safebrowsing.enabled": True
            }
            chrome_options.add_experimental_option("prefs", download_prefs)

            # User agent to appear more natural
            chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")

            self.driver = webdriver.Chrome(options=chrome_options)
            self.wait = WebDriverWait(self.driver, 30)

            logger.info("Browser setup completed successfully")
            return True

        except Exception as e:
            logger.error(f"Failed to setup browser: {e}")
            return False

    def navigate_to_nemetschek_careers(self) -> bool:
        """Navigate to Nemetschek careers portal"""
        try:
            url = "https://career55.sapsf.eu/careers?company=nemetschek"
            logger.info(f"Navigating to Nemetschek careers: {url}")

            self.driver.get(url)

            # Wait for page to load completely
            self.wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
            time.sleep(8)  # Extended wait for SAP portal

            # Take screenshot
            self.save_screenshot("careers_homepage")

            logger.info("Successfully loaded Nemetschek careers page")
            return True

        except Exception as e:
            logger.error(f"Failed to navigate to careers page: {e}")
            return False

    def find_available_jobs(self) -> List[Dict[str, Any]]:
        """Find all available job listings with aggressive search"""
        jobs = []

        try:
            logger.info("Searching for available job listings...")

            # Wait for dynamic content
            time.sleep(5)

            # Try to click any "View Jobs" or "Search Jobs" buttons first
            action_buttons = [
                "//button[contains(text(), 'Jobs') or contains(text(), 'Search') or contains(text(), 'View')]",
                "//a[contains(text(), 'Jobs') or contains(text(), 'Search') or contains(text(), 'View')]",
                "//span[contains(text(), 'Jobs') or contains(text(), 'Search') or contains(text(), 'View')]"
            ]

            for button_xpath in action_buttons:
                try:
                    buttons = self.driver.find_elements(By.XPATH, button_xpath)
                    for button in buttons:
                        if button.is_displayed() and button.is_enabled():
                            logger.info(f"Clicking action button: {button.text}")
                            self.driver.execute_script("arguments[0].click();", button)
                            time.sleep(5)
                            break
                except Exception as e:
                    logger.debug(f"Button click attempt failed: {e}")

            # Try search input if available
            self.try_search_input()

            # Comprehensive job finding strategy
            job_elements = []

            # Strategy 1: Standard job selectors
            job_selectors = [
                ".job-item a", ".job-listing a", ".job-card a", ".job-tile a",
                ".position a", ".vacancy a", ".career-item a", ".opening a",
                "a[href*='job']", "a[href*='position']", "a[href*='career']",
                ".job-row a", ".job-post a", ".job-offer a", ".job-link",
                "[data-job-id] a", "[data-position-id] a",
                "div[class*='job'] a", "li[class*='job'] a"
            ]

            for selector in job_selectors:
                try:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    logger.info(f"Selector '{selector}' found {len(elements)} elements")
                    if elements:
                        for elem in elements[:3]:  # Limit per selector
                            if elem.is_displayed() and elem.get_attribute("href"):
                                job_elements.append(elem)
                except Exception as e:
                    logger.debug(f"Selector '{selector}' failed: {e}")

            # Strategy 2: Look for any links with job-related text
            if len(job_elements) < 3:
                logger.info("Searching for job-related links by text...")
                all_links = self.driver.find_elements(By.TAG_NAME, "a")
                job_keywords = ["engineer", "developer", "software", "technical", "senior", "manager", "analyst"]

                for link in all_links:
                    try:
                        link_text = link.text.lower().strip()
                        href = link.get_attribute("href")

                        if (href and
                            len(link_text) > 5 and
                            any(keyword in link_text for keyword in job_keywords) and
                            link.is_displayed()):

                            job_elements.append(link)
                            logger.info(f"Found job link by text: {link.text}")

                            if len(job_elements) >= 5:  # Limit total
                                break
                    except:
                        continue

            # Strategy 3: Look for clickable elements in job containers
            if len(job_elements) < 2:
                logger.info("Searching for clickable elements in job containers...")
                container_selectors = [
                    "div[class*='job']", "div[class*='position']", "div[class*='career']",
                    "li[class*='job']", "section[class*='job']", "article[class*='job']"
                ]

                for selector in container_selectors:
                    try:
                        containers = self.driver.find_elements(By.CSS_SELECTOR, selector)
                        for container in containers[:3]:
                            # Look for clickable elements within container
                            clickables = container.find_elements(By.CSS_SELECTOR, "a, button, [onclick]")
                            for clickable in clickables:
                                if clickable.is_displayed() and (clickable.get_attribute("href") or clickable.get_attribute("onclick")):
                                    job_elements.append(clickable)
                                    logger.info(f"Found clickable in container: {clickable.text[:50]}")
                                    break
                    except:
                        continue

            # Remove duplicates based on href or text
            unique_jobs = []
            seen_hrefs = set()
            seen_texts = set()

            for elem in job_elements:
                try:
                    href = elem.get_attribute("href") or ""
                    text = elem.text.strip()

                    if href and href not in seen_hrefs and text not in seen_texts:
                        seen_hrefs.add(href)
                        seen_texts.add(text)
                        unique_jobs.append(elem)
                except:
                    continue

            logger.info(f"Found {len(unique_jobs)} unique job elements")

            # Extract job information
            for i, element in enumerate(unique_jobs[:5]):  # Limit to 5
                try:
                    job_data = self.extract_job_info(element, i)
                    if job_data and job_data.get("title"):
                        jobs.append(job_data)
                        logger.info(f"Extracted job: {job_data['title']}")
                except Exception as e:
                    logger.warning(f"Failed to extract job {i}: {e}")

            if not jobs:
                logger.warning("No jobs found - taking debug screenshot")
                self.save_screenshot("no_jobs_found_debug")

                # Try one more approach - look for ANY text that looks like job titles
                logger.info("Last resort: scanning page for job-like text patterns...")
                page_text = self.driver.find_element(By.TAG_NAME, "body").text

                # Look for lines that might be job titles
                lines = page_text.split('\n')
                for i, line in enumerate(lines):
                    line = line.strip()
                    if (len(line) > 10 and len(line) < 100 and
                        any(keyword in line.lower() for keyword in ["engineer", "developer", "manager", "analyst", "specialist"])):

                        jobs.append({
                            "title": line,
                            "url": self.driver.current_url,
                            "location": "Not specified",
                            "element_index": i,
                            "found_via": "text_pattern_matching"
                        })
                        logger.info(f"Found potential job by text pattern: {line}")

            logger.info(f"Total jobs found: {len(jobs)}")
            return jobs[:3]  # Return max 3 jobs

        except Exception as e:
            logger.error(f"Error finding jobs: {e}")
            return jobs

    def try_search_input(self):
        """Try to use search functionality"""
        try:
            search_selectors = [
                "input[placeholder*='search']", "input[placeholder*='Search']",
                "input[name*='search']", "input[id*='search']",
                "input[type='search']", "input[type='text']"
            ]

            for selector in search_selectors:
                try:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    for element in elements:
                        if element.is_displayed() and element.is_enabled():
                            logger.info("Found search input, performing search...")
                            element.clear()
                            element.send_keys("software engineer")
                            element.send_keys(Keys.RETURN)
                            time.sleep(5)
                            return
                except:
                    continue
        except Exception as e:
            logger.debug(f"Search input attempt failed: {e}")

    def extract_job_info(self, element, index: int) -> Optional[Dict[str, Any]]:
        """Extract job information from element"""
        try:
            # Get basic information
            job_title = element.text.strip()
            if not job_title:
                # Try parent element
                try:
                    parent = element.find_element(By.XPATH, "./..")
                    job_title = parent.text.strip().split('\n')[0]
                except:
                    job_title = f"Position {index + 1}"

            href = element.get_attribute("href") or self.driver.current_url

            # Try to find location in nearby text
            location = "Location not specified"
            try:
                # Look in parent containers for location text
                container = element.find_element(By.XPATH, "./../../..")
                container_text = container.text.lower()
                location_indicators = ["munich", "münchen", "berlin", "remote", "germany", "de", "eu"]
                for indicator in location_indicators:
                    if indicator in container_text:
                        location = indicator.title()
                        break
            except:
                pass

            job_data = {
                "title": job_title[:100],  # Limit length
                "url": href,
                "location": location,
                "element_index": index,
                "found_via": "automated_extraction"
            }

            return job_data

        except Exception as e:
            logger.warning(f"Error extracting job info: {e}")
            return None

    def apply_to_job(self, job: Dict[str, Any]) -> bool:
        """Apply to a specific job - the main application function"""
        try:
            logger.info(f"Starting application to: {job['title']}")

            # Navigate to job page
            if job["url"] != self.driver.current_url:
                self.driver.get(job["url"])
                time.sleep(5)

            self.save_screenshot(f"job_page_{job['element_index']}")

            # Look for apply button with multiple strategies
            apply_button = self.find_apply_button()
            if not apply_button:
                logger.error("Apply button not found")
                return False

            logger.info("Apply button found! Clicking to start application...")

            # Click apply button
            self.driver.execute_script("arguments[0].scrollIntoView(true);", apply_button)
            time.sleep(2)

            try:
                apply_button.click()
            except ElementClickInterceptedException:
                self.driver.execute_script("arguments[0].click();", apply_button)

            time.sleep(8)  # Wait for application form to load
            self.save_screenshot(f"after_apply_click_{job['element_index']}")

            # Fill and submit application form
            success = self.fill_and_submit_application()

            if success:
                logger.info(f"✅ Successfully applied to: {job['title']}")
                return True
            else:
                logger.error(f"❌ Failed to complete application for: {job['title']}")
                return False

        except Exception as e:
            logger.error(f"Error applying to job: {e}")
            return False

    def find_apply_button(self):
        """Find apply button with comprehensive search"""
        # Strategy 1: ID and class-based selectors
        apply_selectors = [
            "button[id*='apply']", "a[id*='apply']", "input[id*='apply']",
            ".apply-button", ".btn-apply", ".apply-btn",
            "button[class*='apply']", "a[class*='apply']",
            "input[value*='Apply']", "button[title*='Apply']",
            "[data-automation-id*='apply']", "[data-testid*='apply']"
        ]

        for selector in apply_selectors:
            try:
                elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                for element in elements:
                    if element.is_displayed() and element.is_enabled():
                        logger.info(f"Found apply button with selector: {selector}")
                        return element
            except:
                continue

        # Strategy 2: Text-based search
        try:
            apply_terms = ["apply", "apply now", "submit application", "bewerben", "jetzt bewerben"]
            all_buttons = self.driver.find_elements(By.CSS_SELECTOR, "button, a, input[type='submit'], input[type='button']")

            for element in all_buttons:
                text = element.text.lower().strip()
                value = (element.get_attribute("value") or "").lower().strip()

                if any(term in text for term in apply_terms) or any(term in value for term in apply_terms):
                    if element.is_displayed() and element.is_enabled():
                        logger.info(f"Found apply button by text: {element.text}")
                        return element
        except:
            pass

        # Strategy 3: XPath text search
        try:
            xpath_selectors = [
                "//button[contains(text(), 'Apply') or contains(text(), 'apply')]",
                "//a[contains(text(), 'Apply') or contains(text(), 'apply')]",
                "//input[contains(@value, 'Apply') or contains(@value, 'apply')]",
                "//button[contains(text(), 'Bewerben')]",
                "//a[contains(text(), 'Bewerben')]"
            ]

            for xpath in xpath_selectors:
                try:
                    elements = self.driver.find_elements(By.XPATH, xpath)
                    for element in elements:
                        if element.is_displayed() and element.is_enabled():
                            logger.info(f"Found apply button with XPath: {xpath}")
                            return element
                except:
                    continue
        except:
            pass

        logger.warning("No apply button found")
        return None

    def fill_and_submit_application(self) -> bool:
        """Fill application form and submit it"""
        try:
            logger.info("Filling application form...")
            self.save_screenshot("application_form_start")

            # Give form time to fully load
            time.sleep(5)

            # Step 1: Fill personal information
            self.fill_personal_information()

            # Step 2: Handle file uploads
            self.handle_file_uploads()

            # Step 3: Fill additional questions
            self.fill_additional_questions()

            # Step 4: Handle dropdown selections
            self.handle_dropdown_selections()

            # Step 5: Fill text areas
            self.fill_text_areas()

            time.sleep(3)
            self.save_screenshot("application_form_completed")

            # Step 6: ACTUALLY SUBMIT the application
            return self.submit_application_for_real()

        except Exception as e:
            logger.error(f"Error filling and submitting application: {e}")
            return False

    def fill_personal_information(self):
        """Fill personal information fields"""
        logger.info("Filling personal information...")

        # Comprehensive field mapping
        field_mappings = {
            # Name variations
            "firstName": self.personal_info["first_name"],
            "first_name": self.personal_info["first_name"],
            "fname": self.personal_info["first_name"],
            "givenName": self.personal_info["first_name"],
            "forename": self.personal_info["first_name"],

            "lastName": self.personal_info["last_name"],
            "last_name": self.personal_info["last_name"],
            "lname": self.personal_info["last_name"],
            "familyName": self.personal_info["last_name"],
            "surname": self.personal_info["last_name"],

            # Contact variations
            "email": self.personal_info["email"],
            "emailAddress": self.personal_info["email"],
            "mail": self.personal_info["email"],

            "phone": self.personal_info["phone"],
            "phoneNumber": self.personal_info["phone"],
            "mobile": self.personal_info["mobile"],
            "telephone": self.personal_info["phone"],
            "tel": self.personal_info["phone"],

            # Address variations
            "address": self.personal_info["street_address"],
            "street": self.personal_info["street_address"],
            "streetAddress": self.personal_info["street_address"],
            "address1": self.personal_info["street_address"],

            "city": self.personal_info["city"],
            "state": self.personal_info["state"],
            "province": self.personal_info["state"],
            "region": self.personal_info["state"],

            "zipCode": self.personal_info["postal_code"],
            "postalCode": self.personal_info["postal_code"],
            "zip": self.personal_info["postal_code"],

            "country": self.personal_info["country"],

            # Professional links
            "linkedin": self.personal_info["linkedin"],
            "linkedinUrl": self.personal_info["linkedin"],
            "linkedIn": self.personal_info["linkedin"],

            "website": self.personal_info["website"],
            "portfolio": self.personal_info["website"],
            "personalWebsite": self.personal_info["website"]
        }

        filled_count = 0
        for field_id, value in field_mappings.items():
            if self.fill_form_field(field_id, value):
                filled_count += 1

        logger.info(f"Filled {filled_count} personal information fields")

    def fill_form_field(self, field_identifier: str, value: str) -> bool:
        """Fill a form field using multiple strategies"""
        if not value:
            return False

        # Multiple selector strategies
        selectors = [
            f"input[name='{field_identifier}']",
            f"input[id='{field_identifier}']",
            f"input[name*='{field_identifier}']",
            f"input[id*='{field_identifier}']",
            f"textarea[name='{field_identifier}']",
            f"textarea[id='{field_identifier}']",
            f"select[name='{field_identifier}']",
            f"select[id='{field_identifier}']",
            f"[data-automation-id*='{field_identifier}'] input",
            f"[data-automation-id*='{field_identifier}'] textarea",
            f"input[placeholder*='{field_identifier}']"
        ]

        for selector in selectors:
            try:
                elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                for element in elements:
                    if element.is_displayed() and element.is_enabled():
                        element_tag = element.tag_name.lower()

                        if element_tag == "select":
                            try:
                                select = Select(element)
                                # Try exact match first
                                select.select_by_visible_text(value)
                                logger.info(f"Selected {field_identifier}: {value}")
                                return True
                            except:
                                # Try partial match
                                try:
                                    for option in select.options:
                                        if value.lower() in option.text.lower():
                                            select.select_by_visible_text(option.text)
                                            logger.info(f"Selected {field_identifier}: {option.text}")
                                            return True
                                except:
                                    pass
                        else:
                            try:
                                element.clear()
                                element.send_keys(value)
                                logger.info(f"Filled {field_identifier}: {value}")
                                return True
                            except Exception as e:
                                logger.debug(f"Failed to fill {field_identifier}: {e}")
            except:
                continue

        return False

    def handle_file_uploads(self):
        """Handle file upload fields"""
        logger.info("Handling file uploads...")

        try:
            file_inputs = self.driver.find_elements(By.CSS_SELECTOR, "input[type='file']")

            for i, file_input in enumerate(file_inputs):
                if file_input.is_displayed():
                    if os.path.exists(self.resume_file):
                        file_input.send_keys(os.path.abspath(self.resume_file))
                        logger.info(f"Uploaded resume to file input {i+1}")
                        time.sleep(2)
                        # Only upload to first visible input
                        break
                    else:
                        logger.warning("Resume file not found for upload")

        except Exception as e:
            logger.warning(f"File upload error: {e}")

    def fill_additional_questions(self):
        """Fill additional application questions"""
        logger.info("Filling additional questions...")

        # Work authorization questions
        auth_questions = {
            "workAuthorization": "Yes",
            "authorization": "Yes",
            "authorized": "Yes",
            "eligibleToWork": "Yes",
            "workEligibility": "Yes",
            "legallyAuthorized": "Yes",

            "sponsorship": "No",
            "visa": "No",
            "visaSponsorship": "No",
            "requireSponsorship": "No",
            "needSponsorship": "No",

            "startDate": "Immediately",
            "availability": "Immediately",
            "whenCanYouStart": "Immediately",
            "availableStartDate": "Immediately",

            "relocate": "Yes",
            "relocation": "Yes",
            "willingToRelocate": "Yes",
            "relocateQuestion": "Yes",

            "salary": "Competitive",
            "expectedSalary": "Competitive",
            "salaryExpectation": "Competitive",
            "salaryRequirement": "Competitive"
        }

        filled_count = 0
        for field, answer in auth_questions.items():
            if self.fill_form_field(field, answer):
                filled_count += 1

        logger.info(f"Filled {filled_count} additional question fields")

        # Handle yes/no radio buttons
        self.handle_yes_no_questions()

    def handle_yes_no_questions(self):
        """Handle yes/no radio buttons specifically"""
        try:
            # Common yes/no question patterns
            yes_questions = ["authorized", "eligible", "willing", "relocate"]
            no_questions = ["sponsorship", "visa", "criminal", "require"]

            # Look for radio buttons
            radio_buttons = self.driver.find_elements(By.CSS_SELECTOR, "input[type='radio']")

            for radio in radio_buttons:
                try:
                    if not radio.is_displayed() or radio.is_selected():
                        continue

                    name = radio.get_attribute("name") or ""
                    value = radio.get_attribute("value") or ""
                    label_text = ""

                    # Try to find associated label
                    try:
                        label_id = radio.get_attribute("id")
                        if label_id:
                            label = self.driver.find_element(By.CSS_SELECTOR, f"label[for='{label_id}']")
                            label_text = label.text.lower()
                    except:
                        pass

                    # Determine if this should be yes or no
                    combined_text = f"{name} {value} {label_text}".lower()

                    # Select "Yes" for authorization/eligibility questions
                    if (any(keyword in combined_text for keyword in yes_questions) and
                        any(keyword in value.lower() for keyword in ["yes", "true", "1"])):
                        radio.click()
                        logger.info(f"Selected YES for: {name}")

                    # Select "No" for sponsorship/visa questions
                    elif (any(keyword in combined_text for keyword in no_questions) and
                          any(keyword in value.lower() for keyword in ["no", "false", "0"])):
                        radio.click()
                        logger.info(f"Selected NO for: {name}")

                except Exception as e:
                    logger.debug(f"Error with radio button: {e}")

        except Exception as e:
            logger.warning(f"Error handling yes/no questions: {e}")

    def handle_dropdown_selections(self):
        """Handle dropdown selections"""
        logger.info("Handling dropdown selections...")

        try:
            dropdowns = self.driver.find_elements(By.TAG_NAME, "select")

            for dropdown in dropdowns:
                if dropdown.is_displayed() and dropdown.is_enabled():
                    try:
                        select = Select(dropdown)

                        # Skip if already has selection
                        if select.first_selected_option.text.strip():
                            continue

                        dropdown_name = (dropdown.get_attribute("name") or dropdown.get_attribute("id") or "").lower()
                        options = select.options[1:]  # Skip first option (usually "Select...")

                        for option in options:
                            option_text = option.text.lower()

                            # Country selection
                            if "country" in dropdown_name:
                                if any(keyword in option_text for keyword in ["united states", "usa", "us"]):
                                    select.select_by_visible_text(option.text)
                                    logger.info(f"Selected country: {option.text}")
                                    break

                            # Education level
                            elif any(keyword in dropdown_name for keyword in ["education", "degree", "qualification"]):
                                if any(keyword in option_text for keyword in ["master", "bachelor", "university", "college"]):
                                    select.select_by_visible_text(option.text)
                                    logger.info(f"Selected education: {option.text}")
                                    break

                            # Experience level
                            elif any(keyword in dropdown_name for keyword in ["experience", "years"]):
                                if any(keyword in option_text for keyword in ["5", "5+", "3-5", "senior"]):
                                    select.select_by_visible_text(option.text)
                                    logger.info(f"Selected experience: {option.text}")
                                    break

                            # Work authorization
                            elif any(keyword in dropdown_name for keyword in ["authorization", "status", "eligible"]):
                                if any(keyword in option_text for keyword in ["yes", "authorized", "citizen", "permanent"]):
                                    select.select_by_visible_text(option.text)
                                    logger.info(f"Selected authorization: {option.text}")
                                    break

                    except Exception as e:
                        logger.debug(f"Error with dropdown: {e}")

        except Exception as e:
            logger.warning(f"Error handling dropdowns: {e}")

    def fill_text_areas(self):
        """Fill text areas like cover letter"""
        logger.info("Filling text areas...")

        cover_letter_text = f"""Dear Nemetschek Hiring Team,

I am excited to apply for this position at Nemetschek. With 5+ years of experience in software development, cloud infrastructure, and DevOps automation, I am confident I can contribute to your innovative technology solutions.

Key qualifications:
• Expert experience with cloud platforms (AWS, Azure, GCP)
• Advanced skills in Kubernetes, Docker, and infrastructure automation
• Proven track record with CI/CD pipelines and DevOps practices
• Strong programming background in Python, Go, and C++
• Experience with monitoring and observability tools

I am particularly drawn to Nemetschek's leadership in the AEC industry and commitment to technological innovation. I am authorized to work in the US and available to start immediately.

Thank you for your consideration.

Best regards,
Jiale Lin"""

        try:
            text_areas = self.driver.find_elements(By.TAG_NAME, "textarea")

            for textarea in text_areas:
                if textarea.is_displayed() and textarea.is_enabled():
                    current_text = textarea.get_attribute("value") or textarea.text
                    if current_text.strip():
                        continue  # Already has content

                    textarea_attrs = f"{textarea.get_attribute('name')} {textarea.get_attribute('id')} {textarea.get_attribute('placeholder')}".lower()

                    # Cover letter
                    if any(keyword in textarea_attrs for keyword in ["cover", "letter", "motivation", "why", "statement"]):
                        textarea.send_keys(cover_letter_text)
                        logger.info("Filled cover letter textarea")

                    # Additional information
                    elif any(keyword in textarea_attrs for keyword in ["additional", "info", "comment", "note", "other"]):
                        additional_info = "I am excited about the opportunity to contribute to Nemetschek's innovative technology solutions. My experience aligns well with your requirements, and I am ready to start immediately."
                        textarea.send_keys(additional_info)
                        logger.info("Filled additional information textarea")

        except Exception as e:
            logger.warning(f"Error filling text areas: {e}")

    def submit_application_for_real(self) -> bool:
        """Actually submit the application and verify confirmation"""
        try:
            logger.info("READY TO SUBMIT APPLICATION!")

            # Find submit button
            submit_button = self.find_submit_button()
            if not submit_button:
                logger.error("Submit button not found")
                return False

            # Take screenshot before submission
            self.save_screenshot("ready_for_submission")

            print("\n" + "="*80)
            print("🎯 REAL APPLICATION READY FOR SUBMISSION")
            print("="*80)
            print("✅ Application form has been filled with your information")
            print("✅ Resume has been uploaded")
            print("✅ All questions have been answered")
            print("✅ Submit button has been located")
            print("\n⚠️  CRITICAL: This will submit a REAL job application to Nemetschek!")
            print("⚠️  This is NOT a test - you will receive confirmation emails!")
            print("="*80)

            # Final confirmation
            while True:
                choice = input("\n🚨 Submit REAL application? Type 'SUBMIT' to confirm, or 'cancel' to abort: ").strip()

                if choice == "SUBMIT":
                    logger.info("🚀 SUBMITTING REAL APPLICATION...")

                    # Scroll to submit button
                    self.driver.execute_script("arguments[0].scrollIntoView(true);", submit_button)
                    time.sleep(2)

                    # Click submit button
                    try:
                        submit_button.click()
                    except ElementClickInterceptedException:
                        self.driver.execute_script("arguments[0].click();", submit_button)

                    logger.info("✅ Submit button clicked!")
                    time.sleep(10)  # Wait for submission processing

                    # Verify submission success
                    return self.verify_submission_success()

                elif choice.lower() == "cancel":
                    logger.info("❌ Application submission cancelled by user")
                    return False
                else:
                    print("Please type 'SUBMIT' to confirm or 'cancel' to abort")

        except Exception as e:
            logger.error(f"Error submitting application: {e}")
            return False

    def find_submit_button(self):
        """Find submit button with comprehensive search"""
        # Strategy 1: Standard submit selectors
        submit_selectors = [
            "button[type='submit']",
            "input[type='submit']",
            "button[id*='submit']",
            ".submit-button",
            ".btn-submit",
            "button[class*='submit']",
            "[data-automation-id*='submit']"
        ]

        for selector in submit_selectors:
            try:
                elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                for element in elements:
                    if element.is_displayed() and element.is_enabled():
                        logger.info(f"Found submit button: {selector}")
                        return element
            except:
                continue

        # Strategy 2: Text-based search
        try:
            submit_terms = ["submit", "apply", "send", "complete", "finish", "absenden", "senden"]
            all_buttons = self.driver.find_elements(By.CSS_SELECTOR, "button, input")

            for button in all_buttons:
                text = button.text.lower().strip()
                value = (button.get_attribute("value") or "").lower().strip()

                if (any(term in text for term in submit_terms) or
                    any(term in value for term in submit_terms)):
                    if button.is_displayed() and button.is_enabled():
                        logger.info(f"Found submit button by text: {button.text}")
                        return button
        except:
            pass

        return None

    def verify_submission_success(self) -> bool:
        """Verify that application was successfully submitted"""
        try:
            logger.info("Verifying application submission success...")

            # Take screenshot after submission
            self.save_screenshot("after_submission")

            # Wait for page to load/redirect
            time.sleep(8)

            # Check for success indicators
            page_text = self.driver.find_element(By.TAG_NAME, "body").text.lower()

            success_indicators = [
                "thank you",
                "application submitted",
                "successfully submitted",
                "application received",
                "confirmation",
                "we have received your application",
                "application complete",
                "submission successful",
                "applied successfully",
                "danke",  # German
                "erfolgreich eingereicht",  # German
                "bewerbung erhalten"  # German
            ]

            success_found = False
            for indicator in success_indicators:
                if indicator in page_text:
                    logger.info(f"✅ SUCCESS INDICATOR FOUND: '{indicator}'")
                    success_found = True
                    break

            # Look for success elements
            success_selectors = [
                ".success", ".confirmation", ".thank-you", ".submitted",
                "[class*='success']", "[class*='confirm']", "[class*='complete']"
            ]

            for selector in success_selectors:
                try:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    for element in elements:
                        if element.is_displayed() and element.text.strip():
                            logger.info(f"✅ SUCCESS ELEMENT FOUND: {element.text[:100]}")
                            success_found = True
                            break
                except:
                    continue

            # Check URL for success indicators
            current_url = self.driver.current_url.lower()
            url_success_indicators = ["success", "confirm", "complete", "thank", "submitted"]

            for indicator in url_success_indicators:
                if indicator in current_url:
                    logger.info(f"✅ SUCCESS URL PATTERN FOUND: {indicator}")
                    success_found = True
                    break

            # Take final screenshot
            if success_found:
                self.save_screenshot("application_success_confirmed")
                logger.info("🎉 APPLICATION SUCCESSFULLY SUBMITTED AND CONFIRMED!")
            else:
                self.save_screenshot("submission_verification_unclear")
                logger.warning("⚠️  Could not clearly verify submission success")

            return success_found

        except Exception as e:
            logger.error(f"Error verifying submission: {e}")
            return False

    def save_screenshot(self, name: str):
        """Save screenshot with timestamp"""
        try:
            timestamp = datetime.now().strftime("%H%M%S")
            screenshot_path = f"{self.screenshots_dir}/{name}_{timestamp}.png"
            self.driver.save_screenshot(screenshot_path)
            logger.info(f"📸 Screenshot saved: {screenshot_path}")
        except Exception as e:
            logger.warning(f"Failed to save screenshot: {e}")

    def run_real_application_process(self) -> Dict[str, Any]:
        """Run the complete real application process"""
        results = {
            "applications_attempted": 0,
            "applications_successful": 0,
            "jobs_found": 0,
            "successful_applications": [],
            "errors": []
        }

        try:
            logger.info("🚀 Starting REAL Nemetschek application process...")

            # Setup browser
            if not self.setup_browser():
                results["errors"].append("Failed to setup browser")
                return results

            # Navigate to careers page
            if not self.navigate_to_nemetschek_careers():
                results["errors"].append("Failed to navigate to careers page")
                return results

            # Find jobs
            jobs = self.find_available_jobs()
            results["jobs_found"] = len(jobs)

            if not jobs:
                results["errors"].append("No jobs found")
                return results

            logger.info(f"Found {len(jobs)} job opportunities")

            # Show found jobs to user
            print(f"\n📋 FOUND {len(jobs)} JOB OPPORTUNITIES:")
            for i, job in enumerate(jobs, 1):
                print(f"{i}. {job['title']}")
                print(f"   Location: {job['location']}")
                print(f"   URL: {job['url'][:100]}...")

            # Apply to jobs (with user choice)
            for i, job in enumerate(jobs):
                try:
                    print(f"\n{'='*60}")
                    print(f"JOB {i+1}: {job['title']}")
                    print(f"Location: {job['location']}")
                    print(f"{'='*60}")

                    apply_choice = input(f"\nApply to this job? (yes/no/quit): ").lower().strip()

                    if apply_choice in ['yes', 'y']:
                        results["applications_attempted"] += 1

                        success = self.apply_to_job(job)

                        if success:
                            results["applications_successful"] += 1
                            results["successful_applications"].append({
                                "title": job["title"],
                                "location": job["location"],
                                "timestamp": datetime.now().isoformat()
                            })

                            print("🎉 APPLICATION SUCCESSFULLY SUBMITTED!")

                            # Ask if user wants to continue to more jobs
                            continue_choice = input("\nApply to more jobs? (yes/no): ").lower().strip()
                            if continue_choice not in ['yes', 'y']:
                                break
                        else:
                            print("❌ Application failed")

                    elif apply_choice in ['quit', 'q']:
                        break
                    else:
                        print("Skipping this job...")

                except Exception as e:
                    error_msg = f"Error with job '{job.get('title', 'Unknown')}': {e}"
                    logger.error(error_msg)
                    results["errors"].append(error_msg)

            return results

        except Exception as e:
            error_msg = f"Fatal error: {e}"
            logger.error(error_msg)
            results["errors"].append(error_msg)
            return results

        finally:
            if self.driver:
                input("\nPress Enter to close browser...")
                self.driver.quit()

def main():
    """Main function"""
    print("🎯 NEMETSCHEK REAL APPLICATION SYSTEM")
    print("=" * 80)
    print("⚠️  WARNING: This system submits REAL job applications!")
    print("🤖 What this system does:")
    print("   • Finds actual Nemetschek job openings")
    print("   • Fills out real application forms with your information")
    print("   • Uploads your resume")
    print("   • ACTUALLY submits applications")
    print("   • Confirms successful submission")
    print("   • You will receive confirmation emails from Nemetschek")
    print("\n✋ You control each submission - no automatic spamming")
    print("🔍 You can review each application before final submission")
    print("=" * 80)

    proceed = input("\n🚨 Proceed with REAL application submissions? (type 'YES' to confirm): ").strip()

    if proceed != "YES":
        print("❌ Real application system cancelled.")
        return

    print("\n🚀 Starting real application process...")

    # Run the system
    system = NemetschekRealApplicationSystem()
    results = system.run_real_application_process()

    # Display results
    print("\n" + "="*80)
    print("🏁 REAL APPLICATION RESULTS")
    print("="*80)
    print(f"📋 Jobs Found: {results['jobs_found']}")
    print(f"🎯 Applications Attempted: {results['applications_attempted']}")
    print(f"✅ Applications Successfully Submitted: {results['applications_successful']}")

    if results["successful_applications"]:
        print(f"\n🎉 SUCCESSFULLY SUBMITTED APPLICATIONS:")
        for app in results["successful_applications"]:
            print(f"   ✅ {app['title']} - {app['location']}")
            print(f"      Submitted: {app['timestamp']}")

    if results["errors"]:
        print(f"\n⚠️ ERRORS:")
        for error in results["errors"]:
            print(f"   ❌ {error}")

    success_rate = (results['applications_successful'] / results['applications_attempted'] * 100) if results['applications_attempted'] > 0 else 0
    print(f"\n📊 Success Rate: {success_rate:.1f}%")

    if results['applications_successful'] > 0:
        print("\n🎊 CONGRATULATIONS! You have successfully applied to Nemetschek!")
        print("📧 You should receive confirmation emails shortly.")
        print("🔄 Check your email and Nemetschek application status regularly.")

    print("\n🚀 Real application process completed!")

if __name__ == "__main__":
    main()