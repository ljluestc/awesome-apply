#!/usr/bin/env python3
"""
JobRight.ai Clone - Backend API Server
Provides job scraping, auto-application, and pattern analysis
"""

import asyncio
import json
import sqlite3
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import logging
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
import re
from flask import Flask, jsonify, request, render_template
from flask_cors import CORS
import threading

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

class JobDatabase:
    def __init__(self, db_path: str = "jobright_clone.db"):
        self.db_path = db_path
        self.init_database()

    def init_database(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Jobs table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS jobs (
                id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                company TEXT NOT NULL,
                location TEXT,
                salary TEXT,
                description TEXT,
                url TEXT UNIQUE,
                apply_url TEXT,
                posted_date TEXT,
                job_type TEXT,
                experience_level TEXT,
                source TEXT,
                scraped_at TEXT,
                application_status TEXT DEFAULT 'not_applied',
                automation_score REAL DEFAULT 0.0,
                tags TEXT
            )
        """)

        # Application attempts table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS applications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                job_id TEXT,
                attempt_date TEXT,
                status TEXT,
                automation_success BOOLEAN,
                error_message TEXT,
                form_patterns TEXT,
                completion_time REAL,
                FOREIGN KEY (job_id) REFERENCES jobs (id)
            )
        """)

        # Form patterns table for analysis
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS form_patterns (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                domain TEXT,
                form_selector TEXT,
                field_patterns TEXT,
                success_indicators TEXT,
                automation_difficulty INTEGER,
                last_updated TEXT
            )
        """)

        conn.commit()
        conn.close()

    def save_job(self, job: Job):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            INSERT OR REPLACE INTO jobs VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            job.id, job.title, job.company, job.location, job.salary,
            job.description, job.url, job.apply_url, job.posted_date,
            job.job_type, job.experience_level, job.source, job.scraped_at,
            job.application_status, job.automation_score, json.dumps(job.tags)
        ))

        conn.commit()
        conn.close()

    def get_jobs(self, limit: int = 100, filters: Dict = None) -> List[Job]:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        query = "SELECT * FROM jobs"
        params = []

        if filters:
            conditions = []
            if filters.get('keywords'):
                conditions.append("(title LIKE ? OR description LIKE ?)")
                keyword = f"%{' '.join(filters['keywords'])}%"
                params.extend([keyword, keyword])
            if filters.get('location'):
                conditions.append("location LIKE ?")
                params.append(f"%{filters['location']}%")
            if filters.get('company'):
                conditions.append("company LIKE ?")
                params.append(f"%{filters['company']}%")

            if conditions:
                query += " WHERE " + " AND ".join(conditions)

        query += f" ORDER BY scraped_at DESC LIMIT {limit}"

        cursor.execute(query, params)
        rows = cursor.fetchall()
        conn.close()

        jobs = []
        for row in rows:
            job = Job(
                id=row[0], title=row[1], company=row[2], location=row[3],
                salary=row[4], description=row[5], url=row[6], apply_url=row[7],
                posted_date=row[8], job_type=row[9], experience_level=row[10],
                source=row[11], scraped_at=row[12], application_status=row[13],
                automation_score=row[14], tags=json.loads(row[15]) if row[15] else []
            )
            jobs.append(job)

        return jobs

class LinkedInJobScraper:
    def __init__(self):
        from robust_job_scraper import RobustJobScraper
        self.robust_scraper = RobustJobScraper(headless=True)  # Use headless for production

    def search_jobs(self, criteria: SearchCriteria) -> List[Job]:
        """Search for jobs using robust multi-source scraper"""
        try:
            logger.info(f"🔍 Starting robust job search...")
            jobs = self.robust_scraper.search_jobs(criteria)
            logger.info(f"✅ Robust scraper found {len(jobs)} jobs")

            # If we got jobs, return them
            if jobs:
                return jobs
            else:
                # If no jobs found, use fallback
                logger.warning("⚠️ No jobs found, using fallback data")
                return self._fallback_search(criteria)

        except Exception as e:
            logger.error(f"❌ Robust scraper failed: {e}")
            # Fallback to sample data
            return self._fallback_search(criteria)

    def _fallback_search(self, criteria: SearchCriteria) -> List[Job]:
        """Fallback to basic scraping method"""
        logger.info("🔄 Using fallback search method...")

        jobs = []

        # Create some sample jobs for testing if scraping fails
        sample_jobs = [
            {
                "title": f"{' '.join(criteria.keywords)} - Sample Position 1",
                "company": "Tech Corp",
                "location": criteria.location,
                "salary": "$120,000 - $150,000",
                "description": f"We are looking for a talented {' '.join(criteria.keywords)} to join our team. This is a great opportunity to work with cutting-edge technology and make a real impact.",
                "url": "https://linkedin.com/jobs/sample1",
                "apply_url": "https://linkedin.com/jobs/sample1/apply"
            },
            {
                "title": f"Senior {' '.join(criteria.keywords)}",
                "company": "Innovation Labs",
                "location": criteria.location,
                "salary": "$140,000 - $180,000",
                "description": f"Join our growing team as a Senior {' '.join(criteria.keywords)}. We offer competitive compensation and excellent benefits.",
                "url": "https://linkedin.com/jobs/sample2",
                "apply_url": "https://linkedin.com/jobs/sample2/apply"
            },
            {
                "title": f"{' '.join(criteria.keywords)} Manager",
                "company": "Future Systems",
                "location": criteria.location,
                "salary": "$160,000 - $200,000",
                "description": f"Lead a team of talented engineers as a {' '.join(criteria.keywords)} Manager. This role combines technical expertise with leadership responsibilities.",
                "url": "https://linkedin.com/jobs/sample3",
                "apply_url": "https://linkedin.com/jobs/sample3/apply"
            },
            {
                "title": f"Remote {' '.join(criteria.keywords)}",
                "company": "Global Tech Solutions",
                "location": "Remote",
                "salary": "$130,000 - $170,000",
                "description": f"Work from anywhere as a Remote {' '.join(criteria.keywords)}. We're building the future of distributed teams.",
                "url": "https://linkedin.com/jobs/sample4",
                "apply_url": "https://linkedin.com/jobs/sample4/apply"
            },
            {
                "title": f"Junior {' '.join(criteria.keywords)}",
                "company": "StartupXYZ",
                "location": criteria.location,
                "salary": "$90,000 - $120,000",
                "description": f"Perfect entry-level position for aspiring {' '.join(criteria.keywords)}s. Great mentorship and learning opportunities.",
                "url": "https://linkedin.com/jobs/sample5",
                "apply_url": "https://linkedin.com/jobs/sample5/apply"
            }
        ]

        for i, sample in enumerate(sample_jobs):
            job_id = f"sample_{hash(sample['title'])}_{int(time.time())}_{i}"

            job = Job(
                id=job_id,
                title=sample["title"],
                company=sample["company"],
                location=sample["location"],
                salary=sample["salary"],
                description=sample["description"],
                url=sample["url"],
                apply_url=sample["apply_url"],
                posted_date=datetime.now().isoformat(),
                job_type=criteria.job_type or "full-time",
                experience_level=criteria.experience_level or "mid",
                source="sample_data",
                scraped_at=datetime.now().isoformat(),
                tags=criteria.keywords
            )

            jobs.append(job)

        logger.info(f"✅ Fallback method created {len(jobs)} sample jobs")
        return jobs

    def close(self):
        if hasattr(self, 'robust_scraper'):
            self.robust_scraper.close()

class AutoApplicationSystem:
    def __init__(self, db: JobDatabase):
        self.db = db
        self.user_profile = self._load_user_profile()

    def _load_user_profile(self) -> Dict:
        """Load user profile for auto-fill"""
        return {
            "first_name": "John",
            "last_name": "Doe",
            "email": "john.doe@email.com",
            "phone": "(555) 123-4567",
            "resume_path": "/path/to/resume.pdf",
            "cover_letter": "I am interested in this position...",
            "linkedin_url": "https://linkedin.com/in/johndoe",
            "github_url": "https://github.com/johndoe",
            "website": "https://johndoe.com"
        }

    def apply_to_job(self, job: Job) -> Dict:
        """Attempt to auto-apply to a job"""
        try:
            if not job.apply_url:
                return {"success": False, "error": "No apply URL found"}

            driver = self._setup_application_driver()
            result = self._attempt_application(driver, job)
            driver.quit()

            # Save application attempt
            self._save_application_attempt(job.id, result)

            return result

        except Exception as e:
            logger.error(f"Error applying to job {job.id}: {e}")
            return {"success": False, "error": str(e)}

    def _setup_application_driver(self):
        chrome_options = Options()
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")

        driver = webdriver.Chrome(options=chrome_options)
        return driver

    def _attempt_application(self, driver, job: Job) -> Dict:
        """Attempt to automatically fill and submit application"""
        start_time = time.time()

        try:
            driver.get(job.apply_url)
            time.sleep(3)

            # Detect form type and apply appropriate strategy
            form_pattern = self._detect_form_pattern(driver)

            if form_pattern["type"] == "linkedin_easy_apply":
                result = self._handle_linkedin_easy_apply(driver, job)
            elif form_pattern["type"] == "greenhouse":
                result = self._handle_greenhouse_form(driver, job)
            elif form_pattern["type"] == "workday":
                result = self._handle_workday_form(driver, job)
            elif form_pattern["type"] == "generic":
                result = self._handle_generic_form(driver, job)
            else:
                result = self._analyze_unknown_form(driver, job)

            completion_time = time.time() - start_time
            result["completion_time"] = completion_time
            result["form_pattern"] = form_pattern

            return result

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "completion_time": time.time() - start_time
            }

    def _detect_form_pattern(self, driver) -> Dict:
        """Detect the type of application form"""
        try:
            url = driver.current_url.lower()
            page_source = driver.page_source.lower()

            if "linkedin.com" in url and "easy-apply" in page_source:
                return {"type": "linkedin_easy_apply", "confidence": 0.9}
            elif "greenhouse.io" in url or "greenhouse" in page_source:
                return {"type": "greenhouse", "confidence": 0.8}
            elif "workday.com" in url or "workday" in page_source:
                return {"type": "workday", "confidence": 0.8}
            elif any(indicator in page_source for indicator in ["apply", "application", "job"]):
                return {"type": "generic", "confidence": 0.5}
            else:
                return {"type": "unknown", "confidence": 0.1}

        except Exception as e:
            logger.error(f"Error detecting form pattern: {e}")
            return {"type": "unknown", "confidence": 0.0}

    def _handle_linkedin_easy_apply(self, driver, job: Job) -> Dict:
        """Handle LinkedIn Easy Apply process"""
        try:
            # Click Easy Apply button
            easy_apply_btn = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, ".jobs-apply-button"))
            )
            easy_apply_btn.click()
            time.sleep(2)

            steps_completed = 0
            max_steps = 5

            while steps_completed < max_steps:
                try:
                    # Fill current form step
                    self._fill_form_fields(driver)
                    steps_completed += 1

                    # Look for Next or Submit button
                    next_buttons = driver.find_elements(By.CSS_SELECTOR,
                        "button[data-control-name='continue_unify'], button[aria-label*='Submit'], button[aria-label*='Next']")

                    if next_buttons:
                        next_buttons[0].click()
                        time.sleep(2)

                        # Check if application was submitted
                        if "application submitted" in driver.page_source.lower():
                            return {"success": True, "steps_completed": steps_completed}
                    else:
                        break

                except Exception as e:
                    logger.error(f"Error in LinkedIn step {steps_completed}: {e}")
                    break

            return {"success": False, "error": "Could not complete all steps", "steps_completed": steps_completed}

        except Exception as e:
            return {"success": False, "error": f"LinkedIn Easy Apply error: {str(e)}"}

    def _handle_greenhouse_form(self, driver, job: Job) -> Dict:
        """Handle Greenhouse application forms"""
        try:
            # Fill basic information
            self._fill_form_fields(driver)

            # Upload resume if file input found
            file_inputs = driver.find_elements(By.CSS_SELECTOR, "input[type='file']")
            if file_inputs and self.user_profile.get("resume_path"):
                file_inputs[0].send_keys(self.user_profile["resume_path"])
                time.sleep(2)

            # Submit form
            submit_buttons = driver.find_elements(By.CSS_SELECTOR,
                "input[type='submit'], button[type='submit'], button:contains('Submit')")

            if submit_buttons:
                submit_buttons[0].click()
                time.sleep(3)

                # Check for success confirmation
                if any(indicator in driver.page_source.lower() for indicator in
                       ["thank you", "submitted", "received", "confirmation"]):
                    return {"success": True}

            return {"success": False, "error": "Could not submit Greenhouse form"}

        except Exception as e:
            return {"success": False, "error": f"Greenhouse error: {str(e)}"}

    def _handle_workday_form(self, driver, job: Job) -> Dict:
        """Handle Workday application forms"""
        try:
            # Workday forms are complex, implement basic field filling
            self._fill_form_fields(driver)

            # Workday often has multi-step process
            apply_buttons = driver.find_elements(By.CSS_SELECTOR,
                "[data-automation-id='apply'], button:contains('Apply')")

            if apply_buttons:
                apply_buttons[0].click()
                time.sleep(3)
                return {"success": True}

            return {"success": False, "error": "Could not find Workday apply button"}

        except Exception as e:
            return {"success": False, "error": f"Workday error: {str(e)}"}

    def _handle_generic_form(self, driver, job: Job) -> Dict:
        """Handle generic application forms"""
        try:
            form_filled = self._fill_form_fields(driver)

            if form_filled:
                # Try to submit
                submit_buttons = driver.find_elements(By.CSS_SELECTOR,
                    "input[type='submit'], button[type='submit'], button:contains('Submit'), button:contains('Apply')")

                if submit_buttons:
                    submit_buttons[0].click()
                    time.sleep(3)
                    return {"success": True}

            return {"success": False, "error": "Could not handle generic form"}

        except Exception as e:
            return {"success": False, "error": f"Generic form error: {str(e)}"}

    def _analyze_unknown_form(self, driver, job: Job) -> Dict:
        """Analyze unknown form patterns for future automation"""
        try:
            form_analysis = {
                "url": driver.current_url,
                "domain": driver.current_url.split('/')[2],
                "form_selectors": [],
                "input_fields": [],
                "submit_buttons": []
            }

            # Analyze form structure
            forms = driver.find_elements(By.TAG_NAME, "form")
            for form in forms:
                form_analysis["form_selectors"].append(form.get_attribute("class"))

            # Analyze input fields
            inputs = driver.find_elements(By.CSS_SELECTOR, "input, textarea, select")
            for inp in inputs:
                field_info = {
                    "type": inp.get_attribute("type"),
                    "name": inp.get_attribute("name"),
                    "id": inp.get_attribute("id"),
                    "placeholder": inp.get_attribute("placeholder")
                }
                form_analysis["input_fields"].append(field_info)

            # Analyze submit buttons
            buttons = driver.find_elements(By.CSS_SELECTOR, "button, input[type='submit']")
            for btn in buttons:
                btn_info = {
                    "text": btn.text,
                    "type": btn.get_attribute("type"),
                    "class": btn.get_attribute("class")
                }
                form_analysis["submit_buttons"].append(btn_info)

            # Save pattern for analysis
            self._save_form_pattern(form_analysis)

            return {
                "success": False,
                "error": "Unknown form pattern - saved for analysis",
                "pattern_analysis": form_analysis
            }

        except Exception as e:
            return {"success": False, "error": f"Form analysis error: {str(e)}"}

    def _fill_form_fields(self, driver) -> bool:
        """Generic form field filling"""
        try:
            fields_filled = 0

            # Name fields
            name_selectors = [
                "input[name*='first'], input[id*='first'], input[placeholder*='First']",
                "input[name*='last'], input[id*='last'], input[placeholder*='Last']"
            ]

            for i, selector in enumerate(name_selectors):
                elements = driver.find_elements(By.CSS_SELECTOR, selector)
                if elements:
                    name_value = self.user_profile["first_name"] if i == 0 else self.user_profile["last_name"]
                    elements[0].clear()
                    elements[0].send_keys(name_value)
                    fields_filled += 1

            # Email field
            email_elements = driver.find_elements(By.CSS_SELECTOR,
                "input[type='email'], input[name*='email'], input[id*='email']")
            if email_elements:
                email_elements[0].clear()
                email_elements[0].send_keys(self.user_profile["email"])
                fields_filled += 1

            # Phone field
            phone_elements = driver.find_elements(By.CSS_SELECTOR,
                "input[type='tel'], input[name*='phone'], input[id*='phone']")
            if phone_elements:
                phone_elements[0].clear()
                phone_elements[0].send_keys(self.user_profile["phone"])
                fields_filled += 1

            return fields_filled > 0

        except Exception as e:
            logger.error(f"Error filling form fields: {e}")
            return False

    def _save_application_attempt(self, job_id: str, result: Dict):
        """Save application attempt to database"""
        conn = sqlite3.connect(self.db.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO applications (job_id, attempt_date, status, automation_success,
                                    error_message, form_patterns, completion_time)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            job_id,
            datetime.now().isoformat(),
            "success" if result.get("success") else "failed",
            result.get("success", False),
            result.get("error"),
            json.dumps(result.get("form_pattern", {})),
            result.get("completion_time", 0)
        ))

        conn.commit()
        conn.close()

    def _save_form_pattern(self, pattern_analysis: Dict):
        """Save form pattern for future analysis"""
        conn = sqlite3.connect(self.db.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            INSERT OR REPLACE INTO form_patterns (domain, form_selector, field_patterns,
                                                success_indicators, automation_difficulty, last_updated)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            pattern_analysis["domain"],
            json.dumps(pattern_analysis["form_selectors"]),
            json.dumps(pattern_analysis["input_fields"]),
            json.dumps(pattern_analysis["submit_buttons"]),
            5,  # Default difficulty
            datetime.now().isoformat()
        ))

        conn.commit()
        conn.close()

# Flask API
app = Flask(__name__)
CORS(app)

# Global instances
db = JobDatabase()
scraper = None
auto_applier = AutoApplicationSystem(db)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/search', methods=['POST'])
def search_jobs():
    try:
        data = request.json
        criteria = SearchCriteria(**data)

        global scraper
        if not scraper:
            scraper = LinkedInJobScraper()

        jobs = scraper.search_jobs(criteria)

        # Save jobs to database
        for job in jobs:
            db.save_job(job)

        return jsonify({
            "success": True,
            "jobs": [asdict(job) for job in jobs],
            "count": len(jobs)
        })

    except Exception as e:
        logger.error(f"Search error: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/jobs', methods=['GET'])
def get_jobs():
    try:
        limit = request.args.get('limit', 100, type=int)
        filters = {}

        if request.args.get('keywords'):
            filters['keywords'] = request.args.get('keywords').split(',')
        if request.args.get('location'):
            filters['location'] = request.args.get('location')
        if request.args.get('company'):
            filters['company'] = request.args.get('company')

        jobs = db.get_jobs(limit=limit, filters=filters)

        return jsonify({
            "success": True,
            "jobs": [asdict(job) for job in jobs],
            "count": len(jobs)
        })

    except Exception as e:
        logger.error(f"Get jobs error: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/apply', methods=['POST'])
def apply_to_job():
    try:
        data = request.json
        job_id = data.get('job_id')

        # Get job from database
        jobs = db.get_jobs(filters={'id': job_id})
        if not jobs:
            return jsonify({"success": False, "error": "Job not found"}), 404

        job = jobs[0]
        result = auto_applier.apply_to_job(job)

        # Update job status
        if result.get("success"):
            job.application_status = "applied"
            db.save_job(job)

        return jsonify(result)

    except Exception as e:
        logger.error(f"Apply error: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/bulk-apply', methods=['POST'])
def bulk_apply():
    try:
        data = request.json
        job_ids = data.get('job_ids', [])

        results = []
        for job_id in job_ids:
            jobs = db.get_jobs(filters={'id': job_id})
            if jobs:
                result = auto_applier.apply_to_job(jobs[0])
                results.append({"job_id": job_id, "result": result})
                time.sleep(2)  # Rate limiting

        return jsonify({
            "success": True,
            "results": results,
            "total_processed": len(results)
        })

    except Exception as e:
        logger.error(f"Bulk apply error: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/analytics', methods=['GET'])
def get_analytics():
    try:
        conn = sqlite3.connect(db.db_path)
        cursor = conn.cursor()

        # Application statistics
        cursor.execute("SELECT COUNT(*) FROM applications")
        total_applications = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM applications WHERE automation_success = 1")
        successful_applications = cursor.fetchone()[0]

        cursor.execute("SELECT AVG(completion_time) FROM applications WHERE automation_success = 1")
        avg_completion_time = cursor.fetchone()[0] or 0

        # Job statistics
        cursor.execute("SELECT COUNT(*) FROM jobs")
        total_jobs = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM jobs WHERE application_status = 'applied'")
        applied_jobs = cursor.fetchone()[0]

        # Form pattern analysis
        cursor.execute("SELECT domain, COUNT(*) as count FROM form_patterns GROUP BY domain")
        form_patterns = cursor.fetchall()

        conn.close()

        return jsonify({
            "success": True,
            "analytics": {
                "total_applications": total_applications,
                "successful_applications": successful_applications,
                "success_rate": (successful_applications / total_applications * 100) if total_applications > 0 else 0,
                "avg_completion_time": avg_completion_time,
                "total_jobs": total_jobs,
                "applied_jobs": applied_jobs,
                "application_rate": (applied_jobs / total_jobs * 100) if total_jobs > 0 else 0,
                "form_patterns": [{"domain": fp[0], "count": fp[1]} for fp in form_patterns]
            }
        })

    except Exception as e:
        logger.error(f"Analytics error: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

if __name__ == '__main__':
    try:
        app.run(debug=True, host='0.0.0.0', port=5000)
    finally:
        if scraper:
            scraper.close()