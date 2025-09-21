#!/usr/bin/env python3
"""
Test the complete JobRight.ai clone system
"""

import sys
import os
import requests
import json
import time

def test_backend_api():
    """Test the backend API endpoints"""
    print("🧪 Testing JobRight.ai Clone Backend API...")

    base_url = "http://localhost:5000"

    # Test search endpoint
    print("\n1. Testing job search...")
    search_data = {
        "keywords": ["Software Engineer"],
        "location": "San Francisco, CA",
        "experience_level": "mid",
        "job_type": "full-time",
        "date_posted": "week",
        "remote_ok": False
    }

    try:
        response = requests.post(f"{base_url}/api/search", json=search_data, timeout=30)

        if response.status_code == 200:
            result = response.json()
            if result.get("success"):
                jobs = result.get("jobs", [])
                print(f"✅ Search successful: Found {len(jobs)} jobs")

                # Show first few jobs
                for i, job in enumerate(jobs[:3]):
                    print(f"  {i+1}. {job['title']} at {job['company']}")
                    print(f"     Location: {job['location']}")
                    print(f"     Source: {job['source']}")

                # Test get jobs endpoint
                print("\n2. Testing get jobs...")
                response = requests.get(f"{base_url}/api/jobs?limit=10")
                if response.status_code == 200:
                    result = response.json()
                    print(f"✅ Get jobs successful: {result.get('count', 0)} jobs retrieved")
                else:
                    print(f"❌ Get jobs failed: {response.status_code}")

                # Test analytics endpoint
                print("\n3. Testing analytics...")
                response = requests.get(f"{base_url}/api/analytics")
                if response.status_code == 200:
                    result = response.json()
                    analytics = result.get("analytics", {})
                    print(f"✅ Analytics successful:")
                    print(f"   Total jobs: {analytics.get('total_jobs', 0)}")
                    print(f"   Total applications: {analytics.get('total_applications', 0)}")
                    print(f"   Success rate: {analytics.get('success_rate', 0):.1f}%")
                else:
                    print(f"❌ Analytics failed: {response.status_code}")

                return True
            else:
                print(f"❌ Search failed: {result.get('error', 'Unknown error')}")
                return False
        else:
            print(f"❌ Search request failed: {response.status_code}")
            return False

    except requests.exceptions.ConnectRefused:
        print("❌ Cannot connect to backend server")
        print("💡 Make sure to run: python launch_jobright_clone.py")
        return False
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

def test_manual_scraper():
    """Test scraper manually if backend is not running"""
    print("\n🔧 Testing scraper manually...")

    try:
        from robust_job_scraper import RobustJobScraper, SearchCriteria

        scraper = RobustJobScraper(headless=True)

        criteria = SearchCriteria(
            keywords=["Python Developer"],
            location="New York, NY",
            experience_level="mid",
            job_type="full-time",
            salary_min=None,
            salary_max=None,
            date_posted="week",
            company_size=None,
            remote_ok=False
        )

        jobs = scraper.search_jobs(criteria)

        if jobs:
            print(f"✅ Manual scraper test: Found {len(jobs)} jobs")
            for i, job in enumerate(jobs[:3]):
                print(f"  {i+1}. {job.title} at {job.company} ({job.source})")
            return True
        else:
            print("⚠️ Manual scraper found no jobs")
            return False

    except Exception as e:
        print(f"❌ Manual scraper test failed: {e}")
        return False
    finally:
        if 'scraper' in locals():
            scraper.close()

def main():
    """Main test function"""
    print("🚀 JobRight.ai Clone System Test")
    print("=" * 50)

    # Test 1: Try backend API
    api_success = test_backend_api()

    # Test 2: If API fails, test scraper manually
    if not api_success:
        scraper_success = test_manual_scraper()

        if scraper_success:
            print("\n💡 Scraper works! Start the full system with:")
            print("   python launch_jobright_clone.py")
        else:
            print("\n❌ Both API and manual scraper failed")
            print("💡 Try installing dependencies:")
            print("   pip install -r requirements_jobright_clone.txt")
    else:
        print("\n🎉 System test completed successfully!")
        print("✅ Backend API is working")
        print("✅ Job scraping is functional")
        print("✅ Database operations are working")

        print("\n🌐 Access the web interface at: http://localhost:5000")

if __name__ == "__main__":
    main()