#!/usr/bin/env python3
"""
Enhanced Job Finder - Find jobs and Apply buttons more aggressively
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

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EnhancedJobFinder:
    def __init__(self):
        self.driver = None
        self.applied_jobs = []

    def setup_driver(self):
        """Setup Chrome with persistent session"""
        chrome_options = Options()

        # Use persistent profile
        user_data_dir = "/tmp/chrome_jobright_profile"
        chrome_options.add_argument(f"--user-data-dir={user_data_dir}")
        chrome_options.add_argument("--profile-directory=Default")

        # Anti-detection
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)

        self.driver = webdriver.Chrome(
            service=Service(ChromeDriverManager().install()),
            options=chrome_options
        )

        self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        logger.info("✅ Chrome setup completed")

    def explore_and_find_jobs(self):
        """Explore JobRight.ai to find actual job listings"""
        try:
            logger.info("🔍 EXPLORING JOBRIGHT.AI FOR JOBS...")

            # Try different entry points to find jobs
            exploration_urls = [
                "https://jobright.ai",
                "https://jobright.ai/jobs",
                "https://jobright.ai/jobs/recommend",
                "https://jobright.ai/dashboard",
                "https://jobright.ai/search",
                "https://app.jobright.ai",
                "https://app.jobright.ai/jobs"
            ]

            for url in exploration_urls:
                logger.info(f"\n🎯 Exploring: {url}")

                try:
                    self.driver.get(url)
                    time.sleep(5)

                    current_url = self.driver.current_url
                    title = self.driver.title

                    logger.info(f"   Current: {current_url}")
                    logger.info(f"   Title: {title}")

                    # Look for job-related navigation
                    if self.find_job_navigation():
                        logger.info("   ✅ Found job navigation")

                    # Analyze page content
                    job_count = self.analyze_page_for_jobs()
                    logger.info(f"   Job elements found: {job_count}")

                    if job_count > 0:
                        logger.info(f"   🎯 This page has job listings!")
                        return self.extract_all_jobs_from_page()

                except Exception as e:
                    logger.error(f"   ❌ Error exploring {url}: {e}")
                    continue

            logger.warning("❌ No job listings found in exploration")
            return []

        except Exception as e:
            logger.error(f"Exploration error: {e}")
            return []

    def find_job_navigation(self):
        """Find and click job-related navigation"""
        try:
            # Look for navigation links
            nav_selectors = [
                "//a[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'jobs')]",
                "//a[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'search')]",
                "//a[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'browse')]",
                "//a[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'dashboard')]",
                "//button[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'jobs')]",
                "//nav//a",
                "//*[@role='navigation']//a"
            ]

            found_nav = False
            for selector in nav_selectors:
                try:
                    elements = self.driver.find_elements(By.XPATH, selector)
                    for element in elements:
                        if element.is_displayed():
                            text = element.text.strip().lower()
                            href = element.get_attribute('href') or ''

                            if any(word in text or word in href.lower() for word in ['job', 'search', 'browse', 'find']):
                                logger.info(f"     Navigation found: '{text}' -> {href}")

                                # Try clicking promising navigation
                                if 'job' in text or 'search' in text:
                                    try:
                                        element.click()
                                        time.sleep(3)
                                        found_nav = True
                                        logger.info(f"     Clicked navigation: {text}")
                                        return True
                                    except Exception:
                                        continue
                except Exception:
                    continue

            return found_nav

        except Exception as e:
            logger.error(f"Navigation search error: {e}")
            return False

    def analyze_page_for_jobs(self):
        """Analyze current page for job-related content"""
        try:
            # Look for job cards, listings, or apply buttons
            job_indicators = [
                # Job card containers
                "//*[contains(@class, 'job')]",
                "//*[contains(@class, 'position')]",
                "//*[contains(@class, 'listing')]",
                "//*[contains(@class, 'card')]",

                # Apply buttons
                "//*[contains(text(), 'Apply')]",
                "//*[contains(@class, 'apply')]",

                # Company/title elements
                "//*[contains(@class, 'company')]",
                "//*[contains(@class, 'title')]",

                # Job-related text content
                "//*[contains(text(), 'Company')]",
                "//*[contains(text(), 'Salary')]",
                "//*[contains(text(), 'Location')]",
                "//*[contains(text(), 'Remote')]",
                "//*[contains(text(), 'Full-time')]",
                "//*[contains(text(), 'Part-time')]"
            ]

            total_job_elements = 0

            for selector in job_indicators:
                try:
                    elements = self.driver.find_elements(By.XPATH, selector)
                    visible_elements = [e for e in elements if e.is_displayed()]
                    total_job_elements += len(visible_elements)

                    if visible_elements:
                        logger.info(f"     Found {len(visible_elements)} elements matching: {selector.split('[')[0]}")
                except Exception:
                    continue

            return total_job_elements

        except Exception as e:
            logger.error(f"Page analysis error: {e}")
            return 0

    def extract_all_jobs_from_page(self):
        """Extract all job information and apply buttons from current page"""
        try:
            logger.info("📋 EXTRACTING JOBS FROM PAGE...")

            # Scroll to load all content
            self.scroll_to_load_all_content()

            # Find all potential job containers
            job_containers = self.find_job_containers()
            logger.info(f"   Found {len(job_containers)} job containers")

            jobs = []
            for i, container in enumerate(job_containers):
                try:
                    job_info = self.extract_job_from_container(container, i)
                    if job_info:
                        jobs.append(job_info)
                except Exception as e:
                    logger.debug(f"   Job {i} extraction error: {e}")
                    continue

            logger.info(f"✅ Extracted {len(jobs)} jobs with apply buttons")

            # Try applying to all jobs
            return self.apply_to_jobs(jobs)

        except Exception as e:
            logger.error(f"Job extraction error: {e}")
            return []

    def scroll_to_load_all_content(self):
        """Scroll page to load all dynamic content"""
        try:
            logger.info("   Scrolling to load all content...")

            # Get initial height
            last_height = self.driver.execute_script("return document.body.scrollHeight")

            for i in range(10):  # Max 10 scrolls
                # Scroll to bottom
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(2)

                # Check if new content loaded
                new_height = self.driver.execute_script("return document.body.scrollHeight")
                if new_height == last_height:
                    break
                last_height = new_height

                # Look for "Load More" buttons
                load_more_buttons = self.driver.find_elements(By.XPATH,
                    "//button[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'load') or "
                    "contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'more') or "
                    "contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'show')]"
                )

                for btn in load_more_buttons:
                    if btn.is_displayed() and btn.is_enabled():
                        try:
                            btn.click()
                            time.sleep(3)
                            logger.info(f"     Clicked load more button: {btn.text}")
                        except Exception:
                            continue

            # Scroll back to top
            self.driver.execute_script("window.scrollTo(0, 0);")
            time.sleep(1)

        except Exception as e:
            logger.error(f"Scrolling error: {e}")

    def find_job_containers(self):
        """Find all job container elements"""
        try:
            # Try different selectors for job containers
            container_selectors = [
                # Common job container patterns
                "//*[contains(@class, 'job-card')]",
                "//*[contains(@class, 'job-item')]",
                "//*[contains(@class, 'job-listing')]",
                "//*[contains(@class, 'position-card')]",
                "//*[contains(@class, 'listing-card')]",

                # Generic containers that might contain jobs
                "//div[contains(@class, 'card')]",
                "//li[contains(@class, 'item')]",
                "//div[contains(@class, 'item')]",

                # Containers with apply buttons
                "//*[.//button[contains(text(), 'Apply')] or .//a[contains(text(), 'Apply')]]",

                # Fallback: any container with job-related text
                "//*[contains(., 'Company') and contains(., 'Apply')]",
                "//*[contains(., 'Salary') and (contains(., 'Apply') or contains(., 'apply'))]"
            ]

            all_containers = []

            for selector in container_selectors:
                try:
                    elements = self.driver.find_elements(By.XPATH, selector)
                    visible_elements = [e for e in elements if e.is_displayed()]

                    if visible_elements:
                        logger.info(f"     Found {len(visible_elements)} containers with: {selector.split('[')[0]}")
                        all_containers.extend(visible_elements)
                except Exception:
                    continue

            # Remove duplicates (keep unique elements)
            unique_containers = []
            for container in all_containers:
                try:
                    is_duplicate = False
                    for existing in unique_containers:
                        if (container.location == existing.location and
                            container.size == existing.size):
                            is_duplicate = True
                            break

                    if not is_duplicate:
                        unique_containers.append(container)
                except Exception:
                    continue

            return unique_containers[:50]  # Limit to first 50 to avoid overload

        except Exception as e:
            logger.error(f"Container finding error: {e}")
            return []

    def extract_job_from_container(self, container, index):
        """Extract job information and apply button from a container"""
        try:
            # Try to get job details
            title = "Unknown Position"
            company = "Unknown Company"
            apply_button = None

            # Look for job title
            title_selectors = [
                ".//h1", ".//h2", ".//h3", ".//h4",
                ".//*[contains(@class, 'title')]",
                ".//*[contains(@class, 'job-title')]",
                ".//*[contains(@class, 'position')]"
            ]

            for selector in title_selectors:
                try:
                    title_elem = container.find_element(By.XPATH, selector)
                    if title_elem.is_displayed() and title_elem.text.strip():
                        title = title_elem.text.strip()
                        break
                except Exception:
                    continue

            # Look for company name
            company_selectors = [
                ".//*[contains(@class, 'company')]",
                ".//*[contains(text(), 'Company')]",
                ".//span", ".//div"
            ]

            for selector in company_selectors:
                try:
                    company_elem = container.find_element(By.XPATH, selector)
                    if (company_elem.is_displayed() and company_elem.text.strip() and
                        len(company_elem.text.strip()) > 2 and 'company' not in company_elem.text.lower()):
                        company = company_elem.text.strip()
                        break
                except Exception:
                    continue

            # Look for apply button
            apply_selectors = [
                ".//button[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'apply')]",
                ".//a[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'apply')]",
                ".//*[contains(@class, 'apply')]",
                ".//button", ".//a"
            ]

            for selector in apply_selectors:
                try:
                    buttons = container.find_elements(By.XPATH, selector)
                    for btn in buttons:
                        if btn.is_displayed() and btn.is_enabled():
                            btn_text = btn.text.strip().lower()
                            btn_href = btn.get_attribute('href') or ''

                            if ('apply' in btn_text or 'apply' in btn_href.lower() or
                                'submit' in btn_text or 'send' in btn_text):
                                apply_button = btn
                                break

                    if apply_button:
                        break
                except Exception:
                    continue

            if apply_button:
                logger.info(f"   Job {index+1}: {title} at {company}")
                return {
                    'index': index,
                    'title': title,
                    'company': company,
                    'apply_button': apply_button,
                    'container': container
                }

            return None

        except Exception as e:
            logger.debug(f"Job extraction from container error: {e}")
            return None

    def apply_to_jobs(self, jobs):
        """Apply to all extracted jobs"""
        try:
            logger.info(f"🚀 APPLYING TO {len(jobs)} JOBS...")

            successful_applications = 0
            failed_applications = 0

            for job in jobs:
                try:
                    logger.info(f"\n📋 Applying to: {job['title']} at {job['company']}")

                    # Scroll to job to make it visible
                    self.driver.execute_script("arguments[0].scrollIntoView(true);", job['container'])
                    time.sleep(1)

                    # Click apply button
                    apply_button = job['apply_button']

                    # Try different click methods
                    clicked = False
                    click_methods = [
                        lambda: apply_button.click(),
                        lambda: self.driver.execute_script("arguments[0].click();", apply_button),
                        lambda: ActionChains(self.driver).move_to_element(apply_button).click().perform()
                    ]

                    for method in click_methods:
                        try:
                            method()
                            clicked = True
                            break
                        except Exception:
                            continue

                    if clicked:
                        time.sleep(3)  # Wait for response

                        # Check if new tab opened or page changed
                        current_url = self.driver.current_url
                        if 'apply' in current_url.lower() or len(self.driver.window_handles) > 1:
                            logger.info("   ✅ Application page opened")

                            # Handle application process
                            self.process_application()

                        successful_applications += 1
                        logger.info(f"   ✅ Applied successfully")

                        self.applied_jobs.append({
                            'title': job['title'],
                            'company': job['company'],
                            'status': 'applied',
                            'timestamp': time.time()
                        })

                    else:
                        failed_applications += 1
                        logger.error(f"   ❌ Failed to click apply button")

                    time.sleep(2)  # Brief delay between applications

                except Exception as e:
                    failed_applications += 1
                    logger.error(f"   ❌ Application error: {e}")

            logger.info(f"\n🎯 FINAL RESULTS:")
            logger.info(f"   ✅ Successful Applications: {successful_applications}")
            logger.info(f"   ❌ Failed Applications: {failed_applications}")
            logger.info(f"   📊 Success Rate: {(successful_applications/(successful_applications+failed_applications)*100):.1f}%")

            return self.applied_jobs

        except Exception as e:
            logger.error(f"Apply to jobs error: {e}")
            return []

    def process_application(self):
        """Process application form after clicking apply"""
        try:
            # If new tab opened, switch to it
            if len(self.driver.window_handles) > 1:
                self.driver.switch_to.window(self.driver.window_handles[-1])

            time.sleep(3)

            # Look for submit/send/apply buttons on application page
            submit_selectors = [
                "//button[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'submit')]",
                "//button[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'send')]",
                "//button[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'apply')]",
                "//input[@type='submit']"
            ]

            for selector in submit_selectors:
                try:
                    submit_buttons = self.driver.find_elements(By.XPATH, selector)
                    for btn in submit_buttons:
                        if btn.is_displayed() and btn.is_enabled():
                            logger.info(f"     Clicking submit: {btn.text}")
                            btn.click()
                            time.sleep(2)
                            break
                except Exception:
                    continue

            # If we opened a new tab, close it and go back to main page
            if len(self.driver.window_handles) > 1:
                self.driver.close()
                self.driver.switch_to.window(self.driver.window_handles[0])

        except Exception as e:
            logger.error(f"Application processing error: {e}")

    def run(self):
        """Run the enhanced job finder"""
        try:
            logger.info("🔍 ENHANCED JOB FINDER STARTING...")

            self.setup_driver()

            jobs_applied = self.explore_and_find_jobs()

            if jobs_applied:
                logger.info(f"\n🎉 SUCCESS! Applied to {len(jobs_applied)} jobs!")
                for job in jobs_applied:
                    logger.info(f"   ✅ {job['title']} at {job['company']}")
            else:
                logger.warning("❌ No jobs found or applied to")

            input("\nPress Enter to close browser...")

        except Exception as e:
            logger.error(f"Enhanced job finder error: {e}")

        finally:
            if self.driver:
                self.driver.quit()

if __name__ == "__main__":
    finder = EnhancedJobFinder()
    finder.run()