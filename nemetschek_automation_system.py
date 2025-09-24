#!/usr/bin/env python3
"""
Complete Automation System for Nemetschek Job Applications
Integrates with the dynamic resume generator and automates the entire application process
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
from selenium.common.exceptions import TimeoutException, NoSuchElementException

# Import our dynamic resume generator
from nemetschek_dynamic_resume_generator import DynamicResumeGenerator

class NemetschekApplicationAutomation:
    def __init__(self, headless: bool = False):
        self.logger = logging.getLogger(__name__)
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )

        self.headless = headless
        self.driver = None
        self.wait = None
        self.resume_generator = DynamicResumeGenerator()

        # Application data
        self.personal_data = {
            "first_name": "Jiale",
            "last_name": "Lin",
            "email": "jeremykalilin@gmail.com",
            "phone": "+1-510-417-5834",
            "address": "Santa Clara, CA",
            "linkedin": "https://www.linkedin.com/in/jiale-lin-ab03a4149",
            "website": "https://ljluestc.github.io",
            "work_authorization": "US Citizen",
            "experience_years": "5",
            "current_location": "Santa Clara, CA, United States"
        }

        # Setup directories
        self.output_dir = "nemetschek_applications"
        os.makedirs(self.output_dir, exist_ok=True)
        os.makedirs(f"{self.output_dir}/resumes", exist_ok=True)
        os.makedirs(f"{self.output_dir}/cover_letters", exist_ok=True)

    def setup_driver(self):
        """Setup Chrome WebDriver with appropriate options"""
        chrome_options = Options()

        if self.headless:
            chrome_options.add_argument("--headless")

        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")

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
            self.wait = WebDriverWait(self.driver, 20)
            self.logger.info("WebDriver setup successfully")
            return True
        except Exception as e:
            self.logger.error(f"Failed to setup WebDriver: {e}")
            return False

    def navigate_to_careers_page(self):
        """Navigate to Nemetschek careers page"""
        try:
            url = "https://career55.sapsf.eu/careers?company=nemetschek"
            self.logger.info(f"Navigating to: {url}")
            self.driver.get(url)

            # Wait for page to load
            self.wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
            time.sleep(3)  # Allow dynamic content to load

            self.logger.info("Successfully navigated to careers page")
            return True

        except Exception as e:
            self.logger.error(f"Failed to navigate to careers page: {e}")
            return False

    def search_for_jobs(self, keywords: List[str] = None, location: str = None) -> List[Dict[str, Any]]:
        """Search for relevant jobs on the careers page"""
        jobs = []

        try:
            # Look for search functionality
            search_selectors = [
                "input[placeholder*='keyword']",
                "input[placeholder*='search']",
                "input[name*='search']",
                ".search-input",
                "#searchKeyword"
            ]

            search_input = None
            for selector in search_selectors:
                try:
                    search_input = self.driver.find_element(By.CSS_SELECTOR, selector)
                    if search_input.is_displayed():
                        break
                except NoSuchElementException:
                    continue

            if search_input and keywords:
                search_term = " ".join(keywords)
                search_input.clear()
                search_input.send_keys(search_term)

                # Look for search button
                search_btn_selectors = [
                    "button[type='submit']",
                    ".search-button",
                    "input[type='submit']",
                    ".btn-search"
                ]

                for selector in search_btn_selectors:
                    try:
                        search_btn = self.driver.find_element(By.CSS_SELECTOR, selector)
                        if search_btn.is_displayed():
                            search_btn.click()
                            break
                    except NoSuchElementException:
                        continue

                time.sleep(3)  # Wait for search results

            # Extract job listings
            job_selectors = [
                ".job-item",
                ".job-listing",
                ".position",
                ".vacancy",
                "[data-job-id]",
                ".job-card"
            ]

            job_elements = []
            for selector in job_selectors:
                try:
                    job_elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    if job_elements:
                        break
                except NoSuchElementException:
                    continue

            if not job_elements:
                # Try to find any links that might be job listings
                job_elements = self.driver.find_elements(By.CSS_SELECTOR, "a[href*='job'], a[href*='position'], a[href*='career']")

            for element in job_elements[:10]:  # Limit to first 10 jobs
                try:
                    job_data = self.extract_job_data(element)
                    if job_data:
                        jobs.append(job_data)
                except Exception as e:
                    self.logger.warning(f"Failed to extract job data: {e}")
                    continue

            self.logger.info(f"Found {len(jobs)} jobs")
            return jobs

        except Exception as e:
            self.logger.error(f"Failed to search for jobs: {e}")
            return jobs

    def extract_job_data(self, element) -> Optional[Dict[str, Any]]:
        """Extract job data from a job listing element"""
        try:
            job_data = {
                "title": "",
                "location": "",
                "department": "",
                "job_id": "",
                "link": "",
                "description": "",
                "requirements": ""
            }

            # Extract title
            title_selectors = [
                ".job-title", ".title", "h2", "h3", ".position-title"
            ]

            for selector in title_selectors:
                try:
                    title_elem = element.find_element(By.CSS_SELECTOR, selector)
                    job_data["title"] = title_elem.text.strip()
                    break
                except NoSuchElementException:
                    continue

            # Extract location
            location_selectors = [
                ".location", ".job-location", "[data-location]"
            ]

            for selector in location_selectors:
                try:
                    location_elem = element.find_element(By.CSS_SELECTOR, selector)
                    job_data["location"] = location_elem.text.strip()
                    break
                except NoSuchElementException:
                    continue

            # Extract link
            try:
                link_elem = element if element.tag_name == "a" else element.find_element(By.CSS_SELECTOR, "a")
                job_data["link"] = link_elem.get_attribute("href")
            except NoSuchElementException:
                pass

            # Only return if we have at least a title and link
            if job_data["title"] and job_data["link"]:
                return job_data

            return None

        except Exception as e:
            self.logger.warning(f"Failed to extract job data: {e}")
            return None

    def get_job_details(self, job: Dict[str, Any]) -> Dict[str, Any]:
        """Get detailed job information by visiting the job page"""
        try:
            if not job.get("link"):
                return job

            self.logger.info(f"Getting details for job: {job['title']}")

            # Open job in new tab
            self.driver.execute_script("window.open('');")
            self.driver.switch_to.window(self.driver.window_handles[1])

            self.driver.get(job["link"])
            time.sleep(3)

            # Extract job description
            description_selectors = [
                ".job-description",
                ".description",
                ".job-details",
                ".job-content",
                "[data-description]"
            ]

            for selector in description_selectors:
                try:
                    desc_elem = self.driver.find_element(By.CSS_SELECTOR, selector)
                    job["description"] = desc_elem.text.strip()
                    break
                except NoSuchElementException:
                    continue

            # If no specific description found, get all text content
            if not job.get("description"):
                try:
                    body = self.driver.find_element(By.TAG_NAME, "body")
                    job["description"] = body.text[:2000]  # Limit length
                except:
                    pass

            # Close the tab and switch back
            self.driver.close()
            self.driver.switch_to.window(self.driver.window_handles[0])

            return job

        except Exception as e:
            self.logger.error(f"Failed to get job details: {e}")
            # Make sure we're back on the main window
            try:
                if len(self.driver.window_handles) > 1:
                    self.driver.close()
                    self.driver.switch_to.window(self.driver.window_handles[0])
            except:
                pass
            return job

    def generate_tailored_documents(self, job: Dict[str, Any]) -> Dict[str, str]:
        """Generate tailored resume and cover letter for a specific job"""
        try:
            job_title = job.get("title", "Software Engineer")
            company = "Nemetschek"
            job_description = job.get("description", "")

            # Analyze job requirements
            job_requirements = self.resume_generator.analyze_job_requirements(job_description)

            # Generate LaTeX resume
            latex_resume = self.resume_generator.generate_latex_resume(
                job_title, company, job_requirements
            )

            # Generate cover letter
            cover_letter = self.resume_generator.generate_cover_letter(
                job_title, company, job_requirements
            )

            # Save files
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            safe_title = "".join(c for c in job_title if c.isalnum() or c in (' ', '-', '_')).rstrip()
            safe_title = safe_title.replace(' ', '_')

            # Save LaTeX resume
            resume_filename = f"Jiale_Lin_Resume_{company}_{safe_title}_{timestamp}.tex"
            resume_path = os.path.join(self.output_dir, "resumes", resume_filename)

            with open(resume_path, 'w', encoding='utf-8') as f:
                f.write(latex_resume)

            # Save cover letter
            cover_filename = f"Jiale_Lin_Cover_Letter_{company}_{safe_title}_{timestamp}.txt"
            cover_path = os.path.join(self.output_dir, "cover_letters", cover_filename)

            with open(cover_path, 'w', encoding='utf-8') as f:
                f.write(cover_letter)

            # Try to compile LaTeX to PDF
            pdf_path = self.compile_latex_to_pdf(resume_path)

            self.logger.info(f"Generated documents for {job_title}")

            return {
                "resume_tex": resume_path,
                "resume_pdf": pdf_path,
                "cover_letter": cover_path,
                "job_requirements": job_requirements
            }

        except Exception as e:
            self.logger.error(f"Failed to generate tailored documents: {e}")
            return {}

    def compile_latex_to_pdf(self, tex_path: str) -> Optional[str]:
        """Compile LaTeX file to PDF"""
        try:
            # Check if pdflatex is available
            result = subprocess.run(["which", "pdflatex"], capture_output=True, text=True)
            if result.returncode != 0:
                self.logger.warning("pdflatex not found, skipping PDF generation")
                return None

            # Compile LaTeX
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
            else:
                self.logger.warning(f"LaTeX compilation failed: {result.stderr}")

            return None

        except Exception as e:
            self.logger.error(f"Failed to compile LaTeX: {e}")
            return None

    def apply_to_job(self, job: Dict[str, Any], documents: Dict[str, str]) -> bool:
        """Apply to a specific job"""
        try:
            if not job.get("link"):
                self.logger.error("No job link available")
                return False

            self.logger.info(f"Applying to job: {job['title']}")

            # Navigate to job application page
            self.driver.get(job["link"])
            time.sleep(3)

            # Look for apply button
            apply_selectors = [
                "button[id*='apply']",
                "a[id*='apply']",
                ".apply-button",
                ".btn-apply",
                "button:contains('Apply')",
                "a:contains('Apply')"
            ]

            apply_button = None
            for selector in apply_selectors:
                try:
                    apply_button = self.driver.find_element(By.CSS_SELECTOR, selector)
                    if apply_button.is_displayed():
                        break
                except NoSuchElementException:
                    continue

            if not apply_button:
                # Try to find any button or link with "apply" in text
                all_buttons = self.driver.find_elements(By.CSS_SELECTOR, "button, a")
                for btn in all_buttons:
                    if "apply" in btn.text.lower():
                        apply_button = btn
                        break

            if apply_button:
                apply_button.click()
                time.sleep(3)

                # Fill out application form
                success = self.fill_application_form(documents)
                return success
            else:
                self.logger.warning("Could not find apply button")
                return False

        except Exception as e:
            self.logger.error(f"Failed to apply to job: {e}")
            return False

    def fill_application_form(self, documents: Dict[str, str]) -> bool:
        """Fill out the job application form"""
        try:
            # Wait for form to load
            time.sleep(3)

            # Common form field mappings
            field_mappings = {
                "first_name": ["firstName", "first-name", "fname", "givenName"],
                "last_name": ["lastName", "last-name", "lname", "familyName"],
                "email": ["email", "emailAddress", "e-mail"],
                "phone": ["phone", "phoneNumber", "mobile", "telephone"],
                "address": ["address", "location", "city"],
                "linkedin": ["linkedin", "linkedIn", "socialProfile"],
                "website": ["website", "portfolio", "personalWebsite"]
            }

            # Fill personal information
            for field_key, field_names in field_mappings.items():
                if field_key in self.personal_data:
                    self.fill_form_field(field_names, self.personal_data[field_key])

            # Handle file uploads
            self.handle_file_uploads(documents)

            # Handle dropdowns and checkboxes
            self.handle_form_widgets()

            # Look for submit button (but don't click it automatically)
            submit_selectors = [
                "button[type='submit']",
                "input[type='submit']",
                ".submit-button",
                ".btn-submit",
                "button:contains('Submit')"
            ]

            submit_button = None
            for selector in submit_selectors:
                try:
                    submit_button = self.driver.find_element(By.CSS_SELECTOR, selector)
                    if submit_button.is_displayed():
                        break
                except NoSuchElementException:
                    continue

            if submit_button:
                self.logger.info("Application form filled. Submit button found but not clicked.")
                # You can uncomment the next line to actually submit
                # submit_button.click()
                return True
            else:
                self.logger.warning("Could not find submit button")
                return False

        except Exception as e:
            self.logger.error(f"Failed to fill application form: {e}")
            return False

    def fill_form_field(self, field_names: List[str], value: str):
        """Fill a form field by trying various selectors"""
        for field_name in field_names:
            selectors = [
                f"input[name='{field_name}']",
                f"input[id='{field_name}']",
                f"input[placeholder*='{field_name}']",
                f"textarea[name='{field_name}']",
                f"textarea[id='{field_name}']"
            ]

            for selector in selectors:
                try:
                    element = self.driver.find_element(By.CSS_SELECTOR, selector)
                    if element.is_displayed() and element.is_enabled():
                        element.clear()
                        element.send_keys(value)
                        self.logger.debug(f"Filled field {field_name} with value {value}")
                        return
                except NoSuchElementException:
                    continue

    def handle_file_uploads(self, documents: Dict[str, str]):
        """Handle file upload fields"""
        file_upload_selectors = [
            "input[type='file']",
            ".file-upload",
            ".upload-input"
        ]

        for selector in file_upload_selectors:
            try:
                upload_elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                for upload_elem in upload_elements:
                    if upload_elem.is_displayed():
                        # Determine what type of file to upload based on context
                        parent_text = upload_elem.find_element(By.XPATH, "..").text.lower()

                        if any(word in parent_text for word in ["resume", "cv", "curriculum"]):
                            if documents.get("resume_pdf"):
                                upload_elem.send_keys(documents["resume_pdf"])
                                self.logger.info("Uploaded resume PDF")
                        elif any(word in parent_text for word in ["cover", "letter", "motivation"]):
                            if documents.get("cover_letter"):
                                upload_elem.send_keys(documents["cover_letter"])
                                self.logger.info("Uploaded cover letter")
                        else:
                            # Default to resume
                            if documents.get("resume_pdf"):
                                upload_elem.send_keys(documents["resume_pdf"])
                                self.logger.info("Uploaded resume PDF (default)")

                        time.sleep(2)  # Wait for upload

            except Exception as e:
                self.logger.warning(f"Failed to handle file upload: {e}")

    def handle_form_widgets(self):
        """Handle dropdowns, checkboxes, and other form widgets"""
        try:
            # Handle work authorization dropdowns
            auth_selectors = [
                "select[name*='authorization']",
                "select[name*='eligible']",
                "select[name*='visa']",
                "select[name*='status']"
            ]

            for selector in auth_selectors:
                try:
                    select_elem = self.driver.find_element(By.CSS_SELECTOR, selector)
                    if select_elem.is_displayed():
                        select = Select(select_elem)

                        # Try to select US citizen/authorized options
                        options_text = [opt.text.lower() for opt in select.options]

                        for option_text in options_text:
                            if any(term in option_text for term in ["citizen", "authorized", "yes", "eligible"]):
                                for opt in select.options:
                                    if opt.text.lower() == option_text:
                                        select.select_by_visible_text(opt.text)
                                        self.logger.info(f"Selected work authorization: {opt.text}")
                                        break
                                break
                except NoSuchElementException:
                    continue

            # Handle experience level dropdowns
            exp_selectors = [
                "select[name*='experience']",
                "select[name*='years']"
            ]

            for selector in exp_selectors:
                try:
                    select_elem = self.driver.find_element(By.CSS_SELECTOR, selector)
                    if select_elem.is_displayed():
                        select = Select(select_elem)

                        # Try to select appropriate experience level
                        options_text = [opt.text for opt in select.options]

                        for option_text in options_text:
                            if any(term in option_text for term in ["5", "5+", "3-5", "senior"]):
                                select.select_by_visible_text(option_text)
                                self.logger.info(f"Selected experience level: {option_text}")
                                break
                except NoSuchElementException:
                    continue

        except Exception as e:
            self.logger.warning(f"Failed to handle form widgets: {e}")

    def save_application_results(self, results: List[Dict[str, Any]]):
        """Save application results to JSON file"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            results_file = os.path.join(self.output_dir, f"application_results_{timestamp}.json")

            with open(results_file, 'w', encoding='utf-8') as f:
                json.dump(results, indent=2, fp=f, ensure_ascii=False)

            self.logger.info(f"Saved application results to: {results_file}")

        except Exception as e:
            self.logger.error(f"Failed to save application results: {e}")

    def run_automation(self, job_keywords: List[str] = None, max_applications: int = 5) -> List[Dict[str, Any]]:
        """Run the complete automation workflow"""
        results = []

        try:
            if not self.setup_driver():
                return results

            if not self.navigate_to_careers_page():
                return results

            # Search for jobs
            jobs = self.search_for_jobs(job_keywords or ["software engineer", "developer", "devops"])

            if not jobs:
                self.logger.warning("No jobs found")
                return results

            # Process each job
            processed_count = 0
            for job in jobs:
                if processed_count >= max_applications:
                    break

                try:
                    # Get detailed job information
                    detailed_job = self.get_job_details(job)

                    # Generate tailored documents
                    documents = self.generate_tailored_documents(detailed_job)

                    if not documents:
                        self.logger.warning(f"Failed to generate documents for {job['title']}")
                        continue

                    # Apply to job (currently just fills form without submitting)
                    application_success = self.apply_to_job(detailed_job, documents)

                    result = {
                        "job": detailed_job,
                        "documents": documents,
                        "application_success": application_success,
                        "timestamp": datetime.now().isoformat()
                    }

                    results.append(result)
                    processed_count += 1

                    self.logger.info(f"Processed job {processed_count}/{min(len(jobs), max_applications)}: {job['title']}")

                    # Brief pause between applications
                    time.sleep(5)

                except Exception as e:
                    self.logger.error(f"Failed to process job {job['title']}: {e}")
                    continue

            # Save results
            self.save_application_results(results)

            return results

        except Exception as e:
            self.logger.error(f"Automation failed: {e}")
            return results

        finally:
            if self.driver:
                self.driver.quit()

    def cleanup(self):
        """Cleanup resources"""
        if self.driver:
            self.driver.quit()

def main():
    """Main function to run the automation"""
    automation = NemetschekApplicationAutomation(headless=False)  # Set to True for headless mode

    try:
        # Run automation for specific job types
        job_keywords = [
            "software engineer",
            "senior software engineer",
            "devops engineer",
            "full stack developer",
            "backend engineer",
            "cloud engineer"
        ]

        results = automation.run_automation(
            job_keywords=job_keywords,
            max_applications=3  # Limit for testing
        )

        print(f"\nAutomation completed. Processed {len(results)} job applications.")

        for i, result in enumerate(results, 1):
            job = result['job']
            print(f"\n{i}. {job['title']} at {job.get('location', 'N/A')}")
            print(f"   Application Success: {result['application_success']}")
            print(f"   Documents Generated: {bool(result['documents'])}")

        return results

    except KeyboardInterrupt:
        print("\nAutomation interrupted by user")
        return []
    except Exception as e:
        print(f"Automation failed: {e}")
        return []
    finally:
        automation.cleanup()

if __name__ == "__main__":
    main()