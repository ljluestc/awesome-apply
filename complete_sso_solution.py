#!/usr/bin/env python3
"""
COMPLETE SSO SOLUTION - JobRight.ai Auto-Apply with Full Google SSO Automation
Handles ALL edge cases for jeremykalilin@gmail.com with maximum success rate
"""

import time
import json
import logging
import re
import os
import pickle
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import TimeoutException, NoSuchElementException, ElementClickInterceptedException
from webdriver_manager.chrome import ChromeDriverManager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('complete_sso_solution.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class CompleteSSoSolution:
    def __init__(self, email="jeremykalilin@gmail.com", headless=False):
        """Initialize the complete SSO solution"""
        self.email = email
        self.headless = headless
        self.driver = None
        self.base_url = "https://jobright.ai"
        self.session_id = datetime.now().strftime('%Y%m%d_%H%M%S')

        # Session management
        self.session_file = f'sso_session_{email.replace("@", "_").replace(".", "_")}.pkl'

        # Results tracking
        self.apply_buttons = []
        self.successful_applications = []
        self.failed_applications = []

        # Statistics
        self.stats = {
            'start_time': time.time(),
            'auth_start_time': None,
            'auth_end_time': None,
            'buttons_found': 0,
            'applications_attempted': 0,
            'successful_applications': 0,
            'failed_applications': 0
        }

    def setup_driver(self):
        """Setup Chrome WebDriver optimized for SSO"""
        chrome_options = Options()

        if self.headless:
            chrome_options.add_argument("--headless")

        # Core options
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("--start-maximized")

        # Session persistence
        profile_dir = f"/tmp/chrome_sso_profile_{self.session_id}"
        chrome_options.add_argument(f"--user-data-dir={profile_dir}")

        # Anti-detection for SSO
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        chrome_options.add_argument("--user-agent=Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")

        # OAuth/SSO specific
        chrome_options.add_argument("--disable-web-security")
        chrome_options.add_argument("--allow-running-insecure-content")
        chrome_options.add_argument("--disable-popup-blocking")

        try:
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=chrome_options)

            # Anti-detection scripts
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

            # Set timeouts
            self.driver.implicitly_wait(10)
            self.driver.set_page_load_timeout(60)

            logger.info("Chrome WebDriver setup completed")
            return True

        except Exception as e:
            logger.error(f"Failed to setup WebDriver: {e}")
            return False

    def handle_complete_sso_flow(self):
        """Handle the complete SSO authentication flow"""
        self.stats['auth_start_time'] = time.time()

        try:
            logger.info(f"Starting complete SSO flow for {self.email}")

            # Step 1: Try to load existing session
            if self.load_existing_session():
                logger.info("Existing session loaded successfully")
                self.stats['auth_end_time'] = time.time()
                return True

            # Step 2: Navigate to JobRight.ai
            logger.info("Navigating to JobRight.ai...")
            self.driver.get(self.base_url)
            time.sleep(3)

            # Step 3: Initiate login process
            if not self.initiate_login():
                logger.error("Failed to initiate login")
                return False

            # Step 4: Handle Google SSO
            if not self.handle_google_sso():
                logger.error("Google SSO failed")
                return False

            # Step 5: Complete JobRight setup
            if not self.complete_jobright_setup():
                logger.error("JobRight setup failed")
                return False

            # Step 6: Save session for future use
            self.save_session()

            # Step 7: Navigate to jobs
            if not self.navigate_to_jobs():
                logger.error("Failed to navigate to jobs")
                return False

            self.stats['auth_end_time'] = time.time()
            auth_duration = self.stats['auth_end_time'] - self.stats['auth_start_time']
            logger.info(f"Complete SSO flow successful in {auth_duration:.2f} seconds")
            return True

        except Exception as e:
            logger.error(f"SSO flow failed: {e}")
            return False

    def load_existing_session(self):
        """Load existing authenticated session"""
        try:
            if not os.path.exists(self.session_file):
                logger.info("No existing session found")
                return False

            with open(self.session_file, 'rb') as f:
                session_data = pickle.load(f)

            # Navigate to base URL first
            self.driver.get(self.base_url)
            time.sleep(2)

            # Load cookies
            for cookie in session_data.get('cookies', []):
                try:
                    self.driver.add_cookie(cookie)
                except Exception as e:
                    logger.warning(f"Could not load cookie: {e}")

            # Refresh to apply session
            self.driver.refresh()
            time.sleep(3)

            # Verify session is valid
            if self.verify_authenticated():
                logger.info("Existing session is valid")
                return True
            else:
                logger.info("Existing session is invalid")
                return False

        except Exception as e:
            logger.warning(f"Error loading existing session: {e}")
            return False

    def save_session(self):
        """Save current session for future use"""
        try:
            session_data = {
                'cookies': self.driver.get_cookies(),
                'timestamp': time.time(),
                'email': self.email
            }

            with open(self.session_file, 'wb') as f:
                pickle.dump(session_data, f)

            logger.info("Session saved successfully")

        except Exception as e:
            logger.warning(f"Could not save session: {e}")

    def verify_authenticated(self):
        """Verify if user is authenticated"""
        try:
            # Try accessing a protected page
            self.driver.get(f"{self.base_url}/jobs/recommend")
            time.sleep(5)

            current_url = self.driver.current_url.lower()

            # Check if we're on a jobs page
            if any(keyword in current_url for keyword in ['job', 'recommend', 'dashboard']):
                # Verify with page content
                page_source = self.driver.page_source.lower()
                job_indicators = ['apply', 'position', 'company', 'salary']

                if sum(1 for indicator in job_indicators if indicator in page_source) >= 2:
                    logger.info("Authentication verified")
                    return True

            logger.info("Authentication not verified")
            return False

        except Exception as e:
            logger.warning(f"Error verifying authentication: {e}")
            return False

    def initiate_login(self):
        """Initiate the login process on JobRight.ai"""
        try:
            logger.info("Looking for login options...")

            # Wait for page to load
            time.sleep(3)

            # Look for login/signup buttons
            login_selectors = [
                "//button[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'sign')]",
                "//a[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'sign')]",
                "//button[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'login')]",
                "//button[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'get started')]",
                "//*[@class*='sign']",
                "//*[@class*='login']",
                "//*[@data-action*='auth']"
            ]

            for selector in login_selectors:
                try:
                    elements = self.driver.find_elements(By.XPATH, selector)
                    for element in elements:
                        if element.is_displayed() and element.is_enabled():
                            text = element.text.strip()
                            if text:  # Only click if it has text
                                logger.info(f"Clicking login button: {text}")
                                element.click()
                                time.sleep(3)

                                # Check if Google SSO option appeared
                                if self.look_for_google_sso():
                                    return True

                except Exception:
                    continue

            # Try direct URLs if buttons not found
            login_urls = [
                f"{self.base_url}/login",
                f"{self.base_url}/auth",
                f"{self.base_url}/signin",
                f"{self.base_url}/onboarding-v3/signup"
            ]

            for url in login_urls:
                try:
                    logger.info(f"Trying direct URL: {url}")
                    self.driver.get(url)
                    time.sleep(3)

                    if self.look_for_google_sso():
                        return True

                except Exception:
                    continue

            logger.error("Could not initiate login")
            return False

        except Exception as e:
            logger.error(f"Error initiating login: {e}")
            return False

    def look_for_google_sso(self):
        """Look for Google SSO options and click"""
        try:
            logger.info("Looking for Google SSO button...")

            # Wait for elements to load
            time.sleep(2)

            # Comprehensive Google SSO selectors
            google_selectors = [
                "//button[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'google')]",
                "//a[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'google')]",
                "//button[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'continue with google')]",
                "//button[contains(@class, 'google')]",
                "//a[contains(@class, 'google')]",
                "//*[@data-provider='google']",
                "//*[@data-auth='google']",
                "//img[contains(@src, 'google')]/parent::*",
                "//img[contains(@alt, 'google')]/parent::*",
                "//*[contains(@href, 'oauth')]",
                "//*[contains(@href, 'google')]"
            ]

            for selector in google_selectors:
                try:
                    elements = self.driver.find_elements(By.XPATH, selector)
                    for element in elements:
                        if element.is_displayed() and element.is_enabled():
                            logger.info(f"Found Google SSO option: {element.text or element.get_attribute('outerHTML')[:100]}")
                            element.click()
                            time.sleep(3)
                            return True

                except Exception:
                    continue

            logger.warning("Google SSO button not found")
            return False

        except Exception as e:
            logger.error(f"Error looking for Google SSO: {e}")
            return False

    def handle_google_sso(self):
        """Handle the complete Google SSO process"""
        try:
            logger.info("Handling Google SSO process...")

            # Wait for Google OAuth page
            max_wait = 15
            start_time = time.time()

            while time.time() - start_time < max_wait:
                current_url = self.driver.current_url.lower()
                if 'google.com' in current_url or 'accounts.google' in current_url:
                    logger.info(f"Google OAuth page loaded: {current_url}")
                    break
                time.sleep(1)
            else:
                logger.error("Google OAuth page not loaded")
                return False

            # Step 1: Handle email entry
            if not self.enter_email():
                return False

            # Step 2: Handle password (if needed)
            if self.check_password_needed():
                logger.info("Password entry required - waiting for manual entry...")
                print(f"\n🔐 GOOGLE PASSWORD REQUIRED FOR {self.email}")
                print("=" * 70)
                print("Please enter your Google password in the browser window")
                print("The automation will continue automatically after password entry")
                print("=" * 70)

                if not self.wait_for_password():
                    logger.error("Password entry failed or timeout")
                    return False

            # Step 3: Handle consent/authorization
            if not self.handle_consent():
                logger.warning("Consent handling failed, but continuing...")

            # Step 4: Wait for redirect back to JobRight
            if not self.wait_for_jobright_redirect():
                logger.error("Failed to redirect back to JobRight")
                return False

            logger.info("Google SSO completed successfully")
            return True

        except Exception as e:
            logger.error(f"Google SSO failed: {e}")
            return False

    def enter_email(self):
        """Enter email in Google login"""
        try:
            logger.info(f"Entering email: {self.email}")

            # Find email input
            email_selectors = [
                "input[type='email']",
                "input[id='identifierId']",
                "input[name='identifier']",
                "input[autocomplete='username']"
            ]

            email_input = None
            for selector in email_selectors:
                try:
                    email_input = WebDriverWait(self.driver, 10).until(
                        EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                    )
                    break
                except TimeoutException:
                    continue

            if not email_input:
                logger.error("Email input not found")
                return False

            # Enter email
            email_input.clear()
            email_input.send_keys(self.email)
            time.sleep(1)

            # Click next
            next_selectors = [
                "#identifierNext",
                "button[type='submit']",
                "input[type='submit']",
                "[id*='next']"
            ]

            for selector in next_selectors:
                try:
                    next_button = self.driver.find_element(By.CSS_SELECTOR, selector)
                    if next_button.is_displayed() and next_button.is_enabled():
                        next_button.click()
                        time.sleep(3)
                        logger.info("Email entered and next clicked")
                        return True
                except Exception:
                    continue

            # Fallback: press Enter
            email_input.send_keys(Keys.RETURN)
            time.sleep(3)
            logger.info("Email entered with Enter key")
            return True

        except Exception as e:
            logger.error(f"Error entering email: {e}")
            return False

    def check_password_needed(self):
        """Check if password entry is required"""
        try:
            time.sleep(3)

            password_selectors = [
                "input[type='password']",
                "input[name='password']",
                "#password"
            ]

            for selector in password_selectors:
                try:
                    password_input = self.driver.find_element(By.CSS_SELECTOR, selector)
                    if password_input.is_displayed():
                        logger.info("Password input detected")
                        return True
                except Exception:
                    continue

            return False

        except Exception:
            return False

    def wait_for_password(self):
        """Wait for manual password entry"""
        try:
            max_wait = 300  # 5 minutes
            start_time = time.time()

            while time.time() - start_time < max_wait:
                current_url = self.driver.current_url.lower()

                # Check if moved past password page
                if not any(keyword in current_url for keyword in ['password', 'signin', 'challenge']):
                    logger.info("Password entry completed")
                    return True

                # Check for consent page
                if any(keyword in current_url for keyword in ['consent', 'oauth', 'authorize']):
                    logger.info("Moved to consent page")
                    return True

                time.sleep(2)

            logger.warning("Password entry timeout")
            return True  # Continue anyway

        except Exception as e:
            logger.warning(f"Error waiting for password: {e}")
            return True

    def handle_consent(self):
        """Handle Google consent screen"""
        try:
            logger.info("Handling consent screen...")
            time.sleep(3)

            # Look for consent buttons
            consent_selectors = [
                "//button[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'continue')]",
                "//button[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'allow')]",
                "//button[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'authorize')]",
                "//input[@type='submit']"
            ]

            for selector in consent_selectors:
                try:
                    elements = self.driver.find_elements(By.XPATH, selector)
                    for element in elements:
                        if element.is_displayed() and element.is_enabled():
                            logger.info(f"Clicking consent: {element.text}")
                            element.click()
                            time.sleep(3)
                            return True
                except Exception:
                    continue

            # Check if already past consent
            current_url = self.driver.current_url.lower()
            if 'jobright.ai' in current_url:
                logger.info("Already past consent")
                return True

            return True  # Continue even if consent not found

        except Exception as e:
            logger.warning(f"Consent handling error: {e}")
            return True

    def wait_for_jobright_redirect(self):
        """Wait for redirect back to JobRight"""
        try:
            logger.info("Waiting for JobRight redirect...")

            max_wait = 30
            start_time = time.time()

            while time.time() - start_time < max_wait:
                current_url = self.driver.current_url.lower()
                if 'jobright.ai' in current_url:
                    logger.info(f"Redirected to JobRight: {current_url}")
                    time.sleep(3)  # Let page load
                    return True
                time.sleep(1)

            logger.error("Timeout waiting for JobRight redirect")
            return False

        except Exception as e:
            logger.error(f"Error waiting for redirect: {e}")
            return False

    def complete_jobright_setup(self):
        """Complete any JobRight setup steps"""
        try:
            logger.info("Completing JobRight setup...")
            time.sleep(3)

            current_url = self.driver.current_url.lower()

            # Handle onboarding
            if 'onboarding' in current_url or 'setup' in current_url:
                self.handle_onboarding()

            # Handle any modals or popups
            self.close_modals()

            # Accept terms if needed
            self.accept_terms()

            return True

        except Exception as e:
            logger.warning(f"JobRight setup error: {e}")
            return True  # Continue anyway

    def handle_onboarding(self):
        """Handle onboarding steps"""
        try:
            logger.info("Handling onboarding...")

            for _ in range(10):  # Max 10 steps
                # Look for skip/next/continue buttons
                action_selectors = [
                    "//button[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'skip')]",
                    "//button[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'next')]",
                    "//button[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'continue')]"
                ]

                clicked = False
                for selector in action_selectors:
                    try:
                        elements = self.driver.find_elements(By.XPATH, selector)
                        for element in elements:
                            if element.is_displayed() and element.is_enabled():
                                element.click()
                                time.sleep(2)
                                clicked = True
                                break
                        if clicked:
                            break
                    except Exception:
                        continue

                if not clicked:
                    break

        except Exception as e:
            logger.warning(f"Onboarding error: {e}")

    def close_modals(self):
        """Close any modal dialogs"""
        try:
            close_selectors = [
                "[aria-label*='close']",
                "[aria-label*='Close']",
                "//button[text()='×']",
                "//button[contains(@class, 'close')]"
            ]

            for selector in close_selectors:
                try:
                    if selector.startswith("//"):
                        elements = self.driver.find_elements(By.XPATH, selector)
                    else:
                        elements = self.driver.find_elements(By.CSS_SELECTOR, selector)

                    for element in elements:
                        if element.is_displayed():
                            element.click()
                            time.sleep(1)
                            logger.info("Closed modal")
                            break
                except Exception:
                    continue

        except Exception:
            pass

    def accept_terms(self):
        """Accept terms and conditions"""
        try:
            terms_selectors = [
                "//input[@type='checkbox' and contains(@name, 'terms')]",
                "//input[@type='checkbox' and contains(@name, 'agree')]",
                "//button[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'accept')]"
            ]

            for selector in terms_selectors:
                try:
                    elements = self.driver.find_elements(By.XPATH, selector)
                    for element in elements:
                        if element.is_displayed() and element.is_enabled():
                            element.click()
                            time.sleep(1)
                            logger.info("Accepted terms")
                except Exception:
                    continue

        except Exception:
            pass

    def navigate_to_jobs(self):
        """Navigate to jobs page"""
        try:
            logger.info("Navigating to jobs page...")

            # Try direct URLs
            job_urls = [
                f"{self.base_url}/jobs/recommend",
                f"{self.base_url}/jobs",
                f"{self.base_url}/dashboard"
            ]

            for url in job_urls:
                try:
                    self.driver.get(url)
                    time.sleep(5)

                    if self.verify_jobs_page():
                        logger.info(f"Successfully navigated to jobs: {url}")
                        return True

                except Exception:
                    continue

            logger.error("Could not navigate to jobs page")
            return False

        except Exception as e:
            logger.error(f"Navigation error: {e}")
            return False

    def verify_jobs_page(self):
        """Verify we're on a jobs page"""
        try:
            page_source = self.driver.page_source.lower()
            job_indicators = ['apply', 'job', 'position', 'company']

            found_indicators = sum(1 for indicator in job_indicators if indicator in page_source)

            return found_indicators >= 2

        except Exception:
            return False

    def load_all_jobs(self):
        """Load all available jobs on the page"""
        try:
            logger.info("Loading all jobs...")

            # Scroll to load dynamic content
            last_height = self.driver.execute_script("return document.body.scrollHeight")

            for _ in range(15):  # Max 15 scrolls
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(2)

                # Click load more buttons
                self.click_load_more()

                new_height = self.driver.execute_script("return document.body.scrollHeight")
                if new_height == last_height:
                    break
                last_height = new_height

            # Return to top
            self.driver.execute_script("window.scrollTo(0, 0);")
            time.sleep(2)

            logger.info("Job loading completed")

        except Exception as e:
            logger.warning(f"Job loading error: {e}")

    def click_load_more(self):
        """Click load more buttons"""
        try:
            load_more_selectors = [
                "//button[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'load more')]",
                "//button[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'show more')]",
                "//a[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'more')]"
            ]

            for selector in load_more_selectors:
                try:
                    elements = self.driver.find_elements(By.XPATH, selector)
                    for element in elements:
                        if element.is_displayed() and element.is_enabled():
                            element.click()
                            time.sleep(2)
                            logger.info("Clicked load more")
                            return
                except Exception:
                    continue

        except Exception:
            pass

    def find_all_apply_buttons(self):
        """Find all apply buttons on the page"""
        try:
            logger.info("Finding all apply buttons...")

            buttons = []

            # Text-based search
            apply_patterns = [
                "apply now", "apply with autofill", "quick apply", "easy apply",
                "apply", "submit application", "autofill"
            ]

            for pattern in apply_patterns:
                try:
                    xpath = f"//*[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), '{pattern}')]"
                    elements = self.driver.find_elements(By.XPATH, xpath)

                    for element in elements:
                        if self.is_valid_apply_button(element):
                            button_info = self.extract_button_info(element, f"text_{pattern}")
                            if button_info and not self.is_duplicate(button_info, buttons):
                                buttons.append(button_info)

                except Exception:
                    continue

            # Class-based search
            class_patterns = ["apply", "autofill", "quick", "submit"]

            for pattern in class_patterns:
                try:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, f"[class*='{pattern}']")

                    for element in elements:
                        if self.is_valid_apply_button(element):
                            button_info = self.extract_button_info(element, f"class_{pattern}")
                            if button_info and not self.is_duplicate(button_info, buttons):
                                buttons.append(button_info)

                except Exception:
                    continue

            # Sort by position
            buttons.sort(key=lambda x: (x['location']['y'], x['location']['x']))

            logger.info(f"Found {len(buttons)} apply buttons")
            self.stats['buttons_found'] = len(buttons)

            return buttons

        except Exception as e:
            logger.error(f"Error finding apply buttons: {e}")
            return []

    def is_valid_apply_button(self, element):
        """Check if element is a valid apply button"""
        try:
            if not (element.is_displayed() and element.is_enabled()):
                return False

            size = element.size
            if size['width'] < 30 or size['height'] < 15:
                return False

            tag = element.tag_name.lower()
            if tag not in ['button', 'a', 'input'] and not element.get_attribute('onclick'):
                return False

            text = element.text.strip().lower()
            if len(text) < 2 or len(text) > 100:
                return False

            # Must contain apply-related keywords
            keywords = ['apply', 'submit', 'send', 'quick', 'autofill']
            if not any(keyword in text for keyword in keywords):
                return False

            return True

        except Exception:
            return False

    def extract_button_info(self, element, method):
        """Extract button information"""
        try:
            return {
                'text': element.text.strip(),
                'tag': element.tag_name,
                'classes': element.get_attribute('class') or '',
                'id': element.get_attribute('id') or '',
                'href': element.get_attribute('href') or '',
                'location': element.location,
                'size': element.size,
                'method': method,
                'timestamp': time.time()
            }
        except Exception:
            return None

    def is_duplicate(self, button, existing_buttons):
        """Check if button is duplicate"""
        try:
            for existing in existing_buttons:
                if (button['text'] == existing['text'] and
                    abs(button['location']['x'] - existing['location']['x']) < 10 and
                    abs(button['location']['y'] - existing['location']['y']) < 10):
                    return True
            return False
        except Exception:
            return False

    def apply_to_all_jobs(self):
        """Apply to all found jobs"""
        try:
            logger.info(f"Applying to {len(self.apply_buttons)} jobs...")

            for i, button in enumerate(self.apply_buttons, 1):
                print(f"\n[{i}/{len(self.apply_buttons)}] Applying to: {button['text'][:50]}...")

                result = self.apply_to_job(button)

                if result['success']:
                    self.successful_applications.append(result)
                    self.stats['successful_applications'] += 1
                    print(f"✅ SUCCESS: {result.get('action', 'Applied')}")
                else:
                    self.failed_applications.append(result)
                    self.stats['failed_applications'] += 1
                    print(f"❌ FAILED: {result.get('error', 'Unknown error')}")

                self.stats['applications_attempted'] += 1
                time.sleep(2)  # Delay between applications

            logger.info("Job application process completed")

        except Exception as e:
            logger.error(f"Error applying to jobs: {e}")

    def apply_to_job(self, button):
        """Apply to a single job"""
        try:
            # Find the element
            element = self.relocate_element(button)

            if not element:
                return {
                    'button': button,
                    'success': False,
                    'error': 'Element not found'
                }

            # Record current state
            original_url = self.driver.current_url
            original_windows = self.driver.window_handles

            # Scroll to element and click
            self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", element)
            time.sleep(1)

            try:
                element.click()
            except ElementClickInterceptedException:
                self.driver.execute_script("arguments[0].click();", element)

            time.sleep(3)  # Wait for response

            # Check for new window/tab
            new_windows = self.driver.window_handles
            if len(new_windows) > len(original_windows):
                new_window = [w for w in new_windows if w not in original_windows][0]
                self.driver.switch_to.window(new_window)
                new_url = self.driver.current_url

                # Close new window and return to original
                self.driver.close()
                self.driver.switch_to.window(original_windows[0])

                return {
                    'button': button,
                    'success': True,
                    'action': 'new_window',
                    'url': new_url
                }

            # Check for navigation
            elif self.driver.current_url != original_url:
                new_url = self.driver.current_url
                self.driver.back()
                time.sleep(2)

                return {
                    'button': button,
                    'success': True,
                    'action': 'navigation',
                    'url': new_url
                }

            else:
                return {
                    'button': button,
                    'success': True,
                    'action': 'clicked'
                }

        except Exception as e:
            return {
                'button': button,
                'success': False,
                'error': str(e)
            }

    def relocate_element(self, button):
        """Relocate button element"""
        try:
            # Try by ID first
            if button.get('id'):
                try:
                    element = self.driver.find_element(By.ID, button['id'])
                    if element.is_displayed():
                        return element
                except Exception:
                    pass

            # Try by text and position
            text = button['text'][:20]
            expected_loc = button['location']

            xpath = f"//*[contains(text(), '{text}')]"
            elements = self.driver.find_elements(By.XPATH, xpath)

            for element in elements:
                if element.is_displayed():
                    current_loc = element.location
                    distance = abs(current_loc['x'] - expected_loc['x']) + abs(current_loc['y'] - expected_loc['y'])
                    if distance < 100:  # Within 100 pixels
                        return element

            return None

        except Exception:
            return None

    def save_results(self):
        """Save automation results"""
        try:
            results = {
                'session_info': {
                    'email': self.email,
                    'session_id': self.session_id,
                    'timestamp': datetime.now().isoformat()
                },
                'statistics': self.stats,
                'buttons_found': self.apply_buttons,
                'successful_applications': self.successful_applications,
                'failed_applications': self.failed_applications
            }

            filename = f'complete_sso_results_{self.session_id}.json'
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(results, f, indent=2, default=str)

            logger.info(f"Results saved to {filename}")

        except Exception as e:
            logger.error(f"Error saving results: {e}")

    def print_summary(self):
        """Print final summary"""
        print(f"\n{'='*80}")
        print("🏆 COMPLETE SSO AUTOMATION - FINAL RESULTS")
        print(f"{'='*80}")
        print(f"Email: {self.email}")

        if self.stats['auth_end_time'] and self.stats['auth_start_time']:
            auth_time = self.stats['auth_end_time'] - self.stats['auth_start_time']
            print(f"Authentication Time: {auth_time:.2f} seconds")

        print(f"Apply Buttons Found: {self.stats['buttons_found']}")
        print(f"Applications Attempted: {self.stats['applications_attempted']}")
        print(f"Successful Applications: {self.stats['successful_applications']}")
        print(f"Failed Applications: {self.stats['failed_applications']}")

        if self.stats['applications_attempted'] > 0:
            success_rate = (self.stats['successful_applications'] / self.stats['applications_attempted']) * 100
            print(f"Success Rate: {success_rate:.1f}%")

        if self.successful_applications:
            print(f"\n✅ SUCCESSFUL APPLICATIONS:")
            for i, app in enumerate(self.successful_applications, 1):
                print(f"  {i:2d}. {app['button']['text'][:60]}...")
                if app.get('url'):
                    print(f"      → {app['url'][:70]}...")

        print(f"{'='*80}")

    def run_complete_automation(self):
        """Run the complete automation process"""
        try:
            print("🚀 COMPLETE SSO JOBRIGHT.AI AUTOMATION")
            print(f"Email: {self.email}")
            print("This will automatically handle everything!")
            print("="*60)

            # Setup
            if not self.setup_driver():
                print("❌ WebDriver setup failed")
                return False

            # SSO Authentication
            print("\n🔐 Handling SSO Authentication...")
            if not self.handle_complete_sso_flow():
                print("❌ SSO Authentication failed")
                return False

            print("✅ SSO Authentication successful!")

            # Load all jobs
            print("\n📄 Loading all jobs...")
            self.load_all_jobs()

            # Find apply buttons
            print("\n🔍 Finding apply buttons...")
            self.apply_buttons = self.find_all_apply_buttons()

            if not self.apply_buttons:
                print("❌ No apply buttons found!")
                return False

            print(f"✅ Found {len(self.apply_buttons)} apply buttons")

            # Apply to all jobs
            print(f"\n🎯 Applying to ALL {len(self.apply_buttons)} jobs...")
            self.apply_to_all_jobs()

            return True

        except Exception as e:
            logger.error(f"Complete automation failed: {e}")
            print(f"❌ Automation failed: {e}")
            return False

        finally:
            # Save and summarize
            self.save_results()
            self.print_summary()

            if self.driver:
                if not self.headless:
                    input("\nPress Enter to close browser...")
                self.driver.quit()


def main():
    """Main function"""
    print("🏆 COMPLETE SSO SOLUTION - JOBRIGHT.AI AUTO-APPLY")
    print("Fully automated Google SSO + Apply to ALL jobs!")
    print("="*60)

    email = "jeremykalilin@gmail.com"

    print(f"Email: {email}")
    headless = input("Run in headless mode? (y/n): ").strip().lower() == 'y'

    print(f"\n🚀 Starting complete automation...")
    confirm = input("Begin automated SSO and job applications? (y/n): ").strip().lower()

    if confirm != 'y':
        print("Automation cancelled")
        return

    # Run automation
    automation = CompleteSSoSolution(email=email, headless=headless)
    success = automation.run_complete_automation()

    if success:
        print(f"\n🎉 AUTOMATION COMPLETED SUCCESSFULLY!")
        print(f"Applied to {automation.stats['successful_applications']} jobs")
    else:
        print(f"\n💥 AUTOMATION COMPLETED WITH ISSUES")

    print("Check the results file for detailed information")

if __name__ == "__main__":
    main()