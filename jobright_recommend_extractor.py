#!/usr/bin/env python3
"""
Extract ALL jobs from https://jobright.ai/jobs/recommend as clickable links locally
Direct implementation based on successful automation patterns
"""

import sys
sys.path.append('/home/calelin/awesome-apply/venv/lib/python3.13/site-packages')

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import logging
import json
from datetime import datetime

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class JobRightRecommendExtractor:
    def __init__(self):
        self.driver = None
        self.session_id = datetime.now().strftime('%Y%m%d_%H%M%S')
        self.extracted_jobs = []

    def setup_driver(self):
        """Setup Chrome WebDriver"""
        chrome_options = Options()
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
        logger.info("✅ Chrome driver setup complete")

    def extract_all_jobs(self):
        """Extract all jobs from JobRight recommend page"""
        try:
            url = "https://jobright.ai/jobs/recommend"
            logger.info(f"🎯 Extracting ALL jobs from: {url}")

            self.driver.get(url)
            time.sleep(10)  # Give page time to load

            logger.info(f"📄 Page title: {self.driver.title}")
            logger.info(f"🌐 Current URL: {self.driver.current_url}")

            # Extensive scrolling to load all dynamic content
            for i in range(10):
                logger.info(f"📜 Scrolling pass {i+1}/10")
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(2)
                # Scroll back up to trigger more loading
                self.driver.execute_script("window.scrollTo(0, 0);")
                time.sleep(1)

            # Method 1: Get ALL clickable elements
            all_elements = self.driver.find_elements(By.XPATH, "//*[@href or @onclick or contains(@class, 'job') or contains(@class, 'apply') or contains(@class, 'button') or contains(@class, 'link')]")
            logger.info(f"🔗 Found {len(all_elements)} potentially clickable elements")

            # Method 2: Get all text content that looks like job titles
            job_text_elements = self.driver.find_elements(By.XPATH, "//*[contains(text(), 'Engineer') or contains(text(), 'Developer') or contains(text(), 'Manager') or contains(text(), 'Analyst') or contains(text(), 'Designer') or contains(text(), 'Coordinator') or contains(text(), 'Specialist') or contains(text(), 'Associate') or contains(text(), 'Director') or contains(text(), 'Lead')]")
            logger.info(f"💼 Found {len(job_text_elements)} job title elements")

            # Method 3: JavaScript comprehensive extraction
            js_extraction = self.driver.execute_script("""
                var results = [];
                var allElements = document.querySelectorAll('*');

                for (var i = 0; i < allElements.length; i++) {
                    var elem = allElements[i];
                    var text = elem.textContent || '';
                    var href = elem.href || '';
                    var onclick = elem.getAttribute('onclick') || '';
                    var className = elem.className || '';

                    // Look for job-related content
                    var jobKeywords = ['engineer', 'developer', 'manager', 'analyst', 'designer',
                                     'coordinator', 'specialist', 'associate', 'director', 'lead',
                                     'software', 'data', 'product', 'marketing', 'sales', 'apply'];

                    var isJobRelated = false;
                    for (var j = 0; j < jobKeywords.length; j++) {
                        if (text.toLowerCase().includes(jobKeywords[j]) ||
                            href.toLowerCase().includes(jobKeywords[j]) ||
                            className.toLowerCase().includes(jobKeywords[j])) {
                            isJobRelated = true;
                            break;
                        }
                    }

                    if (isJobRelated && (href || onclick || elem.tagName === 'BUTTON')) {
                        results.push({
                            tagName: elem.tagName,
                            text: text.trim().substring(0, 100),
                            href: href,
                            onclick: onclick,
                            className: className,
                            id: elem.id || '',
                            xpath: getXPath(elem)
                        });
                    }
                }

                function getXPath(element) {
                    if (element.id !== '') {
                        return '//*[@id="' + element.id + '"]';
                    }
                    if (element === document.body) {
                        return '/html/body';
                    }
                    var ix = 0;
                    var siblings = element.parentNode.childNodes;
                    for (var i = 0; i < siblings.length; i++) {
                        var sibling = siblings[i];
                        if (sibling === element) {
                            return getXPath(element.parentNode) + '/' + element.tagName.toLowerCase() + '[' + (ix + 1) + ']';
                        }
                        if (sibling.nodeType === 1 && sibling.tagName === element.tagName) {
                            ix++;
                        }
                    }
                }

                return results;
            """)

            logger.info(f"🔍 JavaScript extraction found {len(js_extraction)} job-related elements")

            # Process and deduplicate all findings
            unique_jobs = {}

            # Process clickable elements
            for element in all_elements:
                try:
                    if element.is_displayed():
                        text = element.text.strip()
                        href = element.get_attribute('href') or ''
                        onclick = element.get_attribute('onclick') or ''

                        if text and (href or onclick):
                            key = f"{text[:50]}_{href[:50]}"
                            if key not in unique_jobs:
                                unique_jobs[key] = {
                                    'title': text[:100],
                                    'url': href,
                                    'onclick': onclick,
                                    'source': 'selenium_clickable'
                                }
                except:
                    continue

            # Process text elements
            for element in job_text_elements:
                try:
                    if element.is_displayed():
                        text = element.text.strip()
                        if text:
                            # Try to find clickable parent
                            parent = element
                            for _ in range(5):
                                try:
                                    parent = parent.find_element(By.XPATH, "..")
                                    href = parent.get_attribute('href')
                                    onclick = parent.get_attribute('onclick')
                                    if href or onclick:
                                        key = f"{text[:50]}_{href[:50] if href else onclick[:50]}"
                                        if key not in unique_jobs:
                                            unique_jobs[key] = {
                                                'title': text[:100],
                                                'url': href or '',
                                                'onclick': onclick or '',
                                                'source': 'selenium_text_parent'
                                            }
                                        break
                                except:
                                    break
                except:
                    continue

            # Process JavaScript extraction
            for item in js_extraction:
                text = item.get('text', '').strip()
                href = item.get('href', '')
                onclick = item.get('onclick', '')

                if text:
                    key = f"{text[:50]}_{href[:50]}"
                    if key not in unique_jobs:
                        unique_jobs[key] = {
                            'title': text[:100],
                            'url': href,
                            'onclick': onclick,
                            'source': 'javascript_extraction',
                            'xpath': item.get('xpath', ''),
                            'tagName': item.get('tagName', ''),
                            'className': item.get('className', '')
                        }

            # Convert to list
            self.extracted_jobs = list(unique_jobs.values())
            logger.info(f"🎉 Total unique jobs extracted: {len(self.extracted_jobs)}")

            return self.extracted_jobs

        except Exception as e:
            logger.error(f"❌ Error extracting jobs: {e}")
            return []

    def save_results(self):
        """Save results in multiple formats"""
        try:
            # JSON format
            json_file = f"jobright_recommend_jobs_{self.session_id}.json"
            with open(json_file, 'w') as f:
                json.dump({
                    'url': 'https://jobright.ai/jobs/recommend',
                    'timestamp': datetime.now().isoformat(),
                    'total_jobs': len(self.extracted_jobs),
                    'jobs': self.extracted_jobs
                }, f, indent=2)

            # Text format
            txt_file = f"jobright_recommend_jobs_{self.session_id}.txt"
            with open(txt_file, 'w') as f:
                f.write(f"JobRight.ai Recommended Jobs - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"URL: https://jobright.ai/jobs/recommend\n")
                f.write(f"Total jobs found: {len(self.extracted_jobs)}\n")
                f.write("="*80 + "\n\n")

                for i, job in enumerate(self.extracted_jobs, 1):
                    f.write(f"{i}. {job['title']}\n")
                    if job['url']:
                        f.write(f"   URL: {job['url']}\n")
                    if job['onclick']:
                        f.write(f"   OnClick: {job['onclick']}\n")
                    f.write(f"   Source: {job['source']}\n")
                    f.write("\n")

            # HTML format with clickable links
            html_file = f"jobright_recommend_jobs_{self.session_id}.html"
            with open(html_file, 'w') as f:
                f.write(f"""<!DOCTYPE html>
<html>
<head>
    <title>JobRight.ai Recommended Jobs - {datetime.now().strftime('%Y-%m-%d')}</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        .job {{ border: 1px solid #ddd; margin: 10px 0; padding: 15px; border-radius: 5px; }}
        .job-title {{ font-weight: bold; color: #0066cc; }}
        .job-url {{ color: #666; margin: 5px 0; }}
        .job-source {{ font-size: 12px; color: #999; }}
        a {{ text-decoration: none; }}
        a:hover {{ text-decoration: underline; }}
        .header {{ background: #f5f5f5; padding: 20px; border-radius: 5px; margin-bottom: 20px; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>JobRight.ai Recommended Jobs</h1>
        <p><strong>Extracted from:</strong> https://jobright.ai/jobs/recommend</p>
        <p><strong>Date:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        <p><strong>Total Jobs Found:</strong> {len(self.extracted_jobs)}</p>
    </div>
""")

                for i, job in enumerate(self.extracted_jobs, 1):
                    f.write(f"""    <div class="job">
        <div class="job-title">
            {i}. """)

                    if job['url']:
                        f.write(f"""<a href="{job['url']}" target="_blank">{job['title']}</a>""")
                    else:
                        f.write(job['title'])

                    f.write(f"""</div>
        <div class="job-url">""")

                    if job['url']:
                        f.write(f"""URL: <a href="{job['url']}" target="_blank">{job['url']}</a>""")
                    elif job['onclick']:
                        f.write(f"""OnClick: {job['onclick']}""")
                    else:
                        f.write("No direct URL available")

                    f.write(f"""</div>
        <div class="job-source">Source: {job['source']}</div>
    </div>
""")

                f.write("""</body>
</html>""")

            logger.info(f"📁 Results saved to:")
            logger.info(f"   JSON: {json_file}")
            logger.info(f"   Text: {txt_file}")
            logger.info(f"   HTML: {html_file}")

            return json_file, txt_file, html_file

        except Exception as e:
            logger.error(f"❌ Error saving results: {e}")
            return None, None, None

    def run(self):
        """Run the complete extraction"""
        try:
            logger.info("🚀 JOBRIGHT.AI RECOMMEND JOBS EXTRACTOR")
            logger.info("🎯 Extracting ALL jobs from https://jobright.ai/jobs/recommend")
            logger.info("="*80)

            self.setup_driver()

            jobs = self.extract_all_jobs()

            if jobs:
                json_file, txt_file, html_file = self.save_results()

                logger.info("="*80)
                logger.info(f"🎉 SUCCESS! Extracted {len(jobs)} jobs from JobRight recommend page")
                logger.info(f"📁 Files created:")
                if json_file:
                    logger.info(f"   📋 JSON: {json_file}")
                if txt_file:
                    logger.info(f"   📝 Text: {txt_file}")
                if html_file:
                    logger.info(f"   🌐 HTML: {html_file}")

                # Print summary
                print(f"\n🎯 JOBRIGHT RECOMMEND JOBS EXTRACTED:")
                print(f"   Total jobs: {len(jobs)}")
                print(f"   HTML file: {html_file}")
                print(f"   Open the HTML file in your browser to see all clickable job links!")

                return jobs
            else:
                logger.warning("⚠️ No jobs extracted")
                return []

        except Exception as e:
            logger.error(f"❌ Extraction failed: {e}")
            return []
        finally:
            if self.driver:
                self.driver.quit()

if __name__ == "__main__":
    extractor = JobRightRecommendExtractor()
    extractor.run()