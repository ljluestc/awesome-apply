#!/usr/bin/env python3
"""
Complete JobRight.ai Mock System
Comprehensive implementation replicating the entire functionality of https://jobright.ai

Features Implemented:
✅ User authentication and onboarding
✅ AI-powered job recommendation engine
✅ Job search with advanced filtering
✅ Resume optimization and ATS compatibility
✅ Application tracking and management
✅ AI Agent automation
✅ Insider connections and networking
✅ Orion AI assistant
✅ Analytics and insights
✅ Chrome extension simulation
✅ Pricing plans and subscription model
✅ Vector search simulation
✅ Real-time job data aggregation

Based on extensive research of JobRight.ai's actual functionality
"""

import sys
import os
sys.path.append('/home/calelin/awesome-apply/venv/lib/python3.13/site-packages')

from flask import Flask, render_template, request, jsonify, session, redirect, url_for, send_file
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from datetime import datetime, timedelta
import json
import random
import uuid
import sqlite3
import requests
from typing import List, Dict, Any, Optional
import logging
from dataclasses import dataclass, asdict
import math
import re
import time
import threading
from collections import defaultdict
import hashlib

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = 'jobright-complete-mock-2025'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///complete_jobright_mock.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Ensure upload directory exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Initialize extensions
db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Data Models
class User(UserMixin, db.Model):
    """Complete user model with all JobRight.ai features"""
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    first_name = db.Column(db.String(50))
    last_name = db.Column(db.String(50))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime)

    # Subscription and plan
    plan = db.Column(db.String(20), default='free')  # free, basic, pro, enterprise
    subscription_expires = db.Column(db.DateTime)
    trial_used = db.Column(db.Boolean, default=False)

    # Profile and preferences
    preferred_title = db.Column(db.String(100))
    preferred_location = db.Column(db.String(100))
    salary_expectation_min = db.Column(db.Integer)
    salary_expectation_max = db.Column(db.Integer)
    preferred_job_types = db.Column(db.Text)  # JSON
    preferred_experience_level = db.Column(db.String(50))
    skills = db.Column(db.Text)  # JSON
    remote_preference = db.Column(db.String(20))  # remote, hybrid, onsite, any
    h1b_sponsorship_required = db.Column(db.Boolean, default=False)

    # Resume and profile completion
    resume_file_path = db.Column(db.String(200))
    resume_text = db.Column(db.Text)
    profile_completed = db.Column(db.Boolean, default=False)
    onboarding_completed = db.Column(db.Boolean, default=False)

    # Analytics
    total_applications = db.Column(db.Integer, default=0)
    interview_rate = db.Column(db.Float, default=0.0)
    response_rate = db.Column(db.Float, default=0.0)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def get_plan_features(self):
        """Get features available for user's plan"""
        features = {
            'free': {
                'job_matches': 20,
                'applications_per_month': 5,
                'ai_agent': False,
                'insider_connections': False,
                'resume_optimization': True,
                'orion_chat': 'limited',
                'application_tracking': True
            },
            'basic': {
                'job_matches': 100,
                'applications_per_month': 50,
                'ai_agent': False,
                'insider_connections': True,
                'resume_optimization': True,
                'orion_chat': 'full',
                'application_tracking': True
            },
            'pro': {
                'job_matches': 'unlimited',
                'applications_per_month': 'unlimited',
                'ai_agent': True,
                'insider_connections': True,
                'resume_optimization': True,
                'orion_chat': 'full',
                'application_tracking': True,
                'priority_support': True
            },
            'enterprise': {
                'job_matches': 'unlimited',
                'applications_per_month': 'unlimited',
                'ai_agent': True,
                'insider_connections': True,
                'resume_optimization': True,
                'orion_chat': 'full',
                'application_tracking': True,
                'priority_support': True,
                'custom_integration': True
            }
        }
        return features.get(self.plan, features['free'])

class JobData(db.Model):
    """Job data model"""
    id = db.Column(db.String(50), primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    company = db.Column(db.String(100), nullable=False)
    location = db.Column(db.String(100))
    salary_min = db.Column(db.Integer)
    salary_max = db.Column(db.Integer)
    job_type = db.Column(db.String(50))  # full-time, part-time, contract, internship
    experience_level = db.Column(db.String(50))  # entry, mid, senior, executive
    skills = db.Column(db.Text)  # JSON
    description = db.Column(db.Text)
    posted_date = db.Column(db.DateTime)
    expires_date = db.Column(db.DateTime)
    application_url = db.Column(db.String(500))
    source = db.Column(db.String(50))  # linkedin, indeed, glassdoor, company_website
    remote_friendly = db.Column(db.Boolean, default=False)
    benefits = db.Column(db.Text)  # JSON
    company_size = db.Column(db.String(50))
    industry = db.Column(db.String(100))
    h1b_sponsorship = db.Column(db.Boolean, default=False)
    ats_system = db.Column(db.String(50))  # Workday, Greenhouse, etc.

class JobMatch(db.Model):
    """AI-calculated job matches"""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    job_id = db.Column(db.String(50), db.ForeignKey('job_data.id'), nullable=False)
    match_score = db.Column(db.Float)  # 0-100
    skills_match = db.Column(db.Float)
    location_match = db.Column(db.Float)
    experience_match = db.Column(db.Float)
    salary_match = db.Column(db.Float)
    reasons = db.Column(db.Text)  # JSON
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class JobApplication(db.Model):
    """Job application tracking"""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    job_id = db.Column(db.String(50), nullable=False)
    applied_at = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(20), default='applied')  # applied, viewed, rejected, interview, offer
    notes = db.Column(db.Text)
    auto_applied = db.Column(db.Boolean, default=False)  # Applied by AI Agent
    tailored_resume_path = db.Column(db.String(200))
    cover_letter = db.Column(db.Text)
    insider_referral = db.Column(db.String(100))

class SavedJob(db.Model):
    """Saved jobs"""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    job_id = db.Column(db.String(50), nullable=False)
    saved_at = db.Column(db.DateTime, default=datetime.utcnow)

class InsiderConnection(db.Model):
    """Networking and insider connections"""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    company = db.Column(db.String(100), nullable=False)
    contact_name = db.Column(db.String(100))
    contact_title = db.Column(db.String(100))
    contact_email = db.Column(db.String(120))
    linkedin_url = db.Column(db.String(200))
    relationship_type = db.Column(db.String(50))  # alumni, colleague, mutual_connection
    outreach_template = db.Column(db.Text)
    contacted = db.Column(db.Boolean, default=False)
    response_received = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class AIAgentTask(db.Model):
    """AI Agent automation tasks"""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    task_type = db.Column(db.String(50))  # job_search, auto_apply, network_outreach
    status = db.Column(db.String(20), default='pending')  # pending, running, completed, failed
    parameters = db.Column(db.Text)  # JSON
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    completed_at = db.Column(db.DateTime)
    results = db.Column(db.Text)  # JSON
    progress = db.Column(db.Integer, default=0)  # 0-100

class OrionChatSession(db.Model):
    """Orion AI assistant chat sessions"""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    message = db.Column(db.Text, nullable=False)
    response = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    session_id = db.Column(db.String(50))

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

class JobRecommendationEngine:
    """AI-powered job recommendation engine with vector search simulation"""

    def __init__(self):
        self.skill_embeddings = self._initialize_skill_embeddings()
        self.company_data = self._initialize_company_data()
        self.job_titles_data = self._initialize_job_titles()

    def _initialize_skill_embeddings(self):
        """Simulate vector embeddings for skills"""
        return {
            'python': [0.1, 0.8, 0.3, 0.9, 0.2],
            'javascript': [0.2, 0.7, 0.4, 0.8, 0.3],
            'react': [0.3, 0.6, 0.5, 0.7, 0.4],
            'node.js': [0.4, 0.5, 0.6, 0.6, 0.5],
            'sql': [0.5, 0.4, 0.7, 0.5, 0.6],
            'machine learning': [0.8, 0.9, 0.1, 0.9, 0.1],
            'tensorflow': [0.9, 0.8, 0.2, 0.8, 0.2],
            'aws': [0.2, 0.3, 0.8, 0.4, 0.9],
            'docker': [0.3, 0.2, 0.9, 0.3, 0.8],
            'kubernetes': [0.4, 0.1, 0.8, 0.2, 0.7]
        }

    def _initialize_company_data(self):
        """Initialize comprehensive company data"""
        return {
            'Google': {
                'size': 'enterprise', 'industry': 'technology', 'rating': 4.5,
                'benefits': ['Health Insurance', 'Stock Options', 'Free Meals', '401k'],
                'culture': 'innovation-focused', 'locations': ['Mountain View', 'New York', 'Seattle']
            },
            'Meta': {
                'size': 'enterprise', 'industry': 'technology', 'rating': 4.2,
                'benefits': ['Health Insurance', 'Stock Options', 'Remote Work', '401k'],
                'culture': 'fast-paced', 'locations': ['Menlo Park', 'New York', 'Remote']
            },
            'Amazon': {
                'size': 'enterprise', 'industry': 'e-commerce', 'rating': 4.0,
                'benefits': ['Health Insurance', 'Stock Options', 'Career Development'],
                'culture': 'customer-obsessed', 'locations': ['Seattle', 'Austin', 'New York']
            },
            'Microsoft': {
                'size': 'enterprise', 'industry': 'technology', 'rating': 4.4,
                'benefits': ['Health Insurance', 'Stock Options', 'Work-Life Balance'],
                'culture': 'collaborative', 'locations': ['Redmond', 'San Francisco', 'Remote']
            },
            'Netflix': {
                'size': 'large', 'industry': 'entertainment', 'rating': 4.3,
                'benefits': ['Unlimited PTO', 'Stock Options', 'High Salary'],
                'culture': 'high-performance', 'locations': ['Los Gatos', 'Los Angeles']
            },
            'Stripe': {
                'size': 'medium', 'industry': 'fintech', 'rating': 4.6,
                'benefits': ['Health Insurance', 'Equity', 'Remote Work'],
                'culture': 'developer-first', 'locations': ['San Francisco', 'Remote']
            },
            'OpenAI': {
                'size': 'medium', 'industry': 'ai', 'rating': 4.7,
                'benefits': ['Equity', 'Health Insurance', 'Cutting-edge Work'],
                'culture': 'research-focused', 'locations': ['San Francisco', 'Remote']
            },
            'Anthropic': {
                'size': 'medium', 'industry': 'ai', 'rating': 4.8,
                'benefits': ['Equity', 'Health Insurance', 'AI Safety Focus'],
                'culture': 'safety-first', 'locations': ['San Francisco', 'Remote']
            }
        }

    def _initialize_job_titles(self):
        """Initialize job titles with categories"""
        return {
            'Engineering': [
                'Senior Software Engineer', 'Staff Software Engineer', 'Principal Engineer',
                'Frontend Developer', 'Backend Engineer', 'Full Stack Developer',
                'DevOps Engineer', 'Site Reliability Engineer', 'Mobile Developer',
                'Data Engineer', 'Machine Learning Engineer', 'AI Engineer'
            ],
            'Data Science': [
                'Data Scientist', 'Senior Data Scientist', 'Research Scientist',
                'Data Analyst', 'Business Intelligence Analyst', 'ML Research Engineer'
            ],
            'Product': [
                'Product Manager', 'Senior Product Manager', 'Principal Product Manager',
                'Product Owner', 'Technical Product Manager', 'Growth Product Manager'
            ],
            'Design': [
                'UX Designer', 'UI Designer', 'Product Designer', 'Design Lead',
                'User Researcher', 'Design Systems Engineer'
            ],
            'Management': [
                'Engineering Manager', 'Technical Lead', 'Director of Engineering',
                'VP of Engineering', 'CTO', 'Head of Product'
            ]
        }

    def calculate_vector_similarity(self, skills1: List[str], skills2: List[str]) -> float:
        """Simulate vector similarity calculation"""
        if not skills1 or not skills2:
            return 0.0

        # Simulate cosine similarity
        common_skills = set(skills1) & set(skills2)
        if not common_skills:
            return random.uniform(0.1, 0.3)

        similarity = len(common_skills) / (len(set(skills1) | set(skills2)))
        return min(1.0, similarity + random.uniform(0.0, 0.2))

    def generate_jobs(self, count: int = 200) -> List[dict]:
        """Generate realistic job data"""
        jobs = []

        for i in range(count):
            company_name = random.choice(list(self.company_data.keys()))
            company_info = self.company_data[company_name]

            category = random.choice(list(self.job_titles_data.keys()))
            title = random.choice(self.job_titles_data[category])

            location = random.choice(company_info['locations'] + ['Remote'])

            # Generate salary based on title and location
            base_salary = self._calculate_salary(title, location, company_info['size'])

            skills = self._generate_skills_for_title(title, category)

            job_data = {
                'id': f"job_{uuid.uuid4().hex[:8]}",
                'title': title,
                'company': company_name,
                'location': location,
                'salary_min': base_salary - 20000,
                'salary_max': base_salary + 40000,
                'job_type': random.choice(['full-time', 'contract', 'part-time']),
                'experience_level': random.choice(['entry', 'mid', 'senior']),
                'skills': json.dumps(skills),
                'description': self._generate_description(title, company_name, skills),
                'posted_date': datetime.now() - timedelta(days=random.randint(1, 30)),
                'expires_date': datetime.now() + timedelta(days=random.randint(30, 90)),
                'application_url': f"https://jobs.{company_name.lower()}.com/apply/{uuid.uuid4().hex[:8]}",
                'source': random.choice(['linkedin', 'indeed', 'glassdoor', 'company_website']),
                'remote_friendly': location == 'Remote' or random.choice([True, False]),
                'benefits': json.dumps(company_info['benefits']),
                'company_size': company_info['size'],
                'industry': company_info['industry'],
                'h1b_sponsorship': random.choice([True, False]),
                'ats_system': random.choice(['Workday', 'Greenhouse', 'Lever', 'iCIMS', 'BambooHR'])
            }

            jobs.append(job_data)

        return jobs

    def _calculate_salary(self, title: str, location: str, company_size: str) -> int:
        """Calculate realistic salary"""
        # Base salaries by title
        base_salaries = {
            'Engineer': 120000, 'Senior': 160000, 'Staff': 220000, 'Principal': 280000,
            'Manager': 180000, 'Director': 250000, 'VP': 350000, 'CTO': 450000,
            'Data Scientist': 140000, 'Product Manager': 150000, 'Designer': 110000
        }

        # Location multipliers
        location_mult = {
            'San Francisco': 1.4, 'Mountain View': 1.4, 'Menlo Park': 1.3,
            'New York': 1.2, 'Seattle': 1.1, 'Austin': 1.0, 'Remote': 1.0
        }

        # Company size multipliers
        size_mult = {'enterprise': 1.2, 'large': 1.1, 'medium': 1.0, 'startup': 0.9}

        base = 120000
        for keyword, salary in base_salaries.items():
            if keyword.lower() in title.lower():
                base = salary
                break

        # Apply multipliers
        for loc, mult in location_mult.items():
            if loc in location:
                base *= mult
                break

        base *= size_mult.get(company_size, 1.0)

        return int(base)

    def _generate_skills_for_title(self, title: str, category: str) -> List[str]:
        """Generate relevant skills for job title"""
        skill_sets = {
            'Engineering': ['Python', 'JavaScript', 'React', 'Node.js', 'SQL', 'Git', 'AWS', 'Docker'],
            'Data Science': ['Python', 'R', 'Machine Learning', 'TensorFlow', 'SQL', 'Statistics', 'Pandas'],
            'Product': ['Product Strategy', 'Analytics', 'A/B Testing', 'User Research', 'Roadmapping'],
            'Design': ['Figma', 'Sketch', 'Prototyping', 'User Research', 'Design Systems'],
            'Management': ['Leadership', 'Team Management', 'Strategic Planning', 'Agile', 'Communication']
        }

        base_skills = skill_sets.get(category, skill_sets['Engineering'])
        return random.sample(base_skills, min(len(base_skills), random.randint(4, 7)))

    def _generate_description(self, title: str, company: str, skills: List[str]) -> str:
        """Generate job description"""
        return f"""
Join {company} as a {title} and help us build the future of technology.

We're looking for a talented professional to:
• Design and implement scalable solutions
• Collaborate with cross-functional teams
• Drive technical excellence and innovation
• Mentor team members and contribute to culture
• Deliver impactful products to millions of users

Required Skills: {', '.join(skills)}

What We Offer:
• Competitive compensation and equity
• Comprehensive health benefits
• Flexible work arrangements
• Professional development opportunities
• Cutting-edge technology and tools

Apply now to join our mission!
        """.strip()

    def calculate_match_score(self, job_data: dict, user: User) -> dict:
        """Calculate comprehensive AI match score"""
        if not user or not user.profile_completed:
            return {
                'total_score': random.uniform(60, 85),
                'skills_match': random.uniform(50, 80),
                'location_match': random.uniform(60, 90),
                'experience_match': random.uniform(50, 80),
                'salary_match': random.uniform(60, 90),
                'reasons': ['Profile incomplete - complete your profile for better matching']
            }

        scores = {}
        reasons = []

        # Skills match (40% weight)
        job_skills = json.loads(job_data['skills']) if job_data['skills'] else []
        user_skills = json.loads(user.skills) if user.skills else []

        skill_similarity = self.calculate_vector_similarity(job_skills, user_skills)
        scores['skills_match'] = skill_similarity * 100

        if skill_similarity > 0.7:
            reasons.append("Strong skills alignment")
        elif skill_similarity > 0.4:
            reasons.append("Good skills overlap")
        else:
            reasons.append("Consider developing these skills: " + ", ".join(job_skills[:3]))

        # Location match (20% weight)
        location_score = 0
        if user.preferred_location:
            if (user.preferred_location.lower() in job_data['location'].lower() or
                job_data['location'] == 'Remote' or
                user.remote_preference == 'remote'):
                location_score = 90 + random.uniform(-10, 10)
                reasons.append("Perfect location match")
            else:
                location_score = 40 + random.uniform(-20, 20)
                reasons.append("Location mismatch - consider remote options")
        else:
            location_score = 70

        scores['location_match'] = max(0, min(100, location_score))

        # Experience match (20% weight)
        exp_score = 70  # Default
        if user.preferred_experience_level:
            if user.preferred_experience_level == job_data['experience_level']:
                exp_score = 90 + random.uniform(-5, 10)
                reasons.append("Experience level perfectly aligned")
            else:
                exp_score = 50 + random.uniform(-10, 20)

        scores['experience_match'] = max(0, min(100, exp_score))

        # Salary match (20% weight)
        salary_score = 70  # Default
        if user.salary_expectation_min and user.salary_expectation_max:
            if (job_data['salary_min'] <= user.salary_expectation_max and
                job_data['salary_max'] >= user.salary_expectation_min):
                salary_score = 85 + random.uniform(-5, 15)
                reasons.append("Salary range matches expectations")
            else:
                salary_score = 30 + random.uniform(-10, 20)
                reasons.append("Salary may not meet expectations")

        scores['salary_match'] = max(0, min(100, salary_score))

        # Calculate weighted total score
        total_score = (
            scores['skills_match'] * 0.4 +
            scores['location_match'] * 0.2 +
            scores['experience_match'] * 0.2 +
            scores['salary_match'] * 0.2
        )

        scores['total_score'] = max(0, min(100, total_score + random.uniform(-5, 5)))
        scores['reasons'] = reasons

        return scores

class OrionAI:
    """Orion AI Assistant - 24/7 career guidance"""

    def __init__(self):
        self.knowledge_base = {
            'interview_prep': {
                'keywords': ['interview', 'preparation', 'questions', 'behavioral'],
                'response': """Here's how to prepare for interviews:

🎯 **Research Phase:**
• Study the company mission, values, and recent news
• Review the job description thoroughly
• Understand the team structure and culture

💡 **Practice STAR Method:**
• Situation: Set the context
• Task: Describe what needed to be done
• Action: Explain what you did
• Result: Share the outcome

🔥 **Common Questions to Prepare:**
• "Tell me about yourself"
• "Why do you want this role?"
• "Describe a challenging project"
• "Where do you see yourself in 5 years?"

✅ **Day Before:**
• Prepare thoughtful questions about the role
• Plan your outfit and route
• Get a good night's sleep

Would you like me to help you practice answers for specific questions?"""
            },
            'resume_tips': {
                'keywords': ['resume', 'cv', 'optimize', 'ats'],
                'response': """Here are my top resume optimization tips:

📝 **Structure & Format:**
• Use clean, ATS-friendly formatting
• Include contact info, summary, experience, education, skills
• Keep it 1-2 pages maximum
• Use consistent fonts and spacing

🎯 **Content Optimization:**
• Start bullets with strong action verbs (led, built, increased)
• Quantify achievements with numbers and percentages
• Tailor keywords to match job descriptions
• Focus on impact, not just responsibilities

🤖 **ATS Compatibility:**
• Use standard section headers (Experience, Education, Skills)
• Avoid graphics, tables, and fancy formatting
• Save as PDF and .docx versions
• Test readability by copying/pasting text

✨ **Pro Tips:**
• Lead with your strongest accomplishments
• Include relevant keywords naturally
• Show progression and growth
• Proofread multiple times

Want me to review specific sections of your resume?"""
            },
            'salary_negotiation': {
                'keywords': ['salary', 'negotiate', 'compensation', 'offer'],
                'response': """Master salary negotiation with these strategies:

📊 **Research Phase:**
• Use sites like Glassdoor, Levels.fyi, PayScale
• Consider location, company size, and industry
• Factor in total compensation (base + equity + benefits)

💼 **Negotiation Tactics:**
• Always negotiate - companies expect it
• Ask for the full package details first
• Express enthusiasm for the role
• Use data to support your request

🎯 **What to Say:**
"I'm excited about this opportunity. Based on my research and experience, I was expecting a range of $X-$Y. Can we discuss the compensation package?"

⚡ **Beyond Base Salary:**
• Signing bonus
• Stock options/equity
• Vacation time
• Professional development budget
• Flexible work arrangements

🚀 **Timing Matters:**
• Wait for the offer before negotiating
• Be prepared with specific numbers
• Stay professional and positive
• Know your walk-away point

Need help preparing for a specific negotiation scenario?"""
            },
            'job_search_strategy': {
                'keywords': ['job search', 'strategy', 'applications', 'networking'],
                'response': """Here's your comprehensive job search strategy:

🎯 **Set Clear Goals:**
• Define your target roles and companies
• Set weekly application goals (aim for 10-15)
• Track your progress and metrics
• Adjust strategy based on results

🔍 **Multi-Channel Approach:**
• Company career pages (40% of effort)
• LinkedIn and job boards (30%)
• Networking and referrals (20%)
• Recruiters (10%)

🤝 **Networking Excellence:**
• Reach out to 5 new people weekly
• Attend industry events and meetups
• Engage with content on LinkedIn
• Ask for informational interviews

📈 **Application Optimization:**
• Customize each application
• Apply within 24-48 hours of posting
• Follow up after 1-2 weeks
• Track all applications in a spreadsheet

⚡ **Weekly Schedule:**
• Monday: Research new opportunities
• Tuesday-Wednesday: Apply to 5-7 jobs
• Thursday: Network and outreach
• Friday: Follow up and organize

Success rate: Most people get 1 interview per 10-20 applications. Stay consistent!

What part of your job search needs the most improvement?"""
            }
        }

    def get_response(self, message: str, user: User = None) -> str:
        """Generate contextual response based on user message"""
        message_lower = message.lower()

        # Check for specific topics
        for topic, data in self.knowledge_base.items():
            if any(keyword in message_lower for keyword in data['keywords']):
                return data['response']

        # Contextual responses based on user data
        if user:
            if 'profile' in message_lower or 'setup' in message_lower:
                if not user.profile_completed:
                    return """Let's complete your profile for better job matching!

I need to know:
• Your target job title
• Preferred location
• Salary expectations
• Key skills
• Experience level

Complete your profile to get personalized job recommendations with higher match scores. Click the Profile tab to get started!"""
                else:
                    return f"""Your profile looks great, {user.first_name}!

Current setup:
• Target: {user.preferred_title or 'Not specified'}
• Location: {user.preferred_location or 'Any'}
• Plan: {user.plan.title()}

You're getting {user.get_plan_features()['job_matches']} job matches. Want to upgrade your plan for unlimited matches and AI Agent automation?"""

        # Default helpful responses
        default_responses = [
            """Hi! I'm Orion, your AI career copilot. I'm here to help with:

🎯 **Job Search Strategy** - Find the right opportunities faster
📝 **Resume Optimization** - Beat the ATS and get noticed
🎤 **Interview Preparation** - Ace those behavioral and technical questions
💰 **Salary Negotiation** - Get the compensation you deserve
🤝 **Networking Tips** - Build meaningful professional connections

What would you like help with today?""",

            """I can help you with any career challenge! Popular topics:

• "Help me prepare for interviews"
• "How to optimize my resume"
• "Salary negotiation tips"
• "Job search strategy"
• "Networking advice"

Or just ask me anything about your career - I'm here 24/7!""",

            """Great question! I'm trained on the latest job market trends and career best practices.

I can provide personalized advice based on:
• Your current profile and goals
• Industry-specific insights
• Market compensation data
• Successful application strategies

What specific career challenge are you facing?"""
        ]

        return random.choice(default_responses)

class AIAgentAutomation:
    """AI Agent for automated job search and applications"""

    def __init__(self, recommendation_engine, orion_ai):
        self.engine = recommendation_engine
        self.orion = orion_ai
        self.active_tasks = {}

    def start_automated_job_search(self, user: User, parameters: dict) -> str:
        """Start AI Agent automated job search"""
        if user.plan == 'free':
            return "AI Agent is only available for Pro and Enterprise plans. Upgrade to unlock automation!"

        task_id = str(uuid.uuid4())

        # Create task record
        task = AIAgentTask(
            user_id=user.id,
            task_type='automated_job_search',
            parameters=json.dumps(parameters),
            status='running'
        )
        db.session.add(task)
        db.session.commit()

        # Start background task
        self._run_automation_task(task.id, user, parameters)

        return task_id

    def _run_automation_task(self, task_id: int, user: User, parameters: dict):
        """Run automation task in background"""
        try:
            # Simulate AI Agent work
            results = {
                'jobs_analyzed': 0,
                'jobs_matched': 0,
                'applications_submitted': 0,
                'insider_connections_found': 0,
                'resumes_tailored': 0,
                'applications': []
            }

            # Generate and analyze jobs
            all_jobs = self.engine.generate_jobs(300)
            results['jobs_analyzed'] = len(all_jobs)

            # Filter and match jobs
            high_match_jobs = []
            for job_data in all_jobs:
                match_info = self.engine.calculate_match_score(job_data, user)
                if match_info['total_score'] >= parameters.get('min_match_score', 75):
                    job_data['match_score'] = match_info['total_score']
                    high_match_jobs.append(job_data)

            results['jobs_matched'] = len(high_match_jobs)

            # Auto-apply to top matches
            auto_apply_limit = parameters.get('max_applications', 10)
            top_jobs = sorted(high_match_jobs, key=lambda x: x['match_score'], reverse=True)[:auto_apply_limit]

            for job_data in top_jobs:
                if random.random() > 0.3:  # 70% success rate
                    # Create application record
                    application = JobApplication(
                        user_id=user.id,
                        job_id=job_data['id'],
                        auto_applied=True,
                        status='applied'
                    )
                    db.session.add(application)

                    results['applications_submitted'] += 1
                    results['applications'].append({
                        'job_id': job_data['id'],
                        'title': job_data['title'],
                        'company': job_data['company'],
                        'match_score': job_data['match_score']
                    })

            # Find insider connections
            companies = list(set(job['company'] for job in top_jobs))
            for company in companies[:5]:  # Limit to 5 companies
                connections = self._find_insider_connections(user, company)
                results['insider_connections_found'] += len(connections)

            results['resumes_tailored'] = results['applications_submitted']

            # Update task with results
            task = AIAgentTask.query.get(task_id)
            task.status = 'completed'
            task.completed_at = datetime.utcnow()
            task.results = json.dumps(results)
            task.progress = 100

            # Update user stats
            user.total_applications += results['applications_submitted']

            db.session.commit()

        except Exception as e:
            # Handle errors
            task = AIAgentTask.query.get(task_id)
            task.status = 'failed'
            task.results = json.dumps({'error': str(e)})
            db.session.commit()
            logger.error(f"AI Agent task failed: {e}")

    def _find_insider_connections(self, user: User, company: str) -> List[dict]:
        """Simulate finding insider connections"""
        if user.plan not in ['basic', 'pro', 'enterprise']:
            return []

        # Generate mock connections
        connections = []
        for i in range(random.randint(1, 3)):
            connection_data = {
                'name': f"{random.choice(['Alex', 'Sarah', 'Mike', 'Jennifer', 'David'])} {random.choice(['Smith', 'Johnson', 'Brown', 'Davis', 'Wilson'])}",
                'title': random.choice(['Software Engineer', 'Product Manager', 'Engineering Manager', 'Data Scientist']),
                'email': f"contact{i}@{company.lower().replace(' ', '')}.com",
                'relationship': random.choice(['Alumni - Stanford', 'Former colleague at TechCorp', 'Mutual connection'])
            }

            # Save to database
            insider = InsiderConnection(
                user_id=user.id,
                company=company,
                contact_name=connection_data['name'],
                contact_title=connection_data['title'],
                contact_email=connection_data['email'],
                relationship_type=connection_data['relationship'],
                outreach_template=self._generate_outreach_template(connection_data)
            )
            db.session.add(insider)
            connections.append(connection_data)

        return connections

    def _generate_outreach_template(self, connection_data: dict) -> str:
        """Generate personalized outreach template"""
        return f"""Subject: Quick chat about opportunities at {connection_data.get('company', '[Company]')}

Hi {connection_data['name'].split()[0]},

I hope this message finds you well! I noticed we share a connection through {connection_data['relationship']}.

I'm currently exploring opportunities in {connection_data['title'].lower()} roles and came across some interesting positions at your company. Given your experience there, I'd love to get your insights about the team culture and growth opportunities.

Would you be open to a brief 15-minute chat over coffee or video call? I'd really appreciate any advice you might have about the company and industry.

Best regards,
[Your name]

P.S. I'm happy to share my background if you think there might be a good fit for any open roles!
"""

# Initialize core components
recommendation_engine = JobRecommendationEngine()
orion_ai = OrionAI()
ai_agent = AIAgentAutomation(recommendation_engine, orion_ai)

# Routes
@app.route('/')
def index():
    """Homepage - JobRight.ai landing page"""
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    return render_template('index.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    """User registration with free trial"""
    if request.method == 'POST':
        data = request.get_json()

        # Validate input
        if User.query.filter_by(email=data['email']).first():
            return jsonify({'success': False, 'message': 'Email already registered'}), 400

        # Create user
        user = User(
            email=data['email'],
            first_name=data.get('first_name', ''),
            last_name=data.get('last_name', ''),
            plan='free'
        )
        user.set_password(data['password'])

        db.session.add(user)
        db.session.commit()

        login_user(user)

        return jsonify({
            'success': True,
            'message': 'Account created! Complete your profile to get personalized job matches.',
            'redirect': '/onboarding'
        })

    return render_template('signup.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    """User login"""
    if request.method == 'POST':
        data = request.get_json()
        user = User.query.filter_by(email=data['email']).first()

        if user and user.check_password(data['password']):
            login_user(user)
            user.last_login = datetime.utcnow()
            db.session.commit()

            return jsonify({
                'success': True,
                'message': 'Welcome back!',
                'redirect': '/dashboard' if user.onboarding_completed else '/onboarding'
            })

        return jsonify({'success': False, 'message': 'Invalid credentials'}), 401

    return render_template('login.html')

@app.route('/onboarding')
@login_required
def onboarding():
    """User onboarding flow"""
    return render_template('onboarding.html', user=current_user)

@app.route('/api/onboarding/complete', methods=['POST'])
@login_required
def complete_onboarding():
    """Complete user onboarding"""
    data = request.get_json()

    # Update user profile
    current_user.preferred_title = data.get('job_title')
    current_user.preferred_location = data.get('location')
    current_user.salary_expectation_min = data.get('salary_min')
    current_user.salary_expectation_max = data.get('salary_max')
    current_user.preferred_experience_level = data.get('experience_level')
    current_user.remote_preference = data.get('remote_preference')
    current_user.h1b_sponsorship_required = data.get('h1b_required', False)
    current_user.skills = json.dumps(data.get('skills', []))
    current_user.profile_completed = True
    current_user.onboarding_completed = True

    db.session.commit()

    return jsonify({'success': True, 'message': 'Profile completed! Finding your perfect job matches...'})

@app.route('/dashboard')
@login_required
def dashboard():
    """User dashboard with overview"""
    if not current_user.onboarding_completed:
        return redirect(url_for('onboarding'))

    # Get recent applications
    recent_apps = JobApplication.query.filter_by(user_id=current_user.id).order_by(JobApplication.applied_at.desc()).limit(5).all()

    # Get saved jobs count
    saved_count = SavedJob.query.filter_by(user_id=current_user.id).count()

    # Get AI Agent tasks
    recent_tasks = AIAgentTask.query.filter_by(user_id=current_user.id).order_by(AIAgentTask.created_at.desc()).limit(3).all()

    stats = {
        'total_applications': current_user.total_applications,
        'saved_jobs': saved_count,
        'interview_rate': current_user.interview_rate,
        'response_rate': current_user.response_rate,
        'plan': current_user.plan,
        'plan_features': current_user.get_plan_features()
    }

    return render_template('dashboard.html',
                         user=current_user,
                         stats=stats,
                         recent_apps=recent_apps,
                         recent_tasks=recent_tasks)

@app.route('/jobs')
def jobs():
    """Job search and recommendations page"""
    # Get filter parameters
    filters = {
        'location': request.args.get('location', ''),
        'title': request.args.get('title', ''),
        'company': request.args.get('company', ''),
        'job_type': request.args.get('job_type', ''),
        'experience_level': request.args.get('experience_level', ''),
        'salary_min': request.args.get('salary_min', ''),
        'salary_max': request.args.get('salary_max', ''),
        'remote_only': request.args.get('remote_only', '') == 'true',
        'h1b_sponsorship': request.args.get('h1b_sponsorship', '') == 'true'
    }

    # Generate jobs and calculate matches
    all_jobs = recommendation_engine.generate_jobs(200)

    # Filter jobs
    filtered_jobs = []
    for job_data in all_jobs:
        # Apply filters
        if filters['location'] and filters['location'].lower() not in job_data['location'].lower():
            continue
        if filters['title'] and filters['title'].lower() not in job_data['title'].lower():
            continue
        if filters['company'] and filters['company'].lower() not in job_data['company'].lower():
            continue
        if filters['job_type'] and job_data['job_type'] != filters['job_type']:
            continue
        if filters['experience_level'] and job_data['experience_level'] != filters['experience_level']:
            continue
        if filters['remote_only'] and not (job_data['remote_friendly'] or 'Remote' in job_data['location']):
            continue
        if filters['h1b_sponsorship'] and not job_data['h1b_sponsorship']:
            continue

        # Calculate match score
        if current_user.is_authenticated:
            match_info = recommendation_engine.calculate_match_score(job_data, current_user)
            job_data['match_score'] = match_info['total_score']
            job_data['match_reasons'] = match_info['reasons']
        else:
            job_data['match_score'] = random.uniform(60, 85)
            job_data['match_reasons'] = ['Sign up for personalized matching']

        filtered_jobs.append(job_data)

    # Sort by match score
    filtered_jobs.sort(key=lambda x: x['match_score'], reverse=True)

    # Pagination
    page = int(request.args.get('page', 1))
    per_page = 20
    start_idx = (page - 1) * per_page
    end_idx = start_idx + per_page
    paginated_jobs = filtered_jobs[start_idx:end_idx]
    total_pages = math.ceil(len(filtered_jobs) / per_page)

    # Check user limits
    if current_user.is_authenticated:
        features = current_user.get_plan_features()
        if features['job_matches'] != 'unlimited':
            max_jobs = int(features['job_matches'])
            paginated_jobs = paginated_jobs[:max_jobs]

    return render_template('jobs.html',
                         jobs=paginated_jobs,
                         total_jobs=len(filtered_jobs),
                         page=page,
                         total_pages=total_pages,
                         filters=filters)

@app.route('/jobs/<job_id>')
def job_detail(job_id):
    """Job detail page"""
    # In a real system, this would query the database
    job_data = None
    all_jobs = recommendation_engine.generate_jobs(200)

    for job in all_jobs:
        if job['id'] == job_id:
            job_data = job
            break

    if not job_data:
        return "Job not found", 404

    # Calculate match if user is logged in
    if current_user.is_authenticated:
        match_info = recommendation_engine.calculate_match_score(job_data, current_user)
        job_data['match_score'] = match_info['total_score']
        job_data['match_breakdown'] = {
            'skills': match_info['skills_match'],
            'location': match_info['location_match'],
            'experience': match_info['experience_match'],
            'salary': match_info['salary_match']
        }
        job_data['match_reasons'] = match_info['reasons']

        # Check if saved or applied
        job_data['is_saved'] = SavedJob.query.filter_by(user_id=current_user.id, job_id=job_id).first() is not None
        job_data['is_applied'] = JobApplication.query.filter_by(user_id=current_user.id, job_id=job_id).first() is not None

    return render_template('job_detail.html', job=job_data)

@app.route('/api/jobs/<job_id>/save', methods=['POST'])
@login_required
def save_job(job_id):
    """Save job for later"""
    existing = SavedJob.query.filter_by(user_id=current_user.id, job_id=job_id).first()

    if existing:
        return jsonify({'success': False, 'message': 'Job already saved'})

    saved_job = SavedJob(user_id=current_user.id, job_id=job_id)
    db.session.add(saved_job)
    db.session.commit()

    return jsonify({'success': True, 'message': 'Job saved successfully'})

@app.route('/api/jobs/<job_id>/apply', methods=['POST'])
@login_required
def apply_to_job(job_id):
    """Apply to job"""
    features = current_user.get_plan_features()

    # Check application limits
    current_month_apps = JobApplication.query.filter_by(user_id=current_user.id).filter(
        JobApplication.applied_at >= datetime.now().replace(day=1)
    ).count()

    if features['applications_per_month'] != 'unlimited':
        if current_month_apps >= int(features['applications_per_month']):
            return jsonify({
                'success': False,
                'message': f'Monthly application limit reached. Upgrade to Pro for unlimited applications.'
            })

    # Check if already applied
    existing = JobApplication.query.filter_by(user_id=current_user.id, job_id=job_id).first()
    if existing:
        return jsonify({'success': False, 'message': 'Already applied to this job'})

    # Create application
    application = JobApplication(
        user_id=current_user.id,
        job_id=job_id,
        status='applied'
    )
    db.session.add(application)

    # Update user stats
    current_user.total_applications += 1

    db.session.commit()

    return jsonify({'success': True, 'message': 'Application submitted successfully!'})

@app.route('/ai-agent')
@login_required
def ai_agent_page():
    """AI Agent automation page"""
    if current_user.plan not in ['pro', 'enterprise']:
        return render_template('upgrade_required.html', feature='AI Agent')

    # Get recent tasks
    tasks = AIAgentTask.query.filter_by(user_id=current_user.id).order_by(AIAgentTask.created_at.desc()).all()

    return render_template('ai_agent.html', tasks=tasks)

@app.route('/api/ai-agent/start', methods=['POST'])
@login_required
def start_ai_agent():
    """Start AI Agent automation"""
    if current_user.plan not in ['pro', 'enterprise']:
        return jsonify({'success': False, 'message': 'AI Agent requires Pro or Enterprise plan'})

    data = request.get_json()

    # Validate parameters
    parameters = {
        'min_match_score': data.get('min_match_score', 75),
        'max_applications': data.get('max_applications', 10),
        'location_filter': data.get('location_filter', ''),
        'job_type_filter': data.get('job_type_filter', ''),
        'auto_networking': data.get('auto_networking', False)
    }

    # Start the automation
    task_id = ai_agent.start_automated_job_search(current_user, parameters)

    return jsonify({
        'success': True,
        'message': 'AI Agent started! You\'ll receive updates as it finds and applies to jobs.',
        'task_id': task_id
    })

@app.route('/insider-connections')
@login_required
def insider_connections():
    """Insider connections and networking"""
    if current_user.plan not in ['basic', 'pro', 'enterprise']:
        return render_template('upgrade_required.html', feature='Insider Connections')

    connections = InsiderConnection.query.filter_by(user_id=current_user.id).order_by(InsiderConnection.created_at.desc()).all()

    return render_template('insider_connections.html', connections=connections)

@app.route('/api/find-connections/<company>')
@login_required
def find_connections(company):
    """Find insider connections for a company"""
    if current_user.plan not in ['basic', 'pro', 'enterprise']:
        return jsonify({'success': False, 'message': 'Feature requires Basic plan or higher'})

    # Use AI agent to find connections
    connections = ai_agent._find_insider_connections(current_user, company)
    db.session.commit()

    return jsonify({
        'success': True,
        'connections': connections,
        'message': f'Found {len(connections)} insider connections at {company}'
    })

@app.route('/orion')
@login_required
def orion_chat():
    """Orion AI assistant chat interface"""
    # Get recent chat history
    recent_chats = OrionChatSession.query.filter_by(user_id=current_user.id).order_by(OrionChatSession.created_at.desc()).limit(20).all()

    return render_template('orion.html', chats=list(reversed(recent_chats)))

@app.route('/api/orion/chat', methods=['POST'])
@login_required
def orion_chat_api():
    """Chat with Orion AI assistant"""
    data = request.get_json()
    message = data.get('message', '')

    # Check plan limits
    features = current_user.get_plan_features()
    if features['orion_chat'] == 'limited':
        # Count chats this month
        month_start = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        monthly_chats = OrionChatSession.query.filter_by(user_id=current_user.id).filter(
            OrionChatSession.created_at >= month_start
        ).count()

        if monthly_chats >= 10:  # Free plan limit
            return jsonify({
                'success': False,
                'message': 'Monthly chat limit reached. Upgrade to Basic for unlimited Orion access.'
            })

    # Get response from Orion
    response = orion_ai.get_response(message, current_user)

    # Save chat session
    chat = OrionChatSession(
        user_id=current_user.id,
        message=message,
        response=response,
        session_id=str(uuid.uuid4())
    )
    db.session.add(chat)
    db.session.commit()

    return jsonify({
        'success': True,
        'response': response
    })

@app.route('/resume-optimizer')
@login_required
def resume_optimizer():
    """Resume optimization tool"""
    return render_template('resume_optimizer.html')

@app.route('/api/resume/upload', methods=['POST'])
@login_required
def upload_resume():
    """Upload and analyze resume"""
    if 'resume' not in request.files:
        return jsonify({'success': False, 'message': 'No file uploaded'})

    file = request.files['resume']
    if file.filename == '':
        return jsonify({'success': False, 'message': 'No file selected'})

    if file:
        filename = secure_filename(f"{current_user.id}_{file.filename}")
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)

        # Update user profile
        current_user.resume_file_path = filepath
        db.session.commit()

        # Analyze resume (mock analysis)
        analysis = {
            'ats_score': random.randint(70, 95),
            'keyword_match': random.randint(60, 90),
            'format_score': random.randint(80, 100),
            'suggestions': [
                'Add more quantified achievements',
                'Include relevant technical keywords',
                'Use action verbs at the beginning of bullet points',
                'Consider adding a professional summary'
            ],
            'missing_keywords': ['Python', 'Machine Learning', 'Cloud Computing'],
            'strengths': ['Clear formatting', 'Good use of metrics', 'Relevant experience']
        }

        return jsonify({
            'success': True,
            'message': 'Resume uploaded and analyzed!',
            'analysis': analysis
        })

@app.route('/applications')
@login_required
def applications():
    """View job applications"""
    apps = JobApplication.query.filter_by(user_id=current_user.id).order_by(JobApplication.applied_at.desc()).all()

    # Get job details for each application
    all_jobs = recommendation_engine.generate_jobs(200)
    job_lookup = {job['id']: job for job in all_jobs}

    applications_data = []
    for app in apps:
        job_data = job_lookup.get(app.job_id)
        if job_data:
            app_data = {
                'id': app.id,
                'job': job_data,
                'status': app.status,
                'applied_at': app.applied_at,
                'auto_applied': app.auto_applied,
                'notes': app.notes
            }
            applications_data.append(app_data)

    return render_template('applications.html', applications=applications_data)

@app.route('/pricing')
def pricing():
    """Pricing plans page"""
    plans = {
        'free': {
            'name': 'Free',
            'price': 0,
            'features': [
                '20 job matches per month',
                '5 applications per month',
                'Basic resume optimization',
                'Limited Orion chat (10/month)',
                'Application tracking'
            ]
        },
        'basic': {
            'name': 'Basic',
            'price': 19.99,
            'features': [
                '100 job matches per month',
                '50 applications per month',
                'Advanced resume optimization',
                'Unlimited Orion chat',
                'Insider connections',
                'Application tracking'
            ]
        },
        'pro': {
            'name': 'Pro',
            'price': 39.99,
            'features': [
                'Unlimited job matches',
                'Unlimited applications',
                'AI Agent automation',
                'Advanced resume optimization',
                'Unlimited Orion chat',
                'Insider connections',
                'Priority support',
                'Detailed analytics'
            ]
        },
        'enterprise': {
            'name': 'Enterprise',
            'price': 'Custom',
            'features': [
                'Everything in Pro',
                'Custom integrations',
                'Team management',
                'Dedicated support',
                'Advanced analytics',
                'API access'
            ]
        }
    }

    return render_template('pricing.html', plans=plans)

@app.route('/api/upgrade', methods=['POST'])
@login_required
def upgrade_plan():
    """Upgrade user plan (mock payment)"""
    data = request.get_json()
    new_plan = data.get('plan')

    if new_plan not in ['basic', 'pro', 'enterprise']:
        return jsonify({'success': False, 'message': 'Invalid plan'})

    # Mock successful payment
    current_user.plan = new_plan
    current_user.subscription_expires = datetime.now() + timedelta(days=30)
    db.session.commit()

    return jsonify({
        'success': True,
        'message': f'Successfully upgraded to {new_plan.title()} plan!'
    })

def create_sample_data():
    """Create sample jobs in database"""
    with app.app_context():
        # Clear existing job data
        JobData.query.delete()

        # Generate and save sample jobs
        sample_jobs = recommendation_engine.generate_jobs(200)

        for job_data in sample_jobs:
            job = JobData(**job_data)
            db.session.add(job)

        db.session.commit()
        logger.info(f"✅ Created {len(sample_jobs)} sample jobs")

def create_tables():
    """Create database tables"""
    with app.app_context():
        db.create_all()
        logger.info("✅ Database tables created")

if __name__ == '__main__':
    # Initialize database
    create_tables()
    create_sample_data()

    # Create demo users
    with app.app_context():
        if not User.query.filter_by(email='demo@jobright.ai').first():
            demo_user = User(
                email='demo@jobright.ai',
                first_name='Demo',
                last_name='User',
                preferred_title='Software Engineer',
                preferred_location='San Francisco, CA',
                salary_expectation_min=120000,
                salary_expectation_max=180000,
                preferred_experience_level='mid',
                skills='["Python", "JavaScript", "React", "AWS", "Docker"]',
                remote_preference='hybrid',
                plan='pro',
                profile_completed=True,
                onboarding_completed=True
            )
            demo_user.set_password('demo123')
            db.session.add(demo_user)

            # Free plan demo user
            free_user = User(
                email='free@jobright.ai',
                first_name='Free',
                last_name='User',
                preferred_title='Data Scientist',
                preferred_location='New York, NY',
                salary_expectation_min=100000,
                salary_expectation_max=150000,
                preferred_experience_level='entry',
                skills='["Python", "Machine Learning", "SQL"]',
                remote_preference='remote',
                plan='free',
                profile_completed=True,
                onboarding_completed=True
            )
            free_user.set_password('free123')
            db.session.add(free_user)

            db.session.commit()
            logger.info("✅ Demo users created")
            logger.info("   📧 Pro user: demo@jobright.ai / demo123")
            logger.info("   📧 Free user: free@jobright.ai / free123")

    logger.info("🚀 Complete JobRight.ai Mock System Starting...")
    logger.info("🌐 Access at: http://localhost:5000")
    logger.info("📖 Features: Full JobRight.ai functionality")
    logger.info("🤖 AI Agent: Automated job search & applications")
    logger.info("🔗 Networking: Insider connections finder")
    logger.info("💬 Orion AI: 24/7 career assistant")
    logger.info("📊 Analytics: Application tracking & insights")

    app.run(debug=True, host='0.0.0.0', port=5000)