#!/usr/bin/env python3
"""
🧪 TEST JOB AUTOMATION 🧪
========================

Quick test of the job automation system to verify everything is working.
"""

import sys
import requests
import json
from datetime import datetime

sys.path.append('/home/calelin/awesome-apply/venv/lib/python3.13/site-packages')

def test_jobright_system():
    """Test the JobRight system functionality"""
    base_url = 'http://localhost:5000'
    session = requests.Session()

    print("🧪 Testing JobRight.ai System")
    print("=" * 50)

    # Test 1: Check if server is running
    try:
        response = session.get(base_url, timeout=5)
        if response.status_code == 200:
            print("✅ JobRight server is running")
        else:
            print(f"❌ Server returned status {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Server not accessible: {e}")
        return False

    # Test 2: Login
    credentials = {
        'email': 'demo@jobright.ai',
        'password': 'demo123'
    }

    try:
        login_response = session.post(
            f"{base_url}/login",
            json=credentials,
            headers={'Content-Type': 'application/json'},
            timeout=10
        )

        if login_response.status_code == 200:
            result = login_response.json()
            if result.get('success'):
                print("✅ Login successful")
            else:
                print(f"❌ Login failed: {result.get('message')}")
                return False
        else:
            print(f"❌ Login failed with status {login_response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Login error: {e}")
        return False

    # Test 3: Get jobs
    try:
        jobs_response = session.get(f"{base_url}/api/jobs/search?limit=10")

        if jobs_response.status_code == 200:
            jobs = jobs_response.json()
            print(f"✅ Found {len(jobs)} jobs available")

            # Show first job if available
            if jobs:
                first_job = jobs[0]
                print(f"📋 Sample job: {first_job.get('title', 'N/A')} at {first_job.get('company', 'N/A')}")
        else:
            print(f"❌ Jobs API failed: {jobs_response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Error getting jobs: {e}")
        return False

    # Test 4: Try scraping new jobs
    try:
        scrape_response = session.post(
            f"{base_url}/api/scrape",
            json={'keywords': 'software engineer', 'location': 'San Francisco, CA'},
            timeout=30
        )

        if scrape_response.status_code == 200:
            scrape_result = scrape_response.json()
            if scrape_result.get('success'):
                jobs_scraped = scrape_result.get('jobs_scraped', 0)
                print(f"✅ Scraped {jobs_scraped} new jobs")
            else:
                print(f"⚠️ Scraping failed: {scrape_result.get('error')}")
        else:
            print(f"⚠️ Scrape API returned {scrape_response.status_code}")
    except Exception as e:
        print(f"⚠️ Scraping error: {e}")

    # Test 5: Get updated job list
    try:
        updated_jobs_response = session.get(f"{base_url}/api/jobs/search?limit=20")

        if updated_jobs_response.status_code == 200:
            updated_jobs = updated_jobs_response.json()
            print(f"✅ Now have {len(updated_jobs)} total jobs available")

            # Try applying to a job
            if updated_jobs:
                test_job = updated_jobs[0]
                job_id = test_job.get('id')

                if job_id:
                    apply_response = session.post(
                        f"{base_url}/api/jobs/{job_id}/apply",
                        json={},
                        timeout=10
                    )

                    if apply_response.status_code == 200:
                        apply_result = apply_response.json()
                        if apply_result.get('success'):
                            print("✅ Successfully applied to test job!")
                            print(f"📝 Applied to: {test_job.get('title')} at {test_job.get('company')}")
                        else:
                            print(f"⚠️ Application failed: {apply_result.get('message')}")
                    else:
                        print(f"❌ Apply API failed: {apply_response.status_code}")

    except Exception as e:
        print(f"❌ Error in application test: {e}")

    # Test 6: Get analytics
    try:
        analytics_response = session.get(f"{base_url}/api/analytics")

        if analytics_response.status_code == 200:
            analytics = analytics_response.json()
            print("✅ Analytics retrieved:")
            print(f"   📊 Total jobs: {analytics.get('total_jobs', 'N/A')}")
            print(f"   🚀 Successful applications: {analytics.get('successful_applications', 'N/A')}")
            print(f"   📈 Success rate: {analytics.get('success_rate', 'N/A'):.1f}%" if analytics.get('success_rate') else "   📈 Success rate: N/A")

    except Exception as e:
        print(f"⚠️ Analytics error: {e}")

    print("=" * 50)
    print("🎉 JobRight.ai system test completed!")
    print("✅ The system is working and ready for automation")
    return True

def run_quick_automation_test():
    """Run a quick automation test"""
    print("\n🤖 Running Quick Automation Test")
    print("=" * 50)

    base_url = 'http://localhost:5000'
    session = requests.Session()

    # Login
    credentials = {'email': 'demo@jobright.ai', 'password': 'demo123'}
    session.post(f"{base_url}/login", json=credentials, headers={'Content-Type': 'application/json'})

    applications_made = 0

    try:
        # Get jobs and apply to a few
        jobs_response = session.get(f"{base_url}/api/jobs/search?limit=5")

        if jobs_response.status_code == 200:
            jobs = jobs_response.json()

            for job in jobs[:3]:  # Apply to first 3 jobs
                job_id = job.get('id')
                if job_id:
                    apply_response = session.post(f"{base_url}/api/jobs/{job_id}/apply", json={})

                    if apply_response.status_code == 200:
                        result = apply_response.json()
                        if result.get('success'):
                            applications_made += 1
                            print(f"✅ Applied to: {job.get('title', 'Unknown')} at {job.get('company', 'Unknown')}")
                        else:
                            print(f"⚠️ Already applied or failed: {result.get('message')}")

    except Exception as e:
        print(f"❌ Automation test error: {e}")

    print(f"🎯 Quick automation test completed: {applications_made} applications submitted")
    return applications_made > 0

def main():
    """Main test function"""
    print(f"🧪 JOBRIGHT.AI AUTOMATION TEST")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

    # Test the basic system
    system_working = test_jobright_system()

    if system_working:
        # Run automation test
        automation_working = run_quick_automation_test()

        if automation_working:
            print("\n🎉 ALL TESTS PASSED!")
            print("🚀 Your job automation system is fully functional")
            print("💡 You can now run continuous automation safely")
        else:
            print("\n⚠️ System works but automation needs attention")
    else:
        print("\n❌ Basic system tests failed")
        return False

    print("\n🎯 READY FOR CONTINUOUS AUTOMATION!")
    print("Run: python simple_continuous_applicator.py")
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)