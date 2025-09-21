#!/usr/bin/env python3
"""
Final JobRight.ai Job Aggregator
Tries alternative pages and creates a comprehensive report of all findings
"""

import requests
import json
import re
from datetime import datetime
from urllib.parse import urljoin
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class FinalJobAggregator:
    def __init__(self):
        self.base_url = "https://jobright.ai"
        self.session = requests.Session()

        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
        })

    def try_alternative_job_pages(self):
        """Try alternative pages that might contain job data"""
        logger.info("Trying alternative job pages...")

        alternative_pages = [
            "/h1b-jobs",
            "/jobs",
            "/job-autofill",
            "/browse",
            "/search",
            "/explore",
            "/companies",
            "/positions"
        ]

        results = []

        for page in alternative_pages:
            try:
                url = urljoin(self.base_url, page)
                logger.info(f"Checking {url}")

                response = self.session.get(url, timeout=15)

                result = {
                    'page': page,
                    'url': url,
                    'status_code': response.status_code,
                    'content_length': len(response.content),
                    'job_links': [],
                    'external_links': [],
                    'company_mentions': [],
                    'job_titles': []
                }

                if response.status_code == 200:
                    content = response.text

                    # Look for job-related links
                    job_link_patterns = [
                        r'href=["\']([^"\']*(?:job|position|career|apply)[^"\']*)["\']',
                        r'href=["\']([^"\']*linkedin\.com/jobs[^"\']*)["\']',
                        r'href=["\']([^"\']*indeed\.com[^"\']*)["\']',
                        r'href=["\']([^"\']*glassdoor\.com[^"\']*)["\']'
                    ]

                    for pattern in job_link_patterns:
                        matches = re.findall(pattern, content, re.IGNORECASE)
                        result['job_links'].extend(matches)

                    # Look for external job board links
                    external_patterns = [
                        r'(https?://[^"\s]*(?:linkedin|indeed|glassdoor|monster|ziprecruiter|greenhouse|lever|bamboohr|smartrecruiters|jobvite|taleo|icims|workday|myworkday)\.(?:com|co|net|io)[^"\s]*)',
                    ]

                    for pattern in external_patterns:
                        matches = re.findall(pattern, content, re.IGNORECASE)
                        result['external_links'].extend(matches)

                    # Look for company names
                    company_patterns = [
                        r'(?i)\b(google|microsoft|amazon|apple|facebook|meta|netflix|tesla|uber|airbnb|spotify|slack|zoom|salesforce|oracle|ibm|intel|nvidia|adobe|twitter|linkedin|snapchat|pinterest|dropbox|stripe|square|palantir|databricks|figma|notion|discord|robinhood|coinbase|doordash|instacart|peloton)\b'
                    ]

                    for pattern in company_patterns:
                        matches = re.findall(pattern, content, re.IGNORECASE)
                        result['company_mentions'].extend(matches)

                    # Look for job titles
                    job_title_patterns = [
                        r'(?i)\b(software engineer|data scientist|product manager|designer|developer|programmer|analyst|architect|consultant|manager|director|lead|senior|junior|intern)\b[^.]*?(engineer|scientist|manager|designer|developer|analyst|architect|consultant)',
                    ]

                    for pattern in job_title_patterns:
                        matches = re.findall(pattern, content, re.IGNORECASE)
                        result['job_titles'].extend([f"{m[0]} {m[1]}" for m in matches])

                    # Deduplicate
                    result['job_links'] = list(set(result['job_links']))
                    result['external_links'] = list(set(result['external_links']))
                    result['company_mentions'] = list(set(result['company_mentions']))
                    result['job_titles'] = list(set(result['job_titles']))

                    logger.info(f"  Found {len(result['job_links'])} job links, {len(result['external_links'])} external links")

                results.append(result)

            except Exception as e:
                logger.warning(f"Failed to check {page}: {e}")
                results.append({
                    'page': page,
                    'error': str(e)
                })

        return results

    def search_for_hidden_apis(self):
        """Search for hidden API endpoints"""
        logger.info("Searching for hidden API endpoints...")

        # Try to find API endpoints mentioned in JavaScript or HTML
        main_page_response = self.session.get(self.base_url)
        content = main_page_response.text

        # Look for API endpoints in the content
        api_patterns = [
            r'["\']([^"\']*api[^"\']*)["\']',
            r'fetch\(["\']([^"\']*)["\']',
            r'axios\.[get|post]+\(["\']([^"\']*)["\']',
            r'url:\s*["\']([^"\']*)["\']',
            r'endpoint:\s*["\']([^"\']*)["\']'
        ]

        potential_apis = set()
        for pattern in api_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            for match in matches:
                if 'api' in match.lower() or match.startswith('/'):
                    potential_apis.add(match)

        # Test potential APIs
        api_results = []
        for api_path in list(potential_apis)[:10]:  # Test first 10
            try:
                if api_path.startswith('/'):
                    url = urljoin(self.base_url, api_path)
                elif api_path.startswith('http'):
                    url = api_path
                else:
                    continue

                response = self.session.get(url, timeout=10)
                api_results.append({
                    'api_path': api_path,
                    'url': url,
                    'status_code': response.status_code,
                    'content_type': response.headers.get('content-type', ''),
                    'content_length': len(response.content)
                })

                if response.status_code == 200:
                    logger.info(f"Working API found: {url}")

            except Exception as e:
                logger.debug(f"API {api_path} failed: {e}")

        return api_results

    def create_dummy_job_data(self):
        """Create example job data to demonstrate the format"""
        logger.info("Creating example job data format...")

        example_jobs = [
            {
                "title": "Senior Software Engineer",
                "company": "TechCorp Inc.",
                "location": "San Francisco, CA",
                "type": "Full-time",
                "description": "Join our team as a Senior Software Engineer working on cutting-edge technology...",
                "requirements": ["5+ years experience", "Python/Java expertise", "System design skills"],
                "apply_url": "https://example-company.com/careers/senior-software-engineer",
                "salary_range": "$150,000 - $200,000",
                "posted_date": "2025-09-20",
                "job_id": "SE-2025-001"
            },
            {
                "title": "Data Scientist",
                "company": "DataAnalytics Pro",
                "location": "New York, NY",
                "type": "Full-time",
                "description": "Looking for a Data Scientist to drive insights from large datasets...",
                "requirements": ["MS in Data Science", "Machine Learning experience", "Python/R"],
                "apply_url": "https://example-data-company.com/jobs/data-scientist",
                "salary_range": "$120,000 - $180,000",
                "posted_date": "2025-09-19",
                "job_id": "DS-2025-042"
            },
            {
                "title": "Product Manager",
                "company": "InnovateNow",
                "location": "Austin, TX",
                "type": "Full-time",
                "description": "Lead product strategy and roadmap for our flagship application...",
                "requirements": ["3+ years PM experience", "Technical background", "Agile methodology"],
                "apply_url": "https://example-innovate.com/careers/product-manager",
                "salary_range": "$130,000 - $170,000",
                "posted_date": "2025-09-18",
                "job_id": "PM-2025-015"
            }
        ]

        return example_jobs

    def run_final_aggregation(self):
        """Run final aggregation of all job data"""
        logger.info("Running final job data aggregation...")

        results = {
            'timestamp': datetime.now().isoformat(),
            'extraction_summary': {
                'methods_attempted': [
                    'Basic HTML scraping',
                    'JavaScript content extraction',
                    'API endpoint discovery',
                    'Selenium automation (attempted)',
                    'Authentication flow analysis',
                    'Sitemap analysis',
                    'Alternative page exploration',
                    'Hidden API search'
                ],
                'authentication_required': True,
                'public_job_data_available': False,
                'recommendation': 'Site requires user authentication for job recommendations'
            },
            'alternative_pages': self.try_alternative_job_pages(),
            'hidden_apis': self.search_for_hidden_apis(),
            'example_job_format': self.create_dummy_job_data(),
            'consolidated_findings': {
                'external_job_links': [],
                'company_mentions': [],
                'job_titles': [],
                'working_endpoints': []
            }
        }

        # Consolidate findings
        for page_result in results['alternative_pages']:
            if 'error' not in page_result:
                results['consolidated_findings']['external_job_links'].extend(page_result.get('external_links', []))
                results['consolidated_findings']['company_mentions'].extend(page_result.get('company_mentions', []))
                results['consolidated_findings']['job_titles'].extend(page_result.get('job_titles', []))

        for api_result in results['hidden_apis']:
            if api_result.get('status_code') == 200:
                results['consolidated_findings']['working_endpoints'].append(api_result['url'])

        # Deduplicate
        for key in results['consolidated_findings']:
            if isinstance(results['consolidated_findings'][key], list):
                results['consolidated_findings'][key] = list(set(results['consolidated_findings'][key]))

        results['final_stats'] = {
            'total_external_links': len(results['consolidated_findings']['external_job_links']),
            'total_companies_mentioned': len(results['consolidated_findings']['company_mentions']),
            'total_job_titles_found': len(results['consolidated_findings']['job_titles']),
            'working_endpoints_found': len(results['consolidated_findings']['working_endpoints'])
        }

        logger.info(f"Final aggregation complete!")
        return results

    def save_comprehensive_report(self, results):
        """Save comprehensive final report"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # JSON file
        json_file = f"/home/calelin/awesome-apply/jobright_final_report_{timestamp}.json"
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)

        # Comprehensive text report
        txt_file = f"/home/calelin/awesome-apply/jobright_comprehensive_report_{timestamp}.txt"
        with open(txt_file, 'w', encoding='utf-8') as f:
            f.write("JOBRIGHT.AI COMPREHENSIVE EXTRACTION REPORT\n")
            f.write("="*60 + "\n")
            f.write(f"Report Generated: {results['timestamp']}\n")
            f.write(f"Analysis Target: https://jobright.ai/jobs/recommend\n\n")

            # Executive Summary
            f.write("EXECUTIVE SUMMARY:\n")
            f.write("-" * 30 + "\n")
            summary = results['extraction_summary']
            f.write(f"Authentication Required: {'Yes' if summary['authentication_required'] else 'No'}\n")
            f.write(f"Public Job Data Available: {'Yes' if summary['public_job_data_available'] else 'No'}\n")
            f.write(f"Methods Attempted: {len(summary['methods_attempted'])}\n")
            f.write(f"Recommendation: {summary['recommendation']}\n\n")

            # Key Findings
            stats = results['final_stats']
            f.write("KEY FINDINGS:\n")
            f.write("-" * 30 + "\n")
            f.write(f"External Job Links Found: {stats['total_external_links']}\n")
            f.write(f"Companies Mentioned: {stats['total_companies_mentioned']}\n")
            f.write(f"Job Titles Identified: {stats['total_job_titles_found']}\n")
            f.write(f"Working Endpoints: {stats['working_endpoints_found']}\n\n")

            # External Links
            if results['consolidated_findings']['external_job_links']:
                f.write("EXTERNAL JOB BOARD LINKS:\n")
                f.write("-" * 30 + "\n")
                for i, link in enumerate(results['consolidated_findings']['external_job_links'], 1):
                    f.write(f"{i:2d}. {link}\n")
                f.write("\n")

            # Companies Mentioned
            if results['consolidated_findings']['company_mentions']:
                f.write("COMPANIES MENTIONED:\n")
                f.write("-" * 30 + "\n")
                for company in sorted(results['consolidated_findings']['company_mentions']):
                    f.write(f"• {company}\n")
                f.write("\n")

            # Job Titles
            if results['consolidated_findings']['job_titles']:
                f.write("JOB TITLES FOUND:\n")
                f.write("-" * 30 + "\n")
                for title in sorted(set(results['consolidated_findings']['job_titles'])):
                    f.write(f"• {title}\n")
                f.write("\n")

            # Methods Attempted
            f.write("EXTRACTION METHODS ATTEMPTED:\n")
            f.write("-" * 30 + "\n")
            for i, method in enumerate(summary['methods_attempted'], 1):
                f.write(f"{i:2d}. {method}\n")
            f.write("\n")

            # Alternative Pages Tested
            f.write("ALTERNATIVE PAGES TESTED:\n")
            f.write("-" * 30 + "\n")
            for page_result in results['alternative_pages']:
                if 'error' not in page_result:
                    f.write(f"{page_result['page']}: {page_result['status_code']} ")
                    f.write(f"({len(page_result.get('job_links', []))} job links, ")
                    f.write(f"{len(page_result.get('external_links', []))} external links)\n")
                else:
                    f.write(f"{page_result['page']}: ERROR - {page_result['error']}\n")
            f.write("\n")

            # Recommendations for Users
            f.write("RECOMMENDATIONS FOR ACCESSING JOBRIGHT.AI JOBS:\n")
            f.write("-" * 30 + "\n")
            f.write("1. Create a free account at https://jobright.ai\n")
            f.write("2. Use OAuth login (Google, LinkedIn, etc.) if available\n")
            f.write("3. Navigate to /jobs/recommend after authentication\n")
            f.write("4. Use browser developer tools to monitor network requests\n")
            f.write("5. Look for API calls that return job data\n")
            f.write("6. Consider using browser automation tools like Selenium with login\n\n")

            # Example Job Data Format
            f.write("EXAMPLE JOB DATA FORMAT:\n")
            f.write("-" * 30 + "\n")
            f.write("The following shows the expected format for job data:\n\n")
            for i, job in enumerate(results['example_job_format'], 1):
                f.write(f"Job {i}:\n")
                f.write(f"  Title: {job['title']}\n")
                f.write(f"  Company: {job['company']}\n")
                f.write(f"  Location: {job['location']}\n")
                f.write(f"  Apply URL: {job['apply_url']}\n")
                f.write(f"  Salary: {job['salary_range']}\n\n")

        # HTML report with enhanced formatting
        html_file = f"/home/calelin/awesome-apply/jobright_final_report_{timestamp}.html"
        with open(html_file, 'w', encoding='utf-8') as f:
            f.write("""<!DOCTYPE html>
<html>
<head>
    <title>JobRight.ai Comprehensive Extraction Report</title>
    <style>
        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; margin: 20px; line-height: 1.6; }
        .header { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; border-radius: 10px; margin-bottom: 30px; }
        .section { background: #f8f9fa; padding: 20px; margin: 20px 0; border-radius: 8px; border-left: 4px solid #007acc; }
        .warning { background: #fff3cd; border-left-color: #ffc107; padding: 15px; border-radius: 5px; margin: 15px 0; }
        .success { background: #d4edda; border-left-color: #28a745; padding: 15px; border-radius: 5px; margin: 15px 0; }
        .stats { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; margin: 20px 0; }
        .stat-box { background: white; border: 1px solid #dee2e6; padding: 20px; border-radius: 8px; text-align: center; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        .stat-number { font-size: 2em; font-weight: bold; color: #007acc; }
        .links-section { background: #e8f4fd; padding: 20px; border-radius: 8px; margin: 20px 0; }
        ul { padding-left: 20px; }
        li { margin: 8px 0; }
        a { color: #007acc; text-decoration: none; }
        a:hover { text-decoration: underline; }
        .method-list { background: #f1f3f4; padding: 15px; border-radius: 5px; }
        .code { background: #f8f9fa; padding: 10px; border-radius: 4px; font-family: monospace; margin: 10px 0; }
    </style>
</head>
<body>""")

            f.write(f"""
<div class="header">
    <h1>🔍 JobRight.ai Comprehensive Extraction Report</h1>
    <p><strong>Generated:</strong> {results['timestamp']}</p>
    <p><strong>Target:</strong> https://jobright.ai/jobs/recommend</p>
</div>

<div class="warning">
    <h3>⚠️ Key Finding</h3>
    <p><strong>Authentication Required:</strong> JobRight.ai requires user login to access job recommendations. Public scraping of job data is not possible without authentication.</p>
</div>
""")

            # Statistics
            stats = results['final_stats']
            f.write('<div class="stats">')
            f.write(f'<div class="stat-box"><div class="stat-number">{stats["total_external_links"]}</div><div>External Job Links</div></div>')
            f.write(f'<div class="stat-box"><div class="stat-number">{stats["total_companies_mentioned"]}</div><div>Companies Found</div></div>')
            f.write(f'<div class="stat-box"><div class="stat-number">{stats["total_job_titles_found"]}</div><div>Job Titles</div></div>')
            f.write(f'<div class="stat-box"><div class="stat-number">{len(results["extraction_summary"]["methods_attempted"])}</div><div>Methods Tried</div></div>')
            f.write('</div>')

            # External links if any
            if results['consolidated_findings']['external_job_links']:
                f.write('<div class="links-section">')
                f.write('<h3>🔗 External Job Board Links Found</h3>')
                f.write('<ul>')
                for link in results['consolidated_findings']['external_job_links']:
                    f.write(f'<li><a href="{link}" target="_blank">{link}</a></li>')
                f.write('</ul>')
                f.write('</div>')

            # Methods attempted
            f.write('<div class="section">')
            f.write('<h3>🛠️ Extraction Methods Attempted</h3>')
            f.write('<div class="method-list">')
            for i, method in enumerate(results['extraction_summary']['methods_attempted'], 1):
                f.write(f'<p>{i}. {method}</p>')
            f.write('</div>')
            f.write('</div>')

            # Companies and job titles
            if results['consolidated_findings']['company_mentions']:
                f.write('<div class="section">')
                f.write('<h3>🏢 Companies Mentioned</h3>')
                f.write('<p>' + ', '.join(sorted(results['consolidated_findings']['company_mentions'])) + '</p>')
                f.write('</div>')

            if results['consolidated_findings']['job_titles']:
                f.write('<div class="section">')
                f.write('<h3>💼 Job Titles Found</h3>')
                f.write('<ul>')
                for title in sorted(set(results['consolidated_findings']['job_titles'])):
                    f.write(f'<li>{title}</li>')
                f.write('</ul>')
                f.write('</div>')

            # Recommendations
            f.write('<div class="success">')
            f.write('<h3>✅ Recommendations for Accessing Job Data</h3>')
            f.write('<ol>')
            f.write('<li>Create a free account at <a href="https://jobright.ai" target="_blank">jobright.ai</a></li>')
            f.write('<li>Use OAuth login (Google, LinkedIn, etc.) if available</li>')
            f.write('<li>Navigate to the recommendations page after authentication</li>')
            f.write('<li>Use browser developer tools to monitor network requests for API calls</li>')
            f.write('<li>Consider using Selenium with proper authentication for automated access</li>')
            f.write('</ol>')
            f.write('</div>')

            f.write('</body></html>')

        return json_file, txt_file, html_file

def main():
    aggregator = FinalJobAggregator()
    results = aggregator.run_final_aggregation()
    json_file, txt_file, html_file = aggregator.save_comprehensive_report(results)

    print(f"\n🎯 FINAL JOBRIGHT.AI EXTRACTION REPORT")
    print(f"="*50)
    print(f"Authentication Required: {'Yes' if results['extraction_summary']['authentication_required'] else 'No'}")
    print(f"Public Job Data: {'Yes' if results['extraction_summary']['public_job_data_available'] else 'No'}")
    print(f"Methods Attempted: {len(results['extraction_summary']['methods_attempted'])}")

    stats = results['final_stats']
    print(f"\n📊 FINDINGS SUMMARY:")
    print(f"   External Job Links: {stats['total_external_links']}")
    print(f"   Companies Mentioned: {stats['total_companies_mentioned']}")
    print(f"   Job Titles Found: {stats['total_job_titles_found']}")
    print(f"   Working Endpoints: {stats['working_endpoints_found']}")

    print(f"\n📁 COMPREHENSIVE REPORTS GENERATED:")
    print(f"   📄 JSON Data: {json_file}")
    print(f"   📝 Text Report: {txt_file}")
    print(f"   🌐 HTML Report: {html_file}")

    print(f"\n💡 CONCLUSION:")
    print(f"   JobRight.ai requires user authentication to access job recommendations.")
    print(f"   To extract job data, you would need to:")
    print(f"   1. Create an account at jobright.ai")
    print(f"   2. Use authenticated browser automation (Selenium with login)")
    print(f"   3. Monitor network requests to find the API endpoints after login")

if __name__ == "__main__":
    main()