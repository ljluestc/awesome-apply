#!/usr/bin/env python3
"""
Complete Mock System for JobRight.ai Jobs Recommend Functionality

This system replicates the entire functionality of https://jobright.ai/jobs/recommend
including:
- Job recommendation engine with AI-powered matching
- User authentication and profile management
- Advanced filtering and search capabilities
- Real-time job data aggregation from multiple sources
- Application tracking and analytics
- Complete UI/UX with modern design
"""

import sys
sys.path.append('/home/calelin/awesome-apply/venv/lib/python3.13/site-packages')

from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
import json
import random
import uuid
import sqlite3
import requests
from typing import List, Dict, Any
import logging
from dataclasses import dataclass, asdict
import math
import re
from real_job_aggregator import RealJobAggregator, RealJob

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = 'jobright-mock-secret-key-2025'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///jobright_mock.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize extensions
db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Data Models
@dataclass
class JobData:
    """Job data structure matching JobRight.ai format"""
    id: str
    title: str
    company: str
    location: str
    salary_min: int
    salary_max: int
    job_type: str  # full-time, part-time, contract, internship
    experience_level: str  # entry, mid, senior, executive
    skills: List[str]
    description: str
    posted_date: datetime
    expires_date: datetime
    application_url: str
    source: str  # linkedin, indeed, glassdoor, company_website
    match_score: float  # AI-calculated match score 0-100
    remote_friendly: bool
    benefits: List[str]
    company_size: str  # startup, small, medium, large, enterprise
    industry: str

class User(UserMixin, db.Model):
    """User model for authentication and preferences"""
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    first_name = db.Column(db.String(50))
    last_name = db.Column(db.String(50))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime)

    # Profile preferences
    preferred_title = db.Column(db.String(100))
    preferred_location = db.Column(db.String(100))
    salary_expectation_min = db.Column(db.Integer)
    salary_expectation_max = db.Column(db.Integer)
    preferred_job_types = db.Column(db.String(200))  # JSON string
    preferred_experience_level = db.Column(db.String(50))
    skills = db.Column(db.Text)  # JSON string
    remote_preference = db.Column(db.String(20))  # remote, hybrid, onsite, any

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class JobApplication(db.Model):
    """Track user job applications"""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    job_id = db.Column(db.String(50), nullable=False)
    applied_at = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(20), default='applied')  # applied, viewed, rejected, interview, offer
    notes = db.Column(db.Text)

class SavedJob(db.Model):
    """Track user saved jobs"""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    job_id = db.Column(db.String(50), nullable=False)
    saved_at = db.Column(db.DateTime, default=datetime.utcnow)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

class JobRecommendationEngine:
    """AI-powered job recommendation engine with real job data"""

    def __init__(self):
        self.real_job_aggregator = RealJobAggregator()
        self.skill_keywords = {
            'software_engineer': ['python', 'javascript', 'react', 'node.js', 'sql', 'git', 'aws', 'docker'],
            'data_scientist': ['python', 'r', 'machine learning', 'tensorflow', 'pandas', 'sql', 'statistics'],
            'product_manager': ['agile', 'scrum', 'roadmap', 'analytics', 'stakeholder management', 'jira'],
            'designer': ['figma', 'sketch', 'adobe', 'ui/ux', 'prototyping', 'user research'],
            'marketing': ['seo', 'google analytics', 'social media', 'content marketing', 'email marketing'],
            'sales': ['crm', 'salesforce', 'lead generation', 'cold calling', 'negotiation']
        }

        self.company_data = {
            'google': {'size': 'enterprise', 'industry': 'technology', 'rating': 4.5},
            'meta': {'size': 'enterprise', 'industry': 'technology', 'rating': 4.2},
            'amazon': {'size': 'enterprise', 'industry': 'e-commerce', 'rating': 4.0},
            'microsoft': {'size': 'enterprise', 'industry': 'technology', 'rating': 4.4},
            'netflix': {'size': 'large', 'industry': 'entertainment', 'rating': 4.3},
            'uber': {'size': 'large', 'industry': 'transportation', 'rating': 3.8},
            'airbnb': {'size': 'large', 'industry': 'hospitality', 'rating': 4.1},
            'stripe': {'size': 'medium', 'industry': 'fintech', 'rating': 4.6},
            'openai': {'size': 'medium', 'industry': 'ai', 'rating': 4.7},
            'tesla': {'size': 'large', 'industry': 'automotive', 'rating': 3.9}
        }

    def get_real_jobs(self, count: int = 100) -> List[JobData]:
        """Get real job postings and convert to our JobData format"""
        real_jobs = self.real_job_aggregator.get_real_jobs(limit=count)

        # Convert RealJob objects to JobData objects
        converted_jobs = []
        for real_job in real_jobs:
            job_data = JobData(
                id=real_job.id,
                title=real_job.title,
                company=real_job.company,
                location=real_job.location,
                salary_min=real_job.salary_min or 80000,
                salary_max=real_job.salary_max or 120000,
                job_type=real_job.job_type,
                experience_level=real_job.experience_level,
                skills=real_job.skills,
                description=real_job.description,
                posted_date=real_job.posted_date,
                expires_date=real_job.expires_date,
                application_url=real_job.application_url,  # REAL APPLICATION URL
                source=real_job.source,
                match_score=real_job.match_score,
                remote_friendly=real_job.remote_friendly,
                benefits=real_job.benefits,
                company_size=real_job.company_size,
                industry=real_job.industry
            )
            converted_jobs.append(job_data)

        return converted_jobs

    def generate_mock_jobs(self, count: int = 100) -> List[JobData]:
        """Generate realistic mock job data (fallback)"""
        jobs = []

        job_titles = [
            'Senior Software Engineer', 'Data Scientist', 'Product Manager', 'UX Designer',
            'Frontend Developer', 'Backend Engineer', 'DevOps Engineer', 'Full Stack Developer',
            'Machine Learning Engineer', 'Mobile Developer', 'Technical Lead', 'Engineering Manager',
            'Data Analyst', 'Business Analyst', 'Quality Assurance Engineer', 'Site Reliability Engineer',
            'Security Engineer', 'Cloud Architect', 'Software Architect', 'Principal Engineer',
            'Marketing Manager', 'Sales Representative', 'Customer Success Manager', 'Operations Manager',
            'Financial Analyst', 'HR Business Partner', 'Recruiter', 'Technical Writer'
        ]

        locations = [
            'San Francisco, CA', 'New York, NY', 'Seattle, WA', 'Austin, TX', 'Boston, MA',
            'Los Angeles, CA', 'Chicago, IL', 'Denver, CO', 'Atlanta, GA', 'Remote',
            'San Jose, CA', 'Portland, OR', 'Miami, FL', 'Washington, DC', 'Dallas, TX'
        ]

        companies = list(self.company_data.keys())

        for i in range(count):
            company = random.choice(companies)
            title = random.choice(job_titles)
            location = random.choice(locations)

            # Generate realistic salary based on role and location
            base_salary = self._calculate_base_salary(title, location)
            salary_min = base_salary - 20000
            salary_max = base_salary + 30000

            # Generate skills based on job title
            skills = self._generate_skills_for_title(title)

            # Generate match score (would be calculated by AI in real system)
            match_score = random.uniform(60, 98)

            job = JobData(
                id=f"job_{uuid.uuid4().hex[:8]}",
                title=title,
                company=company.title(),
                location=location,
                salary_min=salary_min,
                salary_max=salary_max,
                job_type=random.choice(['full-time', 'part-time', 'contract']),
                experience_level=random.choice(['entry', 'mid', 'senior']),
                skills=skills,
                description=self._generate_job_description(title, company, skills),
                posted_date=datetime.now() - timedelta(days=random.randint(1, 30)),
                expires_date=datetime.now() + timedelta(days=random.randint(30, 90)),
                application_url=f"https://jobs.{company}.com/apply/{uuid.uuid4().hex[:8]}",
                source=random.choice(['linkedin', 'indeed', 'glassdoor', 'company_website']),
                match_score=match_score,
                remote_friendly=random.choice([True, False]),
                benefits=['Health Insurance', 'Dental', 'Vision', '401k', 'PTO', 'Stock Options'],
                company_size=self.company_data[company]['size'],
                industry=self.company_data[company]['industry']
            )
            jobs.append(job)

        return sorted(jobs, key=lambda x: x.match_score, reverse=True)

    def _calculate_base_salary(self, title: str, location: str) -> int:
        """Calculate base salary based on title and location"""
        title_multipliers = {
            'Senior': 1.4, 'Principal': 1.8, 'Staff': 1.6, 'Lead': 1.5, 'Manager': 1.3,
            'Director': 2.0, 'VP': 2.5, 'Engineer': 1.0, 'Developer': 1.0, 'Analyst': 0.8
        }

        location_multipliers = {
            'San Francisco': 1.5, 'New York': 1.3, 'Seattle': 1.2, 'San Jose': 1.4,
            'Boston': 1.1, 'Los Angeles': 1.1, 'Remote': 1.0, 'Austin': 0.9, 'Denver': 0.9
        }

        base = 100000  # Base software engineer salary

        # Apply title multiplier
        for keyword, multiplier in title_multipliers.items():
            if keyword.lower() in title.lower():
                base *= multiplier
                break

        # Apply location multiplier
        for loc, multiplier in location_multipliers.items():
            if loc in location:
                base *= multiplier
                break

        return int(base)

    def _generate_skills_for_title(self, title: str) -> List[str]:
        """Generate relevant skills for job title"""
        title_lower = title.lower()

        for category, skills in self.skill_keywords.items():
            if any(keyword in title_lower for keyword in category.split('_')):
                return random.sample(skills, min(len(skills), random.randint(3, 6)))

        # Default skills
        return random.sample(['communication', 'teamwork', 'problem solving', 'leadership'], 2)

    def _generate_job_description(self, title: str, company: str, skills: List[str]) -> str:
        """Generate realistic job description"""
        return f"""
We are seeking a talented {title} to join our team at {company.title()}.

Key Responsibilities:
• Design and implement scalable solutions
• Collaborate with cross-functional teams
• Drive technical decisions and architecture
• Mentor junior team members
• Deliver high-quality software products

Required Skills:
{', '.join(skills)}

What We Offer:
• Competitive salary and equity
• Comprehensive health benefits
• Flexible work arrangements
• Professional development opportunities
• Cutting-edge technology stack

Join us in building the future of technology!
        """.strip()

    def calculate_match_score(self, job: JobData, user: User) -> float:
        """Calculate AI-powered match score between job and user"""
        if not user:
            return random.uniform(60, 85)

        score = 0.0

        # Title match (30%)
        if user.preferred_title and user.preferred_title.lower() in job.title.lower():
            score += 30
        else:
            score += random.uniform(10, 25)

        # Location match (20%)
        if user.preferred_location:
            if user.preferred_location.lower() in job.location.lower() or job.location == 'Remote':
                score += 20
            else:
                score += random.uniform(5, 15)
        else:
            score += 15

        # Salary match (20%)
        if user.salary_expectation_min and user.salary_expectation_max:
            if job.salary_min >= user.salary_expectation_min:
                score += 20
            else:
                score += random.uniform(5, 15)
        else:
            score += 15

        # Skills match (20%)
        if user.skills:
            try:
                user_skills = json.loads(user.skills)
                skill_overlap = len(set(job.skills) & set(user_skills))
                score += min(20, skill_overlap * 5)
            except:
                score += 10
        else:
            score += 10

        # Experience level match (10%)
        if user.preferred_experience_level == job.experience_level:
            score += 10
        else:
            score += random.uniform(2, 8)

        return min(100, score + random.uniform(-5, 5))

    def filter_jobs(self, jobs: List[JobData], filters: Dict[str, Any]) -> List[JobData]:
        """Filter jobs based on user criteria"""
        filtered_jobs = jobs

        # Location filter
        if filters.get('location'):
            location = filters['location'].lower()
            filtered_jobs = [j for j in filtered_jobs if location in j.location.lower()]

        # Job type filter
        if filters.get('job_type'):
            job_type = filters['job_type']
            filtered_jobs = [j for j in filtered_jobs if j.job_type == job_type]

        # Experience level filter
        if filters.get('experience_level'):
            exp_level = filters['experience_level']
            filtered_jobs = [j for j in filtered_jobs if j.experience_level == exp_level]

        # Salary range filter
        if filters.get('salary_min'):
            salary_min = int(filters['salary_min'])
            filtered_jobs = [j for j in filtered_jobs if j.salary_max >= salary_min]

        if filters.get('salary_max'):
            salary_max = int(filters['salary_max'])
            filtered_jobs = [j for j in filtered_jobs if j.salary_min <= salary_max]

        # Remote work filter
        if filters.get('remote_only') == 'true':
            filtered_jobs = [j for j in filtered_jobs if j.remote_friendly or 'Remote' in j.location]

        # Company size filter
        if filters.get('company_size'):
            company_size = filters['company_size']
            filtered_jobs = [j for j in filtered_jobs if j.company_size == company_size]

        # Keywords search
        if filters.get('keywords'):
            keywords = filters['keywords'].lower()
            filtered_jobs = [
                j for j in filtered_jobs
                if keywords in j.title.lower() or
                   keywords in j.description.lower() or
                   any(keywords in skill.lower() for skill in j.skills)
            ]

        return filtered_jobs

# Initialize recommendation engine
recommendation_engine = JobRecommendationEngine()

# Routes
@app.route('/')
def index():
    """Home page - redirect to jobs/recommend"""
    return redirect(url_for('jobs_recommend'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    """User login"""
    if request.method == 'POST':
        data = request.get_json()
        email = data.get('email')
        password = data.get('password')

        user = User.query.filter_by(email=email).first()

        if user and user.check_password(password):
            login_user(user)
            user.last_login = datetime.utcnow()
            db.session.commit()
            return jsonify({'success': True, 'message': 'Login successful'})
        else:
            return jsonify({'success': False, 'message': 'Invalid credentials'}), 401

    return render_template('login.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    """User registration"""
    if request.method == 'POST':
        data = request.get_json()

        # Check if user exists
        if User.query.filter_by(email=data['email']).first():
            return jsonify({'success': False, 'message': 'Email already registered'}), 400

        # Create new user
        user = User(
            email=data['email'],
            first_name=data.get('first_name', ''),
            last_name=data.get('last_name', '')
        )
        user.set_password(data['password'])

        db.session.add(user)
        db.session.commit()

        login_user(user)
        return jsonify({'success': True, 'message': 'Account created successfully'})

    return render_template('signup.html')

@app.route('/logout')
@login_required
def logout():
    """User logout"""
    logout_user()
    return redirect(url_for('login'))

@app.route('/jobs/recommend')
def jobs_recommend():
    """Main job recommendations page with REAL job postings"""
    # Get REAL jobs first, fallback to mock if needed
    try:
        all_jobs = recommendation_engine.get_real_jobs(150)
        logger.info(f"✅ Loaded {len(all_jobs)} real jobs")
    except Exception as e:
        logger.warning(f"⚠️ Failed to load real jobs, using mock data: {e}")
        all_jobs = recommendation_engine.generate_mock_jobs(150)

    # Apply filters if any
    filters = {
        'location': request.args.get('location', ''),
        'job_type': request.args.get('job_type', ''),
        'experience_level': request.args.get('experience_level', ''),
        'salary_min': request.args.get('salary_min', ''),
        'salary_max': request.args.get('salary_max', ''),
        'remote_only': request.args.get('remote_only', ''),
        'company_size': request.args.get('company_size', ''),
        'keywords': request.args.get('keywords', '')
    }

    # Filter jobs based on criteria
    filtered_jobs = recommendation_engine.filter_jobs(all_jobs, filters)

    # Recalculate match scores for current user
    if current_user.is_authenticated:
        for job in filtered_jobs:
            job.match_score = recommendation_engine.calculate_match_score(job, current_user)

        # Re-sort by match score
        filtered_jobs.sort(key=lambda x: x.match_score, reverse=True)

    # Pagination
    page = int(request.args.get('page', 1))
    per_page = int(request.args.get('per_page', 20))
    start_idx = (page - 1) * per_page
    end_idx = start_idx + per_page

    paginated_jobs = filtered_jobs[start_idx:end_idx]
    total_pages = math.ceil(len(filtered_jobs) / per_page)

    # Get user's saved and applied jobs
    saved_job_ids = set()
    applied_job_ids = set()

    if current_user.is_authenticated:
        saved_jobs = SavedJob.query.filter_by(user_id=current_user.id).all()
        saved_job_ids = {job.job_id for job in saved_jobs}

        applied_jobs = JobApplication.query.filter_by(user_id=current_user.id).all()
        applied_job_ids = {job.job_id for job in applied_jobs}

    return render_template('jobs_recommend.html',
                         jobs=paginated_jobs,
                         total_jobs=len(filtered_jobs),
                         page=page,
                         total_pages=total_pages,
                         per_page=per_page,
                         filters=filters,
                         saved_job_ids=saved_job_ids,
                         applied_job_ids=applied_job_ids)

@app.route('/api/jobs/search')
def api_jobs_search():
    """API endpoint for job search with live filtering - REAL JOBS"""
    # Get filters from query parameters
    filters = {
        'location': request.args.get('location', ''),
        'job_type': request.args.get('job_type', ''),
        'experience_level': request.args.get('experience_level', ''),
        'salary_min': request.args.get('salary_min', ''),
        'salary_max': request.args.get('salary_max', ''),
        'remote_only': request.args.get('remote_only', ''),
        'company_size': request.args.get('company_size', ''),
        'keywords': request.args.get('keywords', '')
    }

    # Get REAL jobs and filter
    try:
        all_jobs = recommendation_engine.get_real_jobs(150)
    except Exception as e:
        logger.warning(f"⚠️ API: Failed to load real jobs: {e}")
        all_jobs = recommendation_engine.generate_mock_jobs(150)
    filtered_jobs = recommendation_engine.filter_jobs(all_jobs, filters)

    # Recalculate match scores for current user
    if current_user.is_authenticated:
        for job in filtered_jobs:
            job.match_score = recommendation_engine.calculate_match_score(job, current_user)
        filtered_jobs.sort(key=lambda x: x.match_score, reverse=True)

    # Pagination
    page = int(request.args.get('page', 1))
    per_page = int(request.args.get('per_page', 20))
    start_idx = (page - 1) * per_page
    end_idx = start_idx + per_page

    paginated_jobs = filtered_jobs[start_idx:end_idx]

    # Convert to JSON-serializable format
    jobs_data = []
    for job in paginated_jobs:
        job_dict = asdict(job)
        job_dict['posted_date'] = job.posted_date.isoformat()
        job_dict['expires_date'] = job.expires_date.isoformat()
        jobs_data.append(job_dict)

    return jsonify({
        'jobs': jobs_data,
        'total_jobs': len(filtered_jobs),
        'page': page,
        'total_pages': math.ceil(len(filtered_jobs) / per_page),
        'per_page': per_page
    })

@app.route('/api/jobs/<job_id>/save', methods=['POST'])
@login_required
def save_job(job_id):
    """Save a job for later"""
    # Check if already saved
    existing = SavedJob.query.filter_by(user_id=current_user.id, job_id=job_id).first()

    if existing:
        return jsonify({'success': False, 'message': 'Job already saved'})

    saved_job = SavedJob(user_id=current_user.id, job_id=job_id)
    db.session.add(saved_job)
    db.session.commit()

    return jsonify({'success': True, 'message': 'Job saved successfully'})

@app.route('/api/jobs/<job_id>/unsave', methods=['POST'])
@login_required
def unsave_job(job_id):
    """Remove a job from saved jobs"""
    saved_job = SavedJob.query.filter_by(user_id=current_user.id, job_id=job_id).first()

    if saved_job:
        db.session.delete(saved_job)
        db.session.commit()
        return jsonify({'success': True, 'message': 'Job removed from saved jobs'})

    return jsonify({'success': False, 'message': 'Job not found in saved jobs'})

@app.route('/api/jobs/<job_id>/apply', methods=['POST'])
@login_required
def apply_to_job(job_id):
    """Track job application"""
    # Check if already applied
    existing = JobApplication.query.filter_by(user_id=current_user.id, job_id=job_id).first()

    if existing:
        return jsonify({'success': False, 'message': 'Already applied to this job'})

    application = JobApplication(
        user_id=current_user.id,
        job_id=job_id,
        status='applied'
    )
    db.session.add(application)
    db.session.commit()

    return jsonify({'success': True, 'message': 'Application tracked successfully'})

@app.route('/profile')
@login_required
def profile():
    """User profile and preferences"""
    return render_template('profile.html', user=current_user)

@app.route('/api/profile/update', methods=['POST'])
@login_required
def update_profile():
    """Update user profile and preferences"""
    data = request.get_json()

    # Update user fields
    for field in ['preferred_title', 'preferred_location', 'salary_expectation_min',
                  'salary_expectation_max', 'preferred_experience_level', 'remote_preference']:
        if field in data:
            setattr(current_user, field, data[field])

    # Handle JSON fields
    if 'skills' in data:
        current_user.skills = json.dumps(data['skills'])

    if 'preferred_job_types' in data:
        current_user.preferred_job_types = json.dumps(data['preferred_job_types'])

    db.session.commit()

    return jsonify({'success': True, 'message': 'Profile updated successfully'})

@app.route('/saved-jobs')
@login_required
def saved_jobs():
    """View saved jobs - REAL JOBS"""
    saved_job_records = SavedJob.query.filter_by(user_id=current_user.id).all()
    saved_job_ids = [job.job_id for job in saved_job_records]

    # Get REAL job details
    try:
        all_jobs = recommendation_engine.get_real_jobs(150)
    except Exception as e:
        logger.warning(f"⚠️ Saved jobs: Failed to load real jobs: {e}")
        all_jobs = recommendation_engine.generate_mock_jobs(150)

    saved_jobs_data = [job for job in all_jobs if job.id in saved_job_ids]

    return render_template('saved_jobs.html', jobs=saved_jobs_data)

@app.route('/applications')
@login_required
def applications():
    """View job applications - REAL JOBS"""
    application_records = JobApplication.query.filter_by(user_id=current_user.id).all()

    # Get REAL job details with application status
    try:
        all_jobs = recommendation_engine.get_real_jobs(150)
    except Exception as e:
        logger.warning(f"⚠️ Applications: Failed to load real jobs: {e}")
        all_jobs = recommendation_engine.generate_mock_jobs(150)

    applications_data = []

    for app in application_records:
        job = next((j for j in all_jobs if j.id == app.job_id), None)
        if job:
            job_dict = asdict(job)
            job_dict['application_status'] = app.status
            job_dict['applied_at'] = app.applied_at
            job_dict['notes'] = app.notes
            applications_data.append(job_dict)

    return render_template('applications.html', applications=applications_data)

def create_tables():
    """Create database tables"""
    with app.app_context():
        db.create_all()
        logger.info("✅ Database tables created")

if __name__ == '__main__':
    # Create database tables
    create_tables()

    # Create demo user
    with app.app_context():
        if not User.query.filter_by(email='demo@jobright.mock').first():
            demo_user = User(
                email='demo@jobright.mock',
                first_name='Demo',
                last_name='User',
                preferred_title='Software Engineer',
                preferred_location='San Francisco, CA',
                salary_expectation_min=120000,
                salary_expectation_max=180000,
                preferred_experience_level='mid',
                skills='["python", "javascript", "react", "aws", "docker"]',
                remote_preference='hybrid'
            )
            demo_user.set_password('demo123')
            db.session.add(demo_user)
            db.session.commit()
            logger.info("✅ Demo user created: demo@jobright.mock / demo123")

    logger.info("🚀 JobRight.ai Mock System Starting...")
    logger.info("🌐 Access the application at: http://localhost:5000")
    logger.info("👤 Demo login: demo@jobright.mock / demo123")

    app.run(debug=True, host='0.0.0.0', port=5000)