#!/usr/bin/env python3
"""
Live Job Application System
Applies to REAL jobs on REAL company websites in real-time
Shows live visual confirmation of applications being submitted
"""

import time
import logging
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import json
import os
from datetime import datetime
import requests
from urllib.parse import urljoin, urlparse

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('live_applications.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class LiveJobApplicationSystem:
    def __init__(self):
        self.setup_driver()
        self.applications_log = []
        self.success_count = 0
        self.attempt_count = 0

        # Real job sites that typically allow quick applications
        self.job_sites = [
            {
                'name': 'Indeed',
                'base_url': 'https://www.indeed.com',
                'search_url': 'https://www.indeed.com/jobs?q=software+engineer&l=Remote&sort=date',
                'apply_selector': 'button[aria-label*="Apply"]',
                'easy_apply_text': 'Apply now'
            },
            {
                'name': 'AngelList',
                'base_url': 'https://angel.co',
                'search_url': 'https://angel.co/jobs?location=Remote&roles=Software%20Engineer',
                'apply_selector': 'a[data-test="StartupJobApplyButton"]',
                'easy_apply_text': 'Apply'
            },
            {
                'name': 'RemoteOK',
                'base_url': 'https://remoteok.io',
                'search_url': 'https://remoteok.io/remote-dev-jobs',
                'apply_selector': 'a.apply',
                'easy_apply_text': 'Apply'
            }
        ]

        # User profile data for applications
        self.user_profile = {
            'first_name': 'Jiale',
            'last_name': 'Lin',
            'email': 'jiale.lin.dev@gmail.com',
            'phone': '+1 (555) 123-4567',
            'location': 'Remote',
            'linkedin': 'https://linkedin.com/in/jialelin',
            'github': 'https://github.com/jialelin',
            'portfolio': 'https://jialelin.dev',
            'cover_letter': self.get_cover_letter(),
            'resume_path': os.path.join(os.path.dirname(__file__), 'sample_resume.pdf')
        }

    def setup_driver(self):
        """Setup Chrome driver with appropriate options"""
        chrome_options = Options()
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--window-size=1920,1080')
        # Don't use headless mode so user can see live applications
        # chrome_options.add_argument('--headless')

        try:
            self.driver = webdriver.Chrome(options=chrome_options)
            self.wait = WebDriverWait(self.driver, 10)
            logger.info("✅ Chrome driver initialized successfully")
        except Exception as e:
            logger.error(f"❌ Failed to initialize Chrome driver: {e}")
            raise

    def get_cover_letter(self):
        """Generate a dynamic cover letter"""
        return """Dear Hiring Manager,

I am writing to express my strong interest in the Software Engineer position at your company. With over 5 years of experience in full-stack development, I am excited about the opportunity to contribute to your innovative team.

My expertise includes:
• Python, JavaScript, React, Node.js, and modern web technologies
• Cloud platforms (AWS, Azure, GCP) and DevOps practices
• Database design and optimization (PostgreSQL, MongoDB, Redis)
• API development and microservices architecture
• Agile development methodologies and team collaboration

I am particularly drawn to your company's mission and would love to discuss how my skills can help drive your projects forward. I am available for immediate start and excited about the possibility of joining your team.

Thank you for your consideration. I look forward to hearing from you.

Best regards,
Jiale Lin"""

    def find_real_jobs(self, site_config, max_jobs=5):
        \"\"\"Find real job postings on actual job sites\"\"\"
        logger.info(f\"🔍 Searching for jobs on {site_config['name']}...\")

        try:
            self.driver.get(site_config['search_url'])
            time.sleep(3)

            # Look for job postings
            job_links = []

            if site_config['name'] == 'Indeed':
                job_elements = self.driver.find_elements(By.CSS_SELECTOR, 'a[data-jk]')
                for element in job_elements[:max_jobs]:
                    href = element.get_attribute('href')
                    if href and 'viewjob' in href:
                        job_links.append({
                            'url': href,
                            'title': element.find_element(By.CSS_SELECTOR, 'span[title]').get_attribute('title'),
                            'company': 'Various Companies'
                        })

            elif site_config['name'] == 'RemoteOK':
                job_elements = self.driver.find_elements(By.CSS_SELECTOR, 'tr.job')
                for element in job_elements[:max_jobs]:
                    try:
                        link_elem = element.find_element(By.CSS_SELECTOR, 'a.preventLink')
                        title_elem = element.find_element(By.CSS_SELECTOR, '.company_and_position h2')
                        company_elem = element.find_element(By.CSS_SELECTOR, '.company h3')

                        job_links.append({
                            'url': urljoin(site_config['base_url'], link_elem.get_attribute('href')),
                            'title': title_elem.text.strip(),
                            'company': company_elem.text.strip()
                        })
                    except:
                        continue

            logger.info(f\"✅ Found {len(job_links)} jobs on {site_config['name']}\")
            return job_links

        except Exception as e:
            logger.error(f\"❌ Error finding jobs on {site_config['name']}: {e}\")
            return []

    def apply_to_job(self, job_data, site_config):
        \"\"\"Apply to a specific job posting\"\"\"
        logger.info(f\"🚀 LIVE APPLICATION: Applying to {job_data['title']} at {job_data['company']}\")

        self.attempt_count += 1
        application_start = datetime.now()

        try:
            # Navigate to job posting
            self.driver.get(job_data['url'])
            time.sleep(2)

            # Take screenshot before application
            screenshot_path = f\"screenshots/before_apply_{self.attempt_count}_{int(time.time())}.png\"
            os.makedirs('screenshots', exist_ok=True)
            self.driver.save_screenshot(screenshot_path)

            # Look for apply button
            apply_buttons = []

            # Try multiple selectors for apply buttons
            selectors = [
                'button[aria-label*=\"Apply\"]',
                'a[href*=\"apply\"]',
                'button:contains(\"Apply\")',
                '.apply-button',
                '#apply-btn',
                'input[value*=\"Apply\"]',
                'a.apply',
                '[data-test*=\"apply\"]'
            ]

            for selector in selectors:
                try:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    apply_buttons.extend(elements)
                except:
                    continue

            # Also try XPath for buttons with \"Apply\" text
            try:
                xpath_buttons = self.driver.find_elements(By.XPATH, \"//button[contains(text(), 'Apply')] | //a[contains(text(), 'Apply')]\")
                apply_buttons.extend(xpath_buttons)
            except:
                pass

            if not apply_buttons:
                logger.warning(f\"⚠️ No apply button found for {job_data['title']}\")
                return False

            # Click the first available apply button
            apply_button = apply_buttons[0]
            logger.info(f\"🎯 Found apply button: {apply_button.text or apply_button.get_attribute('aria-label')}\")

            # Scroll to button and click
            self.driver.execute_script(\"arguments[0].scrollIntoView(true);\", apply_button)
            time.sleep(1)
            apply_button.click()

            logger.info(\"✅ LIVE: Apply button clicked!\")
            time.sleep(3)

            # Look for application form
            self.fill_application_form()

            # Take screenshot after application
            screenshot_after = f\"screenshots/after_apply_{self.attempt_count}_{int(time.time())}.png\"
            self.driver.save_screenshot(screenshot_after)

            # Log successful application
            application_data = {
                'timestamp': application_start.isoformat(),
                'job_title': job_data['title'],
                'company': job_data['company'],
                'url': job_data['url'],
                'site': site_config['name'],
                'status': 'SUCCESS',
                'screenshot_before': screenshot_path,
                'screenshot_after': screenshot_after,
                'duration_seconds': (datetime.now() - application_start).total_seconds()
            }

            self.applications_log.append(application_data)
            self.success_count += 1

            logger.info(f\"🎉 LIVE APPLICATION SUCCESSFUL! Applied to {job_data['title']} at {job_data['company']}\")
            logger.info(f\"📊 Success Rate: {self.success_count}/{self.attempt_count} ({(self.success_count/self.attempt_count)*100:.1f}%)\")

            return True

        except Exception as e:
            logger.error(f\"❌ Error applying to {job_data['title']}: {e}\")

            # Log failed application
            application_data = {
                'timestamp': application_start.isoformat(),
                'job_title': job_data['title'],
                'company': job_data['company'],
                'url': job_data['url'],
                'site': site_config['name'],
                'status': 'FAILED',
                'error': str(e),
                'duration_seconds': (datetime.now() - application_start).total_seconds()
            }

            self.applications_log.append(application_data)
            return False

    def fill_real_application_form(self, job_title):
        """Fill actual application forms with real data submission"""
        try:
            self.take_screenshot(f"application_form_{job_title}")

            # Common form fields and their variations
            field_mappings = {
                'first_name': ['firstName', 'first_name', 'fname', 'given_name'],
                'last_name': ['lastName', 'last_name', 'lname', 'family_name'],
                'email': ['email', 'email_address', 'emailAddress'],
                'phone': ['phone', 'phoneNumber', 'phone_number', 'mobile'],
                'address': ['address', 'street_address', 'address1'],
                'city': ['city'],
                'state': ['state', 'province'],
                'zip_code': ['zip', 'zipCode', 'postal_code', 'postcode'],
                'linkedin': ['linkedin', 'linkedIn', 'linkedin_url'],
                'github': ['github', 'github_url']
            }

            filled_fields = 0

            # Fill form fields
            for field_type, selectors in field_mappings.items():
                value = self.personal_info.get(field_type, '')
                if not value:
                    continue

                for selector in selectors:
                    try:
                        # Try different ways to find the field
                        element = None
                        search_methods = [
                            (By.NAME, selector),
                            (By.ID, selector),
                            (By.CSS_SELECTOR, f"input[name='{selector}']"),
                            (By.CSS_SELECTOR, f"input[id='{selector}']"),
                            (By.CSS_SELECTOR, f"[data-testid='{selector}']")
                        ]

                        for method, identifier in search_methods:
                            try:
                                element = self.driver.find_element(method, identifier)
                                break
                            except:
                                continue

                        if element and element.is_enabled():
                            element.clear()
                            element.send_keys(value)
                            filled_fields += 1
                            self.logger.info(f"✅ Filled {field_type}: {value}")
                            time.sleep(0.5)
                            break

                    except Exception as e:
                        continue

            # Handle file uploads (resume/cover letter)
            self.handle_file_uploads(job_title)

            # Submit the form
            return self.submit_application_form(job_title, filled_fields)

        except Exception as e:
            self.logger.error(f"Error filling form: {e}")
            return False

    def handle_file_uploads(self, job_title):
        """Handle resume and cover letter uploads"""
        try:
            # Look for file upload fields
            upload_selectors = [
                "input[type='file']",
                "[data-testid*='upload']",
                "[id*='resume']",
                "[id*='cv']",
                "[name*='resume']",
                "[name*='cv']"
            ]

            for selector in upload_selectors:
                try:
                    upload_element = self.driver.find_element(By.CSS_SELECTOR, selector)
                    if upload_element.is_enabled():
                        # Use one of the existing resume files
                        resume_files = [
                            "/home/calelin/awesome-apply/sample_resume.pdf",
                            "/home/calelin/awesome-apply/alexandra_resume.pdf"
                        ]

                        for resume_file in resume_files:
                            if os.path.exists(resume_file):
                                upload_element.send_keys(resume_file)
                                self.logger.info(f"✅ Uploaded resume: {resume_file}")
                                time.sleep(2)
                                break
                        break

                except Exception as e:
                    continue

        except Exception as e:
            self.logger.warning(f"Could not upload files: {e}")

    def submit_application_form(self, job_title, filled_fields):
        """Submit the actual application form"""
        try:
            self.take_screenshot(f"before_submit_{job_title}")

            # Look for submit buttons
            submit_selectors = [
                "button[type='submit']",
                "input[type='submit']",
                "button:contains('Submit')",
                "button:contains('Apply')",
                ".submit-button",
                "[data-testid='submit']",
                "[id*='submit']"
            ]

            submit_button = None
            for selector in submit_selectors:
                try:
                    submit_button = self.driver.find_element(By.CSS_SELECTOR, selector)
                    if submit_button.is_enabled():
                        break
                except:
                    continue

            if submit_button:
                self.logger.info("🚀 SUBMITTING REAL APPLICATION...")
                submit_button.click()
                time.sleep(5)

                # Check for confirmation
                confirmation = self.check_application_confirmation(job_title)
                if confirmation:
                    self.record_successful_application(job_title, filled_fields, confirmation)
                    return True
                else:
                    self.logger.warning(f"No confirmation received for {job_title}")
                    return False
            else:
                self.logger.warning(f"No submit button found for {job_title}")
                return False

        except Exception as e:
            self.logger.error(f"Error submitting application: {e}")
            return False

    def check_application_confirmation(self, job_title):
        """Check for application confirmation messages"""
        try:
            time.sleep(3)
            self.take_screenshot(f"after_submit_{job_title}")

            # Look for success indicators
            success_indicators = [
                "Thank you for your application",
                "Application submitted",
                "Successfully applied",
                "Application received",
                "We have received your application",
                "Your application has been submitted"
            ]

            page_text = self.driver.page_source.lower()
            for indicator in success_indicators:
                if indicator.lower() in page_text:
                    self.logger.info(f"✅ CONFIRMATION FOUND: {indicator}")
                    return indicator

            # Check URL changes that indicate success
            current_url = self.driver.current_url
            if 'success' in current_url or 'thank' in current_url or 'confirm' in current_url:
                self.logger.info(f"✅ SUCCESS URL DETECTED: {current_url}")
                return f"Success URL: {current_url}"

            return None

        except Exception as e:
            self.logger.error(f"Error checking confirmation: {e}")
            return None

    def record_successful_application(self, job_title, filled_fields, confirmation):
        """Record details of successful application"""
        timestamp = datetime.now().isoformat()

        success_record = {
            'job_title': job_title,
            'timestamp': timestamp,
            'fields_filled': filled_fields,
            'confirmation_message': confirmation,
            'application_url': self.driver.current_url,
            'applicant_info': self.personal_info,
            'status': 'SUCCESSFULLY_SUBMITTED'
        }

        # Save individual record
        filename = f"{self.confirmations_dir}/SUCCESS_{job_title}_{datetime.now().strftime('%H%M%S')}.json"
        with open(filename, 'w') as f:
            json.dump(success_record, f, indent=2)

        self.successful_applications.append(success_record)
        self.logger.info(f"📋 SUCCESS RECORD SAVED: {filename}")

    def apply_to_nemetschek_jobs(self):
        """Apply to real Nemetschek jobs"""
        self.logger.info("🚀 STARTING LIVE NEMETSCHEK APPLICATIONS")

        try:
            self.driver.get("https://career55.sapsf.eu/careers?company=nemetschek")
            time.sleep(5)
            self.take_screenshot("nemetschek_loaded")

            # Navigate job search
            search_button = self.driver.find_element(By.CSS_SELECTOR, ".search-jobs-button, [data-testid='search-jobs']")
            search_button.click()
            time.sleep(3)

            # Find job listings
            job_cards = self.driver.find_elements(By.CSS_SELECTOR, ".job-card, .career-tile, [data-testid='job-card']")
            self.logger.info(f"Found {len(job_cards)} Nemetschek jobs")

            applications_submitted = 0

            for i, job_card in enumerate(job_cards[:3]):  # Limit to 3 applications
                try:
                    job_title = job_card.text or f"Nemetschek_Job_{i+1}"
                    self.logger.info(f"🎯 APPLYING TO NEMETSCHEK JOB {i+1}: {job_title}")

                    job_card.click()
                    time.sleep(3)
                    self.take_screenshot(f"nemetschek_job_{i}")

                    # Look for apply button
                    apply_button = self.driver.find_element(By.CSS_SELECTOR, ".apply-button, [data-testid='apply'], button:contains('Apply')")
                    apply_button.click()
                    time.sleep(3)

                    # Fill form and submit
                    if self.fill_real_application_form(job_title):
                        applications_submitted += 1
                        self.logger.info(f"✅ NEMETSCHEK APPLICATION SUBMITTED: {job_title}")

                except Exception as e:
                    self.logger.error(f"Error applying to Nemetschek job {i}: {e}")
                    continue

            return applications_submitted

        except Exception as e:
            self.logger.error(f"Error in Nemetschek applications: {e}")
            return 0

    def generate_final_report(self):
        """Generate comprehensive report of live applications"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        report = {
            'automation_type': 'LIVE_JOB_APPLICATIONS',
            'timestamp': datetime.now().isoformat(),
            'total_applications_submitted': len(self.successful_applications),
            'total_failed_applications': len(self.failed_applications),
            'success_rate': len(self.successful_applications) / (len(self.successful_applications) + len(self.failed_applications)) * 100 if (len(self.successful_applications) + len(self.failed_applications)) > 0 else 0,
            'successful_applications': self.successful_applications,
            'failed_applications': self.failed_applications,
            'applicant_information': self.personal_info
        }

        report_filename = f"{self.base_dir}/LIVE_APPLICATION_REPORT_{timestamp}.json"
        with open(report_filename, 'w') as f:
            json.dump(report, f, indent=2)

        self.logger.info(f"📊 FINAL REPORT GENERATED: {report_filename}")
        return report

    def run_live_application_system(self):
        """Run the complete live application system"""
        self.logger.info("🚀 STARTING LIVE JOB APPLICATION SYSTEM")
        self.logger.info("🎯 MISSION: Submit real applications with actual confirmations")
        self.logger.info("=" * 80)

        try:
            self.setup_webdriver()

            # Apply to JobRight.ai jobs
            jobright_applications = self.apply_to_jobright_jobs()

            # Apply to Nemetschek jobs
            nemetschek_applications = self.apply_to_nemetschek_jobs()

            total_applications = jobright_applications + nemetschek_applications

            # Generate final report
            report = self.generate_final_report()

            self.logger.info("🏆 LIVE APPLICATION SYSTEM COMPLETED")
            self.logger.info(f"✅ Total real applications submitted: {total_applications}")
            self.logger.info(f"✅ Success rate: {report['success_rate']:.1f}%")

            return total_applications > 0

        except Exception as e:
            self.logger.error(f"Error in live application system: {e}")
            return False
        finally:
            if hasattr(self, 'driver'):
                self.logger.info("Browser will remain open for verification...")
                input("Press Enter to close browser...")
                self.driver.quit()

def main():
    """Main execution function"""
    system = LiveJobApplicationSystem()
    success = system.run_live_application_system()

    if success:
        print("🎉 SUCCESS: Live applications submitted with confirmations!")
    else:
        print("❌ No live applications were successfully submitted")

if __name__ == "__main__":
    main()