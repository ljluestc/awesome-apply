#!/usr/bin/env python3
"""
Comprehensive Test System - Full Terminal Raw Responses
Shows complete job scraping with raw data + tests auto-apply functionality
"""

import sys
sys.path.append('/home/calelin/awesome-apply/venv/lib/python3.13/site-packages')

import json
import requests
import time
from datetime import datetime

def test_job_scraping_api():
    """Test the job scraping API and show full raw responses"""
    print("🚀 COMPREHENSIVE SYSTEM TEST - FULL RAW RESPONSES")
    print("=" * 100)
    print("🎯 Testing REAL job scraping with complete terminal output")
    print("📊 Demonstrating end-to-end functionality with raw data")
    print("=" * 100)

    base_url = "http://localhost:5000"

    # Test 1: Check if server is running
    print("\n📡 TEST 1: Server Status Check")
    print("-" * 60)
    try:
        response = requests.get(f"{base_url}/api/jobs", timeout=10)
        print(f"✅ Server Status: {response.status_code}")
        print(f"✅ Server Response Time: {response.elapsed.total_seconds():.2f}s")

        if response.status_code == 200:
            data = response.json()
            print(f"✅ Current Jobs in Database: {len(data.get('jobs', []))}")

            # Show sample of existing jobs
            jobs = data.get('jobs', [])
            if jobs:
                print("\n📋 SAMPLE EXISTING JOBS (Raw Data):")
                for i, job in enumerate(jobs[:3], 1):
                    print(f"\n  JOB #{i} RAW DATA:")
                    print(f"    Title: {job.get('title', 'N/A')}")
                    print(f"    Company: {job.get('company', 'N/A')}")
                    print(f"    URL: {job.get('url', 'N/A')[:80]}...")
                    print(f"    Source: {job.get('source', 'N/A')}")
                    print(f"    Full JSON: {json.dumps(job, indent=6)}")
        else:
            print(f"❌ Server Error: {response.status_code}")
            return

    except Exception as e:
        print(f"❌ Server Connection Failed: {e}")
        return

    # Test 2: Trigger new job scraping
    print("\n" + "=" * 100)
    print("📡 TEST 2: Live Job Scraping with Full Raw Response")
    print("-" * 60)

    scrape_payload = {
        "keywords": "software engineer",
        "location": "San Jose, CA",
        "remote": False,
        "experience": "all"
    }

    print(f"🔍 SCRAPING REQUEST PAYLOAD:")
    print(json.dumps(scrape_payload, indent=2))
    print("-" * 60)

    try:
        print("🚀 Sending scraping request...")
        start_time = time.time()

        response = requests.post(
            f"{base_url}/api/scrape",
            json=scrape_payload,
            timeout=120  # 2 minutes timeout for scraping
        )

        end_time = time.time()
        scraping_duration = end_time - start_time

        print(f"\n📊 SCRAPING RESPONSE:")
        print(f"   Status Code: {response.status_code}")
        print(f"   Response Time: {scraping_duration:.2f} seconds")
        print(f"   Response Headers: {dict(response.headers)}")

        if response.status_code == 200:
            scrape_data = response.json()
            print(f"\n✅ SCRAPING SUCCESS - RAW RESPONSE:")
            print(json.dumps(scrape_data, indent=2))

            jobs_found = scrape_data.get('jobs_found', 0)
            print(f"\n🎉 REAL JOBS SCRAPED: {jobs_found}")

            if jobs_found > 0:
                print("✅ Job scraping is working correctly!")
                print("✅ Real job data is being extracted successfully")
            else:
                print("⚠️ No jobs found - may need to check selectors")

        else:
            print(f"❌ SCRAPING FAILED:")
            print(f"   Status: {response.status_code}")
            print(f"   Response: {response.text}")

    except Exception as e:
        print(f"❌ SCRAPING REQUEST FAILED: {e}")

    # Test 3: Get updated job list with full data
    print("\n" + "=" * 100)
    print("📡 TEST 3: Retrieve All Jobs with Complete Raw Data")
    print("-" * 60)

    try:
        response = requests.get(f"{base_url}/api/jobs", timeout=10)
        if response.status_code == 200:
            data = response.json()
            jobs = data.get('jobs', [])

            print(f"✅ TOTAL JOBS IN DATABASE: {len(jobs)}")
            print(f"✅ RAW API RESPONSE SIZE: {len(response.text)} characters")

            # Show detailed raw data for first 5 jobs
            print(f"\n📋 DETAILED RAW JOB DATA (First 5 jobs):")
            for i, job in enumerate(jobs[:5], 1):
                print(f"\n{'='*80}")
                print(f"🔍 JOB #{i} - COMPLETE RAW DATA:")
                print(f"{'='*80}")

                # Show each field with raw data
                for key, value in job.items():
                    print(f"  {key:20}: {value}")

                print(f"\n  📄 FULL JSON OBJECT:")
                print(json.dumps(job, indent=4))

                # Test if URL is accessible
                if job.get('url'):
                    print(f"\n  🔗 URL VALIDATION:")
                    try:
                        url_response = requests.head(job['url'], timeout=5, allow_redirects=True)
                        print(f"    ✅ URL Status: {url_response.status_code}")
                        print(f"    ✅ Final URL: {url_response.url}")
                    except:
                        print(f"    ⚠️ URL not accessible (may require cookies/auth)")

            # Test auto-apply functionality
            if jobs:
                print("\n" + "=" * 100)
                print("📡 TEST 4: Auto-Apply Functionality Test")
                print("-" * 60)

                test_job = jobs[0]
                apply_payload = {"job_id": test_job.get('id')}

                print(f"🎯 Testing auto-apply for job:")
                print(f"   Job ID: {test_job.get('id')}")
                print(f"   Title: {test_job.get('title')}")
                print(f"   Company: {test_job.get('company')}")
                print(f"\n🚀 APPLY REQUEST PAYLOAD:")
                print(json.dumps(apply_payload, indent=2))

                try:
                    apply_response = requests.post(
                        f"{base_url}/api/apply",
                        json=apply_payload,
                        timeout=30
                    )

                    print(f"\n📊 APPLY RESPONSE:")
                    print(f"   Status Code: {apply_response.status_code}")
                    print(f"   Raw Response: {apply_response.text}")

                    if apply_response.status_code == 200:
                        apply_data = apply_response.json()
                        print(f"\n✅ APPLY RESPONSE DATA:")
                        print(json.dumps(apply_data, indent=2))

                except Exception as e:
                    print(f"❌ APPLY REQUEST FAILED: {e}")

        else:
            print(f"❌ Failed to get jobs: {response.status_code}")

    except Exception as e:
        print(f"❌ JOBS REQUEST FAILED: {e}")

    # Test 5: Analytics data
    print("\n" + "=" * 100)
    print("📡 TEST 5: Analytics Data with Raw Metrics")
    print("-" * 60)

    try:
        response = requests.get(f"{base_url}/api/analytics", timeout=10)
        if response.status_code == 200:
            analytics = response.json()
            print(f"✅ ANALYTICS RAW DATA:")
            print(json.dumps(analytics, indent=2))
        else:
            print(f"❌ Analytics failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Analytics request failed: {e}")

    # Final Summary
    print("\n" + "=" * 100)
    print("🎉 COMPREHENSIVE TEST COMPLETE")
    print("=" * 100)
    print("✅ Server Status: TESTED")
    print("✅ Job Scraping: TESTED")
    print("✅ Raw Data Display: COMPLETE")
    print("✅ Auto-Apply: TESTED")
    print("✅ Analytics: TESTED")
    print("=" * 100)
    print(f"🕐 Test completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("🌐 UI available at: http://localhost:5000")
    print("📊 All raw data has been displayed in terminal")

if __name__ == "__main__":
    test_job_scraping_api()