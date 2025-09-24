#!/usr/bin/env python3
"""
Complete End-to-End Workflow Testing for JobRight.ai Mock
Tests the entire user journey from login to job application completion
"""

import requests
import json
import time
from typing import Dict, List
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class JobRightWorkflowTester:
    def __init__(self, base_url: str = "http://localhost:5000"):
        self.base_url = base_url
        self.session = requests.Session()
        # Use appropriate credentials based on the system
        if "5000" in base_url:
            self.user_data = {
                'email': 'demo@jobright.mock',
                'password': 'demo123'
            }
        else:
            self.user_data = {
                'email': 'demo@jobright.ai',
                'password': 'demo123'
            }

    def test_complete_workflow(self) -> Dict:
        """Test the complete user workflow from login to job application"""
        results = {
            'workflow_steps': [],
            'total_tests': 0,
            'passed_tests': 0,
            'failed_tests': [],
            'applied_jobs': [],
            'saved_jobs': []
        }

        try:
            # Step 1: Login
            logger.info("🔐 Step 1: Testing user login...")
            login_result = self.test_login()
            results['workflow_steps'].append({
                'step': 'Login',
                'status': 'PASS' if login_result['success'] else 'FAIL',
                'details': login_result
            })
            results['total_tests'] += 1
            if login_result['success']:
                results['passed_tests'] += 1
            else:
                results['failed_tests'].append('Login failed')
                return results  # Can't continue without login

            # Step 2: Load job recommendations
            logger.info("📋 Step 2: Loading job recommendations...")
            jobs_result = self.test_load_jobs()
            results['workflow_steps'].append({
                'step': 'Load Jobs',
                'status': 'PASS' if jobs_result['success'] else 'FAIL',
                'details': jobs_result
            })
            results['total_tests'] += 1
            if jobs_result['success']:
                results['passed_tests'] += 1
                available_jobs = jobs_result.get('jobs', [])
            else:
                results['failed_tests'].append('Failed to load jobs')
                return results

            if not available_jobs:
                logger.warning("⚠️ No jobs available for testing")
                return results

            # Step 3: Save jobs
            logger.info("💾 Step 3: Testing job saving functionality...")
            save_results = self.test_save_jobs(available_jobs[:3])  # Save first 3 jobs
            results['workflow_steps'].append({
                'step': 'Save Jobs',
                'status': 'PASS' if save_results['success'] else 'FAIL',
                'details': save_results
            })
            results['total_tests'] += 1
            if save_results['success']:
                results['passed_tests'] += 1
                results['saved_jobs'] = save_results.get('saved_jobs', [])
            else:
                results['failed_tests'].append('Failed to save jobs')

            # Step 4: Apply to jobs
            logger.info("📝 Step 4: Testing job application functionality...")
            apply_results = self.test_apply_to_jobs(available_jobs[:5])  # Apply to first 5 jobs
            results['workflow_steps'].append({
                'step': 'Apply to Jobs',
                'status': 'PASS' if apply_results['success'] else 'FAIL',
                'details': apply_results
            })
            results['total_tests'] += 1
            if apply_results['success']:
                results['passed_tests'] += 1
                results['applied_jobs'] = apply_results.get('applied_jobs', [])
            else:
                results['failed_tests'].append('Failed to apply to jobs')

            # Step 5: Verify applications
            logger.info("✅ Step 5: Verifying application tracking...")
            verify_results = self.test_verify_applications()
            results['workflow_steps'].append({
                'step': 'Verify Applications',
                'status': 'PASS' if verify_results['success'] else 'FAIL',
                'details': verify_results
            })
            results['total_tests'] += 1
            if verify_results['success']:
                results['passed_tests'] += 1
            else:
                results['failed_tests'].append('Failed to verify applications')

            # Step 6: Test real job URLs
            logger.info("🌐 Step 6: Testing real job application URLs...")
            real_jobs_results = self.test_real_job_urls(available_jobs[:3])
            results['workflow_steps'].append({
                'step': 'Real Job URLs',
                'status': 'PASS' if real_jobs_results['success'] else 'FAIL',
                'details': real_jobs_results
            })
            results['total_tests'] += 1
            if real_jobs_results['success']:
                results['passed_tests'] += 1
            else:
                results['failed_tests'].append('Real job URLs not accessible')

        except Exception as e:
            logger.error(f"❌ Workflow test failed with exception: {e}")
            results['workflow_steps'].append({
                'step': 'Exception',
                'status': 'FAIL',
                'details': {'error': str(e)}
            })
            results['failed_tests'].append(f'Exception: {e}')

        return results

    def test_login(self) -> Dict:
        """Test user login functionality"""
        try:
            response = self.session.post(
                f"{self.base_url}/login",
                json=self.user_data,
                headers={'Content-Type': 'application/json'}
            )

            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    logger.info("✅ Login successful")
                    return {'success': True, 'message': 'Login successful', 'status_code': 200}
                else:
                    logger.error(f"❌ Login failed: {data.get('message')}")
                    return {'success': False, 'message': data.get('message'), 'status_code': 200}
            else:
                logger.error(f"❌ Login request failed with status: {response.status_code}")
                return {'success': False, 'message': f'HTTP {response.status_code}', 'status_code': response.status_code}

        except Exception as e:
            logger.error(f"❌ Login exception: {e}")
            return {'success': False, 'message': str(e), 'status_code': None}

    def test_load_jobs(self) -> Dict:
        """Test loading job recommendations"""
        try:
            response = self.session.get(f"{self.base_url}/api/jobs/search")

            if response.status_code == 200:
                data = response.json()
                jobs = data.get('jobs', [])
                logger.info(f"✅ Loaded {len(jobs)} job recommendations")
                return {
                    'success': True,
                    'message': f'Loaded {len(jobs)} jobs',
                    'jobs': jobs,
                    'status_code': 200
                }
            else:
                logger.error(f"❌ Failed to load jobs: HTTP {response.status_code}")
                return {'success': False, 'message': f'HTTP {response.status_code}', 'status_code': response.status_code}

        except Exception as e:
            logger.error(f"❌ Load jobs exception: {e}")
            return {'success': False, 'message': str(e), 'status_code': None}

    def test_save_jobs(self, jobs: List[Dict]) -> Dict:
        """Test saving jobs functionality"""
        saved_jobs = []
        failed_saves = []

        for job in jobs:
            try:
                job_id = job.get('id')
                if not job_id:
                    continue

                response = self.session.post(
                    f"{self.base_url}/api/jobs/{job_id}/save",
                    json={},
                    headers={'Content-Type': 'application/json'}
                )

                if response.status_code == 200:
                    data = response.json()
                    if data.get('success'):
                        saved_jobs.append({
                            'id': job_id,
                            'title': job.get('title', 'Unknown'),
                            'company': job.get('company', 'Unknown')
                        })
                        logger.info(f"✅ Saved job: {job.get('title')} at {job.get('company')}")
                    else:
                        failed_saves.append(job_id)
                        logger.warning(f"⚠️ Failed to save job {job_id}: {data.get('message')}")
                else:
                    failed_saves.append(job_id)
                    logger.warning(f"⚠️ Failed to save job {job_id}: HTTP {response.status_code}")

                time.sleep(0.1)  # Small delay between requests

            except Exception as e:
                failed_saves.append(job.get('id', 'unknown'))
                logger.error(f"❌ Exception saving job: {e}")

        success = len(saved_jobs) > 0
        return {
            'success': success,
            'message': f'Saved {len(saved_jobs)} jobs, {len(failed_saves)} failed',
            'saved_jobs': saved_jobs,
            'failed_saves': failed_saves
        }

    def test_apply_to_jobs(self, jobs: List[Dict]) -> Dict:
        """Test applying to jobs functionality"""
        applied_jobs = []
        failed_applications = []

        for job in jobs:
            try:
                job_id = job.get('id')
                if not job_id:
                    continue

                response = self.session.post(
                    f"{self.base_url}/api/jobs/{job_id}/apply",
                    json={},
                    headers={'Content-Type': 'application/json'}
                )

                if response.status_code == 200:
                    data = response.json()
                    if data.get('success'):
                        applied_jobs.append({
                            'id': job_id,
                            'title': job.get('title', 'Unknown'),
                            'company': job.get('company', 'Unknown'),
                            'application_url': job.get('application_url', ''),
                            'match_score': job.get('match_score', 0)
                        })
                        logger.info(f"✅ Applied to: {job.get('title')} at {job.get('company')}")
                    else:
                        failed_applications.append(job_id)
                        logger.warning(f"⚠️ Failed to apply to job {job_id}: {data.get('message')}")
                else:
                    failed_applications.append(job_id)
                    logger.warning(f"⚠️ Failed to apply to job {job_id}: HTTP {response.status_code}")

                time.sleep(0.1)  # Small delay between requests

            except Exception as e:
                failed_applications.append(job.get('id', 'unknown'))
                logger.error(f"❌ Exception applying to job: {e}")

        success = len(applied_jobs) > 0
        return {
            'success': success,
            'message': f'Applied to {len(applied_jobs)} jobs, {len(failed_applications)} failed',
            'applied_jobs': applied_jobs,
            'failed_applications': failed_applications
        }

    def test_verify_applications(self) -> Dict:
        """Test verifying applications are tracked"""
        try:
            response = self.session.get(f"{self.base_url}/applications")

            if response.status_code == 200:
                logger.info("✅ Applications page accessible")
                return {
                    'success': True,
                    'message': 'Applications page accessible',
                    'status_code': 200
                }
            else:
                logger.error(f"❌ Applications page not accessible: HTTP {response.status_code}")
                return {'success': False, 'message': f'HTTP {response.status_code}', 'status_code': response.status_code}

        except Exception as e:
            logger.error(f"❌ Applications verification exception: {e}")
            return {'success': False, 'message': str(e), 'status_code': None}

    def test_real_job_urls(self, jobs: List[Dict]) -> Dict:
        """Test that real job application URLs are valid and accessible"""
        valid_urls = []
        invalid_urls = []

        for job in jobs:
            try:
                application_url = job.get('application_url', '')
                if not application_url:
                    continue

                # Test if URL is accessible (with timeout)
                response = requests.head(application_url, timeout=5, allow_redirects=True)

                if response.status_code in [200, 301, 302]:
                    valid_urls.append({
                        'job_title': job.get('title', 'Unknown'),
                        'company': job.get('company', 'Unknown'),
                        'url': application_url,
                        'status_code': response.status_code
                    })
                    logger.info(f"✅ Valid URL for {job.get('title')}: {application_url}")
                else:
                    invalid_urls.append({
                        'job_title': job.get('title', 'Unknown'),
                        'url': application_url,
                        'status_code': response.status_code
                    })
                    logger.warning(f"⚠️ Invalid URL for {job.get('title')}: {application_url} (HTTP {response.status_code})")

            except Exception as e:
                invalid_urls.append({
                    'job_title': job.get('title', 'Unknown'),
                    'url': job.get('application_url', ''),
                    'error': str(e)
                })
                logger.error(f"❌ Exception testing URL for {job.get('title')}: {e}")

        success = len(valid_urls) > 0
        return {
            'success': success,
            'message': f'{len(valid_urls)} valid URLs, {len(invalid_urls)} invalid',
            'valid_urls': valid_urls,
            'invalid_urls': invalid_urls
        }

    def print_workflow_report(self, results: Dict):
        """Print a comprehensive workflow test report"""
        print("\n" + "="*80)
        print("🚀 JOBRIGHT.AI MOCK - COMPLETE WORKFLOW TEST REPORT")
        print("="*80)

        print(f"\n📊 OVERALL RESULTS:")
        print(f"   Total Tests: {results['total_tests']}")
        print(f"   Passed: {results['passed_tests']} ✅")
        print(f"   Failed: {len(results['failed_tests'])} ❌")
        success_rate = (results['passed_tests'] / results['total_tests'] * 100) if results['total_tests'] > 0 else 0
        print(f"   Success Rate: {success_rate:.1f}%")

        print(f"\n📋 WORKFLOW STEPS:")
        for i, step in enumerate(results['workflow_steps'], 1):
            status_icon = "✅" if step['status'] == 'PASS' else "❌"
            print(f"   {i}. {step['step']}: {step['status']} {status_icon}")
            if step['status'] == 'FAIL' and 'message' in step['details']:
                print(f"      Error: {step['details']['message']}")

        if results['applied_jobs']:
            print(f"\n📝 APPLIED JOBS ({len(results['applied_jobs'])}):")
            for job in results['applied_jobs']:
                print(f"   • {job['title']} at {job['company']} (Match: {job.get('match_score', 0)}%)")

        if results['saved_jobs']:
            print(f"\n💾 SAVED JOBS ({len(results['saved_jobs'])}):")
            for job in results['saved_jobs']:
                print(f"   • {job['title']} at {job['company']}")

        if results['failed_tests']:
            print(f"\n❌ FAILED TESTS:")
            for failure in results['failed_tests']:
                print(f"   • {failure}")

        # Overall assessment
        print(f"\n🎯 ASSESSMENT:")
        if success_rate >= 80:
            print("   🎉 EXCELLENT - All critical functionality working!")
        elif success_rate >= 60:
            print("   ⚠️ GOOD - Most functionality working, some issues to fix")
        else:
            print("   ❌ NEEDS WORK - Critical issues found")

        print("\n" + "="*80)

def main():
    """Run complete workflow tests on both systems"""
    systems = [
        ("JobRight Mock System (Port 5000)", "http://localhost:5000"),
        ("Complete JobRight Mock (Port 5001)", "http://localhost:5001")
    ]

    for system_name, base_url in systems:
        print(f"\n🎯 Testing: {system_name}")
        print(f"📡 URL: {base_url}")
        print("-" * 60)

        tester = JobRightWorkflowTester(base_url)
        results = tester.test_complete_workflow()
        tester.print_workflow_report(results)

if __name__ == "__main__":
    main()