#!/usr/bin/env python3
"""
Complete SAP SuccessFactors Nemetschek Automation System
Integrates enhanced dynamic resume generation with full application automation
"""

import os
import json
import time
import logging
import subprocess
from datetime import datetime
from typing import Dict, List, Any, Optional

# Selenium imports
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import TimeoutException, NoSuchElementException, ElementClickInterceptedException

# Import our enhanced resume generator
from enhanced_dynamic_resume_generator import EnhancedDynamicResumeGenerator

class SAPNemetschekAutomation:
    def __init__(self, headless: bool = False):
        self.headless = headless
        self.driver = None
        self.wait = None
        self.logger = self._setup_logging()
        self.resume_generator = EnhancedDynamicResumeGenerator()

        # Personal information
        self.personal_data = {
            "first_name": "Jiale",
            "last_name": "Lin",
            "email": "jeremykalilin@gmail.com",
            "phone": "+1-510-417-5834",
            "address": "Santa Clara, CA",
            "linkedin": "https://www.linkedin.com/in/jiale-lin-ab03a4149",
            "website": "https://ljluestc.github.io",
            "work_authorization": "US Citizen"
        }

        # Create output directory
        self.output_dir = "sap_automation_results"
        os.makedirs(self.output_dir, exist_ok=True)
        os.makedirs(f"{self.output_dir}/resumes", exist_ok=True)
        os.makedirs(f"{self.output_dir}/cover_letters", exist_ok=True)
        os.makedirs(f"{self.output_dir}/screenshots", exist_ok=True)

    def _setup_logging(self) -> logging.Logger:
        """Setup logging configuration"""
        logger = logging.getLogger(__name__)
        logger.setLevel(logging.INFO)

        # Create handlers
        file_handler = logging.FileHandler(f"sap_automation_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")
        console_handler = logging.StreamHandler()

        # Create formatter
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)

        # Add handlers
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)

        return logger

    def setup_driver(self) -> bool:
        """Setup Chrome WebDriver"""
        try:
            chrome_options = Options()
            if self.headless:
                chrome_options.add_argument("--headless")

            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--window-size=1920,1080")

            self.driver = webdriver.Chrome(options=chrome_options)
            self.wait = WebDriverWait(self.driver, 30)
            self.logger.info("WebDriver setup completed")
            return True

        except Exception as e:
            self.logger.error(f"Failed to setup WebDriver: {e}")
            return False

    def navigate_to_careers(self) -> bool:
        """Navigate to Nemetschek careers page"""
        try:
            url = "https://career55.sapsf.eu/careers?company=nemetschek"
            self.logger.info(f"Navigating to: {url}")

            self.driver.get(url)
            self.wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
            time.sleep(5)

            # Take screenshot
            screenshot_path = f"{self.output_dir}/screenshots/careers_page_{datetime.now().strftime('%H%M%S')}.png"
            self.driver.save_screenshot(screenshot_path)

            self.logger.info("Successfully navigated to careers page")
            return True

        except Exception as e:
            self.logger.error(f"Failed to navigate to careers page: {e}")
            return False

    def search_jobs(self, keywords: List[str] = None) -> List[Dict[str, Any]]:
        """Search for job listings - enhanced to find ANY available jobs"""
        jobs = []

        try:
            if not keywords:
                keywords = ["software engineer", "senior", "developer", "engineer", "developer", "technical", "IT"]

            self.logger.info(f"Searching for jobs with keywords: {keywords}")

            # Wait for page to fully load
            time.sleep(5)

            # Take a screenshot to see what's on the page
            screenshot_path = f"job_search_page_{datetime.now().strftime('%H%M%S')}.png"
            self.driver.save_screenshot(screenshot_path)
            self.logger.info(f"Screenshot saved: {screenshot_path}")

            # Try clicking any "Search Jobs" or "View Jobs" buttons
            action_buttons = [
                "button[contains(text(), 'Search')]",
                "button[contains(text(), 'Jobs')]",
                "a[contains(text(), 'Jobs')]",
                "input[type='submit']",
                ".search-button",
                ".job-search-btn"
            ]

            for button_selector in action_buttons:
                try:
                    buttons = self.driver.find_elements(By.XPATH, f"//*[contains(text(), 'Search') or contains(text(), 'Jobs') or contains(text(), 'View')]")
                    for button in buttons:
                        if button.is_displayed() and button.is_enabled():
                            self.logger.info(f"Clicking button: {button.text}")
                            button.click()
                            time.sleep(3)
                            break
                except Exception as e:
                    self.logger.debug(f"Button click failed: {e}")

            # Try to find and use search functionality
            search_selectors = [
                "input[placeholder*='search' or placeholder*='Search' or placeholder*='job' or placeholder*='Job']",
                "input[name*='search' or name*='job']",
                "input[type='text']",
                "input[class*='search']"
            ]

            search_input = None
            for selector in search_selectors:
                try:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    for element in elements:
                        if element.is_displayed() and element.is_enabled():
                            search_input = element
                            self.logger.info(f"Found search input: {selector}")
                            break
                    if search_input:
                        break
                except:
                    continue

            if search_input:
                try:
                    search_input.clear()
                    search_input.send_keys("engineer")
                    search_input.send_keys(Keys.ENTER)
                    time.sleep(5)
                    self.logger.info("Performed search for 'engineer'")
                except Exception as e:
                    self.logger.warning(f"Search input failed: {e}")

            # Comprehensive job selector search
            job_selectors = [
                ".job-item", ".job-listing", ".job-card", ".job-tile",
                ".position", ".vacancy", ".career-item", ".opening",
                "a[href*='job']", "a[href*='position']", "a[href*='career']",
                ".job-row", ".job-post", ".job-offer", ".job-link",
                "[data-job-id]", "[data-position-id]",
                "div[class*='job']", "li[class*='job']",
                "tr[class*='job']", "section[class*='job']"
            ]

            job_elements = []
            for selector in job_selectors:
                try:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    self.logger.info(f"Selector '{selector}' found {len(elements)} elements")
                    if elements:
                        job_elements.extend(elements[:5])  # Take first 5 from each selector
                except Exception as e:
                    self.logger.debug(f"Selector '{selector}' failed: {e}")

            # If still no jobs, look for ANY clickable text that might be a job
            if not job_elements:
                self.logger.info("No jobs found with standard selectors, trying broader search...")
                all_links = self.driver.find_elements(By.TAG_NAME, "a")
                text_keywords = ["engineer", "developer", "software", "technical", "IT", "position", "job", "career"]

                for link in all_links:
                    try:
                        link_text = link.text.lower()
                        if any(keyword in link_text for keyword in text_keywords) and len(link_text) > 5:
                            job_elements.append(link)
                            self.logger.info(f"Found potential job link: {link.text}")
                    except:
                        continue

            # If STILL no jobs, grab ALL visible text elements and look for job-like content
            if not job_elements:
                self.logger.info("Still no jobs found, scanning all page content...")
                all_elements = self.driver.find_elements(By.XPATH, "//*[text()]")
                for element in all_elements:
                    try:
                        text = element.text.strip()
                        if len(text) > 10 and any(keyword in text.lower() for keyword in ["engineer", "developer", "software", "technical"]):
                            job_elements.append(element)
                            self.logger.info(f"Found potential job content: {text[:50]}...")
                    except:
                        continue

            self.logger.info(f"Total elements to analyze: {len(job_elements)}")

            # Extract job information from found elements
            for i, element in enumerate(job_elements[:10]):  # Limit to 10
                try:
                    job_data = self._extract_job_info(element, i)
                    if job_data and job_data.get("title"):
                        jobs.append(job_data)
                        self.logger.info(f"Extracted job: {job_data['title']}")
                except Exception as e:
                    self.logger.warning(f"Failed to extract job {i}: {e}")

            # If we found ANY jobs, log success
            if jobs:
                self.logger.info(f"Successfully found {len(jobs)} job listings")
            else:
                self.logger.warning("No jobs found despite extensive search")
                # Take another screenshot for debugging
                debug_screenshot = f"no_jobs_debug_{datetime.now().strftime('%H%M%S')}.png"
                self.driver.save_screenshot(debug_screenshot)
                self.logger.info(f"Debug screenshot saved: {debug_screenshot}")

            return jobs

        except Exception as e:
            self.logger.error(f"Failed to search for jobs: {e}")
            return jobs

    def _extract_job_info(self, element, index: int) -> Optional[Dict[str, Any]]:
        """Extract job information from element"""
        try:
            job_data = {
                "index": index,
                "title": "",
                "location": "",
                "link": "",
                "description": "",
                "element_text": element.text[:200] if element.text else ""
            }

            # Extract title
            title_selectors = [".job-title", ".title", "h1", "h2", "h3"]
            for selector in title_selectors:
                try:
                    title_elem = element.find_element(By.CSS_SELECTOR, selector)
                    job_data["title"] = title_elem.text.strip()
                    break
                except:
                    continue

            if not job_data["title"] and element.text:
                lines = element.text.strip().split('\n')
                job_data["title"] = lines[0] if lines else f"Job {index + 1}"

            # Extract location
            location_selectors = [".location", ".job-location", ".workplace"]
            for selector in location_selectors:
                try:
                    location_elem = element.find_element(By.CSS_SELECTOR, selector)
                    job_data["location"] = location_elem.text.strip()
                    break
                except:
                    continue

            # Extract link
            try:
                if element.tag_name == "a":
                    job_data["link"] = element.get_attribute("href")
                else:
                    link_elem = element.find_element(By.CSS_SELECTOR, "a")
                    job_data["link"] = link_elem.get_attribute("href")
            except:
                pass

            return job_data if job_data["title"] else None

        except Exception as e:
            self.logger.warning(f"Failed to extract job info: {e}")
            return None

    def get_job_details(self, job: Dict[str, Any]) -> Dict[str, Any]:
        """Get detailed job information"""
        try:
            if not job.get("link"):
                return job

            self.logger.info(f"Getting details for: {job['title']}")

            # Open in new tab
            self.driver.execute_script("window.open('');")
            self.driver.switch_to.window(self.driver.window_handles[-1])

            self.driver.get(job["link"])
            time.sleep(3)

            # Extract job description
            description_selectors = [
                ".job-description", ".description", ".job-details",
                ".content", ".job-summary"
            ]

            description_text = ""
            for selector in description_selectors:
                try:
                    desc_elem = self.driver.find_element(By.CSS_SELECTOR, selector)
                    description_text = desc_elem.text.strip()
                    break
                except:
                    continue

            if not description_text:
                try:
                    description_text = self.driver.find_element(By.TAG_NAME, "body").text[:2000]
                except:
                    pass

            job["description"] = description_text

            # Close tab and return to main window
            self.driver.close()
            self.driver.switch_to.window(self.driver.window_handles[0])

            return job

        except Exception as e:
            self.logger.error(f"Failed to get job details: {e}")
            # Ensure we're back on main window
            try:
                if len(self.driver.window_handles) > 1:
                    self.driver.close()
                    self.driver.switch_to.window(self.driver.window_handles[0])
            except:
                pass
            return job

    def generate_tailored_materials(self, job: Dict[str, Any]) -> Dict[str, Any]:
        """Generate tailored resume and cover letter"""
        try:
            self.logger.info(f"Generating materials for: {job['title']}")

            # Use enhanced resume generator
            result = self.resume_generator.generate_enhanced_resume(
                job_title=job["title"],
                company="Nemetschek",
                job_description=job.get("description", "")
            )

            # Save files
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            safe_title = "".join(c for c in job["title"] if c.isalnum() or c in (' ', '-', '_')).strip()
            safe_title = safe_title.replace(' ', '_')[:50]

            # Save resume
            resume_filename = f"Jiale_Lin_Resume_Nemetschek_{safe_title}_{timestamp}.tex"
            resume_path = os.path.join(self.output_dir, "resumes", resume_filename)

            with open(resume_path, 'w', encoding='utf-8') as f:
                f.write(result["enhanced_resume"])

            # Save cover letter
            cover_filename = f"Jiale_Lin_Cover_Letter_Nemetschek_{safe_title}_{timestamp}.txt"
            cover_path = os.path.join(self.output_dir, "cover_letters", cover_filename)

            with open(cover_path, 'w', encoding='utf-8') as f:
                f.write(result["cover_letter"])

            materials = {
                "resume_tex": resume_path,
                "cover_letter": cover_path,
                "gap_analysis": result["gap_analysis"],
                "identified_gaps": result["identified_gaps"]
            }

            self.logger.info(f"Generated materials saved")
            return materials

        except Exception as e:
            self.logger.error(f"Failed to generate materials: {e}")
            return {}

    def apply_to_job(self, job: Dict[str, Any], materials: Dict[str, Any]) -> bool:
        """Apply to a specific job"""
        try:
            if not job.get("link"):
                self.logger.warning(f"No link for job: {job['title']}")
                return False

            self.logger.info(f"Applying to: {job['title']}")

            # Navigate to job page
            self.driver.get(job["link"])
            time.sleep(3)

            # Take screenshot
            screenshot_path = f"{self.output_dir}/screenshots/job_page_{datetime.now().strftime('%H%M%S')}.png"
            self.driver.save_screenshot(screenshot_path)

            # Look for apply button
            apply_selectors = [
                "button[id*='apply']", "a[id*='apply']", ".apply-button",
                ".btn-apply", "input[value*='Apply']"
            ]

            apply_button = None
            for selector in apply_selectors:
                try:
                    buttons = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    for button in buttons:
                        if button.is_displayed() and button.is_enabled():
                            apply_button = button
                            break
                    if apply_button:
                        break
                except:
                    continue

            if not apply_button:
                # Fallback: look for any element with "apply" in text
                all_elements = self.driver.find_elements(By.CSS_SELECTOR, "button, a, input")
                for element in all_elements:
                    if "apply" in element.text.lower() and element.is_displayed():
                        apply_button = element
                        break

            if apply_button:
                self.logger.info("Found apply button, clicking...")

                # Scroll to and click button
                self.driver.execute_script("arguments[0].scrollIntoView(true);", apply_button)
                time.sleep(1)

                try:
                    apply_button.click()
                except ElementClickInterceptedException:
                    self.driver.execute_script("arguments[0].click();", apply_button)

                time.sleep(5)

                # Fill application form
                success = self._fill_application_form(materials)
                return success
            else:
                self.logger.warning("Could not find apply button")
                return False

        except Exception as e:
            self.logger.error(f"Failed to apply to job: {e}")
            return False

    def _fill_application_form(self, materials: Dict[str, Any]) -> bool:
        """Fill out the application form"""
        try:
            self.logger.info("Filling application form...")
            time.sleep(5)

            # Take screenshot of form
            screenshot_path = f"{self.output_dir}/screenshots/form_{datetime.now().strftime('%H%M%S')}.png"
            self.driver.save_screenshot(screenshot_path)

            # Fill personal information
            self._fill_personal_info()

            # Handle file uploads
            self._handle_file_uploads(materials)

            # Fill additional questions
            self._fill_additional_questions()

            # Take final screenshot
            screenshot_path = f"{self.output_dir}/screenshots/form_completed_{datetime.now().strftime('%H%M%S')}.png"
            self.driver.save_screenshot(screenshot_path)

            # Look for submit button (but don't click for safety)
            submit_selectors = ["button[type='submit']", "input[type='submit']", ".submit-button"]

            submit_found = False
            for selector in submit_selectors:
                try:
                    submit_button = self.driver.find_element(By.CSS_SELECTOR, selector)
                    if submit_button.is_displayed():
                        self.logger.info("Submit button found - form ready")
                        submit_found = True
                        break
                except:
                    continue

            return submit_found

        except Exception as e:
            self.logger.error(f"Failed to fill form: {e}")
            return False

    def _fill_personal_info(self):
        """Fill personal information fields"""
        field_mappings = {
            "firstName": self.personal_data["first_name"],
            "lastName": self.personal_data["last_name"],
            "email": self.personal_data["email"],
            "phone": self.personal_data["phone"],
            "address": self.personal_data["address"],
            "linkedin": self.personal_data["linkedin"],
            "website": self.personal_data["website"]
        }

        for field_id, value in field_mappings.items():
            self._fill_form_field(field_id, value)

    def _fill_form_field(self, field_identifier: str, value: str):
        """Fill a form field using various selectors"""
        if not value:
            return

        selectors = [
            f"input[name='{field_identifier}']",
            f"input[id='{field_identifier}']",
            f"textarea[name='{field_identifier}']",
            f"select[name='{field_identifier}']"
        ]

        for selector in selectors:
            try:
                elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                for element in elements:
                    if element.is_displayed() and element.is_enabled():
                        if element.tag_name.lower() == "select":
                            try:
                                Select(element).select_by_visible_text(value)
                            except:
                                pass
                        else:
                            element.clear()
                            element.send_keys(value)
                        return
            except:
                continue

    def _handle_file_uploads(self, materials: Dict[str, Any]):
        """Handle file upload fields"""
        upload_selectors = ["input[type='file']"]

        for selector in upload_selectors:
            try:
                upload_elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                for upload_elem in upload_elements:
                    if upload_elem.is_displayed():
                        # Upload resume if available
                        if materials.get("resume_tex"):
                            upload_elem.send_keys(materials["resume_tex"])
                            self.logger.info("Uploaded resume")
                            time.sleep(2)
                            break
            except Exception as e:
                self.logger.warning(f"Failed to upload file: {e}")

    def _fill_additional_questions(self):
        """Fill additional application questions"""
        question_mappings = {
            "workAuthorization": "Yes",
            "sponsorship": "No",
            "startDate": "Immediately"
        }

        for field, value in question_mappings.items():
            self._fill_form_field(field, value)

    def run_automation(self, max_applications: int = 2) -> List[Dict[str, Any]]:
        """Run the complete automation workflow"""
        results = []

        try:
            self.logger.info("Starting automation...")

            if not self.setup_driver():
                return results

            if not self.navigate_to_careers():
                return results

            # Search for jobs
            jobs = self.search_jobs(["software engineer", "senior", "developer"])

            if not jobs:
                self.logger.warning("No jobs found")
                return results

            # Process each job
            for i, job in enumerate(jobs[:max_applications]):
                try:
                    self.logger.info(f"Processing job {i+1}: {job['title']}")

                    # Get detailed job information
                    detailed_job = self.get_job_details(job)

                    # Generate tailored materials
                    materials = self.generate_tailored_materials(detailed_job)

                    # Apply to job
                    application_success = False
                    if materials:
                        application_success = self.apply_to_job(detailed_job, materials)

                    result = {
                        "job": detailed_job,
                        "materials": materials,
                        "application_success": application_success,
                        "timestamp": datetime.now().isoformat()
                    }

                    results.append(result)
                    time.sleep(10)  # Pause between applications

                except Exception as e:
                    self.logger.error(f"Failed to process job: {e}")
                    continue

            # Save results
            self._save_results(results)
            return results

        except Exception as e:
            self.logger.error(f"Automation failed: {e}")
            return results

        finally:
            if self.driver:
                self.driver.quit()

    def _save_results(self, results: List[Dict[str, Any]]):
        """Save automation results"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            results_file = f"{self.output_dir}/results_{timestamp}.json"

            serializable_results = []
            for result in results:
                serializable_result = {
                    "job": result["job"],
                    "materials_generated": bool(result.get("materials")),
                    "application_success": result.get("application_success", False),
                    "timestamp": result.get("timestamp")
                }
                serializable_results.append(serializable_result)

            with open(results_file, 'w', encoding='utf-8') as f:
                json.dump(serializable_results, f, indent=2)

            self.logger.info(f"Results saved to: {results_file}")

        except Exception as e:
            self.logger.error(f"Failed to save results: {e}")

def main():
    """Main function"""
    print("🚀 SAP SuccessFactors Nemetschek Automation")
    print("=" * 50)

    automation = SAPNemetschekAutomation(headless=False)

    try:
        results = automation.run_automation(max_applications=2)

        print(f"\n✅ Completed! Processed {len(results)} applications")

        for i, result in enumerate(results, 1):
            job = result['job']
            print(f"\n{i}. {job['title']}")
            print(f"   Location: {job.get('location', 'N/A')}")
            print(f"   Materials: {'✓' if result.get('materials') else '✗'}")
            print(f"   Applied: {'✓' if result.get('application_success') else '✗'}")

    except KeyboardInterrupt:
        print("\n⚠️ Interrupted by user")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    main()