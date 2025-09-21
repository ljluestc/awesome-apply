#!/usr/bin/env python3
"""
Enhanced LinkedIn Job Scraper with Multiple Approaches
Robust scraping with fallback methods and anti-detection
"""

import time
import json
import logging
import random
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException
import requests
from bs4 import BeautifulSoup
import re
from urllib.parse import urlencode, quote_plus

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

class EnhancedLinkedInScraper:
    def __init__(self, headless=False, proxy=None):
        self.headless = headless
        self.proxy = proxy
        self.driver = None
        self.session = requests.Session()
        self.setup_session()

    def setup_session(self):
        """Setup requests session with headers"""
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        })

    def setup_driver(self):
        """Setup Chrome driver with anti-detection measures"""
        chrome_options = Options()

        # Basic options
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_argument("--disable-web-security")
        chrome_options.add_argument("--allow-running-insecure-content")
        chrome_options.add_argument("--disable-features=VizDisplayCompositor")

        # Anti-detection
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        chrome_options.add_argument("--disable-extensions")
        chrome_options.add_argument("--disable-plugins-discovery")
        chrome_options.add_argument("--disable-default-apps")

        # User agent rotation
        user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        ]
        chrome_options.add_argument(f"--user-agent={random.choice(user_agents)}")

        if self.headless:
            chrome_options.add_argument("--headless")

        # Window size
        chrome_options.add_argument("--window-size=1920,1080")

        # Proxy support
        if self.proxy:
            chrome_options.add_argument(f"--proxy-server={self.proxy}")

        try:
            self.driver = webdriver.Chrome(options=chrome_options)

            # Execute anti-detection scripts
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            self.driver.execute_cdp_cmd('Network.setUserAgentOverride', {
                "userAgent": random.choice(user_agents)
            })

            logger.info("✅ Chrome driver initialized successfully")
            return True

        except Exception as e:
            logger.error(f"❌ Failed to setup Chrome driver: {e}")
            return False

    def search_jobs(self, criteria: SearchCriteria) -> List[Job]:
        """Enhanced job search with multiple methods"""
        logger.info(f"🔍 Starting job search for: {criteria.keywords}")

        jobs = []

        # Method 1: Try Selenium scraping
        try:
            selenium_jobs = self._search_with_selenium(criteria)
            jobs.extend(selenium_jobs)
            logger.info(f"✅ Selenium method found {len(selenium_jobs)} jobs")
        except Exception as e:
            logger.error(f"❌ Selenium method failed: {e}")

        # Method 2: Try requests-based scraping
        if len(jobs) < 5:  # If we don't have enough jobs, try alternative method
            try:
                requests_jobs = self._search_with_requests(criteria)
                jobs.extend(requests_jobs)
                logger.info(f"✅ Requests method found {len(requests_jobs)} jobs")
            except Exception as e:
                logger.error(f"❌ Requests method failed: {e}")

        # Method 3: Try Google Jobs API fallback
        if len(jobs) < 5:
            try:
                google_jobs = self._search_google_jobs(criteria)
                jobs.extend(google_jobs)
                logger.info(f"✅ Google Jobs method found {len(google_jobs)} jobs")
            except Exception as e:
                logger.error(f"❌ Google Jobs method failed: {e}")

        # Remove duplicates based on URL
        seen_urls = set()
        unique_jobs = []
        for job in jobs:
            if job.url not in seen_urls:
                seen_urls.add(job.url)
                unique_jobs.append(job)

        logger.info(f"🎯 Total unique jobs found: {len(unique_jobs)}")
        return unique_jobs

    def _search_with_selenium(self, criteria: SearchCriteria) -> List[Job]:
        """Search using Selenium with enhanced selectors"""
        if not self.setup_driver():
            raise Exception("Failed to setup driver")

        jobs = []

        try:
            # Build search URL
            keywords = " ".join(criteria.keywords)
            location = criteria.location

            # LinkedIn job search URL
            base_url = "https://www.linkedin.com/jobs/search"
            params = {
                'keywords': keywords,
                'location': location,
                'sortBy': 'DD',  # Date posted
                'f_TPR': self._get_date_filter(criteria.date_posted),
                'f_WT': '2' if criteria.remote_ok else '',  # Remote work
            }

            # Add experience level filter
            if criteria.experience_level:
                exp_map = {
                    'entry': '1', 'associate': '2', 'mid': '3',
                    'senior': '4', 'director': '5', 'executive': '6'
                }
                if criteria.experience_level.lower() in exp_map:
                    params['f_E'] = exp_map[criteria.experience_level.lower()]

            # Add job type filter
            if criteria.job_type:
                type_map = {
                    'full-time': 'F', 'part-time': 'P', 'contract': 'C',
                    'temporary': 'T', 'internship': 'I'
                }
                if criteria.job_type.lower() in type_map:
                    params['f_JT'] = type_map[criteria.job_type.lower()]

            # Clean empty params
            params = {k: v for k, v in params.items() if v}
            search_url = f"{base_url}?{urlencode(params)}"

            logger.info(f"🌐 Navigating to: {search_url}")
            self.driver.get(search_url)

            # Wait and scroll to trigger loading
            time.sleep(random.uniform(3, 5))
            self._human_like_scroll()

            # Try multiple job card selectors
            job_selectors = [
                ".jobs-search__results-list li",
                ".job-search-card",
                "[data-entity-urn*='jobPosting']",
                ".result-card",
                ".jobs-search-results__list-item"
            ]

            job_cards = []
            for selector in job_selectors:
                try:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    if elements:
                        job_cards = elements
                        logger.info(f"✅ Found {len(job_cards)} job cards with selector: {selector}")
                        break
                except:
                    continue

            if not job_cards:
                # Try alternative approach - look for job titles
                title_elements = self.driver.find_elements(By.CSS_SELECTOR, "h3 a[href*='/jobs/view/']")
                if title_elements:
                    logger.info(f"✅ Found {len(title_elements)} job titles as fallback")
                    job_cards = [elem.find_element(By.XPATH, "./ancestor::li | ./ancestor::div[@class]") for elem in title_elements]

            logger.info(f"📊 Processing {len(job_cards)} job cards")

            for i, card in enumerate(job_cards[:50]):  # Limit to 50 jobs
                try:
                    job = self._extract_job_from_card_enhanced(card, i)
                    if job:
                        jobs.append(job)
                        logger.info(f"✅ Extracted job {i+1}: {job.title} at {job.company}")
                except Exception as e:
                    logger.error(f"❌ Error extracting job {i+1}: {e}")
                    continue

                # Random delay between extractions
                time.sleep(random.uniform(0.5, 1.5))

            # Try to load more jobs by scrolling
            if len(jobs) < 20:
                logger.info("🔄 Attempting to load more jobs...")
                self._load_more_jobs()

                # Re-extract after loading more
                new_cards = self.driver.find_elements(By.CSS_SELECTOR, job_selectors[0])
                for i, card in enumerate(new_cards[len(job_cards):len(job_cards)+20]):
                    try:
                        job = self._extract_job_from_card_enhanced(card, len(jobs) + i)
                        if job:
                            jobs.append(job)
                    except:
                        continue

        finally:
            if self.driver:
                self.driver.quit()

        return jobs

    def _extract_job_from_card_enhanced(self, card, index) -> Optional[Job]:
        """Enhanced job extraction with multiple selector strategies"""
        try:
            # Strategy 1: Standard selectors
            job_data = self._extract_basic_info(card)

            if not job_data.get('title'):
                # Strategy 2: Alternative selectors
                job_data = self._extract_alternative_info(card)

            if not job_data.get('title'):
                # Strategy 3: Text-based extraction
                job_data = self._extract_from_text(card)

            if not job_data.get('title'):
                logger.warning(f"⚠️ Could not extract title for job card {index}")
                return None

            # Generate unique ID
            job_id = f"linkedin_{hash(job_data['url'])}_{int(time.time())}_{index}"

            # Get additional details
            details = self._get_job_details(job_data.get('url'))

            job = Job(
                id=job_id,
                title=job_data.get('title', 'Unknown Title'),
                company=job_data.get('company', 'Unknown Company'),
                location=job_data.get('location', 'Unknown Location'),
                salary=details.get('salary') or job_data.get('salary'),
                description=details.get('description', job_data.get('description', '')),
                url=job_data.get('url', ''),
                apply_url=details.get('apply_url'),
                posted_date=job_data.get('posted_date', datetime.now().isoformat()),
                job_type=details.get('job_type', 'full-time'),
                experience_level=details.get('experience_level', 'mid'),
                source="linkedin",
                scraped_at=datetime.now().isoformat(),
                tags=details.get('tags', [])
            )

            return job

        except Exception as e:
            logger.error(f"❌ Error in enhanced extraction for card {index}: {e}")
            return None

    def _extract_basic_info(self, card) -> Dict:
        """Extract using standard LinkedIn selectors"""
        data = {}

        try:
            # Title and URL
            title_selectors = [
                "h3 a", ".job-search-card__title a", ".result-card__title a",
                "a[data-control-name='job_search_job_title']", ".job-title a"
            ]

            title_elem = None
            for selector in title_selectors:
                try:
                    title_elem = card.find_element(By.CSS_SELECTOR, selector)
                    break
                except:
                    continue

            if title_elem:
                data['title'] = title_elem.text.strip()
                data['url'] = title_elem.get_attribute('href')

            # Company
            company_selectors = [
                ".job-search-card__subtitle a", "h4 a", ".result-card__subtitle a",
                ".job-search-card__subtitle", ".company-name", ".job-company"
            ]

            for selector in company_selectors:
                try:
                    company_elem = card.find_element(By.CSS_SELECTOR, selector)
                    data['company'] = company_elem.text.strip()
                    break
                except:
                    continue

            # Location
            location_selectors = [
                ".job-search-card__location", ".job-result-card__location",
                ".result-card__location", ".job-location"
            ]

            for selector in location_selectors:
                try:
                    location_elem = card.find_element(By.CSS_SELECTOR, selector)
                    data['location'] = location_elem.text.strip()
                    break
                except:
                    continue

            # Posted date
            date_selectors = [
                "time", ".job-search-card__listdate", ".job-result-card__listdate"
            ]

            for selector in date_selectors:
                try:
                    date_elem = card.find_element(By.CSS_SELECTOR, selector)
                    data['posted_date'] = date_elem.get_attribute('datetime') or date_elem.text.strip()
                    break
                except:
                    continue

        except Exception as e:
            logger.debug(f"Basic extraction error: {e}")

        return data

    def _extract_alternative_info(self, card) -> Dict:
        """Extract using alternative selectors and methods"""
        data = {}

        try:
            # Get all links and find job link
            links = card.find_elements(By.TAG_NAME, "a")
            for link in links:
                href = link.get_attribute('href')
                if href and '/jobs/view/' in href:
                    data['url'] = href
                    data['title'] = link.text.strip()
                    break

            # Get text content and parse
            card_text = card.text
            lines = [line.strip() for line in card_text.split('\n') if line.strip()]

            if lines:
                # Usually first non-empty line is title
                for line in lines:
                    if len(line) > 5 and not line.isdigit():
                        if not data.get('title'):
                            data['title'] = line
                        elif not data.get('company'):
                            data['company'] = line
                        elif not data.get('location'):
                            data['location'] = line
                        else:
                            break

        except Exception as e:
            logger.debug(f"Alternative extraction error: {e}")

        return data

    def _extract_from_text(self, card) -> Dict:
        """Extract job info from raw text content"""
        data = {}

        try:
            text = card.text

            # Look for patterns in text
            # Job titles often contain keywords
            title_patterns = [
                r'(Software Engineer|Data Scientist|Product Manager|Developer|Analyst|Designer|Manager|Director|Engineer|Specialist)',
                r'^([A-Z][a-zA-Z\s]+(?:Engineer|Developer|Manager|Analyst|Designer|Specialist|Director))',
            ]

            for pattern in title_patterns:
                match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
                if match:
                    data['title'] = match.group(1).strip()
                    break

            # Look for company names (usually after title)
            lines = text.split('\n')
            for i, line in enumerate(lines):
                if data.get('title') and data['title'].lower() in line.lower():
                    if i + 1 < len(lines):
                        potential_company = lines[i + 1].strip()
                        if len(potential_company) > 2 and len(potential_company) < 50:
                            data['company'] = potential_company
                    break

        except Exception as e:
            logger.debug(f"Text extraction error: {e}")

        return data

    def _get_job_details(self, job_url) -> Dict:
        """Get additional job details from job page"""
        if not job_url:
            return {}

        details = {}

        try:
            # Navigate to job page
            self.driver.get(job_url)
            time.sleep(random.uniform(2, 4))

            # Get description
            desc_selectors = [
                ".jobs-description-content__text",
                ".jobs-box__html-content",
                ".job-view-layout .jobs-description",
                ".description__text"
            ]

            for selector in desc_selectors:
                try:
                    desc_elem = self.driver.find_element(By.CSS_SELECTOR, selector)
                    details['description'] = desc_elem.text.strip()[:1000]  # First 1000 chars
                    break
                except:
                    continue

            # Look for apply button/URL
            apply_selectors = [
                ".jobs-apply-button",
                "[data-control-name='jobdetails_topcard_inapply']",
                ".jobs-s-apply button",
                "a[href*='apply']"
            ]

            for selector in apply_selectors:
                try:
                    apply_elem = self.driver.find_element(By.CSS_SELECTOR, selector)
                    apply_url = apply_elem.get_attribute('href')
                    if apply_url:
                        details['apply_url'] = apply_url
                    else:
                        details['apply_url'] = job_url  # Fallback to job URL
                    break
                except:
                    continue

            # Look for salary
            salary_selectors = [
                ".jobs-details__salary-main-rail",
                ".salary",
                "[data-test='job-salary']"
            ]

            for selector in salary_selectors:
                try:
                    salary_elem = self.driver.find_element(By.CSS_SELECTOR, selector)
                    details['salary'] = salary_elem.text.strip()
                    break
                except:
                    continue

        except Exception as e:
            logger.debug(f"Job details extraction error: {e}")

        return details

    def _search_with_requests(self, criteria: SearchCriteria) -> List[Job]:
        """Fallback method using requests"""
        jobs = []

        try:
            keywords = "+".join(criteria.keywords)
            location = quote_plus(criteria.location)

            # LinkedIn public job search (may have limitations)
            url = f"https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search?keywords={keywords}&location={location}&start=0"

            response = self.session.get(url, timeout=10)

            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                job_cards = soup.find_all('div', class_='result-card')

                for i, card in enumerate(job_cards[:20]):
                    try:
                        title_elem = card.find('h3', class_='result-card__title')
                        company_elem = card.find('h4', class_='result-card__subtitle')
                        location_elem = card.find('span', class_='job-result-card__location')

                        if title_elem and company_elem:
                            job_link = title_elem.find('a')
                            if job_link:
                                job_id = f"linkedin_requests_{hash(job_link.get('href', ''))}_{int(time.time())}_{i}"

                                job = Job(
                                    id=job_id,
                                    title=title_elem.get_text(strip=True),
                                    company=company_elem.get_text(strip=True),
                                    location=location_elem.get_text(strip=True) if location_elem else "Unknown",
                                    salary=None,
                                    description="",
                                    url=job_link.get('href', ''),
                                    apply_url=job_link.get('href', ''),
                                    posted_date=datetime.now().isoformat(),
                                    job_type="unknown",
                                    experience_level="unknown",
                                    source="linkedin_requests",
                                    scraped_at=datetime.now().isoformat()
                                )

                                jobs.append(job)
                    except Exception as e:
                        logger.debug(f"Error parsing requests job {i}: {e}")
                        continue

        except Exception as e:
            logger.error(f"Requests method error: {e}")

        return jobs

    def _search_google_jobs(self, criteria: SearchCriteria) -> List[Job]:
        """Search using Google Jobs as fallback"""
        jobs = []

        try:
            if not self.driver:
                if not self.setup_driver():
                    return jobs

            keywords = " ".join(criteria.keywords)
            location = criteria.location

            # Google Jobs search
            query = f"{keywords} jobs {location}"
            google_url = f"https://www.google.com/search?q={quote_plus(query)}&ibp=htl;jobs"

            self.driver.get(google_url)
            time.sleep(3)

            # Look for Google Jobs results
            job_selectors = [
                ".PwjeAc",  # Google Jobs card
                "[data-ved*='job']",
                ".job-result"
            ]

            job_cards = []
            for selector in job_selectors:
                try:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    if elements:
                        job_cards = elements[:10]  # Limit to 10
                        break
                except:
                    continue

            for i, card in enumerate(job_cards):
                try:
                    # Extract basic info from Google Jobs
                    title = ""
                    company = ""
                    location_text = ""

                    # Try to extract text content
                    card_text = card.text
                    lines = [line.strip() for line in card_text.split('\n') if line.strip()]

                    if len(lines) >= 2:
                        title = lines[0]
                        company = lines[1]
                        if len(lines) >= 3:
                            location_text = lines[2]

                    if title and company:
                        job_id = f"google_jobs_{hash(title + company)}_{int(time.time())}_{i}"

                        job = Job(
                            id=job_id,
                            title=title,
                            company=company,
                            location=location_text or criteria.location,
                            salary=None,
                            description="",
                            url="",
                            apply_url="",
                            posted_date=datetime.now().isoformat(),
                            job_type="unknown",
                            experience_level="unknown",
                            source="google_jobs",
                            scraped_at=datetime.now().isoformat()
                        )

                        jobs.append(job)

                except Exception as e:
                    logger.debug(f"Error parsing Google job {i}: {e}")
                    continue

        except Exception as e:
            logger.error(f"Google Jobs method error: {e}")

        return jobs

    def _human_like_scroll(self):
        """Simulate human-like scrolling"""
        try:
            # Random scroll pattern
            for _ in range(3):
                scroll_pause = random.uniform(0.5, 1.5)
                self.driver.execute_script("window.scrollBy(0, window.innerHeight/3);")
                time.sleep(scroll_pause)

            # Scroll to top
            self.driver.execute_script("window.scrollTo(0, 0);")
            time.sleep(1)

        except Exception as e:
            logger.debug(f"Scroll error: {e}")

    def _load_more_jobs(self):
        """Try to load more jobs by clicking 'Show more' or scrolling"""
        try:
            # Look for "Show more results" button
            show_more_selectors = [
                "button[aria-label*='Show more']",
                ".jobs-search-results__pagination button",
                ".show-more-results",
                ".infinite-scroller__show-more-button"
            ]

            for selector in show_more_selectors:
                try:
                    button = self.driver.find_element(By.CSS_SELECTOR, selector)
                    if button.is_enabled():
                        self.driver.execute_script("arguments[0].click();", button)
                        time.sleep(3)
                        logger.info("✅ Clicked 'Show more' button")
                        return
                except:
                    continue

            # If no button found, try scrolling to bottom
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)

        except Exception as e:
            logger.debug(f"Load more error: {e}")

    def _get_date_filter(self, date_posted: str) -> str:
        """Convert date posted filter to LinkedIn format"""
        date_map = {
            'day': 'r86400',
            'week': 'r604800',
            'month': 'r2592000',
            'any': ''
        }
        return date_map.get(date_posted, '')

    def close(self):
        """Close driver and cleanup"""
        if self.driver:
            try:
                self.driver.quit()
            except:
                pass
        if self.session:
            self.session.close()

def test_scraper():
    """Test the enhanced scraper"""
    print("🧪 Testing Enhanced LinkedIn Scraper...")

    scraper = EnhancedLinkedInScraper(headless=False)

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

        for i, job in enumerate(jobs[:5]):  # Show first 5
            print(f"\n{i+1}. {job.title}")
            print(f"   Company: {job.company}")
            print(f"   Location: {job.location}")
            print(f"   URL: {job.url}")
            print(f"   Source: {job.source}")

        # Save results
        with open("test_scraper_results.json", "w") as f:
            json.dump([asdict(job) for job in jobs], f, indent=2)

        print(f"\n✅ Results saved to test_scraper_results.json")

    except Exception as e:
        print(f"❌ Test failed: {e}")
    finally:
        scraper.close()

if __name__ == "__main__":
    test_scraper()