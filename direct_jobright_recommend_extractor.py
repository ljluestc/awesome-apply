#!/usr/bin/env python3
"""
Direct JobRight Recommend URL Extractor
Target https://jobright.ai/jobs/recommend specifically
"""

import sys
sys.path.append('/home/calelin/awesome-apply/venv/lib/python3.13/site-packages')

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
import time
import logging
import json
from datetime import datetime

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def setup_driver():
    """Setup Chrome WebDriver for JobRight"""
    chrome_options = Options()
    user_data_dir = "/tmp/chrome_jobright_profile"
    chrome_options.add_argument(f"--user-data-dir={user_data_dir}")
    chrome_options.add_argument("--profile-directory=Default")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)

    driver = webdriver.Chrome(
        service=Service(ChromeDriverManager().install()),
        options=chrome_options
    )
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    return driver

def extract_jobs_from_recommend_page():
    """Extract jobs from https://jobright.ai/jobs/recommend"""
    driver = setup_driver()
    try:
        logger.info("🎯 Targeting https://jobright.ai/jobs/recommend directly")

        # Go directly to the recommend URL
        driver.get("https://jobright.ai/jobs/recommend")
        time.sleep(15)

        logger.info(f"📄 Page title: {driver.title}")
        logger.info(f"🌐 Current URL: {driver.current_url}")

        # Scroll extensively to load all content
        for i in range(8):
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(3)
            driver.execute_script("window.scrollTo(0, 0);")
            time.sleep(2)

        # Find all clickable elements with job-related content
        all_clickable = driver.find_elements(By.XPATH, "//*[@href or @onclick or @role='button' or name()='button' or name()='a']")
        logger.info(f"🔗 Found {len(all_clickable)} clickable elements")

        jobs_found = []
        for element in all_clickable:
            try:
                if element.is_displayed():
                    text = element.text.strip()
                    href = element.get_attribute('href') or ''
                    onclick = element.get_attribute('onclick') or ''

                    # Job keywords to look for
                    job_keywords = ['engineer', 'developer', 'manager', 'analyst', 'designer',
                                   'coordinator', 'specialist', 'associate', 'director', 'lead',
                                   'job', 'apply', 'position', 'career', 'work', 'employment']

                    # Check if element contains job-related content
                    text_lower = text.lower()
                    href_lower = href.lower()

                    if text and (href or onclick) and len(text) > 5:
                        is_job_related = any(keyword in text_lower or keyword in href_lower
                                           for keyword in job_keywords)

                        if is_job_related or 'job' in text_lower or 'apply' in text_lower:
                            jobs_found.append({
                                'title': text[:200],  # Limit title length
                                'url': href,
                                'onclick': onclick,
                                'element_type': element.tag_name
                            })
            except:
                continue

        # Deduplicate by URL and title
        unique_jobs = {}
        for job in jobs_found:
            key = f"{job['title'][:50]}_{job['url'][:50]}"
            if key not in unique_jobs and job['title'].strip():
                unique_jobs[key] = job

        final_jobs = list(unique_jobs.values())
        logger.info(f"🎉 Found {len(final_jobs)} unique job-related items")

        return final_jobs, driver.current_url, driver.title

    except Exception as e:
        logger.error(f"❌ Error extracting jobs: {e}")
        return [], "", ""
    finally:
        driver.quit()

def create_local_html_file(jobs, source_url, page_title):
    """Create local HTML file with clickable job links"""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    html_file = f"jobright_recommend_jobs_{timestamp}.html"

    with open(html_file, 'w') as f:
        f.write(f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>JobRight Recommended Jobs - {datetime.now().strftime('%Y-%m-%d')}</title>
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 0;
            padding: 20px;
            background-color: #f5f7fa;
            line-height: 1.6;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            overflow: hidden;
        }}
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            text-align: center;
        }}
        .header h1 {{
            margin: 0;
            font-size: 2.5em;
            font-weight: 300;
        }}
        .header p {{
            margin: 10px 0 0;
            opacity: 0.9;
            font-size: 1.1em;
        }}
        .stats {{
            background: #f8f9fa;
            padding: 20px;
            border-bottom: 1px solid #e9ecef;
            display: flex;
            justify-content: space-around;
            text-align: center;
        }}
        .stat {{
            padding: 10px;
        }}
        .stat-number {{
            font-size: 2em;
            font-weight: bold;
            color: #667eea;
        }}
        .stat-label {{
            color: #6c757d;
            font-size: 0.9em;
        }}
        .search-box {{
            padding: 20px;
            background: #f8f9fa;
            border-bottom: 1px solid #e9ecef;
        }}
        .search-input {{
            width: 100%;
            padding: 12px;
            border: 2px solid #e9ecef;
            border-radius: 25px;
            font-size: 16px;
            outline: none;
            transition: border-color 0.3s;
        }}
        .search-input:focus {{
            border-color: #667eea;
        }}
        .jobs-container {{
            padding: 20px;
        }}
        .job-item {{
            border: 1px solid #e9ecef;
            margin: 15px 0;
            padding: 20px;
            border-radius: 8px;
            transition: all 0.3s ease;
            background: white;
        }}
        .job-item:hover {{
            box-shadow: 0 4px 15px rgba(0,0,0,0.1);
            transform: translateY(-2px);
        }}
        .job-title {{
            font-size: 1.3em;
            font-weight: 600;
            color: #2c3e50;
            margin-bottom: 10px;
        }}
        .job-title a {{
            color: inherit;
            text-decoration: none;
        }}
        .job-title a:hover {{
            color: #667eea;
            text-decoration: underline;
        }}
        .job-url {{
            color: #667eea;
            margin: 10px 0;
            word-break: break-all;
            font-size: 0.9em;
        }}
        .job-meta {{
            font-size: 0.85em;
            color: #6c757d;
            margin-top: 10px;
        }}
        .apply-btn {{
            display: inline-block;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 10px 20px;
            border-radius: 25px;
            text-decoration: none;
            font-weight: 500;
            margin-top: 10px;
            transition: transform 0.3s;
        }}
        .apply-btn:hover {{
            transform: scale(1.05);
            text-decoration: none;
            color: white;
        }}
        .no-results {{
            text-align: center;
            padding: 40px;
            color: #6c757d;
        }}
        .footer {{
            background: #f8f9fa;
            padding: 20px;
            text-align: center;
            color: #6c757d;
            font-size: 0.9em;
        }}
        @media (max-width: 768px) {{
            .stats {{
                flex-direction: column;
            }}
            .header h1 {{
                font-size: 2em;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🎯 JobRight Recommended Jobs</h1>
            <p>All jobs extracted from {source_url}</p>
            <p>Generated on {datetime.now().strftime('%B %d, %Y at %I:%M %p')}</p>
        </div>

        <div class="stats">
            <div class="stat">
                <div class="stat-number">{len(jobs)}</div>
                <div class="stat-label">Total Jobs Found</div>
            </div>
            <div class="stat">
                <div class="stat-number">{len([j for j in jobs if j['url']])}</div>
                <div class="stat-label">Direct Links</div>
            </div>
            <div class="stat">
                <div class="stat-number">{datetime.now().strftime('%m/%d')}</div>
                <div class="stat-label">Extracted Today</div>
            </div>
        </div>

        <div class="search-box">
            <input type="text" class="search-input" placeholder="🔍 Search jobs by title, company, or keywords..."
                   onkeyup="filterJobs(this.value)">
        </div>

        <div class="jobs-container" id="jobsContainer">
""")

        if jobs:
            for i, job in enumerate(jobs, 1):
                job_title = job['title'].strip()
                job_url = job['url']

                f.write(f"""            <div class="job-item" data-search="{job_title.lower()}">
                <div class="job-title">
                    {i}. """)

                if job_url:
                    f.write(f"""<a href="{job_url}" target="_blank">{job_title}</a>""")
                else:
                    f.write(job_title)

                f.write(f"""</div>

                <div class="job-url">
                    🔗 """)

                if job_url:
                    f.write(f"""<a href="{job_url}" target="_blank">{job_url}</a>""")
                else:
                    f.write("No direct URL available")

                f.write(f"""</div>

                <div class="job-meta">
                    Element Type: {job['element_type'].upper()}
                </div>

                {f'<a href="{job_url}" target="_blank" class="apply-btn">🚀 View Job</a>' if job_url else ''}
            </div>
""")
        else:
            f.write("""            <div class="no-results">
                <h2>🔍 No Jobs Found</h2>
                <p>We couldn't extract any job listings from the page. This might be because:</p>
                <ul style="text-align: left; display: inline-block;">
                    <li>The page requires login or authentication</li>
                    <li>Jobs are loaded dynamically with JavaScript</li>
                    <li>The page structure has changed</li>
                </ul>
            </div>""")

        f.write(f"""        </div>

        <div class="footer">
            Generated by JobRight Job Extractor | Source: <a href="{source_url}" target="_blank">{source_url}</a>
        </div>
    </div>

    <script>
        function filterJobs(searchTerm) {{
            const jobs = document.querySelectorAll('.job-item');
            const searchLower = searchTerm.toLowerCase();

            jobs.forEach(job => {{
                const searchData = job.getAttribute('data-search');
                if (searchData.includes(searchLower)) {{
                    job.style.display = 'block';
                }} else {{
                    job.style.display = 'none';
                }}
            }});

            // Show "no results" message if no jobs visible
            const visibleJobs = document.querySelectorAll('.job-item[style="block"], .job-item:not([style*="none"])');
            const container = document.getElementById('jobsContainer');

            if (searchTerm && visibleJobs.length === 0) {{
                const noResults = document.querySelector('.no-results');
                if (!noResults) {{
                    container.innerHTML += '<div class="no-results temp"><h3>No jobs match your search</h3><p>Try different keywords</p></div>';
                }}
            }} else {{
                const tempNoResults = document.querySelector('.no-results.temp');
                if (tempNoResults) {{
                    tempNoResults.remove();
                }}
            }}
        }}

        // Add some interactive features
        document.addEventListener('DOMContentLoaded', function() {{
            console.log('JobRight Jobs Page Loaded');
            console.log('Total jobs:', {len(jobs)});

            // Add click tracking
            document.querySelectorAll('.apply-btn').forEach(btn => {{
                btn.addEventListener('click', function() {{
                    console.log('Job application clicked:', this.href);
                }});
            }});
        }});
    </script>
</body>
</html>""")

    return html_file

def main():
    """Main execution function"""
    logger.info("🚀 JOBRIGHT RECOMMEND JOBS EXTRACTOR STARTING")
    logger.info("="*60)

    # Extract jobs from the recommend page
    jobs, source_url, page_title = extract_jobs_from_recommend_page()

    # Create local HTML file
    html_file = create_local_html_file(jobs, source_url or "https://jobright.ai/jobs/recommend", page_title)

    # Save as JSON too
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    json_file = f"jobright_recommend_jobs_{timestamp}.json"

    with open(json_file, 'w') as f:
        json.dump({
            'source_url': source_url or "https://jobright.ai/jobs/recommend",
            'page_title': page_title,
            'timestamp': datetime.now().isoformat(),
            'total_jobs': len(jobs),
            'jobs': jobs
        }, f, indent=2)

    # Results
    logger.info("="*60)
    logger.info(f"🎉 EXTRACTION COMPLETE!")
    logger.info(f"📊 Total jobs found: {len(jobs)}")
    logger.info(f"🌐 HTML file: {html_file}")
    logger.info(f"📋 JSON file: {json_file}")
    logger.info("="*60)

    print(f"\n🎯 JobRight Recommended Jobs Extracted!")
    print(f"📁 HTML file created: {html_file}")
    print(f"📊 Total jobs: {len(jobs)}")
    print(f"\n🌐 Open {html_file} in your browser to see all clickable job links!")

    return jobs

if __name__ == "__main__":
    main()