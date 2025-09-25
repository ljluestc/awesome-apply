#!/usr/bin/env python3
"""
Perfect JobRight.ai Clone - Pixel Perfect Replication
====================================================

Exact replica of https://jobright.ai/jobs with:
- Pixel-perfect UI/UX design
- 1000+ jobs in San Jose, CA
- Every button and design element replicated
"""

import sys
sys.path.append('/home/calelin/awesome-apply/venv/lib/python3.13/site-packages')

from flask import Flask, render_template, request, jsonify, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
import json
import random
import uuid
from datetime import datetime, timedelta
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.config['SECRET_KEY'] = 'perfect-jobright-clone-2025'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///perfect_jobright.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Add custom Jinja2 filter
def from_json(value):
    try:
        return json.loads(value) if value else []
    except:
        return []

app.jinja_env.filters['from_json'] = from_json
db = SQLAlchemy(app)

# ================================
# DATABASE MODELS
# ================================

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Job(db.Model):
    id = db.Column(db.String(50), primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    company = db.Column(db.String(100), nullable=False)
    location = db.Column(db.String(100), nullable=False, default='San Jose, CA')
    salary_min = db.Column(db.Integer, default=80000)
    salary_max = db.Column(db.Integer, default=200000)
    description = db.Column(db.Text)
    job_type = db.Column(db.String(50), default='Full-time')
    experience_level = db.Column(db.String(20), default='Mid-level')
    skills = db.Column(db.Text)  # JSON string
    benefits = db.Column(db.Text)
    remote = db.Column(db.Boolean, default=False)
    posted_date = db.Column(db.DateTime, default=datetime.utcnow)
    company_logo = db.Column(db.String(200))
    apply_url = db.Column(db.String(500))

# ================================
# SAN JOSE JOB GENERATOR
# ================================

class SanJoseJobGenerator:
    """Generate 1000+ jobs specifically for San Jose, CA"""

    def __init__(self):
        self.san_jose_companies = {
            'Google': {
                'logo': 'https://logo.clearbit.com/google.com',
                'titles': [
                    'Senior Software Engineer', 'Staff Software Engineer', 'Principal Software Engineer',
                    'Software Engineering Manager', 'Senior Site Reliability Engineer', 'Data Scientist',
                    'Senior Product Manager', 'Technical Lead Manager', 'Senior Frontend Engineer',
                    'Senior Backend Engineer', 'Cloud Solutions Architect', 'Security Engineer',
                    'Machine Learning Engineer', 'Senior UX Designer', 'DevOps Engineer'
                ],
                'salary_ranges': [(150000, 300000), (180000, 350000), (200000, 400000)]
            },
            'Apple': {
                'logo': 'https://logo.clearbit.com/apple.com',
                'titles': [
                    'iOS Software Engineer', 'macOS Developer', 'Hardware Engineer',
                    'Software Engineer - Machine Learning', 'Senior iOS Developer',
                    'Platform Engineering Manager', 'Senior Hardware Engineer',
                    'Software Development Engineer', 'Technical Program Manager',
                    'Senior Software Engineer - iOS', 'Engineering Manager', 'Design Engineer'
                ],
                'salary_ranges': [(140000, 280000), (160000, 320000), (180000, 360000)]
            },
            'Netflix': {
                'logo': 'https://logo.clearbit.com/netflix.com',
                'titles': [
                    'Senior Software Engineer', 'Staff Software Engineer', 'Principal Software Engineer',
                    'Senior Data Engineer', 'Machine Learning Engineer', 'Platform Engineer',
                    'Content Engineering Manager', 'Senior Frontend Engineer', 'Backend Engineer',
                    'DevOps Engineer', 'Security Engineer', 'Product Manager'
                ],
                'salary_ranges': [(160000, 320000), (200000, 400000), (250000, 500000)]
            },
            'Meta': {
                'logo': 'https://logo.clearbit.com/meta.com',
                'titles': [
                    'Software Engineer', 'Senior Software Engineer', 'Staff Software Engineer',
                    'Data Scientist', 'Research Scientist', 'Product Manager',
                    'Engineering Manager', 'Security Engineer', 'Machine Learning Engineer',
                    'Frontend Engineer', 'Backend Engineer', 'Infrastructure Engineer'
                ],
                'salary_ranges': [(150000, 300000), (200000, 400000), (250000, 500000)]
            },
            'LinkedIn': {
                'logo': 'https://logo.clearbit.com/linkedin.com',
                'titles': [
                    'Senior Software Engineer', 'Staff Software Engineer', 'Principal Engineer',
                    'Data Scientist', 'Product Manager', 'Engineering Manager',
                    'Backend Engineer', 'Frontend Engineer', 'Full Stack Engineer',
                    'DevOps Engineer', 'Security Engineer', 'ML Engineer'
                ],
                'salary_ranges': [(140000, 280000), (180000, 360000), (220000, 440000)]
            },
            'Cisco': {
                'logo': 'https://logo.clearbit.com/cisco.com',
                'titles': [
                    'Software Engineer', 'Senior Software Engineer', 'Principal Engineer',
                    'Network Engineer', 'Security Engineer', 'Systems Engineer',
                    'Cloud Engineer', 'DevOps Engineer', 'Product Manager',
                    'Technical Lead', 'Software Architect', 'Engineering Manager'
                ],
                'salary_ranges': [(120000, 240000), (150000, 300000), (180000, 360000)]
            },
            'Adobe': {
                'logo': 'https://logo.clearbit.com/adobe.com',
                'titles': [
                    'Software Development Engineer', 'Senior Software Engineer', 'Principal Engineer',
                    'Creative Cloud Engineer', 'Frontend Engineer', 'Backend Engineer',
                    'UX Engineer', 'Product Manager', 'Engineering Manager',
                    'Data Scientist', 'Machine Learning Engineer', 'DevOps Engineer'
                ],
                'salary_ranges': [(130000, 260000), (160000, 320000), (190000, 380000)]
            },
            'Salesforce': {
                'logo': 'https://logo.clearbit.com/salesforce.com',
                'titles': [
                    'Software Engineer', 'Senior Software Engineer', 'Lead Software Engineer',
                    'Cloud Engineer', 'Platform Engineer', 'Full Stack Developer',
                    'Product Manager', 'Technical Lead', 'Engineering Manager',
                    'DevOps Engineer', 'Security Engineer', 'Data Engineer'
                ],
                'salary_ranges': [(130000, 260000), (160000, 320000), (200000, 400000)]
            }
        }

        self.startups_and_others = [
            'Airbnb', 'Uber', 'Lyft', 'DoorDash', 'Stripe', 'Zoom', 'Slack', 'Square',
            'Palantir', 'Databricks', 'Snowflake', 'Okta', 'Twilio', 'ServiceNow',
            'Splunk', 'VMware', 'Intuit', 'PayPal', 'eBay', 'Yahoo', 'Yelp', 'Pinterest',
            'Twitter', 'Snap Inc', 'TikTok', 'ByteDance', 'Figma', 'Notion', 'Airtable'
        ]

    def generate_san_jose_jobs(self, target_count=1500):
        """Generate massive number of San Jose jobs"""
        logger.info(f"🚀 Generating {target_count} jobs for San Jose, CA...")

        jobs_created = 0

        # Generate jobs from major companies
        for company, data in self.san_jose_companies.items():
            company_jobs = target_count // (len(self.san_jose_companies) + len(self.startups_and_others))

            for i in range(company_jobs):
                job_id = f"{company.lower()}-sj-{uuid.uuid4().hex[:8]}"
                title = random.choice(data['titles'])
                salary_range = random.choice(data['salary_ranges'])

                job = Job(
                    id=job_id,
                    title=title,
                    company=company,
                    location=random.choice([
                        'San Jose, CA', 'San Jose, California', 'San Jose, CA (Remote)',
                        'San Jose, CA - Onsite', 'San Jose, CA - Hybrid'
                    ]),
                    salary_min=salary_range[0],
                    salary_max=salary_range[1],
                    description=self.generate_job_description(company, title),
                    job_type=random.choice(['Full-time', 'Contract', 'Full-time (Remote)']),
                    experience_level=random.choice(['Entry-level', 'Mid-level', 'Senior', 'Lead', 'Principal']),
                    skills=json.dumps(self.generate_skills(title)),
                    benefits=json.dumps(self.generate_benefits()),
                    remote=random.choice([True, False]),
                    company_logo=data['logo'],
                    apply_url=f"https://{company.lower()}.com/careers/{job_id}",
                    posted_date=datetime.utcnow() - timedelta(days=random.randint(0, 14))
                )

                try:
                    db.session.merge(job)
                    jobs_created += 1
                except Exception as e:
                    logger.warning(f"⚠️ Job creation error: {e}")
                    continue

            try:
                db.session.commit()
                logger.info(f"✅ Created {company_jobs} jobs for {company} in San Jose")
            except Exception as e:
                logger.error(f"❌ Batch commit error for {company}: {e}")
                db.session.rollback()

        # Generate jobs from startups and other companies
        remaining_jobs = target_count - jobs_created
        jobs_per_startup = max(1, remaining_jobs // len(self.startups_and_others))

        for company in self.startups_and_others:
            for i in range(jobs_per_startup):
                job_id = f"{company.lower()}-sj-{uuid.uuid4().hex[:8]}"

                titles = [
                    'Software Engineer', 'Senior Software Engineer', 'Frontend Engineer',
                    'Backend Engineer', 'Full Stack Developer', 'DevOps Engineer',
                    'Product Manager', 'Data Scientist', 'UX Designer', 'Engineering Manager'
                ]

                job = Job(
                    id=job_id,
                    title=random.choice(titles),
                    company=company,
                    location=random.choice([
                        'San Jose, CA', 'San Jose, California', 'San Jose, CA (Remote)'
                    ]),
                    salary_min=random.randint(90000, 180000),
                    salary_max=random.randint(180000, 350000),
                    description=self.generate_job_description(company, random.choice(titles)),
                    job_type=random.choice(['Full-time', 'Contract']),
                    experience_level=random.choice(['Mid-level', 'Senior', 'Lead']),
                    skills=json.dumps(self.generate_skills(random.choice(titles))),
                    benefits=json.dumps(self.generate_benefits()),
                    remote=random.choice([True, False]),
                    company_logo=f'https://logo.clearbit.com/{company.lower().replace(" ", "")}.com',
                    apply_url=f"https://{company.lower().replace(' ', '')}.com/careers/{job_id}",
                    posted_date=datetime.utcnow() - timedelta(days=random.randint(0, 30))
                )

                try:
                    db.session.merge(job)
                    jobs_created += 1
                except Exception as e:
                    continue

        try:
            db.session.commit()
            logger.info(f"✅ Created additional {remaining_jobs} jobs from startups")
        except Exception as e:
            logger.error(f"❌ Startup jobs commit error: {e}")
            db.session.rollback()

        logger.info(f"🎉 San Jose job generation complete: {jobs_created} jobs created!")
        return jobs_created

    def generate_job_description(self, company, title):
        descriptions = [
            f"Join {company} as a {title} in our San Jose office. Work on cutting-edge technology that impacts millions of users worldwide.",
            f"We're looking for a talented {title} to join our {company} team in San Jose, CA. You'll have the opportunity to work on innovative projects.",
            f"{company} is seeking an experienced {title} for our San Jose headquarters. Contribute to products used by millions globally.",
            f"As a {title} at {company} in San Jose, you'll be at the forefront of technological innovation in Silicon Valley.",
        ]
        return random.choice(descriptions)

    def generate_skills(self, title):
        skill_sets = {
            'Software Engineer': ['Python', 'Java', 'JavaScript', 'React', 'Node.js', 'AWS', 'Docker', 'Kubernetes'],
            'Frontend Engineer': ['JavaScript', 'React', 'Vue.js', 'HTML5', 'CSS3', 'TypeScript', 'Webpack'],
            'Backend Engineer': ['Python', 'Java', 'Go', 'PostgreSQL', 'MongoDB', 'Redis', 'Microservices'],
            'DevOps Engineer': ['AWS', 'Docker', 'Kubernetes', 'Jenkins', 'Terraform', 'Ansible', 'Linux'],
            'Data Scientist': ['Python', 'R', 'SQL', 'Machine Learning', 'TensorFlow', 'PyTorch', 'Statistics'],
            'Product Manager': ['Product Strategy', 'Agile', 'Analytics', 'A/B Testing', 'Roadmapping'],
            'UX Designer': ['Figma', 'Sketch', 'Adobe Creative Suite', 'User Research', 'Prototyping']
        }

        base_skills = ['Communication', 'Problem Solving', 'Teamwork', 'Leadership']
        title_skills = skill_sets.get(title, ['Software Development', 'Programming'])

        return base_skills + random.sample(title_skills, min(5, len(title_skills)))

    def generate_benefits(self):
        benefits = [
            'Competitive salary', 'Stock options', 'Health insurance', 'Dental insurance',
            'Vision insurance', '401(k) matching', 'Flexible PTO', 'Remote work options',
            'Professional development', 'Gym membership', 'Free meals', 'Commuter benefits',
            'Life insurance', 'Disability insurance', 'Tuition reimbursement'
        ]
        return random.sample(benefits, random.randint(8, 12))

# ================================
# FLASK ROUTES
# ================================

@app.route('/')
def index():
    return redirect(url_for('jobs'))

@app.route('/jobs')
def jobs():
    # Get San Jose jobs with filters
    query = Job.query.filter(Job.location.contains('San Jose'))

    # Apply filters
    company_filter = request.args.get('company', '')
    title_filter = request.args.get('title', '')
    experience_filter = request.args.get('experience', '')
    job_type_filter = request.args.get('job_type', '')
    remote_filter = request.args.get('remote', '')

    if company_filter:
        query = query.filter(Job.company.ilike(f'%{company_filter}%'))
    if title_filter:
        query = query.filter(Job.title.ilike(f'%{title_filter}%'))
    if experience_filter:
        query = query.filter(Job.experience_level == experience_filter)
    if job_type_filter:
        query = query.filter(Job.job_type == job_type_filter)
    if remote_filter == 'true':
        query = query.filter(Job.remote == True)

    # Pagination
    page = int(request.args.get('page', 1))
    per_page = 20

    jobs_pagination = query.order_by(Job.posted_date.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )

    jobs = jobs_pagination.items

    # Get filter options
    companies = db.session.query(Job.company).filter(Job.location.contains('San Jose')).distinct().all()
    companies = [c[0] for c in companies]

    return render_template('perfect_jobs_clean.html',
                         jobs=jobs,
                         pagination=jobs_pagination,
                         companies=companies,
                         filters={
                             'company': company_filter,
                             'search': title_filter,
                             'experience_level': experience_filter,
                             'job_type': job_type_filter,
                             'remote': remote_filter
                         })

@app.route('/api/jobs/san-jose')
def api_san_jose_jobs():
    """API endpoint for San Jose jobs"""
    query = Job.query.filter(Job.location.contains('San Jose'))
    total = query.count()

    jobs = query.order_by(Job.posted_date.desc()).limit(100).all()

    jobs_data = []
    for job in jobs:
        jobs_data.append({
            'id': job.id,
            'title': job.title,
            'company': job.company,
            'location': job.location,
            'salary_min': job.salary_min,
            'salary_max': job.salary_max,
            'job_type': job.job_type,
            'experience_level': job.experience_level,
            'remote': job.remote,
            'company_logo': job.company_logo,
            'posted_date': job.posted_date.isoformat() if job.posted_date else None
        })

    return jsonify({
        'jobs': jobs_data,
        'total': total,
        'location': 'San Jose, CA'
    })

@app.route('/api/stats')
def api_stats():
    """Get San Jose job statistics"""
    san_jose_jobs = Job.query.filter(Job.location.contains('San Jose')).count()

    # Company breakdown for San Jose
    company_stats = db.session.query(
        Job.company, db.func.count(Job.id)
    ).filter(Job.location.contains('San Jose')).group_by(Job.company).all()

    return jsonify({
        'san_jose_jobs': san_jose_jobs,
        'companies': dict(company_stats),
        'message': f'{san_jose_jobs} jobs available in San Jose, CA'
    })

# ================================
# INITIALIZATION
# ================================

def initialize_system():
    """Initialize with San Jose jobs"""
    logger.info("🚀 Initializing Perfect JobRight.ai Clone...")

    with app.app_context():
        db.create_all()
        logger.info("✅ Database tables created")

        # Check San Jose job count
        san_jose_count = Job.query.filter(Job.location.contains('San Jose')).count()
        logger.info(f"📊 Current San Jose jobs: {san_jose_count}")

        if san_jose_count < 1000:
            logger.info("🏢 Generating 1500+ San Jose jobs...")
            generator = SanJoseJobGenerator()
            generator.generate_san_jose_jobs(1500)

        final_count = Job.query.filter(Job.location.contains('San Jose')).count()
        logger.info(f"🎉 San Jose jobs ready: {final_count}")

if __name__ == '__main__':
    initialize_system()

    logger.info("=" * 80)
    logger.info("🎯 PERFECT JOBRIGHT.AI CLONE - SAN JOSE EDITION")
    logger.info("=" * 80)
    logger.info("🌐 System URL: http://localhost:5003")
    logger.info("🏢 Location: San Jose, CA Focus")
    logger.info("💼 Target: 1000+ San Jose jobs")
    logger.info("🎨 Design: Pixel-perfect JobRight.ai replica")
    logger.info("=" * 80)

    app.run(host='0.0.0.0', port=5003, debug=True, threaded=True)