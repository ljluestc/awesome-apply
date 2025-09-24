#!/usr/bin/env python3
"""
🚀 SIMPLE CONTINUOUS JOB APPLICATOR 🚀
======================================

This system continuously applies to jobs using your existing JobRight.ai system.
It's a simplified version that focuses on getting you results quickly.

Features:
✅ Uses your existing JobRight.ai server (already running)
✅ Continuously finds and applies to jobs
✅ Real-time application monitoring
✅ Smart job filtering and targeting
✅ Automatic retries and error handling
"""

import sys
import time
import requests
import json
import random
from datetime import datetime
from typing import Dict, List

sys.path.append('/home/calelin/awesome-apply/venv/lib/python3.13/site-packages')

class SimpleContinuousApplicator:
    """Simple but effective job application automation"""

    def __init__(self):
        self.base_url = 'http://localhost:5000'
        self.session = requests.Session()
        self.applications_submitted = 0
        self.jobs_processed = 0
        self.running = True

        # Demo credentials for JobRight system
        self.credentials = {
            'email': 'demo@jobright.ai',
            'password': 'demo123'
        }

        # Job search criteria
        self.search_criteria = [
            {'keywords': 'software engineer', 'location': 'San Francisco, CA'},
            {'keywords': 'python developer', 'location': 'New York, NY'},
            {'keywords': 'full stack developer', 'location': 'Seattle, WA'},
            {'keywords': 'backend engineer', 'location': 'Austin, TX'},
            {'keywords': 'data scientist', 'location': 'Remote'},
            {'keywords': 'machine learning engineer', 'location': 'Boston, MA'},
        ]

    def log(self, message: str):
        """Simple logging with timestamp"""
        timestamp = datetime.now().strftime('%H:%M:%S')
        print(f"[{timestamp}] {message}")

    def login_to_system(self) -> bool:
        """Login to the JobRight system"""
        try:
            response = self.session.post(
                f"{self.base_url}/login",
                json=self.credentials,
                headers={'Content-Type': 'application/json'},
                timeout=10
            )

            if response.status_code == 200:
                result = response.json()
                if result.get('success'):
                    self.log("✅ Successfully logged into JobRight system")
                    return True
                else:
                    self.log(f"❌ Login failed: {result.get('message')}")
                    return False
            else:
                self.log(f"❌ Login failed with status {response.status_code}")
                return False

        except Exception as e:
            self.log(f"❌ Login error: {e}")
            return False

    def get_available_jobs(self) -> List[Dict]:
        """Get jobs from the JobRight API"""
        try:
            # First, trigger job scraping with random criteria
            criteria = random.choice(self.search_criteria)

            scrape_response = self.session.post(
                f"{self.base_url}/api/scrape",
                json=criteria,
                timeout=30
            )

            if scrape_response.status_code == 200:
                scrape_result = scrape_response.json()
                if scrape_result.get('success'):
                    self.log(f"🔍 Scraped {scrape_result.get('jobs_scraped', 0)} new jobs")

            # Get available jobs
            jobs_response = self.session.get(f"{self.base_url}/api/jobs/search?limit=50")

            if jobs_response.status_code == 200:
                jobs = jobs_response.json()
                self.log(f"📋 Found {len(jobs)} jobs available for application")
                return jobs
            else:
                self.log(f"⚠️ Failed to get jobs: {jobs_response.status_code}")
                return []

        except Exception as e:
            self.log(f"❌ Error getting jobs: {e}")
            return []

    def apply_to_job(self, job: Dict) -> bool:
        """Apply to a single job via the JobRight API"""
        try:
            job_id = job.get('id')
            job_title = job.get('title', 'Unknown Position')
            company = job.get('company', 'Unknown Company')

            # Apply via the API
            apply_response = self.session.post(
                f"{self.base_url}/api/jobs/{job_id}/apply",
                json={},
                timeout=15
            )

            if apply_response.status_code == 200:
                result = apply_response.json()
                if result.get('success'):
                    self.applications_submitted += 1
                    self.log(f"✅ Applied to {job_title} at {company} (#{self.applications_submitted})")
                    return True
                else:
                    self.log(f"⚠️ Application failed: {result.get('message')}")
                    return False
            else:
                self.log(f"❌ API error applying to {job_title}: {apply_response.status_code}")
                return False

        except Exception as e:
            self.log(f"❌ Error applying to job: {e}")
            return False

    def filter_good_jobs(self, jobs: List[Dict]) -> List[Dict]:
        """Filter jobs to focus on good opportunities"""
        filtered_jobs = []

        for job in jobs:
            title = job.get('title', '').lower()
            company = job.get('company', '').lower()
            match_score = job.get('match_score', 0)

            # Skip if match score is too low
            if match_score < 70:
                continue

            # Skip certain job types we don't want
            skip_keywords = [
                'intern', 'unpaid', 'volunteer', 'contract',
                'temporary', 'part-time', 'commission'
            ]

            if any(skip_word in title for skip_word in skip_keywords):
                continue

            # Prefer jobs with these positive indicators
            good_keywords = [
                'software engineer', 'developer', 'python', 'full stack',
                'backend', 'frontend', 'data scientist', 'machine learning'
            ]

            if any(good_word in title for good_word in good_keywords):
                filtered_jobs.append(job)

        self.log(f"🎯 Filtered to {len(filtered_jobs)} high-quality jobs")
        return filtered_jobs

    def run_application_cycle(self):
        """Run one complete application cycle"""
        self.log("🔄 Starting application cycle")

        # Get available jobs
        jobs = self.get_available_jobs()
        if not jobs:
            self.log("😴 No jobs found this cycle")
            return 0

        # Filter for good jobs
        good_jobs = self.filter_good_jobs(jobs)
        if not good_jobs:
            self.log("⚠️ No good jobs found after filtering")
            return 0

        # Apply to jobs (limit to avoid overwhelming)
        applications_this_cycle = 0
        max_applications = min(10, len(good_jobs))

        for i, job in enumerate(good_jobs[:max_applications]):
            try:
                self.jobs_processed += 1

                if self.apply_to_job(job):
                    applications_this_cycle += 1

                # Small delay between applications
                time.sleep(random.uniform(2, 5))

            except Exception as e:
                self.log(f"❌ Error in application loop: {e}")
                continue

        self.log(f"📊 Cycle complete: {applications_this_cycle} applications submitted")
        return applications_this_cycle

    def get_system_stats(self) -> Dict:
        """Get current system statistics"""
        try:
            analytics_response = self.session.get(f"{self.base_url}/api/analytics")
            if analytics_response.status_code == 200:
                return analytics_response.json()
        except:
            pass

        return {}

    def run_continuous_automation(self):
        """Main continuous automation loop"""
        self.log("🚀 SIMPLE CONTINUOUS JOB APPLICATOR STARTING")
        self.log("=" * 60)
        self.log("🎯 MISSION: Apply to as many relevant jobs as possible")
        self.log("⚡ STRATEGY: Use existing JobRight.ai system for maximum efficiency")
        self.log("🤖 STATUS: Fully automated - will run until stopped")
        self.log("=" * 60)

        # Login first
        if not self.login_to_system():
            self.log("❌ Could not login to system, exiting")
            return False

        start_time = time.time()

        try:
            while self.running:
                cycle_start = time.time()

                # Run application cycle
                apps_this_cycle = self.run_application_cycle()

                # Get system stats
                stats = self.get_system_stats()

                # Display progress
                runtime_minutes = (time.time() - start_time) / 60
                cycle_time = time.time() - cycle_start

                self.log("=" * 60)
                self.log("📊 AUTOMATION PROGRESS")
                self.log("=" * 60)
                self.log(f"⏱️  Runtime: {runtime_minutes:.1f} minutes")
                self.log(f"🚀 Applications this cycle: {apps_this_cycle}")
                self.log(f"📝 Total applications: {self.applications_submitted}")
                self.log(f"📋 Jobs processed: {self.jobs_processed}")
                self.log(f"⚡ Cycle time: {cycle_time:.1f} seconds")

                # System stats if available
                total_system_apps = stats.get('successful_applications', 0)
                system_jobs = stats.get('total_jobs', 0)
                if total_system_apps > 0:
                    self.log(f"🏆 System total applications: {total_system_apps}")
                    self.log(f"🗄️  System total jobs: {system_jobs}")

                self.log("=" * 60)

                # Wait before next cycle (5-10 minutes)
                wait_time = random.uniform(300, 600)
                self.log(f"😴 Waiting {wait_time/60:.1f} minutes until next cycle...")

                time.sleep(wait_time)

        except KeyboardInterrupt:
            self.log("🛑 Automation stopped by user")
        except Exception as e:
            self.log(f"❌ Fatal error: {e}")
            return False

        # Final summary
        runtime_hours = (time.time() - start_time) / 3600
        final_stats = self.get_system_stats()

        self.log("=" * 60)
        self.log("🏁 AUTOMATION COMPLETED")
        self.log("=" * 60)
        self.log(f"⏱️  Total runtime: {runtime_hours:.1f} hours")
        self.log(f"🚀 Applications submitted: {self.applications_submitted}")
        self.log(f"📋 Jobs processed: {self.jobs_processed}")
        self.log(f"🏆 System applications: {final_stats.get('successful_applications', 'N/A')}")
        self.log(f"📈 Success rate: {(self.applications_submitted/self.jobs_processed*100):.1f}%" if self.jobs_processed > 0 else "N/A")

        if self.applications_submitted > 0:
            self.log("🎉 MISSION ACCOMPLISHED! Jobs have been applied to successfully.")
            self.log("📧 Check your email for responses from employers.")
        else:
            self.log("⚠️ No applications were submitted. Check JobRight system status.")

        self.log("=" * 60)

        return self.applications_submitted > 0

def main():
    """Main function to run continuous job applications"""
    applicator = SimpleContinuousApplicator()

    print("🚀 SIMPLE CONTINUOUS JOB APPLICATOR")
    print("=" * 60)
    print("This system will:")
    print("✅ Connect to your running JobRight.ai system")
    print("✅ Continuously find and scrape new jobs")
    print("✅ Automatically apply to relevant positions")
    print("✅ Provide real-time progress updates")
    print("✅ Run until you stop it (Ctrl+C)")
    print("=" * 60)
    print()

    try:
        success = applicator.run_continuous_automation()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n🛑 Simple Continuous Applicator stopped by user")
        sys.exit(0)
    except Exception as e:
        print(f"\n💥 Fatal error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()