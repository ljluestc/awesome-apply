#!/usr/bin/env python3
"""
Terminal Job Scraper with Full Raw Response Display
Real-time job scraping with comprehensive logging and rate limiting bypass
"""

import time
import json
import logging
import random
import re
import sys
import os
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlencode, quote_plus

# Enhanced logging setup
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('terminal_job_scraper.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

@dataclass
class Job:
    id: str
    title: str
    company: str
    location: str
    salary: Optional[str]
    description: str
    url: str
    apply_url: Optional[str]
    posted_date: str
    job_type: str
    experience_level: str
    source: str
    scraped_at: str
    raw_html: str = ""
    extraction_method: str = ""
    confidence_score: float = 0.0

class TerminalJobScraper:
    def __init__(self, show_browser=True):
        self.show_browser = show_browser
        self.driver = None
        self.jobs_found = []
        self.raw_responses = []
        self.session = requests.Session()
        self.setup_session()

    def setup_session(self):
        """Setup requests session with rotating headers"""
        user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        ]

        self.session.headers.update({
            'User-Agent': random.choice(user_agents),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        })

    def setup_driver(self):
        """Setup Chrome driver with advanced anti-detection"""
        chrome_options = Options()

        if not self.show_browser:
            chrome_options.add_argument("--headless")

        # Stealth options
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_argument("--disable-web-security")
        chrome_options.add_argument("--window-size=1920,1080")

        # Anti-detection
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)

        user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        ]

        chosen_ua = random.choice(user_agents)
        chrome_options.add_argument(f"--user-agent={chosen_ua}")

        try:
            self.driver = webdriver.Chrome(options=chrome_options)
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

            print(f"✅ Chrome driver initialized")
            return True
        except Exception as e:
            print(f"❌ Failed to setup Chrome driver: {e}")
            return False

    def scrape_jobs_real_time(self, keywords, location, max_jobs=50):
        """Scrape jobs in real-time with full terminal output"""
        print("\n" + "="*80)
        print(f"🚀 STARTING REAL-TIME JOB SCRAPING")
        print(f"📋 Keywords: {keywords}")
        print(f"📍 Location: {location}")
        print(f"🎯 Target: {max_jobs} jobs")
        print("="*80)

        if not self.setup_driver():
            print("❌ Failed to setup driver")
            return []

        all_jobs = []

        try:
            # Method 1: LinkedIn Jobs
            linkedin_jobs = self._scrape_linkedin_comprehensive(keywords, location, max_jobs)
            all_jobs.extend(linkedin_jobs)

            # Remove duplicates
            unique_jobs = self._remove_duplicates(all_jobs)

            print(f"\n🎉 SCRAPING COMPLETE!")
            print(f"📊 Total unique jobs found: {len(unique_jobs)}")

            # Display all jobs in terminal
            self._display_jobs_terminal(unique_jobs)

            # Save raw responses
            self._save_raw_responses(unique_jobs)

            return unique_jobs

        finally:
            if self.driver:
                self.driver.quit()

    def _scrape_linkedin_comprehensive(self, keywords, location, max_jobs):
        """Comprehensive LinkedIn scraping with full logging"""
        print(f"\n🔍 SCRAPING LINKEDIN - Target: {max_jobs} jobs")
        print("-" * 60)

        jobs = []

        try:
            # Build URL
            params = {
                'keywords': keywords,
                'location': location,
                'sortBy': 'DD',
                'f_TPR': 'r604800',  # Past week
                'start': 0
            }

            url = f"https://www.linkedin.com/jobs/search?{urlencode(params)}"
            print(f"🌐 URL: {url}")

            self.driver.get(url)
            time.sleep(random.uniform(3, 6))

            # Log page details
            print(f"📄 Page title: {self.driver.title}")
            print(f"📄 Current URL: {self.driver.current_url}")

            # Save raw HTML
            raw_html = self.driver.page_source
            print(f"📄 Page source length: {len(raw_html)} characters")

            self.raw_responses.append({
                'source': 'linkedin',
                'url': self.driver.current_url,
                'html_preview': raw_html[:5000],  # First 5000 chars
                'full_html_length': len(raw_html),
                'timestamp': datetime.now().isoformat()
            })

            # Multiple job finding strategies
            job_selectors = [
                ".jobs-search__results-list li",
                ".job-search-card",
                ".result-card",
                "[data-entity-urn*='jobPosting']",
                ".jobs-search-results__list-item"
            ]

            job_cards = []
            for selector in job_selectors:
                try:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    if elements:
                        job_cards = elements
                        print(f"✅ Found {len(job_cards)} job cards with selector: {selector}")
                        break
                except Exception as e:
                    print(f"❌ Selector '{selector}' failed: {e}")

            if not job_cards:
                print("⚠️ No job cards found with standard selectors, trying alternative...")
                # Scroll and try again
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight/2);")
                time.sleep(3)

                # Try to find any elements with job-related text
                all_elements = self.driver.find_elements(By.XPATH, "//*[contains(text(), 'Engineer') or contains(text(), 'Developer') or contains(text(), 'Manager')]")
                print(f"🔄 Found {len(all_elements)} elements with job-related text")

                # Get their parent containers
                parent_elements = set()
                for elem in all_elements[:50]:  # Limit to first 50
                    try:
                        parent = elem.find_element(By.XPATH, "..")
                        parent_elements.add(parent)
                    except:
                        continue

                job_cards = list(parent_elements)
                print(f"🔄 Using {len(job_cards)} parent elements as job cards")

            # Extract jobs from cards
            for i, card in enumerate(job_cards[:max_jobs]):
                print(f"\n📋 Processing job card {i+1}/{min(len(job_cards), max_jobs)}")

                try:
                    job = self._extract_linkedin_job_detailed(card, i)
                    if job:
                        jobs.append(job)
                        print(f"✅ Extracted: {job.title} at {job.company}")
                        print(f"   📍 Location: {job.location}")
                        print(f"   🔗 URL: {job.url[:80] if job.url else 'No URL'}...")
                        print(f"   🎯 Confidence: {job.confidence_score:.2f}")
                    else:
                        print(f"❌ Failed to extract job from card {i+1}")

                except Exception as e:
                    print(f"❌ Error processing card {i+1}: {e}")

                # Human-like delay
                time.sleep(random.uniform(0.5, 2.0))

        except Exception as e:
            print(f"❌ LinkedIn scraping error: {e}")

        print(f"\n✅ LinkedIn scraping complete: {len(jobs)} jobs extracted")
        return jobs

    def _extract_linkedin_job_detailed(self, card, index):
        """Extract job with detailed logging and multiple strategies"""
        job_data = {
            'title': '',
            'company': '',
            'location': '',
            'url': '',
            'salary': '',
            'description': '',
            'extraction_method': '',
            'confidence_score': 0.0
        }

        # Strategy 1: Standard LinkedIn selectors
        print(f"   🔍 Strategy 1: Standard selectors...")
        try:
            # Title selectors
            title_selectors = [
                "h3 a[data-control-name='job_search_job_title']",
                ".job-search-card__title a",
                "h3 a",
                ".result-card__title a",
                "h2 a",
                "a[href*='/jobs/view/']"
            ]

            for selector in title_selectors:
                try:
                    title_elem = card.find_element(By.CSS_SELECTOR, selector)
                    job_data['title'] = title_elem.text.strip()
                    job_data['url'] = title_elem.get_attribute('href') or ''
                    print(f"      ✅ Title found: {job_data['title']}")
                    break
                except:
                    continue

            # Company selectors
            company_selectors = [
                ".job-search-card__subtitle a",
                "h4 a",
                ".job-search-card__subtitle",
                ".result-card__subtitle",
                "h4",
                "[data-test='job-company']"
            ]

            for selector in company_selectors:
                try:
                    company_elem = card.find_element(By.CSS_SELECTOR, selector)
                    job_data['company'] = company_elem.text.strip()
                    print(f"      ✅ Company found: {job_data['company']}")
                    break
                except:
                    continue

            # Location selectors
            location_selectors = [
                ".job-search-card__location",
                ".job-result-card__location",
                ".result-card__location",
                "[data-test='job-location']"
            ]

            for selector in location_selectors:
                try:
                    location_elem = card.find_element(By.CSS_SELECTOR, selector)
                    job_data['location'] = location_elem.text.strip()
                    print(f"      ✅ Location found: {job_data['location']}")
                    break
                except:
                    continue

            if job_data['title'] and job_data['company']:
                job_data['extraction_method'] = 'standard_selectors'
                job_data['confidence_score'] = 0.9
            else:
                print(f"      ⚠️ Standard selectors incomplete")

        except Exception as e:
            print(f"      ❌ Standard selectors failed: {e}")

        # Strategy 2: Text-based extraction
        if not job_data['title'] or not job_data['company']:
            print(f"   🔍 Strategy 2: Text-based extraction...")
            try:
                card_text = card.text
                lines = [line.strip() for line in card_text.split('\n') if line.strip()]

                print(f"      📝 Card text preview: {card_text[:200]}...")

                # Look for job title patterns
                job_title_patterns = [
                    r'(Senior|Junior|Lead|Principal)?\s*(Software|Data|Full Stack|DevOps|Python|Java)?\s*(Engineer|Developer|Scientist|Analyst|Manager)',
                    r'^([A-Z][a-zA-Z\s&-]+(?:Engineer|Developer|Manager|Analyst|Scientist|Specialist|Director))'
                ]

                for pattern in job_title_patterns:
                    for line in lines:
                        match = re.search(pattern, line, re.IGNORECASE)
                        if match and len(match.group()) > 5:
                            if not job_data['title']:
                                job_data['title'] = match.group().strip()
                                print(f"      ✅ Title extracted: {job_data['title']}")
                            break
                    if job_data['title']:
                        break

                # Extract company (usually after title)
                for i, line in enumerate(lines):
                    if job_data['title'] and job_data['title'].lower() in line.lower():
                        if i + 1 < len(lines):
                            potential_company = lines[i + 1].strip()
                            if len(potential_company) > 2 and len(potential_company) < 60:
                                job_data['company'] = potential_company
                                print(f"      ✅ Company extracted: {job_data['company']}")
                        break

                # Extract location patterns
                location_patterns = [
                    r'([A-Z][a-zA-Z\s]+,\s*[A-Z]{2})',  # City, State
                    r'(Remote|Hybrid)',
                    r'([A-Z][a-zA-Z\s]+,\s*[A-Z][a-zA-Z\s]+)'  # City, Country
                ]

                for pattern in location_patterns:
                    for line in lines:
                        match = re.search(pattern, line)
                        if match:
                            job_data['location'] = match.group().strip()
                            print(f"      ✅ Location extracted: {job_data['location']}")
                            break
                    if job_data['location']:
                        break

                if job_data['title']:
                    job_data['extraction_method'] = 'text_based'
                    job_data['confidence_score'] = 0.7

            except Exception as e:
                print(f"      ❌ Text-based extraction failed: {e}")

        # Strategy 3: URL extraction
        if not job_data['url']:
            print(f"   🔍 Strategy 3: URL extraction...")
            try:
                links = card.find_elements(By.TAG_NAME, "a")
                for link in links:
                    href = link.get_attribute('href')
                    if href and '/jobs/view/' in href:
                        job_data['url'] = href
                        print(f"      ✅ URL found: {href[:60]}...")
                        break
            except Exception as e:
                print(f"      ❌ URL extraction failed: {e}")

        # Create job object
        if job_data['title'] and job_data['company']:
            job_id = f"linkedin_{hash(job_data['title'] + job_data['company'])}_{int(time.time())}_{index}"

            job = Job(
                id=job_id,
                title=job_data['title'],
                company=job_data['company'],
                location=job_data['location'] or 'Location not specified',
                salary=job_data['salary'],
                description=job_data['description'],
                url=job_data['url'],
                apply_url=job_data['url'],
                posted_date=datetime.now().isoformat(),
                job_type='full-time',
                experience_level='mid',
                source='linkedin',
                scraped_at=datetime.now().isoformat(),
                raw_html=card.get_attribute('outerHTML')[:1000] if hasattr(card, 'get_attribute') else '',
                extraction_method=job_data['extraction_method'],
                confidence_score=job_data['confidence_score']
            )

            return job
        else:
            print(f"      ❌ Insufficient data: title='{job_data['title']}', company='{job_data['company']}'")
            return None

    def _remove_duplicates(self, jobs):
        """Remove duplicate jobs"""
        seen = set()
        unique_jobs = []

        for job in jobs:
            key = (job.title.lower().strip(), job.company.lower().strip())
            if key not in seen:
                seen.add(key)
                unique_jobs.append(job)

        return unique_jobs

    def _display_jobs_terminal(self, jobs):
        """Display all jobs in terminal with detailed info"""
        print("\n" + "="*100)
        print(f"📋 COMPLETE JOB LIST - {len(jobs)} JOBS FOUND")
        print("="*100)

        for i, job in enumerate(jobs, 1):
            print(f"\n🔢 JOB #{i}")
            print(f"📌 Title: {job.title}")
            print(f"🏢 Company: {job.company}")
            print(f"📍 Location: {job.location}")
            print(f"💰 Salary: {job.salary or 'Not specified'}")
            print(f"🔗 URL: {job.url}")
            print(f"🎯 Source: {job.source}")
            print(f"📊 Confidence: {job.confidence_score:.2f}")
            print(f"🔧 Method: {job.extraction_method}")
            print(f"⏰ Scraped: {job.scraped_at}")
            print("-" * 80)

        # Summary statistics
        print(f"\n📊 SUMMARY STATISTICS:")
        sources = {}
        for job in jobs:
            sources[job.source] = sources.get(job.source, 0) + 1

        for source, count in sources.items():
            print(f"   {source.upper()}: {count} jobs")

        avg_confidence = sum(job.confidence_score for job in jobs) / len(jobs) if jobs else 0
        print(f"   Average confidence score: {avg_confidence:.2f}")

    def _save_raw_responses(self, jobs):
        """Save all raw responses to files"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # Save raw responses
        with open(f"raw_responses_{timestamp}.json", "w") as f:
            json.dump(self.raw_responses, f, indent=2, default=str)

        # Save jobs data
        jobs_data = [asdict(job) for job in jobs]
        with open(f"scraped_jobs_{timestamp}.json", "w") as f:
            json.dump(jobs_data, f, indent=2)

        print(f"\n💾 Raw responses saved to: raw_responses_{timestamp}.json")
        print(f"💾 Jobs data saved to: scraped_jobs_{timestamp}.json")

def main():
    """Main function to run terminal job scraper"""
    print("🚀 TERMINAL JOB SCRAPER - REAL-TIME DEMONSTRATION")
    print("=" * 80)

    # Default parameters for testing
    keywords = "Software Engineer"
    location = "San Francisco, CA"
    max_jobs = 30
    show_browser = True

    print(f"\n🎯 Starting scrape for: '{keywords}' in '{location}' (max {max_jobs} jobs)")
    print(f"🖥️ Browser visible: {show_browser}")

    # Start scraping
    scraper = TerminalJobScraper(show_browser=show_browser)

    try:
        jobs = scraper.scrape_jobs_real_time(keywords, location, max_jobs)

        if jobs:
            print(f"\n🎉 SUCCESS! Found {len(jobs)} real jobs")
            print("📁 Check the generated JSON files for raw responses and job data")
        else:
            print("❌ No jobs found. Check your keywords and location.")

    except KeyboardInterrupt:
        print("\n⏹️ Scraping interrupted by user")
    except Exception as e:
        print(f"\n❌ Scraping failed: {e}")

if __name__ == "__main__":
    main()