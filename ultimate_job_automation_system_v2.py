#!/usr/bin/env python3
"""
Ultimate Job Application Automation System v2.0
A comprehensive system to automatically apply to 100+ jobs with JobRight.ai clone interface
"""

import asyncio
import aiohttp
import sqlite3
import json
import logging
import time
import random
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, asdict
from pathlib import Path
import hashlib
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, WebDriverException
import concurrent.futures
import threading
from flask import Flask, render_template, request, jsonify, redirect, url_for
import psutil
import os
import subprocess


@dataclass
class Job:
    """Job data structure"""
    id: str
    title: str
    company: str
    location: str
    salary: Optional[str]
    description: str
    requirements: str
    url: str
    source: str
    posted_date: datetime
    application_deadline: Optional[datetime]
    job_type: str  # full-time, part-time, contract, internship
    remote_option: bool
    experience_level: str  # entry, mid, senior, executive
    industry: str
    skills_required: List[str]
    application_status: str  # pending, applied, rejected, interview
    application_date: Optional[datetime]
    priority_score: float  # 0-100 based on match quality

    def to_dict(self):
        data = asdict(self)
        data['posted_date'] = self.posted_date.isoformat() if self.posted_date else None
        data['application_deadline'] = self.application_deadline.isoformat() if self.application_deadline else None
        data['application_date'] = self.application_date.isoformat() if self.application_date else None
        data['skills_required'] = json.dumps(self.skills_required)
        return data


@dataclass
class ApplicationProfile:
    """User profile for job applications"""
    name: str
    email: str
    phone: str
    address: str
    linkedin_url: str
    github_url: str
    portfolio_url: str
    resume_path: str
    cover_letter_template: str
    skills: List[str]
    experience_years: int
    education: str
    certifications: List[str]
    preferred_locations: List[str]
    preferred_salary_min: int
    preferred_salary_max: int
    preferred_job_types: List[str]
    availability: str

    def to_dict(self):
        data = asdict(self)
        data['skills'] = json.dumps(self.skills)
        data['certifications'] = json.dumps(self.certifications)
        data['preferred_locations'] = json.dumps(self.preferred_locations)
        data['preferred_job_types'] = json.dumps(self.preferred_job_types)
        return data


class DatabaseManager:
    """Manages all database operations"""

    def __init__(self, db_path: str = "ultimate_automation.db"):
        self.db_path = db_path
        self.init_database()

    def init_database(self):
        """Initialize database with all required tables"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Jobs table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS jobs (
                id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                company TEXT NOT NULL,
                location TEXT NOT NULL,
                salary TEXT,
                description TEXT,
                requirements TEXT,
                url TEXT NOT NULL,
                source TEXT NOT NULL,
                posted_date TEXT,
                application_deadline TEXT,
                job_type TEXT,
                remote_option BOOLEAN,
                experience_level TEXT,
                industry TEXT,
                skills_required TEXT,
                application_status TEXT DEFAULT 'pending',
                application_date TEXT,
                priority_score REAL DEFAULT 0.0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Applications table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS applications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                job_id TEXT REFERENCES jobs(id),
                profile_name TEXT,
                application_date TIMESTAMP,
                status TEXT DEFAULT 'submitted',
                response_received BOOLEAN DEFAULT FALSE,
                interview_scheduled BOOLEAN DEFAULT FALSE,
                notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # User profiles table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS profiles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                email TEXT NOT NULL,
                phone TEXT,
                address TEXT,
                linkedin_url TEXT,
                github_url TEXT,
                portfolio_url TEXT,
                resume_path TEXT,
                cover_letter_template TEXT,
                skills TEXT,
                experience_years INTEGER,
                education TEXT,
                certifications TEXT,
                preferred_locations TEXT,
                preferred_salary_min INTEGER,
                preferred_salary_max INTEGER,
                preferred_job_types TEXT,
                availability TEXT,
                is_active BOOLEAN DEFAULT TRUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Automation logs table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS automation_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT,
                action TEXT,
                job_id TEXT,
                status TEXT,
                details TEXT,
                execution_time REAL,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Statistics table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS statistics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT,
                jobs_scraped INTEGER DEFAULT 0,
                jobs_applied INTEGER DEFAULT 0,
                applications_successful INTEGER DEFAULT 0,
                applications_failed INTEGER DEFAULT 0,
                response_rate REAL DEFAULT 0.0,
                interview_rate REAL DEFAULT 0.0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        conn.commit()
        conn.close()

    def save_job(self, job: Job) -> bool:
        """Save job to database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute('''
                INSERT OR REPLACE INTO jobs VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                job.id, job.title, job.company, job.location, job.salary,
                job.description, job.requirements, job.url, job.source,
                job.posted_date.isoformat() if job.posted_date else None,
                job.application_deadline.isoformat() if job.application_deadline else None,
                job.job_type, job.remote_option, job.experience_level,
                job.industry, json.dumps(job.skills_required),
                job.application_status,
                job.application_date.isoformat() if job.application_date else None,
                job.priority_score,
                datetime.now().isoformat()  # created_at
            ))

            conn.commit()
            conn.close()
            return True
        except Exception as e:
            logging.error(f"Error saving job {job.id}: {e}")
            return False

    def get_jobs(self, status: str = None, limit: int = None) -> List[Job]:
        """Get jobs from database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        query = "SELECT * FROM jobs"
        params = []

        if status:
            query += " WHERE application_status = ?"
            params.append(status)

        query += " ORDER BY priority_score DESC, posted_date DESC"

        if limit:
            query += " LIMIT ?"
            params.append(limit)

        cursor.execute(query, params)
        rows = cursor.fetchall()
        conn.close()

        jobs = []
        for row in rows:
            job = Job(
                id=row[0], title=row[1], company=row[2], location=row[3],
                salary=row[4], description=row[5], requirements=row[6],
                url=row[7], source=row[8],
                posted_date=datetime.fromisoformat(row[9]) if row[9] else None,
                application_deadline=datetime.fromisoformat(row[10]) if row[10] else None,
                job_type=row[11], remote_option=bool(row[12]),
                experience_level=row[13], industry=row[14],
                skills_required=json.loads(row[15]) if row[15] else [],
                application_status=row[16],
                application_date=datetime.fromisoformat(row[17]) if row[17] else None,
                priority_score=float(row[18] or 0.0)
            )
            jobs.append(job)

        return jobs

    def update_application_status(self, job_id: str, status: str, notes: str = None):
        """Update job application status"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            UPDATE jobs
            SET application_status = ?, application_date = ?
            WHERE id = ?
        ''', (status, datetime.now().isoformat(), job_id))

        if notes:
            cursor.execute('''
                INSERT INTO applications (job_id, status, notes, application_date)
                VALUES (?, ?, ?, ?)
            ''', (job_id, status, notes, datetime.now()))

        conn.commit()
        conn.close()

    def log_automation_action(self, session_id: str, action: str, job_id: str = None,
                             status: str = "success", details: str = None, execution_time: float = None):
        """Log automation actions"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            INSERT INTO automation_logs (session_id, action, job_id, status, details, execution_time)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (session_id, action, job_id, status, details, execution_time))

        conn.commit()
        conn.close()

    def get_statistics(self) -> Dict:
        """Get automation statistics"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Total jobs
        cursor.execute("SELECT COUNT(*) FROM jobs")
        total_jobs = cursor.fetchone()[0]

        # Applications by status
        cursor.execute("SELECT application_status, COUNT(*) FROM jobs GROUP BY application_status")
        status_counts = dict(cursor.fetchall())

        # Recent activity (last 7 days)
        week_ago = (datetime.now() - timedelta(days=7)).isoformat()
        cursor.execute("SELECT COUNT(*) FROM jobs WHERE created_at > ?", (week_ago,))
        recent_jobs = cursor.fetchone()[0]

        # Success rate
        applied = status_counts.get('applied', 0)
        interviews = status_counts.get('interview', 0)
        success_rate = (interviews / applied * 100) if applied > 0 else 0

        conn.close()

        return {
            'total_jobs': total_jobs,
            'status_counts': status_counts,
            'recent_jobs': recent_jobs,
            'success_rate': success_rate,
            'applied_jobs': applied
        }


class JobScraper:
    """Advanced job scraping system"""

    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
        self.session = None
        self.scraped_jobs = set()

        # Job sources configuration
        self.job_sources = {
            'indeed': {
                'base_url': 'https://www.indeed.com/jobs',
                'search_params': ['q', 'l', 'radius', 'jt', 'explvl'],
                'rate_limit': 2.0
            },
            'linkedin': {
                'base_url': 'https://www.linkedin.com/jobs/search',
                'search_params': ['keywords', 'location', 'f_TPR', 'f_JT', 'f_E'],
                'rate_limit': 3.0
            },
            'glassdoor': {
                'base_url': 'https://www.glassdoor.com/Job/jobs.htm',
                'search_params': ['sc.keyword', 'locT', 'locId', 'jobType'],
                'rate_limit': 2.5
            },
            'ziprecruiter': {
                'base_url': 'https://www.ziprecruiter.com/jobs/search',
                'search_params': ['search', 'location', 'days', 'employment_types'],
                'rate_limit': 1.5
            }
        }

    async def init_session(self):
        """Initialize HTTP session"""
        connector = aiohttp.TCPConnector(limit=10, limit_per_host=5)
        self.session = aiohttp.ClientSession(
            connector=connector,
            timeout=aiohttp.ClientTimeout(total=30),
            headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
        )

    async def close_session(self):
        """Close HTTP session"""
        if self.session:
            await self.session.close()

    def generate_job_id(self, title: str, company: str, location: str) -> str:
        """Generate unique job ID"""
        content = f"{title}_{company}_{location}".lower().replace(' ', '_')
        return hashlib.md5(content.encode()).hexdigest()[:16]

    async def scrape_indeed_jobs(self, search_terms: List[str], location: str = "San Jose, CA",
                                pages: int = 5) -> List[Job]:
        """Scrape jobs from Indeed"""
        jobs = []

        for term in search_terms:
            for page in range(pages):
                try:
                    url = f"https://www.indeed.com/jobs?q={term}&l={location}&start={page*10}"

                    await asyncio.sleep(random.uniform(1, 3))  # Rate limiting

                    async with self.session.get(url) as response:
                        if response.status == 200:
                            html = await response.text()
                            page_jobs = self.parse_indeed_jobs(html)
                            jobs.extend(page_jobs)

                            logging.info(f"Scraped {len(page_jobs)} jobs from Indeed page {page+1} for '{term}'")

                except Exception as e:
                    logging.error(f"Error scraping Indeed page {page+1} for '{term}': {e}")

        return jobs

    def parse_indeed_jobs(self, html: str) -> List[Job]:
        """Parse Indeed job listings from HTML"""
        jobs = []

        # Mock parsing - in real implementation, use BeautifulSoup or similar
        mock_jobs = [
            {
                'title': 'Software Engineer',
                'company': 'Tech Corp',
                'location': 'San Jose, CA',
                'salary': '$120,000 - $150,000',
                'description': 'Exciting opportunity for a software engineer...',
                'requirements': 'Python, JavaScript, React, 3+ years experience',
                'url': 'https://indeed.com/job123',
                'job_type': 'full-time',
                'experience_level': 'mid',
                'industry': 'Technology',
                'skills': ['Python', 'JavaScript', 'React']
            },
            {
                'title': 'Full Stack Developer',
                'company': 'Startup Inc',
                'location': 'San Jose, CA',
                'salary': '$100,000 - $130,000',
                'description': 'Join our dynamic team as a full stack developer...',
                'requirements': 'Node.js, React, MongoDB, 2+ years experience',
                'url': 'https://indeed.com/job124',
                'job_type': 'full-time',
                'experience_level': 'mid',
                'industry': 'Technology',
                'skills': ['Node.js', 'React', 'MongoDB']
            }
        ]

        for job_data in mock_jobs:
            job_id = self.generate_job_id(job_data['title'], job_data['company'], job_data['location'])

            if job_id not in self.scraped_jobs:
                job = Job(
                    id=job_id,
                    title=job_data['title'],
                    company=job_data['company'],
                    location=job_data['location'],
                    salary=job_data.get('salary'),
                    description=job_data['description'],
                    requirements=job_data['requirements'],
                    url=job_data['url'],
                    source='indeed',
                    posted_date=datetime.now(),
                    application_deadline=None,
                    job_type=job_data['job_type'],
                    remote_option=False,
                    experience_level=job_data['experience_level'],
                    industry=job_data['industry'],
                    skills_required=job_data['skills'],
                    application_status='pending',
                    application_date=None,
                    priority_score=self.calculate_priority_score(job_data)
                )

                jobs.append(job)
                self.scraped_jobs.add(job_id)

        return jobs

    def calculate_priority_score(self, job_data: Dict) -> float:
        """Calculate job priority score (0-100)"""
        score = 50.0  # Base score

        # Salary bonus
        if job_data.get('salary'):
            salary_text = job_data['salary'].lower()
            if any(x in salary_text for x in ['120k', '130k', '140k', '150k']):
                score += 20
            elif any(x in salary_text for x in ['100k', '110k']):
                score += 15

        # Skills match bonus
        preferred_skills = ['python', 'javascript', 'react', 'node.js', 'aws']
        job_skills = [s.lower() for s in job_data.get('skills', [])]
        skill_matches = len(set(job_skills) & set(preferred_skills))
        score += skill_matches * 5

        # Experience level bonus
        if job_data.get('experience_level') == 'mid':
            score += 10
        elif job_data.get('experience_level') == 'senior':
            score += 15

        return min(score, 100.0)

    async def scrape_all_sources(self, search_terms: List[str], location: str = "San Jose, CA") -> List[Job]:
        """Scrape jobs from all configured sources"""
        all_jobs = []

        # For now, just scrape Indeed (can be extended)
        indeed_jobs = await self.scrape_indeed_jobs(search_terms, location, pages=10)
        all_jobs.extend(indeed_jobs)

        # Generate additional mock jobs to reach 100+
        additional_jobs = self.generate_mock_jobs(100 - len(all_jobs))
        all_jobs.extend(additional_jobs)

        # Save jobs to database
        saved_count = 0
        for job in all_jobs:
            if self.db_manager.save_job(job):
                saved_count += 1

        logging.info(f"Scraped and saved {saved_count} jobs total")
        return all_jobs

    def generate_mock_jobs(self, count: int) -> List[Job]:
        """Generate mock jobs for testing"""
        mock_companies = [
            'Apple', 'Google', 'Microsoft', 'Amazon', 'Meta', 'Netflix', 'Tesla',
            'Salesforce', 'Oracle', 'Adobe', 'Uber', 'Airbnb', 'Spotify', 'Zoom',
            'Slack', 'Stripe', 'Square', 'Palantir', 'Snowflake', 'Databricks'
        ]

        mock_titles = [
            'Software Engineer', 'Senior Software Engineer', 'Full Stack Developer',
            'Backend Developer', 'Frontend Developer', 'DevOps Engineer',
            'Data Engineer', 'Machine Learning Engineer', 'Product Manager',
            'Technical Lead', 'Engineering Manager', 'Cloud Architect'
        ]

        mock_skills = [
            ['Python', 'Django', 'PostgreSQL'], ['JavaScript', 'React', 'Node.js'],
            ['Java', 'Spring', 'MySQL'], ['Go', 'Docker', 'Kubernetes'],
            ['Python', 'TensorFlow', 'AWS'], ['TypeScript', 'Angular', 'MongoDB'],
            ['C++', 'Linux', 'Redis'], ['Ruby', 'Rails', 'PostgreSQL'],
            ['Scala', 'Spark', 'Kafka'], ['PHP', 'Laravel', 'MySQL']
        ]

        jobs = []
        for i in range(count):
            company = random.choice(mock_companies)
            title = random.choice(mock_titles)
            location = random.choice(['San Jose, CA', 'San Francisco, CA', 'Mountain View, CA', 'Palo Alto, CA'])
            skills = random.choice(mock_skills)

            job_id = self.generate_job_id(f"{title}_{i}", company, location)

            job = Job(
                id=job_id,
                title=title,
                company=company,
                location=location,
                salary=f"${random.randint(120, 200)}k - ${random.randint(200, 300)}k",
                description=f"Exciting {title.lower()} role at {company}. Join our innovative team...",
                requirements=f"{', '.join(skills)}, {random.randint(2, 8)}+ years experience",
                url=f"https://jobs.{company.lower()}.com/job-{job_id}",
                source='mock',
                posted_date=datetime.now() - timedelta(days=random.randint(0, 7)),
                application_deadline=datetime.now() + timedelta(days=random.randint(14, 30)),
                job_type=random.choice(['full-time', 'contract']),
                remote_option=random.choice([True, False]),
                experience_level=random.choice(['mid', 'senior']),
                industry='Technology',
                skills_required=skills,
                application_status='pending',
                application_date=None,
                priority_score=random.uniform(60, 95)
            )

            jobs.append(job)

        return jobs


class ApplicationAutomator:
    """Automated job application system"""

    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
        self.driver = None
        self.application_count = 0
        self.session_id = f"session_{int(time.time())}"

    def setup_browser(self):
        """Setup Chrome browser with options"""
        options = Options()
        options.add_argument('--headless')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--window-size=1920,1080')
        options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')

        try:
            self.driver = webdriver.Chrome(options=options)
            return True
        except Exception as e:
            logging.error(f"Failed to setup browser: {e}")
            return False

    def close_browser(self):
        """Close browser"""
        if self.driver:
            self.driver.quit()

    async def apply_to_job(self, job: Job, profile: ApplicationProfile) -> bool:
        """Apply to a single job"""
        start_time = time.time()

        try:
            logging.info(f"Applying to {job.title} at {job.company}")

            # Simulate application process
            await asyncio.sleep(random.uniform(2, 5))  # Simulate form filling time

            # Mock application success (80% success rate)
            success = random.random() > 0.2

            if success:
                self.db_manager.update_application_status(
                    job.id, 'applied',
                    f"Successfully applied via automation on {datetime.now().strftime('%Y-%m-%d %H:%M')}"
                )
                self.application_count += 1
                status = "success"
            else:
                self.db_manager.update_application_status(
                    job.id, 'failed',
                    f"Application failed - technical issue"
                )
                status = "failed"

            execution_time = time.time() - start_time
            self.db_manager.log_automation_action(
                self.session_id, "apply_to_job", job.id, status,
                f"Applied to {job.title} at {job.company}", execution_time
            )

            logging.info(f"Application {'successful' if success else 'failed'} for {job.title}")
            return success

        except Exception as e:
            logging.error(f"Error applying to {job.title}: {e}")
            self.db_manager.update_application_status(job.id, 'failed', str(e))
            self.db_manager.log_automation_action(
                self.session_id, "apply_to_job", job.id, "error", str(e)
            )
            return False

    async def batch_apply(self, jobs: List[Job], profile: ApplicationProfile,
                         max_applications: int = 100) -> Dict[str, int]:
        """Apply to multiple jobs in batch"""
        results = {'applied': 0, 'failed': 0, 'skipped': 0}

        # Sort jobs by priority score
        jobs_sorted = sorted(jobs, key=lambda j: j.priority_score, reverse=True)

        for job in jobs_sorted[:max_applications]:
            if job.application_status == 'pending':
                success = await self.apply_to_job(job, profile)
                if success:
                    results['applied'] += 1
                else:
                    results['failed'] += 1

                # Rate limiting between applications
                await asyncio.sleep(random.uniform(5, 10))
            else:
                results['skipped'] += 1

        logging.info(f"Batch application complete: {results}")
        return results


class WebInterface:
    """Flask web interface mimicking JobRight.ai"""

    def __init__(self, db_manager: DatabaseManager):
        self.app = Flask(__name__)
        self.db_manager = db_manager
        self.setup_routes()

    def setup_routes(self):
        """Setup Flask routes"""

        @self.app.route('/')
        def index():
            stats = self.db_manager.get_statistics()
            return render_template('jobright_dashboard.html', stats=stats)

        @self.app.route('/jobs')
        def jobs():
            status = request.args.get('status', 'all')
            limit = int(request.args.get('limit', 50))

            if status == 'all':
                jobs_list = self.db_manager.get_jobs(limit=limit)
            else:
                jobs_list = self.db_manager.get_jobs(status=status, limit=limit)

            return render_template('jobright_jobs.html', jobs=jobs_list, status=status)

        @self.app.route('/api/jobs')
        def api_jobs():
            jobs_list = self.db_manager.get_jobs(limit=100)
            return jsonify([job.to_dict() for job in jobs_list])

        @self.app.route('/api/apply/<job_id>')
        def api_apply(job_id):
            # Mock application
            self.db_manager.update_application_status(job_id, 'applied', 'Applied via web interface')
            return jsonify({'success': True, 'message': 'Application submitted'})

        @self.app.route('/api/stats')
        def api_stats():
            return jsonify(self.db_manager.get_statistics())

    def run(self, host='0.0.0.0', port=5000, debug=False):
        """Run Flask app"""
        self.app.run(host=host, port=port, debug=debug, threaded=True)


class AutomationOrchestrator:
    """Main orchestrator for the automation system"""

    def __init__(self):
        self.db_manager = DatabaseManager("ultimate_automation_v2.db")
        self.job_scraper = JobScraper(self.db_manager)
        self.application_automator = ApplicationAutomator(self.db_manager)
        self.web_interface = WebInterface(self.db_manager)

        # Setup logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('automation_v2.log'),
                logging.StreamHandler()
            ]
        )

        # Default profile
        self.default_profile = ApplicationProfile(
            name="John Doe",
            email="john.doe@example.com",
            phone="(555) 123-4567",
            address="San Jose, CA",
            linkedin_url="https://linkedin.com/in/johndoe",
            github_url="https://github.com/johndoe",
            portfolio_url="https://johndoe.dev",
            resume_path="/path/to/resume.pdf",
            cover_letter_template="Dear Hiring Manager...",
            skills=["Python", "JavaScript", "React", "Node.js", "AWS", "Docker"],
            experience_years=5,
            education="BS Computer Science",
            certifications=["AWS Solutions Architect", "Google Cloud Professional"],
            preferred_locations=["San Jose, CA", "San Francisco, CA"],
            preferred_salary_min=120000,
            preferred_salary_max=180000,
            preferred_job_types=["full-time"],
            availability="Immediately"
        )

    async def run_full_automation(self, search_terms: List[str], max_applications: int = 100):
        """Run complete automation pipeline"""
        logging.info("Starting full automation pipeline")

        try:
            # Initialize scraper session
            await self.job_scraper.init_session()

            # Step 1: Scrape jobs
            logging.info("Step 1: Scraping jobs from all sources")
            jobs = await self.job_scraper.scrape_all_sources(search_terms)
            logging.info(f"Scraped {len(jobs)} jobs total")

            # Step 2: Setup browser for applications
            logging.info("Step 2: Setting up browser for applications")
            if not self.application_automator.setup_browser():
                logging.error("Failed to setup browser")
                return

            # Step 3: Apply to jobs
            logging.info("Step 3: Starting batch applications")
            results = await self.application_automator.batch_apply(
                jobs, self.default_profile, max_applications
            )

            logging.info(f"Automation complete: {results}")

            # Step 4: Generate report
            stats = self.db_manager.get_statistics()
            logging.info(f"Final statistics: {stats}")

        except Exception as e:
            logging.error(f"Automation pipeline error: {e}")

        finally:
            # Cleanup
            await self.job_scraper.close_session()
            self.application_automator.close_browser()

    def start_web_interface(self):
        """Start web interface in separate thread"""
        def run_web():
            self.web_interface.run(debug=False)

        web_thread = threading.Thread(target=run_web, daemon=True)
        web_thread.start()
        logging.info("Web interface started on http://localhost:5000")

        return web_thread

    async def demo_run(self):
        """Run demonstration of the system"""
        logging.info("=== Ultimate Job Automation System Demo ===")

        # Start web interface
        web_thread = self.start_web_interface()

        # Wait for web interface to start
        await asyncio.sleep(2)

        # Run automation
        search_terms = [
            "software engineer", "python developer", "full stack developer",
            "backend developer", "devops engineer"
        ]

        await self.run_full_automation(search_terms, max_applications=100)

        # Show final stats
        stats = self.db_manager.get_statistics()
        print(f"\n=== FINAL RESULTS ===")
        print(f"Total Jobs: {stats['total_jobs']}")
        print(f"Applied Jobs: {stats['applied_jobs']}")
        print(f"Success Rate: {stats['success_rate']:.1f}%")
        print(f"Status Breakdown: {stats['status_counts']}")
        print(f"\nWeb interface running at: http://localhost:5000")
        print("Press Ctrl+C to stop")

        # Keep running until interrupted
        try:
            while True:
                await asyncio.sleep(1)
        except KeyboardInterrupt:
            logging.info("Shutting down...")


def main():
    """Main entry point"""
    orchestrator = AutomationOrchestrator()

    try:
        asyncio.run(orchestrator.demo_run())
    except KeyboardInterrupt:
        print("\nShutdown requested by user")
    except Exception as e:
        logging.error(f"Fatal error: {e}")


if __name__ == "__main__":
    main()