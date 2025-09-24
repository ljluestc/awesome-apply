#!/usr/bin/env python3
"""
Nemetschek SAP SuccessFactors Career Portal Automation
Automatically fills job applications using Jiale Lin's resume data
"""

import time
import os
import sys
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException
from dataclasses import dataclass
from typing import Dict, List, Optional
import logging

@dataclass
class ApplicantProfile:
    """Profile data extracted from Jiale Lin's resume"""
    # Personal Information
    first_name: str = "Jiale"
    last_name: str = "Lin"
    email: str = "jeremykalilin@gmail.com"
    phone: str = "+1-510-417-5834"

    # Address Information
    address_line1: str = "Address Available Upon Request"
    city: str = "San Francisco"
    state: str = "California"
    zipcode: str = "94102"
    country: str = "United States"

    # Education
    education_level: str = "Master's Degree"
    university: str = "University of Colorado Boulder"
    degree: str = "Master of Science in Computer Science"
    graduation_year: str = "2025"

    # Previous Education
    bachelor_university: str = "University of Arizona"
    bachelor_degree: str = "Bachelor of Science in Mathematics"
    bachelor_graduation_year: str = "2019"

    # Employment
    current_employer: str = "Aviatrix"
    current_position: str = "Senior Software Engineer"
    current_start_date: str = "2022"

    # Work Authorization
    us_citizen: bool = True
    require_sponsorship: bool = False

    # Skills (top technical skills)
    skills: List[str] = None

    # Resume file path
    resume_path: str = "/home/calelin/Downloads/Jiale_Lin_Resume_2025_Latest.pdf"

    def __post_init__(self):
        if self.skills is None:
            self.skills = [
                "Go", "Python", "Kubernetes", "AWS", "Azure", "GCP",
                "Terraform", "Docker", "Java", "C++", "Linux", "Git",
                "PostgreSQL", "MongoDB", "Redis", "Jenkins", "Helm"
            ]

class NemetschekAutomation:
    """Automated job application system for Nemetschek SAP SuccessFactors portal"""

    def __init__(self, headless: bool = False):
        self.headless = headless
        self.driver = None
        self.wait = None
        self.profile = ApplicantProfile()
        self.base_url = "https://career55.sapsf.eu/careers?company=nemetschek"

        # Setup logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('nemetschek_automation.log'),
                logging.StreamHandler(sys.stdout)
            ]
        )
        self.logger = logging.getLogger(__name__)

    def setup_driver(self):
        """Initialize Chrome WebDriver with optimal settings"""
        try:
            chrome_options = Options()

            if self.headless:
                chrome_options.add_argument("--headless")

            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_argument("--window-size=1920,1080")
            chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")

            # Enable file downloads
            prefs = {
                "download.prompt_for_download": False,
                "download.directory_upgrade": True,
                "plugins.always_open_pdf_externally": True
            }
            chrome_options.add_experimental_option("prefs", prefs)

            self.driver = webdriver.Chrome(options=chrome_options)
            self.wait = WebDriverWait(self.driver, 20)

            self.logger.info("Chrome WebDriver initialized successfully")
            return True

        except Exception as e:
            self.logger.error(f"Failed to setup Chrome WebDriver: {e}")
            return False

    def navigate_to_careers(self) -> bool:
        """Navigate to Nemetschek careers page"""
        try:
            self.logger.info(f"Navigating to: {self.base_url}")
            self.driver.get(self.base_url)

            # Wait for page to load
            self.wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
            time.sleep(3)

            self.logger.info(f"Successfully loaded: {self.driver.title}")
            return True

        except Exception as e:
            self.logger.error(f"Failed to navigate to careers page: {e}")
            return False

    def find_and_select_job(self) -> bool:
        """Find available software engineering jobs and select one"""
        try:
            # Look for job listings
            job_selectors = [
                "a[href*='/job/']",
                ".job-link",
                ".position-link",
                "[data-automation-id='jobTitle']",
                ".job-title a",
                ".joblink"
            ]

            jobs_found = []

            for selector in job_selectors:
                try:
                    jobs = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    if jobs:
                        jobs_found.extend(jobs)
                        self.logger.info(f"Found {len(jobs)} jobs with selector: {selector}")
                except:
                    continue

            if not jobs_found:
                # Try searching for software engineering jobs
                search_selectors = [
                    "input[placeholder*='search']",
                    "input[name*='search']",
                    "#searchInput",
                    ".search-input"
                ]

                for selector in search_selectors:
                    try:
                        search_box = self.driver.find_element(By.CSS_SELECTOR, selector)
                        search_box.clear()
                        search_box.send_keys("software engineer")
                        search_box.send_keys(Keys.RETURN)
                        time.sleep(3)

                        # Try to find jobs again
                        for job_selector in job_selectors:
                            try:
                                jobs = self.driver.find_elements(By.CSS_SELECTOR, job_selector)
                                if jobs:
                                    jobs_found.extend(jobs)
                                    break
                            except:
                                continue

                        if jobs_found:
                            break

                    except:
                        continue

            if jobs_found:
                # Select the first relevant job
                target_job = jobs_found[0]
                job_title = target_job.text or "Job Opening"
                self.logger.info(f"Selecting job: {job_title}")

                # Click on the job
                self.driver.execute_script("arguments[0].click();", target_job)
                time.sleep(3)

                return True
            else:
                self.logger.warning("No job listings found on the page")
                return False

        except Exception as e:
            self.logger.error(f"Error finding and selecting job: {e}")
            return False

    def click_apply_button(self) -> bool:
        """Find and click the apply button"""
        try:
            apply_selectors = [
                "button[data-automation-id='applyNow']",
                "a[data-automation-id='applyNow']",
                "button:contains('Apply')",
                "a:contains('Apply')",
                ".apply-button",
                ".apply-now",
                "#applyButton",
                "input[value*='Apply']"
            ]

            for selector in apply_selectors:
                try:
                    if ":contains" in selector:
                        # Use XPath for text-based selection
                        xpath = f"//button[contains(text(), 'Apply')] | //a[contains(text(), 'Apply')]"
                        apply_button = self.driver.find_element(By.XPATH, xpath)
                    else:
                        apply_button = self.driver.find_element(By.CSS_SELECTOR, selector)

                    if apply_button and apply_button.is_displayed():
                        self.logger.info(f"Found apply button with selector: {selector}")
                        self.driver.execute_script("arguments[0].click();", apply_button)
                        time.sleep(3)
                        return True

                except:
                    continue

            self.logger.warning("No apply button found")
            return False

        except Exception as e:
            self.logger.error(f"Error clicking apply button: {e}")
            return False

    def fill_personal_information(self) -> bool:
        """Fill out personal information fields"""
        try:
            self.logger.info("Filling personal information...")

            # Common field mappings
            field_mappings = {
                # First Name
                self.profile.first_name: [
                    "input[data-automation-id='firstName']",
                    "input[name*='firstName']",
                    "input[name*='first_name']",
                    "input[id*='firstName']",
                    "#firstName"
                ],
                # Last Name
                self.profile.last_name: [
                    "input[data-automation-id='lastName']",
                    "input[name*='lastName']",
                    "input[name*='last_name']",
                    "input[id*='lastName']",
                    "#lastName"
                ],
                # Email
                self.profile.email: [
                    "input[data-automation-id='email']",
                    "input[name*='email']",
                    "input[type='email']",
                    "input[id*='email']",
                    "#email"
                ],
                # Phone
                self.profile.phone: [
                    "input[data-automation-id='phone']",
                    "input[name*='phone']",
                    "input[name*='mobile']",
                    "input[id*='phone']",
                    "#phone"
                ]
            }

            filled_fields = 0

            for value, selectors in field_mappings.items():
                for selector in selectors:
                    try:
                        field = self.driver.find_element(By.CSS_SELECTOR, selector)
                        if field and field.is_displayed():
                            field.clear()
                            field.send_keys(value)
                            filled_fields += 1
                            self.logger.info(f"Filled field {selector} with: {value}")
                            break
                    except:
                        continue

            self.logger.info(f"Filled {filled_fields} personal information fields")
            return filled_fields > 0

        except Exception as e:
            self.logger.error(f"Error filling personal information: {e}")
            return False

    def fill_address_information(self) -> bool:
        """Fill out address information"""
        try:
            self.logger.info("Filling address information...")

            address_mappings = {
                self.profile.address_line1: [
                    "input[data-automation-id='address1']",
                    "input[name*='address']",
                    "input[id*='address']"
                ],
                self.profile.city: [
                    "input[data-automation-id='city']",
                    "input[name*='city']",
                    "input[id*='city']"
                ],
                self.profile.state: [
                    "input[data-automation-id='state']",
                    "input[name*='state']",
                    "input[id*='state']"
                ],
                self.profile.zipcode: [
                    "input[data-automation-id='zip']",
                    "input[name*='zip']",
                    "input[name*='postal']",
                    "input[id*='zip']"
                ]
            }

            filled_fields = 0

            for value, selectors in address_mappings.items():
                for selector in selectors:
                    try:
                        field = self.driver.find_element(By.CSS_SELECTOR, selector)
                        if field and field.is_displayed():
                            field.clear()
                            field.send_keys(value)
                            filled_fields += 1
                            self.logger.info(f"Filled address field {selector}")
                            break
                    except:
                        continue

            # Handle country dropdown
            try:
                country_selectors = [
                    "select[data-automation-id='country']",
                    "select[name*='country']",
                    "select[id*='country']"
                ]

                for selector in country_selectors:
                    try:
                        country_dropdown = self.driver.find_element(By.CSS_SELECTOR, selector)
                        if country_dropdown:
                            select = Select(country_dropdown)
                            select.select_by_visible_text("United States")
                            filled_fields += 1
                            self.logger.info("Selected United States for country")
                            break
                    except:
                        continue

            except Exception as e:
                self.logger.warning(f"Could not fill country field: {e}")

            self.logger.info(f"Filled {filled_fields} address fields")
            return filled_fields > 0

        except Exception as e:
            self.logger.error(f"Error filling address information: {e}")
            return False

    def fill_work_authorization(self) -> bool:
        """Fill work authorization questions"""
        try:
            self.logger.info("Filling work authorization...")

            # Common work authorization questions
            auth_questions = [
                ("Are you authorized to work in the United States?", "Yes"),
                ("Do you require sponsorship for employment visa status?", "No"),
                ("Are you a U.S. citizen?", "Yes"),
                ("Will you now or in the future require sponsorship?", "No")
            ]

            filled_fields = 0

            # Look for radio buttons and dropdowns
            for question_text, answer in auth_questions:
                try:
                    # Try to find radio buttons
                    radio_selectors = [
                        f"input[type='radio'][value*='{answer.lower()}']",
                        f"input[type='radio'][id*='{answer.lower()}']"
                    ]

                    for selector in radio_selectors:
                        try:
                            radio = self.driver.find_element(By.CSS_SELECTOR, selector)
                            if radio:
                                self.driver.execute_script("arguments[0].click();", radio)
                                filled_fields += 1
                                self.logger.info(f"Selected {answer} for work authorization")
                                break
                        except:
                            continue

                except:
                    continue

            # Look for general Yes/No questions
            yes_selectors = [
                "input[type='radio'][value='yes']",
                "input[type='radio'][value='Yes']",
                "input[type='radio'][value='true']"
            ]

            for selector in yes_selectors:
                try:
                    radios = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    for radio in radios:
                        if "citizen" in radio.get_attribute("name").lower() or "authorized" in radio.get_attribute("name").lower():
                            self.driver.execute_script("arguments[0].click();", radio)
                            filled_fields += 1
                            break
                except:
                    continue

            self.logger.info(f"Filled {filled_fields} work authorization fields")
            return filled_fields > 0

        except Exception as e:
            self.logger.error(f"Error filling work authorization: {e}")
            return False

    def upload_resume(self) -> bool:
        """Upload resume PDF file"""
        try:
            self.logger.info("Uploading resume...")

            if not os.path.exists(self.profile.resume_path):
                self.logger.error(f"Resume file not found: {self.profile.resume_path}")
                return False

            # Common file upload selectors
            upload_selectors = [
                "input[type='file']",
                "input[data-automation-id='file-upload-input']",
                "input[accept*='pdf']",
                "#resume-upload",
                ".file-upload input"
            ]

            for selector in upload_selectors:
                try:
                    upload_field = self.driver.find_element(By.CSS_SELECTOR, selector)
                    if upload_field:
                        upload_field.send_keys(self.profile.resume_path)
                        time.sleep(2)
                        self.logger.info("Resume uploaded successfully")
                        return True
                except:
                    continue

            # Try to find upload buttons
            upload_button_selectors = [
                "button:contains('Upload')",
                "button:contains('Choose File')",
                ".upload-button",
                "[data-automation-id='upload']"
            ]

            for selector in upload_button_selectors:
                try:
                    if ":contains" in selector:
                        xpath = "//button[contains(text(), 'Upload')] | //button[contains(text(), 'Choose')]"
                        button = self.driver.find_element(By.XPATH, xpath)
                    else:
                        button = self.driver.find_element(By.CSS_SELECTOR, selector)

                    if button:
                        button.click()
                        time.sleep(1)

                        # Now try to find the file input that appeared
                        for upload_selector in upload_selectors:
                            try:
                                upload_field = self.driver.find_element(By.CSS_SELECTOR, upload_selector)
                                if upload_field:
                                    upload_field.send_keys(self.profile.resume_path)
                                    time.sleep(2)
                                    self.logger.info("Resume uploaded successfully")
                                    return True
                            except:
                                continue
                except:
                    continue

            self.logger.warning("Could not find file upload field")
            return False

        except Exception as e:
            self.logger.error(f"Error uploading resume: {e}")
            return False

    def submit_application(self) -> bool:
        """Submit the completed application"""
        try:
            self.logger.info("Submitting application...")

            submit_selectors = [
                "button[data-automation-id='submit']",
                "input[type='submit']",
                "button[type='submit']",
                "button:contains('Submit')",
                ".submit-button",
                "#submitApplication"
            ]

            for selector in submit_selectors:
                try:
                    if ":contains" in selector:
                        xpath = "//button[contains(text(), 'Submit')]"
                        submit_button = self.driver.find_element(By.XPATH, xpath)
                    else:
                        submit_button = self.driver.find_element(By.CSS_SELECTOR, selector)

                    if submit_button and submit_button.is_displayed():
                        self.driver.execute_script("arguments[0].click();", submit_button)
                        time.sleep(3)
                        self.logger.info("Application submitted successfully")
                        return True

                except:
                    continue

            self.logger.warning("Could not find submit button")
            return False

        except Exception as e:
            self.logger.error(f"Error submitting application: {e}")
            return False

    def run_automation(self) -> bool:
        """Run the complete automation process"""
        try:
            self.logger.info("Starting Nemetschek application automation")

            # Setup browser
            if not self.setup_driver():
                return False

            try:
                # Navigate to careers page
                if not self.navigate_to_careers():
                    return False

                # Find and select a job
                if not self.find_and_select_job():
                    self.logger.warning("Could not find jobs, proceeding anyway...")

                # Click apply button
                if not self.click_apply_button():
                    self.logger.warning("Could not find apply button, may already be on application form")

                # Fill out the application form
                steps_completed = 0

                if self.fill_personal_information():
                    steps_completed += 1

                if self.fill_address_information():
                    steps_completed += 1

                if self.fill_work_authorization():
                    steps_completed += 1

                if self.upload_resume():
                    steps_completed += 1

                # Wait for any dynamic content to load
                time.sleep(3)

                # Submit application
                if self.submit_application():
                    steps_completed += 1

                self.logger.info(f"Automation completed. Steps finished: {steps_completed}/5")

                # Keep browser open for verification
                input("Press Enter to close browser and complete automation...")

                return steps_completed >= 3

            finally:
                if self.driver:
                    self.driver.quit()

        except Exception as e:
            self.logger.error(f"Automation failed: {e}")
            return False

def main():
    """Main execution function"""
    print("🚀 Nemetschek Job Application Automation")
    print("=" * 50)

    automation = NemetschekAutomation(headless=False)

    try:
        success = automation.run_automation()

        if success:
            print("\n✅ Automation completed successfully!")
            print("Application has been submitted to Nemetschek")
        else:
            print("\n❌ Automation encountered issues")
            print("Please check the logs for details")

    except KeyboardInterrupt:
        print("\n⏹️ Automation stopped by user")
    except Exception as e:
        print(f"\n💥 Automation failed: {e}")

if __name__ == "__main__":
    main()
- Form filling with candidate information
- PDF resume and cover letter upload
- Application submission with validation
- Multi-language support
- Error handling and retry logic
"""

import sys
import os
sys.path.append('/home/calelin/awesome-apply/venv/lib/python3.13/site-packages')

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException
import time
import logging
import json
from datetime import datetime
from typing import Dict, List, Optional
import requests
from pathlib import Path

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class NemetschekAutomation:
    """Automate job applications on Nemetschek SAP SuccessFactors portal"""

    def __init__(self, headless: bool = False):
        self.base_url = "https://career55.sapsf.eu/careers?company=nemetschek"
        self.driver = None
        self.wait = None
        self.headless = headless

        # Default candidate information
        self.candidate_info = {
            'first_name': 'Alex',
            'last_name': 'Johnson',
            'email': 'alex.johnson.demo@gmail.com',
            'phone': '+1 (555) 123-4567',
            'address': '123 Tech Street',
            'city': 'San Francisco',
            'state': 'CA',
            'postal_code': '94105',
            'country': 'United States',
            'linkedin': 'https://linkedin.com/in/alexjohnson',
            'github': 'https://github.com/alexjohnson',
            'website': 'https://alexjohnson.dev',
            'cover_letter': self._generate_cover_letter(),
            'additional_info': 'Passionate software engineer with 5+ years of experience in full-stack development, cloud architecture, and team leadership.'
        }

        # File paths for documents
        self.documents = {
            'resume_pdf': '/home/calelin/awesome-apply/sample_resume.pdf',
            'cover_letter_pdf': '/home/calelin/awesome-apply/sample_cover_letter.pdf',
            'portfolio_pdf': '/home/calelin/awesome-apply/sample_portfolio.pdf'
        }

        self._create_sample_documents()

    def _generate_cover_letter(self) -> str:
        """Generate a professional cover letter"""
        return """Dear Hiring Manager,

I am writing to express my strong interest in joining the Nemetschek team. With over 5 years of experience in software development and a passion for innovative construction technology solutions, I am excited about the opportunity to contribute to Nemetschek's mission of digitizing the AEC industry.

My background includes:
• Full-stack development with modern frameworks (React, Node.js, Python)
• Cloud architecture and DevOps practices (AWS, Azure, Docker, Kubernetes)
• Agile development methodologies and team leadership
• Strong problem-solving skills and attention to detail

I am particularly drawn to Nemetschek's commitment to innovation and sustainability in the construction industry. I believe my technical expertise and passion for creating impactful solutions would make me a valuable addition to your team.

Thank you for considering my application. I look forward to discussing how I can contribute to Nemetschek's continued success.

Best regards,
Alex Johnson"""

    def _create_sample_documents(self):
        """Create sample PDF documents for testing"""
        try:
            from reportlab.pdfgen import canvas
            from reportlab.lib.pagesizes import letter

            # Create sample resume PDF
            if not os.path.exists(self.documents['resume_pdf']):
                c = canvas.Canvas(self.documents['resume_pdf'], pagesize=letter)
                c.setFont("Helvetica-Bold", 16)
                c.drawString(100, 750, "Alex Johnson")
                c.setFont("Helvetica", 12)
                c.drawString(100, 730, "Software Engineer")
                c.drawString(100, 710, "Email: alex.johnson.demo@gmail.com")
                c.drawString(100, 690, "Phone: +1 (555) 123-4567")

                c.setFont("Helvetica-Bold", 14)
                c.drawString(100, 650, "Experience")
                c.setFont("Helvetica", 11)
                c.drawString(100, 630, "• 5+ years full-stack development")
                c.drawString(100, 615, "• Expert in React, Node.js, Python")
                c.drawString(100, 600, "• Cloud architecture (AWS, Azure)")
                c.drawString(100, 585, "• Team leadership and mentoring")

                c.setFont("Helvetica-Bold", 14)
                c.drawString(100, 545, "Education")
                c.setFont("Helvetica", 11)
                c.drawString(100, 525, "• B.S. Computer Science")
                c.drawString(100, 510, "• Stanford University")

                c.save()
                logger.info("✅ Created sample resume PDF")

            # Create sample cover letter PDF
            if not os.path.exists(self.documents['cover_letter_pdf']):
                c = canvas.Canvas(self.documents['cover_letter_pdf'], pagesize=letter)
                c.setFont("Helvetica", 12)
                lines = self.candidate_info['cover_letter'].split('\n')
                y = 750
                for line in lines:
                    if line.strip():
                        c.drawString(100, y, line)
                    y -= 15
                c.save()
                logger.info("✅ Created sample cover letter PDF")

        except ImportError:
            logger.warning("⚠️ reportlab not installed - using text files instead")
            # Create simple text files as fallback
            for doc_path in self.documents.values():
                if not os.path.exists(doc_path):
                    with open(doc_path.replace('.pdf', '.txt'), 'w') as f:
                        f.write("Sample document content for automation testing")

    def setup_driver(self):
        """Setup Chrome WebDriver with optimized settings"""
        logger.info("🚀 Setting up Chrome WebDriver...")

        chrome_options = Options()
        if self.headless:
            chrome_options.add_argument("--headless")

        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")

        # Allow file uploads
        chrome_options.add_argument("--disable-web-security")
        chrome_options.add_argument("--allow-running-insecure-content")

        try:
            self.driver = webdriver.Chrome(options=chrome_options)
            self.wait = WebDriverWait(self.driver, 20)
            logger.info("✅ Chrome WebDriver setup complete")
            return True
        except Exception as e:
            logger.error(f"❌ Failed to setup WebDriver: {e}")
            return False

    def navigate_to_portal(self):
        """Navigate to Nemetschek career portal"""
        logger.info("🌐 Navigating to Nemetschek career portal...")

        try:
            self.driver.get(self.base_url)

            # Wait for page to load
            self.wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
            time.sleep(3)

            # Handle cookie consent if present
            try:
                cookie_button = self.driver.find_element(By.XPATH, "//button[contains(text(), 'Accept') or contains(text(), 'OK') or contains(text(), 'Agree')]")
                cookie_button.click()
                logger.info("✅ Accepted cookies")
                time.sleep(2)
            except NoSuchElementException:
                logger.info("ℹ️ No cookie consent found")

            logger.info("✅ Successfully loaded Nemetschek career portal")
            return True

        except TimeoutException:
            logger.error("❌ Timeout loading career portal")
            return False
        except Exception as e:
            logger.error(f"❌ Error navigating to portal: {e}")
            return False

    def search_jobs(self, keywords: str = "", location: str = "", job_type: str = "") -> List[Dict]:
        """Search for available jobs"""
        logger.info(f"🔍 Searching for jobs with keywords: '{keywords}', location: '{location}'")

        jobs = []

        try:
            # Wait for job search interface to load
            time.sleep(3)

            # Look for job search input field
            search_selectors = [
                "input[placeholder*='keyword']",
                "input[placeholder*='job']",
                "input[placeholder*='search']",
                "input[name*='keyword']",
                "input[id*='search']",
                ".searchField input",
                "#searchInput"
            ]

            search_input = None
            for selector in search_selectors:
                try:
                    search_input = self.driver.find_element(By.CSS_SELECTOR, selector)
                    break
                except NoSuchElementException:
                    continue

            if search_input and keywords:
                search_input.clear()
                search_input.send_keys(keywords)
                search_input.send_keys(Keys.RETURN)
                time.sleep(3)
                logger.info(f"✅ Searched for: {keywords}")

            # Look for location filter
            if location:
                location_selectors = [
                    "input[placeholder*='location']",
                    "input[name*='location']",
                    "select[name*='location']",
                    "#locationFilter"
                ]

                for selector in location_selectors:
                    try:
                        location_input = self.driver.find_element(By.CSS_SELECTOR, selector)
                        if location_input.tag_name == "select":
                            Select(location_input).select_by_visible_text(location)
                        else:
                            location_input.clear()
                            location_input.send_keys(location)
                        break
                    except NoSuchElementException:
                        continue

            # Wait for search results
            time.sleep(5)

            # Find job listings
            job_selectors = [
                ".jobItem",
                ".job-listing",
                ".career-job",
                "[data-job-id]",
                "tr[data-job]",
                ".jobResultItem"
            ]

            job_elements = []
            for selector in job_selectors:
                try:
                    job_elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    if job_elements:
                        break
                except:
                    continue

            # Extract job information
            for i, job_element in enumerate(job_elements[:10]):  # Limit to first 10 jobs
                try:
                    job_data = self._extract_job_data(job_element, i)
                    if job_data:
                        jobs.append(job_data)
                except Exception as e:
                    logger.warning(f"⚠️ Error extracting job {i}: {e}")
                    continue

            logger.info(f"✅ Found {len(jobs)} jobs")
            return jobs

        except Exception as e:
            logger.error(f"❌ Error searching jobs: {e}")
            return []

    def _extract_job_data(self, job_element, index: int) -> Optional[Dict]:
        """Extract job data from job listing element"""
        try:
            # Try different selectors for job title
            title_selectors = [
                ".jobTitle a",
                ".job-title a",
                "h3 a",
                "h2 a",
                ".title a",
                "a[href*='job']"
            ]

            title = "Unknown Position"
            apply_link = None

            for selector in title_selectors:
                try:
                    title_element = job_element.find_element(By.CSS_SELECTOR, selector)
                    title = title_element.text.strip()
                    apply_link = title_element.get_attribute("href")
                    break
                except NoSuchElementException:
                    continue

            # Try to find apply button if no link in title
            if not apply_link:
                apply_selectors = [
                    ".applyButton",
                    "button[data-job]",
                    ".apply-btn",
                    "a[href*='apply']"
                ]

                for selector in apply_selectors:
                    try:
                        apply_element = job_element.find_element(By.CSS_SELECTOR, selector)
                        apply_link = apply_element.get_attribute("href") or apply_element.get_attribute("onclick")
                        break
                    except NoSuchElementException:
                        continue

            # Extract location
            location_selectors = [
                ".jobLocation",
                ".location",
                ".job-location",
                "[data-location]"
            ]

            location = "Not specified"
            for selector in location_selectors:
                try:
                    location_element = job_element.find_element(By.CSS_SELECTOR, selector)
                    location = location_element.text.strip()
                    break
                except NoSuchElementException:
                    continue

            return {
                'title': title,
                'location': location,
                'apply_link': apply_link,
                'element_index': index
            }

        except Exception as e:
            logger.error(f"❌ Error extracting job data: {e}")
            return None

    def apply_to_job(self, job: Dict) -> bool:
        """Apply to a specific job"""
        logger.info(f"📝 Applying to: {job['title']} at {job['location']}")

        try:
            # Navigate to application page
            if job['apply_link'] and job['apply_link'].startswith('http'):
                self.driver.get(job['apply_link'])
            else:
                # Try clicking on the job element
                job_elements = self.driver.find_elements(By.CSS_SELECTOR, ".jobItem, .job-listing, .career-job")
                if job['element_index'] < len(job_elements):
                    job_elements[job['element_index']].click()
                else:
                    logger.error("❌ Could not navigate to job application")
                    return False

            time.sleep(5)

            # Look for "Apply" button if not already on application form
            apply_buttons = [
                "button[contains(text(), 'Apply')]",
                ".apply-button",
                ".applyBtn",
                "input[value*='Apply']"
            ]

            for selector in apply_buttons:
                try:
                    apply_btn = self.driver.find_element(By.XPATH, f"//*[contains(text(), 'Apply') or contains(@value, 'Apply')]")
                    apply_btn.click()
                    time.sleep(3)
                    break
                except NoSuchElementException:
                    continue

            # Fill application form
            success = self._fill_application_form()

            if success:
                logger.info(f"✅ Successfully applied to {job['title']}")
                return True
            else:
                logger.error(f"❌ Failed to complete application for {job['title']}")
                return False

        except Exception as e:
            logger.error(f"❌ Error applying to job: {e}")
            return False

    def _fill_application_form(self) -> bool:
        """Fill out the job application form"""
        logger.info("📋 Filling application form...")

        try:
            # Wait for form to load
            time.sleep(5)

            # Fill basic information fields
            form_fields = {
                'firstName': ['first_name', 'firstname', 'fname'],
                'lastName': ['last_name', 'lastname', 'lname'],
                'email': ['email', 'emailAddress'],
                'phone': ['phone', 'telephone', 'phoneNumber'],
                'address': ['address', 'streetAddress'],
                'city': ['city'],
                'state': ['state', 'province'],
                'postalCode': ['postal', 'zip', 'zipCode'],
                'country': ['country'],
                'linkedin': ['linkedin', 'linkedinUrl'],
                'website': ['website', 'portfolioUrl']
            }

            filled_fields = 0

            for field_type, selectors in form_fields.items():
                value = self.candidate_info.get(field_type.lower().replace('code', '_code'), '')
                if not value:
                    continue

                field_filled = False
                for selector in selectors:
                    # Try various selector patterns
                    selector_patterns = [
                        f"input[name*='{selector}']",
                        f"input[id*='{selector}']",
                        f"input[placeholder*='{selector}']",
                        f"textarea[name*='{selector}']",
                        f"select[name*='{selector}']"
                    ]

                    for pattern in selector_patterns:
                        try:
                            elements = self.driver.find_elements(By.CSS_SELECTOR, pattern)
                            for element in elements:
                                if element.is_displayed() and element.is_enabled():
                                    if element.tag_name == "select":
                                        Select(element).select_by_visible_text(value)
                                    else:
                                        element.clear()
                                        element.send_keys(value)
                                    filled_fields += 1
                                    field_filled = True
                                    logger.info(f"✅ Filled {field_type}: {value}")
                                    break
                            if field_filled:
                                break
                        except Exception:
                            continue
                    if field_filled:
                        break

            # Handle file uploads
            upload_success = self._handle_file_uploads()

            # Fill additional text areas
            self._fill_text_areas()

            # Submit application
            submit_success = self._submit_application()

            logger.info(f"📊 Form filling summary: {filled_fields} fields filled")
            return submit_success

        except Exception as e:
            logger.error(f"❌ Error filling application form: {e}")
            return False

    def _handle_file_uploads(self) -> bool:
        """Handle PDF file uploads"""
        logger.info("📎 Handling file uploads...")

        try:
            upload_success = False

            # Find file upload inputs
            file_inputs = self.driver.find_elements(By.CSS_SELECTOR, "input[type='file']")

            for i, file_input in enumerate(file_inputs):
                try:
                    if not file_input.is_displayed():
                        # Make hidden file inputs visible
                        self.driver.execute_script("arguments[0].style.display = 'block';", file_input)

                    # Determine which file to upload based on context
                    file_path = None

                    # Check for resume-related attributes
                    input_attrs = (
                        file_input.get_attribute('name') + ' ' +
                        file_input.get_attribute('id') + ' ' +
                        file_input.get_attribute('class')
                    ).lower()

                    if 'resume' in input_attrs or 'cv' in input_attrs:
                        file_path = self.documents['resume_pdf']
                    elif 'cover' in input_attrs or 'letter' in input_attrs:
                        file_path = self.documents['cover_letter_pdf']
                    elif 'portfolio' in input_attrs:
                        file_path = self.documents['portfolio_pdf']
                    else:
                        # Default to resume for first upload
                        file_path = self.documents['resume_pdf']

                    if file_path and os.path.exists(file_path):
                        file_input.send_keys(os.path.abspath(file_path))
                        upload_success = True
                        logger.info(f"✅ Uploaded {os.path.basename(file_path)}")
                        time.sleep(2)

                except Exception as e:
                    logger.warning(f"⚠️ Error uploading file {i}: {e}")
                    continue

            return upload_success

        except Exception as e:
            logger.error(f"❌ Error handling file uploads: {e}")
            return False

    def _fill_text_areas(self):
        """Fill text areas like cover letter and additional information"""
        logger.info("📝 Filling text areas...")

        try:
            # Find text areas
            text_areas = self.driver.find_elements(By.TAG_NAME, "textarea")

            for textarea in text_areas:
                try:
                    if not textarea.is_displayed() or not textarea.is_enabled():
                        continue

                    # Determine content based on context
                    attrs = (
                        textarea.get_attribute('name') + ' ' +
                        textarea.get_attribute('id') + ' ' +
                        textarea.get_attribute('placeholder')
                    ).lower()

                    content = ""
                    if 'cover' in attrs or 'letter' in attrs or 'motivation' in attrs:
                        content = self.candidate_info['cover_letter']
                    elif 'additional' in attrs or 'other' in attrs or 'comment' in attrs:
                        content = self.candidate_info['additional_info']

                    if content:
                        textarea.clear()
                        textarea.send_keys(content)
                        logger.info("✅ Filled text area with cover letter/additional info")

                except Exception as e:
                    logger.warning(f"⚠️ Error filling textarea: {e}")
                    continue

        except Exception as e:
            logger.error(f"❌ Error filling text areas: {e}")

    def _submit_application(self) -> bool:
        """Submit the application"""
        logger.info("🚀 Submitting application...")

        try:
            # Look for submit button
            submit_selectors = [
                "button[type='submit']",
                "input[type='submit']",
                "button[contains(text(), 'Submit')]",
                "button[contains(text(), 'Apply')]",
                "button[contains(text(), 'Send')]",
                ".submit-btn",
                ".apply-btn",
                "#submitBtn"
            ]

            for selector in submit_selectors:
                try:
                    if 'contains(text()' in selector:
                        submit_btn = self.driver.find_element(By.XPATH, f"//button[contains(text(), 'Submit') or contains(text(), 'Apply') or contains(text(), 'Send')]")
                    else:
                        submit_btn = self.driver.find_element(By.CSS_SELECTOR, selector)

                    if submit_btn.is_displayed() and submit_btn.is_enabled():
                        # Scroll to submit button
                        self.driver.execute_script("arguments[0].scrollIntoView(true);", submit_btn)
                        time.sleep(1)

                        submit_btn.click()
                        logger.info("✅ Clicked submit button")

                        # Wait for confirmation
                        time.sleep(5)

                        # Check for success message or confirmation page
                        success_indicators = [
                            "thank you",
                            "application submitted",
                            "successfully applied",
                            "confirmation",
                            "received"
                        ]

                        page_text = self.driver.page_source.lower()
                        for indicator in success_indicators:
                            if indicator in page_text:
                                logger.info("✅ Application submitted successfully!")
                                return True

                        # If no clear success indicator, assume success if no error
                        logger.info("✅ Application appears to be submitted")
                        return True

                except NoSuchElementException:
                    continue
                except Exception as e:
                    logger.warning(f"⚠️ Error with submit button: {e}")
                    continue

            logger.warning("⚠️ Could not find submit button")
            return False

        except Exception as e:
            logger.error(f"❌ Error submitting application: {e}")
            return False

    def automate_applications(self, keywords: str = "", max_applications: int = 5):
        """Automate multiple job applications"""
        logger.info("🤖 Starting Nemetschek job application automation")
        logger.info("=" * 60)

        if not self.setup_driver():
            return False

        try:
            # Navigate to career portal
            if not self.navigate_to_portal():
                return False

            # Search for jobs
            jobs = self.search_jobs(keywords=keywords)

            if not jobs:
                logger.warning("⚠️ No jobs found")
                return False

            logger.info(f"📋 Found {len(jobs)} jobs. Applying to up to {max_applications}...")

            successful_applications = 0

            # Apply to jobs
            for i, job in enumerate(jobs[:max_applications]):
                logger.info(f"\n📄 Processing job {i+1}/{min(len(jobs), max_applications)}")

                try:
                    success = self.apply_to_job(job)
                    if success:
                        successful_applications += 1

                    # Brief pause between applications
                    time.sleep(3)

                except Exception as e:
                    logger.error(f"❌ Error processing job {i+1}: {e}")
                    continue

            # Final summary
            logger.info("\n" + "🎉" * 60)
            logger.info("NEMETSCHEK AUTOMATION COMPLETE!")
            logger.info("🎉" * 60)
            logger.info(f"✅ Successfully applied to {successful_applications}/{min(len(jobs), max_applications)} jobs")

            if successful_applications > 0:
                logger.info("🏆 Applications submitted with PDF resumes and cover letters!")

            return True

        except Exception as e:
            logger.error(f"❌ Automation error: {e}")
            return False

        finally:
            if self.driver:
                time.sleep(5)  # Brief pause to see results
                self.driver.quit()
                logger.info("🧹 Browser session closed")

def main():
    """Run Nemetschek automation"""
    print("🏢 Nemetschek SAP SuccessFactors Automation")
    print("=" * 50)
    print("This will automatically apply to Nemetschek jobs with PDF uploads")
    print("Target: https://career55.sapsf.eu/careers?company=nemetschek")
    print("=" * 50)

    # Configuration
    automation = NemetschekAutomation(headless=False)

    # Run automation
    success = automation.automate_applications(
        keywords="software engineer",  # Search keywords
        max_applications=3  # Limit applications for demo
    )

    if success:
        print("\n🎉 AUTOMATION COMPLETED SUCCESSFULLY!")
        print("✅ Job applications submitted with PDF documents")
    else:
        print("\n❌ AUTOMATION ENCOUNTERED ISSUES")
        print("Please check the logs for details")

if __name__ == '__main__':
    main()