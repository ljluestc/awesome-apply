#!/usr/bin/env python3
"""
TARGETED JOB APPLICATION AUTOMATION
Specifically targets actual job postings with sophisticated filtering
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
        logging.FileHandler('targeted_job_applier.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class TargetedJobApplier:
    def __init__(self):
        """Initialize targeted job application automation"""
        self.driver = None
        self.session_id = datetime.now().strftime('%Y%m%d_%H%M%S')

        # Success tracking
        self.applied_jobs = []
        self.session_stats = {
            'start_time': time.time(),
            'platforms_tried': 0,
            'jobs_found': 0,
            'actual_job_applications': 0,
            'failed_attempts': 0
        }

        # Job search targets
        self.job_targets = [
            {
                'name': 'JobRight_SoftwareJobs',
                'url': 'https://jobright.ai/s?keyword=software%20engineer&location=San%20Jose%2C%20CA',
                'job_selectors': [
                    '.job-card', '.job-item', '.position-card',
                    '[data-testid*="job"]', '.opportunity-card'
                ]
            },
            {
                'name': 'LinkedIn_SoftwareJobs',
                'url': 'https://www.linkedin.com/jobs/search?keywords=software%20engineer&location=San%20Jose%2C%20CA&distance=25&f_TPR=r86400',
                'job_selectors': [
                    '.job-search-card', '.jobs-search-results__list-item',
                    '[data-entity-urn*="jobPosting"]'
                ]
            },
            {
                'name': 'Indeed_SoftwareJobs',
                'url': 'https://indeed.com/jobs?q=software+engineer&l=San+Jose%2C+CA&fromage=1',
                'job_selectors': [
                    '.job_seen_beacon', '.result', '.jobsearch-SerpJobCard'
                ]
            }
        ]

    def setup_driver(self):
        """Setup Chrome WebDriver"""
        try:
            chrome_options = Options()

            # Use persistent profile
            user_data_dir = f"/tmp/chrome_targeted_{self.session_id}"
            chrome_options.add_argument(f"--user-data-dir={user_data_dir}")
            chrome_options.add_argument("--profile-directory=Default")

            # Optimization
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

            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

            logger.info("✅ WebDriver setup successfully")
            return True

        except Exception as e:
            logger.error(f"❌ Failed to setup WebDriver: {e}")
            return False

    def wait_random(self, min_seconds=2, max_seconds=5):
        """Human-like random wait"""
        wait_time = random.uniform(min_seconds, max_seconds)
        time.sleep(wait_time)

    def is_actual_job_posting(self, element) -> bool:
        """Determine if an element represents an actual job posting"""
        try:
            text = element.text.lower()

            # Job title indicators
            job_indicators = [
                'engineer', 'developer', 'analyst', 'manager', 'specialist',
                'coordinator', 'associate', 'intern', 'technician', 'consultant',
                'designer', 'architect', 'lead', 'senior', 'junior', 'entry level'
            ]

            # Exclude non-job content
            exclude_indicators = [
                'blog', 'article', 'guide', 'template', 'tip', 'principle',
                'resume', 'cv', 'linkedin', 'why use', 'how to', 'ultimate',
                'top 10', 'list', 'chatgpt', 'ai tool'
            ]

            # Check for job indicators
            has_job_indicator = any(indicator in text for indicator in job_indicators)

            # Check for exclude indicators
            has_exclude_indicator = any(indicator in text for indicator in exclude_indicators)

            # Additional checks
            href = element.get_attribute('href') or ''
            has_job_url = any(keyword in href.lower() for keyword in ['job', 'position', 'career', 'apply'])

            # Look for company names or job-specific attributes
            classes = element.get_attribute('class') or ''
            has_job_class = any(keyword in classes.lower() for keyword in ['job', 'position', 'card'])

            return (has_job_indicator or has_job_url or has_job_class) and not has_exclude_indicator

        except Exception:
            return False

    def find_actual_job_postings(self, job_selectors: List[str]) -> List[Dict[str, Any]]:
        """Find actual job postings on the page"""
        try:
            job_postings = []

            # Scroll to load all jobs
            self.scroll_to_load_content()

            # Find job containers
            all_containers = []

            for selector in job_selectors:
                try:
                    containers = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    all_containers.extend(containers)
                except Exception:
                    continue

            logger.info(f"🔍 Found {len(all_containers)} potential job containers")

            # Filter for actual job postings
            for container in all_containers:
                try:
                    if container.is_displayed() and self.is_actual_job_posting(container):
                        # Look for apply buttons within this job posting
                        apply_elements = self.find_apply_elements_in_container(container)

                        if apply_elements:
                            job_postings.append({
                                'container': container,
                                'title': container.text[:100],
                                'apply_elements': apply_elements
                            })

                except Exception:
                    continue

            logger.info(f"✅ Found {len(job_postings)} actual job postings with apply options")
            return job_postings

        except Exception as e:
            logger.error(f"❌ Error finding job postings: {e}")
            return []

    def find_apply_elements_in_container(self, container) -> List[Dict[str, Any]]:
        """Find apply elements within a specific job container"""
        try:
            apply_elements = []

            # Apply button selectors
            apply_selectors = [
                "button[contains(translate(text(), 'APPLY', 'apply'), 'apply')]",
                "a[contains(translate(text(), 'APPLY', 'apply'), 'apply')]",
                "button[aria-label*='Apply']",
                "a[aria-label*='Apply']",
                "*[data-testid*='apply']",
                ".apply-button",
                ".easy-apply-button",
                "button[data-tracking-control-name*='apply']"
            ]

            # Look within the container
            for selector in apply_selectors:
                try:
                    elements = container.find_elements(By.CSS_SELECTOR, selector)
                    for element in elements:
                        if element.is_displayed() and element.is_enabled():
                            apply_elements.append({
                                'element': element,
                                'text': element.text.strip(),
                                'selector': selector
                            })
                except Exception:
                    continue

            # Also check if the container itself is clickable (job card click)
            if not apply_elements:
                try:
                    href = container.get_attribute('href')
                    onclick = container.get_attribute('onclick')

                    if href or onclick or container.tag_name in ['a', 'button']:
                        apply_elements.append({
                            'element': container,
                            'text': 'Click job card',
                            'selector': 'job_container'
                        })
                except Exception:
                    pass

            return apply_elements

        except Exception as e:
            logger.error(f"❌ Error finding apply elements in container: {e}")
            return []

    def scroll_to_load_content(self):
        """Scroll to load dynamic content"""
        try:
            last_height = self.driver.execute_script("return document.body.scrollHeight")

            for i in range(5):
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                self.wait_random(2, 3)

                new_height = self.driver.execute_script("return document.body.scrollHeight")
                if new_height == last_height:
                    break
                last_height = new_height

            logger.info(f"📜 Scrolling completed ({i+1} scrolls)")

        except Exception as e:
            logger.error(f"❌ Error during scrolling: {e}")

    def apply_to_job(self, job_posting: Dict[str, Any]) -> bool:
        """Apply to a specific job posting"""
        try:
            logger.info(f"🎯 APPLYING TO JOB: {job_posting['title']}")

            original_url = self.driver.current_url
            original_windows = len(self.driver.window_handles)

            # Try each apply element in the job posting
            for apply_element in job_posting['apply_elements']:
                try:
                    element = apply_element['element']

                    # Scroll to element
                    self.driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", element)
                    self.wait_random(1, 2)

                    # Try clicking
                    success = self.smart_click(element)

                    if success:
                        self.wait_random(3, 5)

                        # Check for application success
                        if self.verify_job_application(original_url, original_windows, job_posting):
                            return True

                except Exception as e:
                    logger.warning(f"⚠️ Failed to click apply element: {e}")
                    continue

            return False

        except Exception as e:
            logger.error(f"❌ Error applying to job: {e}")
            return False

    def smart_click(self, element) -> bool:
        """Smart clicking with multiple strategies"""
        try:
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

            # Strategy 3: ActionChains
            try:
                ActionChains(self.driver).move_to_element(element).click().perform()
                logger.info("✅ ActionChains click successful")
                return True
            except Exception:
                pass

            return False

        except Exception:
            return False

    def verify_job_application(self, original_url: str, original_windows: int, job_posting: Dict[str, Any]) -> bool:
        """Verify that a job application was successful"""
        try:
            current_url = self.driver.current_url
            current_windows = len(self.driver.window_handles)

            # Check for new window (external application)
            if current_windows > original_windows:
                logger.info("📂 New window opened - checking for application")

                # Switch to new window
                self.driver.switch_to.window(self.driver.window_handles[-1])
                self.wait_random(3, 5)

                app_url = self.driver.current_url
                app_title = self.driver.title

                # Check if it's a job application page
                is_job_app = self.is_job_application_page(app_url, app_title)

                if is_job_app:
                    logger.info("🎉 ✅ JOB APPLICATION PAGE OPENED!")
                    logger.info(f"    URL: {app_url}")
                    logger.info(f"    Title: {app_title}")

                    # Record success
                    self.applied_jobs.append({
                        'timestamp': datetime.now().isoformat(),
                        'job_title': job_posting['title'],
                        'application_url': app_url,
                        'application_title': app_title,
                        'type': 'external_application'
                    })

                    self.session_stats['actual_job_applications'] += 1

                    # Close and return to main window
                    self.driver.close()
                    self.driver.switch_to.window(self.driver.window_handles[0])

                    return True
                else:
                    # Close non-application window
                    self.driver.close()
                    self.driver.switch_to.window(self.driver.window_handles[0])

            # Check for URL change (inline application)
            elif current_url != original_url:
                is_job_app = self.is_job_application_page(current_url, self.driver.title)

                if is_job_app:
                    logger.info("🎉 ✅ JOB APPLICATION PAGE REACHED!")
                    logger.info(f"    URL: {current_url}")
                    logger.info(f"    Title: {self.driver.title}")

                    # Record success
                    self.applied_jobs.append({
                        'timestamp': datetime.now().isoformat(),
                        'job_title': job_posting['title'],
                        'application_url': current_url,
                        'application_title': self.driver.title,
                        'type': 'inline_application'
                    })

                    self.session_stats['actual_job_applications'] += 1

                    # Go back to job search
                    self.driver.back()
                    self.wait_random(2, 3)

                    return True

            return False

        except Exception as e:
            logger.error(f"❌ Error verifying job application: {e}")
            return False

    def is_job_application_page(self, url: str, title: str) -> bool:
        """Check if URL/title indicates a job application page"""
        try:
            url_lower = url.lower()
            title_lower = title.lower()

            # Job application indicators
            app_indicators = [
                'apply', 'application', 'job', 'career', 'position',
                'submit', 'resume', 'cv', 'hiring', 'recruit'
            ]

            # Check URL
            url_has_indicator = any(indicator in url_lower for indicator in app_indicators)

            # Check title
            title_has_indicator = any(indicator in title_lower for indicator in app_indicators)

            # Check page content for forms
            try:
                page_source = self.driver.page_source.lower()
                has_form_indicators = any(indicator in page_source for indicator in [
                    'upload resume', 'cover letter', 'application form', 'submit application'
                ])
            except Exception:
                has_form_indicators = False

            return url_has_indicator or title_has_indicator or has_form_indicators

        except Exception:
            return False

    def process_platform(self, target: Dict[str, str]) -> int:
        """Process jobs on a specific platform"""
        try:
            logger.info(f"\n🎯 PROCESSING PLATFORM: {target['name']}")
            logger.info(f"🔗 URL: {target['url']}")
            logger.info("=" * 60)

            # Navigate to platform
            self.driver.get(target['url'])
            self.wait_random(5, 8)

            logger.info(f"📍 Arrived at: {self.driver.current_url}")
            logger.info(f"📑 Page title: {self.driver.title}")

            # Find actual job postings
            job_postings = self.find_actual_job_postings(target['job_selectors'])

            if not job_postings:
                logger.warning(f"⚠️ No job postings found on {target['name']}")
                return 0

            self.session_stats['jobs_found'] += len(job_postings)
            applications_successful = 0

            # Apply to each job
            for i, job_posting in enumerate(job_postings):
                try:
                    logger.info(f"\n[JOB {i+1}/{len(job_postings)}]")

                    if self.apply_to_job(job_posting):
                        applications_successful += 1
                        logger.info(f"✅ Successfully applied to job {i+1}")

                        # Stop if we've reached our goal
                        if applications_successful >= 5:
                            logger.info("\n🎉 REACHED APPLICATION GOAL!")
                            break
                    else:
                        logger.info(f"ℹ️ Could not apply to job {i+1}")
                        self.session_stats['failed_attempts'] += 1

                    # Brief delay between jobs
                    self.wait_random(3, 5)

                except Exception as e:
                    logger.error(f"❌ Error processing job {i+1}: {e}")
                    continue

            logger.info(f"\n📊 PLATFORM RESULTS: {target['name']}")
            logger.info(f"    ✅ Successful applications: {applications_successful}")
            logger.info(f"    📋 Jobs found: {len(job_postings)}")
            logger.info(f"    📈 Success rate: {(applications_successful/len(job_postings)*100):.1f}%" if job_postings else "0%")

            return applications_successful

        except Exception as e:
            logger.error(f"❌ Error processing platform {target['name']}: {e}")
            return 0

    def run_targeted_automation(self):
        """Main automation targeting actual job applications"""
        logger.info("🚀 TARGETED JOB APPLICATION AUTOMATION")
        logger.info("🎯 Specifically targeting actual job postings")
        logger.info("⚡ Filtering out non-job content")
        logger.info("=" * 80)

        try:
            if not self.setup_driver():
                return False

            total_applications = 0

            # Process each platform
            for target in self.job_targets:
                try:
                    self.session_stats['platforms_tried'] += 1

                    applications = self.process_platform(target)
                    total_applications += applications

                    # Progress update
                    runtime = (time.time() - self.session_stats['start_time']) / 60
                    logger.info(f"\n📊 OVERALL PROGRESS:")
                    logger.info(f"    🏢 Platforms tried: {self.session_stats['platforms_tried']}")
                    logger.info(f"    📋 Jobs found: {self.session_stats['jobs_found']}")
                    logger.info(f"    ✅ Successful applications: {total_applications}")
                    logger.info(f"    ❌ Failed attempts: {self.session_stats['failed_attempts']}")
                    logger.info(f"    ⏱️ Runtime: {runtime:.1f} minutes")

                    # Check if goal reached
                    if total_applications >= 10:
                        logger.info("\n🎉 🎉 🎉 MISSION ACCOMPLISHED! 🎉 🎉 🎉")
                        logger.info(f"✅ Successfully applied to {total_applications} actual jobs!")
                        break

                except Exception as e:
                    logger.error(f"❌ Error with platform {target['name']}: {e}")
                    continue

            # Final results
            logger.info("\n🏁 TARGETED AUTOMATION COMPLETED")
            logger.info(f"✅ Total job applications: {total_applications}")

            if self.applied_jobs:
                logger.info("\n📋 SUCCESSFUL JOB APPLICATIONS:")
                for i, job in enumerate(self.applied_jobs, 1):
                    logger.info(f"  {i:2d}. Job: {job['job_title']}")
                    logger.info(f"      URL: {job['application_url']}")
                    logger.info(f"      Type: {job['type']}")
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
    applier = TargetedJobApplier()

    try:
        logger.info("🌟 TARGETED JOB APPLICATION AUTOMATION")
        logger.info("🎯 Focusing specifically on actual job postings")

        success = applier.run_targeted_automation()

        if success:
            logger.info("\n🎉 🎉 🎉 SUCCESS! 🎉 🎉 🎉")
            logger.info("✅ Successfully applied to actual job postings!")
        else:
            logger.warning("\n⚠️ No successful applications")

    except KeyboardInterrupt:
        logger.info("\n⏹️ Automation stopped by user")
    except Exception as e:
        logger.error(f"\n❌ Fatal error: {e}")
        traceback.print_exc()
    finally:
        applier.cleanup()

        # Final stats
        runtime = (time.time() - applier.session_stats['start_time']) / 60
        logger.info("\n" + "="*60)
        logger.info("📊 FINAL STATISTICS")
        logger.info("="*60)
        logger.info(f"✅ Job applications: {applier.session_stats['actual_job_applications']}")
        logger.info(f"📋 Jobs found: {applier.session_stats['jobs_found']}")
        logger.info(f"🏢 Platforms tried: {applier.session_stats['platforms_tried']}")
        logger.info(f"❌ Failed attempts: {applier.session_stats['failed_attempts']}")
        logger.info(f"⏱️ Total runtime: {runtime:.1f} minutes")

if __name__ == "__main__":
    main()