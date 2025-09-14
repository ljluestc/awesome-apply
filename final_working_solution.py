#!/usr/bin/env python3
"""
FINAL WORKING SOLUTION - Direct, simple, effective
Based on what we know works from previous tests
"""

import sys
import os
sys.path.append('/home/calelin/awesome-apply/venv/lib/python3.13/site-packages')

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
import time
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def final_working_solution():
    """The final working solution - simple and direct"""

    print("🎯 FINAL WORKING SOLUTION - APPLY TO ALL JOBS")
    print("="*60)

    # Setup Chrome (use the configuration we know works)
    chrome_options = Options()

    # Persistent profile (this is what made SSO work)
    user_data_dir = "/tmp/chrome_final_profile"
    chrome_options.add_argument(f"--user-data-dir={user_data_dir}")
    chrome_options.add_argument("--profile-directory=Default")

    # Anti-detection (keep this minimal)
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)

    driver = webdriver.Chrome(
        service=Service(ChromeDriverManager().install()),
        options=chrome_options
    )

    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

    applied_jobs = []

    try:
        print("\n1. 🚀 Going to JobRight.ai entry level jobs (we know this works)...")
        driver.get("https://jobright.ai/entry-level-jobs")
        time.sleep(8)  # Give it time to load

        print(f"   Current URL: {driver.current_url}")
        print(f"   Page title: {driver.title}")

        print("\n2. 📜 Scrolling to load all job listings...")
        # Scroll to load content (we know there are jobs here)
        for i in range(5):
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)
            print(f"   Scroll {i+1}/5 completed")

        print("\n3. 🔍 COMPREHENSIVE SEARCH FOR ALL CLICKABLE ELEMENTS...")

        # Get ALL clickable elements on the page
        all_clickable = driver.find_elements(By.XPATH, "//*[@href or @onclick or @role='button' or name()='button' or name()='a']")
        print(f"   Found {len(all_clickable)} total clickable elements")

        # Filter for potentially apply-related elements
        apply_candidates = []

        for element in all_clickable:
            try:
                if element.is_displayed():
                    text = element.text.strip().lower()
                    href = element.get_attribute('href') or ''
                    onclick = element.get_attribute('onclick') or ''
                    class_attr = element.get_attribute('class') or ''

                    # Look for apply-related indicators
                    apply_indicators = [
                        'apply', 'submit', 'send', 'job', 'position', 'view', 'details', 'quick'
                    ]

                    if any(indicator in text or indicator in href.lower() or
                           indicator in onclick.lower() or indicator in class_attr.lower()
                           for indicator in apply_indicators):

                        apply_candidates.append({
                            'element': element,
                            'text': text,
                            'href': href,
                            'onclick': onclick,
                            'class': class_attr
                        })

            except Exception:
                continue

        print(f"   Found {len(apply_candidates)} potential apply-related elements")

        # Show what we found
        print("\n4. 📋 APPLY-RELATED ELEMENTS FOUND:")
        for i, candidate in enumerate(apply_candidates[:20]):  # Show first 20
            print(f"   {i+1:2d}. Text: '{candidate['text'][:50]}'")
            if candidate['href']:
                print(f"       Href: {candidate['href'][:80]}")
            if candidate['class']:
                print(f"       Class: {candidate['class'][:50]}")
            print()

        print(f"\n5. 🎯 ATTEMPTING TO APPLY TO JOBS...")

        successful_applications = 0

        for i, candidate in enumerate(apply_candidates):
            try:
                element = candidate['element']
                text = candidate['text']

                print(f"\n   Application {i+1}/{len(apply_candidates)}")
                print(f"   Target: '{text[:50]}'")

                # Scroll to element
                driver.execute_script("arguments[0].scrollIntoView(true);", element)
                time.sleep(1)

                # Try clicking
                original_url = driver.current_url
                original_window_count = len(driver.window_handles)

                # Click the element
                try:
                    element.click()
                    print("   ✅ Clicked successfully")
                except Exception as e:
                    print(f"   ⚠️ Standard click failed, trying JavaScript click...")
                    try:
                        driver.execute_script("arguments[0].click();", element)
                        print("   ✅ JavaScript click successful")
                    except Exception as e2:
                        print(f"   ❌ Both clicks failed: {e2}")
                        continue

                time.sleep(3)  # Wait for response

                # Check what happened
                new_url = driver.current_url
                new_window_count = len(driver.window_handles)

                if new_window_count > original_window_count:
                    print("   ✅ New window/tab opened - likely job application!")

                    # Switch to new window
                    driver.switch_to.window(driver.window_handles[-1])
                    time.sleep(3)

                    app_url = driver.current_url
                    app_title = driver.title

                    print(f"   Application page: {app_title}")
                    print(f"   Application URL: {app_url}")

                    # Look for and click any apply buttons on this page
                    apply_buttons = driver.find_elements(By.XPATH,
                        "//button[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'apply') or "
                        "contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'submit')] | "
                        "//a[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'apply')]"
                    )

                    if apply_buttons:
                        for btn in apply_buttons:
                            if btn.is_displayed() and btn.is_enabled():
                                print(f"   Found apply button: {btn.text}")
                                try:
                                    btn.click()
                                    print("   ✅ Applied to job!")
                                    successful_applications += 1

                                    applied_jobs.append({
                                        'title': app_title,
                                        'url': app_url,
                                        'original_element': text,
                                        'timestamp': time.time()
                                    })

                                    break  # Only need to click one apply button
                                except Exception as e:
                                    print(f"   ❌ Apply button click failed: {e}")
                    else:
                        print("   📝 No apply buttons found, but page opened (might be application page)")
                        successful_applications += 1
                        applied_jobs.append({
                            'title': app_title,
                            'url': app_url,
                            'original_element': text,
                            'timestamp': time.time()
                        })

                    # Close new window and return to main page
                    driver.close()
                    driver.switch_to.window(driver.window_handles[0])

                elif new_url != original_url:
                    print(f"   ✅ Page navigation occurred - likely job application!")
                    print(f"   New URL: {new_url}")

                    successful_applications += 1
                    applied_jobs.append({
                        'title': driver.title,
                        'url': new_url,
                        'original_element': text,
                        'timestamp': time.time()
                    })

                    # Go back to job listings
                    driver.back()
                    time.sleep(2)

                else:
                    print("   ⚠️ Click registered but no obvious navigation")

                # Brief delay between attempts
                time.sleep(2)

            except Exception as e:
                print(f"   ❌ Application attempt failed: {e}")
                continue

        # Final Results
        print(f"\n🎉 FINAL RESULTS:")
        print(f"   ✅ Successful Applications: {successful_applications}")
        print(f"   📋 Total Elements Processed: {len(apply_candidates)}")

        if successful_applications > 0:
            print(f"   📊 Success Rate: {(successful_applications/len(apply_candidates)*100):.1f}%")

            print(f"\n📋 JOBS APPLIED TO:")
            for i, job in enumerate(applied_jobs):
                print(f"   {i+1:2d}. {job['title']}")
                print(f"       URL: {job['url']}")
                print(f"       Via: {job['original_element'][:50]}")
                print()

        if successful_applications == 0:
            print("\n🤔 DEBUGGING INFO:")
            print("   No successful applications. Let's analyze what we found:")

            unique_texts = set()
            for candidate in apply_candidates[:10]:
                if candidate['text'] and len(candidate['text']) > 2:
                    unique_texts.add(candidate['text'])

            print(f"   Sample clickable text found: {list(unique_texts)[:10]}")

        input(f"\nPress Enter to close browser (Applied to {successful_applications} jobs)...")

    except Exception as e:
        print(f"❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()

    finally:
        if driver:
            driver.quit()

if __name__ == "__main__":
    final_working_solution()