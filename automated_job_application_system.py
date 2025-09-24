#!/usr/bin/env python3
"""
🤖 AUTOMATED JOB APPLICATION SYSTEM 🤖
=====================================

This system opens 10 browser pages and automatically applies to jobs using the JobRight.ai system.
Each page will continuously find and apply to jobs with full automation.

Features:
✅ 10 parallel browser instances
✅ Automatic login with demo credentials
✅ Continuous job discovery and application
✅ Real-time progress tracking
✅ Application status monitoring
✅ Auto-retry on failures
✅ Comprehensive logging

Usage:
    python automated_job_application_system.py
"""

import sys
import os
import time
import requests
import json
import threading
import webbrowser
import subprocess
from datetime import datetime, timedelta
from pathlib import Path
import random
from urllib.parse import urljoin

class AutomatedJobApplicationSystem:
    """Complete automated job application system with 10 parallel instances"""

    def __init__(self):
        self.base_url = 'http://localhost:5000'
        self.demo_credentials = {
            'email': 'demo@jobright.ai',
            'password': 'demo123'
        }
        self.sessions = []
        self.application_stats = {
            'total_applications': 0,
            'successful_applications': 0,
            'failed_applications': 0,
            'unique_jobs_found': set(),
            'pages_active': 0
        }
        self.running = True

    def log(self, message, page_id=None):
        """Enhanced logging with timestamps and page ID"""
        timestamp = datetime.now().strftime('%H:%M:%S')
        page_prefix = f"[PAGE-{page_id}]" if page_id else "[SYSTEM]"
        print(f"[{timestamp}] {page_prefix} {message}")

    def create_authenticated_session(self, page_id):
        """Create an authenticated session for a page"""
        session = requests.Session()

        try:
            # Login to get session
            login_data = {
                'email': self.demo_credentials['email'],
                'password': self.demo_credentials['password']
            }

            response = session.post(
                f"{self.base_url}/login",
                json=login_data,
                headers={'Content-Type': 'application/json'}
            )

            if response.status_code == 200:
                result = response.json()
                if result.get('success'):
                    self.log("✅ Authenticated successfully", page_id)
                    return session
                else:
                    self.log(f"❌ Authentication failed: {result.get('message')}", page_id)
            else:
                self.log(f"❌ Authentication failed with status: {response.status_code}", page_id)

        except Exception as e:
            self.log(f"💥 Authentication error: {e}", page_id)

        return None

    def get_available_jobs(self, session, page_id, limit=10):
        """Get available jobs for application"""
        try:
            # Get jobs from the API
            response = session.get(f"{self.base_url}/api/jobs/search?limit={limit}")

            if response.status_code == 200:
                jobs = response.json()
                self.log(f"📋 Found {len(jobs)} available jobs", page_id)
                return jobs
            else:
                self.log(f"❌ Failed to get jobs: {response.status_code}", page_id)
                return []

        except Exception as e:
            self.log(f"💥 Error getting jobs: {e}", page_id)
            return []

    def apply_to_job(self, session, job, page_id):
        """Apply to a specific job"""
        try:
            job_id = job['id']
            job_title = job.get('title', 'Unknown')
            company = job.get('company', 'Unknown')

            # Check if we've already applied to this job
            if job_id in self.application_stats['unique_jobs_found']:
                self.log(f"⏭️ Skipping {job_title} at {company} (already applied)", page_id)
                return False

            # Apply to the job
            response = session.post(
                f"{self.base_url}/api/jobs/{job_id}/apply",
                json={}
            )

            if response.status_code == 200:
                result = response.json()
                if result.get('success'):
                    self.application_stats['successful_applications'] += 1
                    self.application_stats['total_applications'] += 1
                    self.application_stats['unique_jobs_found'].add(job_id)

                    self.log(f"✅ Applied to {job_title} at {company}", page_id)
                    return True
                else:
                    self.log(f"❌ Application failed: {result.get('message')}", page_id)
                    self.application_stats['failed_applications'] += 1
                    self.application_stats['total_applications'] += 1
                    return False
            else:
                self.log(f"❌ Application failed with status: {response.status_code}", page_id)
                self.application_stats['failed_applications'] += 1
                self.application_stats['total_applications'] += 1
                return False

        except Exception as e:
            self.log(f"💥 Error applying to job: {e}", page_id)
            self.application_stats['failed_applications'] += 1
            self.application_stats['total_applications'] += 1
            return False

    def automation_worker(self, page_id):
        """Worker function for each automated page"""
        self.log(f"🚀 Starting automation worker", page_id)
        self.application_stats['pages_active'] += 1

        # Create authenticated session
        session = self.create_authenticated_session(page_id)
        if not session:
            self.log("❌ Failed to create session, stopping worker", page_id)
            self.application_stats['pages_active'] -= 1
            return

        # Open browser page
        browser_url = f"{self.base_url}/jobs?auto_apply=true&page_id={page_id}"
        try:
            webbrowser.open_new_tab(browser_url)
            self.log(f"🌐 Opened browser tab: {browser_url}", page_id)
        except Exception as e:
            self.log(f"⚠️ Could not open browser tab: {e}", page_id)

        applications_this_session = 0
        max_applications_per_session = 20

        while self.running and applications_this_session < max_applications_per_session:
            try:
                # Get available jobs
                jobs = self.get_available_jobs(session, page_id)

                if not jobs:
                    self.log("😴 No jobs available, waiting 30 seconds...", page_id)
                    time.sleep(30)
                    continue

                # Apply to each job
                for job in jobs:
                    if not self.running:
                        break

                    success = self.apply_to_job(session, job, page_id)
                    if success:
                        applications_this_session += 1

                    # Wait between applications to avoid rate limiting
                    time.sleep(random.uniform(2, 5))

                # Wait before next batch
                if applications_this_session < max_applications_per_session:
                    wait_time = random.uniform(10, 20)
                    self.log(f"⏰ Waiting {wait_time:.1f} seconds before next batch", page_id)
                    time.sleep(wait_time)

            except Exception as e:
                self.log(f"💥 Worker error: {e}", page_id)
                time.sleep(10)

        self.log(f"🏁 Worker completed. Applied to {applications_this_session} jobs", page_id)
        self.application_stats['pages_active'] -= 1

    def monitor_progress(self):
        """Monitor and display progress statistics"""
        self.log("📊 Starting progress monitor")

        start_time = datetime.now()
        last_stats_time = start_time

        while self.running:
            time.sleep(10)  # Update every 10 seconds

            current_time = datetime.now()
            elapsed = current_time - start_time

            # Calculate rates
            total_apps = self.application_stats['total_applications']
            success_rate = (self.application_stats['successful_applications'] / total_apps * 100) if total_apps > 0 else 0
            apps_per_minute = total_apps / (elapsed.total_seconds() / 60) if elapsed.total_seconds() > 0 else 0

            # Display stats
            self.log("=" * 60)
            self.log("📊 AUTOMATED JOB APPLICATION SYSTEM - LIVE STATS")
            self.log("=" * 60)
            self.log(f"⏰ Running Time: {elapsed}")
            self.log(f"🚀 Active Pages: {self.application_stats['pages_active']}")
            self.log(f"📝 Total Applications: {total_apps}")
            self.log(f"✅ Successful: {self.application_stats['successful_applications']}")
            self.log(f"❌ Failed: {self.application_stats['failed_applications']}")
            self.log(f"📈 Success Rate: {success_rate:.1f}%")
            self.log(f"⚡ Rate: {apps_per_minute:.1f} applications/minute")
            self.log(f"🎯 Unique Jobs Found: {len(self.application_stats['unique_jobs_found'])}")
            self.log("=" * 60)

            # Stop if all pages are done
            if self.application_stats['pages_active'] == 0:
                self.log("🏁 All pages completed!")
                break

    def start_automation_system(self):
        """Start the complete automation system with 10 pages"""
        self.log("🤖 STARTING AUTOMATED JOB APPLICATION SYSTEM")
        self.log("=" * 70)
        self.log("🎯 MISSION: Open 10 pages, each automatically applying to jobs")
        self.log("🚀 AUTOMATION: Full JobRight.ai integration")
        self.log("💪 SCALE: Enterprise-level job application automation")
        self.log("=" * 70)

        # Check if server is running
        try:
            response = requests.get(f"{self.base_url}/", timeout=5)
            if response.status_code != 200:
                self.log("❌ JobRight.ai server not accessible!")
                return False
        except:
            self.log("❌ JobRight.ai server not running! Please start it first.")
            return False

        self.log("✅ JobRight.ai server is running")

        # Start monitor thread
        monitor_thread = threading.Thread(target=self.monitor_progress, daemon=True)
        monitor_thread.start()

        # Start 10 automation workers
        threads = []
        for page_id in range(1, 11):
            thread = threading.Thread(
                target=self.automation_worker,
                args=(page_id,),
                daemon=True
            )
            threads.append(thread)
            thread.start()

            self.log(f"🚀 Started automation worker for Page {page_id}")
            time.sleep(2)  # Stagger the starts

        self.log("🎉 All 10 automation workers started!")
        self.log("🌐 Browser tabs should be opening automatically...")
        self.log("📊 Check your browser for live job application automation!")

        # Wait for all threads to complete or user interrupt
        try:
            for thread in threads:
                thread.join()

            monitor_thread.join(timeout=5)

        except KeyboardInterrupt:
            self.log("🛑 User interrupted, stopping automation...")
            self.running = False

        # Final stats
        self.log("=" * 70)
        self.log("🏁 AUTOMATION SYSTEM COMPLETED")
        self.log("=" * 70)
        total = self.application_stats['total_applications']
        success = self.application_stats['successful_applications']
        success_rate = (success / total * 100) if total > 0 else 0

        self.log(f"📊 Final Stats:")
        self.log(f"   Total Applications: {total}")
        self.log(f"   Successful: {success}")
        self.log(f"   Success Rate: {success_rate:.1f}%")
        self.log(f"   Unique Jobs: {len(self.application_stats['unique_jobs_found'])}")
        self.log("=" * 70)

        return total > 0

def main():
    """Main function to start the automation system"""
    print("🤖 ULTIMATE JOBRIGHT.AI AUTOMATED APPLICATION SYSTEM")
    print("=" * 70)
    print("This system will:")
    print("✅ Open 10 browser tabs")
    print("✅ Automatically login to each tab")
    print("✅ Find and apply to jobs continuously")
    print("✅ Track applications in real-time")
    print("✅ Provide live statistics")
    print("=" * 70)

    automation_system = AutomatedJobApplicationSystem()

    try:
        success = automation_system.start_automation_system()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"💥 System error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()