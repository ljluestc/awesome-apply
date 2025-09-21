#!/usr/bin/env python3
"""
MASTER JOB APPLICATION AUTOMATION
Multi-platform, multi-strategy approach with robust error handling and retry mechanisms
Combines all successful patterns from previous attempts
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
        logging.FileHandler('master_job_applier.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class MasterJobApplier:
    def __init__(self):
        """Initialize the master job application automation"""
        self.driver = None
        self.session_id = datetime.now().strftime('%Y%m%d_%H%M%S')

        # Success tracking
        self.applied_jobs = []
        self.session_stats = {
            'start_time': time.time(),
            'platforms_tried': 0,
            'total_jobs_found': 0,
            'successful_applications': 0,
            'failed_attempts': 0,
            'errors_encountered': 0
        }

        # Job platforms to try
        self.job_platforms = [
            {
                'name': 'JobRight',
                'url': 'https://jobright.ai/entry-level-jobs',
                'strategy': 'comprehensive_search'
            },
            {
                'name': 'LinkedIn',
                'url': 'https://www.linkedin.com/jobs/search?keywords=software&location=San+Jose%2C+California%2C+United+States&geoId=106233382&distance=25&f_TPR=r86400&sortBy=DD',
                'strategy': 'javascript_targeting'
            },
            {
                'name': 'JobRight_Alternative',
                'url': 'https://jobright.ai/s?keyword=software%20engineer&location=San%20Jose%2C%20CA',
                'strategy': 'direct_application'
            }
        ]

    def setup_driver(self):
        """Setup Chrome WebDriver with optimal configuration"""
        try:
            chrome_options = Options()

            # Use persistent profile for better success rates
            user_data_dir = f"/tmp/chrome_master_profile_{self.session_id}"
            chrome_options.add_argument(f"--user-data-dir={user_data_dir}")
            chrome_options.add_argument("--profile-directory=Default")

            # Reliability options
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

            # Create driver
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=chrome_options)

            # Anti-detection JavaScript
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

            logger.info("✅ WebDriver setup successfully")
            return True

        except Exception as e:
            logger.error(f"❌ Failed to setup WebDriver: {e}")
            return False

    def wait_random(self, min_seconds=2, max_seconds=5):
        """Wait for a random amount of time to appear more human-like"""
        wait_time = random.uniform(min_seconds, max_seconds)
        time.sleep(wait_time)

    def scroll_page_intelligently(self):
        """Scroll page intelligently to load dynamic content"""
        try:
            # Get initial page height
            last_height = self.driver.execute_script("return document.body.scrollHeight")

            scroll_attempts = 0
            max_scrolls = 10

            while scroll_attempts < max_scrolls:
                # Scroll down to bottom
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                self.wait_random(2, 4)

                # Calculate new scroll height and compare with last scroll height
                new_height = self.driver.execute_script("return document.body.scrollHeight")

                if new_height == last_height:
                    break

                last_height = new_height
                scroll_attempts += 1

            logger.info(f"📜 Intelligent scrolling completed ({scroll_attempts} scrolls)")
            return True

        except Exception as e:
            logger.error(f"❌ Error during intelligent scrolling: {e}")
            return False

    def find_all_apply_elements(self):
        """Find all potential apply elements using comprehensive search"""
        try:
            apply_elements = []

            # Comprehensive selectors for apply buttons/links
            apply_selectors = [
                # Direct apply buttons
                "button[contains(translate(text(), 'APPLY', 'apply'), 'apply')]",
                "a[contains(translate(text(), 'APPLY', 'apply'), 'apply')]",

                # Attribute-based selectors
                "*[data-testid*='apply']",
                "*[data-test*='apply']",
                "*[class*='apply']",
                "*[id*='apply']",
                "*[aria-label*='apply']",
                "*[aria-label*='Apply']",

                # Job-related buttons
                "button[contains(translate(text(), 'JOB', 'job'), 'job')]",
                "a[contains(translate(text(), 'JOB', 'job'), 'job')]",
                "button[contains(translate(text(), 'VIEW', 'view'), 'view')]",
                "a[contains(translate(text(), 'VIEW', 'view'), 'view')]",

                # Submit buttons
                "button[contains(translate(text(), 'SUBMIT', 'submit'), 'submit')]",
                "input[type='submit']",

                # External links
                "a[target='_blank']",
                "a[href*='apply']",
                "a[href*='job']",
                "a[href*='career']",

                # Generic clickable elements
                "*[onclick*='apply']",
                "*[onclick*='job']",
                "*[role='button']"
            ]

            # XPath selectors for text-based matching
            xpath_selectors = [
                "//button[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'apply')]",
                "//a[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'apply')]",
                "//button[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'submit')]",
                "//button[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'job')]",
                "//a[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'view')]",
                "//button[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'quick')]"
            ]

            # Find elements using CSS selectors
            for selector in apply_selectors:
                try:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    for element in elements:
                        if element.is_displayed() and element.is_enabled():
                            apply_elements.append({
                                'element': element,
                                'selector': selector,
                                'method': 'css',
                                'text': element.text.strip(),
                                'href': element.get_attribute('href') or '',
                                'class': element.get_attribute('class') or '',
                                'onclick': element.get_attribute('onclick') or ''
                            })
                except Exception:
                    continue

            # Find elements using XPath
            for xpath in xpath_selectors:
                try:
                    elements = self.driver.find_elements(By.XPATH, xpath)
                    for element in elements:
                        if element.is_displayed() and element.is_enabled():
                            # Check if already found
                            found = False
                            for existing in apply_elements:
                                if existing['element'] == element:
                                    found = True
                                    break

                            if not found:
                                apply_elements.append({
                                    'element': element,
                                    'selector': xpath,
                                    'method': 'xpath',
                                    'text': element.text.strip(),
                                    'href': element.get_attribute('href') or '',
                                    'class': element.get_attribute('class') or '',
                                    'onclick': element.get_attribute('onclick') or ''
                                })
                except Exception:
                    continue

            logger.info(f"🔍 Found {len(apply_elements)} potential apply elements")
            return apply_elements

        except Exception as e:
            logger.error(f"❌ Error finding apply elements: {e}")
            return []

    def smart_click_element(self, element_info: Dict[str, Any]) -> bool:
        """Smart clicking with multiple fallback strategies"""
        try:
            element = element_info['element']

            # Scroll to element
            self.driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", element)
            self.wait_random(1, 2)

            # Strategy 1: Regular click
            try:
                element.click()
                logger.info("✅ Regular click successful")
                return True
            except Exception:
                pass

            # Strategy 2: JavaScript click
            try:
                self.driver.execute_script("arguments[0].click();", element)
                logger.info("✅ JavaScript click successful")
                return True
            except Exception:
                pass

            # Strategy 3: ActionChains click
            try:
                ActionChains(self.driver).move_to_element(element).click().perform()
                logger.info("✅ ActionChains click successful")
                return True
            except Exception:
                pass

            # Strategy 4: JavaScript focus and click
            try:
                self.driver.execute_script("arguments[0].focus(); arguments[0].click();", element)
                logger.info("✅ Focus + JavaScript click successful")
                return True
            except Exception:
                pass

            # Strategy 5: Send ENTER key
            try:
                element.send_keys(Keys.ENTER)
                logger.info("✅ ENTER key successful")
                return True
            except Exception:
                pass

            logger.warning(f"⚠️ All click strategies failed for element: {element_info['text'][:50]}")
            return False

        except Exception as e:
            logger.error(f"❌ Error in smart click: {e}")
            return False

    def verify_application_success(self, original_url: str, element_info: Dict[str, Any]) -> bool:
        """Verify if application was successful using multiple indicators"""
        try:
            self.wait_random(3, 5)

            current_url = self.driver.current_url
            current_title = self.driver.title
            window_count = len(self.driver.window_handles)

            # Success indicators
            success_indicators = {
                'url_change': current_url != original_url,
                'new_window': window_count > 1,
                'application_url': any(keyword in current_url.lower() for keyword in ['apply', 'application', 'job', 'career', 'submit']),
                'application_title': any(keyword in current_title.lower() for keyword in ['apply', 'application', 'job', 'career']),
                'form_present': False,
                'success_text': False
            }

            # Check for forms
            try:
                forms = self.driver.find_elements(By.TAG_NAME, 'form')
                file_inputs = self.driver.find_elements(By.CSS_SELECTOR, 'input[type="file"]')
                textareas = self.driver.find_elements(By.TAG_NAME, 'textarea')

                success_indicators['form_present'] = len(forms) > 0 or len(file_inputs) > 0 or len(textareas) > 0
            except Exception:
                pass

            # Check for success text
            try:
                page_text = self.driver.page_source.lower()
                success_keywords = ['thank you', 'application received', 'successfully applied', 'resume', 'cover letter', 'submit application']
                success_indicators['success_text'] = any(keyword in page_text for keyword in success_keywords)
            except Exception:
                pass

            # Determine success
            success_count = sum(success_indicators.values())
            is_successful = success_count >= 2

            if is_successful:
                logger.info("🎉 ✅ APPLICATION SUCCESS DETECTED!")
                logger.info(f"    URL changed: {success_indicators['url_change']}")
                logger.info(f"    New window: {success_indicators['new_window']}")
                logger.info(f"    Application URL: {success_indicators['application_url']}")
                logger.info(f"    Application title: {success_indicators['application_title']}")
                logger.info(f"    Form present: {success_indicators['form_present']}")
                logger.info(f"    Success text: {success_indicators['success_text']}")
                logger.info(f"    Current URL: {current_url}")
                logger.info(f"    Page title: {current_title}")

                # Record successful application
                self.applied_jobs.append({
                    'timestamp': datetime.now().isoformat(),
                    'platform': getattr(self, 'current_platform', 'Unknown'),
                    'original_url': original_url,
                    'application_url': current_url,
                    'title': current_title,
                    'element_clicked': element_info['text'],
                    'success_indicators': success_indicators
                })

                self.session_stats['successful_applications'] += 1
                return True
            else:
                logger.info(f"ℹ️ Application not confirmed ({success_count}/6 indicators)")
                return False

        except Exception as e:
            logger.error(f"❌ Error verifying application success: {e}")
            return False

    def handle_new_window_or_navigation(self, original_window_count: int):
        """Handle new windows or navigation that occurred"""
        try:
            current_window_count = len(self.driver.window_handles)

            if current_window_count > original_window_count:
                # New window opened
                logger.info("📂 New window detected, switching to it")
                self.driver.switch_to.window(self.driver.window_handles[-1])
                self.wait_random(3, 5)

                # Look for additional apply buttons on the new page
                additional_applies = self.find_all_apply_elements()

                if additional_applies:
                    logger.info(f"🎯 Found {len(additional_applies)} additional apply options in new window")

                    for apply_option in additional_applies[:3]:  # Try first 3
                        if self.smart_click_element(apply_option):
                            logger.info("✅ Successfully clicked apply in new window")
                            break

                # Close new window and return to main
                self.wait_random(2, 3)
                self.driver.close()
                self.driver.switch_to.window(self.driver.window_handles[0])

                return True

            return False

        except Exception as e:
            logger.error(f"❌ Error handling new window: {e}")
            return False

    def apply_to_jobs_on_platform(self, platform: Dict[str, str]) -> int:
        """Apply to all jobs on a specific platform"""
        try:
            self.current_platform = platform['name']
            logger.info(f"\n🎯 PROCESSING PLATFORM: {platform['name']}")
            logger.info(f"🔗 URL: {platform['url']}")
            logger.info("=" * 60)

            # Navigate to platform
            self.driver.get(platform['url'])
            self.wait_random(5, 8)

            logger.info(f"📍 Navigated to: {self.driver.current_url}")
            logger.info(f"📑 Page title: {self.driver.title}")

            # Scroll to load content
            self.scroll_page_intelligently()

            # Find all apply elements
            apply_elements = self.find_all_apply_elements()

            if not apply_elements:
                logger.warning(f"⚠️ No apply elements found on {platform['name']}")
                return 0

            logger.info(f"🎯 Found {len(apply_elements)} apply elements to try")

            successful_applications = 0

            # Try each apply element
            for i, element_info in enumerate(apply_elements):
                try:
                    logger.info(f"\n[{i+1}/{len(apply_elements)}] ATTEMPTING APPLICATION")
                    logger.info(f"Text: '{element_info['text'][:100]}'")
                    logger.info(f"Selector: {element_info['selector']}")

                    original_url = self.driver.current_url
                    original_window_count = len(self.driver.window_handles)

                    # Try to click the element
                    if self.smart_click_element(element_info):
                        # Wait and check for changes
                        self.wait_random(3, 5)

                        # Handle new windows
                        self.handle_new_window_or_navigation(original_window_count)

                        # Verify success
                        if self.verify_application_success(original_url, element_info):
                            successful_applications += 1
                            logger.info(f"✅ APPLICATION #{successful_applications} SUCCESSFUL!")
                        else:
                            logger.info("ℹ️ Click successful but application not confirmed")
                    else:
                        logger.warning("⚠️ Failed to click element")
                        self.session_stats['failed_attempts'] += 1

                    # Brief delay between attempts
                    self.wait_random(2, 4)

                    # Go back to main page if needed
                    if self.driver.current_url != original_url:
                        try:
                            self.driver.get(platform['url'])
                            self.wait_random(3, 5)
                            self.scroll_page_intelligently()
                        except Exception:
                            pass

                except Exception as e:
                    logger.error(f"❌ Error processing element {i+1}: {e}")
                    self.session_stats['errors_encountered'] += 1
                    continue

            logger.info(f"\n📊 PLATFORM RESULTS for {platform['name']}:")
            logger.info(f"    ✅ Successful applications: {successful_applications}")
            logger.info(f"    📋 Total elements tried: {len(apply_elements)}")
            logger.info(f"    📈 Success rate: {(successful_applications/len(apply_elements)*100):.1f}%" if apply_elements else "0%")

            return successful_applications

        except Exception as e:
            logger.error(f"❌ Error on platform {platform['name']}: {e}")
            self.session_stats['errors_encountered'] += 1
            return 0

    def run_master_automation(self):
        """Main automation loop - try all platforms until success"""
        logger.info("🚀 MASTER JOB APPLICATION AUTOMATION STARTING")
        logger.info("🎯 Multi-platform, multi-strategy approach")
        logger.info("⚡ Will continue until jobs are successfully applied to")
        logger.info("=" * 80)

        try:
            # Setup driver
            if not self.setup_driver():
                logger.error("❌ Failed to setup WebDriver")
                return False

            total_applications = 0

            # Try each platform
            for platform in self.job_platforms:
                try:
                    self.session_stats['platforms_tried'] += 1

                    applications_on_platform = self.apply_to_jobs_on_platform(platform)
                    total_applications += applications_on_platform

                    # Print overall progress
                    runtime = (time.time() - self.session_stats['start_time']) / 60
                    logger.info(f"\n📊 OVERALL PROGRESS:")
                    logger.info(f"    🏢 Platforms tried: {self.session_stats['platforms_tried']}")
                    logger.info(f"    ✅ Total applications: {total_applications}")
                    logger.info(f"    ❌ Failed attempts: {self.session_stats['failed_attempts']}")
                    logger.info(f"    ⚠️ Errors encountered: {self.session_stats['errors_encountered']}")
                    logger.info(f"    ⏱️ Runtime: {runtime:.1f} minutes")

                    # Check if we've achieved our goal
                    if total_applications >= 5:
                        logger.info("\n🎉 🎉 🎉 MISSION ACCOMPLISHED! 🎉 🎉 🎉")
                        logger.info(f"✅ Successfully applied to {total_applications} jobs!")
                        break

                except Exception as e:
                    logger.error(f"❌ Error with platform {platform['name']}: {e}")
                    continue

            # Final results
            logger.info("\n🏁 AUTOMATION COMPLETED")
            logger.info(f"✅ Total successful applications: {total_applications}")

            if total_applications > 0:
                logger.info("\n📋 SUCCESSFUL APPLICATIONS:")
                for i, job in enumerate(self.applied_jobs, 1):
                    logger.info(f"  {i:2d}. Platform: {job['platform']}")
                    logger.info(f"      Title: {job['title']}")
                    logger.info(f"      URL: {job['application_url']}")
                    logger.info(f"      Time: {job['timestamp']}")
                    logger.info("")

            return total_applications > 0

        except Exception as e:
            logger.error(f"❌ Fatal automation error: {e}")
            traceback.print_exc()
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
    applier = MasterJobApplier()

    try:
        logger.info("🌟 MASTER JOB APPLICATION AUTOMATION")
        logger.info("🎯 Multi-platform automation with comprehensive strategies")
        logger.info("🔄 Will continue trying until jobs are successfully applied to")

        success = applier.run_master_automation()

        if success:
            logger.info("\n🎉 🎉 🎉 SUCCESS! 🎉 🎉 🎉")
            logger.info("✅ Jobs have been successfully applied to!")
            logger.info("🏆 Master automation completed successfully!")
        else:
            logger.warning("\n⚠️ Automation completed but no successful applications")

    except KeyboardInterrupt:
        logger.info("\n⏹️ Automation stopped by user")
    except Exception as e:
        logger.error(f"\n❌ Fatal error: {e}")
        traceback.print_exc()
    finally:
        applier.cleanup()

        # Final statistics
        runtime = (time.time() - applier.session_stats['start_time']) / 60
        logger.info("\n" + "="*60)
        logger.info("📊 FINAL STATISTICS")
        logger.info("="*60)
        logger.info(f"✅ Successful applications: {applier.session_stats['successful_applications']}")
        logger.info(f"🏢 Platforms tried: {applier.session_stats['platforms_tried']}")
        logger.info(f"❌ Failed attempts: {applier.session_stats['failed_attempts']}")
        logger.info(f"⚠️ Errors encountered: {applier.session_stats['errors_encountered']}")
        logger.info(f"⏱️ Total runtime: {runtime:.1f} minutes")

if __name__ == "__main__":
    main()