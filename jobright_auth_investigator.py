#!/usr/bin/env python3
"""
JobRight.ai Authentication and Access Investigator
Determines if the site requires login and attempts to find public job data
"""

import requests
import json
import re
from urllib.parse import urljoin, urlparse
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class JobRightAuthInvestigator:
    def __init__(self):
        self.base_url = "https://jobright.ai"
        self.session = requests.Session()

        # More realistic browser headers
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        })

    def check_main_site(self):
        """Check the main site for available information"""
        logger.info("Checking main site structure...")

        try:
            response = self.session.get(self.base_url)
            response.raise_for_status()

            content = response.text

            # Look for authentication indicators
            auth_indicators = [
                'login', 'signin', 'sign-in', 'authenticate', 'auth',
                'register', 'signup', 'sign-up', 'account'
            ]

            requires_auth = any(indicator in content.lower() for indicator in auth_indicators)

            # Look for public job links
            job_links = []
            patterns = [
                r'href=["\']([^"\']*job[^"\']*)["\']',
                r'href=["\']([^"\']*career[^"\']*)["\']',
                r'href=["\']([^"\']*position[^"\']*)["\']'
            ]

            for pattern in patterns:
                matches = re.findall(pattern, content, re.IGNORECASE)
                job_links.extend(matches)

            return {
                'url': self.base_url,
                'status_code': response.status_code,
                'content_length': len(content),
                'likely_requires_auth': requires_auth,
                'job_links_found': len(set(job_links)),
                'job_links': list(set(job_links)),
                'title': re.search(r'<title>(.*?)</title>', content, re.IGNORECASE).group(1) if re.search(r'<title>(.*?)</title>', content) else "No title"
            }

        except Exception as e:
            logger.error(f"Error checking main site: {e}")
            return None

    def try_public_endpoints(self):
        """Try various public endpoints that might contain job data"""
        logger.info("Trying public endpoints...")

        public_endpoints = [
            "/", "/jobs", "/careers", "/positions", "/search",
            "/public/jobs", "/api/public", "/feed", "/rss",
            "/sitemap.xml", "/robots.txt", "/api/health",
            "/browse", "/explore", "/listings"
        ]

        results = []

        for endpoint in public_endpoints:
            try:
                url = urljoin(self.base_url, endpoint)
                response = self.session.get(url, timeout=10)

                result = {
                    'endpoint': endpoint,
                    'url': url,
                    'status_code': response.status_code,
                    'content_type': response.headers.get('content-type', ''),
                    'content_length': len(response.content),
                    'accessible': response.status_code == 200
                }

                if response.status_code == 200:
                    content = response.text

                    # Check if it contains job data
                    job_indicators = ['job', 'position', 'career', 'employment', 'hiring']
                    job_content = sum(1 for indicator in job_indicators if indicator in content.lower())
                    result['job_content_score'] = job_content

                    # Look for structured data
                    if 'application/json' in response.headers.get('content-type', ''):
                        try:
                            json_data = response.json()
                            result['json_data'] = json_data
                        except:
                            pass

                    # Look for specific job-related patterns
                    if job_content > 0:
                        job_patterns = [
                            r'(?i)(software engineer|developer|programmer)',
                            r'(?i)(data scientist|analyst)',
                            r'(?i)(product manager|project manager)',
                            r'(?i)(marketing|sales)',
                            r'(?i)(designer|ui/ux)'
                        ]

                        job_matches = []
                        for pattern in job_patterns:
                            matches = re.findall(pattern, content[:5000])  # Check first 5000 chars
                            job_matches.extend(matches)

                        result['job_titles_found'] = len(job_matches)
                        result['sample_job_titles'] = job_matches[:10]

                results.append(result)
                logger.info(f"Endpoint {endpoint}: {response.status_code}")

            except Exception as e:
                results.append({
                    'endpoint': endpoint,
                    'error': str(e)
                })

        return results

    def analyze_authentication_flow(self):
        """Analyze how authentication works on the site"""
        logger.info("Analyzing authentication flow...")

        # Look for login/auth endpoints
        auth_endpoints = [
            "/login", "/signin", "/auth", "/authenticate",
            "/api/auth", "/api/login", "/oauth", "/sso"
        ]

        auth_analysis = {
            'auth_endpoints': [],
            'oauth_providers': [],
            'signup_available': False,
            'guest_access': False
        }

        for endpoint in auth_endpoints:
            try:
                url = urljoin(self.base_url, endpoint)
                response = self.session.get(url, timeout=10)

                if response.status_code in [200, 302, 401]:
                    auth_analysis['auth_endpoints'].append({
                        'endpoint': endpoint,
                        'status': response.status_code,
                        'redirect': response.headers.get('location') if response.status_code == 302 else None
                    })

                    if response.status_code == 200:
                        content = response.text

                        # Look for OAuth providers
                        oauth_patterns = [
                            r'google', r'linkedin', r'facebook', r'github',
                            r'microsoft', r'apple', r'twitter'
                        ]

                        for provider in oauth_patterns:
                            if provider in content.lower():
                                auth_analysis['oauth_providers'].append(provider)

                        # Check for guest access
                        if any(term in content.lower() for term in ['guest', 'demo', 'preview', 'trial']):
                            auth_analysis['guest_access'] = True

                        # Check for signup
                        if any(term in content.lower() for term in ['register', 'signup', 'sign up', 'create account']):
                            auth_analysis['signup_available'] = True

            except Exception as e:
                logger.debug(f"Auth endpoint {endpoint} failed: {e}")

        return auth_analysis

    def search_for_job_data_apis(self):
        """Search for job data in various API formats"""
        logger.info("Searching for job data APIs...")

        # Try different API patterns and formats
        api_patterns = [
            ("/api/jobs", {}),
            ("/api/search", {"q": "software engineer"}),
            ("/api/recommendations", {}),
            ("/feed/jobs", {}),
            ("/export/jobs", {}),
            ("/data/jobs.json", {}),
            ("/jobs.json", {}),
            ("/api/public/jobs", {}),
            ("/api/v1/search", {"query": "developer"}),
            ("/graphql", {"query": "{ jobs { title company } }"})
        ]

        api_results = []

        for api_path, params in api_patterns:
            try:
                url = urljoin(self.base_url, api_path)

                # Try both GET and POST
                for method in ['GET', 'POST']:
                    try:
                        if method == 'GET':
                            response = self.session.get(url, params=params, timeout=10)
                        else:
                            response = self.session.post(url, json=params, timeout=10)

                        result = {
                            'api_path': api_path,
                            'method': method,
                            'status_code': response.status_code,
                            'content_type': response.headers.get('content-type', ''),
                            'content_length': len(response.content)
                        }

                        if response.status_code == 200:
                            # Try to parse as JSON
                            try:
                                json_data = response.json()
                                result['json_data'] = json_data
                                result['has_job_data'] = self.contains_job_data(json_data)
                            except:
                                result['has_job_data'] = self.contains_job_data(response.text)

                        api_results.append(result)

                        if response.status_code == 200:
                            logger.info(f"API success: {method} {api_path} -> {response.status_code}")

                    except Exception as e:
                        logger.debug(f"API {method} {api_path} failed: {e}")

            except Exception as e:
                logger.debug(f"API pattern {api_path} failed: {e}")

        return api_results

    def contains_job_data(self, data):
        """Check if data contains job information"""
        data_str = str(data).lower()
        job_indicators = [
            'title', 'company', 'description', 'salary', 'location',
            'requirements', 'skills', 'experience', 'employment',
            'position', 'role', 'job', 'career', 'hire', 'apply'
        ]

        score = sum(1 for indicator in job_indicators if indicator in data_str)
        return score >= 3  # Require at least 3 job-related terms

    def check_alternative_access_methods(self):
        """Check for alternative ways to access job data"""
        logger.info("Checking alternative access methods...")

        alternatives = {
            'rss_feeds': [],
            'sitemaps': [],
            'public_exports': [],
            'partner_apis': []
        }

        # Check for RSS feeds
        rss_paths = ["/feed", "/rss", "/jobs.rss", "/jobs/feed", "/api/feed"]
        for path in rss_paths:
            try:
                url = urljoin(self.base_url, path)
                response = self.session.get(url, timeout=10)
                if response.status_code == 200 and 'xml' in response.headers.get('content-type', ''):
                    alternatives['rss_feeds'].append(url)
            except:
                pass

        # Check for sitemaps
        sitemap_paths = ["/sitemap.xml", "/sitemap_jobs.xml", "/jobs/sitemap.xml"]
        for path in sitemap_paths:
            try:
                url = urljoin(self.base_url, path)
                response = self.session.get(url, timeout=10)
                if response.status_code == 200:
                    alternatives['sitemaps'].append(url)
            except:
                pass

        return alternatives

    def run_complete_investigation(self):
        """Run complete investigation of JobRight.ai access methods"""
        logger.info("Starting complete JobRight.ai investigation...")

        investigation = {
            'timestamp': datetime.now().isoformat(),
            'main_site': self.check_main_site(),
            'public_endpoints': self.try_public_endpoints(),
            'authentication': self.analyze_authentication_flow(),
            'api_search': self.search_for_job_data_apis(),
            'alternatives': self.check_alternative_access_methods()
        }

        # Analyze results
        accessible_endpoints = [ep for ep in investigation['public_endpoints'] if ep.get('accessible', False)]
        job_content_endpoints = [ep for ep in accessible_endpoints if ep.get('job_content_score', 0) > 0]
        working_apis = [api for api in investigation['api_search'] if api.get('status_code') == 200]

        investigation['summary'] = {
            'total_endpoints_checked': len(investigation['public_endpoints']),
            'accessible_endpoints': len(accessible_endpoints),
            'endpoints_with_job_content': len(job_content_endpoints),
            'working_apis': len(working_apis),
            'authentication_required': investigation['main_site']['likely_requires_auth'] if investigation['main_site'] else True,
            'alternative_access_available': len(investigation['alternatives']['rss_feeds']) > 0 or len(investigation['alternatives']['sitemaps']) > 0
        }

        return investigation

    def save_investigation_results(self, investigation):
        """Save investigation results"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # JSON file
        json_file = f"/home/calelin/awesome-apply/jobright_investigation_{timestamp}.json"
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(investigation, f, indent=2, ensure_ascii=False)

        # Summary report
        report_file = f"/home/calelin/awesome-apply/jobright_access_report_{timestamp}.txt"
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write("JobRight.ai Access Investigation Report\n")
            f.write("="*50 + "\n")
            f.write(f"Investigation Date: {investigation['timestamp']}\n\n")

            summary = investigation['summary']
            f.write("SUMMARY:\n")
            f.write(f"  Authentication Required: {'Yes' if summary['authentication_required'] else 'No'}\n")
            f.write(f"  Accessible Endpoints: {summary['accessible_endpoints']}/{summary['total_endpoints_checked']}\n")
            f.write(f"  Endpoints with Job Content: {summary['endpoints_with_job_content']}\n")
            f.write(f"  Working APIs: {summary['working_apis']}\n")
            f.write(f"  Alternative Access: {'Available' if summary['alternative_access_available'] else 'Not Found'}\n\n")

            # Accessible endpoints
            f.write("ACCESSIBLE ENDPOINTS:\n")
            f.write("-" * 30 + "\n")
            for ep in investigation['public_endpoints']:
                if ep.get('accessible', False):
                    f.write(f"  {ep['endpoint']} -> {ep['status_code']} (Job Score: {ep.get('job_content_score', 0)})\n")

            # Working APIs
            f.write(f"\nWORKING APIs:\n")
            f.write("-" * 30 + "\n")
            for api in investigation['api_search']:
                if api.get('status_code') == 200:
                    f.write(f"  {api['method']} {api['api_path']} -> {api['status_code']}\n")
                    if api.get('has_job_data'):
                        f.write(f"    Contains job data: Yes\n")

            # Authentication info
            auth = investigation['authentication']
            f.write(f"\nAUTHENTICATION:\n")
            f.write("-" * 30 + "\n")
            f.write(f"  Auth Endpoints: {len(auth['auth_endpoints'])}\n")
            f.write(f"  OAuth Providers: {', '.join(auth['oauth_providers']) if auth['oauth_providers'] else 'None'}\n")
            f.write(f"  Signup Available: {'Yes' if auth['signup_available'] else 'No'}\n")
            f.write(f"  Guest Access: {'Yes' if auth['guest_access'] else 'No'}\n")

            # Recommendations
            f.write(f"\nRECOMMENDATIONS:\n")
            f.write("-" * 30 + "\n")
            if summary['authentication_required']:
                f.write("• The site appears to require authentication to access job recommendations\n")
                if auth['signup_available']:
                    f.write("• Account registration is available\n")
                if auth['oauth_providers']:
                    f.write(f"• OAuth login available via: {', '.join(auth['oauth_providers'])}\n")

            if summary['endpoints_with_job_content'] > 0:
                f.write("• Some job content was found in public endpoints\n")

            if summary['alternative_access_available']:
                f.write("• Alternative access methods (RSS/Sitemap) are available\n")
            else:
                f.write("• No alternative access methods found\n")

        return json_file, report_file

def main():
    investigator = JobRightAuthInvestigator()
    investigation = investigator.run_complete_investigation()
    json_file, report_file = investigator.save_investigation_results(investigation)

    print(f"\nJobRight.ai Investigation Complete!")
    print(f"Files created:")
    print(f"  📊 Detailed Results: {json_file}")
    print(f"  📋 Summary Report: {report_file}")

    summary = investigation['summary']
    print(f"\nKey Findings:")
    print(f"  🔐 Authentication Required: {'Yes' if summary['authentication_required'] else 'No'}")
    print(f"  🌐 Accessible Endpoints: {summary['accessible_endpoints']}")
    print(f"  💼 Job Content Found: {summary['endpoints_with_job_content']} endpoints")
    print(f"  🔌 Working APIs: {summary['working_apis']}")

    if summary['authentication_required']:
        print(f"\n⚠️  The site likely requires user authentication to access job recommendations.")
        print(f"   Consider creating an account or using OAuth login to access full job data.")

    if summary['endpoints_with_job_content'] > 0:
        print(f"\n✅ Found some job content in public areas!")

    if not summary['alternative_access_available']:
        print(f"\n❌ No public APIs or feeds found for job data access.")

if __name__ == "__main__":
    main()