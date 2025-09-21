#!/usr/bin/env python3
"""
Robust Job Scraper with Multiple Sources
Combines LinkedIn, Indeed, and other job boards for comprehensive results
"""

import time
import json
import logging
import random
import re
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
from urllib.parse import urlencode, quote_plus, urlparse

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
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
    application_status: str = "not_applied"
    automation_score: float = 0.0
    tags: List[str] = None

    def __post_init__(self):
        if self.tags is None:
            self.tags = []

@dataclass
class SearchCriteria:
    keywords: List[str]
    location: str
    experience_level: str
    job_type: str
    salary_min: Optional[int]
    salary_max: Optional[int]
    date_posted: str
    company_size: Optional[str]
    remote_ok: bool

class RobustJobScraper:
    def __init__(self, headless=True):
        self.headless = headless
        self.driver = None
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
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        })

    def setup_driver(self):
        """Setup Chrome driver with stealth options"""
        chrome_options = Options()

        if self.headless:
            chrome_options.add_argument("--headless")

        # Stealth options
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_argument("--disable-web-security")
        chrome_options.add_argument("--allow-running-insecure-content")
        chrome_options.add_argument("--window-size=1920,1080")

        # Anti-detection
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)

        # Random user agent
        user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        ]
        chrome_options.add_argument(f"--user-agent={random.choice(user_agents)}")

        try:
            self.driver = webdriver.Chrome(options=chrome_options)
            # Anti-detection scripts
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            logger.info("✅ Driver setup successful")
            return True
        except Exception as e:
            logger.error(f"❌ Driver setup failed: {e}")
            return False

    def search_jobs(self, criteria: SearchCriteria) -> List[Job]:
        """Search jobs from multiple sources"""
        logger.info(f"🔍 Starting multi-source job search for: {criteria.keywords}")

        all_jobs = []

        # Source 1: LinkedIn
        try:
            linkedin_jobs = self._search_linkedin(criteria)
            all_jobs.extend(linkedin_jobs)
            logger.info(f"✅ LinkedIn: {len(linkedin_jobs)} jobs")
        except Exception as e:
            logger.error(f"❌ LinkedIn search failed: {e}")

        # Source 2: Indeed
        try:
            indeed_jobs = self._search_indeed(criteria)
            all_jobs.extend(indeed_jobs)
            logger.info(f"✅ Indeed: {len(indeed_jobs)} jobs")
        except Exception as e:
            logger.error(f"❌ Indeed search failed: {e}")

        # Source 3: SimplyHired
        try:
            simply_jobs = self._search_simplyhired(criteria)
            all_jobs.extend(simply_jobs)
            logger.info(f"✅ SimplyHired: {len(simply_jobs)} jobs")
        except Exception as e:
            logger.error(f"❌ SimplyHired search failed: {e}")

        # Remove duplicates and return
        unique_jobs = self._remove_duplicates(all_jobs)
        logger.info(f"🎯 Total unique jobs: {len(unique_jobs)}")

        return unique_jobs

    def _search_linkedin(self, criteria: SearchCriteria) -> List[Job]:
        """Search LinkedIn jobs"""
        if not self.setup_driver():
            return []

        jobs = []

        try:
            # Build LinkedIn URL
            keywords = " ".join(criteria.keywords)
            params = {
                'keywords': keywords,
                'location': criteria.location,
                'sortBy': 'DD'
            }

            # Add filters
            if criteria.remote_ok:
                params['f_WT'] = '2'

            if criteria.experience_level:
                exp_map = {'entry': '1', 'associate': '2', 'mid': '3', 'senior': '4', 'director': '5'}
                if criteria.experience_level.lower() in exp_map:
                    params['f_E'] = exp_map[criteria.experience_level.lower()]

            url = f"https://www.linkedin.com/jobs/search?{urlencode(params)}"
            logger.info(f"LinkedIn URL: {url}")

            self.driver.get(url)
            time.sleep(5)

            # Handle potential login prompt
            if "authwall" in self.driver.current_url or "login" in self.driver.current_url:
                logger.warning("LinkedIn requires login, using guest access")
                guest_url = url.replace('/jobs/search', '/jobs-guest/jobs/api/seeMoreJobPostings/search')
                response = self.session.get(guest_url)
                if response.status_code == 200:
                    soup = BeautifulSoup(response.text, 'html.parser')
                    return self._parse_linkedin_guest_results(soup, criteria)

            # Find job cards
            self._wait_for_jobs_to_load()

            job_cards = []
            selectors = [
                ".jobs-search__results-list li",
                ".job-search-card",
                ".result-card",
                "[data-entity-urn*='jobPosting']"
            ]

            for selector in selectors:
                try:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    if elements:
                        job_cards = elements[:20]  # Limit to first 20
                        logger.info(f"Found {len(job_cards)} jobs with selector: {selector}")
                        break
                except:
                    continue

            # Extract job data
            for i, card in enumerate(job_cards):
                try:
                    job = self._extract_linkedin_job(card, i)
                    if job:
                        jobs.append(job)
                except Exception as e:
                    logger.debug(f"Error extracting LinkedIn job {i}: {e}")
                    continue

        finally:
            if self.driver:
                self.driver.quit()

        return jobs

    def _search_indeed(self, criteria: SearchCriteria) -> List[Job]:
        """Search Indeed jobs"""
        jobs = []

        try:
            keywords = "+".join(criteria.keywords)
            location = quote_plus(criteria.location)

            url = f"https://www.indeed.com/jobs?q={keywords}&l={location}&sort=date"

            if criteria.remote_ok:
                url += "&remotejob=032b3046-06a3-4876-8dfd-474eb5e7ed11"

            logger.info(f"Indeed URL: {url}")

            response = self.session.get(url, timeout=10)

            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')

                # Find job cards
                job_cards = soup.find_all(['div', 'article'], class_=lambda x: x and any(keyword in x.lower() for keyword in ['job', 'result']))

                for i, card in enumerate(job_cards[:15]):  # Limit to 15 jobs
                    try:
                        job = self._extract_indeed_job(card, i)
                        if job:
                            jobs.append(job)
                    except Exception as e:
                        logger.debug(f"Error extracting Indeed job {i}: {e}")
                        continue

        except Exception as e:
            logger.error(f"Indeed search error: {e}")

        return jobs

    def _search_simplyhired(self, criteria: SearchCriteria) -> List[Job]:
        """Search SimplyHired jobs"""
        jobs = []

        try:
            keywords = "+".join(criteria.keywords)
            location = quote_plus(criteria.location)

            url = f"https://www.simplyhired.com/search?q={keywords}&l={location}"

            response = self.session.get(url, timeout=10)

            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')

                # Find job cards
                job_cards = soup.find_all('article', class_=lambda x: x and 'job' in x.lower())

                for i, card in enumerate(job_cards[:10]):  # Limit to 10 jobs
                    try:
                        job = self._extract_simplyhired_job(card, i)
                        if job:
                            jobs.append(job)
                    except Exception as e:
                        logger.debug(f"Error extracting SimplyHired job {i}: {e}")
                        continue

        except Exception as e:
            logger.error(f"SimplyHired search error: {e}")

        return jobs

    def _extract_linkedin_job(self, card, index) -> Optional[Job]:
        """Extract job from LinkedIn card"""
        try:
            # Try multiple approaches
            job_data = {}

            # Method 1: Standard selectors
            title_selectors = ["h3 a", ".job-search-card__title a", "h3", "h2"]
            company_selectors = [".job-search-card__subtitle a", "h4 a", ".job-search-card__subtitle"]
            location_selectors = [".job-search-card__location", ".job-result-card__location"]

            for selector in title_selectors:
                try:
                    elem = card.find_element(By.CSS_SELECTOR, selector)
                    job_data['title'] = elem.text.strip()
                    if elem.tag_name == 'a':
                        job_data['url'] = elem.get_attribute('href')
                    break
                except:
                    continue

            for selector in company_selectors:
                try:
                    elem = card.find_element(By.CSS_SELECTOR, selector)
                    job_data['company'] = elem.text.strip()
                    break
                except:
                    continue

            for selector in location_selectors:
                try:
                    elem = card.find_element(By.CSS_SELECTOR, selector)
                    job_data['location'] = elem.text.strip()
                    break
                except:
                    continue

            # Method 2: Text parsing if selectors fail
            if not job_data.get('title'):
                card_text = card.text
                lines = [line.strip() for line in card_text.split('\n') if line.strip()]

                if lines:
                    job_data['title'] = lines[0]
                    if len(lines) > 1:
                        job_data['company'] = lines[1]
                    if len(lines) > 2:
                        job_data['location'] = lines[2]

            # Create job object
            if job_data.get('title'):
                job_id = f"linkedin_{hash(job_data.get('title', ''))}_{int(time.time())}_{index}"

                return Job(
                    id=job_id,
                    title=job_data.get('title', 'Unknown Title'),
                    company=job_data.get('company', 'Unknown Company'),
                    location=job_data.get('location', 'Unknown Location'),
                    salary=None,
                    description="",
                    url=job_data.get('url', ''),
                    apply_url=job_data.get('url', ''),
                    posted_date=datetime.now().isoformat(),
                    job_type="full-time",
                    experience_level="mid",
                    source="linkedin",
                    scraped_at=datetime.now().isoformat()
                )

        except Exception as e:
            logger.debug(f"LinkedIn extraction error: {e}")

        return None

    def _extract_indeed_job(self, card, index) -> Optional[Job]:
        """Extract job from Indeed card"""
        try:
            title_elem = card.find('h2') or card.find(['span', 'a'], title=True)
            company_elem = card.find('span', class_=lambda x: x and 'company' in x.lower()) or card.find('a', class_=lambda x: x and 'company' in x.lower())
            location_elem = card.find(['div', 'span'], class_=lambda x: x and 'location' in x.lower())

            title = title_elem.get_text(strip=True) if title_elem else f"Position #{index + 1}"
            company = company_elem.get_text(strip=True) if company_elem else "Company Name"
            location = location_elem.get_text(strip=True) if location_elem else "Location"

            # Get job URL
            url = ""
            link_elem = card.find('a', href=True)
            if link_elem:
                href = link_elem['href']
                if href.startswith('/'):
                    url = f"https://www.indeed.com{href}"
                else:
                    url = href

            job_id = f"indeed_{hash(title)}_{int(time.time())}_{index}"

            return Job(
                id=job_id,
                title=title,
                company=company,
                location=location,
                salary=None,
                description="",
                url=url,
                apply_url=url,
                posted_date=datetime.now().isoformat(),
                job_type="full-time",
                experience_level="mid",
                source="indeed",
                scraped_at=datetime.now().isoformat()
            )

        except Exception as e:
            logger.debug(f"Indeed extraction error: {e}")

        return None

    def _extract_simplyhired_job(self, card, index) -> Optional[Job]:
        """Extract job from SimplyHired card"""
        try:
            title_elem = card.find(['h3', 'h2', 'a'])
            company_elem = card.find('span', class_=lambda x: x and 'company' in x.lower())

            title = title_elem.get_text(strip=True) if title_elem else f"Job #{index + 1}"
            company = company_elem.get_text(strip=True) if company_elem else "Company"

            job_id = f"simplyhired_{hash(title)}_{int(time.time())}_{index}"

            return Job(
                id=job_id,
                title=title,
                company=company,
                location="Location",
                salary=None,
                description="",
                url="",
                apply_url="",
                posted_date=datetime.now().isoformat(),
                job_type="full-time",
                experience_level="mid",
                source="simplyhired",
                scraped_at=datetime.now().isoformat()
            )

        except Exception as e:
            logger.debug(f"SimplyHired extraction error: {e}")

        return None

    def _wait_for_jobs_to_load(self):
        """Wait for job listings to load"""
        try:
            # Wait for any job-related content
            wait = WebDriverWait(self.driver, 15)

            selectors_to_try = [
                ".jobs-search__results-list",
                ".job-search-card",
                ".result-card",
                "[data-entity-urn*='jobPosting']"
            ]

            for selector in selectors_to_try:
                try:
                    wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, selector)))
                    logger.info(f"Jobs loaded using selector: {selector}")
                    break
                except TimeoutException:
                    continue

            # Additional wait for dynamic content
            time.sleep(3)

        except Exception as e:
            logger.debug(f"Wait for jobs error: {e}")

    def _parse_linkedin_guest_results(self, soup, criteria) -> List[Job]:
        """Parse LinkedIn guest API results"""
        jobs = []

        try:
            job_cards = soup.find_all(['li', 'div'], class_=lambda x: x and 'job' in x.lower())

            for i, card in enumerate(job_cards[:15]):
                try:
                    title_elem = card.find(['h3', 'h2', 'a'])
                    company_elem = card.find(['h4', 'span'], class_=lambda x: x and any(keyword in x.lower() for keyword in ['company', 'subtitle']))

                    if title_elem:
                        title = title_elem.get_text(strip=True)
                        company = company_elem.get_text(strip=True) if company_elem else "Company"

                        job_id = f"linkedin_guest_{hash(title)}_{int(time.time())}_{i}"

                        job = Job(
                            id=job_id,
                            title=title,
                            company=company,
                            location=criteria.location,
                            salary=None,
                            description="",
                            url="",
                            apply_url="",
                            posted_date=datetime.now().isoformat(),
                            job_type="full-time",
                            experience_level="mid",
                            source="linkedin_guest",
                            scraped_at=datetime.now().isoformat()
                        )

                        jobs.append(job)

                except Exception as e:
                    logger.debug(f"LinkedIn guest parsing error: {e}")
                    continue

        except Exception as e:
            logger.error(f"LinkedIn guest results error: {e}")

        return jobs

    def _remove_duplicates(self, jobs: List[Job]) -> List[Job]:
        """Remove duplicate jobs based on title and company"""
        seen = set()
        unique_jobs = []

        for job in jobs:
            key = (job.title.lower().strip(), job.company.lower().strip())
            if key not in seen:
                seen.add(key)
                unique_jobs.append(job)

        return unique_jobs

    def close(self):
        """Cleanup resources"""
        if self.driver:
            try:
                self.driver.quit()
            except:
                pass
        if self.session:
            self.session.close()

def test_robust_scraper():
    """Test the robust scraper"""
    print("🧪 Testing Robust Job Scraper...")

    scraper = RobustJobScraper(headless=False)

    criteria = SearchCriteria(
        keywords=["Software Engineer"],
        location="San Francisco, CA",
        experience_level="mid",
        job_type="full-time",
        salary_min=None,
        salary_max=None,
        date_posted="week",
        company_size=None,
        remote_ok=False
    )

    try:
        jobs = scraper.search_jobs(criteria)

        print(f"\n🎯 Results: Found {len(jobs)} jobs")

        # Group by source
        by_source = {}
        for job in jobs:
            if job.source not in by_source:
                by_source[job.source] = []
            by_source[job.source].append(job)

        for source, source_jobs in by_source.items():
            print(f"\n📊 {source.upper()}: {len(source_jobs)} jobs")
            for i, job in enumerate(source_jobs[:3]):  # Show first 3 from each source
                print(f"  {i+1}. {job.title} - {job.company}")

        # Save results
        with open("robust_scraper_results.json", "w") as f:
            json.dump([asdict(job) for job in jobs], f, indent=2)

        print(f"\n✅ Results saved to robust_scraper_results.json")

    except Exception as e:
        print(f"❌ Test failed: {e}")
    finally:
        scraper.close()

if __name__ == "__main__":
    test_robust_scraper()