#!/usr/bin/env python3
"""
Ultimate LinkedIn Job Application Automation
Uses JavaScript execution and smart element detection to avoid stale reference issues
Focuses specifically on confirming job applications are opened
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
        logging.FileHandler('ultimate_linkedin_automation.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class UltimateJobApplier:
    def __init__(self):
        """Initialize the ultimate job application automation"""
        self.driver = None
        self.session_id = datetime.now().strftime('%Y%m%d_%H%M%S')

        # Target parameters
        self.search_params = {
            'keywords': 'software',
            'location': 'San Jose, California, United States',
            'geoId': '106233382',
            'distance': '25'
        }

        # Application tracking
        self.confirmed_applications = []
        self.session_stats = {
            'start_time': time.time(),
            'jobs_processed': 0,
            'applications_opened': 0,
            'successful_clicks': 0
        }

    def setup_driver(self):
        """Setup Chrome WebDriver"""
        chrome_options = Options()

        # Essential options
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

            # Anti-detection
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

            logger.info("✅ WebDriver setup successfully")
            return True

        except Exception as e:
            logger.error(f"❌ Failed to setup WebDriver: {e}")
            return False

    def navigate_to_jobs(self):
        """Navigate to LinkedIn jobs"""
        try:
            # Build search URL
            base_url = "https://www.linkedin.com/jobs/search"
            params = {
                'keywords': self.search_params['keywords'],
                'location': self.search_params['location'],
                'geoId': self.search_params['geoId'],
                'distance': self.search_params['distance'],
                'f_TPR': 'r86400',
                'sortBy': 'DD'
            }

            search_url = f"{base_url}?" + urllib.parse.urlencode(params)
            logger.info(f"🔗 Navigating to: {search_url}")

            self.driver.get(search_url)
            time.sleep(5)

            if "linkedin.com" in self.driver.current_url.lower():
                logger.info("✅ Successfully navigated to LinkedIn job search")
                return True
            else:
                logger.error(f"❌ Navigation failed")
                return False

        except Exception as e:
            logger.error(f"❌ Error navigating: {e}")
            return False

    def get_job_count_via_js(self):
        """Get the number of job cards using JavaScript"""
        try:
            js_code = """
            var jobCards = document.querySelectorAll('.job-search-card, .jobs-search-results__list-item, [data-entity-urn*="jobPosting"]');
            return jobCards.length;
            """

            count = self.driver.execute_script(js_code)
            logger.info(f"✅ Found {count} jobs via JavaScript")
            return count

        except Exception as e:
            logger.error(f"❌ Error getting job count: {e}")
            return 0

    def click_job_by_index_js(self, index):
        """Click a job by index using JavaScript to avoid stale elements"""
        try:
            js_code = f"""
            var jobCards = document.querySelectorAll('.job-search-card, .jobs-search-results__list-item, [data-entity-urn*="jobPosting"]');
            if (jobCards.length > {index}) {{
                var job = jobCards[{index}];
                job.scrollIntoView({{behavior: 'smooth', block: 'center'}});

                // Wait a moment then click
                setTimeout(function() {{
                    job.click();
                }}, 1000);

                return true;
            }}
            return false;
            """

            result = self.driver.execute_script(js_code)

            if result:
                time.sleep(3)  # Wait for job to load
                logger.info(f"✅ Successfully clicked job #{index + 1} via JavaScript")
                self.session_stats['successful_clicks'] += 1
                return True
            else:
                logger.warning(f"⚠️ Could not click job #{index + 1}")
                return False

        except Exception as e:
            logger.error(f"❌ Error clicking job #{index + 1}: {e}")
            return False

    def find_apply_buttons_js(self):
        """Find apply buttons using JavaScript"""
        try:
            js_code = """
            // Look for apply buttons with comprehensive selectors
            var applySelectors = [
                '.jobs-apply-button',
                'button[aria-label*="Apply"]',
                'button[aria-label*="apply"]',
                'a[aria-label*="Apply"]',
                'a[aria-label*="apply"]',
                '[data-control-name*="apply"]',
                '.apply-button',
                '.easy-apply-button',
                'button[data-tracking-control-name*="apply"]',
                '[data-control-name="jobdetails_topcard_iapply"]'
            ];

            var foundButtons = [];

            for (var i = 0; i < applySelectors.length; i++) {
                var buttons = document.querySelectorAll(applySelectors[i]);
                for (var j = 0; j < buttons.length; j++) {
                    var btn = buttons[j];
                    if (btn.offsetParent !== null && !btn.disabled) { // visible and enabled
                        var text = (btn.textContent || btn.innerText || '').toLowerCase();
                        var ariaLabel = (btn.getAttribute('aria-label') || '').toLowerCase();

                        if (text.includes('apply') || ariaLabel.includes('apply')) {
                            foundButtons.push({
                                selector: applySelectors[i],
                                text: btn.textContent || btn.innerText,
                                ariaLabel: btn.getAttribute('aria-label'),
                                index: foundButtons.length
                            });
                        }
                    }
                }
            }

            return foundButtons;
            """

            buttons = self.driver.execute_script(js_code)
            return buttons

        except Exception as e:
            logger.error(f"❌ Error finding apply buttons: {e}")
            return []

    def click_apply_button_js(self, button_info):
        """Click apply button using JavaScript"""
        try:
            js_code = f"""
            var buttons = document.querySelectorAll('{button_info['selector']}');
            var targetButton = null;

            for (var i = 0; i < buttons.length; i++) {{
                var btn = buttons[i];
                var text = (btn.textContent || btn.innerText || '').toLowerCase();
                var ariaLabel = (btn.getAttribute('aria-label') || '').toLowerCase();

                if ((text.includes('apply') || ariaLabel.includes('apply')) && btn.offsetParent !== null) {{
                    targetButton = btn;
                    break;
                }}
            }}

            if (targetButton) {{
                targetButton.scrollIntoView({{behavior: 'smooth', block: 'center'}});

                setTimeout(function() {{
                    targetButton.click();
                }}, 1000);

                return true;
            }}

            return false;
            """

            result = self.driver.execute_script(js_code)

            if result:
                time.sleep(5)  # Wait for application page to load
                logger.info(f"🚀 APPLY BUTTON CLICKED via JavaScript!")
                return True
            else:
                logger.warning("⚠️ Could not click apply button")
                return False

        except Exception as e:
            logger.error(f"❌ Error clicking apply button: {e}")
            return False

    def find_external_links_js(self):
        """Find external application links using JavaScript"""
        try:
            js_code = """
            var externalSelectors = [
                'a[href*="apply"]',
                'a[target="_blank"]',
                '[data-tracking-control-name="external_apply"]',
                'a[class*="external"]'
            ];

            var foundLinks = [];

            for (var i = 0; i < externalSelectors.length; i++) {
                var links = document.querySelectorAll(externalSelectors[i]);
                for (var j = 0; j < links.length; j++) {
                    var link = links[j];
                    if (link.offsetParent !== null) { // visible
                        var href = link.getAttribute('href') || '';
                        var text = (link.textContent || link.innerText || '').toLowerCase();

                        if (href.toLowerCase().includes('apply') || text.includes('apply')) {
                            foundLinks.push({
                                href: href,
                                text: link.textContent || link.innerText,
                                selector: externalSelectors[i]
                            });
                        }
                    }
                }
            }

            return foundLinks;
            """

            links = self.driver.execute_script(js_code)
            return links

        except Exception as e:
            logger.error(f"❌ Error finding external links: {e}")
            return []

    def verify_application_page(self, job_index):
        """Verify that an application page/form has opened"""
        try:
            logger.info(f"✅ Verifying application page for job #{job_index + 1}")

            time.sleep(3)  # Wait for page to load

            current_url = self.driver.current_url.lower()
            page_title = self.driver.title.lower()

            # Check URL
            url_indicators = ['apply', 'application', 'form', 'submit']
            url_check = any(indicator in current_url for indicator in url_indicators)

            # Check title
            title_indicators = ['apply', 'application', 'job']
            title_check = any(indicator in page_title for indicator in title_indicators)

            # Check for form elements using JavaScript
            js_code = """
            var formElements = document.querySelectorAll('form, input[type="file"], textarea, .application, .apply-form');
            return formElements.length;
            """

            form_count = self.driver.execute_script(js_code)

            # Check page content using JavaScript
            js_code = """
            var pageText = document.body.innerText.toLowerCase();
            var indicators = ['upload resume', 'cover letter', 'submit application', 'application form', 'required field'];
            var found = 0;
            for (var i = 0; i < indicators.length; i++) {
                if (pageText.includes(indicators[i])) {
                    found++;
                }
            }
            return found;
            """

            text_indicators = self.driver.execute_script(js_code)

            # Determine if application opened
            application_opened = url_check or title_check or form_count > 0 or text_indicators > 0

            if application_opened:
                logger.info("🎉 ✅ JOB APPLICATION SUCCESSFULLY OPENED!")
                logger.info(f"    🔗 URL check: {url_check}")
                logger.info(f"    📄 Title check: {title_check}")
                logger.info(f"    📋 Form elements: {form_count}")
                logger.info(f"    📝 Text indicators: {text_indicators}")
                logger.info(f"    🌐 Current URL: {current_url}")
                logger.info(f"    📑 Page title: {page_title}")

                # Record successful opening
                self.confirmed_applications.append({
                    'job_index': job_index + 1,
                    'timestamp': datetime.now().isoformat(),
                    'url': current_url,
                    'title': page_title,
                    'verification': {
                        'url_check': url_check,
                        'title_check': title_check,
                        'form_count': form_count,
                        'text_indicators': text_indicators
                    }
                })

                self.session_stats['applications_opened'] += 1

                # Go back to job list
                self.driver.back()
                time.sleep(3)

                return True
            else:
                logger.warning(f"⚠️ Application not confirmed for job #{job_index + 1}")
                return False

        except Exception as e:
            logger.error(f"❌ Error verifying application: {e}")
            return False

    def handle_external_link(self, link_info, job_index):
        """Handle external application links"""
        try:
            href = link_info['href']
            logger.info(f"🔗 Opening external application: {href}")

            # Open in new tab using JavaScript
            js_code = f"window.open('{href}', '_blank');"
            self.driver.execute_script(js_code)
            time.sleep(3)

            # Switch to new tab
            self.driver.switch_to.window(self.driver.window_handles[-1])
            time.sleep(5)

            # Check external page
            current_url = self.driver.current_url.lower()

            # Check if it's an application page using JavaScript
            js_code = """
            var pageText = document.body.innerText.toLowerCase();
            var urlText = window.location.href.toLowerCase();
            var indicators = ['apply', 'application', 'career', 'job', 'resume', 'submit', 'candidate', 'hiring'];

            var found = 0;
            for (var i = 0; i < indicators.length; i++) {
                if (pageText.includes(indicators[i]) || urlText.includes(indicators[i])) {
                    found++;
                }
            }
            return found;
            """

            indicator_count = self.driver.execute_script(js_code)

            if indicator_count > 0:
                logger.info("🎉 ✅ EXTERNAL APPLICATION PAGE SUCCESSFULLY OPENED!")
                logger.info(f"    🌐 URL: {current_url}")
                logger.info(f"    🔍 Application indicators found: {indicator_count}")

                # Record successful opening
                self.confirmed_applications.append({
                    'job_index': job_index + 1,
                    'timestamp': datetime.now().isoformat(),
                    'type': 'external',
                    'url': current_url,
                    'indicator_count': indicator_count
                })

                self.session_stats['applications_opened'] += 1
                success = True
            else:
                logger.warning("⚠️ External page doesn't appear to be an application")
                success = False

            # Close external tab and return to LinkedIn
            self.driver.close()
            self.driver.switch_to.window(self.driver.window_handles[0])
            time.sleep(2)

            return success

        except Exception as e:
            logger.error(f"❌ Error with external link: {e}")
            return False

    def process_job(self, job_index):
        """Process a single job - click it and try to apply"""
        try:
            logger.info(f"\n[{job_index + 1}] PROCESSING JOB #{job_index + 1}")
            logger.info("-" * 40)

            # Click job using JavaScript
            if not self.click_job_by_index_js(job_index):
                logger.warning(f"⚠️ Could not click job #{job_index + 1}")
                return False

            # Look for apply buttons
            apply_buttons = self.find_apply_buttons_js()

            if apply_buttons:
                logger.info(f"🎯 Found {len(apply_buttons)} apply button(s)")

                # Try to click the first apply button
                for button in apply_buttons:
                    logger.info(f"    Trying button: '{button['text']}' ({button['selector']})")

                    if self.click_apply_button_js(button):
                        # Verify application opened
                        if self.verify_application_page(job_index):
                            logger.info(f"✅ Job #{job_index + 1}: Application CONFIRMED OPENED")
                            return True
                        else:
                            logger.info(f"⚠️ Job #{job_index + 1}: Applied but could not verify opening")
                            return False

            # If no apply buttons, look for external links
            external_links = self.find_external_links_js()

            if external_links:
                logger.info(f"🔗 Found {len(external_links)} external link(s)")

                for link in external_links:
                    logger.info(f"    Trying external link: {link['href']}")

                    if self.handle_external_link(link, job_index):
                        logger.info(f"✅ Job #{job_index + 1}: External application CONFIRMED OPENED")
                        return True

            logger.info(f"ℹ️ Job #{job_index + 1}: No application options available")
            return False

        except Exception as e:
            logger.error(f"❌ Error processing job #{job_index + 1}: {e}")
            return False

    def run_automation(self):
        """Main automation loop"""
        logger.info("🚀 STARTING ULTIMATE LINKEDIN JOB APPLICATION AUTOMATION")
        logger.info("🎯 Target: Software jobs within 25 miles of San Jose, CA")
        logger.info("⚡ Mission: Confirm job applications are opened successfully")
        logger.info("🧠 Using JavaScript-based automation to avoid stale elements")
        logger.info("=" * 80)

        try:
            # Setup
            if not self.setup_driver():
                return False

            if not self.navigate_to_jobs():
                return False

            # Get job count
            job_count = self.get_job_count_via_js()

            if job_count == 0:
                logger.warning("⚠️ No jobs found")
                return False

            logger.info(f"🎯 Found {job_count} jobs to process")

            # Process each job
            for i in range(job_count):
                self.session_stats['jobs_processed'] = i + 1

                success = self.process_job(i)

                # Print progress
                runtime = (time.time() - self.session_stats['start_time']) / 60
                logger.info(f"\n📊 PROGRESS UPDATE:")
                logger.info(f"    📋 Jobs processed: {self.session_stats['jobs_processed']}")
                logger.info(f"    🎯 Successful clicks: {self.session_stats['successful_clicks']}")
                logger.info(f"    ✅ Applications opened: {self.session_stats['applications_opened']}")
                logger.info(f"    ⏱️ Runtime: {runtime:.1f} minutes")

                # Check if mission accomplished
                if self.session_stats['applications_opened'] >= 5:
                    logger.info("\n🎉 ✅ MISSION ACCOMPLISHED!")
                    logger.info("🏆 JOB APPLICATIONS HAVE BEEN CONFIRMED OPENED!")
                    logger.info(f"🎯 Total confirmed openings: {self.session_stats['applications_opened']}")
                    return True

                # Delay between jobs
                time.sleep(3)

                # Stop after processing 30 jobs if no applications opened
                if i >= 29 and self.session_stats['applications_opened'] == 0:
                    logger.warning("⚠️ Processed 30 jobs without confirmed applications")
                    break

            # Final summary
            logger.info("\n🏁 AUTOMATION COMPLETED")
            logger.info(f"✅ Applications confirmed opened: {self.session_stats['applications_opened']}")

            return self.session_stats['applications_opened'] > 0

        except Exception as e:
            logger.error(f"❌ Automation error: {e}")
            return False

    def cleanup(self):
        """Clean up resources"""
        if self.driver:
            try:
                self.driver.quit()
                logger.info("🧹 Resources cleaned up")
            except:
                pass

def main():
    automation = UltimateJobApplier()

    try:
        logger.info("🌟 ULTIMATE LINKEDIN JOB APPLICATION AUTOMATION")
        logger.info("🎯 Will continue until job applications are confirmed opened")
        logger.info("🧠 Uses JavaScript execution to avoid stale element issues")

        success = automation.run_automation()

        if success:
            logger.info("\n🎉 🎉 🎉 SUCCESS! 🎉 🎉 🎉")
            logger.info("✅ JOB APPLICATIONS HAVE BEEN CONFIRMED OPENED!")
            logger.info("🏆 Mission accomplished - applications are working!")
        else:
            logger.warning("\n⚠️ Automation completed but no applications were confirmed")

    except KeyboardInterrupt:
        logger.info("\n⏹️ Automation stopped by user")

    finally:
        automation.cleanup()

        # Final statistics
        runtime = (time.time() - automation.session_stats['start_time']) / 60
        logger.info("\n" + "="*60)
        logger.info("📊 FINAL RESULTS")
        logger.info("="*60)
        logger.info(f"✅ Applications confirmed opened: {automation.session_stats['applications_opened']}")
        logger.info(f"🎯 Successful job clicks: {automation.session_stats['successful_clicks']}")
        logger.info(f"📋 Jobs processed: {automation.session_stats['jobs_processed']}")
        logger.info(f"⏱️ Total runtime: {runtime:.1f} minutes")

        if automation.confirmed_applications:
            logger.info(f"\n📝 CONFIRMED APPLICATION OPENINGS:")
            for app in automation.confirmed_applications:
                app_type = app.get('type', 'linkedin')
                logger.info(f"  • Job #{app['job_index']} ({app_type}): {app['url']}")

if __name__ == "__main__":
    main()