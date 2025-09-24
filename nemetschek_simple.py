#!/usr/bin/env python3
"""
Simple Nemetschek Job Application Automation
"""

import time
import os
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options

def setup_driver():
    """Setup Chrome driver"""
    chrome_options = Options()
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--window-size=1920,1080")

    driver = webdriver.Chrome(options=chrome_options)
    return driver

def main():
    print("🚀 Nemetschek Job Application Automation")
    print("=" * 50)

    # Profile data
    profile = {
        'first_name': 'Jiale',
        'last_name': 'Lin',
        'email': 'jeremykalilin@gmail.com',
        'phone': '+1-510-417-5834',
        'resume_path': '/home/calelin/Downloads/Jiale_Lin_Resume_2025_Latest.pdf'
    }

    # Check resume exists
    if not os.path.exists(profile['resume_path']):
        print(f"❌ Resume not found: {profile['resume_path']}")
        return

    driver = setup_driver()
    wait = WebDriverWait(driver, 20)

    try:
        # Navigate to Nemetschek careers
        url = "https://career55.sapsf.eu/careers?company=nemetschek"
        print(f"📍 Navigating to: {url}")
        driver.get(url)

        # Wait for page load
        time.sleep(5)
        print(f"✅ Page loaded: {driver.title}")

        # Look for jobs
        print("🔍 Looking for job listings...")

        # Try various job selectors
        job_selectors = [
            "a[href*='/job/']",
            ".job-link",
            ".position-link",
            "[data-automation-id='jobTitle']"
        ]

        jobs_found = False
        for selector in job_selectors:
            try:
                jobs = driver.find_elements(By.CSS_SELECTOR, selector)
                if jobs:
                    print(f"✅ Found {len(jobs)} jobs with selector: {selector}")
                    # Click first job
                    driver.execute_script("arguments[0].click();", jobs[0])
                    time.sleep(3)
                    jobs_found = True
                    break
            except:
                continue

        if not jobs_found:
            print("⚠️ No jobs found, continuing to look for application form...")

        # Look for apply button
        print("🔍 Looking for apply button...")
        apply_selectors = [
            "//button[contains(text(), 'Apply')]",
            "//a[contains(text(), 'Apply')]",
            "//button[contains(text(), 'Bewerben')]",  # German
            "//a[contains(text(), 'Bewerben')]"
        ]

        for xpath in apply_selectors:
            try:
                apply_btn = driver.find_element(By.XPATH, xpath)
                if apply_btn and apply_btn.is_displayed():
                    print(f"✅ Found apply button")
                    driver.execute_script("arguments[0].click();", apply_btn)
                    time.sleep(3)
                    break
            except:
                continue

        # Fill form fields
        print("📝 Filling application form...")

        # Personal info
        field_mappings = [
            (profile['first_name'], ["input[name*='firstName']", "input[id*='firstName']"]),
            (profile['last_name'], ["input[name*='lastName']", "input[id*='lastName']"]),
            (profile['email'], ["input[type='email']", "input[name*='email']"]),
            (profile['phone'], ["input[name*='phone']", "input[name*='mobile']"])
        ]

        filled_count = 0
        for value, selectors in field_mappings:
            for selector in selectors:
                try:
                    field = driver.find_element(By.CSS_SELECTOR, selector)
                    if field and field.is_displayed():
                        field.clear()
                        field.send_keys(value)
                        print(f"✅ Filled {selector}: {value}")
                        filled_count += 1
                        break
                except:
                    continue

        # Upload resume
        print("📎 Uploading resume...")
        upload_selectors = [
            "input[type='file']",
            "input[accept*='pdf']"
        ]

        for selector in upload_selectors:
            try:
                upload_field = driver.find_element(By.CSS_SELECTOR, selector)
                if upload_field:
                    upload_field.send_keys(profile['resume_path'])
                    print("✅ Resume uploaded successfully")
                    time.sleep(2)
                    break
            except:
                continue

        print(f"📊 Form filling completed: {filled_count} fields filled")
        print("🎯 Keeping browser open for manual review...")

        # Keep browser open for manual verification
        input("Press Enter to close browser...")

    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        driver.quit()
        print("✅ Automation completed")

if __name__ == "__main__":
    main()