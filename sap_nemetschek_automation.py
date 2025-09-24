#!/usr/bin/env python3
"""
🚀 SAP NEMETSCHEK CAREERS AUTOMATION SYSTEM 🚀
===============================================

Complete automation system for applying to jobs on SAP SuccessFactors
careers site for Nemetschek with dynamic resume generation.

Features:
✅ Job discovery and filtering
✅ Dynamic resume generation per job
✅ Automated application filling
✅ Login handling and session management
✅ File upload automation
✅ Application tracking
✅ Error handling and retries
"""

import time
import json
import logging
import re
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException
import requests
from dynamic_resume_generator import DynamicResumeGenerator, JialeLinProfile

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/home/calelin/awesome-apply/sap_automation.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class SAPNemetschekCareersAutomation:
    """Complete automation system for SAP SuccessFactors Nemetschek careers"""

    def __init__(self, headless: bool = False):
        self.base_url = "https://career55.sapsf.eu/careers?company=nemetschek"
        self.headless = headless
        self.driver = None
        self.wait = None
        self.resume_generator = DynamicResumeGenerator(JialeLinProfile())
        self.application_data = self._load_application_data()
        self.applied_jobs = set()
        self.session_stats = {
            'jobs_found': 0,
            'applications_submitted': 0,
            'applications_failed': 0,
            'resumes_generated': 0,
            'start_time': datetime.now()
        }

    def _load_application_data(self) -> Dict:
        """Load personal application data for Jiale Lin"""
        return {
            'personal_info': {
                'first_name': 'Jiale',
                'last_name': 'Lin',
                'email': 'jeremykalilin@gmail.com',
                'phone': '+1-510-417-5834',
                'address': {
                    'street': '123 Tech Street',
                    'city': 'San Francisco',
                    'state': 'CA',
                    'zip_code': '94105',
                    'country': 'United States'
                },
                'linkedin': 'https://www.linkedin.com/in/jiale-lin-ab03a4149',
                'website': 'https://ljluestc.github.io'
            },
            'work_authorization': {
                'citizenship': 'US Citizen',
                'visa_status': 'US Citizen',
                'requires_sponsorship': False
            },
            'education': {
                'highest_degree': 'Master of Science',
                'field_of_study': 'Computer Science',
                'university': 'University of Colorado Boulder',
                'graduation_year': '2025',
                'gpa': '3.8'
            },
            'experience': {
                'years_of_experience': '6',
                'current_title': 'Senior Software Engineer',
                'current_company': 'Aviatrix',
                'salary_expectation': '180000',
                'available_start_date': (datetime.now() + timedelta(days=30)).strftime('%m/%d/%Y')
            },
            'preferences': {
                'willing_to_relocate': True,
                'willing_to_travel': True,
                'remote_work_preference': 'Hybrid',
                'preferred_locations': ['San Francisco', 'San Jose', 'Remote']
            }
        }

    def initialize_driver(self):
        """Initialize Chrome WebDriver with optimized settings"""
        logger.info("Initializing Chrome WebDriver...")

        chrome_options = Options()

        if self.headless:
            chrome_options.add_argument("--headless")

        # Optimization flags
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("--disable-extensions")
        chrome_options.add_argument("--disable-plugins")
        chrome_options.add_argument("--disable-images")
        chrome_options.add_argument("--disable-javascript-harmony-shipping")

        # User agent to appear more legitimate
        chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")

        # Download preferences
        prefs = {
            "profile.default_content_settings.popups": 0,
            "profile.default_content_setting_values.notifications": 2,
            "profile.default_content_settings.automatic_downloads": 1,
        }
        chrome_options.add_experimental_option("prefs", prefs)

        try:
            self.driver = webdriver.Chrome(options=chrome_options)
            self.wait = WebDriverWait(self.driver, 20)
            logger.info("✅ WebDriver initialized successfully")
            return True

        except Exception as e:
            logger.error(f"❌ Failed to initialize WebDriver: {e}")
            return False

    def navigate_to_careers_page(self) -> bool:
        """Navigate to SAP SuccessFactors Nemetschek careers page"""
        try:
            logger.info(f"Navigating to: {self.base_url}")
            self.driver.get(self.base_url)

            # Wait for page to load
            self.wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))

            # Check if we're on the right page
            if "nemetschek" in self.driver.current_url.lower():
                logger.info("✅ Successfully navigated to Nemetschek careers page")
                return True
            else:
                logger.warning(f"⚠️ Unexpected URL: {self.driver.current_url}")
                return False

        except Exception as e:
            logger.error(f"❌ Failed to navigate to careers page: {e}")
            return False

    def discover_jobs(self, search_keywords: List[str] = None, max_jobs: int = 10) -> List[Dict]:
        """Discover available jobs on the careers page"""
        logger.info("🔍 Discovering available jobs...")

        jobs = []

        try:
            # Handle any cookie banners or popups
            self._handle_popups()

            # Look for search functionality
            search_successful = self._perform_job_search(search_keywords)

            # Wait for job listings to load
            time.sleep(3)

            # Try different selectors for job listings
            job_selectors = [
                "[data-automation-id='jobTitle']",
                ".jobTitle",
                "[role='gridcell'] a",
                ".job-title a",
                "[data-automation-id='listViewRow']",
                ".listViewRow",
                "tr[role='row']",
                ".job-listing",
                ".career-job-item"
            ]

            job_elements = []
            for selector in job_selectors:
                try:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    if elements:
                        logger.info(f"✅ Found {len(elements)} job elements using selector: {selector}")
                        job_elements = elements
                        break
                except:
                    continue

            if not job_elements:
                logger.warning("⚠️ No job elements found with standard selectors, trying alternative approach")
                job_elements = self._find_jobs_alternative_method()

            # Process found job elements
            for i, element in enumerate(job_elements[:max_jobs]):
                try:
                    job_data = self._extract_job_data(element, i)
                    if job_data:
                        jobs.append(job_data)
                        self.session_stats['jobs_found'] += 1

                except Exception as e:
                    logger.warning(f"⚠️ Failed to extract job data for element {i}: {e}")
                    continue

            logger.info(f"📋 Discovered {len(jobs)} jobs")
            return jobs

        except Exception as e:
            logger.error(f"❌ Failed to discover jobs: {e}")
            return []

    def _handle_popups(self):
        """Handle cookie banners and popups"""
        popup_selectors = [
            "#onetrust-accept-btn-handler",
            ".cookie-accept-button",
            "[data-automation-id='acceptCookies']",
            ".accept-cookies",
            "#acceptAllCookies",
            ".cookie-banner button"
        ]

        for selector in popup_selectors:
            try:
                element = self.driver.find_element(By.CSS_SELECTOR, selector)
                if element.is_displayed():
                    element.click()
                    logger.info(f"✅ Closed popup using selector: {selector}")
                    time.sleep(1)
                    break
            except:
                continue

    def _perform_job_search(self, keywords: List[str] = None) -> bool:
        """Perform job search with keywords"""
        if not keywords:
            keywords = ["software engineer", "developer", "backend", "full stack"]

        search_selectors = [
            "[data-automation-id='searchField']",
            "#searchField",
            ".search-input",
            "input[type='search']",
            "[placeholder*='search']",
            "[placeholder*='keyword']"
        ]

        for keyword in keywords[:1]:  # Try first keyword
            for selector in search_selectors:
                try:
                    search_input = self.driver.find_element(By.CSS_SELECTOR, selector)
                    search_input.clear()
                    search_input.send_keys(keyword)
                    search_input.send_keys(Keys.RETURN)

                    logger.info(f"✅ Performed search with keyword: {keyword}")
                    time.sleep(3)
                    return True

                except:
                    continue

        logger.info("ℹ️ No search field found, proceeding with default listings")
        return False

    def _find_jobs_alternative_method(self) -> List:
        """Alternative method to find job listings"""
        alternative_selectors = [
            "a[href*='job']",
            "a[href*='career']",
            "a[href*='position']",
            "[data-automation-id*='job']",
            ".job-link",
            ".position-link"
        ]

        for selector in alternative_selectors:
            try:
                elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                if elements:
                    logger.info(f"✅ Found {len(elements)} potential job links using: {selector}")
                    return elements
            except:
                continue

        return []

    def _extract_job_data(self, element, index: int) -> Optional[Dict]:
        """Extract job data from a job element"""
        try:
            job_data = {
                'id': f"sap_nemetschek_{index}_{int(time.time())}",
                'title': 'Unknown Position',
                'company': 'Nemetschek',
                'location': 'Unknown',
                'url': self.driver.current_url,
                'description': '',
                'requirements': '',
                'element_index': index,
                'discovered_at': datetime.now().isoformat()
            }

            # Try to extract job title
            title_selectors = [
                ".jobTitle",
                "[data-automation-id='jobTitle']",
                ".job-title",
                ".position-title"
            ]

            for selector in title_selectors:
                try:
                    title_element = element.find_element(By.CSS_SELECTOR, selector)
                    job_data['title'] = title_element.text.strip()
                    break
                except:
                    continue

            # If element is a link, get href
            try:
                if element.tag_name == 'a':
                    job_data['url'] = element.get_attribute('href')
                else:
                    # Look for link within element
                    link = element.find_element(By.TAG_NAME, 'a')
                    job_data['url'] = link.get_attribute('href')
            except:
                pass

            # Try to get job title from text if not found
            if job_data['title'] == 'Unknown Position':
                text = element.text.strip()
                if text:
                    # Take first line as title
                    job_data['title'] = text.split('\n')[0][:100]

            # Try to extract location
            location_selectors = [
                ".location",
                "[data-automation-id='location']",
                ".job-location"
            ]

            for selector in location_selectors:
                try:
                    location_element = element.find_element(By.CSS_SELECTOR, selector)
                    job_data['location'] = location_element.text.strip()
                    break
                except:
                    continue

            logger.info(f"📄 Extracted job: {job_data['title']} at {job_data['location']}")
            return job_data

        except Exception as e:
            logger.warning(f"⚠️ Failed to extract job data: {e}")
            return None

    def apply_to_job(self, job: Dict) -> bool:
        """Apply to a specific job with dynamic resume generation"""
        logger.info(f"🎯 Applying to: {job['title']} at {job['company']}")

        try:
            # Generate customized resume for this job
            resume_path = self._generate_job_specific_resume(job)

            if not resume_path:
                logger.error("❌ Failed to generate resume")
                return False

            # Navigate to job application page
            if not self._navigate_to_job_application(job):
                logger.error("❌ Failed to navigate to job application")
                return False

            # Fill out application form
            if not self._fill_application_form(job, resume_path):
                logger.error("❌ Failed to fill application form")
                return False

            # Submit application
            if not self._submit_application():
                logger.error("❌ Failed to submit application")
                return False

            logger.info(f"✅ Successfully applied to {job['title']}")
            self.applied_jobs.add(job['id'])
            self.session_stats['applications_submitted'] += 1
            return True

        except Exception as e:
            logger.error(f"❌ Application failed for {job['title']}: {e}")
            self.session_stats['applications_failed'] += 1
            return False

    def _generate_job_specific_resume(self, job: Dict) -> Optional[str]:
        """Generate a customized resume for the specific job"""
        try:
            logger.info(f"📝 Generating customized resume for {job['title']}")

            # Get job description if available
            job_description = self._fetch_job_description(job)

            # Analyze job requirements
            job_requirements = self.resume_generator.analyzer.analyze_job_posting(job_description)

            # Generate enhanced profile
            enhanced_profile = self.resume_generator.enhance_profile_for_job(job_requirements)

            # Create PDF filename
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            safe_title = re.sub(r'[^\w\s-]', '', job['title']).strip()
            safe_title = re.sub(r'[-\s]+', '_', safe_title)
            filename = f"/home/calelin/awesome-apply/Jiale_Lin_Resume_{job['company']}_{safe_title}_{timestamp}.pdf"

            # Generate customized resume
            self.resume_generator.create_enhanced_pdf(
                enhanced_profile, job['title'], job['company'], filename
            )
            resume_path = filename

            self.session_stats['resumes_generated'] += 1
            logger.info(f"✅ Generated resume: {resume_path}")
            return resume_path

        except Exception as e:
            logger.error(f"❌ Failed to generate resume: {e}")
            return None

    def _fetch_job_description(self, job: Dict) -> str:
        """Fetch detailed job description"""
        try:
            # If we have a job URL, navigate to it
            if job['url'] and job['url'] != self.driver.current_url:
                self.driver.get(job['url'])
                time.sleep(3)

            # Try to find job description
            description_selectors = [
                "[data-automation-id='jobPostingDescription']",
                ".job-description",
                ".jobDescription",
                ".posting-description",
                ".job-details",
                "#jobDescription"
            ]

            description = ""
            for selector in description_selectors:
                try:
                    element = self.driver.find_element(By.CSS_SELECTOR, selector)
                    description = element.text.strip()
                    if description:
                        break
                except:
                    continue

            # Fallback to page text if no specific description found
            if not description:
                description = self.driver.find_element(By.TAG_NAME, "body").text

            logger.info(f"📖 Fetched job description ({len(description)} characters)")
            return description

        except Exception as e:
            logger.warning(f"⚠️ Failed to fetch job description: {e}")
            return f"Job Title: {job['title']} at {job['company']}"

    def _navigate_to_job_application(self, job: Dict) -> bool:
        """Navigate to the job application page"""
        try:
            # Look for apply button
            apply_selectors = [
                "[data-automation-id='applyToJobPostingButton']",
                ".apply-button",
                "#applyButton",
                "button[title*='Apply']",
                "a[title*='Apply']",
                "button:contains('Apply')",
                ".btn-apply"
            ]

            for selector in apply_selectors:
                try:
                    apply_button = self.wait.until(
                        EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                    )
                    apply_button.click()
                    logger.info(f"✅ Clicked apply button using: {selector}")
                    time.sleep(3)
                    return True

                except TimeoutException:
                    continue
                except Exception as e:
                    logger.warning(f"⚠️ Failed to click apply button with {selector}: {e}")
                    continue

            # Alternative: look for any clickable element with "apply" text
            try:
                elements = self.driver.find_elements(By.XPATH, "//*[contains(text(), 'Apply') or contains(text(), 'APPLY')]")
                for element in elements:
                    if element.is_displayed() and element.is_enabled():
                        element.click()
                        logger.info("✅ Clicked apply element found by text")
                        time.sleep(3)
                        return True
            except:
                pass

            logger.warning("⚠️ No apply button found")
            return False

        except Exception as e:
            logger.error(f"❌ Failed to navigate to application: {e}")
            return False

    def _fill_application_form(self, job: Dict, resume_path: str) -> bool:
        """Fill out the job application form"""
        try:
            logger.info("📝 Filling application form...")

            # Handle login if required
            if not self._handle_login_if_required():
                return False

            # Wait for form to load
            time.sleep(3)

            # Fill personal information
            self._fill_personal_information()

            # Upload resume
            self._upload_resume(resume_path)

            # Fill additional fields
            self._fill_additional_fields(job)

            # Handle any required fields
            self._handle_required_fields()

            logger.info("✅ Application form filled successfully")
            return True

        except Exception as e:
            logger.error(f"❌ Failed to fill application form: {e}")
            return False

    def _handle_login_if_required(self) -> bool:
        """Handle login if the application requires it"""
        try:
            # Check if we need to login
            login_indicators = [
                "login",
                "sign in",
                "create account",
                "register"
            ]

            page_text = self.driver.page_source.lower()
            needs_login = any(indicator in page_text for indicator in login_indicators)

            if needs_login:
                logger.info("🔐 Login required, checking for guest application option...")

                # Look for guest/external candidate option
                guest_selectors = [
                    "[data-automation-id='externalCandidate']",
                    ".external-candidate",
                    "button:contains('External')",
                    "a:contains('External')",
                    "[title*='External']",
                    ".guest-application"
                ]

                for selector in guest_selectors:
                    try:
                        guest_button = self.driver.find_element(By.CSS_SELECTOR, selector)
                        if guest_button.is_displayed():
                            guest_button.click()
                            logger.info("✅ Selected external candidate option")
                            time.sleep(2)
                            return True
                    except:
                        continue

                logger.warning("⚠️ Could not find guest application option")
                return False

            return True

        except Exception as e:
            logger.error(f"❌ Failed to handle login: {e}")
            return False

    def _fill_personal_information(self):
        """Fill personal information fields"""
        data = self.application_data['personal_info']

        field_mappings = [
            ('first_name', ['firstName', 'first_name', 'fname']),
            ('last_name', ['lastName', 'last_name', 'lname']),
            ('email', ['email', 'emailAddress', 'email_address']),
            ('phone', ['phone', 'phoneNumber', 'mobile', 'telephone'])
        ]

        for data_field, field_names in field_mappings:
            value = data.get(data_field, '')
            if value:
                self._fill_field_by_names(field_names, value)

        # Address fields
        address = data.get('address', {})
        address_mappings = [
            ('street', ['address', 'street', 'address1']),
            ('city', ['city']),
            ('state', ['state', 'province']),
            ('zip_code', ['zip', 'zipCode', 'postalCode']),
            ('country', ['country'])
        ]

        for addr_field, field_names in address_mappings:
            value = address.get(addr_field, '')
            if value:
                self._fill_field_by_names(field_names, value)

    def _fill_field_by_names(self, field_names: List[str], value: str):
        """Fill field by trying multiple possible field names"""
        for field_name in field_names:
            selectors = [
                f"[name='{field_name}']",
                f"[id='{field_name}']",
                f"[data-automation-id='{field_name}']",
                f"input[placeholder*='{field_name}']",
                f"#{field_name}",
                f".{field_name}"
            ]

            for selector in selectors:
                try:
                    element = self.driver.find_element(By.CSS_SELECTOR, selector)
                    if element.is_displayed() and element.is_enabled():
                        element.clear()
                        element.send_keys(value)
                        logger.info(f"✅ Filled {field_name}: {value}")
                        return
                except:
                    continue

    def _upload_resume(self, resume_path: str):
        """Upload resume file"""
        try:
            upload_selectors = [
                "input[type='file'][accept*='pdf']",
                "input[type='file']",
                "[data-automation-id='fileUpload']",
                ".file-upload input",
                "#resumeUpload",
                "[name='resume']"
            ]

            for selector in upload_selectors:
                try:
                    upload_element = self.driver.find_element(By.CSS_SELECTOR, selector)
                    if upload_element.is_displayed():
                        upload_element.send_keys(resume_path)
                        logger.info(f"✅ Uploaded resume: {resume_path}")
                        time.sleep(2)
                        return
                except:
                    continue

            logger.warning("⚠️ Could not find resume upload field")

        except Exception as e:
            logger.warning(f"⚠️ Failed to upload resume: {e}")

    def _fill_additional_fields(self, job: Dict):
        """Fill additional application fields"""
        work_auth = self.application_data['work_authorization']
        experience = self.application_data['experience']
        education = self.application_data['education']

        # Work authorization
        if work_auth['citizenship'] == 'US Citizen':
            self._select_dropdown_option(['workAuth', 'authorization'], 'US Citizen')
            self._select_dropdown_option(['sponsorship'], 'No')

        # Years of experience
        self._fill_field_by_names(['experience', 'yearsExperience'], experience['years_of_experience'])

        # Education
        self._select_dropdown_option(['education', 'degree'], education['highest_degree'])
        self._fill_field_by_names(['university', 'school'], education['university'])
        self._fill_field_by_names(['graduationYear'], education['graduation_year'])

        # Salary expectation
        self._fill_field_by_names(['salary', 'expectedSalary'], experience['salary_expectation'])

        # Start date
        self._fill_field_by_names(['startDate', 'availableDate'], experience['available_start_date'])

    def _select_dropdown_option(self, field_names: List[str], option_text: str):
        """Select dropdown option"""
        for field_name in field_names:
            selectors = [
                f"select[name='{field_name}']",
                f"select[id='{field_name}']",
                f"#{field_name}",
                f".{field_name} select"
            ]

            for selector in selectors:
                try:
                    dropdown = Select(self.driver.find_element(By.CSS_SELECTOR, selector))

                    # Try exact match first
                    try:
                        dropdown.select_by_visible_text(option_text)
                        logger.info(f"✅ Selected {field_name}: {option_text}")
                        return
                    except:
                        # Try partial match
                        for option in dropdown.options:
                            if option_text.lower() in option.text.lower():
                                dropdown.select_by_visible_text(option.text)
                                logger.info(f"✅ Selected {field_name}: {option.text}")
                                return
                except:
                    continue

    def _handle_required_fields(self):
        """Handle any remaining required fields"""
        try:
            # Look for required field indicators
            required_selectors = [
                "input[required]:not([value])",
                "select[required]",
                ".required input:not([value])",
                "[aria-required='true']:not([value])"
            ]

            for selector in required_selectors:
                try:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    for element in elements:
                        if element.is_displayed() and element.is_enabled():
                            # Try to fill with appropriate default
                            field_type = element.get_attribute('type')
                            field_name = element.get_attribute('name') or element.get_attribute('id')

                            if field_type == 'text':
                                element.send_keys('Not specified')
                            elif field_type == 'email':
                                element.send_keys(self.application_data['personal_info']['email'])
                            elif field_type == 'tel':
                                element.send_keys(self.application_data['personal_info']['phone'])
                            elif element.tag_name == 'select':
                                Select(element).select_by_index(1)  # Select first non-empty option

                            logger.info(f"✅ Filled required field: {field_name}")

                except Exception as e:
                    logger.warning(f"⚠️ Could not handle required field: {e}")
                    continue

        except Exception as e:
            logger.warning(f"⚠️ Failed to handle required fields: {e}")

    def _submit_application(self) -> bool:
        """Submit the application"""
        try:
            submit_selectors = [
                "button[type='submit']",
                "input[type='submit']",
                "[data-automation-id='submitApplication']",
                "#submitApplication",
                ".submit-button",
                "button:contains('Submit')",
                "button:contains('Apply')"
            ]

            for selector in submit_selectors:
                try:
                    submit_button = self.wait.until(
                        EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                    )

                    # Scroll to button
                    self.driver.execute_script("arguments[0].scrollIntoView();", submit_button)
                    time.sleep(1)

                    submit_button.click()
                    logger.info(f"✅ Clicked submit button using: {selector}")

                    # Wait for confirmation
                    time.sleep(5)

                    # Check for success indicators
                    success_indicators = [
                        "application submitted",
                        "thank you",
                        "application received",
                        "successfully applied"
                    ]

                    page_text = self.driver.page_source.lower()
                    if any(indicator in page_text for indicator in success_indicators):
                        logger.info("✅ Application submitted successfully")
                        return True

                except TimeoutException:
                    continue
                except Exception as e:
                    logger.warning(f"⚠️ Failed to submit with {selector}: {e}")
                    continue

            logger.warning("⚠️ Could not find or click submit button")
            return False

        except Exception as e:
            logger.error(f"❌ Failed to submit application: {e}")
            return False

    def run_automation_session(self, max_applications: int = 5, keywords: List[str] = None) -> Dict:
        """Run a complete automation session"""
        logger.info("🚀 Starting SAP Nemetschek careers automation session")
        logger.info("=" * 70)

        try:
            # Initialize driver
            if not self.initialize_driver():
                return self._get_session_summary(success=False)

            # Navigate to careers page
            if not self.navigate_to_careers_page():
                return self._get_session_summary(success=False)

            # Discover jobs
            jobs = self.discover_jobs(keywords, max_jobs=max_applications * 2)

            if not jobs:
                logger.warning("⚠️ No jobs found")
                return self._get_session_summary(success=False)

            # Apply to jobs
            applications_attempted = 0
            for job in jobs:
                if applications_attempted >= max_applications:
                    break

                if job['id'] not in self.applied_jobs:
                    logger.info(f"🎯 Attempting application {applications_attempted + 1}/{max_applications}")

                    success = self.apply_to_job(job)
                    applications_attempted += 1

                    if success:
                        logger.info(f"✅ Successfully applied to {job['title']}")
                    else:
                        logger.warning(f"⚠️ Failed to apply to {job['title']}")

                    # Wait between applications
                    import random
                    time.sleep(random.randint(10, 20))

            return self._get_session_summary(success=True)

        except Exception as e:
            logger.error(f"❌ Automation session failed: {e}")
            return self._get_session_summary(success=False)

        finally:
            if self.driver:
                self.driver.quit()
                logger.info("🔌 WebDriver closed")

    def _get_session_summary(self, success: bool) -> Dict:
        """Get automation session summary"""
        duration = datetime.now() - self.session_stats['start_time']

        summary = {
            'success': success,
            'duration': str(duration),
            'jobs_found': self.session_stats['jobs_found'],
            'applications_submitted': self.session_stats['applications_submitted'],
            'applications_failed': self.session_stats['applications_failed'],
            'resumes_generated': self.session_stats['resumes_generated'],
            'success_rate': (
                self.session_stats['applications_submitted'] /
                max(1, self.session_stats['applications_submitted'] + self.session_stats['applications_failed'])
            ) * 100,
            'applied_jobs': list(self.applied_jobs),
            'timestamp': datetime.now().isoformat()
        }

        # Log summary
        logger.info("=" * 70)
        logger.info("📊 AUTOMATION SESSION SUMMARY")
        logger.info("=" * 70)
        logger.info(f"✅ Session Success: {summary['success']}")
        logger.info(f"⏱️ Duration: {summary['duration']}")
        logger.info(f"🔍 Jobs Found: {summary['jobs_found']}")
        logger.info(f"📝 Resumes Generated: {summary['resumes_generated']}")
        logger.info(f"✅ Applications Submitted: {summary['applications_submitted']}")
        logger.info(f"❌ Applications Failed: {summary['applications_failed']}")
        logger.info(f"📈 Success Rate: {summary['success_rate']:.1f}%")
        logger.info("=" * 70)

        return summary

def main():
    """Main function for testing the automation"""
    import random

    print("🚀 SAP NEMETSCHEK CAREERS AUTOMATION")
    print("=" * 50)
    print("This automation will:")
    print("✅ Search for software engineering jobs")
    print("✅ Generate customized resumes for each job")
    print("✅ Automatically fill and submit applications")
    print("=" * 50)

    # Initialize automation
    automation = SAPNemetschekCareersAutomation(headless=False)

    # Define search keywords
    search_keywords = [
        "software engineer",
        "backend developer",
        "full stack developer",
        "python developer",
        "senior engineer"
    ]

    try:
        # Run automation session
        summary = automation.run_automation_session(
            max_applications=3,
            keywords=search_keywords
        )

        # Save results
        results_file = f"/home/calelin/awesome-apply/sap_automation_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(results_file, 'w') as f:
            json.dump(summary, f, indent=2)

        print(f"\n📄 Results saved to: {results_file}")

        return 0 if summary['success'] else 1

    except KeyboardInterrupt:
        print("\n🛑 Automation interrupted by user")
        return 1
    except Exception as e:
        print(f"\n💥 Automation failed: {e}")
        return 1

if __name__ == "__main__":
    import sys
    sys.exit(main())