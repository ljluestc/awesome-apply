#!/usr/bin/env python3
"""
JobRight.ai Sitemap Job Extractor
Extracts job URLs from the sitemap and fetches job details
"""

import requests
import xml.etree.ElementTree as ET
import json
import re
from datetime import datetime
from urllib.parse import urljoin, urlparse
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class SitemapJobExtractor:
    def __init__(self):
        self.base_url = "https://jobright.ai"
        self.sitemap_url = "https://jobright.ai/sitemap.xml"
        self.session = requests.Session()

        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
        })

    def fetch_sitemap(self):
        """Fetch and parse the sitemap"""
        logger.info(f"Fetching sitemap from {self.sitemap_url}")

        try:
            response = self.session.get(self.sitemap_url, timeout=30)
            response.raise_for_status()

            logger.info(f"Sitemap fetched: {len(response.content)} bytes")

            # Try to parse as XML
            try:
                root = ET.fromstring(response.content)
                return root, 'xml'
            except ET.ParseError:
                # If not XML, return as text for analysis
                return response.text, 'text'

        except Exception as e:
            logger.error(f"Failed to fetch sitemap: {e}")
            return None, None

    def extract_urls_from_xml_sitemap(self, root):
        """Extract URLs from XML sitemap"""
        urls = []

        # Handle different sitemap formats
        namespaces = {
            '': 'http://www.sitemaps.org/schemas/sitemap/0.9',
            'sitemap': 'http://www.sitemaps.org/schemas/sitemap/0.9'
        }

        try:
            # Try to find URL elements
            for url_elem in root.findall('.//url', namespaces) or root.findall('.//url'):
                loc_elem = url_elem.find('loc', namespaces) or url_elem.find('loc')
                if loc_elem is not None and loc_elem.text:
                    urls.append({
                        'url': loc_elem.text.strip(),
                        'lastmod': None,
                        'priority': None
                    })

                    # Try to get additional info
                    lastmod_elem = url_elem.find('lastmod', namespaces) or url_elem.find('lastmod')
                    if lastmod_elem is not None and lastmod_elem.text:
                        urls[-1]['lastmod'] = lastmod_elem.text.strip()

                    priority_elem = url_elem.find('priority', namespaces) or url_elem.find('priority')
                    if priority_elem is not None and priority_elem.text:
                        urls[-1]['priority'] = priority_elem.text.strip()

            # If no URLs found with namespaces, try without
            if not urls:
                for url_elem in root.iter():
                    if url_elem.tag.endswith('url'):
                        for child in url_elem:
                            if child.tag.endswith('loc') and child.text:
                                urls.append({
                                    'url': child.text.strip(),
                                    'lastmod': None,
                                    'priority': None
                                })

        except Exception as e:
            logger.warning(f"Error parsing XML sitemap: {e}")

        return urls

    def extract_urls_from_text_sitemap(self, content):
        """Extract URLs from text-based sitemap"""
        urls = []

        # Look for URL patterns
        url_patterns = [
            r'https?://[^\s<>"\']+',
            r'<loc[^>]*>(https?://[^<]+)</loc>',
            r'<url[^>]*>(https?://[^<]+)</url>'
        ]

        for pattern in url_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            for match in matches:
                if isinstance(match, tuple):
                    match = match[0]  # Take first group if tuple
                if match.startswith('http'):
                    urls.append({
                        'url': match.strip(),
                        'lastmod': None,
                        'priority': None
                    })

        return urls

    def filter_job_urls(self, urls):
        """Filter URLs that are likely job-related"""
        job_urls = []

        job_indicators = [
            '/job/', '/jobs/', '/position/', '/positions/',
            '/career/', '/careers/', '/opportunity/', '/opportunities/',
            '/apply/', '/application/', '/posting/', '/postings/',
            '/recommend/', '/recommendation/'
        ]

        for url_data in urls:
            url = url_data['url']
            if any(indicator in url.lower() for indicator in job_indicators):
                job_urls.append(url_data)

        logger.info(f"Found {len(job_urls)} job-related URLs in sitemap")
        return job_urls

    def fetch_job_page(self, url):
        """Fetch a job page and extract relevant information"""
        try:
            response = self.session.get(url, timeout=15)
            response.raise_for_status()

            content = response.text

            job_info = {
                'url': url,
                'status_code': response.status_code,
                'title': '',
                'company': '',
                'location': '',
                'description': '',
                'apply_links': [],
                'external_links': []
            }

            # Extract title
            title_match = re.search(r'<title[^>]*>([^<]+)</title>', content, re.IGNORECASE)
            if title_match:
                job_info['title'] = title_match.group(1).strip()

            # Look for job-specific meta tags
            meta_patterns = [
                r'<meta[^>]*property=["\']og:title["\'][^>]*content=["\']([^"\']+)["\']',
                r'<meta[^>]*name=["\']title["\'][^>]*content=["\']([^"\']+)["\']',
                r'<meta[^>]*property=["\']job:title["\'][^>]*content=["\']([^"\']+)["\']'
            ]

            for pattern in meta_patterns:
                match = re.search(pattern, content, re.IGNORECASE)
                if match and not job_info['title']:
                    job_info['title'] = match.group(1).strip()

            # Look for company information
            company_patterns = [
                r'<meta[^>]*property=["\']job:company["\'][^>]*content=["\']([^"\']+)["\']',
                r'<meta[^>]*name=["\']company["\'][^>]*content=["\']([^"\']+)["\']',
                r'"company"[^:]*:[^"]*"([^"]+)"',
                r'class="[^"]*company[^"]*"[^>]*>([^<]+)<'
            ]

            for pattern in company_patterns:
                match = re.search(pattern, content, re.IGNORECASE)
                if match:
                    job_info['company'] = match.group(1).strip()
                    break

            # Look for location
            location_patterns = [
                r'<meta[^>]*property=["\']job:location["\'][^>]*content=["\']([^"\']+)["\']',
                r'<meta[^>]*name=["\']location["\'][^>]*content=["\']([^"\']+)["\']',
                r'"location"[^:]*:[^"]*"([^"]+)"',
                r'class="[^"]*location[^"]*"[^>]*>([^<]+)<'
            ]

            for pattern in location_patterns:
                match = re.search(pattern, content, re.IGNORECASE)
                if match:
                    job_info['location'] = match.group(1).strip()
                    break

            # Look for apply links
            apply_patterns = [
                r'href=["\']([^"\']*apply[^"\']*)["\']',
                r'href=["\']([^"\']*application[^"\']*)["\']',
                r'data-apply-url=["\']([^"\']*)["\']',
                r'data-job-url=["\']([^"\']*)["\']'
            ]

            for pattern in apply_patterns:
                matches = re.findall(pattern, content, re.IGNORECASE)
                job_info['apply_links'].extend(matches)

            # Look for external job board links
            external_domains = [
                'linkedin.com', 'indeed.com', 'glassdoor.com', 'monster.com',
                'ziprecruiter.com', 'greenhouse.io', 'lever.co', 'workday.com'
            ]

            for domain in external_domains:
                pattern = rf'https?://[^"\s]*{re.escape(domain)}[^"\s]*'
                matches = re.findall(pattern, content, re.IGNORECASE)
                job_info['external_links'].extend(matches)

            # Clean up duplicates
            job_info['apply_links'] = list(set(job_info['apply_links']))
            job_info['external_links'] = list(set(job_info['external_links']))

            return job_info

        except Exception as e:
            logger.warning(f"Failed to fetch job page {url}: {e}")
            return {
                'url': url,
                'error': str(e)
            }

    def run_sitemap_extraction(self):
        """Run complete sitemap-based job extraction"""
        logger.info("Starting sitemap-based job extraction...")

        results = {
            'timestamp': datetime.now().isoformat(),
            'sitemap_url': self.sitemap_url,
            'extraction_method': 'sitemap_analysis',
            'total_urls_found': 0,
            'job_urls_found': 0,
            'jobs_extracted': 0,
            'all_urls': [],
            'job_urls': [],
            'job_details': [],
            'external_application_links': [],
            'summary': {}
        }

        # Step 1: Fetch sitemap
        sitemap_data, sitemap_type = self.fetch_sitemap()
        if not sitemap_data:
            logger.error("Could not fetch sitemap")
            return results

        # Step 2: Extract URLs
        if sitemap_type == 'xml':
            urls = self.extract_urls_from_xml_sitemap(sitemap_data)
        else:
            urls = self.extract_urls_from_text_sitemap(sitemap_data)

        results['total_urls_found'] = len(urls)
        results['all_urls'] = urls
        logger.info(f"Found {len(urls)} total URLs in sitemap")

        # Step 3: Filter job URLs
        job_urls = self.filter_job_urls(urls)
        results['job_urls_found'] = len(job_urls)
        results['job_urls'] = job_urls

        # Step 4: Extract job details
        if job_urls:
            logger.info(f"Extracting details from {len(job_urls)} job URLs...")

            for i, job_url_data in enumerate(job_urls[:20], 1):  # Limit to first 20 for now
                logger.info(f"Processing job {i}/{min(20, len(job_urls))}: {job_url_data['url']}")
                job_details = self.fetch_job_page(job_url_data['url'])
                results['job_details'].append(job_details)

                # Collect external application links
                if 'apply_links' in job_details:
                    results['external_application_links'].extend(job_details['apply_links'])
                if 'external_links' in job_details:
                    results['external_application_links'].extend(job_details['external_links'])

        results['jobs_extracted'] = len(results['job_details'])
        results['external_application_links'] = list(set(results['external_application_links']))

        # Create summary
        successful_extractions = [job for job in results['job_details'] if 'error' not in job]
        results['summary'] = {
            'successful_extractions': len(successful_extractions),
            'failed_extractions': len(results['job_details']) - len(successful_extractions),
            'total_apply_links': len(results['external_application_links']),
            'jobs_with_apply_links': len([job for job in successful_extractions if job.get('apply_links') or job.get('external_links')]),
            'average_apply_links_per_job': len(results['external_application_links']) / max(len(successful_extractions), 1)
        }

        logger.info(f"Sitemap extraction complete! Extracted {len(successful_extractions)} jobs successfully")
        return results

    def save_results(self, results):
        """Save extraction results"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # JSON file
        json_file = f"/home/calelin/awesome-apply/sitemap_jobs_{timestamp}.json"
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)

        # Text summary
        txt_file = f"/home/calelin/awesome-apply/sitemap_job_links_{timestamp}.txt"
        with open(txt_file, 'w', encoding='utf-8') as f:
            f.write("JobRight.ai Sitemap Job Extraction Results\n")
            f.write("="*60 + "\n")
            f.write(f"Extraction Date: {results['timestamp']}\n")
            f.write(f"Source: {results['sitemap_url']}\n")
            f.write(f"Total URLs in Sitemap: {results['total_urls_found']}\n")
            f.write(f"Job URLs Found: {results['job_urls_found']}\n")
            f.write(f"Jobs Successfully Extracted: {results['summary']['successful_extractions']}\n")
            f.write(f"Total Apply Links: {results['summary']['total_apply_links']}\n\n")

            # Clickable job application links
            f.write("CLICKABLE JOB APPLICATION LINKS:\n")
            f.write("-" * 40 + "\n")
            for i, link in enumerate(results['external_application_links'], 1):
                f.write(f"{i:3d}. {link}\n")

            f.write(f"\n\nJOB DETAILS:\n")
            f.write("-" * 40 + "\n")
            for i, job in enumerate(results['job_details'], 1):
                if 'error' not in job:
                    f.write(f"\n{i:2d}. {job.get('title', 'No Title')}\n")
                    f.write(f"    Company: {job.get('company', 'Unknown')}\n")
                    f.write(f"    Location: {job.get('location', 'Unknown')}\n")
                    f.write(f"    URL: {job['url']}\n")
                    if job.get('apply_links'):
                        f.write(f"    Apply Links: {len(job['apply_links'])}\n")
                        for link in job['apply_links'][:3]:
                            f.write(f"      - {link}\n")
                    if job.get('external_links'):
                        f.write(f"    External Links: {len(job['external_links'])}\n")
                        for link in job['external_links'][:2]:
                            f.write(f"      - {link}\n")

        # HTML report with clickable links
        html_file = f"/home/calelin/awesome-apply/sitemap_jobs_report_{timestamp}.html"
        with open(html_file, 'w', encoding='utf-8') as f:
            f.write("""<!DOCTYPE html>
<html>
<head>
    <title>JobRight.ai Sitemap Job Extraction</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; line-height: 1.6; }
        .header { background: #f0f8ff; padding: 20px; border-radius: 8px; margin-bottom: 20px; }
        .job-card { background: #f9f9f9; padding: 15px; margin: 10px 0; border-radius: 5px; border-left: 4px solid #007acc; }
        .apply-links { background: #e8f5e8; padding: 15px; border-radius: 5px; margin: 20px 0; }
        .stats { display: flex; gap: 20px; margin: 20px 0; }
        .stat-box { background: #fff; border: 1px solid #ddd; padding: 15px; border-radius: 5px; text-align: center; }
        a { color: #007acc; text-decoration: none; }
        a:hover { text-decoration: underline; }
        ul { padding-left: 20px; }
    </style>
</head>
<body>""")

            f.write(f"""
<div class="header">
    <h1>JobRight.ai Job Extraction Results</h1>
    <p><strong>Extraction Date:</strong> {results['timestamp']}</p>
    <p><strong>Method:</strong> Sitemap Analysis</p>
</div>

<div class="stats">
    <div class="stat-box">
        <h3>{results['job_urls_found']}</h3>
        <p>Job URLs Found</p>
    </div>
    <div class="stat-box">
        <h3>{results['summary']['successful_extractions']}</h3>
        <p>Jobs Extracted</p>
    </div>
    <div class="stat-box">
        <h3>{results['summary']['total_apply_links']}</h3>
        <p>Apply Links</p>
    </div>
</div>
""")

            # Apply links section
            if results['external_application_links']:
                f.write('<div class="apply-links">')
                f.write('<h2>🔗 Direct Application Links (Clickable)</h2>')
                f.write('<ul>')
                for link in results['external_application_links']:
                    f.write(f'<li><a href="{link}" target="_blank">{link}</a></li>')
                f.write('</ul>')
                f.write('</div>')

            # Job details
            f.write('<h2>💼 Job Details</h2>')
            for job in results['job_details']:
                if 'error' not in job:
                    f.write('<div class="job-card">')
                    f.write(f'<h3><a href="{job["url"]}" target="_blank">{job.get("title", "No Title")}</a></h3>')
                    if job.get('company'):
                        f.write(f'<p><strong>Company:</strong> {job["company"]}</p>')
                    if job.get('location'):
                        f.write(f'<p><strong>Location:</strong> {job["location"]}</p>')

                    all_links = job.get('apply_links', []) + job.get('external_links', [])
                    if all_links:
                        f.write('<p><strong>Application Links:</strong></p>')
                        f.write('<ul>')
                        for link in all_links:
                            f.write(f'<li><a href="{link}" target="_blank">{link}</a></li>')
                        f.write('</ul>')
                    f.write('</div>')

            f.write('</body></html>')

        return json_file, txt_file, html_file

def main():
    extractor = SitemapJobExtractor()
    results = extractor.run_sitemap_extraction()
    json_file, txt_file, html_file = extractor.save_results(results)

    print(f"\nSitemap Job Extraction Complete!")
    print(f"📊 Results Summary:")
    print(f"   Total URLs in Sitemap: {results['total_urls_found']}")
    print(f"   Job URLs Found: {results['job_urls_found']}")
    print(f"   Jobs Successfully Extracted: {results['summary']['successful_extractions']}")
    print(f"   Total Application Links: {results['summary']['total_apply_links']}")

    print(f"\n📁 Files Created:")
    print(f"   JSON Data: {json_file}")
    print(f"   Text Summary: {txt_file}")
    print(f"   HTML Report: {html_file}")

    if results['summary']['total_apply_links'] > 0:
        print(f"\n✅ SUCCESS! Found {results['summary']['total_apply_links']} application links!")
        print(f"   Open the HTML report for clickable job application links.")
    else:
        print(f"\n⚠️  No direct application links found in extracted jobs.")

if __name__ == "__main__":
    main()