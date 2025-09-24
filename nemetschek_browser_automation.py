#!/usr/bin/env python3
"""
Nemetschek Browser Automation for Job Applications
Automates the application process on Nemetschek's careers website
"""

import time
import logging
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.webdriver.common.keys import Keys
import os
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class NemetschekJobApplicationAutomator:
    def __init__(self):
        self.candidate_info = {
            'first_name': 'Jiale',
            'last_name': 'Lin',
            'email': 'jeremykalilin@gmail.com',
            'phone': '+1-510-417-5834',
            'linkedin': 'https://linkedin.com/in/jiale-lin',
            'github': 'https://ljluestc.github.io',
            'address': {
                'street': '1234 Main St',
                'city': 'Santa Clara',
                'state': 'CA',
                'zip_code': '95054',
                'country': 'United States'
            },
            'work_authorization': 'US Citizen',
            'availability': 'Immediately'
        }

    def setup_browser(self, headless=False):
        """Setup Chrome browser with appropriate options"""
        chrome_options = Options()
        if headless:
            chrome_options.add_argument("--headless")

        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("--user-agent=Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36")

        # Allow file uploads
        prefs = {
            "download.default_directory": str(Path.cwd()),
            "download.prompt_for_download": False,
            "download.directory_upgrade": True,
            "safebrowsing.enabled": True
        }
        chrome_options.add_experimental_option("prefs", prefs)

        driver = webdriver.Chrome(options=chrome_options)
        return driver

    def navigate_to_nemetschek_careers(self, driver):
        """Navigate to Nemetschek careers page"""
        try:
            logger.info("Navigating to Nemetschek careers page...")
            driver.get("https://careers.nemetschek.com")

            # Wait for page to load
            wait = WebDriverWait(driver, 10)
            wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))

            logger.info("Successfully loaded Nemetschek careers page")
            return True

        except Exception as e:
            logger.error(f"Error navigating to careers page: {e}")
            return False

    def search_for_devops_jobs(self, driver):
        """Search for DevOps and Cloud Engineer jobs"""
        try:
            wait = WebDriverWait(driver, 10)

            # Look for search functionality
            search_selectors = [
                "input[placeholder*='search']",
                "input[name*='search']",
                "input[id*='search']",
                ".search-input",
                "#search",
                "[data-testid*='search']"
            ]

            search_input = None
            for selector in search_selectors:
                try:
                    search_input = driver.find_element(By.CSS_SELECTOR, selector)
                    break
                except NoSuchElementException:
                    continue

            if search_input:
                logger.info("Found search input, searching for DevOps jobs...")
                search_input.clear()
                search_input.send_keys("DevOps Cloud Engineer")
                search_input.send_keys(Keys.RETURN)
                time.sleep(2)

            # Look for job listings
            job_selectors = [
                "a[href*='job']",
                ".job-listing",
                ".career-item",
                "[data-testid*='job']",
                ".job-title a"
            ]

            jobs = []
            for selector in job_selectors:
                try:
                    job_elements = driver.find_elements(By.CSS_SELECTOR, selector)
                    if job_elements:
                        jobs = job_elements
                        break
                except:
                    continue

            logger.info(f"Found {len(jobs)} job listings")
            return jobs

        except Exception as e:
            logger.error(f"Error searching for jobs: {e}")
            return []

    def apply_to_job(self, driver, job_element):
        """Apply to a specific job"""
        try:
            # Click on the job to view details
            driver.execute_script("arguments[0].click();", job_element)
            time.sleep(3)

            # Look for apply button
            apply_selectors = [
                "button:contains('Apply')",
                "a:contains('Apply')",
                "[data-testid*='apply']",
                ".apply-button",
                "input[value*='Apply']",
                "button[class*='apply']"
            ]

            apply_button = None
            for selector in apply_selectors:
                try:
                    if ":contains(" in selector:
                        # Use XPath for text search
                        xpath = f"//button[contains(text(), 'Apply')] | //a[contains(text(), 'Apply')] | //input[contains(@value, 'Apply')]"
                        apply_button = driver.find_element(By.XPATH, xpath)
                    else:
                        apply_button = driver.find_element(By.CSS_SELECTOR, selector)
                    break
                except NoSuchElementException:
                    continue

            if not apply_button:
                logger.warning("Could not find apply button")
                return False

            logger.info("Found apply button, clicking...")
            driver.execute_script("arguments[0].click();", apply_button)
            time.sleep(3)

            # Fill out application form
            self.fill_application_form(driver)

            return True

        except Exception as e:
            logger.error(f"Error applying to job: {e}")
            return False

    def fill_application_form(self, driver):
        """Fill out the application form with candidate information"""
        try:
            wait = WebDriverWait(driver, 10)

            # Define form field mappings
            field_mappings = {
                'first_name': ['firstName', 'first_name', 'fname', 'givenName'],
                'last_name': ['lastName', 'last_name', 'lname', 'familyName', 'surname'],
                'email': ['email', 'emailAddress', 'mail'],
                'phone': ['phone', 'phoneNumber', 'mobile', 'telephone'],
                'linkedin': ['linkedin', 'linkedinUrl', 'linkedInProfile'],
                'github': ['github', 'githubUrl', 'portfolio', 'website']
            }

            # Fill out basic information
            for field_type, field_names in field_mappings.items():
                value = self.candidate_info.get(field_type, '')

                for field_name in field_names:
                    selectors = [
                        f"input[name='{field_name}']",
                        f"input[id='{field_name}']",
                        f"input[name*='{field_name}']",
                        f"input[placeholder*='{field_name}']"
                    ]

                    for selector in selectors:
                        try:
                            field = driver.find_element(By.CSS_SELECTOR, selector)
                            field.clear()
                            field.send_keys(value)
                            logger.info(f"Filled {field_type}: {value}")
                            break
                        except NoSuchElementException:
                            continue
                    else:
                        continue
                    break

            # Handle file uploads
            self.upload_resume(driver)

            # Handle dropdown selections
            self.handle_dropdowns(driver)

            logger.info("Successfully filled application form")

        except Exception as e:
            logger.error(f"Error filling application form: {e}")

    def upload_resume(self, driver):
        """Upload resume file"""
        try:
            # Look for file input elements
            file_inputs = driver.find_elements(By.CSS_SELECTOR, "input[type='file']")

            if not file_inputs:
                logger.warning("No file upload fields found")
                return

            # Find the most recent resume PDF
            resume_files = list(Path(".").glob("Jiale_Lin_Resume_*.pdf"))
            if not resume_files:
                logger.warning("No resume PDF files found")
                return

            # Get the most recent resume
            latest_resume = max(resume_files, key=lambda x: x.stat().st_mtime)
            resume_path = str(latest_resume.absolute())

            # Upload to the first file input (usually for resume)
            file_input = file_inputs[0]
            file_input.send_keys(resume_path)
            logger.info(f"Uploaded resume: {latest_resume.name}")

        except Exception as e:
            logger.error(f"Error uploading resume: {e}")

    def handle_dropdowns(self, driver):
        """Handle dropdown selections for work authorization, etc."""
        try:
            # Work authorization dropdown
            auth_selectors = [
                "select[name*='authorization']",
                "select[name*='status']",
                "select[name*='citizen']",
                "[data-testid*='authorization']"
            ]

            for selector in auth_selectors:
                try:
                    dropdown = driver.find_element(By.CSS_SELECTOR, selector)
                    # Try to select US Citizen or similar
                    options = dropdown.find_elements(By.TAG_NAME, "option")
                    for option in options:
                        if any(text in option.text.lower() for text in ['citizen', 'authorized', 'yes']):
                            option.click()
                            logger.info(f"Selected work authorization: {option.text}")
                            break
                    break
                except NoSuchElementException:
                    continue

        except Exception as e:
            logger.error(f"Error handling dropdowns: {e}")

    def submit_application(self, driver):
        """Submit the application"""
        try:
            # Look for submit button
            submit_selectors = [
                "button[type='submit']",
                "input[type='submit']",
                "button:contains('Submit')",
                "[data-testid*='submit']",
                ".submit-button"
            ]

            submit_button = None
            for selector in submit_selectors:
                try:
                    if ":contains(" in selector:
                        submit_button = driver.find_element(By.XPATH, "//button[contains(text(), 'Submit')] | //input[contains(@value, 'Submit')]")
                    else:
                        submit_button = driver.find_element(By.CSS_SELECTOR, selector)
                    break
                except NoSuchElementException:
                    continue

            if submit_button:
                logger.info("Found submit button - REVIEW APPLICATION BEFORE SUBMITTING")
                print("\n" + "="*60)
                print("APPLICATION READY FOR SUBMISSION")
                print("="*60)
                print("Please review the application form carefully.")
                print("The automation has filled out the form but you should:")
                print("1. Review all filled information")
                print("2. Upload additional documents if needed")
                print("3. Add cover letter if required")
                print("4. Answer any additional questions")
                print("5. Submit manually when ready")
                print("="*60)

                # Don't auto-submit, let user review
                input("Press Enter when you have reviewed and are ready to continue...")

                return True
            else:
                logger.warning("Could not find submit button")
                return False

        except Exception as e:
            logger.error(f"Error submitting application: {e}")
            return False

    def automate_nemetschek_application(self):
        """Main function to automate Nemetschek application process"""
        driver = None
        try:
            logger.info("Starting Nemetschek application automation...")

            # Setup browser
            driver = self.setup_browser(headless=False)

            # Navigate to careers page
            if not self.navigate_to_nemetschek_careers(driver):
                return False

            # Search for relevant jobs
            jobs = self.search_for_devops_jobs(driver)

            if not jobs:
                logger.warning("No jobs found, navigating to known Cloud DevOps position...")
                # Navigate directly to known position
                driver.get("https://careers.nemetschek.com/job-invite/1496")
                time.sleep(3)

                # Try to apply to this specific job
                self.apply_to_specific_job(driver)
            else:
                # Apply to first relevant job
                logger.info(f"Applying to first job from {len(jobs)} found...")
                self.apply_to_job(driver, jobs[0])

            logger.info("Application process completed!")
            return True

        except Exception as e:
            logger.error(f"Error in automation: {e}")
            return False

        finally:
            if driver:
                input("Press Enter to close browser...")
                driver.quit()

    def apply_to_specific_job(self, driver):
        """Apply to a specific job when navigated directly"""
        try:
            wait = WebDriverWait(driver, 10)

            # Look for apply button on job detail page
            apply_xpath = "//button[contains(text(), 'Apply')] | //a[contains(text(), 'Apply')] | //button[contains(text(), 'Bewerben')] | //a[contains(text(), 'Bewerben')]"

            try:
                apply_button = wait.until(EC.element_to_be_clickable((By.XPATH, apply_xpath)))
                logger.info("Found apply button for specific job")

                driver.execute_script("arguments[0].click();", apply_button)
                time.sleep(3)

                # Fill application form
                self.fill_application_form(driver)

                # Don't auto-submit, let user review
                self.submit_application(driver)

            except TimeoutException:
                logger.warning("Could not find apply button on job page")

        except Exception as e:
            logger.error(f"Error applying to specific job: {e}")

def main():
    """Main function"""
    print("🚀 Nemetschek Application Automation")
    print("=" * 40)

    automator = NemetschekJobApplicationAutomator()

    print("Starting browser automation...")
    print("This will:")
    print("1. Navigate to Nemetschek careers")
    print("2. Search for DevOps/Cloud jobs")
    print("3. Fill out application form")
    print("4. Stop before submission for your review")
    print("\nMake sure you have:")
    print("- Generated resume PDF in current directory")
    print("- Reviewed candidate information")
    print("\nStarting in 3 seconds...")

    time.sleep(3)

    success = automator.automate_nemetschek_application()

    if success:
        print("✅ Automation completed successfully!")
    else:
        print("❌ Automation encountered errors")

if __name__ == "__main__":
    main()