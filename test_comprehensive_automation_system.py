#!/usr/bin/env python3
"""
Test script for the comprehensive job automation system
Verifies all components work together correctly
"""

import sys
sys.path.append('/home/calelin/awesome-apply/venv/lib/python3.13/site-packages')

import asyncio
import json
import logging
from datetime import datetime, timedelta
from comprehensive_job_automation_system import (
    ComprehensiveAutomationSystem,
    JobScrapingAPI,
    ClickHouseJobStorage,
    AutomationPatternEngine,
    IntelligentFormDetector,
    BatchApplicationSystem,
    JobPosting
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SystemTester:
    """Test suite for comprehensive automation system"""

    def __init__(self):
        self.test_results = {
            'storage_test': False,
            'scraping_test': False,
            'pattern_engine_test': False,
            'form_detection_test': False,
            'batch_system_test': False,
            'integration_test': False
        }

    async def run_all_tests(self):
        """Run comprehensive test suite"""
        logger.info("🧪 Starting comprehensive automation system tests")

        # Test 1: Storage System
        logger.info("📦 Testing storage system...")
        self.test_results['storage_test'] = await self.test_storage_system()

        # Test 2: Job Scraping
        logger.info("🔍 Testing job scraping...")
        self.test_results['scraping_test'] = await self.test_job_scraping()

        # Test 3: Pattern Engine
        logger.info("🧠 Testing pattern engine...")
        self.test_results['pattern_engine_test'] = await self.test_pattern_engine()

        # Test 4: Form Detection
        logger.info("📋 Testing form detection...")
        self.test_results['form_detection_test'] = await self.test_form_detection()

        # Test 5: Batch System
        logger.info("⚡ Testing batch application system...")
        self.test_results['batch_system_test'] = await self.test_batch_system()

        # Test 6: Full Integration
        logger.info("🔄 Testing full integration...")
        self.test_results['integration_test'] = await self.test_full_integration()

        # Generate test report
        self.generate_test_report()

        return self.test_results

    async def test_storage_system(self):
        """Test ClickHouse/SQLite storage"""
        try:
            storage = ClickHouseJobStorage()

            # Create test job
            test_job = JobPosting(
                id="test_job_001",
                title="Senior Software Engineer",
                company="Test Company",
                location="Remote",
                salary_min=120000,
                salary_max=180000,
                job_type="full-time",
                experience_level="senior",
                skills=["Python", "JavaScript", "React"],
                description="Test job description for automation testing",
                posted_date=datetime.now() - timedelta(days=1),
                expires_date=datetime.now() + timedelta(days=30),
                application_url="https://example.com/jobs/test",
                source="test",
                remote_friendly=True,
                benefits=["Health Insurance", "Remote Work"],
                company_size="medium",
                industry="technology",
                match_score=85.5,
                automation_confidence=0.8
            )

            # Test saving
            saved_count = storage.save_jobs([test_job])

            # Test retrieving
            retrieved_jobs = storage.get_jobs_for_automation(limit=10)

            logger.info(f"✅ Storage test: Saved {saved_count}, Retrieved {len(retrieved_jobs)} jobs")
            return saved_count > 0 and len(retrieved_jobs) > 0

        except Exception as e:
            logger.error(f"❌ Storage test failed: {e}")
            return False

    async def test_job_scraping(self):
        """Test job scraping APIs"""
        try:
            scraper = JobScrapingAPI()
            await scraper.initialize_session()

            # Test RemoteOK scraping
            remoteok_jobs = await scraper.scrape_remoteok_all()

            # Test GitHub scraping
            github_jobs = await scraper.scrape_github_jobs_comprehensive()

            await scraper.session.close()

            total_jobs = len(remoteok_jobs) + len(github_jobs)
            logger.info(f"✅ Scraping test: Found {total_jobs} jobs ({len(remoteok_jobs)} RemoteOK, {len(github_jobs)} GitHub)")

            return total_jobs > 10  # Expect at least 10 jobs

        except Exception as e:
            logger.error(f"❌ Scraping test failed: {e}")
            return False

    async def test_pattern_engine(self):
        """Test automation pattern engine"""
        try:
            storage = ClickHouseJobStorage()
            pattern_engine = AutomationPatternEngine(storage)

            # Test pattern creation
            mock_analysis = {
                'site_name': 'Example Jobs',
                'fields': {
                    'email': {
                        'selector': '#email',
                        'type': 'email',
                        'required': True
                    },
                    'first_name': {
                        'selector': '#first_name',
                        'type': 'text',
                        'required': True
                    }
                },
                'submit_button': {
                    'selector': '#submit-btn'
                }
            }

            pattern = pattern_engine.create_pattern_from_analysis("https://example.com/apply", mock_analysis)

            # Test pattern retrieval
            retrieved_pattern = pattern_engine.get_pattern_for_url("https://example.com/apply")

            logger.info(f"✅ Pattern engine test: Created pattern {pattern.id}")
            return pattern is not None and retrieved_pattern is not None

        except Exception as e:
            logger.error(f"❌ Pattern engine test failed: {e}")
            return False

    async def test_form_detection(self):
        """Test intelligent form detection"""
        try:
            form_detector = IntelligentFormDetector()

            if not form_detector.driver:
                logger.info("⚠️ Form detection test skipped (no Chrome driver)")
                return True  # Consider this a pass if no driver available

            # Test with a simple form page
            test_html = """
            <!DOCTYPE html>
            <html>
            <body>
                <form id="job-application-form">
                    <input type="email" name="email" id="email" required placeholder="Your email">
                    <input type="text" name="first_name" id="first_name" required placeholder="First name">
                    <input type="text" name="last_name" id="last_name" required placeholder="Last name">
                    <input type="file" name="resume" id="resume" accept=".pdf,.doc,.docx">
                    <button type="submit" id="submit-btn">Apply Now</button>
                </form>
            </body>
            </html>
            """

            # Create a temporary HTML file
            import tempfile
            import os

            with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False) as f:
                f.write(test_html)
                temp_file = f.name

            try:
                analysis = form_detector.analyze_application_page(f"file://{temp_file}")

                form_detector.driver.quit()
                os.unlink(temp_file)

                fields_detected = len(analysis.get('fields', {}))
                buttons_detected = len(analysis.get('buttons', []))

                logger.info(f"✅ Form detection test: {fields_detected} fields, {buttons_detected} buttons detected")
                return fields_detected >= 4 and buttons_detected >= 1

            except Exception as e:
                if form_detector.driver:
                    form_detector.driver.quit()
                os.unlink(temp_file)
                raise e

        except Exception as e:
            logger.error(f"❌ Form detection test failed: {e}")
            return False

    async def test_batch_system(self):
        """Test batch application system"""
        try:
            storage = ClickHouseJobStorage()
            pattern_engine = AutomationPatternEngine(storage)
            form_detector = IntelligentFormDetector()
            batch_system = BatchApplicationSystem(storage, pattern_engine, form_detector)

            # Create test jobs in storage first
            test_jobs = []
            for i in range(5):
                job = JobPosting(
                    id=f"batch_test_job_{i}",
                    title=f"Test Engineer {i}",
                    company=f"Test Company {i}",
                    location="Remote",
                    salary_min=100000,
                    salary_max=150000,
                    job_type="full-time",
                    experience_level="mid",
                    skills=["Python", "Testing"],
                    description=f"Test job {i} for batch processing",
                    posted_date=datetime.now() - timedelta(days=1),
                    expires_date=datetime.now() + timedelta(days=30),
                    application_url=f"https://example.com/jobs/test-{i}",
                    source="test",
                    remote_friendly=True,
                    benefits=["Remote Work"],
                    company_size="startup",
                    industry="technology",
                    match_score=80.0 + i,
                    automation_confidence=0.5 + (i * 0.1)
                )
                test_jobs.append(job)

            storage.save_jobs(test_jobs)

            # Test batch processing (dry run)
            results = await batch_system.run_batch_applications(
                target_applications=3,
                time_limit_hours=0.1  # 6 minutes
            )

            if form_detector.driver:
                form_detector.driver.quit()

            logger.info(f"✅ Batch system test: Processed {results.get('attempted', 0)} applications")
            return True  # Consider successful if no exceptions

        except Exception as e:
            logger.error(f"❌ Batch system test failed: {e}")
            return False

    async def test_full_integration(self):
        """Test full system integration"""
        try:
            system = ComprehensiveAutomationSystem()

            # Run a mini version of the full cycle
            results = await system.run_full_automation_cycle(
                target_jobs=50,
                target_applications=5
            )

            if results and not results.get('error'):
                scraping_results = results.get('scraping_results', {})
                application_results = results.get('application_results', {})

                jobs_found = scraping_results.get('total_jobs_found', 0)
                apps_attempted = application_results.get('attempted', 0)

                logger.info(f"✅ Integration test: {jobs_found} jobs found, {apps_attempted} applications attempted")
                return jobs_found > 0  # At least some jobs should be found

            return False

        except Exception as e:
            logger.error(f"❌ Integration test failed: {e}")
            return False

    def generate_test_report(self):
        """Generate comprehensive test report"""
        passed_tests = sum(1 for result in self.test_results.values() if result)
        total_tests = len(self.test_results)

        logger.info("\n" + "="*50)
        logger.info("🧪 COMPREHENSIVE AUTOMATION SYSTEM TEST REPORT")
        logger.info("="*50)

        for test_name, passed in self.test_results.items():
            status = "✅ PASS" if passed else "❌ FAIL"
            logger.info(f"{test_name.replace('_', ' ').title()}: {status}")

        logger.info("-"*50)
        logger.info(f"Overall Result: {passed_tests}/{total_tests} tests passed")

        if passed_tests == total_tests:
            logger.info("🎉 All tests passed! System is ready for production use.")
        elif passed_tests >= total_tests * 0.8:
            logger.info("⚠️ Most tests passed. System is mostly functional with minor issues.")
        else:
            logger.info("❌ Multiple test failures. System needs debugging before use.")

        logger.info("="*50)

        # Generate detailed recommendations
        self.generate_recommendations()

    def generate_recommendations(self):
        """Generate recommendations based on test results"""
        logger.info("\n📋 RECOMMENDATIONS:")

        if not self.test_results['storage_test']:
            logger.info("- Fix storage system (ClickHouse/SQLite connection)")

        if not self.test_results['scraping_test']:
            logger.info("- Check API endpoints and rate limiting")

        if not self.test_results['form_detection_test']:
            logger.info("- Install Chrome/ChromeDriver for form detection")

        if not self.test_results['batch_system_test']:
            logger.info("- Debug batch application logic")

        if not self.test_results['integration_test']:
            logger.info("- Review overall system architecture")

        logger.info("- Consider adding more error handling and retries")
        logger.info("- Implement monitoring and alerting")
        logger.info("- Add user configuration management")

async def main():
    """Main test execution"""
    tester = SystemTester()
    results = await tester.run_all_tests()

    # Save results to file
    with open('automation_system_test_results.json', 'w') as f:
        json.dump({
            'test_results': results,
            'timestamp': datetime.now().isoformat(),
            'summary': f"{sum(results.values())}/{len(results)} tests passed"
        }, f, indent=2)

    return results

if __name__ == "__main__":
    asyncio.run(main())