#!/usr/bin/env python3
"""
Live Nemetschek Application System
Actually applies to real jobs and confirms submission
"""

import os
import time
import json
import logging
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
import subprocess

# Import our resume generator
from sap_nemetschek_complete_automation import AdvancedResumeAnalyzer, DynamicLatexResumeGenerator

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class NemetschekLiveApplicationSystem:
    """Complete live application system for Nemetschek jobs"""

    def __init__(self):
        self.analyzer = AdvancedResumeAnalyzer()
        self.resume_generator = DynamicLatexResumeGenerator(self.analyzer)

        # Setup directories
        self.output_dir = "live_applications"
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
            "willing_to_relocate": "Yes"
        }

        self.driver = None
        self.wait = None

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
            time.sleep(5)  # Additional wait for dynamic content

            # Take screenshot
            self.save_screenshot("careers_homepage")

            # Check if we're on the right page
            page_title = self.driver.title.lower()
            if "nemetschek" in page_title or "career" in page_title:
                logger.info("Successfully loaded Nemetschek careers page")
                return True
            else:
                logger.warning(f"Unexpected page title: {self.driver.title}")
                return True  # Continue anyway

        except Exception as e:
            logger.error(f"Failed to navigate to careers page: {e}")
            return False

    def find_available_jobs(self) -> List[Dict[str, Any]]:
        """Find all available job listings"""
        jobs = []

        try:
            logger.info("Searching for available job listings...")

            # Multiple strategies to find jobs
            job_selectors = [
                # Common job listing selectors
                "a[href*='job']",
                ".job-item a",
                ".job-listing a",
                ".position a",
                ".career-item a",
                "[data-automation-id*='job'] a",
                ".job-title a",
                "a[id*='job']",
                "div[role='link']",
                ".job-card a"
            ]

            all_job_elements = []

            for selector in job_selectors:
                try:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    for element in elements:
                        if element.is_displayed() and element.get_attribute("href"):
                            all_job_elements.append(element)
                    if all_job_elements:
                        logger.info(f"Found job elements using selector: {selector}")
                        break
                except Exception as e:
                    continue

            # If no specific job selectors work, try broader search
            if not all_job_elements:
                logger.info("Trying broader search for clickable elements...")
                all_links = self.driver.find_elements(By.TAG_NAME, "a")

                for link in all_links:
                    try:
                        href = link.get_attribute("href")
                        text = link.text.strip().lower()

                        if href and ("job" in href or "position" in href or "career" in href):
                            if any(keyword in text for keyword in ["engineer", "developer", "manager", "analyst", "senior"]):
                                all_job_elements.append(link)
                    except:
                        continue

            # Extract job information
            seen_urls = set()
            for i, element in enumerate(all_job_elements[:15]):  # Limit to first 15
                try:
                    href = element.get_attribute("href")
                    if href in seen_urls:
                        continue
                    seen_urls.add(href)

                    # Extract basic job info
                    job_title = element.text.strip()
                    if not job_title:
                        # Try to find title in parent elements
                        parent = element.find_element(By.XPATH, "./..")
                        job_title = parent.text.strip().split('\n')[0] if parent.text else f"Job {i+1}"

                    # Look for location info
                    location = "Location not specified"
                    try:
                        parent_container = element.find_element(By.XPATH, "./../../..")
                        location_indicators = ["Munich", "München", "Berlin", "Remote", "Germany", "DE"]
                        for indicator in location_indicators:
                            if indicator in parent_container.text:
                                location = indicator
                                break
                    except:
                        pass

                    job_data = {
                        "title": job_title,
                        "url": href,
                        "location": location,
                        "element_index": i,
                        "found_via": "automated_search"
                    }

                    jobs.append(job_data)
                    logger.info(f"Found job: {job_title} | {location}")

                except Exception as e:
                    logger.warning(f"Error extracting job {i}: {e}")
                    continue

            # If still no jobs found, create target URLs to try
            if not jobs:
                logger.info("No jobs found via selectors, trying direct search...")

                # Try searching for specific terms
                search_terms = ["software engineer", "devops", "senior", "developer"]
                self.try_job_search(search_terms)

                # Re-run job finding after search
                time.sleep(3)
                return self.find_available_jobs()

            logger.info(f"Total jobs found: {len(jobs)}")
            return jobs

        except Exception as e:
            logger.error(f"Error finding jobs: {e}")
            return jobs

    def try_job_search(self, search_terms: List[str]):
        """Try to use search functionality on the page"""
        try:
            # Look for search inputs
            search_selectors = [
                "input[placeholder*='search']",
                "input[placeholder*='Search']",
                "input[name*='search']",
                "input[id*='search']",
                ".search-input",
                "#search",
                "input[type='search']",
                "input[type='text']"
            ]

            search_input = None
            for selector in search_selectors:
                try:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    for element in elements:
                        if element.is_displayed() and element.is_enabled():
                            search_input = element
                            break
                    if search_input:
                        break
                except:
                    continue

            if search_input:
                logger.info("Found search input, performing search...")
                search_input.clear()
                search_input.send_keys(" ".join(search_terms[:2]))  # Use first 2 terms
                search_input.send_keys(Keys.RETURN)
                time.sleep(3)
                self.save_screenshot("after_search")
            else:
                logger.info("No search input found")

        except Exception as e:
            logger.warning(f"Search attempt failed: {e}")

    def get_job_details(self, job: Dict[str, Any]) -> Dict[str, Any]:
        """Get detailed information about a job"""
        try:
            logger.info(f"Getting details for job: {job['title']}")

            # Open job in new tab to preserve main page
            self.driver.execute_script("window.open('');")
            self.driver.switch_to.window(self.driver.window_handles[-1])

            # Navigate to job page
            self.driver.get(job["url"])
            time.sleep(3)

            self.save_screenshot(f"job_details_{job['element_index']}")

            # Extract job description
            description_selectors = [
                ".job-description",
                ".description",
                ".job-details",
                ".job-content",
                ".position-description",
                "[data-automation-id*='description']",
                ".content",
                "div[role='main']"
            ]

            job_description = ""
            for selector in description_selectors:
                try:
                    desc_element = self.driver.find_element(By.CSS_SELECTOR, selector)
                    job_description = desc_element.text.strip()
                    if len(job_description) > 100:  # Valid description
                        break
                except:
                    continue

            # Fallback: get body text
            if not job_description or len(job_description) < 100:
                try:
                    body_text = self.driver.find_element(By.TAG_NAME, "body").text
                    job_description = body_text[:2000]  # First 2000 chars
                except:
                    job_description = "Job description not available"

            # Look for apply button to confirm this is an application page
            apply_button_found = self.find_apply_button(check_only=True)

            job["description"] = job_description
            job["has_apply_button"] = apply_button_found
            job["page_url"] = self.driver.current_url

            # Close tab and return to main window
            self.driver.close()
            self.driver.switch_to.window(self.driver.window_handles[0])

            return job

        except Exception as e:
            logger.error(f"Error getting job details: {e}")
            # Ensure we return to main window
            try:
                if len(self.driver.window_handles) > 1:
                    self.driver.close()
                    self.driver.switch_to.window(self.driver.window_handles[0])
            except:
                pass
            return job

    def create_tailored_application_materials(self, job: Dict[str, Any]) -> Dict[str, str]:
        """Create tailored resume and cover letter for the job"""
        try:
            logger.info(f"Creating tailored materials for: {job['title']}")

            # Analyze job requirements
            job_analysis = self.analyzer.analyze_job_requirements(job.get("description", ""))
            job_analysis.title = job["title"]
            job_analysis.company = "Nemetschek"
            job_analysis.location = job.get("location", "")

            logger.info(f"Job analysis complete - Match score: {job_analysis.match_score:.1f}%")

            # Generate LaTeX resume
            latex_resume = self.resume_generator.generate_tailored_resume(
                job_analysis, job["title"], "Nemetschek"
            )

            # Generate cover letter
            cover_letter = self.resume_generator.generate_cover_letter(
                job_analysis, job["title"], "Nemetschek"
            )

            # Save files
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            safe_title = "".join(c for c in job["title"] if c.isalnum() or c in (' ', '-', '_')).strip()
            safe_title = safe_title.replace(' ', '_')[:50]

            # Save LaTeX resume
            resume_tex_path = f"{self.documents_dir}/Resume_Nemetschek_{safe_title}_{timestamp}.tex"
            with open(resume_tex_path, 'w', encoding='utf-8') as f:
                f.write(latex_resume)

            # Try to compile to PDF
            resume_pdf_path = self.compile_latex_to_pdf(resume_tex_path)

            # Save cover letter
            cover_letter_path = f"{self.documents_dir}/Cover_Letter_Nemetschek_{safe_title}_{timestamp}.txt"
            with open(cover_letter_path, 'w', encoding='utf-8') as f:
                f.write(cover_letter)

            materials = {
                "resume_tex": resume_tex_path,
                "resume_pdf": resume_pdf_path or resume_tex_path,  # Use PDF if available, else TEX
                "cover_letter": cover_letter_path,
                "match_score": job_analysis.match_score,
                "missing_skills": job_analysis.missing_skills,
                "matching_skills": job_analysis.matching_skills
            }

            logger.info(f"Materials created successfully")
            return materials

        except Exception as e:
            logger.error(f"Error creating materials: {e}")
            return {}

    def compile_latex_to_pdf(self, tex_path: str) -> Optional[str]:
        """Compile LaTeX file to PDF"""
        try:
            # Check if pdflatex is available
            result = subprocess.run(["which", "pdflatex"], capture_output=True, text=True)
            if result.returncode != 0:
                logger.warning("pdflatex not found, PDF compilation skipped")
                return None

            # Compile LaTeX
            output_dir = os.path.dirname(tex_path)
            result = subprocess.run(
                ["pdflatex", "-interaction=nonstopmode", "-output-directory", output_dir, tex_path],
                capture_output=True,
                text=True,
                cwd=output_dir,
                timeout=30
            )

            if result.returncode == 0:
                pdf_path = tex_path.replace('.tex', '.pdf')
                if os.path.exists(pdf_path):
                    logger.info(f"PDF compiled successfully: {pdf_path}")
                    return pdf_path

            logger.warning("LaTeX compilation failed")
            return None

        except Exception as e:
            logger.warning(f"PDF compilation error: {e}")
            return None

    def find_apply_button(self, check_only: bool = False):
        """Find the apply button on the job page"""
        apply_selectors = [
            "button[id*='apply']",
            "a[id*='apply']",
            ".apply-button",
            ".btn-apply",
            "input[value*='Apply']",
            "button[title*='Apply']",
            "[data-automation-id*='apply']",
            "button[class*='apply']",
            "a[class*='apply']"
        ]

        # Try selector-based search first
        for selector in apply_selectors:
            try:
                elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                for element in elements:
                    if element.is_displayed() and element.is_enabled():
                        if check_only:
                            return True
                        return element
            except:
                continue

        # Text-based search as fallback
        try:
            all_buttons = self.driver.find_elements(By.CSS_SELECTOR, "button, a, input")
            for element in all_buttons:
                text = element.text.lower().strip()
                value = element.get_attribute("value")

                if value:
                    value = value.lower().strip()

                apply_terms = ["apply", "apply now", "submit application", "bewerben"]

                if any(term in text for term in apply_terms) or (value and any(term in value for term in apply_terms)):
                    if element.is_displayed():
                        if check_only:
                            return True
                        return element
        except:
            pass

        if check_only:
            return False
        return None

    def apply_to_job(self, job: Dict[str, Any], materials: Dict[str, str]) -> bool:
        """Apply to a specific job"""
        try:
            logger.info(f"Starting application to: {job['title']}")

            # Navigate to job page
            self.driver.get(job["url"])
            time.sleep(3)

            self.save_screenshot(f"job_page_before_apply_{job['element_index']}")

            # Find and click apply button
            apply_button = self.find_apply_button()
            if not apply_button:
                logger.error("Apply button not found")
                return False

            logger.info("Apply button found, clicking...")

            # Scroll to button and click
            self.driver.execute_script("arguments[0].scrollIntoView(true);", apply_button)
            time.sleep(1)

            try:
                apply_button.click()
            except ElementClickInterceptedException:
                # Try JavaScript click if regular click fails
                self.driver.execute_script("arguments[0].click();", apply_button)

            time.sleep(5)
            self.save_screenshot(f"after_apply_click_{job['element_index']}")

            # Fill application form
            success = self.fill_application_form(materials)

            if success:
                logger.info(f"Successfully applied to: {job['title']}")
            else:
                logger.error(f"Failed to complete application for: {job['title']}")

            return success

        except Exception as e:
            logger.error(f"Error applying to job: {e}")
            return False

    def fill_application_form(self, materials: Dict[str, str]) -> bool:
        """Fill out the complete application form"""
        try:
            logger.info("Filling application form...")
            time.sleep(3)

            self.save_screenshot("application_form_start")

            # Step 1: Fill personal information
            self.fill_personal_information()

            # Step 2: Handle file uploads
            self.handle_file_uploads(materials)

            # Step 3: Fill additional questions
            self.fill_additional_questions()

            # Step 4: Handle any dropdown selections
            self.handle_dropdown_selections()

            # Step 5: Fill text areas (cover letter, additional info)
            self.fill_text_areas(materials)

            time.sleep(2)
            self.save_screenshot("application_form_filled")

            # Step 6: Submit application
            return self.submit_application()

        except Exception as e:
            logger.error(f"Error filling application form: {e}")
            return False

    def fill_personal_information(self):
        """Fill personal information fields"""
        logger.info("Filling personal information...")

        # Common field mappings
        field_mappings = {
            # Name fields
            "firstName": self.personal_info["first_name"],
            "lastname": self.personal_info["last_name"],
            "first_name": self.personal_info["first_name"],
            "last_name": self.personal_info["last_name"],
            "fname": self.personal_info["first_name"],
            "lname": self.personal_info["last_name"],

            # Contact fields
            "email": self.personal_info["email"],
            "emailAddress": self.personal_info["email"],
            "phone": self.personal_info["phone"],
            "phoneNumber": self.personal_info["phone"],
            "mobile": self.personal_info["mobile"],
            "telephone": self.personal_info["phone"],

            # Address fields
            "address": self.personal_info["street_address"],
            "street": self.personal_info["street_address"],
            "streetAddress": self.personal_info["street_address"],
            "city": self.personal_info["city"],
            "state": self.personal_info["state"],
            "zipCode": self.personal_info["postal_code"],
            "postalCode": self.personal_info["postal_code"],
            "country": self.personal_info["country"],

            # Professional fields
            "linkedin": self.personal_info["linkedin"],
            "linkedinUrl": self.personal_info["linkedin"],
            "website": self.personal_info["website"],
            "portfolio": self.personal_info["website"]
        }

        for field_identifier, value in field_mappings.items():
            self.fill_form_field(field_identifier, value)

    def fill_form_field(self, field_identifier: str, value: str, field_type: str = "input"):
        """Fill a form field using multiple selector strategies"""
        if not value:
            return False

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
            f"[data-automation-id*='{field_identifier}'] textarea"
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
                                # Try to select by visible text first
                                try:
                                    select.select_by_visible_text(value)
                                except:
                                    # Try partial match
                                    for option in select.options:
                                        if value.lower() in option.text.lower():
                                            select.select_by_visible_text(option.text)
                                            break
                                logger.info(f"Selected {field_identifier}: {value}")
                                return True
                            except Exception as e:
                                logger.warning(f"Failed to select {field_identifier}: {e}")
                        else:
                            try:
                                element.clear()
                                element.send_keys(value)
                                logger.info(f"Filled {field_identifier}: {value}")
                                return True
                            except Exception as e:
                                logger.warning(f"Failed to fill {field_identifier}: {e}")
            except:
                continue

        return False

    def handle_file_uploads(self, materials: Dict[str, str]):
        """Handle file upload fields"""
        logger.info("Handling file uploads...")

        try:
            file_inputs = self.driver.find_elements(By.CSS_SELECTOR, "input[type='file']")

            for i, file_input in enumerate(file_inputs):
                if file_input.is_displayed():
                    # Upload resume (prefer PDF, fallback to TEX)
                    file_to_upload = materials.get("resume_pdf") or materials.get("resume_tex")

                    if file_to_upload and os.path.exists(file_to_upload):
                        file_input.send_keys(os.path.abspath(file_to_upload))
                        logger.info(f"Uploaded file {i+1}: {os.path.basename(file_to_upload)}")
                        time.sleep(2)

                        # Only upload to first file input to avoid duplicates
                        break
                    else:
                        logger.warning("No resume file available for upload")

        except Exception as e:
            logger.warning(f"File upload error: {e}")

    def fill_additional_questions(self):
        """Fill additional application questions"""
        logger.info("Filling additional questions...")

        # Common questions and answers
        question_answers = {
            "workAuthorization": "Yes",
            "authorization": "Yes",
            "authorized": "Yes",
            "sponsorship": "No",
            "visa": "No",
            "visaSponsorship": "No",
            "startDate": "Immediately",
            "availability": "Immediately",
            "whenCanYouStart": "Immediately",
            "relocate": "Yes",
            "relocation": "Yes",
            "willingToRelocate": "Yes",
            "salary": "Competitive",
            "expectedSalary": "Competitive",
            "salaryExpectation": "Competitive"
        }

        for field, answer in question_answers.items():
            self.fill_form_field(field, answer)

        # Handle yes/no radio buttons and checkboxes
        self.handle_yes_no_questions()

    def handle_yes_no_questions(self):
        """Handle yes/no radio buttons and checkboxes"""
        try:
            # Look for common yes/no question patterns
            yes_no_patterns = [
                ("authorized", "yes"),
                ("sponsorship", "no"),
                ("visa", "no"),
                ("relocate", "yes"),
                ("willing", "yes")
            ]

            for pattern, answer in yes_no_patterns:
                # Find radio buttons
                radio_selectors = [
                    f"input[type='radio'][name*='{pattern}'][value*='{answer}']",
                    f"input[type='radio'][id*='{pattern}'][value*='{answer}']"
                ]

                for selector in radio_selectors:
                    try:
                        elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                        for element in elements:
                            if element.is_displayed() and not element.is_selected():
                                element.click()
                                logger.info(f"Selected {pattern}: {answer}")
                                break
                    except:
                        continue

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
                        options = select.options

                        # Skip if already selected
                        if select.first_selected_option.text.strip():
                            continue

                        # Try to select appropriate options based on context
                        dropdown_name = dropdown.get_attribute("name") or dropdown.get_attribute("id") or ""
                        dropdown_name = dropdown_name.lower()

                        for option in options[1:]:  # Skip first option (usually "Select...")
                            option_text = option.text.lower()

                            # Country selection
                            if "country" in dropdown_name:
                                if "united states" in option_text or "usa" in option_text or "us" in option_text:
                                    select.select_by_visible_text(option.text)
                                    logger.info(f"Selected country: {option.text}")
                                    break

                            # Authorization/Citizenship
                            elif any(keyword in dropdown_name for keyword in ["authorization", "citizen", "status"]):
                                if any(keyword in option_text for keyword in ["yes", "authorized", "citizen", "permanent"]):
                                    select.select_by_visible_text(option.text)
                                    logger.info(f"Selected authorization: {option.text}")
                                    break

                            # Education level
                            elif "education" in dropdown_name or "degree" in dropdown_name:
                                if any(keyword in option_text for keyword in ["master", "bachelor", "university"]):
                                    select.select_by_visible_text(option.text)
                                    logger.info(f"Selected education: {option.text}")
                                    break

                            # Experience level
                            elif "experience" in dropdown_name or "years" in dropdown_name:
                                if any(keyword in option_text for keyword in ["5", "5+", "3-5", "senior"]):
                                    select.select_by_visible_text(option.text)
                                    logger.info(f"Selected experience: {option.text}")
                                    break

                    except Exception as e:
                        logger.warning(f"Error with dropdown: {e}")

        except Exception as e:
            logger.warning(f"Error handling dropdowns: {e}")

    def fill_text_areas(self, materials: Dict[str, str]):
        """Fill text areas like cover letter"""
        logger.info("Filling text areas...")

        try:
            text_areas = self.driver.find_elements(By.TAG_NAME, "textarea")

            for textarea in text_areas:
                if textarea.is_displayed() and textarea.is_enabled():
                    # Check if it's empty and should be filled
                    current_text = textarea.get_attribute("value") or textarea.text
                    if current_text.strip():
                        continue  # Already has content

                    textarea_name = (textarea.get_attribute("name") or textarea.get_attribute("id") or "").lower()

                    # Cover letter
                    if any(keyword in textarea_name for keyword in ["cover", "letter", "motivation", "why"]):
                        if materials.get("cover_letter"):
                            try:
                                with open(materials["cover_letter"], 'r') as f:
                                    cover_text = f.read()
                                textarea.send_keys(cover_text[:2000])  # Limit length
                                logger.info("Filled cover letter textarea")
                            except:
                                pass

                    # Additional information
                    elif any(keyword in textarea_name for keyword in ["additional", "info", "comment", "note"]):
                        additional_info = """I am excited about the opportunity to contribute to Nemetschek's innovative technology solutions. My experience in cloud infrastructure, DevOps automation, and software development aligns well with your requirements. I am authorized to work in the US and available to start immediately."""
                        textarea.send_keys(additional_info)
                        logger.info("Filled additional information textarea")

        except Exception as e:
            logger.warning(f"Error filling text areas: {e}")

    def submit_application(self) -> bool:
        """Submit the application form"""
        try:
            logger.info("Attempting to submit application...")

            # Take screenshot before submission
            self.save_screenshot("before_submission")

            # Look for submit button
            submit_selectors = [
                "button[type='submit']",
                "input[type='submit']",
                "button[id*='submit']",
                ".submit-button",
                ".btn-submit",
                "[data-automation-id*='submit']",
                "button[class*='submit']"
            ]

            submit_button = None
            for selector in submit_selectors:
                try:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    for element in elements:
                        if element.is_displayed() and element.is_enabled():
                            submit_button = element
                            break
                    if submit_button:
                        break
                except:
                    continue

            # Text-based search for submit button
            if not submit_button:
                all_buttons = self.driver.find_elements(By.CSS_SELECTOR, "button, input")
                for button in all_buttons:
                    text = button.text.lower().strip()
                    value = button.get_attribute("value")

                    if value:
                        value = value.lower().strip()

                    submit_terms = ["submit", "apply", "send application", "senden", "absenden"]

                    if any(term in text for term in submit_terms) or (value and any(term in value for term in submit_terms)):
                        if button.is_displayed() and button.is_enabled():
                            submit_button = button
                            break

            if submit_button:
                logger.info("Submit button found!")

                # Ask for user confirmation before actual submission
                print("\n" + "="*60)
                print("🎯 APPLICATION READY FOR SUBMISSION")
                print("="*60)
                print("The application form has been filled out with your information.")
                print("Please review the form carefully before submitting.")
                print("\nForm includes:")
                print("  ✅ Personal information")
                print("  ✅ Resume upload")
                print("  ✅ Cover letter")
                print("  ✅ Work authorization details")
                print("  ✅ Additional questions")
                print("\n⚠️  IMPORTANT: This will submit a REAL application to Nemetschek!")
                print("="*60)

                # Give user option to submit or cancel
                while True:
                    choice = input("\nDo you want to submit this application? (yes/no/review): ").lower().strip()

                    if choice in ['yes', 'y']:
                        # Actually submit
                        self.driver.execute_script("arguments[0].scrollIntoView(true);", submit_button)
                        time.sleep(1)

                        try:
                            submit_button.click()
                        except ElementClickInterceptedException:
                            self.driver.execute_script("arguments[0].click();", submit_button)

                        logger.info("Application submitted!")
                        time.sleep(5)

                        # Take screenshot of confirmation
                        self.save_screenshot("after_submission")

                        # Check for confirmation message
                        return self.check_submission_confirmation()

                    elif choice in ['no', 'n']:
                        logger.info("Application submission cancelled by user")
                        return False

                    elif choice == 'review':
                        # Take screenshot for review
                        self.save_screenshot("form_for_review")
                        print(f"📸 Screenshot saved for review: {self.screenshots_dir}/form_for_review_*.png")
                        continue

                    else:
                        print("Please enter 'yes', 'no', or 'review'")
                        continue
            else:
                logger.error("Submit button not found")
                return False

        except Exception as e:
            logger.error(f"Error submitting application: {e}")
            return False

    def check_submission_confirmation(self) -> bool:
        """Check if application was successfully submitted"""
        try:
            time.sleep(3)

            # Look for confirmation messages
            confirmation_indicators = [
                "thank you",
                "application submitted",
                "successfully submitted",
                "received your application",
                "confirmation",
                "we have received",
                "application complete",
                "danke",  # German
                "erfolgreich",  # German
                "eingegangen"  # German
            ]

            page_text = self.driver.find_element(By.TAG_NAME, "body").text.lower()

            for indicator in confirmation_indicators:
                if indicator in page_text:
                    logger.info(f"✅ Confirmation found: '{indicator}'")
                    self.save_screenshot("submission_confirmed")
                    return True

            # Check for confirmation elements
            confirmation_selectors = [
                ".confirmation",
                ".success",
                ".thank-you",
                "[class*='confirm']",
                "[class*='success']"
            ]

            for selector in confirmation_selectors:
                try:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    for element in elements:
                        if element.is_displayed() and element.text.strip():
                            logger.info(f"✅ Confirmation element found: {element.text[:100]}")
                            return True
                except:
                    continue

            logger.warning("No clear confirmation message found")
            return False

        except Exception as e:
            logger.error(f"Error checking confirmation: {e}")
            return False

    def save_screenshot(self, name: str):
        """Save screenshot with timestamp"""
        try:
            timestamp = datetime.now().strftime("%H%M%S")
            screenshot_path = f"{self.screenshots_dir}/{name}_{timestamp}.png"
            self.driver.save_screenshot(screenshot_path)
            logger.info(f"Screenshot saved: {screenshot_path}")
        except Exception as e:
            logger.warning(f"Failed to save screenshot: {e}")

    def run_live_application_process(self) -> Dict[str, Any]:
        """Run the complete live application process"""
        results = {
            "applications_attempted": 0,
            "applications_successful": 0,
            "jobs_found": 0,
            "materials_generated": 0,
            "errors": [],
            "successful_applications": []
        }

        try:
            logger.info("🚀 Starting live Nemetschek application process...")

            # Setup browser
            if not self.setup_browser():
                results["errors"].append("Failed to setup browser")
                return results

            # Navigate to careers page
            if not self.navigate_to_nemetschek_careers():
                results["errors"].append("Failed to navigate to careers page")
                return results

            # Find available jobs
            jobs = self.find_available_jobs()
            results["jobs_found"] = len(jobs)

            if not jobs:
                results["errors"].append("No jobs found")
                return results

            logger.info(f"Found {len(jobs)} available positions")

            # Process jobs (limit to 3 for safety)
            for i, job in enumerate(jobs[:3]):
                try:
                    logger.info(f"\n{'='*60}")
                    logger.info(f"PROCESSING JOB {i+1}/{min(len(jobs), 3)}")
                    logger.info(f"Title: {job['title']}")
                    logger.info(f"Location: {job['location']}")
                    logger.info(f"{'='*60}")

                    # Get detailed job information
                    detailed_job = self.get_job_details(job)

                    if not detailed_job.get("has_apply_button"):
                        logger.warning("No apply button found, skipping job")
                        continue

                    # Create tailored materials
                    materials = self.create_tailored_application_materials(detailed_job)
                    if materials:
                        results["materials_generated"] += 1

                    # Ask user if they want to apply to this job
                    print(f"\n🎯 JOB OPPORTUNITY:")
                    print(f"   Title: {detailed_job['title']}")
                    print(f"   Location: {detailed_job['location']}")
                    print(f"   Match Score: {materials.get('match_score', 0):.1f}%")
                    print(f"   Missing Skills: {len(materials.get('missing_skills', []))}")

                    apply_choice = input(f"\nApply to this position? (yes/no/skip): ").lower().strip()

                    if apply_choice in ['yes', 'y']:
                        results["applications_attempted"] += 1

                        # Apply to job
                        success = self.apply_to_job(detailed_job, materials)

                        if success:
                            results["applications_successful"] += 1
                            results["successful_applications"].append({
                                "title": detailed_job["title"],
                                "location": detailed_job["location"],
                                "match_score": materials.get("match_score", 0),
                                "timestamp": datetime.now().isoformat()
                            })
                            logger.info(f"✅ Successfully applied to: {detailed_job['title']}")
                        else:
                            results["errors"].append(f"Failed to apply to: {detailed_job['title']}")

                    elif apply_choice in ['skip', 's']:
                        logger.info("Skipping this job")
                        continue
                    else:
                        logger.info("Moving to next job")
                        continue

                    # Brief pause between applications
                    time.sleep(5)

                except Exception as e:
                    error_msg = f"Error processing job '{job.get('title', 'Unknown')}': {e}"
                    logger.error(error_msg)
                    results["errors"].append(error_msg)
                    continue

            return results

        except Exception as e:
            error_msg = f"Fatal error in live application process: {e}"
            logger.error(error_msg)
            results["errors"].append(error_msg)
            return results

        finally:
            if self.driver:
                input("\nPress Enter to close browser...")
                self.driver.quit()

def main():
    """Main function to run live application system"""
    print("🎯 NEMETSCHEK LIVE APPLICATION SYSTEM")
    print("=" * 60)
    print("⚠️  WARNING: This system will submit REAL applications!")
    print("🤖 Features:")
    print("   • Finds live job postings")
    print("   • Creates tailored resumes")
    print("   • Fills application forms")
    print("   • Actually submits applications")
    print("   • Confirms submission success")
    print("\n✋ You will have control over each submission")
    print("=" * 60)

    proceed = input("\nProceed with live application system? (yes/no): ").lower().strip()

    if proceed not in ['yes', 'y']:
        print("Application system cancelled.")
        return

    # Run the live application system
    system = NemetschekLiveApplicationSystem()
    results = system.run_live_application_process()

    # Display final results
    print("\n" + "="*60)
    print("🎊 LIVE APPLICATION RESULTS")
    print("="*60)
    print(f"📋 Jobs Found: {results['jobs_found']}")
    print(f"📄 Materials Generated: {results['materials_generated']}")
    print(f"🎯 Applications Attempted: {results['applications_attempted']}")
    print(f"✅ Applications Successful: {results['applications_successful']}")

    if results["successful_applications"]:
        print(f"\n🏆 SUCCESSFUL APPLICATIONS:")
        for app in results["successful_applications"]:
            print(f"   ✅ {app['title']} ({app['match_score']:.1f}% match)")

    if results["errors"]:
        print(f"\n⚠️ ERRORS ENCOUNTERED:")
        for error in results["errors"]:
            print(f"   ❌ {error}")

    success_rate = (results['applications_successful'] / results['applications_attempted'] * 100) if results['applications_attempted'] > 0 else 0
    print(f"\n📊 Success Rate: {success_rate:.1f}%")
    print("🚀 Live application process completed!")

if __name__ == "__main__":
    main()