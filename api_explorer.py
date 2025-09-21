#!/usr/bin/env python3
"""
API Explorer for JobRight.ai
Attempts to discover and interact with API endpoints
"""

import requests
import json
import time
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class JobRightAPIExplorer:
    def __init__(self):
        self.base_url = "https://jobright.ai"
        self.session = requests.Session()

        # Set realistic headers
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Referer': 'https://jobright.ai/jobs/recommend',
            'Origin': 'https://jobright.ai',
        })

    def explore_api_endpoint(self, endpoint):
        """Explore a specific API endpoint"""
        logger.info(f"Exploring API endpoint: {endpoint}")

        results = {
            'endpoint': endpoint,
            'methods_tested': {},
            'timestamp': datetime.now().isoformat()
        }

        # Try different HTTP methods
        methods = ['GET', 'POST', 'OPTIONS']

        for method in methods:
            try:
                if method == 'GET':
                    response = self.session.get(endpoint, timeout=10)
                elif method == 'POST':
                    response = self.session.post(endpoint, json={}, timeout=10)
                elif method == 'OPTIONS':
                    response = self.session.options(endpoint, timeout=10)

                results['methods_tested'][method] = {
                    'status_code': response.status_code,
                    'headers': dict(response.headers),
                    'content_type': response.headers.get('content-type', ''),
                    'content_length': len(response.content),
                    'content_preview': response.text[:1000] if response.text else ''
                }

                logger.info(f"{method} {endpoint}: {response.status_code}")

                # If we get JSON response, try to parse it
                if 'application/json' in response.headers.get('content-type', ''):
                    try:
                        json_data = response.json()
                        results['methods_tested'][method]['json_data'] = json_data
                        logger.info(f"Successfully parsed JSON response for {method}")
                    except:
                        pass

            except Exception as e:
                results['methods_tested'][method] = {
                    'error': str(e)
                }
                logger.warning(f"{method} {endpoint} failed: {e}")

        return results

    def try_api_variations(self):
        """Try various API endpoint patterns"""
        base_endpoints = [
            "/api/jobs",
            "/api/jobs/recommend",
            "/api/jobs/recommendations",
            "/api/v1/jobs",
            "/api/v1/jobs/recommend",
            "/api/v1/recommendations",
            "/jobs/api",
            "/jobs/api/recommend",
            "/recommend/api",
            "/api/search",
            "/api/search/jobs",
            "/graphql",
            "/api/graphql"
        ]

        all_results = []

        for endpoint_path in base_endpoints:
            full_url = self.base_url + endpoint_path
            results = self.explore_api_endpoint(full_url)
            all_results.append(results)

            # Add a small delay between requests
            time.sleep(0.5)

        return all_results

    def try_with_parameters(self, base_endpoint):
        """Try API endpoint with various parameters"""
        logger.info(f"Trying {base_endpoint} with parameters...")

        param_sets = [
            {},
            {'page': 1},
            {'limit': 20},
            {'page': 1, 'limit': 20},
            {'q': 'software engineer'},
            {'location': 'San Francisco'},
            {'query': 'developer'},
            {'search': 'python'},
            {'category': 'technology'},
            {'type': 'recommendation'},
            {'userId': 'test'},
            {'recommendations': 'true'}
        ]

        results = []

        for params in param_sets:
            try:
                response = self.session.get(base_endpoint, params=params, timeout=10)

                result = {
                    'parameters': params,
                    'status_code': response.status_code,
                    'url': response.url,
                    'content_length': len(response.content),
                    'content_type': response.headers.get('content-type', ''),
                    'content_preview': response.text[:500]
                }

                # Try to parse JSON
                if 'application/json' in response.headers.get('content-type', ''):
                    try:
                        result['json_data'] = response.json()
                    except:
                        pass

                results.append(result)
                logger.info(f"Params {params}: {response.status_code}")

            except Exception as e:
                results.append({
                    'parameters': params,
                    'error': str(e)
                })

            time.sleep(0.3)

        return results

    def analyze_known_endpoint(self):
        """Analyze the known /jobs/api endpoint"""
        endpoint = "https://jobright.ai/jobs/api"

        logger.info("Analyzing known /jobs/api endpoint...")

        # Basic exploration
        basic_results = self.explore_api_endpoint(endpoint)

        # Try with parameters
        param_results = self.try_with_parameters(endpoint)

        return {
            'basic_exploration': basic_results,
            'parameter_testing': param_results
        }

    def run_full_exploration(self):
        """Run complete API exploration"""
        logger.info("Starting full API exploration...")

        results = {
            'timestamp': datetime.now().isoformat(),
            'known_endpoint_analysis': self.analyze_known_endpoint(),
            'endpoint_variations': self.try_api_variations()
        }

        return results

    def save_results(self, results):
        """Save exploration results"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"/home/calelin/awesome-apply/api_exploration_{timestamp}.json"

        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)

        # Create summary
        summary_file = f"/home/calelin/awesome-apply/api_summary_{timestamp}.txt"
        with open(summary_file, 'w', encoding='utf-8') as f:
            f.write("JobRight.ai API Exploration Summary\n")
            f.write("="*50 + "\n")
            f.write(f"Timestamp: {results['timestamp']}\n\n")

            # Known endpoint analysis
            known = results['known_endpoint_analysis']
            f.write("KNOWN ENDPOINT ANALYSIS (/jobs/api):\n")
            f.write("-" * 30 + "\n")

            for method, data in known['basic_exploration']['methods_tested'].items():
                if 'error' not in data:
                    f.write(f"{method}: {data['status_code']} - {data['content_type']}\n")
                    if data.get('json_data'):
                        f.write(f"  JSON Response: Yes\n")
                    f.write(f"  Content Length: {data['content_length']}\n")
                else:
                    f.write(f"{method}: Error - {data['error']}\n")

            f.write(f"\nParameter Testing Results: {len(known['parameter_testing'])} combinations tested\n")

            # Working endpoints
            f.write("\nWORKING ENDPOINTS:\n")
            f.write("-" * 20 + "\n")

            for endpoint_result in results['endpoint_variations']:
                endpoint = endpoint_result['endpoint']
                for method, data in endpoint_result['methods_tested'].items():
                    if 'error' not in data and data['status_code'] == 200:
                        f.write(f"{method} {endpoint}: {data['status_code']}\n")
                        if data.get('json_data'):
                            f.write(f"  Has JSON data: {len(str(data['json_data']))} chars\n")

        return filename, summary_file

def main():
    explorer = JobRightAPIExplorer()
    results = explorer.run_full_exploration()
    json_file, summary_file = explorer.save_results(results)

    print(f"\nAPI Exploration Complete!")
    print(f"JSON Results: {json_file}")
    print(f"Summary: {summary_file}")

if __name__ == "__main__":
    main()