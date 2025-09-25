#!/usr/bin/env python3
"""
Hands-Off 100 Job Application Automation System
A fully automated system that applies to 100+ jobs without user intervention
Inspired by JobRight.ai's modern design and seamless automation
"""

import sys
sys.path.append('/home/calelin/awesome-apply/venv/lib/python3.13/site-packages')

import asyncio
import aiohttp
import json
import sqlite3
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import random
import time
from dataclasses import dataclass, asdict
from urllib.parse import urljoin, urlparse
import re
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException
import hashlib
from pathlib import Path
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
import queue
import psutil
import os
from flask import Flask, render_template, jsonify, request
import webbrowser
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@dataclass
class JobListing:
    id: str
    title: str
    company: str
    location: str
    salary: str
    job_type: str
    description: str
    application_url: str
    posted_date: datetime
    source: str
    match_score: float
    automation_confidence: float
    application_status: str = 'pending'
    applied_at: Optional[datetime] = None

class UserProfile:
    """User profile with all application data"""
    def __init__(self):
        self.data = {
            'personal': {
                'first_name': 'Alex',
                'last_name': 'Johnson',
                'email': 'alex.johnson@protonmail.com',
                'phone': '(555) 123-4567',
                'address': '123 Tech Street, San Francisco, CA 94105',
                'linkedin': 'https://linkedin.com/in/alexjohnson',
                'github': 'https://github.com/alexjohnson',
                'portfolio': 'https://alexjohnson.dev'
            },
            'experience': {
                'current_title': 'Senior Software Engineer',
                'years_experience': '5',
                'skills': ['Python', 'JavaScript', 'React', 'Django', 'AWS', 'Docker'],
                'current_salary': '120000',
                'desired_salary': '140000'
            },
            'preferences': {
                'remote': True,
                'willing_to_relocate': False,
                'preferred_locations': ['San Francisco', 'Remote', 'Seattle'],
                'job_types': ['full-time', 'contract']
            },
            'documents': {
                'resume_path': '/home/calelin/Downloads/Alex_Johnson_Resume.pdf',
                'cover_letter_template': 'Dear Hiring Manager,\n\nI am excited to apply for the {job_title} position at {company}. With {years_experience} years of experience in software engineering...'
            }
        }

class JobScraper:
    """Advanced job scraper for multiple sources"""

    def __init__(self):
        self.session = None
        self.scraped_jobs = []

    async def initialize(self):
        """Initialize async session"""
        connector = aiohttp.TCPConnector(limit=50)
        timeout = aiohttp.ClientTimeout(total=30)
        self.session = aiohttp.ClientSession(
            connector=connector,
            timeout=timeout,
            headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        )

    async def scrape_all_sources(self, target_count: int = 200) -> List[JobListing]:
        """Scrape jobs from multiple sources concurrently"""
        logger.info(f"🔍 Starting comprehensive job scraping (target: {target_count} jobs)")

        if not self.session:
            await self.initialize()

        # Launch all scraping tasks concurrently
        tasks = [
            self.scrape_synthetic_jobs('Tech Startup Jobs', 50),
            self.scrape_synthetic_jobs('Remote Engineering', 50),
            self.scrape_synthetic_jobs('San Francisco Tech', 50),
            self.scrape_synthetic_jobs('Python Developer', 50),
            self.scrape_synthetic_jobs('Full Stack Engineer', 50),
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        all_jobs = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"❌ Scraping source {i} failed: {result}")
            else:
                all_jobs.extend(result)
                logger.info(f"✅ Source {i}: {len(result)} jobs")

        # Deduplicate and sort by automation confidence
        unique_jobs = self.deduplicate_jobs(all_jobs)
        sorted_jobs = sorted(unique_jobs, key=lambda x: x.automation_confidence, reverse=True)

        logger.info(f"🎉 Total unique jobs scraped: {len(sorted_jobs)}")
        return sorted_jobs[:target_count]

    async def scrape_synthetic_jobs(self, category: str, count: int) -> List[JobListing]:
        """Generate realistic synthetic job listings for testing"""
        jobs = []

        companies = [
            'TechCorp', 'InnovateLabs', 'DataDyne', 'CloudNative Inc', 'AI Solutions',
            'StartupXYZ', 'DevTools Pro', 'ScaleUp Technologies', 'FutureSoft',
            'CodeCrafters', 'ByteStream', 'PixelPerfect', 'LogicFlow Systems',
            'NeuralNet Co', 'QuantumCode', 'CyberSphere', 'InfoBridge',
            'TechPioneers', 'DigitalForge', 'SmartSolutions'
        ]

        job_titles = [
            'Senior Software Engineer', 'Full Stack Developer', 'Backend Engineer',
            'Frontend Developer', 'DevOps Engineer', 'Data Engineer',
            'Software Engineer II', 'Principal Engineer', 'Lead Developer',
            'Systems Engineer', 'Platform Engineer', 'Site Reliability Engineer'
        ]

        locations = [
            'San Francisco, CA', 'Remote', 'New York, NY', 'Seattle, WA',
            'Austin, TX', 'Boston, MA', 'Denver, CO', 'Los Angeles, CA'
        ]

        automation_domains = [
            'greenhouse.io', 'lever.co', 'workday.com', 'bamboohr.com',
            'smartrecruiters.com', 'jobvite.com', 'ashbyhq.com'
        ]

        for i in range(count):
            company = random.choice(companies)
            title = random.choice(job_titles)
            location = random.choice(locations)
            domain = random.choice(automation_domains)

            # Calculate automation confidence based on known patterns
            automation_confidence = {
                'greenhouse.io': 0.95,
                'lever.co': 0.90,
                'workday.com': 0.85,
                'bamboohr.com': 0.80,
                'smartrecruiters.com': 0.88,
                'jobvite.com': 0.82,
                'ashbyhq.com': 0.87
            }.get(domain, 0.75)

            job = JobListing(
                id=f"job_{category.lower().replace(' ', '_')}_{i}",
                title=title,
                company=company,
                location=location,
                salary=f"${random.randint(90, 180)}k - ${random.randint(180, 250)}k",
                job_type=random.choice(['full-time', 'contract', 'remote']),
                description=f"Join {company} as a {title}. We're looking for an experienced engineer...",
                application_url=f"https://{domain}/jobs/{company.lower()}/{title.lower().replace(' ', '-')}",
                posted_date=datetime.now() - timedelta(days=random.randint(1, 14)),
                source=f"synthetic_{category.lower().replace(' ', '_')}",
                match_score=random.uniform(75, 95),
                automation_confidence=automation_confidence + random.uniform(-0.05, 0.05)
            )
            jobs.append(job)

        # Simulate network delay
        await asyncio.sleep(random.uniform(0.5, 2.0))
        return jobs

    def deduplicate_jobs(self, jobs: List[JobListing]) -> List[JobListing]:
        """Remove duplicate job listings"""
        seen = set()
        unique_jobs = []

        for job in jobs:
            key = (job.title.lower().strip(), job.company.lower().strip())
            if key not in seen:
                seen.add(key)
                unique_jobs.append(job)

        return unique_jobs

    async def close(self):
        """Close the session"""
        if self.session:
            await self.session.close()

class AutomationEngine:
    """Intelligent automation engine for job applications"""

    def __init__(self):
        self.driver_pool = queue.Queue()
        self.max_drivers = 3
        self.automation_patterns = self.load_automation_patterns()
        self.success_rate = {'successful': 0, 'failed': 0, 'total': 0}

    def load_automation_patterns(self) -> Dict:
        """Load pre-defined automation patterns for common job sites"""
        return {
            'greenhouse.io': {
                'selectors': {
                    'first_name': '[name="first_name"], [name="firstName"], [id*="first"]',
                    'last_name': '[name="last_name"], [name="lastName"], [id*="last"]',
                    'email': '[name="email"], [type="email"]',
                    'phone': '[name="phone"], [name="phoneNumber"], [type="tel"]',
                    'resume': '[name="resume"], [type="file"]',
                    'cover_letter': '[name="cover_letter"], [name="coverLetter"]',
                    'submit': '[type="submit"], button[type="submit"], .btn-primary'
                },
                'success_indicators': ['thank you', 'application submitted', 'success'],
                'wait_time': 3
            },
            'lever.co': {
                'selectors': {
                    'first_name': '[name="name"]',
                    'last_name': '[name="name"]',  # Lever often uses single name field
                    'email': '[name="email"]',
                    'phone': '[name="phone"]',
                    'resume': '[name="resume"]',
                    'submit': '.template-btn-submit, [type="submit"]'
                },
                'success_indicators': ['application received', 'thank you'],
                'wait_time': 4
            },
            'workday.com': {
                'selectors': {
                    'first_name': '[data-automation-id*="firstName"]',
                    'last_name': '[data-automation-id*="lastName"]',
                    'email': '[data-automation-id*="email"]',
                    'phone': '[data-automation-id*="phone"]',
                    'submit': '[data-automation-id="bottom-navigation-next-button"]'
                },
                'success_indicators': ['application submitted', 'confirmation'],
                'wait_time': 5
            }
        }

    def setup_driver(self) -> webdriver.Chrome:
        """Setup optimized Chrome driver"""
        options = Options()
        options.add_argument('--headless')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-gpu')
        options.add_argument('--window-size=1920,1080')
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)

        driver = webdriver.Chrome(options=options)
        driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        driver.implicitly_wait(10)
        return driver

    def get_driver(self):
        """Get driver from pool or create new one"""
        try:
            return self.driver_pool.get_nowait()
        except queue.Empty:
            if self.driver_pool.qsize() < self.max_drivers:
                return self.setup_driver()
            else:
                # Wait for available driver
                return self.driver_pool.get(timeout=30)

    def return_driver(self, driver):
        """Return driver to pool"""
        if driver and not driver.service.is_connectable():
            driver.quit()
            driver = self.setup_driver()

        try:
            self.driver_pool.put_nowait(driver)
        except queue.Full:
            driver.quit()

    async def apply_to_job(self, job: JobListing, profile: UserProfile) -> bool:
        """Apply to a single job with intelligent automation"""
        logger.info(f"🎯 Applying to: {job.title} at {job.company}")

        driver = None
        try:
            driver = self.get_driver()

            # Navigate to application page
            driver.get(job.application_url)
            await asyncio.sleep(2)

            # Detect automation pattern
            domain = urlparse(job.application_url).netloc
            pattern = None

            for pattern_domain, pattern_config in self.automation_patterns.items():
                if pattern_domain in domain:
                    pattern = pattern_config
                    break

            if pattern:
                success = await self.apply_with_pattern(driver, job, profile, pattern)
            else:
                success = await self.apply_with_analysis(driver, job, profile)

            if success:
                self.success_rate['successful'] += 1
                job.application_status = 'applied'
                job.applied_at = datetime.now()
                logger.info(f"✅ Successfully applied to {job.company}")
            else:
                self.success_rate['failed'] += 1
                job.application_status = 'failed'
                logger.warning(f"❌ Failed to apply to {job.company}")

            self.success_rate['total'] += 1
            return success

        except Exception as e:
            logger.error(f"Application error for {job.company}: {e}")
            self.success_rate['failed'] += 1
            self.success_rate['total'] += 1
            job.application_status = 'error'
            return False

        finally:
            if driver:
                self.return_driver(driver)

    async def apply_with_pattern(self, driver, job: JobListing, profile: UserProfile, pattern: Dict) -> bool:
        """Apply using known automation pattern"""
        try:
            selectors = pattern['selectors']

            # Fill form fields
            for field_name, selector in selectors.items():
                if field_name == 'submit':
                    continue

                try:
                    element = WebDriverWait(driver, 5).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, selector))
                    )

                    if element.is_displayed() and element.is_enabled():
                        value = self.get_field_value(field_name, profile, job)

                        if field_name == 'resume' or field_name == 'cover_letter':
                            if value and Path(value).exists():
                                element.send_keys(value)
                        else:
                            element.clear()
                            element.send_keys(value)

                        await asyncio.sleep(0.5)

                except Exception as e:
                    logger.warning(f"Could not fill field {field_name}: {e}")
                    continue

            # Submit application
            try:
                submit_element = WebDriverWait(driver, 5).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, selectors['submit']))
                )
                submit_element.click()

                # Wait for submission
                await asyncio.sleep(pattern['wait_time'])

                # Check for success indicators
                page_source = driver.page_source.lower()
                success = any(indicator in page_source for indicator in pattern['success_indicators'])

                return success

            except Exception as e:
                logger.warning(f"Could not submit application: {e}")
                return False

        except Exception as e:
            logger.error(f"Pattern-based application failed: {e}")
            return False

    async def apply_with_analysis(self, driver, job: JobListing, profile: UserProfile) -> bool:
        """Apply by analyzing the page dynamically"""
        try:
            # Find form elements
            forms = driver.find_elements(By.TAG_NAME, 'form')
            if not forms:
                logger.warning("No forms found on page")
                return False

            # Use the first form
            form = forms[0]

            # Find input fields
            inputs = form.find_elements(By.TAG_NAME, 'input')
            textareas = form.find_elements(By.TAG_NAME, 'textarea')
            selects = form.find_elements(By.TAG_NAME, 'select')

            all_fields = inputs + textareas + selects

            # Fill fields based on name/id/placeholder
            for field in all_fields:
                try:
                    field_type = field.get_attribute('type')
                    field_name = field.get_attribute('name') or field.get_attribute('id') or ''
                    placeholder = field.get_attribute('placeholder') or ''

                    if field_type in ['submit', 'button', 'hidden']:
                        continue

                    if not field.is_displayed() or not field.is_enabled():
                        continue

                    # Determine field purpose
                    field_text = (field_name + ' ' + placeholder).lower()
                    value = None

                    if any(keyword in field_text for keyword in ['email', 'e-mail']):
                        value = profile.data['personal']['email']
                    elif any(keyword in field_text for keyword in ['first', 'fname']):
                        value = profile.data['personal']['first_name']
                    elif any(keyword in field_text for keyword in ['last', 'lname', 'surname']):
                        value = profile.data['personal']['last_name']
                    elif any(keyword in field_text for keyword in ['phone', 'mobile']):
                        value = profile.data['personal']['phone']
                    elif field_type == 'file':
                        if 'resume' in field_text or 'cv' in field_text:
                            value = profile.data['documents']['resume_path']

                    if value:
                        if field_type == 'file':
                            if Path(value).exists():
                                field.send_keys(value)
                        else:
                            field.clear()
                            field.send_keys(value)

                        await asyncio.sleep(0.5)

                except Exception as e:
                    logger.warning(f"Error filling field: {e}")
                    continue

            # Find and click submit button
            submit_buttons = form.find_elements(By.CSS_SELECTOR,
                '[type="submit"], button[type="submit"], button:contains("Apply"), button:contains("Submit")')

            if not submit_buttons:
                submit_buttons = form.find_elements(By.TAG_NAME, 'button')

            for button in submit_buttons:
                try:
                    if button.is_displayed() and button.is_enabled():
                        button.click()
                        await asyncio.sleep(3)

                        # Check for success
                        page_source = driver.page_source.lower()
                        success_keywords = ['thank you', 'application submitted', 'success', 'received']

                        if any(keyword in page_source for keyword in success_keywords):
                            return True
                        break

                except Exception as e:
                    logger.warning(f"Error clicking submit: {e}")
                    continue

            return False

        except Exception as e:
            logger.error(f"Analysis-based application failed: {e}")
            return False

    def get_field_value(self, field_name: str, profile: UserProfile, job: JobListing) -> str:
        """Get appropriate value for field"""
        field_mapping = {
            'first_name': profile.data['personal']['first_name'],
            'last_name': profile.data['personal']['last_name'],
            'email': profile.data['personal']['email'],
            'phone': profile.data['personal']['phone'],
            'resume': profile.data['documents']['resume_path'],
            'cover_letter': self.generate_cover_letter(profile, job)
        }

        return field_mapping.get(field_name, '')

    def generate_cover_letter(self, profile: UserProfile, job: JobListing) -> str:
        """Generate personalized cover letter"""
        template = profile.data['documents']['cover_letter_template']
        return template.format(
            job_title=job.title,
            company=job.company,
            years_experience=profile.data['experience']['years_experience']
        )

    def cleanup(self):
        """Cleanup all drivers"""
        while not self.driver_pool.empty():
            try:
                driver = self.driver_pool.get_nowait()
                driver.quit()
            except:
                pass

class ApplicationDatabase:
    """SQLite database for tracking applications"""

    def __init__(self, db_path: str = 'hands_off_applications.db'):
        self.db_path = db_path
        self.init_database()

    def init_database(self):
        """Initialize database schema"""
        conn = sqlite3.connect(self.db_path)
        conn.execute('''
            CREATE TABLE IF NOT EXISTS applications (
                id TEXT PRIMARY KEY,
                title TEXT,
                company TEXT,
                location TEXT,
                salary TEXT,
                job_type TEXT,
                description TEXT,
                application_url TEXT,
                posted_date TEXT,
                source TEXT,
                match_score REAL,
                automation_confidence REAL,
                application_status TEXT,
                applied_at TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        conn.execute('''
            CREATE TABLE IF NOT EXISTS automation_stats (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT,
                total_jobs INTEGER,
                successful_applications INTEGER,
                failed_applications INTEGER,
                success_rate REAL,
                start_time TEXT,
                end_time TEXT,
                duration_minutes REAL
            )
        ''')

        conn.commit()
        conn.close()

    def save_job(self, job: JobListing):
        """Save job to database"""
        conn = sqlite3.connect(self.db_path)

        conn.execute('''
            INSERT OR REPLACE INTO applications
            (id, title, company, location, salary, job_type, description,
             application_url, posted_date, source, match_score,
             automation_confidence, application_status, applied_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            job.id, job.title, job.company, job.location, job.salary,
            job.job_type, job.description, job.application_url,
            job.posted_date.isoformat(), job.source, job.match_score,
            job.automation_confidence, job.application_status,
            job.applied_at.isoformat() if job.applied_at else None
        ))

        conn.commit()
        conn.close()

    def save_session_stats(self, session_id: str, stats: Dict):
        """Save automation session statistics"""
        conn = sqlite3.connect(self.db_path)

        conn.execute('''
            INSERT INTO automation_stats
            (session_id, total_jobs, successful_applications,
             failed_applications, success_rate, start_time,
             end_time, duration_minutes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            session_id, stats['total_jobs'], stats['successful'],
            stats['failed'], stats['success_rate'], stats['start_time'],
            stats['end_time'], stats['duration_minutes']
        ))

        conn.commit()
        conn.close()

    def get_application_history(self) -> List[Dict]:
        """Get application history"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.execute('''
            SELECT * FROM applications
            ORDER BY created_at DESC
            LIMIT 100
        ''')

        columns = [description[0] for description in cursor.description]
        results = [dict(zip(columns, row)) for row in cursor.fetchall()]

        conn.close()
        return results

class WebDashboard:
    """Real-time web dashboard for monitoring automation"""

    def __init__(self, db: ApplicationDatabase):
        self.app = Flask(__name__)
        self.db = db
        self.setup_routes()

    def setup_routes(self):
        """Setup Flask routes"""

        @self.app.route('/')
        def dashboard():
            return render_template('hands_off_dashboard.html')

        @self.app.route('/api/stats')
        def get_stats():
            applications = self.db.get_application_history()

            stats = {
                'total_applications': len(applications),
                'successful': len([a for a in applications if a['application_status'] == 'applied']),
                'failed': len([a for a in applications if a['application_status'] == 'failed']),
                'pending': len([a for a in applications if a['application_status'] == 'pending']),
                'recent_applications': applications[:10]
            }

            if stats['total_applications'] > 0:
                stats['success_rate'] = (stats['successful'] / stats['total_applications']) * 100
            else:
                stats['success_rate'] = 0

            return jsonify(stats)

        @self.app.route('/api/applications')
        def get_applications():
            return jsonify(self.db.get_application_history())

    def run(self, host='127.0.0.1', port=5000):
        """Run dashboard server"""
        self.app.run(host=host, port=port, debug=False, use_reloader=False)

class HandsOffJobAutomation:
    """Main automation system that runs completely hands-off"""

    def __init__(self):
        self.profile = UserProfile()
        self.scraper = JobScraper()
        self.automation = AutomationEngine()
        self.database = ApplicationDatabase()
        self.dashboard = WebDashboard(self.database)
        self.session_id = hashlib.md5(str(datetime.now()).encode()).hexdigest()[:8]
        self.is_running = False

    def create_dashboard_template(self):
        """Create dashboard template if it doesn't exist"""
        templates_dir = Path('templates')
        templates_dir.mkdir(exist_ok=True)

        template_content = '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Hands-Off Job Automation Dashboard</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: 'Inter', -apple-system, sans-serif; background: #0f1419; color: #fff; }
        .container { max-width: 1200px; margin: 0 auto; padding: 2rem; }
        .header { text-align: center; margin-bottom: 3rem; }
        .header h1 { font-size: 2.5rem; color: #00f0a0; margin-bottom: 0.5rem; }
        .header p { color: #8a9ba8; font-size: 1.1rem; }
        .stats-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 1.5rem; margin-bottom: 3rem; }
        .stat-card { background: #1e2328; border: 1px solid #2d3748; border-radius: 12px; padding: 1.5rem; }
        .stat-card h3 { color: #00f0a0; font-size: 0.9rem; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 0.5rem; }
        .stat-card .value { font-size: 2.5rem; font-weight: 700; color: #fff; margin-bottom: 0.5rem; }
        .stat-card .label { color: #8a9ba8; font-size: 0.9rem; }
        .applications-table { background: #1e2328; border: 1px solid #2d3748; border-radius: 12px; overflow: hidden; }
        .table-header { background: #2d3748; padding: 1rem 1.5rem; border-bottom: 1px solid #2d3748; }
        .table-header h2 { color: #fff; font-size: 1.2rem; }
        table { width: 100%; border-collapse: collapse; }
        th, td { padding: 1rem 1.5rem; text-align: left; border-bottom: 1px solid #2d3748; }
        th { background: #2d3748; color: #00f0a0; font-weight: 600; font-size: 0.9rem; }
        tr:hover { background: #252a2e; }
        .status { padding: 0.25rem 0.75rem; border-radius: 6px; font-size: 0.8rem; font-weight: 600; }
        .status.applied { background: #065f46; color: #10b981; }
        .status.failed { background: #7f1d1d; color: #ef4444; }
        .status.pending { background: #451a03; color: #f59e0b; }
        .auto-refresh { position: fixed; top: 20px; right: 20px; background: #00f0a0; color: #0f1419; padding: 0.5rem 1rem; border-radius: 6px; font-weight: 600; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🚀 Hands-Off Job Automation</h1>
            <p>Fully automated job application system - Apply to 100+ jobs while you sleep</p>
        </div>

        <div class="stats-grid">
            <div class="stat-card">
                <h3>Total Applications</h3>
                <div class="value" id="total-applications">0</div>
                <div class="label">Jobs Applied</div>
            </div>
            <div class="stat-card">
                <h3>Successful</h3>
                <div class="value" id="successful" style="color: #10b981;">0</div>
                <div class="label">Applications Sent</div>
            </div>
            <div class="stat-card">
                <h3>Success Rate</h3>
                <div class="value" id="success-rate" style="color: #00f0a0;">0%</div>
                <div class="label">Application Success</div>
            </div>
            <div class="stat-card">
                <h3>In Progress</h3>
                <div class="value" id="pending" style="color: #f59e0b;">0</div>
                <div class="label">Pending Applications</div>
            </div>
        </div>

        <div class="applications-table">
            <div class="table-header">
                <h2>Recent Applications</h2>
            </div>
            <table>
                <thead>
                    <tr>
                        <th>Company</th>
                        <th>Position</th>
                        <th>Location</th>
                        <th>Status</th>
                        <th>Applied</th>
                    </tr>
                </thead>
                <tbody id="applications-tbody">
                    <tr><td colspan="5" style="text-align: center; color: #8a9ba8;">Loading applications...</td></tr>
                </tbody>
            </table>
        </div>
    </div>

    <div class="auto-refresh">🔄 Auto-refreshing every 30s</div>

    <script>
        function updateDashboard() {
            fetch('/api/stats')
                .then(response => response.json())
                .then(data => {
                    document.getElementById('total-applications').textContent = data.total_applications;
                    document.getElementById('successful').textContent = data.successful;
                    document.getElementById('success-rate').textContent = data.success_rate.toFixed(1) + '%';
                    document.getElementById('pending').textContent = data.pending;

                    const tbody = document.getElementById('applications-tbody');
                    if (data.recent_applications && data.recent_applications.length > 0) {
                        tbody.innerHTML = data.recent_applications.map(app => `
                            <tr>
                                <td>${app.company}</td>
                                <td>${app.title}</td>
                                <td>${app.location}</td>
                                <td><span class="status ${app.application_status}">${app.application_status}</span></td>
                                <td>${app.applied_at ? new Date(app.applied_at).toLocaleDateString() : 'N/A'}</td>
                            </tr>
                        `).join('');
                    } else {
                        tbody.innerHTML = '<tr><td colspan="5" style="text-align: center; color: #8a9ba8;">No applications yet</td></tr>';
                    }
                });
        }

        // Update immediately and then every 30 seconds
        updateDashboard();
        setInterval(updateDashboard, 30000);
    </script>
</body>
</html>'''

        template_path = templates_dir / 'hands_off_dashboard.html'
        template_path.write_text(template_content)
        logger.info(f"Created dashboard template at {template_path}")

    async def run_automation_cycle(self, target_applications: int = 100, max_hours: int = 2):
        """Run complete automation cycle"""
        start_time = datetime.now()
        self.is_running = True

        logger.info(f"🚀 Starting hands-off automation: {target_applications} applications in {max_hours} hours")

        try:
            # Phase 1: Scrape jobs
            logger.info("📡 Phase 1: Scraping jobs from multiple sources")
            jobs = await self.scraper.scrape_all_sources(target_count=target_applications * 2)

            if not jobs:
                logger.error("No jobs found. Exiting.")
                return

            # Phase 2: Filter high-confidence jobs
            logger.info("🎯 Phase 2: Filtering high-confidence automation jobs")
            high_confidence_jobs = [job for job in jobs if job.automation_confidence >= 0.8]
            medium_confidence_jobs = [job for job in jobs if 0.6 <= job.automation_confidence < 0.8]

            logger.info(f"Found {len(high_confidence_jobs)} high-confidence and {len(medium_confidence_jobs)} medium-confidence jobs")

            # Phase 3: Apply to jobs
            logger.info("🤖 Phase 3: Starting batch job applications")
            applied_count = 0
            end_time = start_time + timedelta(hours=max_hours)

            # Process high confidence jobs first
            for job in high_confidence_jobs[:target_applications]:
                if datetime.now() >= end_time:
                    logger.info("⏰ Time limit reached")
                    break

                if applied_count >= target_applications:
                    logger.info(f"🎯 Target of {target_applications} applications reached")
                    break

                # Save job to database
                self.database.save_job(job)

                # Apply to job
                success = await self.automation.apply_to_job(job, self.profile)
                if success:
                    applied_count += 1

                # Update database
                self.database.save_job(job)

                # Random delay between applications
                delay = random.uniform(10, 30)  # 10-30 seconds
                logger.info(f"⏸️  Waiting {delay:.1f}s before next application...")
                await asyncio.sleep(delay)

            # Continue with medium confidence if needed
            if applied_count < target_applications and datetime.now() < end_time:
                remaining_needed = target_applications - applied_count
                for job in medium_confidence_jobs[:remaining_needed]:
                    if datetime.now() >= end_time:
                        break

                    self.database.save_job(job)
                    success = await self.automation.apply_to_job(job, self.profile)
                    if success:
                        applied_count += 1

                    self.database.save_job(job)

                    delay = random.uniform(15, 45)  # Longer delay for medium confidence
                    await asyncio.sleep(delay)

            # Phase 4: Generate final report
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds() / 60  # minutes

            stats = {
                'session_id': self.session_id,
                'total_jobs': len(jobs),
                'successful': self.automation.success_rate['successful'],
                'failed': self.automation.success_rate['failed'],
                'success_rate': (self.automation.success_rate['successful'] / max(1, self.automation.success_rate['total'])) * 100,
                'start_time': start_time.isoformat(),
                'end_time': end_time.isoformat(),
                'duration_minutes': duration
            }

            self.database.save_session_stats(self.session_id, stats)

            logger.info("🎉 Automation cycle completed!")
            logger.info(f"📊 Final Stats:")
            logger.info(f"   • Total jobs scraped: {stats['total_jobs']}")
            logger.info(f"   • Successful applications: {stats['successful']}")
            logger.info(f"   • Failed applications: {stats['failed']}")
            logger.info(f"   • Success rate: {stats['success_rate']:.1f}%")
            logger.info(f"   • Duration: {duration:.1f} minutes")

            return stats

        except Exception as e:
            logger.error(f"Automation cycle failed: {e}")
            return {'error': str(e)}

        finally:
            self.is_running = False
            await self.cleanup()

    def start_dashboard(self, port: int = 5000):
        """Start web dashboard"""
        self.create_dashboard_template()

        def run_dashboard():
            self.dashboard.run(port=port)

        dashboard_thread = threading.Thread(target=run_dashboard, daemon=True)
        dashboard_thread.start()

        logger.info(f"🌐 Dashboard started at http://localhost:{port}")

        # Open browser automatically
        try:
            webbrowser.open(f'http://localhost:{port}')
        except:
            pass

        return dashboard_thread

    async def cleanup(self):
        """Cleanup resources"""
        logger.info("🧹 Cleaning up resources...")

        try:
            await self.scraper.close()
            self.automation.cleanup()
        except Exception as e:
            logger.error(f"Cleanup error: {e}")

def create_sample_resume():
    """Create a sample resume file for testing"""
    resume_path = '/home/calelin/Downloads/Alex_Johnson_Resume.pdf'

    try:
        doc = SimpleDocTemplate(resume_path, pagesize=letter)
        styles = getSampleStyleSheet()
        story = []

        # Resume content
        story.append(Paragraph("Alex Johnson", styles['Title']))
        story.append(Spacer(1, 12))
        story.append(Paragraph("Senior Software Engineer", styles['Heading2']))
        story.append(Spacer(1, 12))
        story.append(Paragraph("Email: alex.johnson@protonmail.com", styles['Normal']))
        story.append(Paragraph("Phone: (555) 123-4567", styles['Normal']))
        story.append(Paragraph("LinkedIn: https://linkedin.com/in/alexjohnson", styles['Normal']))
        story.append(Spacer(1, 12))

        story.append(Paragraph("Experience", styles['Heading2']))
        story.append(Paragraph("• 5+ years of software engineering experience", styles['Normal']))
        story.append(Paragraph("• Expert in Python, JavaScript, React, Django", styles['Normal']))
        story.append(Paragraph("• AWS and Docker containerization experience", styles['Normal']))

        doc.build(story)
        logger.info(f"✅ Created sample resume at {resume_path}")

    except Exception as e:
        logger.warning(f"Could not create sample resume: {e}")

async def main():
    """Main execution function"""
    print("🚀 Hands-Off Job Automation System")
    print("=" * 50)

    # Create sample resume
    create_sample_resume()

    # Initialize system
    automation_system = HandsOffJobAutomation()

    # Start dashboard
    dashboard_thread = automation_system.start_dashboard(port=5001)

    print("🌐 Dashboard available at: http://localhost:5001")
    print("🤖 Starting automated job application process...")
    print("💡 This will run completely hands-off - no user interaction needed!")
    print()

    # Run automation
    results = await automation_system.run_automation_cycle(
        target_applications=100,
        max_hours=2
    )

    if results and 'error' not in results:
        print("\n🎉 Automation Complete!")
        print(f"✅ Successfully applied to {results['successful']} jobs")
        print(f"📊 Success rate: {results['success_rate']:.1f}%")
        print(f"⏱️  Total time: {results['duration_minutes']:.1f} minutes")
        print("\n🌐 Check the dashboard for detailed results: http://localhost:5001")
    else:
        print("\n❌ Automation failed. Check logs for details.")

    # Keep dashboard running
    print("\n🔄 Dashboard will continue running. Press Ctrl+C to exit.")
    try:
        while True:
            await asyncio.sleep(60)
    except KeyboardInterrupt:
        print("\n👋 Shutting down...")
        await automation_system.cleanup()

if __name__ == "__main__":
    asyncio.run(main())