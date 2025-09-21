#!/usr/bin/env python3
"""
Configuration file for JobRight.ai Clone
"""

import os
from dataclasses import dataclass
from typing import Dict, Any

@dataclass
class UserProfile:
    """User profile for auto-fill functionality"""
    first_name: str = "John"
    last_name: str = "Doe"
    email: str = "john.doe@email.com"
    phone: str = "(555) 123-4567"
    linkedin_url: str = "https://linkedin.com/in/johndoe"
    github_url: str = "https://github.com/johndoe"
    website: str = "https://johndoe.com"
    resume_path: str = "/path/to/resume.pdf"
    cover_letter_template: str = """Dear Hiring Manager,

I am excited to apply for the {job_title} position at {company}. With my background in {relevant_skills}, I believe I would be a valuable addition to your team.

{custom_message}

I look forward to discussing how my experience can contribute to {company}'s success.

Best regards,
{first_name} {last_name}"""

    # Skills and preferences
    skills: list = None
    preferred_locations: list = None
    salary_range: Dict[str, int] = None
    work_authorization: str = "US Citizen"
    willing_to_relocate: bool = False
    remote_preference: str = "hybrid"  # remote, onsite, hybrid, any

    def __post_init__(self):
        if self.skills is None:
            self.skills = [
                "Python", "JavaScript", "React", "Node.js",
                "SQL", "Git", "AWS", "Docker"
            ]
        if self.preferred_locations is None:
            self.preferred_locations = [
                "San Francisco, CA", "New York, NY", "Seattle, WA", "Remote"
            ]
        if self.salary_range is None:
            self.salary_range = {"min": 80000, "max": 150000}

class AppConfig:
    """Application configuration"""

    # Database settings
    DATABASE_PATH = "jobright_clone.db"

    # Web scraping settings
    SCRAPING_DELAY = 2  # seconds between requests
    MAX_PAGES_PER_SEARCH = 5
    MAX_JOBS_PER_SEARCH = 100

    # Auto-application settings
    APPLICATION_DELAY = 3  # seconds between applications
    MAX_APPLICATIONS_PER_SESSION = 20
    AUTO_APPLY_ENABLED = True

    # Browser settings
    HEADLESS_MODE = False  # Set to True for production
    BROWSER_TIMEOUT = 30
    PAGE_LOAD_TIMEOUT = 15

    # API settings
    API_HOST = "0.0.0.0"
    API_PORT = 5000
    DEBUG_MODE = True

    # Logging settings
    LOG_LEVEL = "INFO"
    LOG_FILE = "jobright_clone.log"

    # Form detection patterns
    FORM_PATTERNS = {
        "linkedin": {
            "selectors": [
                ".jobs-apply-button",
                "[data-control-name='jobdetails_topcard_inapply']"
            ],
            "success_indicators": [
                "application submitted",
                "your application has been sent"
            ]
        },
        "greenhouse": {
            "selectors": [
                "input[type='submit']",
                "button[type='submit']"
            ],
            "success_indicators": [
                "thank you for your application",
                "application received"
            ]
        },
        "workday": {
            "selectors": [
                "[data-automation-id='apply']",
                "button:contains('Apply')"
            ],
            "success_indicators": [
                "application submitted successfully"
            ]
        }
    }

    # Field mapping for auto-fill
    FIELD_MAPPINGS = {
        "first_name": [
            "input[name*='first']",
            "input[id*='first']",
            "input[placeholder*='First']",
            "input[name*='firstName']"
        ],
        "last_name": [
            "input[name*='last']",
            "input[id*='last']",
            "input[placeholder*='Last']",
            "input[name*='lastName']"
        ],
        "email": [
            "input[type='email']",
            "input[name*='email']",
            "input[id*='email']"
        ],
        "phone": [
            "input[type='tel']",
            "input[name*='phone']",
            "input[id*='phone']"
        ],
        "linkedin": [
            "input[name*='linkedin']",
            "input[placeholder*='LinkedIn']",
            "input[name*='profile']"
        ],
        "website": [
            "input[name*='website']",
            "input[name*='portfolio']",
            "input[placeholder*='Website']"
        ]
    }

# Environment-based configuration
def get_config():
    """Get configuration based on environment"""
    env = os.getenv('FLASK_ENV', 'development')

    if env == 'production':
        AppConfig.DEBUG_MODE = False
        AppConfig.HEADLESS_MODE = True
        AppConfig.LOG_LEVEL = "WARNING"
        AppConfig.MAX_APPLICATIONS_PER_SESSION = 50

    return AppConfig

# Default user profile - can be overridden
DEFAULT_USER_PROFILE = UserProfile()