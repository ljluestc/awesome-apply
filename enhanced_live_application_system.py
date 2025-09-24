#!/usr/bin/env python3
"""
ENHANCED LIVE JOB APPLICATION SYSTEM
===================================
Improved system with better form handling and real application confirmation
"""

import time
import json
import logging
import os
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import TimeoutException, NoSuchElementException, StaleElementReferenceException

class EnhancedLiveApplicationSystem:
    def __init__(self):
        self.setup_logging()
        self.setup_directories()
        self.personal_info = {
            'first_name': 'Jiale',
            'last_name': 'Lin',
            'full_name': 'Jiale Lin',
            'email': 'jiale.lin.x@gmail.com',
            'phone': '+1-857-294-1281',
            'address': '123 Tech Street',
            'city': 'Boston',
            'state': 'MA',
            'zip_code': '02101',
            'country': 'United States',
            'linkedin': 'https://linkedin.com/in/jiale-lin',
            'github': 'https://github.com/jiale-lin',
            'website': 'https://jiale-lin.dev',
            'cover_letter': 'I am excited to apply for this position. With my extensive background in software engineering and cloud technologies, I believe I would be a valuable addition to your team.',
            'why_interested': 'I am passionate about working with innovative technologies and contributing to impactful projects that make a difference.'
        }
        self.successful_applications = []
        self.confirmation_count = 0

    def setup_logging(self):
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('enhanced_live_applications.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)

    def setup_directories(self):
        self.base_dir = "enhanced_live_applications"
        self.screenshots_dir = f"{self.base_dir}/screenshots"
        self.confirmations_dir = f"{self.base_dir}/confirmations"

        for directory in [self.base_dir, self.screenshots_dir, self.confirmations_dir]:
            os.makedirs(directory, exist_ok=True)

    def setup_webdriver(self):
        self.logger.info("🚀 Setting up Enhanced WebDriver...")
        chrome_options = Options()
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        chrome_options.add_argument("--user-agent=Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")

        self.driver = webdriver.Chrome(options=chrome_options)
        self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        self.wait = WebDriverWait(self.driver, 20)
        self.actions = ActionChains(self.driver)
        self.logger.info("✅ Enhanced WebDriver ready")

    def take_screenshot(self, description):
        timestamp = datetime.now().strftime("%H%M%S")
        filename = f"{self.screenshots_dir}/{description}_{timestamp}.png"
        self.driver.save_screenshot(filename)
        self.logger.info(f"📸 Screenshot: {filename}")
        return filename

    def safe_click(self, element):
        """Safely click an element with multiple strategies"""
        try:
            # Strategy 1: Regular click
            if element.is_enabled() and element.is_displayed():
                element.click()
                return True
        except:
            pass

        try:
            # Strategy 2: JavaScript click
            self.driver.execute_script("arguments[0].click();", element)
            return True
        except:
            pass

        try:
            # Strategy 3: ActionChains click
            self.actions.move_to_element(element).click().perform()
            return True
        except:
            pass

        return False

    def safe_send_keys(self, element, text):
        """Safely send keys to an element"""
        try:
            element.clear()
            element.send_keys(text)
            return True
        except:
            try:
                self.driver.execute_script("arguments[0].value = arguments[1];", element, text)
                return True
            except:
                return False

    def find_and_apply_to_jobs(self):
        """Enhanced job application system"""
        self.logger.info("🎯 STARTING ENHANCED LIVE APPLICATION SYSTEM")
        self.logger.info("=" * 60)

        try:
            # Navigate to JobRight.ai
            self.driver.get("https://jobright.ai/jobs/recommend?pos=10")
            time.sleep(8)
            self.take_screenshot("jobright_homepage")

            # Handle any popups or overlays
            self.handle_popups()

            # Find job links more carefully
            job_links = self.extract_job_links()
            self.logger.info(f"Found {len(job_links)} job opportunities")

            if len(job_links) == 0:
                self.logger.warning("No job links found, trying alternative approach...")
                job_links = self.alternative_job_extraction()

            # Apply to jobs one by one
            for i, job_data in enumerate(job_links[:10]):  # Limit to 10 applications
                if self.apply_to_single_job(i, job_data):
                    self.confirmation_count += 1

                if self.confirmation_count >= 5:  # Stop after 5 successful applications
                    break

                time.sleep(3)  # Rate limiting

            return self.confirmation_count

        except Exception as e:
            self.logger.error(f"Error in application system: {e}")
            return self.confirmation_count

    def handle_popups(self):
        """Handle popups, modals, and overlays"""
        popup_selectors = [
            "[data-testid='close-modal']",
            ".modal-close",
            ".close-button",
            "[aria-label='Close']",
            "button:contains('Close')",
            "button:contains('Dismiss')",
            ".overlay-close"
        ]

        for selector in popup_selectors:
            try:
                popup = self.driver.find_element(By.CSS_SELECTOR, selector)
                if popup.is_displayed():
                    self.safe_click(popup)
                    time.sleep(1)
            except:
                continue

    def extract_job_links(self):
        """Extract job links with improved methods"""
        job_links = []

        # Multiple strategies to find job links
        selectors = [
            "a[href*='/jobs/info/']",
            "a[href*='/job/']",
            ".job-card a",
            ".job-listing a",
            "[data-testid*='job'] a",
            ".position-card a"
        ]

        for selector in selectors:
            try:
                elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                for elem in elements:
                    try:
                        url = elem.get_attribute('href')
                        title = elem.text.strip() or elem.get_attribute('title') or f"Job_{len(job_links)+1}"
                        if url and 'job' in url:
                            job_links.append({'url': url, 'title': title, 'element': elem})
                    except:
                        continue

                if job_links:
                    break
            except:
                continue

        return job_links

    def alternative_job_extraction(self):
        """Alternative method to extract jobs"""
        self.logger.info("Trying alternative job extraction...")

        # Scroll to load more content
        self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(3)

        # Look for any clickable elements that might be jobs
        clickable_elements = self.driver.find_elements(By.CSS_SELECTOR, "[role='button'], .clickable, [onclick]")

        job_candidates = []
        for elem in clickable_elements:
            try:
                text = elem.text.strip()
                if any(keyword in text.lower() for keyword in ['engineer', 'developer', 'analyst', 'manager', 'coordinator']):
                    job_candidates.append({'url': self.driver.current_url, 'title': text, 'element': elem})
            except:
                continue

        return job_candidates[:10]  # Limit to 10

    def apply_to_single_job(self, index, job_data):
        """Apply to a single job with enhanced error handling"""
        try:
            job_title = job_data['title']
            job_url = job_data.get('url', self.driver.current_url)

            self.logger.info(f"🎯 APPLICATION {index+1}: {job_title}")
            self.logger.info(f"URL: {job_url}")

            # Navigate to job if URL is different
            if job_url != self.driver.current_url:
                self.driver.get(job_url)
                time.sleep(5)
            else:
                # Click the job element
                if 'element' in job_data:
                    self.safe_click(job_data['element'])
                    time.sleep(3)

            self.take_screenshot(f"job_page_{index}")

            # Look for apply buttons with enhanced selectors
            apply_button = self.find_apply_button()

            if apply_button:
                self.logger.info("✅ Found apply button - proceeding...")
                if self.safe_click(apply_button):
                    time.sleep(5)
                    return self.complete_application(job_title, index)
                else:
                    self.logger.warning("Failed to click apply button")
            else:
                self.logger.warning("No apply button found")

            return False

        except Exception as e:
            self.logger.error(f"Error applying to job {index}: {e}")
            return False

    def find_apply_button(self):
        """Find apply button with comprehensive selectors"""
        apply_selectors = [
            "button[data-testid*='apply']",
            "a[data-testid*='apply']",
            "button:contains('Apply')",
            "a:contains('Apply')",
            "button:contains('Apply Now')",
            ".apply-button",
            ".apply-btn",
            "[id*='apply']",
            "[class*='apply']",
            "button[type='submit']",
            ".cta-button",
            ".primary-button"
        ]

        for selector in apply_selectors:
            try:
                elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                for element in elements:
                    if element.is_displayed() and element.is_enabled():
                        text = element.text.lower()
                        if 'apply' in text or 'submit' in text:
                            return element
            except:
                continue

        return None

    def complete_application(self, job_title, index):
        """Complete the application process"""
        try:
            self.take_screenshot(f"application_form_{index}")

            # Fill form fields
            filled_count = self.fill_application_form()

            # Submit application
            if self.submit_application():
                # Check for confirmation
                confirmation = self.check_confirmation()
                if confirmation:
                    self.record_success(job_title, index, confirmation)
                    return True

            return False

        except Exception as e:
            self.logger.error(f"Error completing application: {e}")
            return False

    def fill_application_form(self):
        """Fill application form with enhanced field detection"""
        filled_count = 0

        # Enhanced field mappings
        field_mappings = [
            (['first_name', 'firstName', 'fname', 'given_name', 'first-name'], self.personal_info['first_name']),
            (['last_name', 'lastName', 'lname', 'family_name', 'last-name'], self.personal_info['last_name']),
            (['full_name', 'fullName', 'name', 'applicant_name'], self.personal_info['full_name']),
            (['email', 'email_address', 'emailAddress', 'e_mail'], self.personal_info['email']),
            (['phone', 'phoneNumber', 'phone_number', 'mobile', 'telephone'], self.personal_info['phone']),
            (['address', 'street_address', 'address1', 'street'], self.personal_info['address']),
            (['city'], self.personal_info['city']),
            (['state', 'province'], self.personal_info['state']),
            (['zip', 'zipCode', 'postal_code', 'postcode'], self.personal_info['zip_code']),
            (['linkedin', 'linkedIn', 'linkedin_url'], self.personal_info['linkedin']),
            (['github', 'github_url'], self.personal_info['github']),
            (['cover_letter', 'coverLetter', 'message', 'additional_info'], self.personal_info['cover_letter']),
            (['why_interested', 'motivation', 'interest'], self.personal_info['why_interested'])
        ]

        for field_names, value in field_mappings:
            if self.fill_field(field_names, value):
                filled_count += 1

        self.logger.info(f"✅ Filled {filled_count} form fields")
        return filled_count

    def fill_field(self, field_names, value):
        """Fill a specific field using multiple search strategies"""
        for field_name in field_names:
            # Multiple search strategies
            search_strategies = [
                (By.NAME, field_name),
                (By.ID, field_name),
                (By.CSS_SELECTOR, f"input[name='{field_name}']"),
                (By.CSS_SELECTOR, f"input[id='{field_name}']"),
                (By.CSS_SELECTOR, f"textarea[name='{field_name}']"),
                (By.CSS_SELECTOR, f"textarea[id='{field_name}']"),
                (By.CSS_SELECTOR, f"[data-testid='{field_name}']"),
                (By.CSS_SELECTOR, f"[placeholder*='{field_name}']"),
                (By.XPATH, f"//input[contains(@placeholder, '{field_name}')]"),
                (By.XPATH, f"//textarea[contains(@placeholder, '{field_name}')]")
            ]

            for strategy, selector in search_strategies:
                try:
                    element = self.driver.find_element(strategy, selector)
                    if element.is_enabled() and element.is_displayed():
                        if self.safe_send_keys(element, value):
                            self.logger.info(f"✅ Filled {field_name}: {value[:20]}...")
                            time.sleep(0.5)
                            return True
                except:
                    continue

        return False

    def submit_application(self):
        """Submit the application with enhanced submit detection"""
        submit_selectors = [
            "button[type='submit']",
            "input[type='submit']",
            "button:contains('Submit')",
            "button:contains('Apply')",
            "button:contains('Send')",
            ".submit-button",
            ".apply-button",
            "[data-testid*='submit']",
            "[id*='submit']",
            ".btn-primary",
            ".cta-button"
        ]

        for selector in submit_selectors:
            try:
                elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                for element in elements:
                    if element.is_displayed() and element.is_enabled():
                        text = element.text.lower()
                        if any(word in text for word in ['submit', 'apply', 'send']):
                            self.logger.info("🚀 SUBMITTING APPLICATION...")
                            if self.safe_click(element):
                                time.sleep(5)
                                return True
            except:
                continue

        self.logger.warning("No submit button found")
        return False

    def check_confirmation(self):
        """Check for application confirmation"""
        time.sleep(3)
        self.take_screenshot("after_submission")

        # Success indicators
        success_phrases = [
            "thank you for your application",
            "application submitted",
            "successfully applied",
            "application received",
            "we have received your application",
            "your application has been submitted",
            "application complete",
            "thank you for applying",
            "we'll be in touch",
            "application successful"
        ]

        page_text = self.driver.page_source.lower()
        for phrase in success_phrases:
            if phrase in page_text:
                self.logger.info(f"✅ CONFIRMATION: {phrase}")
                return phrase

        # Check URL for success indicators
        current_url = self.driver.current_url.lower()
        url_success_indicators = ['success', 'thank', 'confirm', 'complete', 'submitted']
        for indicator in url_success_indicators:
            if indicator in current_url:
                self.logger.info(f"✅ SUCCESS URL: {current_url}")
                return f"Success URL detected: {indicator}"

        # Check for success elements
        success_selectors = [
            ".success-message",
            ".confirmation-message",
            "[data-testid*='success']",
            ".alert-success",
            ".message-success"
        ]

        for selector in success_selectors:
            try:
                element = self.driver.find_element(By.CSS_SELECTOR, selector)
                if element.is_displayed():
                    self.logger.info(f"✅ SUCCESS ELEMENT: {element.text}")
                    return element.text
            except:
                continue

        self.logger.warning("No confirmation detected")
        return None

    def record_success(self, job_title, index, confirmation):
        """Record successful application"""
        timestamp = datetime.now().isoformat()

        success_record = {
            'job_title': job_title,
            'timestamp': timestamp,
            'confirmation': confirmation,
            'application_url': self.driver.current_url,
            'index': index,
            'status': 'LIVE_APPLICATION_CONFIRMED'
        }

        filename = f"{self.confirmations_dir}/LIVE_SUCCESS_{index}_{datetime.now().strftime('%H%M%S')}.json"
        with open(filename, 'w') as f:
            json.dump(success_record, f, indent=2)

        self.successful_applications.append(success_record)
        self.logger.info(f"🎉 SUCCESS RECORDED: {filename}")

    def generate_final_report(self):
        """Generate final comprehensive report"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        report = {
            'system_type': 'ENHANCED_LIVE_APPLICATION_SYSTEM',
            'timestamp': datetime.now().isoformat(),
            'confirmed_applications': len(self.successful_applications),
            'success_details': self.successful_applications,
            'confirmation_rate': f"{self.confirmation_count}/10 attempted applications",
            'applicant': self.personal_info['full_name']
        }

        report_file = f"{self.base_dir}/ENHANCED_LIVE_REPORT_{timestamp}.json"
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)

        self.logger.info(f"📊 FINAL REPORT: {report_file}")
        return report

    def run_enhanced_system(self):
        """Run the enhanced live application system"""
        self.logger.info("🚀 ENHANCED LIVE APPLICATION SYSTEM STARTING")
        self.logger.info("🎯 GOAL: Real applications with confirmed submissions")
        self.logger.info("=" * 80)

        try:
            self.setup_webdriver()
            confirmed_count = self.find_and_apply_to_jobs()
            report = self.generate_final_report()

            self.logger.info("🏆 ENHANCED SYSTEM COMPLETED")
            self.logger.info(f"✅ Confirmed applications: {confirmed_count}")

            if confirmed_count > 0:
                self.logger.info("🎉 SUCCESS: Live applications confirmed!")
                return True
            else:
                self.logger.warning("❌ No applications were confirmed")
                return False

        except Exception as e:
            self.logger.error(f"System error: {e}")
            return False
        finally:
            if hasattr(self, 'driver'):
                self.logger.info("🔍 Keeping browser open for verification...")
                time.sleep(10)  # Keep open for 10 seconds to verify
                self.driver.quit()

def main():
    system = EnhancedLiveApplicationSystem()
    success = system.run_enhanced_system()

    if success:
        print("🎉 ENHANCED SYSTEM SUCCESS: Live applications confirmed!")
    else:
        print("❌ No confirmed applications - system needs refinement")

if __name__ == "__main__":
    main()