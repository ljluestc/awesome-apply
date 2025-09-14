#!/usr/bin/env python3
"""
Comprehensive JobRight.ai Discovery
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
import json

def comprehensive_discovery():
    print("🔍 COMPREHENSIVE JOBRIGHT.AI DISCOVERY")
    print("="*60)

    chrome_options = Options()
    # Run visible to see what's happening
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
        # Step 1: Visit main page and wait for full load
        print("\n1. Loading JobRight.ai and waiting for dynamic content...")
        driver.get("https://jobright.ai")
        time.sleep(8)  # Wait longer for JavaScript to load

        print(f"Current URL: {driver.current_url}")
        print(f"Page title: {driver.title}")

        # Check if we need to scroll or interact to reveal content
        print("\n2. Checking page dimensions and scrolling...")
        page_height = driver.execute_script("return Math.max( document.body.scrollHeight, document.body.offsetHeight, document.documentElement.clientHeight, document.documentElement.scrollHeight, document.documentElement.offsetHeight );")
        print(f"Page height: {page_height}px")

        # Scroll to reveal content
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight/3);")
        time.sleep(2)
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight/2);")
        time.sleep(2)
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(2)
        driver.execute_script("window.scrollTo(0, 0);")
        time.sleep(2)

        # Step 3: Comprehensive element discovery
        print("\n3. Comprehensive element discovery...")

        # Get all clickable elements
        all_clickable = driver.find_elements(By.XPATH, "//*[@href or @onclick or @role='button' or name()='button' or name()='a']")
        print(f"Found {len(all_clickable)} clickable elements")

        auth_related = []
        for elem in all_clickable:
            try:
                if elem.is_displayed():
                    text = elem.text.strip().lower()
                    href = (elem.get_attribute('href') or '').lower()
                    onclick = (elem.get_attribute('onclick') or '').lower()
                    class_attr = (elem.get_attribute('class') or '').lower()
                    id_attr = (elem.get_attribute('id') or '').lower()

                    # Check if auth-related
                    auth_keywords = [
                        'sign', 'log', 'auth', 'login', 'signin', 'register',
                        'account', 'profile', 'user', 'google', 'oauth'
                    ]

                    is_auth_related = any(
                        keyword in text or keyword in href or
                        keyword in onclick or keyword in class_attr or
                        keyword in id_attr
                        for keyword in auth_keywords
                    )

                    if is_auth_related:
                        auth_related.append({
                            'text': elem.text.strip(),
                            'href': elem.get_attribute('href') or '',
                            'onclick': elem.get_attribute('onclick') or '',
                            'class': elem.get_attribute('class') or '',
                            'id': elem.get_attribute('id') or '',
                            'tag': elem.tag_name,
                            'element': elem
                        })

            except Exception as e:
                continue

        print(f"\nFound {len(auth_related)} authentication-related elements:")
        for i, elem_info in enumerate(auth_related):
            print(f"\n{i+1}. {elem_info['tag'].upper()}: '{elem_info['text']}'")
            if elem_info['href']:
                print(f"   Href: {elem_info['href']}")
            if elem_info['class']:
                print(f"   Class: {elem_info['class']}")
            if elem_info['id']:
                print(f"   ID: {elem_info['id']}")

        # Step 4: Try different strategies to find auth
        print("\n4. Trying different discovery strategies...")

        strategies = [
            # Strategy 1: Look for job board features that might require login
            {
                'name': 'Job Board Navigation',
                'selectors': [
                    "//*[contains(text(), 'Jobs')]",
                    "//*[contains(text(), 'Search')]",
                    "//*[contains(text(), 'Apply')]",
                    "//*[contains(@href, 'job')]",
                    "//*[contains(@href, 'search')]"
                ]
            },
            # Strategy 2: Look for user-related features
            {
                'name': 'User Features',
                'selectors': [
                    "//*[contains(text(), 'Profile')]",
                    "//*[contains(text(), 'Dashboard')]",
                    "//*[contains(text(), 'My')]",
                    "//*[contains(@class, 'user')]",
                    "//*[contains(@class, 'profile')]"
                ]
            }
        ]

        for strategy in strategies:
            print(f"\n   Trying strategy: {strategy['name']}")
            for selector in strategy['selectors']:
                try:
                    elements = driver.find_elements(By.XPATH, selector)
                    for elem in elements[:3]:  # Check first 3 matches
                        if elem.is_displayed():
                            print(f"     Found: '{elem.text.strip()}' -> {elem.get_attribute('href') or 'No href'}")

                            # Try clicking promising elements
                            elem_text = elem.text.strip().lower()
                            if any(word in elem_text for word in ['jobs', 'search', 'dashboard']):
                                try:
                                    print(f"     Clicking: {elem.text.strip()}")
                                    elem.click()
                                    time.sleep(5)
                                    print(f"     New URL: {driver.current_url}")

                                    # Check if this revealed login options
                                    login_check = driver.find_elements(By.XPATH, "//*[contains(text(), 'Sign') or contains(text(), 'Log') or contains(@href, 'auth')]")
                                    if login_check:
                                        print(f"     ✅ Found {len(login_check)} login options after click!")
                                        for login_elem in login_check[:3]:
                                            if login_elem.is_displayed():
                                                print(f"       Login option: '{login_elem.text.strip()}'")
                                    return driver.current_url
                                except Exception as e:
                                    print(f"     ❌ Click failed: {e}")
                                    continue
                except Exception:
                    continue

        # Step 5: Check what the most common job board URLs might be
        print("\n5. Trying common job board URL patterns...")
        test_urls = [
            "https://jobright.ai/jobs",
            "https://jobright.ai/dashboard",
            "https://jobright.ai/search",
            "https://jobright.ai/browse",
            "https://jobright.ai/recommendations",
            "https://app.jobright.ai",
            "https://app.jobright.ai/login",
            "https://app.jobright.ai/dashboard"
        ]

        for url in test_urls:
            try:
                print(f"   Trying: {url}")
                driver.get(url)
                time.sleep(3)

                current = driver.current_url
                title = driver.title
                print(f"     Result: {current} -> {title}")

                # Check if this page has login options
                login_check = driver.find_elements(By.XPATH, "//*[contains(text(), 'Sign') or contains(text(), 'Log') or contains(@href, 'google') or contains(@class, 'google')]")
                if login_check:
                    print(f"     ✅ Found {len(login_check)} login/auth elements!")
                    for elem in login_check[:5]:
                        if elem.is_displayed():
                            print(f"       - '{elem.text.strip()}' | {elem.get_attribute('href') or 'No href'}")

                    return current

            except Exception as e:
                print(f"     ❌ Failed: {e}")

        print("\n❌ No clear authentication path found")
        print("💡 The site might require a different approach or be a SPA")

        return None

    except Exception as e:
        print(f"❌ Discovery failed: {e}")
        return None

    finally:
        input("\nPress Enter to close browser...")
        driver.quit()

if __name__ == "__main__":
    result = comprehensive_discovery()
    if result:
        print(f"\n🎯 Best URL found: {result}")
    else:
        print("\n❌ No authentication entry point discovered")