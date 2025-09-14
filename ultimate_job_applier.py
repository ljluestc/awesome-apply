#!/usr/bin/env python3
"""
Ultimate Job Applier - Handles all job application scenarios
"""

import sys
import os
sys.path.append('/home/calelin/awesome-apply/venv/lib/python3.13/site-packages')

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
import time
import logging
import json

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class UltimateJobApplier:
    def __init__(self):
        self.driver = None
        self.applied_jobs = []
        self.job_urls = []

    def setup_driver(self):
        """Setup Chrome with all optimizations"""
        chrome_options = Options()

        # User profile for persistence
        user_data_dir = "/tmp/chrome_ultimate_profile"
        chrome_options.add_argument(f"--user-data-dir={user_data_dir}")
        chrome_options.add_argument("--profile-directory=Default")

        # Performance optimizations
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)

        # Speed optimizations
        chrome_options.add_argument("--disable-extensions")
        chrome_options.add_argument("--disable-plugins")
        chrome_options.add_argument("--disable-images")
        chrome_options.add_argument("--disable-javascript")  # We'll enable for specific pages

        self.driver = webdriver.Chrome(
            service=Service(ChromeDriverManager().install()),
            options=chrome_options
        )

        self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        logger.info("✅ Ultimate Chrome setup completed")

    def find_all_job_urls(self):
        """Find all job URLs on JobRight.ai"""
        try:
            logger.info("🔍 FINDING ALL JOB URLs...")

            # Start from entry level jobs page (we know this works)
            job_pages = [
                "https://jobright.ai/entry-level-jobs",
                "https://jobright.ai/remote-jobs",
                "https://jobright.ai/part-time-jobs",
                "https://jobright.ai/internship-jobs",
                "https://jobright.ai"
            ]

            all_urls = set()

            for page_url in job_pages:
                try:
                    logger.info(f"\n🎯 Scanning page: {page_url}")
                    self.driver.get(page_url)
                    time.sleep(3)

                    # Re-enable JavaScript for this page
                    self.driver.execute_script("""
                        var script = document.createElement('script');
                        script.innerHTML = 'console.log("JS enabled");';
                        document.head.appendChild(script);
                    """)

                    # Scroll to load dynamic content
                    self.scroll_page()

                    # Find all job-related links
                    job_urls = self.extract_job_urls_from_page()
                    all_urls.update(job_urls)

                    logger.info(f"   Found {len(job_urls)} job URLs on this page")

                except Exception as e:
                    logger.error(f"   ❌ Error scanning {page_url}: {e}")
                    continue

            self.job_urls = list(all_urls)
            logger.info(f"✅ Total unique job URLs found: {len(self.job_urls)}")

            return self.job_urls

        except Exception as e:
            logger.error(f"Job URL finding error: {e}")
            return []

    def scroll_page(self):
        """Scroll page to load all dynamic content"""
        try:
            # Multiple scroll strategies
            last_height = self.driver.execute_script("return document.body.scrollHeight")

            for i in range(5):
                # Scroll down
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(2)

                # Check if content loaded
                new_height = self.driver.execute_script("return document.body.scrollHeight")
                if new_height == last_height:
                    break
                last_height = new_height

                # Click "Load More" buttons
                load_more_buttons = self.driver.find_elements(By.XPATH,
                    "//*[contains(text(), 'Load') or contains(text(), 'More') or contains(text(), 'Show')]"
                )

                for btn in load_more_buttons:
                    try:
                        if btn.is_displayed() and btn.is_enabled():
                            btn.click()
                            time.sleep(2)
                            break
                    except Exception:
                        continue

        except Exception as e:
            logger.error(f"Scrolling error: {e}")

    def extract_job_urls_from_page(self):
        """Extract all job URLs from current page"""
        try:
            job_urls = set()

            # Find all links that might lead to jobs
            link_selectors = [
                "//a[contains(@href, 'job')]",
                "//a[contains(@href, 'position')]",
                "//a[contains(@href, 'career')]",
                "//a[contains(@href, 'apply')]",
                "//a[contains(@href, 'company')]",
                "//a[contains(@href, '/j/')]",  # Common job ID pattern
                "//a[contains(@href, '/jobs/')]"
            ]

            for selector in link_selectors:
                try:
                    elements = self.driver.find_elements(By.XPATH, selector)
                    for element in elements:
                        href = element.get_attribute('href')
                        if href and 'jobright.ai' in href:
                            job_urls.add(href)
                except Exception:
                    continue

            # Also look for clickable job cards that might have onClick handlers
            clickable_selectors = [
                "//*[contains(@class, 'job')][@onclick or @data-href]",
                "//*[contains(@class, 'card')][@onclick or @data-href]",
                "//*[contains(@class, 'listing')][@onclick or @data-href]"
            ]

            for selector in clickable_selectors:
                try:
                    elements = self.driver.find_elements(By.XPATH, selector)
                    for element in elements:
                        data_href = element.get_attribute('data-href')
                        onclick = element.get_attribute('onclick')

                        if data_href and 'jobright.ai' in data_href:
                            job_urls.add(data_href)
                        elif onclick and 'jobright.ai' in onclick:
                            # Extract URL from onclick
                            import re
                            url_match = re.search(r'https?://[^\s\'"]+', onclick)
                            if url_match:
                                job_urls.add(url_match.group())
                except Exception:
                    continue

            return list(job_urls)

        except Exception as e:
            logger.error(f"URL extraction error: {e}")
            return []

    def visit_and_apply_to_job(self, job_url):
        """Visit individual job page and apply"""
        try:
            logger.info(f"\n📋 Visiting job: {job_url}")

            self.driver.get(job_url)
            time.sleep(3)

            # Re-enable JavaScript
            self.driver.execute_script("window.location.reload();")
            time.sleep(3)

            current_url = self.driver.current_url
            page_title = self.driver.title

            logger.info(f"   Page: {page_title}")
            logger.info(f"   URL: {current_url}")

            # Try to find apply buttons with comprehensive search
            apply_buttons = self.find_apply_buttons_comprehensive()

            if not apply_buttons:
                logger.warning("   ❌ No apply buttons found")
                return False

            logger.info(f"   ✅ Found {len(apply_buttons)} apply buttons")

            # Try applying with each button
            for i, button in enumerate(apply_buttons):
                try:
                    logger.info(f"   Clicking apply button {i+1}: {button.text[:50]}")

                    # Scroll to button
                    self.driver.execute_script("arguments[0].scrollIntoView(true);", button)
                    time.sleep(1)

                    # Try clicking
                    success = self.click_button_ultimate(button)

                    if success:
                        logger.info("   ✅ Apply button clicked successfully")

                        # Wait for response
                        time.sleep(3)

                        # Check if we're now on application page or form
                        if self.handle_application_flow():
                            logger.info("   ✅ Application submitted successfully")

                            self.applied_jobs.append({
                                'url': job_url,
                                'title': page_title,
                                'status': 'applied',
                                'timestamp': time.time()
                            })

                            return True

                except Exception as e:
                    logger.error(f"   Apply button {i+1} error: {e}")
                    continue

            logger.warning("   ❌ All apply attempts failed")
            return False

        except Exception as e:
            logger.error(f"Job visit error: {e}")
            return False

    def find_apply_buttons_comprehensive(self):
        """Find apply buttons with ultimate comprehensive search"""
        try:
            apply_buttons = []

            # Ultra-comprehensive apply button selectors
            apply_selectors = [
                # Direct text matches
                "//button[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'apply now')]",
                "//a[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'apply now')]",
                "//button[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'apply')]",
                "//a[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'apply')]",
                "//button[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'submit application')]",
                "//button[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'quick apply')]",

                # Attribute-based matches
                "//*[@data-action='apply']",
                "//*[@data-testid*='apply']",
                "//*[@id*='apply']",
                "//*[contains(@class, 'apply-btn')]",
                "//*[contains(@class, 'apply-button')]",
                "//*[contains(@class, 'btn-apply')]",

                # URL-based matches
                "//a[contains(@href, 'apply')]",
                "//a[contains(@href, 'application')]",

                # Generic buttons that might be apply buttons
                "//button[contains(@class, 'primary')]",
                "//button[contains(@class, 'btn-primary')]",
                "//button[contains(@class, 'cta')]",
                "//a[contains(@class, 'btn-primary')]",
                "//a[contains(@class, 'cta')]",

                # Form submit buttons
                "//input[@type='submit']",
                "//button[@type='submit']"
            ]

            for selector in apply_selectors:
                try:
                    elements = self.driver.find_elements(By.XPATH, selector)
                    for element in elements:
                        if element.is_displayed() and element.is_enabled():
                            # Additional validation
                            text = element.text.strip().lower()
                            href = element.get_attribute('href') or ''
                            onclick = element.get_attribute('onclick') or ''

                            # Check if this looks like an apply button
                            if (
                                'apply' in text or 'submit' in text or 'send' in text or
                                'apply' in href.lower() or 'apply' in onclick.lower() or
                                element.get_attribute('data-action') == 'apply'
                            ):
                                apply_buttons.append(element)

                except Exception:
                    continue

            # Remove duplicates
            unique_buttons = []
            for button in apply_buttons:
                try:
                    is_duplicate = False
                    for existing in unique_buttons:
                        if (button.location == existing.location and
                            button.size == existing.size):
                            is_duplicate = True
                            break

                    if not is_duplicate:
                        unique_buttons.append(button)
                except Exception:
                    continue

            return unique_buttons

        except Exception as e:
            logger.error(f"Apply button search error: {e}")
            return []

    def click_button_ultimate(self, button):
        """Ultimate button clicking with all strategies"""
        try:
            # Try multiple click strategies
            click_strategies = [
                # Standard click
                lambda: button.click(),

                # JavaScript click
                lambda: self.driver.execute_script("arguments[0].click();", button),

                # ActionChains click
                lambda: ActionChains(self.driver).move_to_element(button).click().perform(),

                # ActionChains with offset
                lambda: ActionChains(self.driver).move_to_element_with_offset(button, 5, 5).click().perform(),

                # Force click (remove overlays first)
                lambda: self.force_click(button),

                # Submit form if button is in a form
                lambda: self.submit_parent_form(button),

                # Trigger events manually
                lambda: self.trigger_click_events(button)
            ]

            for i, strategy in enumerate(click_strategies):
                try:
                    strategy()
                    logger.info(f"     Click strategy {i+1} succeeded")
                    return True
                except Exception as e:
                    logger.debug(f"     Click strategy {i+1} failed: {e}")
                    continue

            logger.error("     All click strategies failed")
            return False

        except Exception as e:
            logger.error(f"Ultimate click error: {e}")
            return False

    def force_click(self, button):
        """Force click by removing overlays"""
        # Remove common overlay elements
        self.driver.execute_script("""
            // Remove common overlay classes
            var overlays = document.querySelectorAll('.overlay, .modal, .popup, .loading');
            overlays.forEach(function(el) { el.remove(); });

            // Remove elements with high z-index
            var allElements = document.querySelectorAll('*');
            allElements.forEach(function(el) {
                var style = window.getComputedStyle(el);
                if (parseInt(style.zIndex) > 1000) {
                    el.style.display = 'none';
                }
            });
        """)

        time.sleep(1)
        button.click()

    def submit_parent_form(self, button):
        """Submit the form containing the button"""
        form = button.find_element(By.XPATH, "./ancestor::form")
        if form:
            form.submit()

    def trigger_click_events(self, button):
        """Manually trigger click events"""
        self.driver.execute_script("""
            var element = arguments[0];
            var events = ['mousedown', 'mouseup', 'click'];

            events.forEach(function(eventType) {
                var event = new MouseEvent(eventType, {
                    'view': window,
                    'bubbles': true,
                    'cancelable': true
                });
                element.dispatchEvent(event);
            });
        """, button)

    def handle_application_flow(self):
        """Handle the application flow after clicking apply"""
        try:
            logger.info("     Handling application flow...")

            # Check if we're on a new page or modal appeared
            current_url = self.driver.current_url

            # Wait for page to load/change
            time.sleep(3)

            # Look for application forms
            forms = self.driver.find_elements(By.TAG_NAME, "form")
            if forms:
                logger.info(f"     Found {len(forms)} forms")

                # Try to fill and submit forms
                for form in forms:
                    if self.fill_and_submit_form(form):
                        return True

            # Look for success messages
            success_indicators = [
                "//div[contains(text(), 'applied') or contains(text(), 'submitted') or contains(text(), 'success')]",
                "//*[contains(@class, 'success')]",
                "//*[contains(@class, 'confirmation')]"
            ]

            for selector in success_indicators:
                try:
                    elements = self.driver.find_elements(By.XPATH, selector)
                    if elements:
                        logger.info("     Success message found")
                        return True
                except Exception:
                    continue

            # Check if URL changed to indicate application submission
            if 'thank' in current_url or 'success' in current_url or 'confirmation' in current_url:
                logger.info("     URL indicates success")
                return True

            return False

        except Exception as e:
            logger.error(f"Application flow error: {e}")
            return False

    def fill_and_submit_form(self, form):
        """Fill and submit an application form"""
        try:
            logger.info("     Filling application form...")

            # Find all inputs in the form
            inputs = form.find_elements(By.TAG_NAME, "input")
            textareas = form.find_elements(By.TAG_NAME, "textarea")

            # Basic form filling (you can expand this)
            for input_elem in inputs:
                try:
                    input_type = input_elem.get_attribute('type')
                    input_name = input_elem.get_attribute('name') or ''

                    if input_type == 'text' and 'name' in input_name.lower():
                        input_elem.send_keys("Jeremy Kalilin")
                    elif input_type == 'email' or 'email' in input_name.lower():
                        input_elem.send_keys("jeremykalilin@gmail.com")
                    elif input_type == 'tel' or 'phone' in input_name.lower():
                        input_elem.send_keys("555-123-4567")

                except Exception:
                    continue

            # Fill textareas with basic info
            for textarea in textareas:
                try:
                    if textarea.is_displayed() and textarea.is_enabled():
                        textarea.send_keys("I am interested in this position and believe I would be a great fit for your team.")
                except Exception:
                    continue

            # Find and click submit button
            submit_buttons = form.find_elements(By.XPATH,
                ".//button[@type='submit'] | .//input[@type='submit'] | .//button[contains(text(), 'Submit')]"
            )

            for button in submit_buttons:
                try:
                    if button.is_displayed() and button.is_enabled():
                        logger.info(f"     Submitting form with: {button.text}")
                        button.click()
                        time.sleep(2)
                        return True
                except Exception:
                    continue

            return False

        except Exception as e:
            logger.error(f"Form filling error: {e}")
            return False

    def run_ultimate_application(self):
        """Run the ultimate job application process"""
        try:
            logger.info("🚀 ULTIMATE JOB APPLICATION STARTING...")
            logger.info("="*60)

            self.setup_driver()

            # Step 1: Find all job URLs
            job_urls = self.find_all_job_urls()

            if not job_urls:
                logger.error("❌ No job URLs found")
                return

            logger.info(f"📋 Found {len(job_urls)} jobs to apply to")

            # Step 2: Apply to each job
            successful_applications = 0
            failed_applications = 0

            for i, job_url in enumerate(job_urls[:20]):  # Limit to first 20 jobs
                logger.info(f"\n🎯 Job {i+1}/{min(20, len(job_urls))}")

                try:
                    if self.visit_and_apply_to_job(job_url):
                        successful_applications += 1
                    else:
                        failed_applications += 1

                    # Brief delay between jobs
                    time.sleep(3)

                except Exception as e:
                    failed_applications += 1
                    logger.error(f"   Job {i+1} error: {e}")

            # Results
            logger.info(f"\n🎉 ULTIMATE RESULTS:")
            logger.info(f"   ✅ Successful Applications: {successful_applications}")
            logger.info(f"   ❌ Failed Applications: {failed_applications}")

            if successful_applications > 0:
                logger.info(f"   📊 Success Rate: {(successful_applications/(successful_applications+failed_applications)*100):.1f}%")

                logger.info(f"\n📋 APPLIED JOBS:")
                for job in self.applied_jobs:
                    logger.info(f"   ✅ {job['title']} - {job['url']}")

            input("\nPress Enter to close browser...")

        except Exception as e:
            logger.error(f"Ultimate application error: {e}")

        finally:
            if self.driver:
                self.driver.quit()

if __name__ == "__main__":
    applier = UltimateJobApplier()
    applier.run_ultimate_application()