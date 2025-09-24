#!/usr/bin/env python3
"""
Test Automated Job Applications - 10 Pages End-to-End
=====================================================

This script will:
1. Test sign-in functionality
2. Navigate to /jobs/recommend
3. Automatically apply to jobs on 10 different pages
4. Verify all applications are completed successfully
5. Generate detailed reports
"""

import sys
sys.path.append('/home/calelin/awesome-apply/venv/lib/python3.13/site-packages')

import requests
import time
import json
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class JobRightAutomatedTester:
    """Test automated job applications across multiple pages"""

    def __init__(self, base_url='http://localhost:5000'):
        self.base_url = base_url
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        self.total_applications = 0
        self.successful_applications = 0
        self.failed_applications = 0
        self.application_reports = []

    def test_sign_in(self):
        """Test sign-in functionality"""
        logger.info("🔐 Testing sign-in functionality...")

        # Test sign-in page
        response = self.session.get(f'{self.base_url}/login')
        if response.status_code != 200:
            logger.error(f"❌ Login page failed: {response.status_code}")
            return False

        logger.info("✅ Login page accessible")

        # Test demo user login
        login_data = {
            'email': 'demo@jobright.mock',
            'password': 'demo123'
        }

        response = self.session.post(
            f'{self.base_url}/login',
            json=login_data,
            headers={'Content-Type': 'application/json'}
        )

        if response.status_code == 200:
            result = response.json()
            if result.get('success'):
                logger.info("✅ Demo user login successful")
                return True
            else:
                logger.error(f"❌ Login failed: {result.get('message')}")
                return False
        else:
            logger.error(f"❌ Login request failed: {response.status_code}")
            return False

    def test_jobs_recommend_page(self):
        """Test /jobs/recommend page functionality"""
        logger.info("🏠 Testing /jobs/recommend page...")

        response = self.session.get(f'{self.base_url}/jobs/recommend')
        if response.status_code == 200:
            logger.info("✅ /jobs/recommend page accessible")
            return True
        else:
            logger.error(f"❌ /jobs/recommend page failed: {response.status_code}")
            return False

    def get_jobs_from_api(self, page=1):
        """Get jobs from the API for a specific page"""
        logger.info(f"📋 Fetching jobs from page {page}...")

        response = self.session.get(
            f'{self.base_url}/api/jobs/search',
            params={'page': page, 'per_page': 20}
        )

        if response.status_code == 200:
            data = response.json()
            jobs = data.get('jobs', [])
            logger.info(f"✅ Found {len(jobs)} jobs on page {page}")
            return jobs
        else:
            logger.error(f"❌ Failed to fetch jobs from page {page}: {response.status_code}")
            return []

    def apply_to_job(self, job_id, job_title, company):
        """Apply to a single job"""
        try:
            response = self.session.post(
                f'{self.base_url}/api/jobs/{job_id}/apply',
                headers={'Content-Type': 'application/json'}
            )

            if response.status_code == 200:
                result = response.json()
                if result.get('success'):
                    logger.info(f"✅ Applied to {job_title} at {company}")
                    self.successful_applications += 1
                    return True
                else:
                    message = result.get('message', 'Unknown error')
                    if 'already applied' in message.lower():
                        logger.info(f"⏭️ Already applied to {job_title} at {company}")
                        return True  # Count as success since we applied before
                    else:
                        logger.warning(f"⚠️ Application failed for {job_title} at {company}: {message}")
                        self.failed_applications += 1
                        return False
            else:
                logger.error(f"❌ HTTP error applying to {job_title} at {company}: {response.status_code}")
                self.failed_applications += 1
                return False

        except Exception as e:
            logger.error(f"❌ Exception applying to {job_title} at {company}: {e}")
            self.failed_applications += 1
            return False

    def bulk_apply_to_jobs(self, job_ids):
        """Apply to multiple jobs using bulk endpoint"""
        if not job_ids:
            return None

        logger.info(f"🚀 Bulk applying to {len(job_ids)} jobs...")

        try:
            response = self.session.post(
                f'{self.base_url}/api/jobs/apply-multiple',
                json={'job_ids': job_ids},
                headers={'Content-Type': 'application/json'}
            )

            if response.status_code == 200:
                result = response.json()
                if result.get('success'):
                    bulk_results = result.get('results', {})
                    successful = bulk_results.get('successful', 0)
                    failed = bulk_results.get('failed', 0)

                    logger.info(f"✅ Bulk application completed: {successful} successful, {failed} failed")
                    self.successful_applications += successful
                    self.failed_applications += failed
                    return {
                        'successful': successful,
                        'failed': failed,
                        'total': len(job_ids)
                    }
                else:
                    logger.error(f"❌ Bulk application failed: {result.get('message')}")
                    return None
            else:
                logger.error(f"❌ Bulk application HTTP error: {response.status_code}")
                return None

        except Exception as e:
            logger.error(f"❌ Exception in bulk application: {e}")
            return None

    def test_page_applications(self, page_num):
        """Test applications for a specific page"""
        logger.info(f"\n📄 TESTING PAGE {page_num}")
        logger.info("=" * 50)

        page_report = {
            'page': page_num,
            'jobs_found': 0,
            'applications_attempted': 0,
            'applications_successful': 0,
            'applications_failed': 0,
            'jobs_applied': [],
            'start_time': datetime.now(),
            'end_time': None
        }

        # Get jobs for this page
        jobs = self.get_jobs_from_api(page_num)
        page_report['jobs_found'] = len(jobs)

        if not jobs:
            logger.warning(f"⚠️ No jobs found on page {page_num}")
            page_report['end_time'] = datetime.now()
            return page_report

        # Apply to jobs on this page
        jobs_to_apply = jobs[:10]  # Apply to first 10 jobs on each page
        job_ids = [job['id'] for job in jobs_to_apply]

        # Try bulk application first
        bulk_results = self.bulk_apply_to_jobs(job_ids)

        if bulk_results is None:
            # Fall back to individual applications
            logger.info("🔄 Falling back to individual applications...")
            for job in jobs_to_apply:
                job_id = job['id']
                job_title = job.get('title', 'Unknown Job')
                company = job.get('company', 'Unknown Company')

                page_report['applications_attempted'] += 1
                self.total_applications += 1

                success = self.apply_to_job(job_id, job_title, company)

                if success:
                    page_report['applications_successful'] += 1
                    page_report['jobs_applied'].append({
                        'id': job_id,
                        'title': job_title,
                        'company': company,
                        'application_url': job.get('application_url', ''),
                        'match_score': job.get('match_score', 0)
                    })
                else:
                    page_report['applications_failed'] += 1

                # Small delay between applications
                time.sleep(0.5)
        else:
            # Bulk application completed - use actual results
            page_report['applications_attempted'] = bulk_results['total']
            page_report['applications_successful'] = bulk_results['successful']
            page_report['applications_failed'] = bulk_results['failed']

            # Add only the successfully applied jobs to the list
            for i, job in enumerate(jobs_to_apply):
                if i < bulk_results['successful']:
                    page_report['jobs_applied'].append({
                        'id': job['id'],
                        'title': job.get('title', 'Unknown Job'),
                        'company': job.get('company', 'Unknown Company'),
                        'application_url': job.get('application_url', ''),
                        'match_score': job.get('match_score', 0)
                    })

        page_report['end_time'] = datetime.now()
        self.application_reports.append(page_report)

        logger.info(f"📊 Page {page_num} Results:")
        logger.info(f"   Jobs Found: {page_report['jobs_found']}")
        logger.info(f"   Applications Attempted: {page_report['applications_attempted']}")
        logger.info(f"   Applications Successful: {page_report['applications_successful']}")
        logger.info(f"   Applications Failed: {page_report['applications_failed']}")

        return page_report

    def run_complete_test(self):
        """Run complete test across 10 pages"""
        logger.info("🚀 STARTING COMPLETE AUTOMATED TESTING")
        logger.info("=" * 60)

        start_time = datetime.now()

        # Test sign-in
        if not self.test_sign_in():
            logger.error("❌ Sign-in test failed. Aborting.")
            return False

        # Test jobs/recommend page
        if not self.test_jobs_recommend_page():
            logger.error("❌ Jobs recommend page test failed. Aborting.")
            return False

        # Test applications across 10 pages
        for page in range(1, 11):
            try:
                self.test_page_applications(page)
                time.sleep(1)  # Delay between pages
            except Exception as e:
                logger.error(f"❌ Error testing page {page}: {e}")
                continue

        end_time = datetime.now()
        total_duration = end_time - start_time

        # Generate final report
        self.generate_final_report(total_duration)

        return True

    def generate_final_report(self, total_duration):
        """Generate comprehensive final report"""
        logger.info("\n" + "🎯" * 60)
        logger.info("FINAL COMPREHENSIVE TEST REPORT")
        logger.info("🎯" * 60)

        logger.info(f"⏱️  Total Test Duration: {total_duration}")
        logger.info(f"📄 Pages Tested: {len(self.application_reports)}")
        logger.info(f"📋 Total Jobs Found: {sum(r['jobs_found'] for r in self.application_reports)}")
        logger.info(f"🎯 Total Applications Attempted: {sum(r['applications_attempted'] for r in self.application_reports)}")
        logger.info(f"✅ Total Successful Applications: {self.successful_applications}")
        logger.info(f"❌ Total Failed Applications: {self.failed_applications}")

        if self.total_applications > 0:
            success_rate = (self.successful_applications / (self.successful_applications + self.failed_applications)) * 100
            logger.info(f"📈 Success Rate: {success_rate:.1f}%")
        else:
            success_rate = 0

        logger.info("\n📊 PER-PAGE BREAKDOWN:")
        logger.info("-" * 60)

        for report in self.application_reports:
            duration = report['end_time'] - report['start_time']
            logger.info(f"Page {report['page']:2d}: {report['applications_successful']:2d}/{report['applications_attempted']:2d} successful ({duration.total_seconds():.1f}s)")

        logger.info("\n🎉 TOP APPLICATIONS:")
        logger.info("-" * 60)

        all_applications = []
        for report in self.application_reports:
            all_applications.extend(report['jobs_applied'])

        # Sort by match score
        top_applications = sorted(all_applications, key=lambda x: x.get('match_score', 0), reverse=True)[:10]

        for i, app in enumerate(top_applications, 1):
            logger.info(f"{i:2d}. {app['title']} at {app['company']} (Match: {app.get('match_score', 0):.1f}%)")

        logger.info("\n🎯 FINAL ASSESSMENT:")
        logger.info("-" * 60)

        if success_rate >= 90:
            assessment = "🏆 EXCELLENT - All systems working perfectly!"
        elif success_rate >= 80:
            assessment = "✅ VERY GOOD - Minor issues only"
        elif success_rate >= 70:
            assessment = "⚠️ GOOD - Some areas need improvement"
        elif success_rate >= 50:
            assessment = "🔧 NEEDS WORK - Multiple issues found"
        else:
            assessment = "❌ CRITICAL - Major problems detected"

        logger.info(assessment)

        if self.successful_applications >= 50:
            logger.info("🎊 SUCCESS: Applied to 50+ jobs automatically!")
        elif self.successful_applications >= 25:
            logger.info("🎉 GOOD: Applied to 25+ jobs automatically!")
        else:
            logger.info("⚠️ LIMITED: Less than 25 successful applications")

        logger.info("\n" + "🎯" * 60)

        # Save detailed report to file
        self.save_detailed_report()

    def save_detailed_report(self):
        """Save detailed report to JSON file"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'/home/calelin/awesome-apply/automated_test_report_{timestamp}.json'

        report_data = {
            'test_summary': {
                'timestamp': datetime.now().isoformat(),
                'total_pages_tested': len(self.application_reports),
                'total_applications_attempted': sum(r['applications_attempted'] for r in self.application_reports),
                'total_successful_applications': self.successful_applications,
                'total_failed_applications': self.failed_applications,
                'success_rate': (self.successful_applications / max(1, self.successful_applications + self.failed_applications)) * 100
            },
            'page_reports': []
        }

        for report in self.application_reports:
            page_data = {
                'page': report['page'],
                'jobs_found': report['jobs_found'],
                'applications_attempted': report['applications_attempted'],
                'applications_successful': report['applications_successful'],
                'applications_failed': report['applications_failed'],
                'duration_seconds': (report['end_time'] - report['start_time']).total_seconds(),
                'jobs_applied': report['jobs_applied']
            }
            report_data['page_reports'].append(page_data)

        try:
            with open(filename, 'w') as f:
                json.dump(report_data, f, indent=2)
            logger.info(f"📄 Detailed report saved to: {filename}")
        except Exception as e:
            logger.error(f"❌ Failed to save report: {e}")

def main():
    """Run the automated testing"""
    tester = JobRightAutomatedTester()

    logger.info("🤖 JobRight.ai Automated Application Tester")
    logger.info("=" * 60)
    logger.info("This will test sign-in and apply to jobs across 10 pages")
    logger.info("🎯 Target: http://localhost:5000")
    logger.info("=" * 60)

    success = tester.run_complete_test()

    if success:
        logger.info("\n🎉 AUTOMATED TESTING COMPLETED SUCCESSFULLY!")
    else:
        logger.info("\n❌ AUTOMATED TESTING ENCOUNTERED ISSUES")

    return success

if __name__ == '__main__':
    main()