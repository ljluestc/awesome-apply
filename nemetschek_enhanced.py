#!/usr/bin/env python3
"""
Enhanced Nemetschek SAP SuccessFactors Automation
Handles job search, application forms, and PDF upload
"""

import time
import os
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys

def setup_driver():
    """Setup Chrome driver with optimal settings"""
    chrome_options = Options()
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")

    # Allow file downloads and uploads
    prefs = {
        "download.prompt_for_download": False,
        "download.directory_upgrade": True,
        "plugins.always_open_pdf_externally": True
    }
    chrome_options.add_experimental_option("prefs", prefs)

    driver = webdriver.Chrome(options=chrome_options)
    return driver

def wait_for_page_load(driver, timeout=10):
    """Wait for page to fully load"""
    wait = WebDriverWait(driver, timeout)
    wait.until(lambda d: d.execute_script("return document.readyState") == "complete")
    time.sleep(2)  # Additional wait for dynamic content

def search_for_jobs(driver, search_terms="software engineer"):
    """Search for relevant jobs"""
    print(f"🔍 Searching for jobs: {search_terms}")

    # SAP SuccessFactors search selectors
    search_selectors = [
        "input[placeholder*='Search']",
        "input[placeholder*='search']",
        "input[name*='search']",
        "input[id*='search']",
        ".searchInput",
        "#searchInput"
    ]

    for selector in search_selectors:
        try:
            search_box = driver.find_element(By.CSS_SELECTOR, selector)
            if search_box and search_box.is_displayed():
                search_box.clear()
                search_box.send_keys(search_terms)
                search_box.send_keys(Keys.RETURN)
                print(f"✅ Used search box: {selector}")
                time.sleep(3)
                return True
        except:
            continue

    print("⚠️ No search box found")
    return False

def find_jobs(driver):
    """Find job listings on the page"""
    print("🎯 Looking for job listings...")

    # SAP SuccessFactors job listing selectors
    job_selectors = [
        "a[href*='/job/']",
        "a[href*='/jobs/']",
        "a[href*='jobDetail']",
        ".job-link",
        ".jobTitle a",
        ".job-title a",
        "[data-automation-id='jobTitle']",
        ".jobListItem a",
        ".searchResultsJobTitle a"
    ]

    all_jobs = []
    for selector in job_selectors:
        try:
            jobs = driver.find_elements(By.CSS_SELECTOR, selector)
            if jobs:
                print(f"✅ Found {len(jobs)} jobs with: {selector}")
                all_jobs.extend(jobs)

                # Click on first job found
                if jobs[0].is_displayed():
                    driver.execute_script("arguments[0].click();", jobs[0])
                    print(f"✅ Clicked on job: {jobs[0].text[:50]}")
                    time.sleep(3)
                    return True
        except Exception as e:
            continue

    print("⚠️ No job listings found")
    return False

def apply_for_job(driver):
    """Click apply button for job"""
    print("📝 Looking for apply button...")

    # Apply button selectors for SAP SuccessFactors
    apply_selectors = [
        "//button[contains(text(), 'Apply')]",
        "//a[contains(text(), 'Apply')]",
        "//button[contains(text(), 'Bewerben')]",  # German
        "//a[contains(text(), 'Bewerben')]",
        "//button[contains(@class, 'apply')]",
        "//a[contains(@class, 'apply')]",
        "//button[@data-automation-id='applyNow']",
        "//a[@data-automation-id='applyNow']"
    ]

    for xpath in apply_selectors:
        try:
            apply_btn = driver.find_element(By.XPATH, xpath)
            if apply_btn and apply_btn.is_displayed():
                print(f"✅ Found apply button")
                driver.execute_script("arguments[0].click();", apply_btn)
                time.sleep(3)
                return True
        except:
            continue

    print("⚠️ No apply button found")
    return False

def fill_application_form(driver, profile):
    """Fill out application form with profile data"""
    print("📝 Filling application form...")

    # Form field mappings
    field_mappings = [
        (profile['first_name'], [
            "input[name*='firstName']", "input[id*='firstName']",
            "input[name*='first_name']", "input[id*='first_name']",
            "input[placeholder*='First']"
        ]),
        (profile['last_name'], [
            "input[name*='lastName']", "input[id*='lastName']",
            "input[name*='last_name']", "input[id*='last_name']",
            "input[placeholder*='Last']"
        ]),
        (profile['email'], [
            "input[type='email']", "input[name*='email']",
            "input[id*='email']", "input[placeholder*='email']"
        ]),
        (profile['phone'], [
            "input[name*='phone']", "input[id*='phone']",
            "input[name*='mobile']", "input[id*='mobile']",
            "input[placeholder*='phone']"
        ])
    ]

    filled_count = 0
    for value, selectors in field_mappings:
        for selector in selectors:
            try:
                field = driver.find_element(By.CSS_SELECTOR, selector)
                if field and field.is_displayed() and field.is_enabled():
                    field.clear()
                    field.send_keys(value)
                    print(f"✅ Filled {selector}: {value}")
                    filled_count += 1
                    break
            except:
                continue

    # Handle dropdowns for country, work authorization
    try:
        # Country dropdown
        country_selectors = [
            "select[name*='country']", "select[id*='country']"
        ]
        for selector in country_selectors:
            try:
                dropdown = driver.find_element(By.CSS_SELECTOR, selector)
                if dropdown:
                    select = Select(dropdown)
                    select.select_by_visible_text("United States")
                    print("✅ Selected United States for country")
                    filled_count += 1
                    break
            except:
                continue

        # Work authorization - look for Yes/No radio buttons
        auth_radios = driver.find_elements(By.CSS_SELECTOR, "input[type='radio'][value*='yes'], input[type='radio'][value*='Yes']")
        for radio in auth_radios:
            name = radio.get_attribute("name").lower()
            if any(word in name for word in ['citizen', 'authorized', 'work', 'sponsor']):
                driver.execute_script("arguments[0].click();", radio)
                print(f"✅ Selected Yes for work authorization: {name}")
                filled_count += 1
                break

    except Exception as e:
        print(f"⚠️ Could not fill dropdowns: {e}")

    return filled_count

def upload_resume(driver, resume_path):
    """Upload resume file"""
    print("📎 Uploading resume...")

    if not os.path.exists(resume_path):
        print(f"❌ Resume not found: {resume_path}")
        return False

    # File upload selectors
    upload_selectors = [
        "input[type='file']",
        "input[accept*='pdf']",
        "input[name*='resume']",
        "input[name*='cv']",
        "input[id*='resume']",
        "input[id*='cv']"
    ]

    for selector in upload_selectors:
        try:
            upload_field = driver.find_element(By.CSS_SELECTOR, selector)
            if upload_field:
                upload_field.send_keys(resume_path)
                print("✅ Resume uploaded successfully")
                time.sleep(2)

                # Verify upload
                try:
                    if upload_field.get_attribute("value"):
                        print("✅ Upload verified - file path set")
                        return True
                except:
                    pass

                return True
        except Exception as e:
            continue

    # Try clicking upload buttons first
    upload_button_selectors = [
        "//button[contains(text(), 'Upload')]",
        "//button[contains(text(), 'Choose')]",
        "//a[contains(text(), 'Upload')]",
        "//span[contains(text(), 'Upload')]"
    ]

    for xpath in upload_button_selectors:
        try:
            button = driver.find_element(By.XPATH, xpath)
            if button and button.is_displayed():
                button.click()
                time.sleep(1)

                # Now try file inputs again
                for selector in upload_selectors:
                    try:
                        upload_field = driver.find_element(By.CSS_SELECTOR, selector)
                        if upload_field:
                            upload_field.send_keys(resume_path)
                            print("✅ Resume uploaded after clicking button")
                            return True
                    except:
                        continue
        except:
            continue

    print("⚠️ Could not upload resume")
    return False

def submit_application(driver):
    """Submit the application"""
    print("📤 Looking for submit button...")

    submit_selectors = [
        "//button[contains(text(), 'Submit')]",
        "//button[contains(text(), 'Send')]",
        "//input[@type='submit']",
        "//button[@type='submit']",
        "//button[contains(text(), 'Absenden')]",  # German
        "//button[@data-automation-id='submit']"
    ]

    for xpath in submit_selectors:
        try:
            submit_btn = driver.find_element(By.XPATH, xpath)
            if submit_btn and submit_btn.is_displayed():
                print("✅ Found submit button")
                # Don't actually submit - just show it was found
                print("⚠️ Submit button found but not clicked (manual review mode)")
                return True
        except:
            continue

    print("⚠️ No submit button found")
    return False

def main():
    print("🚀 Enhanced Nemetschek Job Application Automation")
    print("=" * 60)

    # Jiale Lin's profile data
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

    print(f"✅ Resume found: {profile['resume_path']}")
    print(f"📋 Profile: {profile['first_name']} {profile['last_name']} ({profile['email']})")

    driver = setup_driver()

    try:
        # Navigate to Nemetschek careers
        url = "https://career55.sapsf.eu/careers?company=nemetschek"
        print(f"📍 Navigating to: {url}")
        driver.get(url)
        wait_for_page_load(driver)

        print(f"✅ Page loaded: {driver.title}")

        # Search for jobs
        search_for_jobs(driver, "software engineer")
        wait_for_page_load(driver)

        # Find and select a job
        if find_jobs(driver):
            wait_for_page_load(driver)

            # Apply for the job
            if apply_for_job(driver):
                wait_for_page_load(driver)

                # Fill application form
                filled_count = fill_application_form(driver, profile)
                print(f"📊 Form fields filled: {filled_count}")

                # Upload resume
                resume_uploaded = upload_resume(driver, profile['resume_path'])

                # Look for submit button
                submit_available = submit_application(driver)

                # Summary
                print("\n" + "=" * 60)
                print("📊 AUTOMATION SUMMARY")
                print("=" * 60)
                print(f"✅ Page Navigation: Success")
                print(f"✅ Job Selection: Success")
                print(f"✅ Apply Button: Success")
                print(f"📝 Form Fields: {filled_count} filled")
                print(f"📎 Resume Upload: {'Success' if resume_uploaded else 'Failed'}")
                print(f"📤 Submit Ready: {'Yes' if submit_available else 'No'}")

                if resume_uploaded and submit_available:
                    print("\n🎉 READY FOR SUBMISSION!")
                    print("Application form is complete and ready to submit")
                else:
                    print("\n⚠️ Manual intervention needed")

        print("\n🎯 Keeping browser open for manual review...")
        print("Press Ctrl+C to close browser")

        # Keep browser open
        while True:
            time.sleep(1)

    except KeyboardInterrupt:
        print("\n✅ User terminated automation")
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        driver.quit()
        print("✅ Automation completed")

if __name__ == "__main__":
    main()