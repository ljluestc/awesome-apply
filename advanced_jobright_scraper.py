#!/usr/bin/env python3
"""
Advanced JobRight.ai Scraper
Uses multiple techniques to extract job data without Selenium dependency
"""

import requests
import json
import re
import time
import subprocess
from datetime import datetime
from urllib.parse import urljoin, urlparse, parse_qs
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class AdvancedJobRightScraper:
    def __init__(self):
        self.base_url = "https://jobright.ai"
        self.recommend_url = "https://jobright.ai/jobs/recommend"
        self.session = requests.Session()
        self.results = {
            'timestamp': datetime.now().isoformat(),
            'source_url': self.recommend_url,
            'extraction_methods': {},
            'job_listings': [],
            'external_application_links': [],
            'api_endpoints': [],
            'total_jobs_found': 0
        }

        # Enhanced headers to mimic real browser
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Cache-Control': 'max-age=0'
        })

    def fetch_page_with_retries(self, url, max_retries=3):
        """Fetch page with retry logic"""
        for attempt in range(max_retries):
            try:
                logger.info(f"Fetching {url} (attempt {attempt + 1})")
                response = self.session.get(url, timeout=30)
                response.raise_for_status()
                return response
            except Exception as e:
                logger.warning(f"Attempt {attempt + 1} failed: {e}")
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)  # Exponential backoff
                else:
                    raise

    def extract_from_javascript(self, content):
        """Extract data from JavaScript variables and objects"""
        logger.info("Extracting data from JavaScript...")

        js_patterns = [
            # React/Next.js initial props
            r'window\.__NEXT_DATA__\s*=\s*({.*?});',
            r'window\.__INITIAL_PROPS__\s*=\s*({.*?});',
            r'window\.__APP_DATA__\s*=\s*({.*?});',

            # Common data variables
            r'var\s+jobs\s*=\s*(\[.*?\]);',
            r'const\s+jobs\s*=\s*(\[.*?\]);',
            r'let\s+jobs\s*=\s*(\[.*?\]);',
            r'jobsData\s*=\s*(\[.*?\]);',
            r'recommendations\s*=\s*(\[.*?\]);',

            # JSON-LD structured data
            r'<script type="application/ld\+json"[^>]*>(.*?)</script>',

            # API calls in JavaScript
            r'fetch\(["\']([^"\']*api[^"\']*)["\']',
            r'axios\.get\(["\']([^"\']*api[^"\']*)["\']',
            r'\.post\(["\']([^"\']*api[^"\']*)["\']',

            # Data attributes and URLs
            r'data-job-url=["\']([^"\']*)["\']',
            r'data-apply-url=["\']([^"\']*)["\']',
            r'href=["\']([^"\']*apply[^"\']*)["\']',
            r'href=["\']([^"\']*job[^"\']*)["\']',

            # Common job board patterns
            r'(https?://[^"\s]*(?:linkedin|indeed|glassdoor|monster|ziprecruiter|greenhouse|lever|bamboohr|smartrecruiters|jobvite|taleo|icims|workday|myworkday)\.(?:com|co|net|io)[^"\s]*)',
        ]

        extracted_data = {
            'json_objects': [],
            'api_endpoints': [],
            'job_urls': [],
            'external_job_urls': []
        }

        for pattern in js_patterns:
            try:
                matches = re.findall(pattern, content, re.DOTALL | re.IGNORECASE)
                for match in matches:
                    if pattern.startswith(r'(https?://[^"\s]*(?:'):  # External job URLs
                        extracted_data['external_job_urls'].append(match)
                    elif 'api' in pattern:  # API endpoints
                        extracted_data['api_endpoints'].append(match)
                    elif pattern.startswith(r'href='):  # Job URLs
                        if match.startswith('http'):
                            extracted_data['job_urls'].append(match)
                    else:  # JSON objects
                        try:
                            # Try to parse as JSON
                            json_data = json.loads(match)
                            extracted_data['json_objects'].append(json_data)
                        except json.JSONDecodeError:
                            # If not valid JSON, store as string for analysis
                            extracted_data['json_objects'].append({'raw': match[:1000]})
            except Exception as e:
                logger.debug(f"Pattern {pattern} failed: {e}")

        logger.info(f"JavaScript extraction found: {len(extracted_data['json_objects'])} JSON objects, "
                   f"{len(extracted_data['external_job_urls'])} external URLs, "
                   f"{len(extracted_data['api_endpoints'])} API endpoints")

        return extracted_data

    def analyze_html_structure(self, content):
        """Analyze HTML structure for job-related elements"""
        logger.info("Analyzing HTML structure...")

        # Look for job-related class names and IDs
        job_patterns = [
            r'class=["\'][^"\']*job[^"\']*["\']',
            r'class=["\'][^"\']*recommendation[^"\']*["\']',
            r'class=["\'][^"\']*position[^"\']*["\']',
            r'class=["\'][^"\']*listing[^"\']*["\']',
            r'id=["\'][^"\']*job[^"\']*["\']',
            r'data-testid=["\'][^"\']*job[^"\']*["\']'
        ]

        html_analysis = {
            'job_related_classes': [],
            'potential_containers': [],
            'meta_tags': [],
            'structured_data': []
        }

        # Extract job-related classes
        for pattern in job_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            html_analysis['job_related_classes'].extend(matches)

        # Look for meta tags with job information
        meta_pattern = r'<meta[^>]*(?:property|name)=["\'][^"\']*(?:job|title|description)[^"\']*["\'][^>]*content=["\']([^"\']*)["\'][^>]*>'
        meta_matches = re.findall(meta_pattern, content, re.IGNORECASE)
        html_analysis['meta_tags'] = meta_matches

        # Look for structured data
        structured_patterns = [
            r'itemtype=["\']https://schema\.org/JobPosting["\'][^>]*>',
            r'<script type="application/ld\+json"[^>]*>(.*?)</script>'
        ]

        for pattern in structured_patterns:
            matches = re.findall(pattern, content, re.DOTALL)
            html_analysis['structured_data'].extend(matches)

        return html_analysis

    def try_chromium_headless(self):
        """Use Chromium in headless mode to render JavaScript"""
        logger.info("Attempting to use Chromium headless mode...")

        try:
            # Create a temporary JavaScript file to extract data
            js_code = """
            setTimeout(() => {
                const data = {
                    title: document.title,
                    url: window.location.href,
                    jobElements: [],
                    allLinks: [],
                    dataElements: []
                };

                // Find elements with job-related classes
                const jobSelectors = [
                    '[class*="job"]', '[class*="Job"]', '[class*="position"]',
                    '[class*="listing"]', '[class*="recommendation"]',
                    '[data-testid*="job"]', 'article', '[role="article"]'
                ];

                jobSelectors.forEach(selector => {
                    try {
                        const elements = document.querySelectorAll(selector);
                        elements.forEach(el => {
                            const jobInfo = {
                                tagName: el.tagName,
                                className: el.className,
                                id: el.id,
                                text: el.textContent.slice(0, 200),
                                innerHTML: el.innerHTML.slice(0, 500),
                                attributes: {}
                            };

                            // Get all attributes
                            for (let attr of el.attributes) {
                                jobInfo.attributes[attr.name] = attr.value;
                            }

                            data.jobElements.push(jobInfo);
                        });
                    } catch(e) {
                        console.error('Error with selector:', selector, e);
                    }
                });

                // Get all links
                document.querySelectorAll('a[href]').forEach(link => {
                    data.allLinks.push({
                        href: link.href,
                        text: link.textContent.trim().slice(0, 100),
                        className: link.className
                    });
                });

                // Look for data in window object
                const windowKeys = Object.keys(window);
                windowKeys.forEach(key => {
                    if (key.includes('job') || key.includes('data') || key.includes('props')) {
                        try {
                            data.dataElements.push({
                                key: key,
                                value: JSON.stringify(window[key]).slice(0, 1000)
                            });
                        } catch(e) {
                            data.dataElements.push({
                                key: key,
                                value: 'Could not serialize'
                            });
                        }
                    }
                });

                console.log('JOBRIGHT_DATA_START');
                console.log(JSON.stringify(data));
                console.log('JOBRIGHT_DATA_END');
            }, 5000);
            """

            # Write JavaScript to temp file
            js_file = '/tmp/extract_jobs.js'
            with open(js_file, 'w') as f:
                f.write(js_code)

            # Run Chromium with the JavaScript
            cmd = [
                'chromium', '--headless', '--no-sandbox', '--disable-gpu',
                '--disable-dev-shm-usage', '--disable-extensions',
                '--virtual-time-budget=10000',
                '--run-all-compositor-stages-before-draw',
                '--evaluate', js_file,
                self.recommend_url
            ]

            logger.info("Running Chromium headless...")
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)

            if result.returncode == 0:
                # Extract data from output
                output = result.stdout + result.stderr
                start_marker = 'JOBRIGHT_DATA_START'
                end_marker = 'JOBRIGHT_DATA_END'

                if start_marker in output and end_marker in output:
                    start_idx = output.find(start_marker) + len(start_marker)
                    end_idx = output.find(end_marker)
                    json_str = output[start_idx:end_idx].strip()

                    try:
                        data = json.loads(json_str)
                        logger.info(f"Chromium extraction successful: {len(data.get('jobElements', []))} job elements")
                        return data
                    except json.JSONDecodeError as e:
                        logger.warning(f"Failed to parse Chromium output: {e}")

            logger.warning("Chromium headless extraction failed")
            return None

        except Exception as e:
            logger.warning(f"Chromium headless error: {e}")
            return None

    def search_for_job_applications(self, content, chromium_data=None):
        """Search for actual job application links"""
        logger.info("Searching for job application opportunities...")

        job_applications = []

        # Common job board domains to look for
        job_domains = [
            'linkedin.com/jobs', 'indeed.com', 'glassdoor.com', 'monster.com',
            'ziprecruiter.com', 'careerbuilder.com', 'simplyhired.com',
            'jobs.com', 'greenhouse.io', 'lever.co', 'bamboohr.com',
            'smartrecruiters.com', 'jobvite.com', 'taleo.net', 'icims.com',
            'myworkday.com', 'workday.com', 'successfactors.com'
        ]

        # Extract URLs from content
        url_patterns = [
            r'https?://[^\s"\'<>]+',
            r'href=["\']([^"\']+)["\']',
            r'src=["\']([^"\']+)["\']'
        ]

        found_urls = set()
        for pattern in url_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            found_urls.update(matches)

        # Add URLs from Chromium data if available
        if chromium_data:
            for link in chromium_data.get('allLinks', []):
                found_urls.add(link.get('href', ''))

        # Filter for job-related URLs
        for url in found_urls:
            if not url or url.startswith('#') or url.startswith('javascript:'):
                continue

            # Check if it's a job board URL
            for domain in job_domains:
                if domain in url.lower():
                    job_applications.append({
                        'type': 'external_job_board',
                        'url': url,
                        'domain': domain,
                        'source': 'url_extraction'
                    })
                    break

            # Check for generic application URLs
            if any(term in url.lower() for term in ['apply', 'application', 'career', 'job', 'position']):
                # Avoid internal jobright links unless they lead to external applications
                if 'jobright.ai' not in url or 'external' in url or 'redirect' in url:
                    job_applications.append({
                        'type': 'application_link',
                        'url': url,
                        'source': 'keyword_matching'
                    })

        logger.info(f"Found {len(job_applications)} potential job application links")
        return job_applications

    def run_comprehensive_extraction(self):
        """Run all extraction methods"""
        logger.info("Starting comprehensive JobRight.ai job extraction...")

        # Step 1: Fetch the main page
        try:
            response = self.fetch_page_with_retries(self.recommend_url)
            page_content = response.text
            self.results['page_size'] = len(page_content)
            logger.info(f"Retrieved page content: {len(page_content)} characters")
        except Exception as e:
            logger.error(f"Failed to fetch page: {e}")
            return self.results

        # Step 2: Extract from JavaScript
        js_data = self.extract_from_javascript(page_content)
        self.results['extraction_methods']['javascript'] = js_data

        # Step 3: Analyze HTML structure
        html_data = self.analyze_html_structure(page_content)
        self.results['extraction_methods']['html_analysis'] = html_data

        # Step 4: Try Chromium headless
        chromium_data = self.try_chromium_headless()
        if chromium_data:
            self.results['extraction_methods']['chromium_headless'] = chromium_data

        # Step 5: Search for job applications
        job_apps = self.search_for_job_applications(page_content, chromium_data)
        self.results['job_applications'] = job_apps

        # Step 6: Consolidate findings
        all_job_links = set()

        # Add from JavaScript extraction
        all_job_links.update(js_data.get('external_job_urls', []))
        all_job_links.update(js_data.get('job_urls', []))

        # Add from job applications
        for app in job_apps:
            all_job_links.add(app['url'])

        # Add from Chromium data
        if chromium_data:
            for link in chromium_data.get('allLinks', []):
                href = link.get('href', '')
                if href and any(term in href.lower() for term in ['job', 'apply', 'career', 'position']):
                    all_job_links.add(href)

        self.results['all_job_links'] = list(all_job_links)
        self.results['total_jobs_found'] = len(all_job_links)

        logger.info(f"Extraction complete! Found {self.results['total_jobs_found']} job-related links")
        return self.results

    def save_results(self):
        """Save all results to files"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # JSON results
        json_file = f"/home/calelin/awesome-apply/advanced_jobright_results_{timestamp}.json"
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(self.results, f, indent=2, ensure_ascii=False)

        # Text summary with clickable links
        txt_file = f"/home/calelin/awesome-apply/jobright_jobs_{timestamp}.txt"
        with open(txt_file, 'w', encoding='utf-8') as f:
            f.write("JobRight.ai Comprehensive Job Extraction Results\n")
            f.write("="*60 + "\n")
            f.write(f"Extraction Date: {self.results['timestamp']}\n")
            f.write(f"Source URL: {self.results['source_url']}\n")
            f.write(f"Total Job Links Found: {self.results['total_jobs_found']}\n")
            f.write(f"Page Size: {self.results.get('page_size', 0)} characters\n\n")

            # Job Applications Section
            f.write("CLICKABLE JOB LINKS:\n")
            f.write("-" * 40 + "\n")
            for i, link in enumerate(self.results['all_job_links'], 1):
                f.write(f"{i:3d}. {link}\n")

            f.write(f"\n\nJOB APPLICATIONS BY TYPE:\n")
            f.write("-" * 40 + "\n")

            job_apps = self.results.get('job_applications', [])
            external_boards = [app for app in job_apps if app['type'] == 'external_job_board']
            application_links = [app for app in job_apps if app['type'] == 'application_link']

            f.write(f"\nExternal Job Boards ({len(external_boards)}):\n")
            for i, app in enumerate(external_boards, 1):
                f.write(f"  {i:2d}. {app['url']} (via {app['domain']})\n")

            f.write(f"\nApplication Links ({len(application_links)}):\n")
            for i, app in enumerate(application_links, 1):
                f.write(f"  {i:2d}. {app['url']}\n")

            # Method Summary
            f.write(f"\n\nEXTRACTION METHOD SUMMARY:\n")
            f.write("-" * 40 + "\n")
            for method, data in self.results['extraction_methods'].items():
                f.write(f"\n{method.upper()}:\n")
                if method == 'javascript':
                    f.write(f"  JSON Objects: {len(data.get('json_objects', []))}\n")
                    f.write(f"  External URLs: {len(data.get('external_job_urls', []))}\n")
                    f.write(f"  API Endpoints: {len(data.get('api_endpoints', []))}\n")
                elif method == 'chromium_headless' and data:
                    f.write(f"  Job Elements: {len(data.get('jobElements', []))}\n")
                    f.write(f"  All Links: {len(data.get('allLinks', []))}\n")

        # HTML analysis file
        html_file = f"/home/calelin/awesome-apply/jobright_analysis_{timestamp}.html"
        with open(html_file, 'w', encoding='utf-8') as f:
            f.write("""<!DOCTYPE html>
<html>
<head>
    <title>JobRight.ai Analysis Results</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; }
        .section { margin: 20px 0; padding: 15px; background: #f5f5f5; border-radius: 5px; }
        .link { display: block; margin: 5px 0; }
        .method { background: #e8e8e8; padding: 10px; margin: 10px 0; border-radius: 3px; }
        ul { list-style-type: none; padding: 0; }
        li { margin: 5px 0; }
        a { color: #0066cc; text-decoration: none; }
        a:hover { text-decoration: underline; }
    </style>
</head>
<body>""")

            f.write(f"<h1>JobRight.ai Job Links Analysis</h1>")
            f.write(f"<p><strong>Extraction Date:</strong> {self.results['timestamp']}</p>")
            f.write(f"<p><strong>Total Links Found:</strong> {self.results['total_jobs_found']}</p>")

            f.write("<div class='section'><h2>All Job Links (Clickable)</h2><ul>")
            for link in self.results['all_job_links']:
                f.write(f"<li><a href='{link}' target='_blank'>{link}</a></li>")
            f.write("</ul></div>")

            f.write("</body></html>")

        return json_file, txt_file, html_file

def main():
    scraper = AdvancedJobRightScraper()
    results = scraper.run_comprehensive_extraction()
    json_file, txt_file, html_file = scraper.save_results()

    print(f"\nAdvanced JobRight.ai Extraction Complete!")
    print(f"Total job links found: {results['total_jobs_found']}")
    print(f"\nFiles created:")
    print(f"  📊 JSON Data: {json_file}")
    print(f"  📝 Text Summary: {txt_file}")
    print(f"  🌐 HTML Report: {html_file}")

    if results['total_jobs_found'] > 0:
        print(f"\n✅ Success! Found {results['total_jobs_found']} job-related links")
        print(f"   Check the files above for clickable links to job applications.")
    else:
        print(f"\n⚠️  No job links found. The site may require authentication or have changed structure.")

if __name__ == "__main__":
    main()