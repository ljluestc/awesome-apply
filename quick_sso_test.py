#!/usr/bin/env python3
"""
Quick SSO Test - Fast discovery and testing
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
import time

def quick_sso_test():
    print("🚀 QUICK SSO DISCOVERY TEST")
    print("="*50)

    # Setup Chrome
    chrome_options = Options()
    # chrome_options.add_argument("--headless")  # Comment out to see browser
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

    try:
        # Step 1: Visit main page and discover structure
        print("\n1. Discovering JobRight.ai structure...")
        driver.get("https://jobright.ai")
        time.sleep(5)

        print(f"Current URL: {driver.current_url}")
        print(f"Page title: {driver.title}")

        # Look for sign in / login buttons
        print("\n2. Looking for sign-in options...")

        login_selectors = [
            "//a[contains(text(), 'Sign')]",
            "//a[contains(text(), 'Log')]",
            "//button[contains(text(), 'Sign')]",
            "//button[contains(text(), 'Log')]",
            "//*[contains(@class, 'login')]",
            "//*[contains(@class, 'signin')]",
            "//*[contains(@href, 'login')]",
            "//*[contains(@href, 'signin')]",
            "//*[contains(@href, 'auth')]"
        ]

        found_elements = []
        for selector in login_selectors:
            try:
                elements = driver.find_elements(By.XPATH, selector)
                for elem in elements:
                    if elem.is_displayed():
                        text = elem.text.strip()
                        href = elem.get_attribute('href') or 'N/A'
                        onclick = elem.get_attribute('onclick') or 'N/A'
                        found_elements.append({
                            'text': text,
                            'href': href,
                            'onclick': onclick,
                            'element': elem
                        })
            except Exception:
                continue

        print(f"Found {len(found_elements)} potential login elements:")
        for i, elem_info in enumerate(found_elements):
            print(f"  {i+1}. Text: '{elem_info['text']}'")
            print(f"     Href: {elem_info['href']}")
            print(f"     Onclick: {elem_info['onclick']}")
            print()

        # Step 3: Try clicking the most promising login element
        if found_elements:
            print("3. Trying to click most promising login element...")
            best_element = found_elements[0]['element']
            try:
                best_element.click()
                time.sleep(5)

                print(f"After click - Current URL: {driver.current_url}")

                # Look for Google SSO options
                print("\n4. Looking for Google SSO options...")
                google_selectors = [
                    "//*[contains(text(), 'Google')]",
                    "//*[contains(@class, 'google')]",
                    "//*[contains(@href, 'google')]",
                    "//*[contains(@onclick, 'google')]"
                ]

                google_elements = []
                for selector in google_selectors:
                    try:
                        elements = driver.find_elements(By.XPATH, selector)
                        for elem in elements:
                            if elem.is_displayed():
                                text = elem.text.strip()
                                href = elem.get_attribute('href') or 'N/A'
                                google_elements.append({
                                    'text': text,
                                    'href': href,
                                    'element': elem
                                })
                    except Exception:
                        continue

                print(f"Found {len(google_elements)} Google SSO elements:")
                for i, elem_info in enumerate(google_elements):
                    print(f"  {i+1}. Text: '{elem_info['text']}'")
                    print(f"     Href: {elem_info['href']}")
                    print()

                # Try clicking Google SSO if found
                if google_elements:
                    print("5. Clicking Google SSO...")
                    try:
                        google_elements[0]['element'].click()
                        time.sleep(5)

                        print(f"After Google SSO click - URL: {driver.current_url}")

                        if 'google' in driver.current_url.lower():
                            print("✅ SUCCESS: Redirected to Google SSO!")
                        else:
                            print("❌ No redirect to Google detected")

                    except Exception as e:
                        print(f"❌ Failed to click Google SSO: {e}")
                else:
                    print("❌ No Google SSO options found")

            except Exception as e:
                print(f"❌ Failed to click login element: {e}")
        else:
            print("❌ No login elements found on main page")

        input("\nPress Enter to close browser...")

    except Exception as e:
        print(f"❌ Test failed: {e}")

    finally:
        driver.quit()

if __name__ == "__main__":
    quick_sso_test()