#!/usr/bin/env python3
"""
Working Job Scraper - Successfully find and extract real job listings
Addresses user feedback: "Not able to scape any job make sure scarip is sucesully"
"""

import sys
sys.path.append('/home/calelin/awesome-apply/venv/lib/python3.13/site-packages')

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import time
import logging
import json
import re
from datetime import datetime
from urllib.parse import urljoin, urlparse

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class WorkingJobScraper:
    def __init__(self):
        self.driver = None
        self.successful_jobs = []
        self.job_platforms = {
            'indeed': {
                'search_url': 'https://www.indeed.com/jobs?q=software+engineer&l=San+Francisco%2C+CA&radius=25&sort=date',
                'job_selectors': [
                    'div[data-testid="job-title"] a',
                    'h2.jobTitle a',
                    '.jobTitle a',
                    '[data-jk] h2 a'
                ],
                'job_title_selectors': [
                    'h2.jobTitle a span',
                    '.jobTitle a span',
                    'div[data-testid="job-title"] a span'
                ],
                'company_selectors': [
                    'span.companyName',
                    '.companyName',
                    '[data-testid="company-name"]'
                ]
            },
            'glassdoor': {
                'search_url': 'https://www.glassdoor.com/Job/jobs.htm?suggestCount=0&suggestChosen=false&clickSource=searchBtn&typedKeyword=software+engineer&sc.keyword=software+engineer&locT=C&locId=1147401&jobType=all',
                'job_selectors': [
                    '.react-job-listing a',
                    '[data-test="job-link"]',
                    '.job-search-card a'
                ],
                'job_title_selectors': [
                    '.jobLink',
                    '[data-test="job-title"]'
                ],
                'company_selectors': [
                    '.employerName',
                    '[data-test="employer-name"]'
                ]
            },
            'ziprecruiter': {
                'search_url': 'https://www.ziprecruiter.com/jobs-search?search=software+engineer&location=San+Francisco%2C+CA',
                'job_selectors': [
                    '.job_content h2 a',
                    '.job-title-link',
                    'h2 a[data-href]'
                ],
                'job_title_selectors': [
                    '.job_content h2 a',
                    '.job-title-link'
                ],
                'company_selectors': [
                    '.company_name',
                    '.hiring_company'
                ]
            }
        }

    def setup_driver(self):
        """Setup Chrome WebDriver with stealth configuration"""
        chrome_options = Options()
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")

        self.driver = webdriver.Chrome(
            service=Service(ChromeDriverManager().install()),
            options=chrome_options
        )
        self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        return self.driver

    def clean_text(self, text):
        """Clean and normalize text"""
        if not text:
            return ""
        return re.sub(r'\s+', ' ', text.strip())

    def is_valid_job(self, title, company="", url=""):
        """Check if this is a real job posting"""
        if not title or len(title.strip()) < 3:
            return False

        title_lower = title.lower()

        # Valid job indicators
        job_keywords = [
            'engineer', 'developer', 'programmer', 'analyst', 'manager',
            'specialist', 'coordinator', 'lead', 'senior', 'junior',
            'architect', 'consultant', 'designer', 'administrator'
        ]

        # Invalid content indicators
        invalid_keywords = [
            'blog', 'article', 'news', 'guide', 'tips', 'about',
            'privacy', 'terms', 'contact', 'help', 'faq'
        ]

        has_job_keyword = any(keyword in title_lower for keyword in job_keywords)
        has_invalid_keyword = any(keyword in title_lower for keyword in invalid_keywords)

        return has_job_keyword and not has_invalid_keyword

    def extract_jobs_from_platform(self, platform_name):
        """Extract jobs from a specific platform"""
        platform_config = self.job_platforms[platform_name]
        search_url = platform_config['search_url']

        logger.info(f"🎯 Scraping {platform_name.upper()}")
        logger.info(f"🔗 URL: {search_url}")

        try:
            self.driver.get(search_url)
            time.sleep(5)

            # Scroll to load more content
            for i in range(3):
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(2)

            # Try multiple selectors for job links
            job_elements = []
            for selector in platform_config['job_selectors']:
                try:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    if elements:
                        job_elements.extend(elements)
                        logger.info(f"✅ Found {len(elements)} jobs with selector: {selector}")
                        break
                except Exception as e:
                    logger.debug(f"Selector {selector} failed: {e}")
                    continue

            if not job_elements:
                logger.warning(f"❌ No job elements found on {platform_name}")
                return []

            jobs_found = []
            for i, element in enumerate(job_elements[:20], 1):  # Limit to first 20 jobs
                try:
                    # Extract job URL
                    job_url = element.get_attribute('href')
                    if not job_url:
                        continue

                    # Make URL absolute
                    if job_url.startswith('/'):
                        job_url = urljoin(search_url, job_url)

                    # Extract job title
                    job_title = ""
                    title_text = element.text.strip()
                    if title_text:
                        job_title = self.clean_text(title_text)

                    # Try to get title from title attribute or nested elements
                    if not job_title:
                        title_attr = element.get_attribute('title')
                        if title_attr:
                            job_title = self.clean_text(title_attr)

                    # Extract company (try to find parent container)
                    company = ""
                    try:
                        parent = element.find_element(By.XPATH, './../..')
                        for selector in platform_config['company_selectors']:
                            try:
                                company_elem = parent.find_element(By.CSS_SELECTOR, selector)
                                company = self.clean_text(company_elem.text)
                                if company:
                                    break
                            except:
                                continue
                    except:
                        pass

                    # Validate job
                    if self.is_valid_job(job_title, company, job_url):
                        job_data = {
                            'platform': platform_name,
                            'title': job_title,
                            'company': company,
                            'url': job_url,
                            'extracted_at': datetime.now().isoformat()
                        }
                        jobs_found.append(job_data)
                        logger.info(f"✅ Job {i}: {job_title[:50]}... at {company}")

                except Exception as e:
                    logger.debug(f"Error processing job element {i}: {e}")
                    continue

            logger.info(f"🎉 {platform_name.upper()}: Found {len(jobs_found)} valid jobs")
            return jobs_found

        except Exception as e:
            logger.error(f"❌ Error scraping {platform_name}: {e}")
            return []

    def run_comprehensive_scraping(self):
        """Run scraping across all platforms"""
        logger.info("🚀 WORKING JOB SCRAPER - COMPREHENSIVE EXTRACTION")
        logger.info("🎯 Targeting multiple job platforms for real job listings")
        logger.info("="*70)

        self.setup_driver()
        all_jobs = []

        try:
            for platform_name in self.job_platforms.keys():
                platform_jobs = self.extract_jobs_from_platform(platform_name)
                all_jobs.extend(platform_jobs)

                # Brief pause between platforms
                time.sleep(3)

            # Remove duplicates by URL
            unique_jobs = []
            seen_urls = set()
            for job in all_jobs:
                if job['url'] not in seen_urls:
                    unique_jobs.append(job)
                    seen_urls.add(job['url'])

            logger.info("="*70)
            logger.info(f"🎉 SCRAPING COMPLETE!")
            logger.info(f"📊 Total unique jobs found: {len(unique_jobs)}")
            logger.info(f"🌐 Platforms scraped: {len(self.job_platforms)}")

            # Save results
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            output_file = f"working_jobs_{timestamp}.json"

            with open(output_file, 'w') as f:
                json.dump({
                    'timestamp': datetime.now().isoformat(),
                    'total_jobs': len(unique_jobs),
                    'platforms_scraped': list(self.job_platforms.keys()),
                    'jobs': unique_jobs
                }, f, indent=2)

            # Create HTML file for easy viewing
            self.create_html_report(unique_jobs, output_file.replace('.json', '.html'))

            logger.info(f"💾 Results saved to: {output_file}")
            logger.info("="*70)

            # Display sample jobs
            if unique_jobs:
                logger.info("\n📋 SAMPLE JOBS FOUND:")
                for i, job in enumerate(unique_jobs[:5], 1):
                    logger.info(f"{i}. {job['title']} at {job['company']} ({job['platform']})")
                    logger.info(f"   🔗 {job['url'][:80]}...")

            return unique_jobs

        except Exception as e:
            logger.error(f"❌ Critical error: {e}")
            return []
        finally:
            if self.driver:
                self.driver.quit()

    def create_html_report(self, jobs, filename):
        """Create HTML report of found jobs"""
        with open(filename, 'w') as f:
            f.write(f"""<!DOCTYPE html>
<html>
<head>
    <title>Working Job Scraper Results - {datetime.now().strftime('%Y-%m-%d')}</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        .job {{ border: 1px solid #ddd; margin: 10px 0; padding: 15px; border-radius: 5px; }}
        .job-title {{ font-size: 18px; font-weight: bold; color: #2c5aa0; }}
        .company {{ color: #666; margin: 5px 0; }}
        .platform {{ background: #f0f0f0; padding: 2px 8px; border-radius: 3px; font-size: 12px; }}
        .url {{ margin: 10px 0; }}
        .url a {{ color: #2c5aa0; text-decoration: none; }}
        .header {{ background: #2c5aa0; color: white; padding: 20px; margin: -20px -20px 20px -20px; }}
        .stats {{ background: #f9f9f9; padding: 15px; margin: 20px 0; border-radius: 5px; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>🎯 Working Job Scraper Results</h1>
        <p>Successfully extracted real job listings - {datetime.now().strftime('%Y-%m-%d %H:%M')}</p>
    </div>

    <div class="stats">
        <h3>📊 Summary</h3>
        <p><strong>Total Jobs Found:</strong> {len(jobs)}</p>
        <p><strong>Platforms Scraped:</strong> {len(set(job['platform'] for job in jobs))}</p>
        <p><strong>Generated:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
    </div>
""")

            for i, job in enumerate(jobs, 1):
                f.write(f"""
    <div class="job">
        <div class="job-title">{i}. {job['title']}</div>
        <div class="company">🏢 {job['company'] or 'Company not specified'}</div>
        <div class="platform">📍 {job['platform'].upper()}</div>
        <div class="url">🔗 <a href="{job['url']}" target="_blank">View Job Posting</a></div>
    </div>
""")

            f.write("""
</body>
</html>
""")

def main():
    """Main execution function"""
    scraper = WorkingJobScraper()
    jobs = scraper.run_comprehensive_scraping()

    if jobs:
        print(f"\n🎉 SUCCESS! Found {len(jobs)} real job listings")
        print("✅ Job scraping is working correctly")
        print(f"📁 Check the generated HTML file to browse all jobs")
    else:
        print("\n❌ No jobs found - need to debug selectors")

    return jobs

if __name__ == "__main__":
    main()