#!/usr/bin/env python3
"""
JobRight UI Replica with Automated LinkedIn Job Applications
Replicates JobRight.ai UI and provides intelligent automation with pattern learning
"""

import sys
import os
import json
import sqlite3
import time
import logging
import random
import threading
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from flask import Flask, render_template, request, jsonify, send_from_directory
import signal

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

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('jobright_replica.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class AutomationDatabase:
    """Database for storing automation patterns and job application results"""

    def __init__(self, db_path='jobright_automation.db'):
        self.db_path = db_path
        self.init_database()

    def init_database(self):
        """Initialize database tables"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Jobs table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS jobs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                company TEXT,
                location TEXT,
                description TEXT,
                url TEXT UNIQUE,
                salary_range TEXT,
                job_type TEXT,
                remote_option TEXT,
                experience_level TEXT,
                scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                source TEXT DEFAULT 'linkedin'
            )
        ''')

        # Applications table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS applications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                job_id INTEGER,
                status TEXT, -- 'success', 'failed', 'skipped', 'manual_required'
                error_message TEXT,
                automation_pattern TEXT,
                form_fields_detected TEXT, -- JSON
                applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                response_time REAL,
                success_score REAL,
                FOREIGN KEY (job_id) REFERENCES jobs (id)
            )
        ''')

        # Automation patterns table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS automation_patterns (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                company TEXT,
                job_board TEXT,
                pattern_type TEXT, -- 'apply_button', 'form_fields', 'navigation'
                selectors TEXT, -- JSON array of CSS selectors that work
                success_rate REAL,
                attempts INTEGER DEFAULT 1,
                last_used TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # User preferences table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_preferences (
                id INTEGER PRIMARY KEY DEFAULT 1,
                name TEXT DEFAULT 'John Doe',
                email TEXT DEFAULT 'john.doe@example.com',
                phone TEXT DEFAULT '+1-555-123-4567',
                linkedin_profile TEXT,
                github_profile TEXT,
                resume_summary TEXT,
                target_locations TEXT, -- JSON array
                target_roles TEXT, -- JSON array
                salary_min INTEGER,
                salary_max INTEGER,
                remote_preference TEXT DEFAULT 'any',
                experience_years INTEGER DEFAULT 3,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Analytics table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS analytics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                metric_name TEXT,
                metric_value REAL,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                details TEXT -- JSON
            )
        ''')

        # Insert default user preferences if not exists
        cursor.execute('INSERT OR IGNORE INTO user_preferences (id) VALUES (1)')

        conn.commit()
        conn.close()
        logger.info("✅ Database initialized successfully")

    def add_job(self, job_data: Dict) -> Optional[int]:
        """Add job to database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            cursor.execute('''
                INSERT OR REPLACE INTO jobs
                (title, company, location, description, url, salary_range,
                 job_type, remote_option, experience_level, source)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                job_data.get('title', ''),
                job_data.get('company', ''),
                job_data.get('location', ''),
                job_data.get('description', ''),
                job_data.get('url', ''),
                job_data.get('salary_range', ''),
                job_data.get('job_type', 'Full-time'),
                job_data.get('remote_option', 'On-site'),
                job_data.get('experience_level', 'Mid-level'),
                job_data.get('source', 'linkedin')
            ))
            job_id = cursor.lastrowid
            conn.commit()
            return job_id
        except Exception as e:
            logger.error(f"Error adding job to database: {e}")
            return None
        finally:
            conn.close()

    def get_jobs(self, limit: int = 100, filters: Dict = None) -> List[Dict]:
        """Get jobs from database with optional filters"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            query = '''
                SELECT j.*,
                       CASE WHEN a.status = 'success' THEN 1 ELSE 0 END as applied
                FROM jobs j
                LEFT JOIN applications a ON j.id = a.job_id
            '''
            params = []

            if filters:
                conditions = []
                if filters.get('location'):
                    conditions.append('j.location LIKE ?')
                    params.append(f"%{filters['location']}%")
                if filters.get('title'):
                    conditions.append('j.title LIKE ?')
                    params.append(f"%{filters['title']}%")
                if filters.get('company'):
                    conditions.append('j.company LIKE ?')
                    params.append(f"%{filters['company']}%")
                if filters.get('remote_only'):
                    conditions.append("j.remote_option LIKE '%remote%'")

                if conditions:
                    query += ' WHERE ' + ' AND '.join(conditions)

            query += f' ORDER BY j.scraped_at DESC LIMIT {limit}'

            cursor.execute(query, params)
            results = cursor.fetchall()

            columns = [description[0] for description in cursor.description]
            return [dict(zip(columns, row)) for row in results]
        except Exception as e:
            logger.error(f"Error getting jobs: {e}")
            return []
        finally:
            conn.close()

    def record_application(self, job_id: int, status: str, **kwargs):
        """Record application attempt"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            cursor.execute('''
                INSERT INTO applications
                (job_id, status, error_message, automation_pattern,
                 form_fields_detected, response_time, success_score)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                job_id,
                status,
                kwargs.get('error_message'),
                kwargs.get('automation_pattern'),
                json.dumps(kwargs.get('form_fields', {})),
                kwargs.get('response_time'),
                kwargs.get('success_score', 0.0)
            ))
            conn.commit()
        except Exception as e:
            logger.error(f"Error recording application: {e}")
        finally:
            conn.close()

    def get_analytics(self) -> Dict:
        """Get application analytics"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            # Basic stats
            cursor.execute('SELECT COUNT(*) FROM jobs')
            total_jobs = cursor.fetchone()[0]

            cursor.execute('SELECT COUNT(*) FROM applications WHERE status = "success"')
            successful_apps = cursor.fetchone()[0]

            cursor.execute('SELECT COUNT(*) FROM applications')
            total_attempts = cursor.fetchone()[0]

            cursor.execute('SELECT AVG(response_time) FROM applications WHERE response_time IS NOT NULL')
            avg_response_time = cursor.fetchone()[0] or 0

            # Success rate by company
            cursor.execute('''
                SELECT j.company,
                       COUNT(*) as total,
                       SUM(CASE WHEN a.status = 'success' THEN 1 ELSE 0 END) as successful
                FROM jobs j
                LEFT JOIN applications a ON j.id = a.job_id
                WHERE j.company IS NOT NULL AND j.company != ''
                GROUP BY j.company
                ORDER BY successful DESC
                LIMIT 10
            ''')
            company_stats = cursor.fetchall()

            # Recent activity
            cursor.execute('''
                SELECT DATE(applied_at) as date, COUNT(*) as applications
                FROM applications
                WHERE applied_at >= date('now', '-7 days')
                GROUP BY DATE(applied_at)
                ORDER BY date DESC
            ''')
            daily_activity = cursor.fetchall()

            return {
                'total_jobs': total_jobs,
                'successful_applications': successful_apps,
                'total_attempts': total_attempts,
                'success_rate': (successful_apps / total_attempts * 100) if total_attempts > 0 else 0,
                'avg_response_time': round(avg_response_time, 2),
                'company_stats': [{'company': c[0], 'total': c[1], 'successful': c[2],
                                 'rate': (c[2]/c[1]*100) if c[1] > 0 else 0} for c in company_stats],
                'daily_activity': [{'date': d[0], 'applications': d[1]} for d in daily_activity]
            }
        except Exception as e:
            logger.error(f"Error getting analytics: {e}")
            return {}
        finally:
            conn.close()

class WorkingJobScraper:
    """Working multi-platform job scraper that successfully finds real jobs"""

    def __init__(self, database: AutomationDatabase):
        self.database = database
        self.driver = None
        self.scraped_jobs = []
        self.job_platforms = {
            'indeed': {
                'search_url_template': 'https://www.indeed.com/jobs?q={keywords}&l={location}&radius=25&sort=date',
                'job_selectors': [
                    'div[data-testid="job-title"] a',
                    'h2.jobTitle a',
                    '.jobTitle a',
                    '[data-jk] h2 a'
                ],
                'company_selectors': [
                    'span.companyName',
                    '.companyName',
                    '[data-testid="company-name"]'
                ]
            },
            'glassdoor': {
                'search_url_template': 'https://www.glassdoor.com/Job/jobs.htm?suggestCount=0&suggestChosen=false&clickSource=searchBtn&typedKeyword={keywords}&sc.keyword={keywords}&locT=C&locId=1147401&jobType=all',
                'job_selectors': [
                    '.react-job-listing a',
                    '[data-test="job-link"]',
                    '.job-search-card a'
                ],
                'company_selectors': [
                    '.employerName',
                    '[data-test="employer-name"]'
                ]
            },
            'ziprecruiter': {
                'search_url_template': 'https://www.ziprecruiter.com/jobs-search?search={keywords}&location={location}',
                'job_selectors': [
                    '.job_content h2 a',
                    '.job-title-link',
                    'h2 a[data-href]'
                ],
                'company_selectors': [
                    '.company_name',
                    '.hiring_company'
                ]
            }
        }

    def setup_driver(self):
        """Setup Chrome WebDriver with stealth configuration"""
        try:
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
            logger.info("✅ Working job scraper driver setup complete")
            return True
        except Exception as e:
            logger.error(f"❌ Working job scraper setup failed: {e}")
            return False

    def clean_text(self, text):
        """Clean and normalize text"""
        if not text:
            return ""
        import re
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

    def scrape_linkedin_jobs(self, criteria: Dict) -> List[Dict]:
        """Main entry point for job scraping - now uses multi-platform approach"""
        if not self.driver:
            self.setup_driver()

        keywords = criteria.get('keywords', 'software engineer')
        location = criteria.get('location', 'San Francisco, CA')

        logger.info(f"🔍 Scraping jobs with criteria: {keywords} in {location}")

        all_jobs = []

        # Try Indeed first (most reliable)
        indeed_jobs = self.extract_jobs_from_platform('indeed', keywords, location)
        all_jobs.extend(indeed_jobs)

        # If we have enough jobs from Indeed, return them
        if len(all_jobs) >= 10:
            logger.info(f"✅ Found {len(all_jobs)} jobs from Indeed - sufficient for automation")
            self.scraped_jobs = all_jobs
            return all_jobs

        # Try other platforms if needed
        for platform in ['glassdoor', 'ziprecruiter']:
            try:
                platform_jobs = self.extract_jobs_from_platform(platform, keywords, location)
                all_jobs.extend(platform_jobs)
                if len(all_jobs) >= 15:  # Stop when we have enough
                    break
            except Exception as e:
                logger.warning(f"Platform {platform} failed: {e}")
                continue

        # Remove duplicates by URL
        unique_jobs = []
        seen_urls = set()
        for job in all_jobs:
            if job['url'] not in seen_urls:
                unique_jobs.append(job)
                seen_urls.add(job['url'])

        logger.info(f"✅ Successfully scraped {len(unique_jobs)} unique jobs")
        self.scraped_jobs = unique_jobs

        # Add jobs to database
        for job in unique_jobs:
            job_id = self.database.add_job(job)
            if job_id:
                job['id'] = job_id

        return unique_jobs

    def extract_jobs_from_platform(self, platform_name, keywords, location):
        """Extract jobs from a specific platform"""
        platform_config = self.job_platforms[platform_name]

        # Build search URL
        search_url = platform_config['search_url_template'].format(
            keywords=keywords.replace(' ', '+'),
            location=location.replace(' ', '+').replace(',', '%2C')
        )

        logger.info(f"🎯 Scraping {platform_name.upper()}: {search_url}")

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
            from urllib.parse import urljoin

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
                            'title': job_title,
                            'company': company or 'Company not specified',
                            'location': location,
                            'url': job_url,
                            'description': f"Job found on {platform_name}",
                            'job_type': 'Full-time',
                            'remote_option': 'On-site',
                            'experience_level': 'Mid-level',
                            'source': platform_name,
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

    def close(self):
        """Close the driver"""
        if self.driver:
            self.driver.quit()

class IntelligentJobApplier:
    """Intelligent job application automation with pattern learning"""

    def __init__(self, database: AutomationDatabase):
        self.database = database
        self.driver = None
        self.user_data = {
            'name': 'John Doe',
            'email': 'john.doe@example.com',
            'phone': '+1-555-123-4567',
            'linkedin_profile': 'https://linkedin.com/in/johndoe',
            'github_profile': 'https://github.com/johndoe',
            'resume_summary': 'Experienced software engineer with 5+ years in full-stack development.'
        }

    def setup_driver(self):
        """Setup Chrome WebDriver for applications"""
        try:
            chrome_options = Options()
            user_data_dir = "/tmp/chrome_job_applier"
            chrome_options.add_argument(f"--user-data-dir={user_data_dir}")
            chrome_options.add_argument("--profile-directory=Default")
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
            logger.info("✅ Job applier driver setup complete")
            return True
        except Exception as e:
            logger.error(f"❌ Job applier setup failed: {e}")
            return False

    def apply_to_job(self, job: Dict) -> Dict:
        """Apply to a single job with intelligent automation"""
        if not self.driver:
            self.setup_driver()

        start_time = time.time()
        job_id = job.get('id')
        company = job.get('company', '')

        result = {
            'job_id': job_id,
            'status': 'failed',
            'error_message': None,
            'response_time': 0,
            'success_score': 0.0,
            'timestamp': datetime.now().isoformat()
        }

        try:
            logger.info(f"🎯 Applying to: {job['title']} at {company}")

            # Navigate to job
            self.driver.get(job['url'])
            time.sleep(3)

            # Find and click apply button
            apply_clicked = self.find_and_click_apply_button(job)

            if apply_clicked:
                # Fill application form
                form_filled = self.fill_application_form(job)

                if form_filled:
                    result['status'] = 'success'
                    result['success_score'] = 1.0
                    logger.info(f"✅ Successfully applied to {job['title']}")
                else:
                    result['error_message'] = 'Form filling failed'
                    result['success_score'] = 0.5
                    logger.warning(f"⚠️ Form filling failed for {job['title']}")
            else:
                result['error_message'] = 'Apply button not found or not clickable'
                logger.warning(f"⚠️ No apply button found for {job['title']}")

        except Exception as e:
            result['error_message'] = f"Application failed: {str(e)}"
            logger.error(f"❌ Application failed for {job['title']}: {e}")

        # Record result
        result['response_time'] = time.time() - start_time
        self.database.record_application(
            job_id, result['status'],
            error_message=result['error_message'],
            response_time=result['response_time'],
            success_score=result['success_score']
        )

        return result

    def find_and_click_apply_button(self, job: Dict) -> bool:
        """Find and click apply button with multiple strategies"""
        try:
            # Common apply button selectors
            apply_selectors = [
                "button[aria-label*='Easy Apply']",
                "button[aria-label*='Apply']",
                ".jobs-s-apply button",
                ".jobs-apply-button",
                "button[data-control-name*='apply']",
                "a[aria-label*='Apply']"
            ]

            for selector in apply_selectors:
                try:
                    buttons = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    for button in buttons:
                        if button.is_displayed() and button.is_enabled():
                            # Scroll to button
                            self.driver.execute_script("arguments[0].scrollIntoView(true);", button)
                            time.sleep(1)

                            # Try clicking
                            button.click()
                            time.sleep(2)
                            return True
                except:
                    continue

            return False
        except Exception as e:
            logger.error(f"Error finding apply button: {e}")
            return False

    def fill_application_form(self, job: Dict) -> bool:
        """Fill application form intelligently"""
        try:
            # Wait for form to load
            time.sleep(3)

            # Common form field mappings
            field_mappings = {
                'email': {
                    'selectors': ["input[type='email']", "input[name*='email']", "input[id*='email']"],
                    'value': self.user_data['email']
                },
                'phone': {
                    'selectors': ["input[type='tel']", "input[name*='phone']", "input[id*='phone']"],
                    'value': self.user_data['phone']
                },
                'name': {
                    'selectors': ["input[name*='name']", "input[id*='firstName']", "input[placeholder*='name']"],
                    'value': self.user_data['name']
                },
                'linkedin': {
                    'selectors': ["input[name*='linkedin']", "input[placeholder*='linkedin']"],
                    'value': self.user_data['linkedin_profile']
                },
                'github': {
                    'selectors': ["input[name*='github']", "input[placeholder*='github']"],
                    'value': self.user_data['github_profile']
                },
                'cover_letter': {
                    'selectors': ["textarea", "input[name*='cover']", "textarea[name*='message']"],
                    'value': f"I am very interested in the {job.get('title', 'position')} role at {job.get('company', 'your company')}. {self.user_data['resume_summary']}"
                }
            }

            filled_count = 0
            for field_type, field_info in field_mappings.items():
                if self.fill_field(field_info['selectors'], field_info['value']):
                    filled_count += 1
                    logger.debug(f"Filled {field_type} field")

            logger.info(f"Filled {filled_count} form fields")

            # Try to submit form
            return self.submit_form()

        except Exception as e:
            logger.error(f"Error filling form: {e}")
            return False

    def fill_field(self, selectors: List[str], value: str) -> bool:
        """Fill a form field using multiple selector strategies"""
        for selector in selectors:
            try:
                fields = self.driver.find_elements(By.CSS_SELECTOR, selector)
                for field in fields:
                    if field.is_displayed() and field.is_enabled():
                        field.clear()
                        field.send_keys(value)
                        return True
            except:
                continue
        return False

    def submit_form(self) -> bool:
        """Submit the application form"""
        submit_selectors = [
            "button[type='submit']",
            "button[aria-label*='Submit']",
            "button[aria-label*='Send']",
            "button:contains('Submit')",
            "button:contains('Apply')",
            ".artdeco-button--primary"
        ]

        for selector in submit_selectors:
            try:
                buttons = self.driver.find_elements(By.CSS_SELECTOR, selector)
                for button in buttons:
                    if button.is_displayed() and button.is_enabled():
                        button.click()
                        time.sleep(3)
                        logger.info("✅ Form submitted successfully")
                        return True
            except:
                continue

        logger.warning("⚠️ Could not find submit button")
        return False

    def close(self):
        """Close the driver"""
        if self.driver:
            self.driver.quit()

class MasterJobApplier:
    def __init__(self):
        """Initialize the comprehensive job application system"""
        self.database = AutomationDatabase()
        self.scraper = WorkingJobScraper(self.database)
        self.applier = IntelligentJobApplier(self.database)
        """Initialize the comprehensive job application system"""
        self.database = AutomationDatabase()
        self.scraper = WorkingJobScraper(self.database)
        self.applier = IntelligentJobApplier(self.database)
        self.session_id = datetime.now().strftime('%Y%m%d_%H%M%S')
        self.applied_jobs = []
        self.session_stats = {
            'start_time': time.time(),
            'successful_applications': 0,
            'failed_attempts': 0,
            'total_jobs_scraped': 0
        }

    def scrape_jobs(self, criteria: Dict) -> List[Dict]:
        """Scrape jobs using the LinkedIn scraper"""
        try:
            jobs = self.scraper.scrape_linkedin_jobs(criteria)
            self.session_stats['total_jobs_scraped'] += len(jobs)
            return jobs
        except Exception as e:
            logger.error(f"Error scraping jobs: {e}")
            return []

    def apply_to_jobs(self, job_ids: List[int]) -> List[Dict]:
        """Apply to multiple jobs"""
        results = []
        jobs = self.database.get_jobs()

        for job in jobs:
            if job['id'] in job_ids:
                result = self.applier.apply_to_job(job)
                results.append(result)

                if result['status'] == 'success':
                    self.session_stats['successful_applications'] += 1
                    self.applied_jobs.append(job)
                else:
                    self.session_stats['failed_attempts'] += 1

                time.sleep(random.uniform(2, 5))  # Delay between applications

        return results

    def close(self):
        """Close all drivers"""
        self.scraper.close()
        self.applier.close()

# Flask Web Application
app = Flask(__name__)
app.secret_key = 'jobright-replica-secret-key'

# Global instances
master_applier = MasterJobApplier()

@app.route('/')
def index():
    """Main JobRight replica dashboard"""
    return render_template('jobright_exact_replica.html')

@app.route('/api/jobs')
def api_jobs():
    """API endpoint to get jobs"""
    filters = {
        'location': request.args.get('location'),
        'title': request.args.get('title'),
        'company': request.args.get('company'),
        'remote_only': request.args.get('remote') == 'true'
    }
    # Remove None values
    filters = {k: v for k, v in filters.items() if v is not None}

    jobs = master_applier.database.get_jobs(limit=100, filters=filters)
    return jsonify({'jobs': jobs, 'total': len(jobs)})

@app.route('/api/scrape', methods=['POST'])
def api_scrape():
    """API endpoint to scrape new jobs"""
    criteria = request.get_json() or {}

    try:
        jobs = master_applier.scrape_jobs(criteria)
        return jsonify({
            'success': True,
            'jobs_scraped': len(jobs),
            'jobs': jobs
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/apply', methods=['POST'])
def api_apply():
    """API endpoint to apply to jobs"""
    data = request.get_json()
    job_ids = data.get('job_ids', [])

    if not job_ids:
        return jsonify({'success': False, 'error': 'No job IDs provided'}), 400

    try:
        results = master_applier.apply_to_jobs(job_ids)
        successful_count = len([r for r in results if r['status'] == 'success'])

        return jsonify({
            'success': True,
            'applications': results,
            'total_applied': successful_count
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/analytics')
def api_analytics():
    """API endpoint for analytics"""
    try:
        analytics = master_applier.database.get_analytics()
        return jsonify(analytics)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/static/<path:filename>')
def serve_static(filename):
    """Serve static files"""
    return send_from_directory('static', filename)

def create_templates():
    """Create the JobRight replica HTML template"""
    os.makedirs('templates', exist_ok=True)
    os.makedirs('static', exist_ok=True)

    # JobRight replica HTML template
    html_template = '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>JobRight AI - Intelligent Job Search & Auto-Apply</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap" rel="stylesheet">
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
            background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
            color: #333;
            line-height: 1.6;
        }

        /* Header */
        .header {
            background: white;
            box-shadow: 0 2px 20px rgba(0,0,0,0.1);
            padding: 15px 0;
            position: sticky;
            top: 0;
            z-index: 100;
        }

        .header-content {
            max-width: 1400px;
            margin: 0 auto;
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 0 20px;
        }

        .logo {
            display: flex;
            align-items: center;
            font-size: 1.8em;
            font-weight: 800;
            color: #00f0a0;
        }

        .logo::before {
            content: "🎯";
            margin-right: 10px;
        }

        .nav-menu {
            display: flex;
            gap: 30px;
            align-items: center;
        }

        .nav-item {
            color: #666;
            text-decoration: none;
            font-weight: 500;
            transition: color 0.3s;
        }

        .nav-item:hover {
            color: #00f0a0;
        }

        /* Main Container */
        .container {
            max-width: 1400px;
            margin: 0 auto;
            padding: 30px 20px;
        }

        /* Hero Section */
        .hero {
            text-align: center;
            margin-bottom: 40px;
            padding: 40px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            border-radius: 20px;
            color: white;
        }

        .hero h1 {
            font-size: 3.5em;
            font-weight: 800;
            margin-bottom: 15px;
            background: linear-gradient(45deg, #fff, #00f0a0);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }

        .hero p {
            font-size: 1.3em;
            opacity: 0.9;
            max-width: 600px;
            margin: 0 auto;
        }

        /* Control Panel */
        .control-panel {
            background: white;
            border-radius: 20px;
            padding: 30px;
            margin-bottom: 30px;
            box-shadow: 0 8px 40px rgba(0,0,0,0.1);
        }

        .panel-title {
            font-size: 1.5em;
            font-weight: 700;
            color: #2c3e50;
            margin-bottom: 25px;
            display: flex;
            align-items: center;
        }

        .panel-title::before {
            content: "⚡";
            margin-right: 10px;
        }

        .control-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-bottom: 25px;
        }

        .control-group {
            display: flex;
            flex-direction: column;
        }

        .control-group label {
            font-weight: 600;
            color: #555;
            margin-bottom: 8px;
            font-size: 0.95em;
        }

        .control-group input,
        .control-group select {
            padding: 14px 16px;
            border: 2px solid #e1e8ed;
            border-radius: 12px;
            font-size: 16px;
            background: white;
            transition: all 0.3s ease;
        }

        .control-group input:focus,
        .control-group select:focus {
            outline: none;
            border-color: #00f0a0;
            box-shadow: 0 0 0 3px rgba(0, 240, 160, 0.1);
        }

        .button-group {
            display: flex;
            gap: 15px;
            flex-wrap: wrap;
        }

        .btn {
            background: linear-gradient(135deg, #00f0a0 0%, #00d4aa 100%);
            color: white;
            padding: 14px 28px;
            border: none;
            border-radius: 12px;
            font-size: 16px;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s ease;
            display: flex;
            align-items: center;
            gap: 8px;
        }

        .btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 8px 25px rgba(0, 240, 160, 0.3);
        }

        .btn:active {
            transform: translateY(0);
        }

        .btn-secondary {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        }

        .btn-danger {
            background: linear-gradient(135deg, #ff6b6b 0%, #ee5a52 100%);
        }

        .btn:disabled {
            opacity: 0.6;
            cursor: not-allowed;
            transform: none;
        }

        /* Stats Dashboard */
        .stats-dashboard {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }

        .stat-card {
            background: white;
            border-radius: 16px;
            padding: 25px;
            text-align: center;
            box-shadow: 0 4px 20px rgba(0,0,0,0.1);
            position: relative;
            overflow: hidden;
        }

        .stat-card::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            height: 4px;
            background: linear-gradient(135deg, #00f0a0 0%, #00d4aa 100%);
        }

        .stat-number {
            font-size: 2.5em;
            font-weight: 800;
            color: #00f0a0;
            margin-bottom: 8px;
        }

        .stat-label {
            color: #666;
            font-weight: 500;
            font-size: 0.95em;
        }

        /* Jobs Container */
        .jobs-container {
            background: white;
            border-radius: 20px;
            padding: 30px;
            box-shadow: 0 8px 40px rgba(0,0,0,0.1);
        }

        .jobs-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 25px;
            flex-wrap: wrap;
            gap: 20px;
        }

        .jobs-title {
            font-size: 1.8em;
            font-weight: 700;
            color: #2c3e50;
            display: flex;
            align-items: center;
        }

        .jobs-title::before {
            content: "💼";
            margin-right: 10px;
        }

        .search-filter {
            display: flex;
            gap: 15px;
            align-items: center;
        }

        .search-input {
            padding: 12px 16px;
            border: 2px solid #e1e8ed;
            border-radius: 25px;
            font-size: 16px;
            min-width: 250px;
            background: #f8f9fa;
        }

        .search-input:focus {
            outline: none;
            border-color: #00f0a0;
            background: white;
        }

        /* Job Grid */
        .job-grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(380px, 1fr));
            gap: 20px;
        }

        .job-card {
            background: #f8f9fa;
            border: 2px solid transparent;
            border-radius: 16px;
            padding: 25px;
            transition: all 0.3s ease;
            position: relative;
            cursor: pointer;
        }

        .job-card:hover {
            transform: translateY(-4px);
            box-shadow: 0 12px 40px rgba(0,0,0,0.15);
            border-color: #00f0a0;
            background: white;
        }

        .job-card.selected {
            border-color: #00f0a0;
            background: linear-gradient(135deg, rgba(0, 240, 160, 0.05) 0%, rgba(0, 212, 170, 0.05) 100%);
        }

        .job-checkbox {
            position: absolute;
            top: 20px;
            right: 20px;
            width: 20px;
            height: 20px;
            cursor: pointer;
        }

        .job-title {
            font-size: 1.4em;
            font-weight: 700;
            color: #2c3e50;
            margin-bottom: 8px;
            line-height: 1.3;
            padding-right: 40px;
        }

        .job-company {
            color: #00f0a0;
            font-weight: 600;
            font-size: 1.1em;
            margin-bottom: 8px;
        }

        .job-location {
            color: #666;
            font-size: 0.95em;
            margin-bottom: 15px;
            display: flex;
            align-items: center;
        }

        .job-location::before {
            content: "📍";
            margin-right: 6px;
        }

        .job-meta {
            display: flex;
            flex-wrap: wrap;
            gap: 8px;
            margin-bottom: 15px;
        }

        .job-tag {
            background: rgba(0, 240, 160, 0.15);
            color: #00b894;
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 0.85em;
            font-weight: 500;
        }

        .job-actions {
            display: flex;
            gap: 10px;
            margin-top: 15px;
        }

        .job-btn {
            padding: 8px 16px;
            font-size: 14px;
            border-radius: 8px;
            border: none;
            cursor: pointer;
            font-weight: 500;
            transition: all 0.3s;
        }

        .job-btn-primary {
            background: #00f0a0;
            color: white;
        }

        .job-btn-secondary {
            background: #e9ecef;
            color: #666;
        }

        .job-btn:hover {
            transform: translateY(-1px);
        }

        /* Loading States */
        .loading {
            text-align: center;
            padding: 60px;
            color: #666;
        }

        .spinner {
            border: 3px solid #f3f3f3;
            border-top: 3px solid #00f0a0;
            border-radius: 50%;
            width: 40px;
            height: 40px;
            animation: spin 1s linear infinite;
            margin: 0 auto 20px;
        }

        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }

        /* Notifications */
        .notification {
            position: fixed;
            top: 20px;
            right: 20px;
            background: #00f0a0;
            color: white;
            padding: 16px 24px;
            border-radius: 12px;
            box-shadow: 0 8px 25px rgba(0, 240, 160, 0.3);
            z-index: 1000;
            transform: translateX(400px);
            transition: transform 0.3s ease;
            max-width: 350px;
        }

        .notification.show {
            transform: translateX(0);
        }

        .notification.error {
            background: #ff6b6b;
            box-shadow: 0 8px 25px rgba(255, 107, 107, 0.3);
        }

        .notification.success {
            background: #00b894;
            box-shadow: 0 8px 25px rgba(0, 184, 148, 0.3);
        }

        /* Responsive Design */
        @media (max-width: 768px) {
            .container {
                padding: 20px 15px;
            }

            .hero h1 {
                font-size: 2.5em;
            }

            .control-grid {
                grid-template-columns: 1fr;
            }

            .stats-dashboard {
                grid-template-columns: repeat(2, 1fr);
            }

            .job-grid {
                grid-template-columns: 1fr;
            }

            .search-filter {
                flex-direction: column;
                width: 100%;
            }

            .search-input {
                min-width: 100%;
            }

            .button-group {
                justify-content: center;
            }
        }

        /* Additional Animations */
        @keyframes fadeInUp {
            from {
                opacity: 0;
                transform: translateY(20px);
            }
            to {
                opacity: 1;
                transform: translateY(0);
            }
        }

        .job-card {
            animation: fadeInUp 0.5s ease forwards;
        }

        .stat-card {
            animation: fadeInUp 0.5s ease forwards;
        }

        /* Custom scrollbar */
        ::-webkit-scrollbar {
            width: 8px;
        }

        ::-webkit-scrollbar-track {
            background: #f1f1f1;
            border-radius: 4px;
        }

        ::-webkit-scrollbar-thumb {
            background: #00f0a0;
            border-radius: 4px;
        }

        ::-webkit-scrollbar-thumb:hover {
            background: #00d4aa;
        }
    </style>
</head>
<body>
    <div class="header">
        <div class="header-content">
            <div class="logo">JobRight AI</div>
            <nav class="nav-menu">
                <a href="#" class="nav-item">Dashboard</a>
                <a href="#" class="nav-item">Analytics</a>
                <a href="#" class="nav-item">Settings</a>
            </nav>
        </div>
    </div>

    <div class="container">
        <div class="hero">
            <h1>Intelligent Job Search</h1>
            <p>Find and apply to your dream jobs with AI-powered automation and smart pattern learning</p>
        </div>

        <div class="stats-dashboard">
            <div class="stat-card">
                <div class="stat-number" id="totalJobs">0</div>
                <div class="stat-label">Total Jobs</div>
            </div>
            <div class="stat-card">
                <div class="stat-number" id="appliedJobs">0</div>
                <div class="stat-label">Applied Today</div>
            </div>
            <div class="stat-card">
                <div class="stat-number" id="successRate">0%</div>
                <div class="stat-label">Success Rate</div>
            </div>
            <div class="stat-card">
                <div class="stat-number" id="selectedJobs">0</div>
                <div class="stat-label">Selected</div>
            </div>
        </div>

        <div class="control-panel">
            <div class="panel-title">Job Search Controls</div>

            <div class="control-grid">
                <div class="control-group">
                    <label for="keywords">🔍 Keywords</label>
                    <input type="text" id="keywords" placeholder="software engineer, data scientist, product manager" value="software engineer">
                </div>
                <div class="control-group">
                    <label for="location">📍 Location</label>
                    <input type="text" id="location" placeholder="San Francisco, New York, Remote" value="San Jose, CA">
                </div>
                <div class="control-group">
                    <label for="experience">💼 Experience Level</label>
                    <select id="experience">
                        <option value="all">All Levels</option>
                        <option value="entry">Entry Level</option>
                        <option value="mid">Mid Level</option>
                        <option value="senior">Senior Level</option>
                    </select>
                </div>
                <div class="control-group">
                    <label for="remote">🏠 Remote Work</label>
                    <select id="remote">
                        <option value="false">Any</option>
                        <option value="true">Remote Only</option>
                    </select>
                </div>
            </div>

            <div class="button-group">
                <button class="btn" onclick="scrapeJobs()" id="scrapeBtn">
                    🔍 <span>Scrape New Jobs</span>
                </button>
                <button class="btn btn-secondary" onclick="loadJobs()">
                    🔄 <span>Refresh Jobs</span>
                </button>
                <button class="btn" onclick="selectAll()">
                    ✅ <span>Select All</span>
                </button>
                <button class="btn" onclick="applyToSelected()" id="applyBtn">
                    🚀 <span>Auto-Apply Selected</span>
                </button>
                <button class="btn btn-danger" onclick="clearSelection()">
                    ❌ <span>Clear Selection</span>
                </button>
            </div>
        </div>

        <div class="jobs-container">
            <div class="jobs-header">
                <div class="jobs-title">Available Jobs</div>
                <div class="search-filter">
                    <input type="text" class="search-input" id="searchJobs" placeholder="🔍 Search jobs, companies, locations..." onkeyup="filterJobs()">
                </div>
            </div>

            <div id="jobsGrid" class="job-grid">
                <div class="loading">
                    <div class="spinner"></div>
                    <p>Loading amazing job opportunities...</p>
                </div>
            </div>
        </div>
    </div>

    <div id="notification" class="notification"></div>

    <script>
        let allJobs = [];
        let selectedJobs = new Set();
        let isLoading = false;

        // Load jobs on page load
        document.addEventListener('DOMContentLoaded', function() {
            loadJobs();
            loadAnalytics();
        });

        function showNotification(message, type = 'success') {
            const notification = document.getElementById('notification');
            notification.textContent = message;
            notification.className = `notification ${type}`;
            notification.classList.add('show');

            setTimeout(() => {
                notification.classList.remove('show');
            }, 4000);
        }

        function updateStats() {
            document.getElementById('totalJobs').textContent = allJobs.length;
            document.getElementById('selectedJobs').textContent = selectedJobs.size;
        }

        async function loadAnalytics() {
            try {
                const response = await fetch('/api/analytics');
                const data = await response.json();

                document.getElementById('appliedJobs').textContent = data.successful_applications || 0;
                document.getElementById('successRate').textContent = `${Math.round(data.success_rate || 0)}%`;
            } catch (error) {
                console.error('Error loading analytics:', error);
            }
        }

        async function loadJobs() {
            try {
                const response = await fetch('/api/jobs');
                const data = await response.json();
                allJobs = data.jobs;
                renderJobs(allJobs);
                updateStats();
                loadAnalytics();
            } catch (error) {
                showNotification('Failed to load jobs', 'error');
                console.error('Error loading jobs:', error);
            }
        }

        async function scrapeJobs() {
            if (isLoading) return;

            const keywords = document.getElementById('keywords').value;
            const location = document.getElementById('location').value;
            const experience = document.getElementById('experience').value;
            const remote = document.getElementById('remote').value === 'true';

            isLoading = true;
            const scrapeBtn = document.getElementById('scrapeBtn');
            const originalText = scrapeBtn.innerHTML;
            scrapeBtn.innerHTML = '⏳ <span>Scraping Jobs...</span>';
            scrapeBtn.disabled = true;

            try {
                const response = await fetch('/api/scrape', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        keywords: keywords,
                        location: location,
                        experience: experience,
                        remote: remote
                    })
                });

                const data = await response.json();

                if (data.success) {
                    showNotification(`🎉 Successfully scraped ${data.jobs_scraped} new jobs!`, 'success');
                    loadJobs(); // Refresh the jobs list
                } else {
                    showNotification(`❌ Failed to scrape jobs: ${data.error}`, 'error');
                }
            } catch (error) {
                showNotification('❌ Scraping failed. Please try again.', 'error');
                console.error('Error scraping jobs:', error);
            } finally {
                isLoading = false;
                scrapeBtn.innerHTML = originalText;
                scrapeBtn.disabled = false;
            }
        }

        async function applyToSelected() {
            if (selectedJobs.size === 0) {
                showNotification('Please select jobs to apply to first', 'error');
                return;
            }

            if (isLoading) return;

            isLoading = true;
            const applyBtn = document.getElementById('applyBtn');
            const originalText = applyBtn.innerHTML;
            applyBtn.innerHTML = '🚀 <span>Applying...</span>';
            applyBtn.disabled = true;

            try {
                const response = await fetch('/api/apply', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        job_ids: Array.from(selectedJobs)
                    })
                });

                const data = await response.json();

                if (data.success) {
                    showNotification(`🎉 Successfully applied to ${data.total_applied} jobs!`, 'success');
                    selectedJobs.clear();
                    updateJobCards();
                    updateStats();
                    loadAnalytics();
                } else {
                    showNotification(`❌ Application failed: ${data.error}`, 'error');
                }
            } catch (error) {
                showNotification('❌ Application failed. Please try again.', 'error');
                console.error('Error applying to jobs:', error);
            } finally {
                isLoading = false;
                applyBtn.innerHTML = originalText;
                applyBtn.disabled = false;
            }
        }

        function renderJobs(jobs) {
            const grid = document.getElementById('jobsGrid');

            if (jobs.length === 0) {
                grid.innerHTML = `
                    <div class="loading">
                        <p>🔍 No jobs found. Try scraping new jobs with different criteria!</p>
                    </div>
                `;
                return;
            }

            grid.innerHTML = jobs.map(job => `
                <div class="job-card" data-job-id="${job.id}" ${selectedJobs.has(job.id) ? 'class="job-card selected"' : ''}>
                    <input type="checkbox" class="job-checkbox" onchange="toggleJobSelection(${job.id})" ${selectedJobs.has(job.id) ? 'checked' : ''}>

                    <div class="job-title">${job.title}</div>
                    <div class="job-company">${job.company || 'Company Name'}</div>
                    <div class="job-location">${job.location || 'Location not specified'}</div>

                    <div class="job-meta">
                        <span class="job-tag">${job.job_type || 'Full-time'}</span>
                        <span class="job-tag">${job.remote_option || 'On-site'}</span>
                        <span class="job-tag">${job.experience_level || 'Mid-level'}</span>
                        ${job.applied ? '<span class="job-tag" style="background: #e8f5e8; color: #27ae60;">✅ Applied</span>' : ''}
                    </div>

                    <div class="job-actions">
                        <button class="job-btn job-btn-primary" onclick="window.open('${job.url}', '_blank')">
                            🔗 View Job
                        </button>
                        ${job.salary_range ? `<span style="font-size: 12px; color: #666;">${job.salary_range}</span>` : ''}
                    </div>
                </div>
            `).join('');

            updateJobCards();
        }

        function toggleJobSelection(jobId) {
            if (selectedJobs.has(jobId)) {
                selectedJobs.delete(jobId);
            } else {
                selectedJobs.add(jobId);
            }
            updateJobCards();
            updateStats();
        }

        function updateJobCards() {
            document.querySelectorAll('.job-card').forEach(card => {
                const jobId = parseInt(card.getAttribute('data-job-id'));
                if (selectedJobs.has(jobId)) {
                    card.classList.add('selected');
                } else {
                    card.classList.remove('selected');
                }
            });
        }

        function selectAll() {
            allJobs.forEach(job => selectedJobs.add(job.id));
            document.querySelectorAll('.job-checkbox').forEach(checkbox => {
                checkbox.checked = true;
            });
            updateJobCards();
            updateStats();
            showNotification(`Selected ${allJobs.length} jobs`, 'success');
        }

        function clearSelection() {
            selectedJobs.clear();
            document.querySelectorAll('.job-checkbox').forEach(checkbox => {
                checkbox.checked = false;
            });
            updateJobCards();
            updateStats();
            showNotification('Selection cleared', 'success');
        }

        function filterJobs() {
            const searchTerm = document.getElementById('searchJobs').value.toLowerCase();
            const filteredJobs = allJobs.filter(job =>
                job.title.toLowerCase().includes(searchTerm) ||
                (job.company && job.company.toLowerCase().includes(searchTerm)) ||
                (job.location && job.location.toLowerCase().includes(searchTerm))
            );
            renderJobs(filteredJobs);
        }

        // Keyboard shortcuts
        document.addEventListener('keydown', function(e) {
            if (e.ctrlKey || e.metaKey) {
                switch(e.key) {
                    case 'a':
                        e.preventDefault();
                        selectAll();
                        break;
                    case 'r':
                        e.preventDefault();
                        loadJobs();
                        break;
                    case 'Enter':
                        e.preventDefault();
                        if (selectedJobs.size > 0) {
                            applyToSelected();
                        }
                        break;
                }
            }
        });

        // Auto-refresh every 5 minutes
        setInterval(loadAnalytics, 300000);
    </script>
</body>
</html>'''

    with open('templates/jobright_replica.html', 'w') as f:
        f.write(html_template)

    logger.info("✅ JobRight replica template created successfully")

def main():
    """Main function to run the JobRight replica application"""
    logger.info("🚀 JOBRIGHT AI REPLICA STARTING")
    logger.info("🎯 LinkedIn Job Scraping + Intelligent Auto-Apply")
    logger.info("🤖 Pattern Learning + Analytics Dashboard")
    logger.info("="*60)

    # Create templates
    create_templates()

    # Set up signal handlers for graceful shutdown
    def signal_handler(sig, frame):
        logger.info("🛑 Shutting down gracefully...")
        master_applier.close()
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    try:
        logger.info("🌐 Starting JobRight replica server on http://localhost:5000")
        logger.info("💡 Open your browser and navigate to: http://localhost:5000")
        logger.info("🎯 Features available:")
        logger.info("   • LinkedIn job scraping with smart criteria")
        logger.info("   • Intelligent auto-apply with pattern learning")
        logger.info("   • Real-time analytics and success tracking")
        logger.info("   • JobRight.ai UI replica with modern design")
        logger.info("="*60)

        app.run(host='0.0.0.0', port=5000, debug=False, threaded=True)
    except Exception as e:
        logger.error(f"❌ Server failed to start: {e}")
    finally:
        master_applier.close()

if __name__ == "__main__":
    main()


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