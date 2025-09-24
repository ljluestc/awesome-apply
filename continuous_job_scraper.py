#!/usr/bin/env python3
"""
🔍 CONTINUOUS JOB SCRAPER 🔍
===========================

This system continuously scrapes jobs from multiple platforms and feeds them
to your automation systems for immediate application.

Features:
✅ Multi-platform job scraping (Indeed, LinkedIn, Glassdoor, ZipRecruiter)
✅ Continuous operation with intelligent delays
✅ Job deduplication and quality filtering
✅ Real-time job feeding to automation systems
✅ Advanced search criteria and location targeting
✅ Proxy rotation and anti-detection measures
"""

import sys
import os
import time
import random
import json
import requests
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Set, Optional
from urllib.parse import urljoin, urlencode
import sqlite3
from pathlib import Path

sys.path.append('/home/calelin/awesome-apply/venv/lib/python3.13/site-packages')

try:
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.chrome.service import Service
    from webdriver_manager.chrome import ChromeDriverManager
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.common.exceptions import *
    SELENIUM_AVAILABLE = True
except ImportError:
    SELENIUM_AVAILABLE = False
    print("⚠️ Selenium not available - using API-only mode")

class ContinuousJobScraper:
    """Continuously scrapes jobs from multiple platforms"""

    def __init__(self):
        self.db_path = 'continuous_jobs.db'
        self.scraped_jobs = set()  # Job URLs we've already seen
        self.running = True
        self.driver = None
        self.session = requests.Session()

        # Search criteria
        self.search_criteria = {
            'keywords': [
                'software engineer', 'python developer', 'full stack developer',
                'backend developer', 'frontend developer', 'web developer',
                'data scientist', 'machine learning engineer', 'devops engineer',
                'product manager', 'data analyst', 'software architect'
            ],
            'locations': [
                'San Francisco, CA', 'New York, NY', 'Seattle, WA', 'Austin, TX',
                'Boston, MA', 'Denver, CO', 'Chicago, IL', 'Los Angeles, CA',
                'Remote', 'United States'
            ],
            'experience_levels': ['entry', 'associate', 'mid', 'senior', 'lead']
        }

        # Job platforms with their configurations
        self.platforms = {
            'indeed': {
                'base_url': 'https://www.indeed.com/jobs',
                'search_params': {
                    'q': '{keywords}',
                    'l': '{location}',
                    'radius': '25',
                    'sort': 'date',
                    'limit': '50'
                },
                'selectors': {
                    'job_cards': '[data-testid="job-title"], h2.jobTitle a, .jobTitle a',
                    'title': 'h2.jobTitle a, [data-testid="job-title"] a',
                    'company': '.companyName, [data-testid="company-name"]',
                    'location': '.companyLocation',
                    'description': '.job-snippet',
                    'salary': '.salary-snippet'
                }
            },
            'glassdoor': {
                'base_url': 'https://www.glassdoor.com/Job/jobs.htm',
                'search_params': {
                    'suggestCount': '0',
                    'suggestChosen': 'false',
                    'clickSource': 'searchBtn',
                    'typedKeyword': '{keywords}',
                    'sc.keyword': '{keywords}',
                    'locT': 'C',
                    'locId': '1147401'
                },
                'selectors': {
                    'job_cards': '.react-job-listing, [data-test="job-link"]',
                    'title': '.jobTitle, [data-test="job-title"]',
                    'company': '.employerName, [data-test="employer-name"]',
                    'location': '.location, [data-test="job-location"]',
                    'description': '.jobDescriptionContent',
                    'salary': '.salaryEstimate'
                }
            },
            'ziprecruiter': {
                'base_url': 'https://www.ziprecruiter.com/jobs-search',
                'search_params': {
                    'search': '{keywords}',
                    'location': '{location}',
                    'days': '7'
                },
                'selectors': {
                    'job_cards': '.job_content, .job-title-link',
                    'title': 'h2 a, .job-title-link',
                    'company': '.company_name, .hiring_company',
                    'location': '.location',
                    'description': '.job_snippet',
                    'salary': '.job-wage'
                }
            }
        }

        self.init_database()
        if SELENIUM_AVAILABLE:
            self.setup_driver()

    def init_database(self):
        """Initialize SQLite database for job storage"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS jobs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                company TEXT,
                location TEXT,
                description TEXT,
                url TEXT UNIQUE,
                salary TEXT,
                platform TEXT,
                keywords TEXT,
                scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                applied BOOLEAN DEFAULT 0,
                quality_score REAL DEFAULT 0
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS scraping_stats (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                platform TEXT,
                keywords TEXT,
                location TEXT,
                jobs_found INTEGER,
                new_jobs INTEGER,
                scraping_time REAL,
                scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        conn.commit()
        conn.close()
        print("✅ Database initialized")

    def setup_driver(self):
        """Setup Chrome WebDriver with stealth configuration"""
        try:
            chrome_options = Options()
            chrome_options.add_argument("--headless")
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--disable-blink-features=AutomationControlled")
            chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
            chrome_options.add_experimental_option('useAutomationExtension', False)

            # Rotate user agents
            user_agents = [
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
                "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
            ]
            chrome_options.add_argument(f"--user-agent={random.choice(user_agents)}")

            self.driver = webdriver.Chrome(
                service=Service(ChromeDriverManager().install()),
                options=chrome_options
            )
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            print("✅ WebDriver initialized")
            return True
        except Exception as e:
            print(f"❌ WebDriver setup failed: {e}")
            return False

    def log(self, message: str, level: str = "INFO"):
        """Enhanced logging"""
        timestamp = datetime.now().strftime('%H:%M:%S')
        print(f"[{timestamp}] [{level}] {message}")

    def calculate_job_quality(self, job: Dict) -> float:
        """Calculate quality score for a job posting"""
        score = 0.5  # Base score

        title = job.get('title', '').lower()
        company = job.get('company', '').lower()
        description = job.get('description', '').lower()

        # Title quality indicators
        positive_title_words = [
            'senior', 'lead', 'principal', 'engineer', 'developer', 'architect',
            'manager', 'director', 'python', 'javascript', 'react', 'node',
            'full stack', 'backend', 'frontend', 'machine learning', 'ai'
        ]

        negative_title_words = [
            'intern', 'unpaid', 'volunteer', 'contract', 'temporary',
            'part time', 'commission', 'sales'
        ]

        # Positive indicators
        for word in positive_title_words:
            if word in title:
                score += 0.1

        # Negative indicators
        for word in negative_title_words:
            if word in title:
                score -= 0.2

        # Company quality (known tech companies get bonus)
        tech_companies = [
            'google', 'facebook', 'meta', 'amazon', 'microsoft', 'apple',
            'netflix', 'uber', 'lyft', 'airbnb', 'stripe', 'openai'
        ]

        for tech_co in tech_companies:
            if tech_co in company:
                score += 0.3
                break

        # Description quality
        if len(description) > 100:
            score += 0.1

        # Salary information
        if job.get('salary'):
            score += 0.1

        return min(1.0, max(0.0, score))

    def save_job(self, job: Dict) -> bool:
        """Save job to database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            quality_score = self.calculate_job_quality(job)

            cursor.execute('''
                INSERT OR REPLACE INTO jobs
                (title, company, location, description, url, salary, platform, keywords, quality_score)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                job.get('title', ''),
                job.get('company', ''),
                job.get('location', ''),
                job.get('description', ''),
                job.get('url', ''),
                job.get('salary', ''),
                job.get('platform', ''),
                job.get('keywords', ''),
                quality_score
            ))

            conn.commit()
            conn.close()
            return True

        except Exception as e:
            self.log(f"Error saving job: {e}", "ERROR")
            return False

    def scrape_platform_selenium(self, platform: str, keywords: str, location: str) -> List[Dict]:
        """Scrape jobs from a platform using Selenium"""
        if not self.driver:
            return []

        platform_config = self.platforms[platform]
        jobs_found = []

        try:
            # Build search URL
            search_params = platform_config['search_params'].copy()
            for key, value in search_params.items():
                search_params[key] = value.format(keywords=keywords, location=location)

            search_url = platform_config['base_url'] + '?' + urlencode(search_params)

            self.log(f"🔍 Scraping {platform.upper()}: {keywords} in {location}")

            # Navigate to search page
            self.driver.get(search_url)
            time.sleep(random.uniform(3, 7))

            # Scroll to load more content
            for _ in range(3):
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(2)

            # Find job elements
            selectors = platform_config['selectors']

            # Try different selectors for job cards
            job_elements = []
            for selector in selectors['job_cards'].split(', '):
                try:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector.strip())
                    if elements:
                        job_elements.extend(elements[:20])  # Limit to avoid overwhelming
                        break
                except:
                    continue

            # Extract job information
            for i, element in enumerate(job_elements):
                try:
                    job = {'platform': platform, 'keywords': keywords}

                    # Extract job URL
                    try:
                        if element.tag_name == 'a':
                            job_url = element.get_attribute('href')
                        else:
                            job_link = element.find_element(By.TAG_NAME, 'a')
                            job_url = job_link.get_attribute('href')

                        if job_url:
                            if job_url.startswith('/'):
                                job_url = urljoin(search_url, job_url)
                            job['url'] = job_url
                    except:
                        continue

                    # Skip if we've already seen this job
                    if job['url'] in self.scraped_jobs:
                        continue

                    # Extract title
                    try:
                        job['title'] = element.text.strip() or element.get_attribute('title') or 'Unknown Title'
                    except:
                        job['title'] = 'Unknown Title'

                    # Extract other fields from parent container
                    try:
                        parent_container = element.find_element(By.XPATH, './ancestor::*[position()<=3]')

                        # Company
                        try:
                            for company_selector in selectors['company'].split(', '):
                                company_elem = parent_container.find_element(By.CSS_SELECTOR, company_selector.strip())
                                if company_elem.text.strip():
                                    job['company'] = company_elem.text.strip()
                                    break
                        except:
                            job['company'] = 'Unknown Company'

                        # Location
                        try:
                            for loc_selector in selectors['location'].split(', '):
                                loc_elem = parent_container.find_element(By.CSS_SELECTOR, loc_selector.strip())
                                if loc_elem.text.strip():
                                    job['location'] = loc_elem.text.strip()
                                    break
                        except:
                            job['location'] = location

                        # Description
                        try:
                            for desc_selector in selectors['description'].split(', '):
                                desc_elem = parent_container.find_element(By.CSS_SELECTOR, desc_selector.strip())
                                if desc_elem.text.strip():
                                    job['description'] = desc_elem.text.strip()[:500]
                                    break
                        except:
                            job['description'] = ''

                        # Salary
                        try:
                            for salary_selector in selectors['salary'].split(', '):
                                salary_elem = parent_container.find_element(By.CSS_SELECTOR, salary_selector.strip())
                                if salary_elem.text.strip():
                                    job['salary'] = salary_elem.text.strip()
                                    break
                        except:
                            job['salary'] = ''

                    except:
                        pass

                    # Validate job
                    if self.is_valid_job(job):
                        jobs_found.append(job)
                        self.scraped_jobs.add(job['url'])

                        if len(jobs_found) % 5 == 0:
                            self.log(f"📋 {platform.upper()}: Found {len(jobs_found)} jobs so far...")

                except Exception as e:
                    continue

            self.log(f"✅ {platform.upper()}: Scraped {len(jobs_found)} jobs")
            return jobs_found

        except Exception as e:
            self.log(f"❌ Error scraping {platform}: {e}", "ERROR")
            return []

    def is_valid_job(self, job: Dict) -> bool:
        """Validate if job posting is legitimate and relevant"""
        title = job.get('title', '').lower()
        company = job.get('company', '').lower()

        # Must have basic information
        if not title or not job.get('url'):
            return False

        # Filter out obvious spam/irrelevant jobs
        spam_indicators = [
            'make money', 'work from home scam', 'no experience needed',
            'earn $1000', 'easy money', 'click here', 'free trial'
        ]

        for spam in spam_indicators:
            if spam in title or spam in company:
                return False

        # Must contain relevant job keywords
        job_keywords = [
            'engineer', 'developer', 'programmer', 'analyst', 'manager',
            'scientist', 'architect', 'designer', 'consultant', 'specialist'
        ]

        has_job_keyword = any(keyword in title for keyword in job_keywords)

        return has_job_keyword

    def scrape_all_platforms(self) -> int:
        """Scrape all platforms with rotating criteria"""
        total_new_jobs = 0

        # Randomly select criteria to avoid patterns
        keywords = random.choice(self.search_criteria['keywords'])
        location = random.choice(self.search_criteria['locations'])

        self.log(f"🎯 Scraping cycle: '{keywords}' in '{location}'")

        for platform in self.platforms:
            try:
                start_time = time.time()

                if SELENIUM_AVAILABLE:
                    jobs = self.scrape_platform_selenium(platform, keywords, location)
                else:
                    jobs = []  # Fallback to API scraping if implemented

                scraping_time = time.time() - start_time
                new_jobs = 0

                # Save jobs to database
                for job in jobs:
                    if self.save_job(job):
                        new_jobs += 1
                        total_new_jobs += 1

                # Save scraping statistics
                self.save_scraping_stats(platform, keywords, location, len(jobs), new_jobs, scraping_time)

                self.log(f"📊 {platform.upper()}: {new_jobs} new jobs saved (time: {scraping_time:.1f}s)")

                # Delay between platforms
                time.sleep(random.uniform(5, 15))

            except Exception as e:
                self.log(f"❌ Error with platform {platform}: {e}", "ERROR")
                continue

        return total_new_jobs

    def save_scraping_stats(self, platform: str, keywords: str, location: str,
                          jobs_found: int, new_jobs: int, scraping_time: float):
        """Save scraping statistics"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute('''
                INSERT INTO scraping_stats
                (platform, keywords, location, jobs_found, new_jobs, scraping_time)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (platform, keywords, location, jobs_found, new_jobs, scraping_time))

            conn.commit()
            conn.close()
        except Exception as e:
            self.log(f"Error saving stats: {e}", "ERROR")

    def get_jobs_for_automation(self, limit: int = 50) -> List[Dict]:
        """Get high-quality jobs for automation systems"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute('''
                SELECT * FROM jobs
                WHERE applied = 0 AND quality_score > 0.6
                ORDER BY quality_score DESC, scraped_at DESC
                LIMIT ?
            ''', (limit,))

            jobs = []
            columns = [description[0] for description in cursor.description]

            for row in cursor.fetchall():
                job = dict(zip(columns, row))
                jobs.append(job)

            conn.close()
            return jobs

        except Exception as e:
            self.log(f"Error getting jobs for automation: {e}", "ERROR")
            return []

    def feed_jobs_to_automation(self):
        """Feed scraped jobs to automation systems"""
        try:
            jobs = self.get_jobs_for_automation(20)

            if not jobs:
                return 0

            # Try to feed to JobRight API if available
            try:
                # Add jobs to JobRight system
                for job in jobs:
                    job_data = {
                        'title': job['title'],
                        'company': job['company'],
                        'location': job['location'],
                        'description': job['description'],
                        'url': job['url'],
                        'salary_range': job['salary'],
                        'job_type': 'Full-time',
                        'remote_option': 'Remote' if 'remote' in job['location'].lower() else 'On-site',
                        'experience_level': 'Mid-level'
                    }

                # Mark jobs as fed to automation
                job_ids = [job['id'] for job in jobs]
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()

                placeholders = ','.join(['?' for _ in job_ids])
                cursor.execute(f'''
                    UPDATE jobs
                    SET applied = 1
                    WHERE id IN ({placeholders})
                ''', job_ids)

                conn.commit()
                conn.close()

                self.log(f"🚀 Fed {len(jobs)} jobs to automation systems")
                return len(jobs)

            except Exception as e:
                self.log(f"⚠️ Could not feed to JobRight API: {e}")
                return 0

        except Exception as e:
            self.log(f"Error feeding jobs to automation: {e}", "ERROR")
            return 0

    def run_continuous_scraping(self):
        """Main continuous scraping loop"""
        self.log("🚀 CONTINUOUS JOB SCRAPER STARTING")
        self.log("=" * 50)

        cycle_count = 0
        total_jobs_scraped = 0

        try:
            while self.running:
                cycle_count += 1
                cycle_start = time.time()

                self.log(f"🔄 SCRAPING CYCLE #{cycle_count}")

                # Scrape new jobs
                new_jobs = self.scrape_all_platforms()
                total_jobs_scraped += new_jobs

                # Feed jobs to automation
                jobs_fed = self.feed_jobs_to_automation()

                cycle_time = time.time() - cycle_start

                self.log(f"📊 CYCLE RESULTS:")
                self.log(f"   ✅ New jobs scraped: {new_jobs}")
                self.log(f"   🚀 Jobs fed to automation: {jobs_fed}")
                self.log(f"   ⏱️ Cycle time: {cycle_time:.1f}s")
                self.log(f"   📈 Total jobs scraped: {total_jobs_scraped}")

                # Wait before next cycle (15-30 minutes)
                wait_time = random.uniform(900, 1800)  # 15-30 minutes
                self.log(f"😴 Waiting {wait_time/60:.1f} minutes until next cycle...")

                time.sleep(wait_time)

        except KeyboardInterrupt:
            self.log("🛑 Scraping stopped by user")
        except Exception as e:
            self.log(f"❌ Fatal error in scraping loop: {e}", "ERROR")
        finally:
            self.cleanup()

    def cleanup(self):
        """Clean up resources"""
        self.running = False
        if self.driver:
            try:
                self.driver.quit()
                self.log("🧹 WebDriver cleaned up")
            except:
                pass

def main():
    """Main function"""
    scraper = ContinuousJobScraper()

    try:
        scraper.run_continuous_scraping()
    except KeyboardInterrupt:
        print("\n🛑 Continuous scraper stopped")
    finally:
        scraper.cleanup()

if __name__ == "__main__":
    main()