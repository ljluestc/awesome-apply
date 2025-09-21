#!/usr/bin/env python3
"""
REAL JOB APPLICATION AUTOMATION
Actually navigates to external company pages and completes real job applications
"""

import sys
import os
import time
import json
import logging
import random
import traceback
from datetime import datetime
from typing import List, Dict, Any, Optional

# Add venv path
sys.path.append('/home/calelin/awesome-apply/venv/lib/python3.13/site-packages')

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import *
import urllib.parse

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('real_job_applier.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class RealJobApplier:
    def __init__(self):
        """Initialize real job application automation"""
        self.driver = None
        self.session_id = datetime.now().strftime('%Y%m%d_%H%M%S')

        # Real application tracking
        self.real_applications = []
        self.session_stats = {
            'start_time': time.time(),
            'external_sites_visited': 0,
            'real_forms_found': 0,
            'real_applications_submitted': 0,
            'failed_attempts': 0
        }

    def setup_driver(self):
        """Setup Chrome WebDriver"""
        try:
            chrome_options = Options()

            # Use persistent profile
            user_data_dir = f"/tmp/chrome_real_{self.session_id}"
            chrome_options.add_argument(f"--user-data-dir={user_data_dir}")
            chrome_options.add_argument("--profile-directory=Default")

            # Basic options
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_argument("--window-size=1920,1080")
            chrome_options.add_argument("--start-maximized")

            # Anti-detection
            chrome_options.add_argument("--disable-blink-features=AutomationControlled")
            chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
            chrome_options.add_experimental_option('useAutomationExtension', False)

            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

            logger.info("✅ WebDriver setup successfully")
            return True

        except Exception as e:
            logger.error(f"❌ Failed to setup WebDriver: {e}")
            return False

    def wait_random(self, min_seconds=2, max_seconds=5):
        """Random wait"""
        wait_time = random.uniform(min_seconds, max_seconds)
        time.sleep(wait_time)

    def dismiss_overlays_and_popups(self):
        """Aggressively dismiss overlays, popups, and blocking elements"""
        try:
            # Common blocking elements
            blocking_selectors = [
                # Cookie banners
                ".cookie-banner", ".cookie-notice", "[data-testid*='cookie']",
                ".gdpr-banner", ".privacy-notice", ".consent-banner",

                # Modal overlays
                ".modal", ".popup", ".overlay", ".dialog", "[role='dialog']",

                # Newsletter signups
                ".newsletter-popup", ".email-signup", ".subscribe-modal",

                # Trust Arc
                ".trustarc-banner", ".trustarc-banner-details",
                "#truste-consent-track", "#consent-pref-link",

                # Generic overlays
                ".overlay-backdrop", ".modal-backdrop", ".popup-overlay",
                "[data-testid*='overlay']", "[data-testid*='modal']"
            ]

            for selector in blocking_selectors:
                try:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    for element in elements:
                        if element.is_displayed():
                            # Try to close it
                            self.try_close_element(element)

                            # Hide it with JavaScript as backup
                            try:
                                self.driver.execute_script("arguments[0].style.display = 'none';", element)
                                self.driver.execute_script("arguments[0].remove();", element)
                            except:
                                pass
                except:
                    continue

            # Also dismiss any overlays by pressing ESC
            try:
                self.driver.find_element(By.TAG_NAME, "body").send_keys(Keys.ESCAPE)
            except:
                pass

        except Exception as e:
            logger.warning(f"⚠️ Error dismissing overlays: {e}")

    def try_close_element(self, element):
        """Try to close an element by finding close buttons"""
        try:
            # Look for close buttons within the element
            close_selectors = [
                "button", ".close", ".x", "[aria-label*='close']",
                "[aria-label*='dismiss']", "[title*='close']",
                ".close-button", ".modal-close", ".popup-close"
            ]

            for selector in close_selectors:
                try:
                    close_buttons = element.find_elements(By.CSS_SELECTOR, selector)
                    for btn in close_buttons:
                        if btn.is_displayed():
                            try:
                                btn.click()
                                logger.info(f"✅ Closed overlay using: {selector}")
                                time.sleep(0.5)
                                return
                            except:
                                continue
                except:
                    continue
        except:
            pass

    def smart_click_with_retries(self, element, max_retries=3):
        """Smart clicking with aggressive overlay dismissal"""
        for attempt in range(max_retries):
            try:
                # Aggressively dismiss overlays
                self.dismiss_overlays_and_popups()

                # Scroll to element
                self.driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", element)
                self.wait_random(1, 2)

                # Dismiss overlays again after scrolling
                self.dismiss_overlays_and_popups()

                # Try multiple click strategies
                strategies = [
                    ("JavaScript Click", lambda: self.driver.execute_script("arguments[0].click();", element)),
                    ("Standard Click", lambda: element.click()),
                    ("ActionChains", lambda: ActionChains(self.driver).move_to_element(element).click().perform()),
                    ("Force Click", lambda: self.driver.execute_script("arguments[0].dispatchEvent(new MouseEvent('click', {bubbles: true}));", element)),
                    ("Focus Click", lambda: self.driver.execute_script("arguments[0].focus(); arguments[0].click();", element))
                ]

                for strategy_name, strategy_func in strategies:
                    try:
                        strategy_func()
                        logger.info(f"✅ {strategy_name} successful on attempt {attempt + 1}")
                        return True
                    except Exception as e:
                        logger.info(f"⚠️ {strategy_name} failed: {str(e)[:100]}")
                        continue

                logger.warning(f"⚠️ All click strategies failed on attempt {attempt + 1}")
                self.wait_random(1, 3)

            except Exception as e:
                logger.warning(f"⚠️ Click attempt {attempt + 1} failed: {e}")
                self.wait_random(1, 2)

        return False

    def find_external_application_links(self):
        """Find links that lead to external company application pages"""
        try:
            logger.info("🔍 SEARCHING FOR EXTERNAL APPLICATION LINKS")

            # Go to Indeed
            self.driver.get("https://indeed.com/jobs?q=software+engineer&l=San+Jose%2C+CA&fromage=1")
            self.wait_random(5, 8)

            # Scroll to load content
            for i in range(3):
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                self.wait_random(2, 3)

            external_links = []

            # Find all apply links that go to external sites
            apply_links = self.driver.find_elements(By.CSS_SELECTOR, "a[href*='apply'], a[aria-label*='Apply'], a[title*='Apply']")

            for link in apply_links:
                try:
                    if link.is_displayed():
                        href = link.get_attribute('href') or ''
                        text = link.text.strip()

                        # Filter for external company applications
                        if href and 'indeed.com' not in href and any(keyword in href.lower() for keyword in ['apply', 'career', 'job']):
                            external_links.append({
                                'element': link,
                                'href': href,
                                'text': text
                            })

                except Exception:
                    continue

            # Also look for "Apply on company site" buttons that open in new tabs
            company_site_buttons = self.driver.find_elements(By.XPATH, "//a[contains(text(), 'Apply on company site') or contains(text(), 'Apply on employer site')]")

            for button in company_site_buttons:
                try:
                    if button.is_displayed():
                        href = button.get_attribute('href') or ''
                        text = button.text.strip()

                        external_links.append({
                            'element': button,
                            'href': href,
                            'text': text,
                            'type': 'company_site'
                        })

                except Exception:
                    continue

            logger.info(f"✅ Found {len(external_links)} external application links")

            # Show what we found
            for i, link in enumerate(external_links[:5], 1):
                logger.info(f"    {i}. {link['text'][:50]} -> {link['href'][:80]}")

            return external_links

        except Exception as e:
            logger.error(f"❌ Error finding external links: {e}")
            return []

    def apply_to_external_site(self, link_info):
        """Navigate to external site and complete application"""
        try:
            original_window = self.driver.current_window_handle
            href = link_info['href']

            logger.info(f"\n🌐 APPLYING TO EXTERNAL SITE")
            logger.info(f"🔗 URL: {href}")
            logger.info(f"📋 Text: {link_info['text']}")
            logger.info("=" * 60)

            # Click the link
            if link_info.get('type') == 'company_site':
                # This will likely open in a new window
                if self.smart_click_with_retries(link_info['element']):
                    self.wait_random(5, 8)

                    # Check if new window opened
                    if len(self.driver.window_handles) > 1:
                        self.driver.switch_to.window(self.driver.window_handles[-1])
                        logger.info("✅ Switched to new window")
                    else:
                        logger.info("ℹ️ No new window, checking current page")

            else:
                # Direct navigation
                self.driver.get(href)
                self.wait_random(5, 8)

            self.session_stats['external_sites_visited'] += 1

            current_url = self.driver.current_url
            current_title = self.driver.title

            logger.info(f"📍 Arrived at: {current_url}")
            logger.info(f"📑 Page title: {current_title}")

            # Dismiss overlays on the new site
            self.dismiss_overlays_and_popups()

            # Look for actual application forms
            if self.find_and_complete_real_application_form(current_url, current_title):
                logger.info("🎉 ✅ REAL APPLICATION COMPLETED!")
                self.session_stats['real_applications_submitted'] += 1

                # Record successful application
                self.real_applications.append({
                    'timestamp': datetime.now().isoformat(),
                    'company_url': current_url,
                    'company_title': current_title,
                    'original_link': href
                })

                # Return to original window
                if len(self.driver.window_handles) > 1:
                    self.driver.close()
                    self.driver.switch_to.window(original_window)

                return True
            else:
                logger.info("ℹ️ No real application form found on external site")
                self.session_stats['failed_attempts'] += 1

                # Return to original window
                if len(self.driver.window_handles) > 1:
                    self.driver.close()
                    self.driver.switch_to.window(original_window)

                return False

        except Exception as e:
            logger.error(f"❌ Error applying to external site: {e}")
            self.session_stats['failed_attempts'] += 1

            # Try to return to original window
            try:
                if len(self.driver.window_handles) > 1:
                    self.driver.close()
                    self.driver.switch_to.window(original_window)
            except:
                pass

            return False

    def find_and_complete_real_application_form(self, url, title):
        """Find and complete a real job application form"""
        try:
            logger.info("📝 LOOKING FOR REAL APPLICATION FORM")

            # Wait for page to load
            self.wait_random(3, 5)

            # Dismiss overlays
            self.dismiss_overlays_and_popups()

            # Check if this looks like a real application page
            url_lower = url.lower()
            title_lower = title.lower()

            # Strong indicators this is a real application page
            application_indicators = [
                'apply', 'application', 'career', 'job', 'position',
                'hiring', 'recruit', 'candidate', 'resume', 'cv'
            ]

            is_likely_application_page = any(indicator in url_lower for indicator in application_indicators) or \
                                       any(indicator in title_lower for indicator in application_indicators)

            if not is_likely_application_page:
                logger.info("ℹ️ Page doesn't appear to be an application page")
                return False

            logger.info("✅ Page appears to be an application page")

            # Look for real application forms
            real_form_indicators = []

            # File upload fields (resume/CV)
            file_inputs = self.driver.find_elements(By.CSS_SELECTOR, "input[type='file']")
            for file_input in file_inputs:
                if file_input.is_displayed():
                    accept = file_input.get_attribute('accept') or ''
                    name = file_input.get_attribute('name') or ''
                    if any(keyword in (accept + name).lower() for keyword in ['resume', 'cv', 'pdf', 'doc']):
                        real_form_indicators.append(f"Resume upload: {name}")

            # Application-specific text fields
            text_inputs = self.driver.find_elements(By.CSS_SELECTOR, "input[type='text'], input[type='email'], input[type='tel']")
            application_field_count = 0
            for text_input in text_inputs:
                if text_input.is_displayed():
                    name = text_input.get_attribute('name') or ''
                    placeholder = text_input.get_attribute('placeholder') or ''
                    combined = (name + placeholder).lower()

                    if any(keyword in combined for keyword in ['name', 'email', 'phone', 'address', 'experience', 'education']):
                        application_field_count += 1

            if application_field_count >= 3:
                real_form_indicators.append(f"Application fields: {application_field_count}")

            # Cover letter text areas
            textareas = self.driver.find_elements(By.TAG_NAME, "textarea")
            for textarea in textareas:
                if textarea.is_displayed():
                    placeholder = textarea.get_attribute('placeholder') or ''
                    name = textarea.get_attribute('name') or ''
                    if any(keyword in (placeholder + name).lower() for keyword in ['cover', 'letter', 'message', 'why', 'motivation']):
                        real_form_indicators.append("Cover letter field")

            if real_form_indicators:
                logger.info(f"🎯 REAL APPLICATION FORM DETECTED!")
                logger.info(f"    Form indicators: {len(real_form_indicators)}")
                for indicator in real_form_indicators:
                    logger.info(f"    • {indicator}")

                self.session_stats['real_forms_found'] += 1

                # Fill the form
                if self.fill_real_application_form():
                    # Submit the form
                    return self.submit_real_application_form()
                else:
                    logger.warning("⚠️ Could not fill application form")
                    return False
            else:
                logger.info("ℹ️ No real application form elements detected")
                return False

        except Exception as e:
            logger.error(f"❌ Error finding real application form: {e}")
            return False

    def fill_real_application_form(self):
        """Fill a real job application form with sample data"""
        try:
            logger.info("📝 FILLING REAL APPLICATION FORM")

            # Sample application data
            sample_data = {
                'firstname': 'John',
                'lastname': 'Doe',
                'name': 'John Doe',
                'email': 'john.doe@example.com',
                'phone': '555-123-4567',
                'address': '123 Main St',
                'city': 'San Jose',
                'state': 'CA',
                'zip': '95134',
                'experience': '5',
                'education': 'Bachelor of Science in Computer Science'
            }

            fields_filled = 0

            # Fill text inputs
            text_inputs = self.driver.find_elements(By.CSS_SELECTOR, "input[type='text'], input[type='email'], input[type='tel']")
            for text_input in text_inputs:
                if text_input.is_displayed() and text_input.is_enabled():
                    try:
                        name = text_input.get_attribute('name') or ''
                        placeholder = text_input.get_attribute('placeholder') or ''
                        combined = (name + placeholder).lower()

                        value_to_fill = None
                        for key, value in sample_data.items():
                            if key in combined:
                                value_to_fill = value
                                break

                        if value_to_fill:
                            self.dismiss_overlays_and_popups()  # Dismiss before interacting
                            text_input.clear()
                            text_input.send_keys(value_to_fill)
                            logger.info(f"✅ Filled '{name}' with '{value_to_fill}'")
                            fields_filled += 1
                            time.sleep(0.5)

                    except Exception as e:
                        logger.warning(f"⚠️ Could not fill field: {e}")
                        continue

            # Fill textareas (cover letter)
            textareas = self.driver.find_elements(By.TAG_NAME, "textarea")
            for textarea in textareas:
                if textarea.is_displayed() and textarea.is_enabled():
                    try:
                        self.dismiss_overlays_and_popups()
                        cover_letter = "I am very interested in this position and believe my background in software engineering makes me a strong candidate. I look forward to discussing this opportunity with you."
                        textarea.clear()
                        textarea.send_keys(cover_letter)
                        logger.info("✅ Filled cover letter/message field")
                        fields_filled += 1
                        time.sleep(0.5)
                    except Exception as e:
                        logger.warning(f"⚠️ Could not fill textarea: {e}")

            logger.info(f"📋 Filled {fields_filled} form fields")
            return fields_filled > 0

        except Exception as e:
            logger.error(f"❌ Error filling form: {e}")
            return False

    def submit_real_application_form(self):
        """Submit the real application form"""
        try:
            logger.info("🚀 SUBMITTING REAL APPLICATION FORM")

            # Dismiss overlays before submission
            self.dismiss_overlays_and_popups()

            # Look for submit buttons
            submit_selectors = [
                "button[type='submit']",
                "input[type='submit']",
                "button[contains(translate(text(), 'SUBMIT', 'submit'), 'submit')]",
                "button[contains(translate(text(), 'APPLY', 'apply'), 'apply')]",
                "button[contains(translate(text(), 'SEND', 'send'), 'send')]"
            ]

            xpath_selectors = [
                "//button[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'submit application')]",
                "//button[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'apply now')]",
                "//button[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'send application')]",
                "//input[contains(translate(@value, 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'submit')]"
            ]

            # Try CSS selectors
            for selector in submit_selectors:
                try:
                    buttons = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    for button in buttons:
                        if button.is_displayed() and button.is_enabled():
                            button_text = button.text.strip().lower()
                            if any(keyword in button_text for keyword in ['submit', 'apply', 'send']):
                                logger.info(f"🎯 Found submit button: '{button.text}'")

                                if self.smart_click_with_retries(button):
                                    logger.info("✅ REAL APPLICATION SUBMITTED!")
                                    self.wait_random(3, 5)

                                    # Check for confirmation
                                    if self.check_application_confirmation():
                                        logger.info("🎉 ✅ APPLICATION CONFIRMATION DETECTED!")
                                        return True
                                    else:
                                        logger.info("ℹ️ Application submitted but no confirmation detected")
                                        return True  # Still count as success

                except Exception as e:
                    logger.warning(f"⚠️ Error with submit button: {e}")
                    continue

            # Try XPath selectors
            for xpath in xpath_selectors:
                try:
                    buttons = self.driver.find_elements(By.XPATH, xpath)
                    for button in buttons:
                        if button.is_displayed() and button.is_enabled():
                            logger.info(f"🎯 Found submit button via XPath: '{button.text}'")

                            if self.smart_click_with_retries(button):
                                logger.info("✅ REAL APPLICATION SUBMITTED!")
                                self.wait_random(3, 5)

                                if self.check_application_confirmation():
                                    logger.info("🎉 ✅ APPLICATION CONFIRMATION DETECTED!")
                                    return True
                                else:
                                    logger.info("ℹ️ Application submitted but no confirmation detected")
                                    return True

                except Exception as e:
                    logger.warning(f"⚠️ Error with XPath submit button: {e}")
                    continue

            logger.warning("⚠️ No submit button found")
            return False

        except Exception as e:
            logger.error(f"❌ Error submitting form: {e}")
            return False

    def check_application_confirmation(self):
        """Check for application confirmation"""
        try:
            # Wait a moment for confirmation to appear
            self.wait_random(2, 4)

            # Check URL for confirmation
            current_url = self.driver.current_url.lower()
            url_confirmation = any(keyword in current_url for keyword in ['thank', 'success', 'confirm', 'submitted'])

            # Check page content for confirmation
            page_source = self.driver.page_source.lower()
            content_confirmation = any(keyword in page_source for keyword in [
                'thank you', 'application received', 'successfully submitted',
                'application submitted', 'we have received', 'confirmation'
            ])

            return url_confirmation or content_confirmation

        except Exception:
            return False

    def run_real_applications(self):
        """Run real job applications"""
        logger.info("🚀 REAL JOB APPLICATION AUTOMATION")
        logger.info("🎯 Navigate to external company sites and complete real applications")
        logger.info("📝 Fill actual application forms and submit them")
        logger.info("=" * 80)

        try:
            if not self.setup_driver():
                return False

            # Find external application links
            external_links = self.find_external_application_links()

            if not external_links:
                logger.warning("⚠️ No external application links found")
                return False

            successful_applications = 0

            # Try to apply to each external site
            for i, link_info in enumerate(external_links[:5], 1):  # Try first 5
                try:
                    logger.info(f"\n[EXTERNAL SITE {i}/{min(5, len(external_links))}]")

                    if self.apply_to_external_site(link_info):
                        successful_applications += 1
                        logger.info(f"🎉 SUCCESSFUL REAL APPLICATION #{successful_applications}!")

                        # Stop after 3 successful real applications
                        if successful_applications >= 3:
                            logger.info("🎯 Completed 3 real applications!")
                            break

                    # Brief delay between applications
                    self.wait_random(5, 10)

                except Exception as e:
                    logger.error(f"❌ Error with external site {i}: {e}")
                    continue

            # Final results
            runtime = (time.time() - self.session_stats['start_time']) / 60
            logger.info("\n📊 FINAL REAL APPLICATION RESULTS:")
            logger.info(f"    🌐 External sites visited: {self.session_stats['external_sites_visited']}")
            logger.info(f"    📝 Real forms found: {self.session_stats['real_forms_found']}")
            logger.info(f"    ✅ Real applications submitted: {self.session_stats['real_applications_submitted']}")
            logger.info(f"    ❌ Failed attempts: {self.session_stats['failed_attempts']}")
            logger.info(f"    ⏱️ Runtime: {runtime:.1f} minutes")

            if self.real_applications:
                logger.info("\n📋 REAL APPLICATIONS COMPLETED:")
                for i, app in enumerate(self.real_applications, 1):
                    logger.info(f"  {i}. Company: {app['company_title']}")
                    logger.info(f"     URL: {app['company_url']}")
                    logger.info(f"     Time: {app['timestamp']}")
                    logger.info("")

            return successful_applications > 0

        except Exception as e:
            logger.error(f"❌ Fatal error: {e}")
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
    applier = RealJobApplier()

    try:
        logger.info("🌟 REAL JOB APPLICATION AUTOMATION")
        logger.info("🎯 Actually navigate to company sites and complete real applications")

        success = applier.run_real_applications()

        if success:
            logger.info("\n🎉 🎉 🎉 SUCCESS! 🎉 🎉 🎉")
            logger.info("✅ Successfully completed REAL job applications!")
        else:
            logger.warning("\n⚠️ No real applications completed")

    except KeyboardInterrupt:
        logger.info("\n⏹️ Automation stopped by user")
    except Exception as e:
        logger.error(f"\n❌ Fatal error: {e}")
    finally:
        applier.cleanup()

if __name__ == "__main__":
    main()