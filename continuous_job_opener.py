#!/usr/bin/env python3
"""
CONTINUOUS JOB APPLICATION AUTOMATION
Shows live job applications and doesn't stop until demonstrating actual job applications
Enhanced targeting for real job postings with apply buttons
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

# Configure logging for live output
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('continuous_job_opener.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class ContinuousJobOpener:
    def __init__(self):
        """Initialize continuous job application automation"""
        self.driver = None
        self.session_id = datetime.now().strftime('%Y%m%d_%H%M%S')

        # Live application tracking
        self.live_applications = []
        self.confirmed_applications = []
        self.session_stats = {
            'start_time': time.time(),
            'platforms_processed': 0,
            'total_apply_attempts': 0,
            'confirmed_applications': 0,
            'form_submissions': 0,
            'external_applications': 0,
            'restart_count': 0
        }

        # Enhanced job platforms with better targeting
        self.job_platforms = [
            {
                'name': 'Indeed_RecentJobs',
                'url': 'https://indeed.com/jobs?q=software+engineer&l=San+Jose%2C+CA&fromage=1&sort=date',
                'apply_indicators': ['Apply now', 'Easy Apply', 'Apply on company site', 'Apply'],
                'job_selectors': ['.jobsearch-SerpJobCard', '.job_seen_beacon', '.result']
            },
            {
                'name': 'LinkedIn_EasyApply',
                'url': 'https://www.linkedin.com/jobs/search?keywords=software%20engineer&location=San%20Jose%2C%20CA&f_LF=f_AL',
                'apply_indicators': ['Easy Apply', 'Apply', 'Apply now'],
                'job_selectors': ['.job-search-card', '.jobs-search-results__list-item']
            },
            {
                'name': 'JobRight_LiveJobs',
                'url': 'https://jobright.ai/s?keyword=software%20engineer&location=San%20Jose%2C%20CA&sort=date',
                'apply_indicators': ['Apply', 'Apply Now', 'Quick Apply', 'Submit Application'],
                'job_selectors': ['.job-card', '.position-card', '.opportunity-card']
            },
            {
                'name': 'Glassdoor_Jobs',
                'url': 'https://www.glassdoor.com/Job/san-jose-software-engineer-jobs-SRCH_IL.0,8_IC1147401_KO9,26.htm',
                'apply_indicators': ['Apply Now', 'Easy Apply', 'Apply'],
                'job_selectors': ['.react-job-listing', '.jobListing']
            },
            {
                'name': 'AngelList_Startups',
                'url': 'https://angel.co/jobs?job_types%5B%5D=full-time&locations%5B%5D=1688-san-jose',
                'apply_indicators': ['Apply', 'Apply Now', 'Join'],
                'job_selectors': ['.job-listing', '.startup-job']
            }
        ]

    def setup_driver(self):
        """Setup Chrome WebDriver with enhanced configuration"""
        try:
            chrome_options = Options()

            # Use persistent profile for better authentication
            user_data_dir = f"/tmp/chrome_continuous_{self.session_id}"
            chrome_options.add_argument(f"--user-data-dir={user_data_dir}")
            chrome_options.add_argument("--profile-directory=Default")

            # Optimization for speed and reliability
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_argument("--window-size=1920,1080")
            chrome_options.add_argument("--start-maximized")

            # Enhanced anti-detection
            chrome_options.add_argument("--disable-blink-features=AutomationControlled")
            chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
            chrome_options.add_experimental_option('useAutomationExtension', False)
            chrome_options.add_argument("--user-agent=Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")

            # Create driver
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=chrome_options)

            # Enhanced anti-detection
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

            logger.info("✅ WebDriver setup successfully for continuous operation")
            return True

        except Exception as e:
            logger.error(f"❌ Failed to setup WebDriver: {e}")
            return False

    def wait_human_like(self, min_seconds=2, max_seconds=6):
        """Human-like random waiting"""
        wait_time = random.uniform(min_seconds, max_seconds)
        time.sleep(wait_time)

    def comprehensive_scroll_and_load(self):
        """Comprehensive scrolling to load all dynamic content"""
        try:
            logger.info("📜 Loading all job content...")

            # Initial scroll to trigger loading
            for i in range(8):
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                self.wait_human_like(2, 4)

                # Also scroll up a bit to trigger additional loading
                if i % 2 == 0:
                    self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight * 0.7);")
                    self.wait_human_like(1, 2)

            # Scroll back to top
            self.driver.execute_script("window.scrollTo(0, 0);")
            self.wait_human_like(2, 3)

            logger.info("✅ Content loading completed")
            return True

        except Exception as e:
            logger.error(f"❌ Error during content loading: {e}")
            return False

    def find_actual_job_postings_with_apply(self, platform: Dict[str, Any]):
        """Find actual job postings that have apply buttons/links"""
        try:
            logger.info(f"🔍 SEARCHING FOR JOBS WITH APPLY BUTTONS ON {platform['name']}")

            job_opportunities = []

            # First, find job containers
            all_job_containers = []

            for selector in platform['job_selectors']:
                try:
                    containers = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    all_job_containers.extend(containers)
                    if containers:
                        logger.info(f"    Found {len(containers)} containers with selector: {selector}")
                except Exception:
                    continue

            logger.info(f"📋 Found {len(all_job_containers)} total job containers")

            # Now find apply buttons/links in each container or globally
            apply_selectors = [
                # Direct apply buttons
                "button[contains(translate(text(), 'APPLY', 'apply'), 'apply')]",
                "a[contains(translate(text(), 'APPLY', 'apply'), 'apply')]",
                "input[value*='Apply' i]",

                # Specific platform selectors
                "button[data-jk]",  # Indeed
                ".jobs-apply-button",  # LinkedIn
                "button[aria-label*='Apply' i]",
                "a[aria-label*='Apply' i]",

                # Class-based selectors
                "*[class*='apply' i]",
                "*[class*='easy-apply' i]",
                "*[class*='quick-apply' i]",

                # Data attribute selectors
                "*[data-testid*='apply' i]",
                "*[data-test*='apply' i]",
                "*[data-control-name*='apply' i]",

                # Form submit buttons that might be applications
                "button[type='submit']",
                "input[type='submit']",

                # Generic job application patterns
                "button[title*='Apply' i]",
                "a[title*='Apply' i]",
                "button[name*='apply' i]",
                "a[href*='apply' i]"
            ]

            # XPath selectors for text-based matching
            xpath_selectors = [
                "//button[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'apply')]",
                "//a[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'apply')]",
                "//button[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'submit')]",
                "//input[contains(translate(@value, 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'apply')]",
                "//span[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'apply')]/parent::*",
                "//div[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'easy apply')]/parent::*"
            ]

            # Find all apply elements
            all_apply_elements = []

            # CSS selectors
            for selector in apply_selectors:
                try:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    for element in elements:
                        if element.is_displayed() and element.is_enabled():
                            all_apply_elements.append(element)
                except Exception:
                    continue

            # XPath selectors
            for xpath in xpath_selectors:
                try:
                    elements = self.driver.find_elements(By.XPATH, xpath)
                    for element in elements:
                        if element.is_displayed() and element.is_enabled():
                            if element not in all_apply_elements:
                                all_apply_elements.append(element)
                except Exception:
                    continue

            logger.info(f"🎯 Found {len(all_apply_elements)} potential apply elements")

            # Filter and score apply elements
            for element in all_apply_elements:
                try:
                    text = element.text.strip().lower()
                    aria_label = element.get_attribute('aria-label') or ''
                    class_attr = element.get_attribute('class') or ''
                    href = element.get_attribute('href') or ''

                    # Score based on how likely it is to be a real apply button
                    score = 0

                    # High-value indicators
                    for indicator in platform['apply_indicators']:
                        if indicator.lower() in text or indicator.lower() in aria_label.lower():
                            score += 10

                    # Medium-value indicators
                    apply_keywords = ['apply', 'submit', 'join', 'send']
                    for keyword in apply_keywords:
                        if keyword in text or keyword in aria_label.lower():
                            score += 5

                    # Bonus for form buttons
                    if element.tag_name in ['button', 'input']:
                        score += 3

                    # Bonus for external links
                    if href and 'apply' in href.lower():
                        score += 5

                    # Only include elements with decent scores
                    if score >= 5:
                        job_opportunities.append({
                            'element': element,
                            'text': text,
                            'score': score,
                            'aria_label': aria_label,
                            'href': href,
                            'type': 'apply_button'
                        })

                except Exception:
                    continue

            # Sort by score (highest first)
            job_opportunities.sort(key=lambda x: x['score'], reverse=True)

            logger.info(f"✅ Found {len(job_opportunities)} high-quality apply opportunities")

            # Show top opportunities
            if job_opportunities:
                logger.info("🎯 TOP APPLY OPPORTUNITIES:")
                for i, opp in enumerate(job_opportunities[:10], 1):
                    logger.info(f"    {i:2d}. Score: {opp['score']:2d} | Text: '{opp['text'][:60]}'")
                    if opp['href']:
                        logger.info(f"         Href: {opp['href'][:80]}")

            return job_opportunities

        except Exception as e:
            logger.error(f"❌ Error finding job opportunities: {e}")
            return []

    def attempt_live_job_application(self, opportunity: Dict[str, Any], platform_name: str) -> bool:
        """Attempt to apply for a job and show live progress"""
        try:
            element = opportunity['element']

            logger.info(f"\n🚀 LIVE JOB APPLICATION ATTEMPT")
            logger.info(f"📋 Platform: {platform_name}")
            logger.info(f"🎯 Target: {opportunity['text'][:100]}")
            logger.info(f"📊 Score: {opportunity['score']}")
            logger.info(f"🔗 Href: {opportunity['href'][:100] if opportunity['href'] else 'None'}")
            logger.info("=" * 60)

            # Record attempt
            self.session_stats['total_apply_attempts'] += 1

            # Scroll to element
            logger.info("📍 Scrolling to apply button...")
            self.driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", element)
            self.wait_human_like(2, 3)

            # Capture initial state
            original_url = self.driver.current_url
            original_window_count = len(self.driver.window_handles)
            original_page_source_length = len(self.driver.page_source)

            logger.info(f"📊 Initial state captured:")
            logger.info(f"    URL: {original_url}")
            logger.info(f"    Windows: {original_window_count}")
            logger.info(f"    Page size: {original_page_source_length} chars")

            # Try to click the apply button
            click_success = False
            logger.info("🖱️ Attempting to click apply button...")

            # Multiple click strategies
            strategies = [
                ("Standard Click", lambda: element.click()),
                ("JavaScript Click", lambda: self.driver.execute_script("arguments[0].click();", element)),
                ("ActionChains Click", lambda: ActionChains(self.driver).move_to_element(element).click().perform()),
                ("Focus + Enter", lambda: (element.send_keys(Keys.ENTER))),
                ("Focus + Click", lambda: self.driver.execute_script("arguments[0].focus(); arguments[0].click();", element))
            ]

            for strategy_name, strategy_func in strategies:
                try:
                    logger.info(f"    Trying: {strategy_name}")
                    strategy_func()
                    logger.info(f"    ✅ {strategy_name} executed successfully")
                    click_success = True
                    break
                except Exception as e:
                    logger.info(f"    ❌ {strategy_name} failed: {str(e)[:50]}")
                    continue

            if not click_success:
                logger.warning("⚠️ All click strategies failed")
                return False

            # Wait for response
            logger.info("⏳ Waiting for application response...")
            self.wait_human_like(3, 6)

            # Check what happened
            current_url = self.driver.current_url
            current_window_count = len(self.driver.window_handles)
            current_page_source_length = len(self.driver.page_source)

            logger.info(f"📊 Post-click state:")
            logger.info(f"    URL: {current_url}")
            logger.info(f"    Windows: {current_window_count}")
            logger.info(f"    Page size: {current_page_source_length} chars")

            # Analyze changes
            url_changed = current_url != original_url
            new_window_opened = current_window_count > original_window_count
            page_content_changed = abs(current_page_source_length - original_page_source_length) > 1000

            logger.info(f"📈 Changes detected:")
            logger.info(f"    URL changed: {url_changed}")
            logger.info(f"    New window: {new_window_opened}")
            logger.info(f"    Content changed: {page_content_changed}")

            # Handle new window
            if new_window_opened:
                logger.info("🪟 NEW WINDOW OPENED - Checking for application form...")
                try:
                    self.driver.switch_to.window(self.driver.window_handles[-1])
                    self.wait_human_like(3, 5)

                    new_window_url = self.driver.current_url
                    new_window_title = self.driver.title

                    logger.info(f"    New window URL: {new_window_url}")
                    logger.info(f"    New window title: {new_window_title}")

                    # Check if it's an application page
                    is_application_page = self.verify_application_page(new_window_url, new_window_title)

                    if is_application_page:
                        logger.info("🎉 ✅ APPLICATION PAGE DETECTED!")

                        # Look for forms to fill
                        forms_found = self.handle_application_forms()

                        if forms_found:
                            self.session_stats['form_submissions'] += 1
                            logger.info("📝 ✅ APPLICATION FORM SUBMITTED!")

                        self.session_stats['external_applications'] += 1
                        success = True
                    else:
                        logger.info("ℹ️ New window opened but not an application page")
                        success = False

                    # Close and return to main window
                    self.driver.close()
                    self.driver.switch_to.window(self.driver.window_handles[0])

                except Exception as e:
                    logger.error(f"❌ Error handling new window: {e}")
                    try:
                        self.driver.switch_to.window(self.driver.window_handles[0])
                    except:
                        pass
                    success = False

            # Handle URL change (inline application)
            elif url_changed:
                logger.info("🔄 URL CHANGED - Checking for application page...")

                is_application_page = self.verify_application_page(current_url, self.driver.title)

                if is_application_page:
                    logger.info("🎉 ✅ APPLICATION PAGE REACHED!")

                    # Look for forms to fill
                    forms_found = self.handle_application_forms()

                    if forms_found:
                        self.session_stats['form_submissions'] += 1
                        logger.info("📝 ✅ APPLICATION FORM SUBMITTED!")

                    success = True
                else:
                    logger.info("ℹ️ URL changed but not to an application page")
                    success = False

            # Handle content change (modal or dynamic form)
            elif page_content_changed:
                logger.info("📄 PAGE CONTENT CHANGED - Checking for application modal/form...")

                forms_found = self.handle_application_forms()

                if forms_found:
                    logger.info("🎉 ✅ APPLICATION FORM DETECTED AND SUBMITTED!")
                    self.session_stats['form_submissions'] += 1
                    success = True
                else:
                    logger.info("ℹ️ Content changed but no application form found")
                    success = False

            else:
                logger.info("⚠️ No significant changes detected after click")
                success = False

            # Record application attempt
            application_record = {
                'timestamp': datetime.now().isoformat(),
                'platform': platform_name,
                'opportunity_text': opportunity['text'],
                'opportunity_score': opportunity['score'],
                'click_successful': click_success,
                'url_changed': url_changed,
                'new_window': new_window_opened,
                'content_changed': page_content_changed,
                'application_successful': success,
                'original_url': original_url,
                'result_url': current_url
            }

            self.live_applications.append(application_record)

            if success:
                self.confirmed_applications.append(application_record)
                self.session_stats['confirmed_applications'] += 1

                logger.info("🎉 🎉 🎉 LIVE JOB APPLICATION SUCCESSFUL! 🎉 🎉 🎉")
                logger.info(f"✅ Total confirmed applications: {self.session_stats['confirmed_applications']}")
            else:
                logger.info("ℹ️ Click successful but application not confirmed")

            logger.info("=" * 60)
            return success

        except Exception as e:
            logger.error(f"❌ Error during live application attempt: {e}")
            traceback.print_exc()
            return False

    def verify_application_page(self, url: str, title: str) -> bool:
        """Verify if we're on an actual job application page"""
        try:
            url_lower = url.lower()
            title_lower = title.lower()

            # Strong application indicators
            strong_indicators = [
                'apply', 'application', 'job', 'career', 'position',
                'submit', 'resume', 'cv', 'hiring', 'recruit',
                'candidate', 'employment'
            ]

            # Check URL and title
            url_indicates_app = any(indicator in url_lower for indicator in strong_indicators)
            title_indicates_app = any(indicator in title_lower for indicator in strong_indicators)

            # Check page content for application-specific elements
            try:
                page_source = self.driver.page_source.lower()
                content_indicators = [
                    'upload resume', 'cover letter', 'application form',
                    'submit application', 'personal information',
                    'work experience', 'education', 'skills'
                ]
                content_indicates_app = any(indicator in page_source for indicator in content_indicators)
            except:
                content_indicates_app = False

            return url_indicates_app or title_indicates_app or content_indicates_app

        except Exception:
            return False

    def handle_application_forms(self) -> bool:
        """Look for and handle application forms on the current page"""
        try:
            logger.info("📝 Looking for application forms...")

            # Look for file upload inputs (resume upload)
            file_inputs = self.driver.find_elements(By.CSS_SELECTOR, "input[type='file']")
            if file_inputs:
                logger.info(f"📎 Found {len(file_inputs)} file upload fields (likely for resume)")
                for i, file_input in enumerate(file_inputs):
                    if file_input.is_displayed():
                        logger.info(f"    File input {i+1}: {file_input.get_attribute('name') or 'unnamed'}")

            # Look for text areas (cover letter)
            textareas = self.driver.find_elements(By.TAG_NAME, "textarea")
            if textareas:
                logger.info(f"📝 Found {len(textareas)} text areas (likely for cover letter)")
                for i, textarea in enumerate(textareas):
                    if textarea.is_displayed():
                        placeholder = textarea.get_attribute('placeholder') or ''
                        logger.info(f"    Textarea {i+1}: {placeholder[:50]}")

            # Look for forms
            forms = self.driver.find_elements(By.TAG_NAME, "form")
            if forms:
                logger.info(f"📋 Found {len(forms)} forms on the page")

            # Look for submit buttons
            submit_selectors = [
                "button[type='submit']",
                "input[type='submit']",
                "button[contains(translate(text(), 'SUBMIT', 'submit'), 'submit')]",
                "button[contains(translate(text(), 'APPLY', 'apply'), 'apply')]",
                "button[contains(translate(text(), 'SEND', 'send'), 'send')]"
            ]

            submit_buttons = []
            for selector in submit_selectors:
                try:
                    buttons = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    submit_buttons.extend(buttons)
                except:
                    continue

            if submit_buttons:
                logger.info(f"🚀 Found {len(submit_buttons)} submit buttons")

                # Try to click the most promising submit button
                for button in submit_buttons:
                    if button.is_displayed() and button.is_enabled():
                        try:
                            button_text = button.text.strip()
                            logger.info(f"    Clicking submit button: '{button_text}'")
                            button.click()
                            self.wait_human_like(2, 4)
                            logger.info("    ✅ Submit button clicked successfully")
                            return True
                        except Exception as e:
                            logger.info(f"    ❌ Failed to click submit button: {e}")
                            continue

            # Check if we found application-related elements
            found_application_elements = len(file_inputs) > 0 or len(textareas) > 0 or len(forms) > 0

            if found_application_elements:
                logger.info("✅ Application form elements detected!")
                return True
            else:
                logger.info("ℹ️ No clear application form elements found")
                return False

        except Exception as e:
            logger.error(f"❌ Error handling application forms: {e}")
            return False

    def process_platform_continuously(self, platform: Dict[str, Any]) -> int:
        """Process a platform continuously looking for job applications"""
        try:
            logger.info(f"\n🎯 PROCESSING PLATFORM: {platform['name']}")
            logger.info(f"🔗 URL: {platform['url']}")
            logger.info(f"🎪 Looking for live job applications...")
            logger.info("=" * 70)

            # Navigate to platform
            logger.info(f"🌐 Navigating to {platform['name']}...")
            self.driver.get(platform['url'])
            self.wait_human_like(5, 8)

            logger.info(f"📍 Arrived at: {self.driver.current_url}")
            logger.info(f"📑 Page title: {self.driver.title}")

            # Load all content
            self.comprehensive_scroll_and_load()

            # Find job opportunities with apply buttons
            job_opportunities = self.find_actual_job_postings_with_apply(platform)

            if not job_opportunities:
                logger.warning(f"⚠️ No job opportunities found on {platform['name']}")
                return 0

            successful_applications = 0

            # Try to apply to each opportunity
            for i, opportunity in enumerate(job_opportunities):
                try:
                    logger.info(f"\n[OPPORTUNITY {i+1}/{len(job_opportunities)}]")

                    # Attempt live application
                    if self.attempt_live_job_application(opportunity, platform['name']):
                        successful_applications += 1
                        logger.info(f"🎉 SUCCESSFUL APPLICATION #{successful_applications}")

                        # Don't stop - keep going for more applications
                        if successful_applications >= 5:
                            logger.info("🚀 Reached 5 applications on this platform, moving to next")
                            break

                    # Brief delay between attempts
                    self.wait_human_like(3, 6)

                except Exception as e:
                    logger.error(f"❌ Error processing opportunity {i+1}: {e}")
                    continue

            logger.info(f"\n📊 PLATFORM RESULTS: {platform['name']}")
            logger.info(f"    ✅ Successful applications: {successful_applications}")
            logger.info(f"    📋 Opportunities found: {len(job_opportunities)}")
            logger.info(f"    📈 Success rate: {(successful_applications/len(job_opportunities)*100):.1f}%" if job_opportunities else "0%")

            return successful_applications

        except Exception as e:
            logger.error(f"❌ Error processing platform {platform['name']}: {e}")
            return 0

    def run_continuous_automation(self):
        """Main continuous automation - keeps running until demonstrating live applications"""
        logger.info("🚀 CONTINUOUS JOB APPLICATION AUTOMATION")
        logger.info("🎯 Live job application demonstration")
        logger.info("⚡ Won't stop until showing actual job applications")
        logger.info("🔄 Continuous operation across multiple platforms")
        logger.info("=" * 80)

        total_applications = 0
        cycle_count = 0

        try:
            # Setup driver
            if not self.setup_driver():
                logger.error("❌ Failed to setup WebDriver")
                return False

            # Main continuous loop
            while True:
                cycle_count += 1
                logger.info(f"\n🔄 STARTING AUTOMATION CYCLE #{cycle_count}")
                logger.info("=" * 50)

                # Process each platform
                for platform in self.job_platforms:
                    try:
                        self.session_stats['platforms_processed'] += 1

                        applications_on_platform = self.process_platform_continuously(platform)
                        total_applications += applications_on_platform

                        # Print live progress
                        runtime = (time.time() - self.session_stats['start_time']) / 60
                        logger.info(f"\n📊 LIVE PROGRESS UPDATE:")
                        logger.info(f"    🔄 Cycle: #{cycle_count}")
                        logger.info(f"    🏢 Platforms processed: {self.session_stats['platforms_processed']}")
                        logger.info(f"    🎯 Apply attempts: {self.session_stats['total_apply_attempts']}")
                        logger.info(f"    ✅ Confirmed applications: {self.session_stats['confirmed_applications']}")
                        logger.info(f"    📝 Form submissions: {self.session_stats['form_submissions']}")
                        logger.info(f"    🔗 External applications: {self.session_stats['external_applications']}")
                        logger.info(f"    ⏱️ Runtime: {runtime:.1f} minutes")

                        # Show recent applications
                        if self.confirmed_applications:
                            logger.info(f"\n📋 RECENT CONFIRMED APPLICATIONS:")
                            for app in self.confirmed_applications[-3:]:  # Show last 3
                                logger.info(f"    • {app['platform']}: {app['opportunity_text'][:50]} (Score: {app['opportunity_score']})")

                        # Brief delay between platforms
                        self.wait_human_like(5, 10)

                    except KeyboardInterrupt:
                        logger.info("\n⏹️ Automation stopped by user")
                        return True
                    except Exception as e:
                        logger.error(f"❌ Error with platform {platform['name']}: {e}")
                        continue

                # Check if we should continue
                if total_applications >= 15:
                    logger.info(f"\n🎉 🎉 🎉 MISSION ACCOMPLISHED! 🎉 🎉 🎉")
                    logger.info(f"✅ Successfully demonstrated {total_applications} live job applications!")
                    break

                # Wait before next cycle
                logger.info(f"\n⏳ Completed cycle #{cycle_count}. Starting next cycle...")
                self.wait_human_like(10, 15)

        except KeyboardInterrupt:
            logger.info("\n⏹️ Automation stopped by user")
        except Exception as e:
            logger.error(f"❌ Fatal automation error: {e}")
            traceback.print_exc()
        finally:
            self.cleanup()

        return total_applications > 0

    def cleanup(self):
        """Clean up and show final results"""
        if self.driver:
            try:
                self.driver.quit()
                logger.info("🧹 WebDriver cleaned up")
            except:
                pass

        # Final comprehensive results
        runtime = (time.time() - self.session_stats['start_time']) / 60

        logger.info("\n" + "="*70)
        logger.info("📊 FINAL CONTINUOUS AUTOMATION RESULTS")
        logger.info("="*70)
        logger.info(f"✅ Total confirmed applications: {self.session_stats['confirmed_applications']}")
        logger.info(f"🎯 Total apply attempts: {self.session_stats['total_apply_attempts']}")
        logger.info(f"📝 Form submissions: {self.session_stats['form_submissions']}")
        logger.info(f"🔗 External applications: {self.session_stats['external_applications']}")
        logger.info(f"🏢 Platforms processed: {self.session_stats['platforms_processed']}")
        logger.info(f"⏱️ Total runtime: {runtime:.1f} minutes")

        if self.confirmed_applications:
            logger.info(f"\n📋 ALL CONFIRMED APPLICATIONS:")
            for i, app in enumerate(self.confirmed_applications, 1):
                logger.info(f"  {i:2d}. Platform: {app['platform']}")
                logger.info(f"      Job: {app['opportunity_text']}")
                logger.info(f"      Score: {app['opportunity_score']}")
                logger.info(f"      URL: {app['result_url']}")
                logger.info(f"      Time: {app['timestamp']}")
                logger.info("")

def main():
    applier = ContinuousJobOpener()

    try:
        logger.info("🌟 CONTINUOUS JOB APPLICATION AUTOMATION")
        logger.info("🎯 Live demonstration of job applications")
        logger.info("🔄 Continuous operation until success")

        success = applier.run_continuous_automation()

        if success:
            logger.info("\n🎉 🎉 🎉 SUCCESS! 🎉 🎉 🎉")
            logger.info("✅ Live job applications successfully demonstrated!")
        else:
            logger.warning("\n⚠️ Automation ended without demonstrations")

    except KeyboardInterrupt:
        logger.info("\n⏹️ Automation stopped by user")
    except Exception as e:
        logger.error(f"\n❌ Fatal error: {e}")
        traceback.print_exc()
    finally:
        logger.info("\n🏁 Continuous automation session ended")

if __name__ == "__main__":
    main()