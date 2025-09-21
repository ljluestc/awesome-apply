#!/usr/bin/env python3
"""
Comprehensive JobRight.ai Job Link Extractor
Attempts multiple strategies to extract job links from jobright.ai/jobs/recommend
"""

import requests
import json
import time
import re
from urllib.parse import urljoin, urlparse
from datetime import datetime
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class JobRightScraper:
    def __init__(self):
        self.base_url = "https://jobright.ai"
        self.recommend_url = "https://jobright.ai/jobs/recommend"
        self.session = requests.Session()
        self.job_links = []
        self.job_data = []

        # Common headers to appear more like a real browser
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        })

    def attempt_basic_scraping(self):
        """Try basic HTML scraping first"""
        logger.info("Attempting basic HTML scraping...")
        try:
            response = self.session.get(self.recommend_url, timeout=30)
            response.raise_for_status()

            content = response.text
            logger.info(f"Retrieved {len(content)} characters of HTML content")

            # Look for common job link patterns
            patterns = [
                r'href=["\']([^"\']*job[^"\']*)["\']',
                r'href=["\']([^"\']*apply[^"\']*)["\']',
                r'href=["\']([^"\']*position[^"\']*)["\']',
                r'data-url=["\']([^"\']*)["\']',
                r'data-link=["\']([^"\']*)["\']',
                r'data-href=["\']([^"\']*)["\']',
            ]

            found_links = set()
            for pattern in patterns:
                matches = re.findall(pattern, content, re.IGNORECASE)
                for match in matches:
                    if match and not match.startswith('#') and not match.startswith('javascript:'):
                        found_links.add(match)

            logger.info(f"Found {len(found_links)} potential links from basic scraping")
            return list(found_links), content

        except Exception as e:
            logger.error(f"Basic scraping failed: {e}")
            return [], ""

    def attempt_api_discovery(self):
        """Try to discover API endpoints"""
        logger.info("Attempting API endpoint discovery...")
        try:
            # Try common API patterns
            api_endpoints = [
                "/api/jobs",
                "/api/jobs/recommend",
                "/api/v1/jobs",
                "/api/v1/jobs/recommend",
                "/jobs/api",
                "/recommend/api",
                "/graphql",
            ]

            found_endpoints = []
            for endpoint in api_endpoints:
                url = urljoin(self.base_url, endpoint)
                try:
                    response = self.session.get(url, timeout=10)
                    if response.status_code == 200:
                        found_endpoints.append((url, response.text[:500]))
                        logger.info(f"Found potential API endpoint: {url}")
                except:
                    continue

            return found_endpoints

        except Exception as e:
            logger.error(f"API discovery failed: {e}")
            return []

    def search_for_external_links(self, content):
        """Extract external job application links"""
        logger.info("Searching for external job application links...")

        # Common job board domains
        job_domains = [
            'linkedin.com', 'indeed.com', 'glassdoor.com', 'monster.com',
            'ziprecruiter.com', 'careerbuilder.com', 'simplyhired.com',
            'jobs.com', 'workday.com', 'greenhouse.io', 'lever.co',
            'bamboohr.com', 'smartrecruiters.com', 'jobvite.com',
            'taleo.net', 'icims.com', 'myworkday.com'
        ]

        external_links = set()

        # Look for URLs containing job board domains
        for domain in job_domains:
            pattern = rf'https?://[^"\s]*{re.escape(domain)}[^"\s]*'
            matches = re.findall(pattern, content, re.IGNORECASE)
            external_links.update(matches)

        # Also look for generic application URLs
        app_patterns = [
            r'https?://[^"\s]*apply[^"\s]*',
            r'https?://[^"\s]*career[^"\s]*',
            r'https?://[^"\s]*job[^"\s]*',
            r'https?://[^"\s]*position[^"\s]*',
        ]

        for pattern in app_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            external_links.update(matches)

        logger.info(f"Found {len(external_links)} potential external job links")
        return list(external_links)

    def extract_json_data(self, content):
        """Extract job data from JSON embedded in the page"""
        logger.info("Extracting JSON data from page...")

        json_patterns = [
            r'<script[^>]*>\s*window\.__INITIAL_STATE__\s*=\s*({.*?})\s*</script>',
            r'<script[^>]*>\s*window\.__PRELOADED_STATE__\s*=\s*({.*?})\s*</script>',
            r'<script[^>]*>\s*window\.APP_STATE\s*=\s*({.*?})\s*</script>',
            r'<script type="application/json"[^>]*>({.*?})</script>',
            r'"jobs":\s*(\[.*?\])',
            r'"recommendations":\s*(\[.*?\])',
        ]

        extracted_data = []
        for pattern in json_patterns:
            matches = re.findall(pattern, content, re.DOTALL)
            for match in matches:
                try:
                    if match.strip().startswith('['):
                        data = json.loads(match)
                    else:
                        data = json.loads(match)
                    extracted_data.append(data)
                    logger.info("Successfully extracted JSON data")
                except json.JSONDecodeError:
                    continue

        return extracted_data

    def run_comprehensive_extraction(self):
        """Run all extraction methods"""
        logger.info("Starting comprehensive job link extraction...")

        results = {
            'timestamp': datetime.now().isoformat(),
            'source_url': self.recommend_url,
            'extraction_methods': {},
            'all_links': set(),
            'job_data': []
        }

        # Method 1: Basic HTML scraping
        basic_links, content = self.attempt_basic_scraping()
        results['extraction_methods']['basic_scraping'] = {
            'links_found': len(basic_links),
            'links': basic_links
        }
        results['all_links'].update(basic_links)

        # Method 2: API discovery
        api_endpoints = self.attempt_api_discovery()
        results['extraction_methods']['api_discovery'] = {
            'endpoints_found': len(api_endpoints),
            'endpoints': api_endpoints
        }

        # Method 3: External link extraction
        if content:
            external_links = self.search_for_external_links(content)
            results['extraction_methods']['external_links'] = {
                'links_found': len(external_links),
                'links': external_links
            }
            results['all_links'].update(external_links)

            # Method 4: JSON data extraction
            json_data = self.extract_json_data(content)
            results['extraction_methods']['json_extraction'] = {
                'data_objects_found': len(json_data),
                'data': json_data
            }
            results['job_data'].extend(json_data)

        # Convert set to list for JSON serialization
        results['all_links'] = list(results['all_links'])
        results['total_links_found'] = len(results['all_links'])

        logger.info(f"Extraction complete. Found {results['total_links_found']} total links")

        return results

    def save_results(self, results):
        """Save results in multiple formats"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # Save JSON results
        json_file = f"/home/calelin/awesome-apply/jobright_extraction_{timestamp}.json"
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)

        # Save text file with clickable links
        txt_file = f"/home/calelin/awesome-apply/jobright_links_{timestamp}.txt"
        with open(txt_file, 'w', encoding='utf-8') as f:
            f.write(f"JobRight.ai Job Links Extraction Results\n")
            f.write(f"Generated: {results['timestamp']}\n")
            f.write(f"Source: {results['source_url']}\n")
            f.write(f"Total Links Found: {results['total_links_found']}\n")
            f.write("="*80 + "\n\n")

            for i, link in enumerate(results['all_links'], 1):
                f.write(f"{i:3d}. {link}\n")

            f.write("\n" + "="*80 + "\n")
            f.write("Extraction Method Details:\n")
            for method, data in results['extraction_methods'].items():
                f.write(f"\n{method.upper()}:\n")
                f.write(f"  Links found: {data.get('links_found', 0)}\n")
                if 'links' in data:
                    for link in data['links'][:5]:  # Show first 5 links per method
                        f.write(f"    - {link}\n")

        return json_file, txt_file

if __name__ == "__main__":
    scraper = JobRightScraper()
    results = scraper.run_comprehensive_extraction()
    json_file, txt_file = scraper.save_results(results)

    print(f"\nExtraction Results:")
    print(f"Total links found: {results['total_links_found']}")
    print(f"Results saved to:")
    print(f"  JSON: {json_file}")
    print(f"  TXT:  {txt_file}")

    # Print summary
    print(f"\nMethod Summary:")
    for method, data in results['extraction_methods'].items():
        print(f"  {method}: {data.get('links_found', 0)} links")