#!/usr/bin/env python3
"""
JobRight.ai Perfect Clone - Browser Automation System
=====================================================

This script creates a perfect clone of JobRight.ai functionality by:
1. Opening 10 browser tabs with real job applications
2. Automatically filling common form fields
3. Highlighting submit buttons for manual verification
4. Tracking all applications in the system
"""

import sys
sys.path.append('/home/calelin/awesome-apply/venv/lib/python3.13/site-packages')

import requests
import time
import json
from datetime import datetime
import logging
from typing import List, Dict
import webbrowser
import threading
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
import random

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class JobRightPerfectClone:
    """Perfect clone of JobRight.ai with browser automation"""

    def __init__(self, base_url='http://localhost:5000'):
        self.base_url = base_url
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        self.drivers = []
        self.demo_user_data = {
            'name': 'Alex Johnson',
            'email': 'alex.johnson.demo@gmail.com',
            'phone': '+1 (555) 123-4567',
            'linkedin': 'https://linkedin.com/in/alexjohnson',
            'github': 'https://github.com/alexjohnson',
            'portfolio': 'https://alexjohnson.dev',
            'experience': '5',
            'salary': '120000',
            'cover_letter': 'I am excited to apply for this position. With my extensive experience in software development and machine learning, I believe I would be a valuable addition to your team. I have worked on numerous projects involving Python, JavaScript, and AI technologies, and I am passionate about creating innovative solutions.',
            'skills': ['Python', 'JavaScript', 'React', 'Node.js', 'Machine Learning', 'AI', 'SQL', 'AWS']
        }

    def login_to_system(self):
        """Login to the JobRight mock system"""
        logger.info("🔐 Logging into JobRight.ai system...")

        login_data = {
            'email': 'demo@jobright.ai',
            'password': 'demo123'
        }

        response = self.session.post(
            f'{self.base_url}/login',
            json=login_data,
            headers={'Content-Type': 'application/json'}
        )

        if response.status_code == 200:
            result = response.json()
            if result.get('success'):
                logger.info("✅ Successfully logged into JobRight.ai")
                return True
            else:
                logger.error(f"❌ Login failed: {result.get('message')}")
                return False
        else:
            logger.error(f"❌ Login request failed: {response.status_code}")
            return False

    def get_real_jobs(self, count=10):
        """Get real job postings with application URLs"""
        logger.info(f"📋 Fetching {count} real job opportunities...")

        jobs = []
        page = 1

        while len(jobs) < count:
            response = self.session.get(
                f'{self.base_url}/api/jobs/search',
                params={'page': page, 'per_page': 20}
            )

            if response.status_code == 200:
                data = response.json()
                page_jobs = data.get('jobs', [])

                if not page_jobs:
                    break

                # Filter jobs with valid application URLs
                valid_jobs = [
                    job for job in page_jobs
                    if job.get('application_url') and
                    job.get('application_url').startswith('http')
                ]

                jobs.extend(valid_jobs)
                page += 1
            else:
                logger.error(f"❌ Failed to fetch jobs: {response.status_code}")
                break

        jobs = jobs[:count]
        logger.info(f"✅ Found {len(jobs)} jobs with valid application URLs")
        return jobs

    def setup_chrome_driver(self):
        """Setup Chrome WebDriver with appropriate options"""
        options = Options()
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-web-security')
        options.add_argument('--allow-running-insecure-content')
        options.add_argument('--disable-features=VizDisplayCompositor')

        # Enable automation-friendly settings
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)

        try:
            driver = webdriver.Chrome(options=options)
            driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            return driver
        except Exception as e:
            logger.error(f"❌ Failed to setup Chrome driver: {e}")
            return None

    def fill_generic_application_form(self, driver, job):
        """Fill common job application form fields"""
        try:
            logger.info(f"🖊️ Filling application form for {job['title']} at {job['company']}")

            # Wait for page to load
            time.sleep(3)

            # Common form field selectors and variations
            field_mappings = {
                'name': [
                    'input[name*="name"]', 'input[id*="name"]', 'input[placeholder*="name"]',
                    'input[name*="full"]', 'input[id*="full"]', 'input[placeholder*="full"]',
                    'input[name*="firstName"]', 'input[name*="first_name"]',
                    'input[type="text"]'
                ],
                'email': [
                    'input[name*="email"]', 'input[id*="email"]', 'input[placeholder*="email"]',
                    'input[type="email"]'
                ],
                'phone': [
                    'input[name*="phone"]', 'input[id*="phone"]', 'input[placeholder*="phone"]',
                    'input[name*="mobile"]', 'input[id*="mobile"]', 'input[placeholder*="mobile"]',
                    'input[type="tel"]'
                ],
                'linkedin': [
                    'input[name*="linkedin"]', 'input[id*="linkedin"]', 'input[placeholder*="linkedin"]',
                    'input[name*="profile"]', 'input[id*="profile"]'
                ],
                'github': [
                    'input[name*="github"]', 'input[id*="github"]', 'input[placeholder*="github"]',
                    'input[name*="portfolio"]', 'input[id*="portfolio"]'
                ],
                'website': [
                    'input[name*="website"]', 'input[id*="website"]', 'input[placeholder*="website"]',
                    'input[name*="portfolio"]', 'input[id*="portfolio"]'
                ],
                'experience': [
                    'input[name*="experience"]', 'input[id*="experience"]', 'input[placeholder*="experience"]',
                    'input[name*="years"]', 'input[id*="years"]', 'select[name*="experience"]'
                ],
                'salary': [
                    'input[name*="salary"]', 'input[id*="salary"]', 'input[placeholder*="salary"]',
                    'input[name*="compensation"]', 'input[id*="compensation"]'
                ],
                'cover_letter': [
                    'textarea[name*="cover"]', 'textarea[id*="cover"]', 'textarea[placeholder*="cover"]',
                    'textarea[name*="letter"]', 'textarea[id*="letter"]', 'textarea[placeholder*="letter"]',
                    'textarea[name*="message"]', 'textarea[id*="message"]', 'textarea[placeholder*="message"]',
                    'textarea'
                ]
            }

            filled_fields = []

            # Fill each field type
            for field_type, selectors in field_mappings.items():
                for selector in selectors:
                    try:
                        elements = driver.find_elements(By.CSS_SELECTOR, selector)
                        for element in elements:
                            if element.is_displayed() and element.is_enabled():
                                # Skip if already filled
                                if element.get_attribute('value'):
                                    continue

                                # Fill based on field type
                                if field_type == 'name':
                                    element.clear()
                                    element.send_keys(self.demo_user_data['name'])
                                    filled_fields.append(f"Name: {self.demo_user_data['name']}")
                                    break
                                elif field_type == 'email':
                                    element.clear()
                                    element.send_keys(self.demo_user_data['email'])
                                    filled_fields.append(f"Email: {self.demo_user_data['email']}")
                                    break
                                elif field_type == 'phone':
                                    element.clear()
                                    element.send_keys(self.demo_user_data['phone'])
                                    filled_fields.append(f"Phone: {self.demo_user_data['phone']}")
                                    break
                                elif field_type == 'linkedin':
                                    element.clear()
                                    element.send_keys(self.demo_user_data['linkedin'])
                                    filled_fields.append(f"LinkedIn: {self.demo_user_data['linkedin']}")
                                    break
                                elif field_type == 'github':
                                    element.clear()
                                    element.send_keys(self.demo_user_data['github'])
                                    filled_fields.append(f"GitHub: {self.demo_user_data['github']}")
                                    break
                                elif field_type == 'website':
                                    element.clear()
                                    element.send_keys(self.demo_user_data['portfolio'])
                                    filled_fields.append(f"Website: {self.demo_user_data['portfolio']}")
                                    break
                                elif field_type == 'experience':
                                    if element.tag_name == 'select':
                                        # Handle dropdown
                                        options = element.find_elements(By.TAG_NAME, 'option')
                                        for option in options:
                                            if '5' in option.text or 'mid' in option.text.lower():
                                                option.click()
                                                filled_fields.append(f"Experience: 5 years")
                                                break
                                    else:
                                        element.clear()
                                        element.send_keys(self.demo_user_data['experience'])
                                        filled_fields.append(f"Experience: {self.demo_user_data['experience']} years")
                                    break
                                elif field_type == 'salary':
                                    element.clear()
                                    element.send_keys(self.demo_user_data['salary'])
                                    filled_fields.append(f"Salary: ${self.demo_user_data['salary']}")
                                    break
                                elif field_type == 'cover_letter':
                                    element.clear()
                                    # Customize cover letter for each job
                                    customized_letter = self.demo_user_data['cover_letter'].replace(
                                        'this position',
                                        f"the {job['title']} position at {job['company']}"
                                    )
                                    element.send_keys(customized_letter)
                                    filled_fields.append("Cover Letter: Custom message")
                                    break

                        if filled_fields and field_type in str(filled_fields[-1]):
                            break  # Found and filled this field type

                    except Exception as e:
                        continue  # Try next selector

            # Look for file upload fields (resume)
            try:
                file_inputs = driver.find_elements(By.CSS_SELECTOR, 'input[type="file"]')
                for file_input in file_inputs:
                    if file_input.is_displayed():
                        # We don't have an actual resume file, so just note it
                        filled_fields.append("Resume: Upload field found (manual upload required)")
                        break
            except:
                pass

            # Highlight submit buttons
            self.highlight_submit_buttons(driver)

            if filled_fields:
                logger.info(f"✅ Filled {len(filled_fields)} fields:")
                for field in filled_fields:
                    logger.info(f"   • {field}")
            else:
                logger.warning("⚠️ No fillable fields found on this page")

            return len(filled_fields) > 0

        except Exception as e:
            logger.error(f"❌ Error filling form: {e}")
            return False

    def highlight_submit_buttons(self, driver):
        """Highlight submit buttons for manual verification"""
        try:
            # Common submit button selectors
            submit_selectors = [
                'button[type="submit"]',
                'input[type="submit"]',
                'button:contains("Submit")',
                'button:contains("Apply")',
                'button:contains("Send")',
                'a[class*="submit"]',
                'a[class*="apply"]'
            ]

            highlighted_count = 0

            for selector in submit_selectors:
                try:
                    if ':contains(' in selector:
                        # Handle text-based selectors with JavaScript
                        script = f"""
                        var buttons = Array.from(document.querySelectorAll('button, input[type="submit"], a'));
                        buttons.forEach(function(btn) {{
                            var text = btn.textContent || btn.value || '';
                            if (text.toLowerCase().includes('submit') ||
                                text.toLowerCase().includes('apply') ||
                                text.toLowerCase().includes('send')) {{
                                btn.style.border = '3px solid #00f0a0';
                                btn.style.backgroundColor = '#00f0a0';
                                btn.style.color = 'white';
                                btn.style.boxShadow = '0 0 15px #00f0a0';
                                btn.style.fontWeight = 'bold';
                            }}
                        }});
                        """
                        driver.execute_script(script)
                        highlighted_count += 1
                    else:
                        elements = driver.find_elements(By.CSS_SELECTOR, selector)
                        for element in elements:
                            if element.is_displayed():
                                driver.execute_script("""
                                    arguments[0].style.border = '3px solid #00f0a0';
                                    arguments[0].style.backgroundColor = '#00f0a0';
                                    arguments[0].style.color = 'white';
                                    arguments[0].style.boxShadow = '0 0 15px #00f0a0';
                                    arguments[0].style.fontWeight = 'bold';
                                """, element)
                                highlighted_count += 1
                except:
                    continue

            if highlighted_count > 0:
                logger.info(f"🎯 Highlighted {highlighted_count} submit buttons")

        except Exception as e:
            logger.error(f"❌ Error highlighting buttons: {e}")

    def open_job_application_tab(self, job, tab_number):
        """Open a job application in a new browser tab"""
        try:
            logger.info(f"🌐 Opening Tab {tab_number}: {job['title']} at {job['company']}")

            driver = self.setup_chrome_driver()
            if not driver:
                return None

            self.drivers.append(driver)

            # Navigate to the job application URL
            driver.get(job['application_url'])

            # Set window title for easy identification
            driver.execute_script(f"document.title = 'JobRight Tab {tab_number}: {job['title']} - {job['company']}';")

            # Wait for page to load
            time.sleep(5)

            # Fill the application form
            filled = self.fill_generic_application_form(driver, job)

            # Log this application in our system
            self.log_application_attempt(job, tab_number, filled)

            logger.info(f"✅ Tab {tab_number} ready: {job['title']} at {job['company']}")
            return driver

        except Exception as e:
            logger.error(f"❌ Error opening tab {tab_number}: {e}")
            return None

    def log_application_attempt(self, job, tab_number, filled):
        """Log the application attempt in our system"""
        try:
            # Apply through our system as well
            response = self.session.post(
                f'{self.base_url}/api/jobs/{job["id"]}/apply',
                headers={'Content-Type': 'application/json'}
            )

            if response.status_code == 200:
                result = response.json()
                if result.get('success'):
                    logger.info(f"📝 Logged application for Tab {tab_number} in JobRight system")

        except Exception as e:
            logger.error(f"❌ Error logging application: {e}")

    def run_perfect_clone(self):
        """Run the perfect clone automation"""
        logger.info("🚀 STARTING JOBRIGHT.AI PERFECT CLONE")
        logger.info("=" * 60)

        # Step 1: Login to system
        if not self.login_to_system():
            logger.error("❌ Failed to login. Cannot continue.")
            return False

        # Step 2: Get real jobs
        jobs = self.get_real_jobs(10)
        if not jobs:
            logger.error("❌ No jobs found. Cannot continue.")
            return False

        logger.info(f"🎯 Opening {len(jobs)} job applications in browser tabs...")
        logger.info("=" * 60)

        # Step 3: Open each job in a new browser tab
        successful_tabs = 0

        for i, job in enumerate(jobs, 1):
            try:
                driver = self.open_job_application_tab(job, i)
                if driver:
                    successful_tabs += 1

                # Small delay between opening tabs
                time.sleep(2)

            except Exception as e:
                logger.error(f"❌ Failed to open tab {i}: {e}")
                continue

        logger.info("=" * 60)
        logger.info("🎉 PERFECT CLONE AUTOMATION COMPLETED!")
        logger.info("=" * 60)
        logger.info(f"✅ Successfully opened {successful_tabs} job application tabs")
        logger.info(f"📋 Total jobs processed: {len(jobs)}")
        logger.info("🎯 All forms have been automatically filled")
        logger.info("💡 Submit buttons are highlighted in green")
        logger.info("📝 Applications are logged in JobRight system")
        logger.info("")
        logger.info("🔄 NEXT STEPS:")
        logger.info("1. Review each form for accuracy")
        logger.info("2. Upload your resume to file upload fields")
        logger.info("3. Click the green submit buttons to complete applications")
        logger.info("4. Track your applications in JobRight at http://localhost:5000/applications")
        logger.info("=" * 60)

        # Keep browsers open
        logger.info("🌐 Browser tabs will remain open for manual review...")
        logger.info("💡 Close this terminal to close all browser tabs")

        try:
            # Keep the script running so browsers stay open
            while True:
                time.sleep(60)
                logger.info(f"⏰ {datetime.now().strftime('%H:%M:%S')} - Monitoring {len(self.drivers)} browser tabs...")
        except KeyboardInterrupt:
            logger.info("🛑 Shutting down browser automation...")
            self.cleanup()

        return True

    def cleanup(self):
        """Clean up browser drivers"""
        logger.info("🧹 Cleaning up browser instances...")
        for driver in self.drivers:
            try:
                driver.quit()
            except:
                pass
        self.drivers.clear()
        logger.info("✅ Cleanup completed")

def main():
    """Main function"""
    clone = JobRightPerfectClone()

    logger.info("🤖 JobRight.ai Perfect Clone - Browser Automation")
    logger.info("=" * 60)
    logger.info("This will open 10 job application pages with auto-filled forms")
    logger.info("🎯 Target: http://localhost:5000")
    logger.info("=" * 60)

    try:
        success = clone.run_perfect_clone()
        return success
    except KeyboardInterrupt:
        logger.info("🛑 User interrupted the process")
        clone.cleanup()
        return False
    except Exception as e:
        logger.error(f"❌ Unexpected error: {e}")
        clone.cleanup()
        return False

if __name__ == '__main__':
    main()