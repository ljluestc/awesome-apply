#!/usr/bin/env python3
"""
JobRight.ai Jobs Scraper with ClickHouse Integration
Scrapes jobs from https://jobright.ai/jobs/recommend?pos=10 and saves to ClickHouse
"""

import os
import time
import json
import logging
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import clickhouse_connect

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class JobRightClickHouseScraper:
    def __init__(self):
        self.setup_driver()
        self.setup_clickhouse()
        self.scraped_jobs = []

        # Create output directory
        self.output_dir = "jobright_scraping_output"
        os.makedirs(self.output_dir, exist_ok=True)
        os.makedirs(f"{self.output_dir}/screenshots", exist_ok=True)

    def setup_driver(self):
        """Setup Chrome WebDriver with optimal settings for scraping"""
        chrome_options = Options()
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")

        self.driver = webdriver.Chrome(options=chrome_options)
        self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        self.wait = WebDriverWait(self.driver, 15)

    def setup_clickhouse(self):
        """Setup ClickHouse connection and create tables"""
        try:
            # Connect to ClickHouse (local instance)
            self.clickhouse_client = clickhouse_connect.get_client(
                host='localhost',
                port=8123,
                username='default',
                password='',
                database='default'
            )

            # Create jobs table if it doesn't exist
            create_table_sql = """
            CREATE TABLE IF NOT EXISTS jobright_jobs (
                job_id String,
                title String,
                company String,
                location String,
                salary String,
                job_type String,
                experience_level String,
                description String,
                requirements String,
                benefits String,
                posted_date String,
                apply_url String,
                scraped_at DateTime,
                source String DEFAULT 'jobright.ai'
            ) ENGINE = MergeTree()
            ORDER BY scraped_at
            """

            self.clickhouse_client.command(create_table_sql)
            logger.info("✅ ClickHouse connection established and table created")

        except Exception as e:
            logger.error(f"❌ ClickHouse setup failed: {e}")
            logger.info("📝 Will save to JSON file instead")
            self.clickhouse_client = None

    def navigate_to_jobright(self):
        """Navigate to JobRight.ai and handle login if needed"""
        try:
            # First try the jobs page directly
            url = "https://jobright.ai/jobs"
            logger.info(f"🌐 Navigating to: {url}")

            self.driver.get(url)
            time.sleep(5)

            # Take screenshot
            screenshot_path = f"{self.output_dir}/screenshots/jobright_initial_{datetime.now().strftime('%H%M%S')}.png"
            self.driver.save_screenshot(screenshot_path)
            logger.info(f"📸 Screenshot saved: {screenshot_path}")

            # Check if we need to sign up or login
            if "sign" in self.driver.current_url.lower() or "login" in self.driver.current_url.lower():
                logger.info("🔐 Detected login requirement, trying to access public jobs...")

                # Try to access jobs without login
                self.driver.get("https://jobright.ai/jobs/search")
                time.sleep(5)

            # Try to click "Try JobRight for Free" or similar buttons
            try_free_buttons = [
                "//button[contains(text(), 'Try JobRight for Free')]",
                "//a[contains(text(), 'Try JobRight for Free')]",
                "//button[contains(text(), 'Get Started')]",
                "//a[contains(text(), 'Get Started')]",
                "//button[contains(text(), 'Free')]",
                "//a[contains(text(), 'Free')]"
            ]

            for button_xpath in try_free_buttons:
                try:
                    button = self.driver.find_element(By.XPATH, button_xpath)
                    if button.is_displayed():
                        logger.info(f"🖱️ Clicking: {button.text}")
                        button.click()
                        time.sleep(5)
                        break
                except:
                    continue

            # Try alternative URLs that might have public job listings
            alternative_urls = [
                "https://jobright.ai/jobs/search",
                "https://jobright.ai/jobs/browse",
                "https://jobright.ai/careers",
                "https://jobright.ai/opportunities"
            ]

            for alt_url in alternative_urls:
                try:
                    logger.info(f"🔄 Trying alternative URL: {alt_url}")
                    self.driver.get(alt_url)
                    time.sleep(5)

                    # Check if we can find job elements
                    job_indicators = self.driver.find_elements(By.XPATH, "//*[contains(text(), 'Software Engineer') or contains(text(), 'Developer') or contains(text(), 'Engineer')]")
                    if job_indicators:
                        logger.info(f"✅ Found job indicators at: {alt_url}")
                        break
                except:
                    continue

            # Take final screenshot
            final_screenshot = f"{self.output_dir}/screenshots/jobright_final_{datetime.now().strftime('%H%M%S')}.png"
            self.driver.save_screenshot(final_screenshot)
            logger.info(f"📸 Final screenshot: {final_screenshot}")

            return True

        except Exception as e:
            logger.error(f"❌ Failed to navigate to JobRight: {e}")
            return False

    def extract_job_listings(self):
        """Extract job listings from the page"""
        try:
            logger.info("🔍 Extracting job listings...")

            # Wait for jobs to load
            time.sleep(10)

            # Multiple selectors to try for job listings
            job_selectors = [
                ".job-card",
                ".job-item",
                ".job-listing",
                "[data-job-id]",
                ".recommendation-item",
                ".job-rec",
                ".job-post",
                ".position-card",
                ".vacancy",
                "div[class*='job']",
                "article[class*='job']",
                "li[class*='job']"
            ]

            jobs_found = []

            for selector in job_selectors:
                try:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    logger.info(f"🔍 Selector '{selector}' found {len(elements)} elements")

                    if elements:
                        for i, element in enumerate(elements[:20]):  # Limit to 20 per selector
                            try:
                                job_data = self.extract_job_details(element, i, selector)
                                if job_data and job_data.get('title'):
                                    jobs_found.append(job_data)
                                    logger.info(f"✅ Extracted: {job_data['title']} at {job_data.get('company', 'Unknown')}")
                            except Exception as e:
                                logger.debug(f"Failed to extract job {i}: {e}")

                        if jobs_found:
                            break  # Stop if we found jobs with this selector

                except Exception as e:
                    logger.debug(f"Selector '{selector}' failed: {e}")

            # If no jobs found with standard selectors, try broader search
            if not jobs_found:
                logger.info("🔍 No jobs found with standard selectors, trying broader search...")
                self.try_alternative_extraction_methods()

            self.scraped_jobs = jobs_found
            logger.info(f"📊 Total jobs extracted: {len(jobs_found)}")
            return jobs_found

        except Exception as e:
            logger.error(f"❌ Failed to extract job listings: {e}")
            return []

    def extract_job_details(self, element, index: int, selector: str) -> Optional[Dict[str, Any]]:
        """Extract detailed information from a job element"""
        try:
            job_data = {
                'job_id': f"jr_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{index}",
                'title': '',
                'company': '',
                'location': '',
                'salary': '',
                'job_type': '',
                'experience_level': '',
                'description': '',
                'requirements': '',
                'benefits': '',
                'posted_date': '',
                'apply_url': '',
                'scraped_at': datetime.now(timezone.utc).isoformat(),
                'extraction_method': selector
            }

            # Extract title
            title_selectors = [
                "h1", "h2", "h3", ".title", ".job-title",
                ".position-title", "[data-title]", "a[href*='job']"
            ]

            for title_sel in title_selectors:
                try:
                    title_elem = element.find_element(By.CSS_SELECTOR, title_sel)
                    title_text = title_elem.text.strip()
                    if title_text and len(title_text) > 5:
                        job_data['title'] = title_text
                        break
                except:
                    continue

            # Extract company
            company_selectors = [
                ".company", ".company-name", ".employer",
                "[data-company]", ".org", ".business"
            ]

            for comp_sel in company_selectors:
                try:
                    comp_elem = element.find_element(By.CSS_SELECTOR, comp_sel)
                    comp_text = comp_elem.text.strip()
                    if comp_text:
                        job_data['company'] = comp_text
                        break
                except:
                    continue

            # Extract location
            location_selectors = [
                ".location", ".job-location", ".workplace",
                "[data-location]", ".city", ".place"
            ]

            for loc_sel in location_selectors:
                try:
                    loc_elem = element.find_element(By.CSS_SELECTOR, loc_sel)
                    loc_text = loc_elem.text.strip()
                    if loc_text:
                        job_data['location'] = loc_text
                        break
                except:
                    continue

            # Extract salary
            salary_selectors = [
                ".salary", ".pay", ".compensation",
                "[data-salary]", ".wage", ".income"
            ]

            for sal_sel in salary_selectors:
                try:
                    sal_elem = element.find_element(By.CSS_SELECTOR, sal_sel)
                    sal_text = sal_elem.text.strip()
                    if sal_text and ('$' in sal_text or 'k' in sal_text.lower()):
                        job_data['salary'] = sal_text
                        break
                except:
                    continue

            # Extract apply URL
            try:
                link_elem = element.find_element(By.CSS_SELECTOR, "a")
                href = link_elem.get_attribute("href")
                if href:
                    job_data['apply_url'] = href
            except:
                pass

            # Extract description (from element text)
            try:
                description = element.text.strip()
                if description and len(description) > 50:
                    # Clean up the description
                    lines = description.split('\n')
                    cleaned_lines = [line.strip() for line in lines if line.strip()]
                    job_data['description'] = ' '.join(cleaned_lines[:10])  # Limit to first 10 lines
            except:
                pass

            # Only return if we have at least a title
            if job_data['title']:
                return job_data
            else:
                return None

        except Exception as e:
            logger.debug(f"Failed to extract job details: {e}")
            return None

    def try_alternative_extraction_methods(self):
        """Try alternative methods to extract job data"""
        try:
            logger.info("🔄 Trying alternative extraction methods...")

            # Method 1: Look for any clickable elements with job-like text
            all_links = self.driver.find_elements(By.TAG_NAME, "a")
            job_keywords = ["engineer", "developer", "software", "senior", "junior", "manager", "analyst"]

            found_jobs = []
            for link in all_links:
                try:
                    link_text = link.text.lower()
                    if any(keyword in link_text for keyword in job_keywords) and len(link.text) > 10:
                        job_data = {
                            'job_id': f"jr_alt_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{len(found_jobs)}",
                            'title': link.text.strip(),
                            'company': 'Unknown',
                            'location': 'Unknown',
                            'salary': '',
                            'job_type': '',
                            'experience_level': '',
                            'description': '',
                            'requirements': '',
                            'benefits': '',
                            'posted_date': '',
                            'apply_url': link.get_attribute("href") or '',
                            'scraped_at': datetime.now(timezone.utc).isoformat(),
                            'extraction_method': 'alternative_link_text'
                        }
                        found_jobs.append(job_data)
                        logger.info(f"🔗 Found job link: {job_data['title']}")
                except:
                    continue

            # Method 2: Look for structured data (JSON-LD)
            try:
                script_elements = self.driver.find_elements(By.XPATH, "//script[@type='application/ld+json']")
                for script in script_elements:
                    try:
                        script_content = script.get_attribute("innerHTML")
                        data = json.loads(script_content)
                        if isinstance(data, dict) and data.get("@type") == "JobPosting":
                            job_data = self.extract_from_structured_data(data)
                            if job_data:
                                found_jobs.append(job_data)
                                logger.info(f"📋 Found structured job: {job_data['title']}")
                    except:
                        continue
            except:
                pass

            # Method 3: Try to find and click pagination or load more buttons
            pagination_selectors = [
                "button[class*='load']", "button[class*='more']",
                ".pagination", ".load-more", ".show-more"
            ]

            for selector in pagination_selectors:
                try:
                    button = self.driver.find_element(By.CSS_SELECTOR, selector)
                    if button.is_displayed() and button.is_enabled():
                        logger.info(f"🔄 Clicking pagination button: {selector}")
                        button.click()
                        time.sleep(5)
                        break
                except:
                    continue

            self.scraped_jobs.extend(found_jobs)

        except Exception as e:
            logger.error(f"❌ Alternative extraction failed: {e}")

    def extract_from_structured_data(self, data: Dict) -> Optional[Dict[str, Any]]:
        """Extract job data from JSON-LD structured data"""
        try:
            job_data = {
                'job_id': f"jr_struct_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                'title': data.get("title", ""),
                'company': data.get("hiringOrganization", {}).get("name", ""),
                'location': data.get("jobLocation", {}).get("address", {}).get("addressLocality", ""),
                'salary': str(data.get("baseSalary", "")),
                'job_type': data.get("employmentType", ""),
                'experience_level': data.get("experienceRequirements", ""),
                'description': data.get("description", ""),
                'requirements': data.get("qualifications", ""),
                'benefits': "",
                'posted_date': data.get("datePosted", ""),
                'apply_url': data.get("url", ""),
                'scraped_at': datetime.now(timezone.utc).isoformat(),
                'extraction_method': 'structured_data'
            }

            if job_data['title']:
                return job_data
            return None

        except Exception as e:
            logger.debug(f"Failed to extract from structured data: {e}")
            return None

    def save_to_clickhouse(self, jobs: List[Dict[str, Any]]):
        """Save jobs to ClickHouse database"""
        if not self.clickhouse_client or not jobs:
            logger.warning("⚠️ No ClickHouse client or no jobs to save")
            return False

        try:
            logger.info(f"💾 Saving {len(jobs)} jobs to ClickHouse...")

            # Prepare data for insertion
            job_rows = []
            for job in jobs:
                row = [
                    job.get('job_id', ''),
                    job.get('title', ''),
                    job.get('company', ''),
                    job.get('location', ''),
                    job.get('salary', ''),
                    job.get('job_type', ''),
                    job.get('experience_level', ''),
                    job.get('description', ''),
                    job.get('requirements', ''),
                    job.get('benefits', ''),
                    job.get('posted_date', ''),
                    job.get('apply_url', ''),
                    datetime.now(timezone.utc)
                ]
                job_rows.append(row)

            # Insert data
            self.clickhouse_client.insert(
                'jobright_jobs',
                job_rows,
                column_names=[
                    'job_id', 'title', 'company', 'location', 'salary',
                    'job_type', 'experience_level', 'description', 'requirements',
                    'benefits', 'posted_date', 'apply_url', 'scraped_at'
                ]
            )

            logger.info("✅ Jobs successfully saved to ClickHouse!")
            return True

        except Exception as e:
            logger.error(f"❌ Failed to save to ClickHouse: {e}")
            return False

    def save_to_json_backup(self, jobs: List[Dict[str, Any]]):
        """Save jobs to JSON file as backup"""
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            json_file = f"{self.output_dir}/jobright_jobs_{timestamp}.json"

            with open(json_file, 'w', encoding='utf-8') as f:
                json.dump({
                    'scraped_at': datetime.now().isoformat(),
                    'total_jobs': len(jobs),
                    'jobs': jobs
                }, f, indent=2, ensure_ascii=False)

            logger.info(f"📄 Jobs saved to JSON backup: {json_file}")
            return json_file

        except Exception as e:
            logger.error(f"❌ Failed to save JSON backup: {e}")
            return None

    def verify_clickhouse_data(self):
        """Verify data was saved correctly to ClickHouse"""
        if not self.clickhouse_client:
            return False

        try:
            # Query recent jobs
            result = self.clickhouse_client.query(
                "SELECT COUNT(*) as total_jobs FROM jobright_jobs WHERE scraped_at >= now() - INTERVAL 1 HOUR"
            )

            total_jobs = result.result_rows[0][0] if result.result_rows else 0
            logger.info(f"✅ ClickHouse verification: {total_jobs} jobs found in last hour")

            # Get sample jobs
            sample_result = self.clickhouse_client.query(
                "SELECT title, company, location FROM jobright_jobs WHERE scraped_at >= now() - INTERVAL 1 HOUR LIMIT 5"
            )

            logger.info("📋 Sample jobs in ClickHouse:")
            for row in sample_result.result_rows:
                logger.info(f"   - {row[0]} at {row[1]} ({row[2]})")

            return True

        except Exception as e:
            logger.error(f"❌ ClickHouse verification failed: {e}")
            return False

    def run_scraping_workflow(self):
        """Run the complete scraping workflow"""
        try:
            logger.info("🚀 STARTING JOBRIGHT.AI SCRAPING WITH CLICKHOUSE INTEGRATION")
            logger.info("=" * 70)

            # Step 1: Navigate to JobRight
            if not self.navigate_to_jobright():
                logger.error("Failed to navigate to JobRight")
                return False

            # Step 2: Extract job listings
            jobs = self.extract_job_listings()

            if not jobs:
                logger.warning("⚠️ No jobs extracted")
                return False

            # Step 3: Save to ClickHouse
            clickhouse_success = self.save_to_clickhouse(jobs)

            # Step 4: Save JSON backup
            json_file = self.save_to_json_backup(jobs)

            # Step 5: Verify ClickHouse data
            if clickhouse_success:
                self.verify_clickhouse_data()

            # Final summary
            logger.info("\n" + "=" * 70)
            logger.info("🎉 SCRAPING COMPLETED!")
            logger.info("=" * 70)
            logger.info(f"📊 Total jobs scraped: {len(jobs)}")
            logger.info(f"💾 ClickHouse saved: {'✅ YES' if clickhouse_success else '❌ NO'}")
            logger.info(f"📄 JSON backup: {json_file}")
            logger.info(f"📁 Output directory: {self.output_dir}")

            return True

        except Exception as e:
            logger.error(f"❌ Scraping workflow failed: {e}")
            return False
        finally:
            if hasattr(self, 'driver'):
                self.driver.quit()

def main():
    """Main function"""
    scraper = JobRightClickHouseScraper()
    success = scraper.run_scraping_workflow()

    if success:
        print("\n✅ JobRight scraping completed successfully!")
    else:
        print("\n❌ JobRight scraping failed!")

    return success

if __name__ == "__main__":
    main()