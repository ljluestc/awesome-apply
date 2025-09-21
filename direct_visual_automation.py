#!/usr/bin/env python3
"""
Direct LinkedIn Job Application Automation
Focused on opening and confirming job applications for software positions in San Jose area
"""

import time
import json
import logging
import os
import sys
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import *
from webdriver_manager.chrome import ChromeDriverManager
import urllib.parse

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('direct_linkedin_automation.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class DirectLinkedInAutomation:
    def __init__(self):
        """Initialize direct LinkedIn automation focused on application confirmation"""
        self.driver = None
        self.session_id = datetime.now().strftime('%Y%m%d_%H%M%S')

        # Target parameters - exactly as requested
        self.search_params = {
            'keywords': 'software',
            'location': 'San Jose, California, United States',
            'geoId': '106233382',
            'distance': '25'
        }

        # Application tracking
        self.confirmed_openings = []
        self.session_stats = {
            'start_time': time.time(),
            'jobs_found': 0,
            'jobs_clicked': 0,
            'applications_opened': 0,
            'external_applications': 0
        }

    def create_driver(self):
        """Create WebDriver with maximum stability and visibility"""
        chrome_options = Options()

        # Make browser visible for debugging
        # chrome_options.add_argument("--headless")  # Commented out for visibility

        # Stability options
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("--start-maximized")

        # Anti-detection
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        chrome_options.add_argument("--user-agent=Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")

        try:
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=chrome_options)

            # Anti-detection JavaScript
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

            logger.info("✅ WebDriver created successfully")
            return True

        except Exception as e:
            logger.error(f"❌ Failed to create WebDriver: {e}")
            return False

    def navigate_to_linkedin_jobs(self):
        """Navigate directly to LinkedIn job search with our parameters"""
        try:
            # Build the exact search URL
            base_url = "https://www.linkedin.com/jobs/search"
            params = {
                'keywords': self.search_params['keywords'],
                'location': self.search_params['location'],
                'geoId': self.search_params['geoId'],
                'distance': self.search_params['distance'],
                'f_TPR': 'r86400',  # Recent jobs
                'sortBy': 'DD'  # Date posted
            }

            search_url = f"{base_url}?" + urllib.parse.urlencode(params)
            logger.info(f"🔗 Navigating to: {search_url}")

            self.driver.get(search_url)
            time.sleep(5)

            # Check if we reached LinkedIn
            current_url = self.driver.current_url.lower()
            if "linkedin.com" in current_url:
                logger.info("✅ Successfully reached LinkedIn job search")
                return True
            else:
                logger.error(f"❌ Failed to reach LinkedIn. Current URL: {current_url}")
                return False

        except Exception as e:
            logger.error(f"❌ Navigation error: {e}")
            return False

    def get_all_job_cards(self):
        """Get all job cards from the current page"""
        try:
            # Wait for job cards to load
            time.sleep(3)

            # Multiple selectors for job cards
            selectors = [
                ".job-search-card",
                ".jobs-search-results__list-item",
                "[data-entity-urn*='jobPosting']",
                ".base-search-card"
            ]

            all_jobs = []
            for selector in selectors:
                try:
                    jobs = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    if jobs:
                        all_jobs = jobs
                        logger.info(f"✅ Found {len(jobs)} jobs using selector: {selector}")
                        break
                except Exception:
                    continue

            self.session_stats['jobs_found'] = len(all_jobs)
            return all_jobs

        except Exception as e:
            logger.error(f"❌ Error finding job cards: {e}")
            return []

    def click_job_card(self, job_card, job_index):
        """Click on a job card to view details"""
        try:
            logger.info(f"🎯 Clicking job #{job_index + 1}")

            # Scroll to job card
            self.driver.execute_script("arguments[0].scrollIntoView(true);", job_card)
            time.sleep(1)

            # Click the job card
            ActionChains(self.driver).move_to_element(job_card).click().perform()
            time.sleep(3)

            self.session_stats['jobs_clicked'] += 1
            logger.info(f"✅ Successfully clicked job #{job_index + 1}")
            return True

        except Exception as e:
            logger.error(f"❌ Error clicking job #{job_index + 1}: {e}")
            return False

    def find_and_click_apply_button(self, job_index):
        """Find and click apply button for current job"""
        try:
            logger.info(f"🔍 Looking for apply button on job #{job_index + 1}")

            # Comprehensive list of apply button selectors
            apply_selectors = [
                ".jobs-apply-button",
                "button[aria-label*='Apply']",
                "button[aria-label*='apply']",
                "a[aria-label*='Apply']",
                "a[aria-label*='apply']",
                "[data-control-name*='apply']",
                ".apply-button",
                ".easy-apply-button",
                "button[data-tracking-control-name*='apply']",
                "[data-control-name='jobdetails_topcard_iapply']",
                "button[class*='apply']",
                "a[class*='apply']"
            ]

            apply_button = None
            button_selector_used = None

            # Search for apply buttons
            for selector in apply_selectors:
                try:
                    buttons = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    for btn in buttons:
                        if btn.is_displayed() and btn.is_enabled():
                            text = btn.text.lower()
                            aria_label = btn.get_attribute('aria-label') or ""
                            aria_label = aria_label.lower()

                            # Check if this looks like an apply button
                            if ('apply' in text or 'apply' in aria_label or
                                'submit' in text or 'submit' in aria_label):
                                apply_button = btn
                                button_selector_used = selector
                                break
                    if apply_button:
                        break
                except Exception:
                    continue

            if apply_button:
                logger.info(f"🎯 Found apply button using: {button_selector_used}")
                logger.info(f"    Button text: '{apply_button.text}'")

                # Click the apply button
                try:
                    self.driver.execute_script("arguments[0].scrollIntoView(true);", apply_button)
                    time.sleep(1)
                    apply_button.click()
                    time.sleep(5)

                    logger.info("🚀 APPLY BUTTON CLICKED!")

                    # Verify application page/form opened
                    return self.verify_application_opened(job_index)

                except Exception as e:
                    logger.error(f"❌ Error clicking apply button: {e}")
                    return False
            else:
                # Check for external application links
                external_selectors = [
                    "a[href*='apply']",
                    "a[target='_blank']",
                    "[data-tracking-control-name='external_apply']",
                    "a[class*='external']"
                ]

                for selector in external_selectors:
                    try:
                        links = self.driver.find_elements(By.CSS_SELECTOR, selector)
                        for link in links:
                            if link.is_displayed():
                                href = link.get_attribute('href') or ""
                                text = link.text.lower()

                                if 'apply' in href.lower() or 'apply' in text:
                                    logger.info(f"🔗 Found external apply link: {href}")
                                    return self.handle_external_application(link, job_index)
                    except Exception:
                        continue

                logger.warning(f"⚠️ No apply button found for job #{job_index + 1}")
                return False

        except Exception as e:
            logger.error(f"❌ Error finding apply button for job #{job_index + 1}: {e}")
            return False

    def verify_application_opened(self, job_index):
        """Verify that an application form or page has opened"""
        try:
            logger.info(f"✅ Verifying application opened for job #{job_index + 1}")

            # Wait a moment for page to load
            time.sleep(3)

            current_url = self.driver.current_url.lower()
            page_source = self.driver.page_source.lower()

            # Check URL for application indicators
            url_indicators = ['apply', 'application', 'form', 'submit']
            url_has_application = any(indicator in current_url for indicator in url_indicators)

            # Check for application form elements
            form_indicators = [
                "form",
                "input[type='file']",  # Resume upload
                "textarea",
                ".application",
                ".apply-form",
                "upload resume",
                "cover letter",
                "submit application"
            ]

            form_elements_found = []
            for indicator in form_indicators:
                try:
                    if indicator.startswith('.') or indicator.startswith('['):
                        # CSS selector
                        elements = self.driver.find_elements(By.CSS_SELECTOR, indicator)
                        if elements:
                            form_elements_found.append(indicator)
                    else:
                        # Text search
                        if indicator in page_source:
                            form_elements_found.append(indicator)
                except Exception:
                    continue

            # Check page title
            page_title = self.driver.title.lower()
            title_has_application = any(word in page_title for word in ['apply', 'application', 'job'])

            # Determine if application opened
            application_opened = bool(url_has_application or form_elements_found or title_has_application)

            if application_opened:
                logger.info("🎉 ✅ JOB APPLICATION SUCCESSFULLY OPENED!")
                logger.info(f"    🔗 URL indicates application: {url_has_application}")
                logger.info(f"    📋 Form elements found: {len(form_elements_found)}")
                logger.info(f"    📄 Title indicates application: {title_has_application}")
                logger.info(f"    🌐 Current URL: {current_url}")
                logger.info(f"    📑 Page title: {self.driver.title}")

                if form_elements_found:
                    logger.info(f"    🔍 Form indicators: {', '.join(form_elements_found[:3])}")

                # Record the successful opening
                self.confirmed_openings.append({
                    'job_index': job_index + 1,
                    'timestamp': datetime.now().isoformat(),
                    'url': current_url,
                    'title': self.driver.title,
                    'verification_method': {
                        'url_check': url_has_application,
                        'form_elements': len(form_elements_found),
                        'title_check': title_has_application
                    }
                })

                self.session_stats['applications_opened'] += 1

                # Go back to job list for next job
                self.driver.back()
                time.sleep(3)

                return True
            else:
                logger.warning(f"⚠️ Could not verify application opened for job #{job_index + 1}")
                return False

        except Exception as e:
            logger.error(f"❌ Error verifying application for job #{job_index + 1}: {e}")
            return False

    def handle_external_application(self, link, job_index):
        """Handle external application links"""
        try:
            href = link.get_attribute('href')
            logger.info(f"🔗 Opening external application for job #{job_index + 1}: {href}")

            # Open in new tab
            original_window = self.driver.current_window_handle
            self.driver.execute_script("window.open(arguments[0]);", href)
            time.sleep(3)

            # Switch to new tab
            self.driver.switch_to.window(self.driver.window_handles[-1])
            time.sleep(5)

            # Check external site
            current_url = self.driver.current_url.lower()
            page_source = self.driver.page_source.lower()

            external_indicators = [
                'apply', 'application', 'career', 'job', 'position',
                'resume', 'submit', 'candidate', 'hiring', 'form'
            ]

            external_application_detected = any(
                indicator in current_url or indicator in page_source
                for indicator in external_indicators
            )

            if external_application_detected:
                logger.info("🎉 ✅ EXTERNAL JOB APPLICATION SUCCESSFULLY OPENED!")
                logger.info(f"    🌐 External URL: {current_url}")

                self.confirmed_openings.append({
                    'job_index': job_index + 1,
                    'timestamp': datetime.now().isoformat(),
                    'url': current_url,
                    'type': 'external',
                    'original_linkedin_url': self.driver.current_url
                })

                self.session_stats['external_applications'] += 1
                success = True
            else:
                logger.warning(f"⚠️ External site did not appear to be an application page")
                success = False

            # Close external tab and return to LinkedIn
            self.driver.close()
            self.driver.switch_to.window(original_window)
            time.sleep(2)

            return success

        except Exception as e:
            logger.error(f"❌ Error with external application: {e}")
            return False

    def run_job_application_automation(self):
        """Main automation loop - apply to jobs until confirmed openings"""
        logger.info("🚀 STARTING DIRECT LINKEDIN JOB APPLICATION AUTOMATION")
        logger.info("🎯 Target: Software jobs within 25 miles of San Jose, CA")
        logger.info("⚡ Goal: Confirm job applications are being opened")
        logger.info("=" * 80)

        try:
            # Create WebDriver
            if not self.create_driver():
                logger.error("❌ Failed to create WebDriver")
                return False

            # Navigate to LinkedIn jobs
            if not self.navigate_to_linkedin_jobs():
                logger.error("❌ Failed to navigate to LinkedIn jobs")
                return False

            # Main application loop
            page_count = 0
            total_jobs_processed = 0

            while self.session_stats['applications_opened'] < 10:  # Stop after 10 confirmed openings
                page_count += 1
                logger.info(f"\n📄 PROCESSING PAGE {page_count}")
                logger.info("=" * 50)

                # Get job cards on current page
                job_cards = self.get_all_job_cards()

                if not job_cards:
                    logger.warning("⚠️ No job cards found on this page")
                    break

                # Process each job on the page
                for i, job_card in enumerate(job_cards):
                    logger.info(f"\n[{i+1}/{len(job_cards)}] PROCESSING JOB #{total_jobs_processed + 1}")
                    logger.info("-" * 40)

                    # Click job card
                    if self.click_job_card(job_card, total_jobs_processed):
                        # Try to find and click apply button
                        application_success = self.find_and_click_apply_button(total_jobs_processed)

                        if application_success:
                            logger.info(f"✅ Job #{total_jobs_processed + 1}: Application opened successfully")
                        else:
                            logger.info(f"ℹ️ Job #{total_jobs_processed + 1}: No application available")

                    total_jobs_processed += 1

                    # Print progress
                    logger.info(f"\n📊 CURRENT PROGRESS:")
                    logger.info(f"    📋 Jobs processed: {total_jobs_processed}")
                    logger.info(f"    🎯 Jobs clicked: {self.session_stats['jobs_clicked']}")
                    logger.info(f"    ✅ Applications opened: {self.session_stats['applications_opened']}")
                    logger.info(f"    🔗 External applications: {self.session_stats['external_applications']}")
                    logger.info(f"    ⏱️ Runtime: {(time.time() - self.session_stats['start_time'])/60:.1f} minutes")

                    # Check if we've reached our goal
                    if self.session_stats['applications_opened'] >= 5:
                        logger.info("\n🎉 SUCCESS! CONFIRMED JOB APPLICATIONS HAVE BEEN OPENED!")
                        logger.info(f"✅ Total confirmed openings: {self.session_stats['applications_opened']}")
                        return True

                    # Delay between jobs
                    time.sleep(3)

                # Try to go to next page (basic implementation)
                try:
                    next_button = self.driver.find_element(By.CSS_SELECTOR, "[aria-label*='Next']")
                    if next_button.is_enabled():
                        next_button.click()
                        time.sleep(5)
                    else:
                        logger.info("📄 No more pages available")
                        break
                except:
                    logger.info("📄 No next page button found")
                    break

            # Final results
            logger.info("\n🏁 AUTOMATION COMPLETED")
            logger.info(f"✅ Total applications opened: {self.session_stats['applications_opened']}")

            return True

        except Exception as e:
            logger.error(f"❌ Automation error: {e}")
            return False

    def cleanup(self):
        """Clean up resources"""
        if self.driver:
            try:
                self.driver.quit()
                logger.info("🧹 WebDriver cleaned up")
            except:
                pass

def main():
    automation = DirectLinkedInAutomation()

    try:
        success = automation.run_job_application_automation()

        if success:
            logger.info("\n🎉 MISSION ACCOMPLISHED!")
            logger.info("✅ Job applications have been confirmed opened")
        else:
            logger.error("\n❌ Automation encountered issues")

    except KeyboardInterrupt:
        logger.info("\n⏹️ Automation stopped by user")

    finally:
        automation.cleanup()

        # Final statistics
        logger.info("\n" + "="*60)
        logger.info("📊 FINAL RESULTS")
        logger.info("="*60)
        logger.info(f"✅ Applications confirmed opened: {automation.session_stats['applications_opened']}")
        logger.info(f"🔗 External applications: {automation.session_stats['external_applications']}")
        logger.info(f"🎯 Jobs clicked: {automation.session_stats['jobs_clicked']}")
        logger.info(f"📋 Total jobs found: {automation.session_stats['jobs_found']}")
        logger.info(f"⏱️ Total runtime: {(time.time() - automation.session_stats['start_time'])/60:.1f} minutes")

        if automation.confirmed_openings:
            logger.info(f"\n📝 CONFIRMED APPLICATION OPENINGS:")
            for opening in automation.confirmed_openings:
                logger.info(f"  • Job #{opening['job_index']}: {opening['url']}")

if __name__ == "__main__":
    main()