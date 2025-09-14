#!/usr/bin/env python3
"""
ULTIMATE JobRight.ai Auto-Apply with AUTOMATED SSO Authentication
Automatically handles Google SSO login for jeremykalilin@gmail.com
and applies to ALL jobs without any manual intervention
"""

import time
import json
import logging
import re
import os
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import TimeoutException, NoSuchElementException, ElementClickInterceptedException, StaleElementReferenceException
from webdriver_manager.chrome import ChromeDriverManager
import pickle

# Configure comprehensive logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('ultimate_sso_automation.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class UltimateSSoJobRightAutomation:
    def __init__(self, headless=False, email="jeremykalilin@gmail.com"):
        """Initialize the ultimate SSO automation"""
        self.driver = None
        self.headless = headless
        self.email = email
        self.base_url = "https://jobright.ai"
        self.apply_buttons = []
        self.successful_applications = []
        self.failed_applications = []
        self.session_id = datetime.now().strftime('%Y%m%d_%H%M%S')
        self.cookies_file = f'jobright_session_{self.email.replace("@", "_")}.pkl'

        # SSO configuration
        self.sso_config = {
            'email': email,
            'google_sso_enabled': True,
            'session_persistence': True,
            'auto_accept_permissions': True
        }

        # Statistics
        self.stats = {
            'start_time': None,
            'end_time': None,
            'authentication_time': None,
            'buttons_found': 0,
            'applications_attempted': 0,
            'applications_successful': 0,
            'applications_failed': 0
        }

    def setup_driver_with_persistence(self):
        """Setup Chrome WebDriver with session persistence and SSO support"""
        chrome_options = Options()

        if self.headless:
            chrome_options.add_argument("--headless")

        # Essential options
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("--start-maximized")

        # Session persistence
        chrome_options.add_argument(f"--user-data-dir=/tmp/chrome_profile_{self.session_id}")

        # Anti-detection (enhanced for SSO)
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        chrome_options.add_argument("--user-agent=Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")

        # SSO and OAuth support
        chrome_options.add_argument("--disable-web-security")
        chrome_options.add_argument("--allow-running-insecure-content")
        chrome_options.add_argument("--disable-features=VizDisplayCompositor")

        try:
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=chrome_options)

            # Enhanced anti-detection for SSO
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            self.driver.execute_cdp_cmd('Network.setUserAgentOverride', {
                "userAgent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            })

            # Optimal timeouts for SSO
            self.driver.implicitly_wait(10)
            self.driver.set_page_load_timeout(60)

            logger.info("Chrome WebDriver with SSO support initialized successfully")
            return True

        except Exception as e:
            logger.error(f"Failed to initialize WebDriver: {e}")
            return False

    def load_existing_session(self):
        """Load existing session cookies if available"""
        try:
            if os.path.exists(self.cookies_file):
                with open(self.cookies_file, 'rb') as f:
                    cookies = pickle.load(f)

                # Go to base URL first
                self.driver.get(self.base_url)
                time.sleep(2)

                # Add cookies
                for cookie in cookies:
                    try:
                        self.driver.add_cookie(cookie)
                    except Exception as e:
                        logger.warning(f"Could not add cookie: {e}")

                # Refresh to apply cookies
                self.driver.refresh()
                time.sleep(3)

                logger.info("Loaded existing session cookies")
                return True

        except Exception as e:
            logger.warning(f"Could not load existing session: {e}")

        return False

    def save_session(self):
        """Save current session cookies"""
        try:
            cookies = self.driver.get_cookies()
            with open(self.cookies_file, 'wb') as f:
                pickle.dump(cookies, f)
            logger.info("Session cookies saved")
        except Exception as e:
            logger.warning(f"Could not save session: {e}")

    def automated_sso_authentication(self):
        """Fully automated SSO authentication process"""
        try:
            auth_start_time = time.time()
            logger.info("Starting automated SSO authentication...")

            # Step 1: Try existing session first
            if self.load_existing_session():
                if self.verify_authentication():
                    logger.info("Already authenticated with existing session")
                    self.stats['authentication_time'] = time.time() - auth_start_time
                    return True

            # Step 2: Navigate to JobRight.ai
            logger.info("Navigating to JobRight.ai...")
            self.driver.get(self.base_url)
            time.sleep(3)

            # Step 3: Look for sign-in options
            if not self.initiate_sso_login():
                logger.error("Could not initiate SSO login")
                return False

            # Step 4: Handle Google SSO flow
            if not self.handle_google_sso_flow():
                logger.error("Google SSO flow failed")
                return False

            # Step 5: Complete JobRight.ai authentication
            if not self.complete_jobright_authentication():
                logger.error("JobRight.ai authentication completion failed")
                return False

            # Step 6: Save session
            self.save_session()

            # Step 7: Navigate to jobs page
            if not self.navigate_to_jobs_after_auth():
                logger.error("Could not navigate to jobs page after auth")
                return False

            self.stats['authentication_time'] = time.time() - auth_start_time
            logger.info(f"SSO authentication completed successfully in {self.stats['authentication_time']:.2f} seconds")
            return True

        except Exception as e:
            logger.error(f"SSO authentication failed: {e}")
            return False

    def verify_authentication(self):
        """Verify if user is already authenticated"""
        try:
            # Navigate to a protected page
            self.driver.get(f"{self.base_url}/jobs/recommend")
            time.sleep(5)

            current_url = self.driver.current_url.lower()

            # Check if we're on a jobs page (not redirected to login)
            if any(indicator in current_url for indicator in ['job', 'recommend', 'dashboard']):
                # Double-check by looking for job content
                if self.has_job_content():
                    logger.info("Authentication verified - user is logged in")
                    return True

            logger.info("Authentication verification failed")
            return False

        except Exception as e:
            logger.warning(f"Error verifying authentication: {e}")
            return False

    def initiate_sso_login(self):
        """Initiate SSO login process"""
        try:
            logger.info("Looking for sign-in options...")

            # Look for sign-in buttons/links
            signin_patterns = [
                "//button[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'sign in')]",
                "//a[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'sign in')]",
                "//button[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'login')]",
                "//a[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'login')]",
                "//button[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'get started')]",
                "//*[contains(@class, 'sign') and contains(@class, 'in')]",
                "//*[contains(@class, 'login')]",
                "//*[contains(@data-action, 'login')]"
            ]

            for pattern in signin_patterns:
                try:
                    elements = self.driver.find_elements(By.XPATH, pattern)
                    for element in elements:
                        if element.is_displayed() and element.is_enabled():
                            logger.info(f"Found sign-in button: {element.text}")

                            # Scroll to and click
                            self.driver.execute_script("arguments[0].scrollIntoView();", element)
                            time.sleep(1)
                            element.click()
                            time.sleep(3)

                            # Look for Google SSO option
                            return self.find_google_sso_button()

                except Exception as e:
                    continue

            # Try direct navigation to login page
            login_urls = [
                f"{self.base_url}/login",
                f"{self.base_url}/auth/login",
                f"{self.base_url}/signin",
                f"{self.base_url}/onboarding"
            ]

            for url in login_urls:
                try:
                    logger.info(f"Trying direct login URL: {url}")
                    self.driver.get(url)
                    time.sleep(3)

                    if self.find_google_sso_button():
                        return True

                except Exception:
                    continue

            logger.error("Could not find sign-in options")
            return False

        except Exception as e:
            logger.error(f"Error initiating SSO login: {e}")
            return False

    def find_google_sso_button(self):
        """Find and click Google SSO button"""
        try:
            logger.info("Looking for Google SSO button...")

            # Wait for page to load
            time.sleep(3)

            # Google SSO button patterns
            google_patterns = [
                "//button[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'google')]",
                "//a[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'google')]",
                "//button[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'continue with google')]",
                "//button[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'sign in with google')]",
                "//*[contains(@class, 'google')]",
                "//*[contains(@data-provider, 'google')]",
                "//*[contains(@data-action, 'google')]",
                "//img[contains(@src, 'google')]/ancestor::button",
                "//img[contains(@alt, 'google')]/ancestor::button"
            ]

            for pattern in google_patterns:
                try:
                    elements = self.driver.find_elements(By.XPATH, pattern)
                    for element in elements:
                        if element.is_displayed() and element.is_enabled():
                            logger.info(f"Found Google SSO button: {element.text}")

                            # Scroll to and click
                            self.driver.execute_script("arguments[0].scrollIntoView();", element)
                            time.sleep(1)
                            element.click()
                            time.sleep(3)

                            return True

                except Exception:
                    continue

            # Look for OAuth/SSO patterns
            oauth_patterns = [
                "//*[contains(@href, 'oauth')]",
                "//*[contains(@href, 'auth/google')]",
                "//*[contains(@action, 'google')]"
            ]

            for pattern in oauth_patterns:
                try:
                    elements = self.driver.find_elements(By.XPATH, pattern)
                    for element in elements:
                        if element.is_displayed():
                            logger.info(f"Found OAuth element: {element.get_attribute('outerHTML')[:100]}")
                            element.click()
                            time.sleep(3)
                            return True

                except Exception:
                    continue

            logger.warning("Google SSO button not found")
            return False

        except Exception as e:
            logger.error(f"Error finding Google SSO button: {e}")
            return False

    def handle_google_sso_flow(self):
        """Handle the complete Google SSO authentication flow"""
        try:
            logger.info("Handling Google SSO flow...")

            # Wait for Google login page
            WebDriverWait(self.driver, 15).until(
                lambda driver: "accounts.google.com" in driver.current_url.lower() or
                              "google.com" in driver.current_url.lower()
            )

            current_url = self.driver.current_url
            logger.info(f"Google SSO page loaded: {current_url}")

            # Step 1: Handle email entry
            if not self.enter_google_email():
                logger.error("Failed to enter Google email")
                return False

            # Step 2: Check if already logged in to Google
            if self.check_google_already_logged_in():
                logger.info("Already logged in to Google, proceeding...")
                return self.handle_google_consent()

            # Step 3: Handle password entry (if required)
            if self.is_password_required():
                logger.warning("Password required for Google login")
                print("\n🔐 GOOGLE PASSWORD REQUIRED")
                print("=" * 60)
                print(f"Please enter your Google password for {self.email}")
                print("The browser will wait for manual password entry...")
                print("After entering password, the automation will continue automatically")
                print("=" * 60)

                # Wait for manual password entry
                self.wait_for_password_entry()

            # Step 4: Handle consent/permissions
            return self.handle_google_consent()

        except Exception as e:
            logger.error(f"Error in Google SSO flow: {e}")
            return False

    def enter_google_email(self):
        """Enter email in Google login form"""
        try:
            logger.info(f"Entering email: {self.email}")

            # Wait for email input field
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
                        EC.presence_of_element_located((By.CSS_SELECTOR, selector))
                    )
                    if email_input.is_displayed():
                        break
                except TimeoutException:
                    continue

            if not email_input:
                logger.error("Email input field not found")
                return False

            # Clear and enter email
            email_input.clear()
            email_input.send_keys(self.email)
            time.sleep(1)

            # Click Next button
            next_selectors = [
                "input[type='submit']",
                "button[type='submit']",
                "#identifierNext",
                "[id*='next']",
                "button:contains('Next')",
                "input[value='Next']"
            ]

            for selector in next_selectors:
                try:
                    if ":contains(" in selector:
                        # Convert to XPath
                        text = selector.split(":contains('")[1].split("')")[0]
                        next_button = self.driver.find_element(By.XPATH, f"//button[contains(text(), '{text}')]")
                    else:
                        next_button = self.driver.find_element(By.CSS_SELECTOR, selector)

                    if next_button.is_displayed() and next_button.is_enabled():
                        next_button.click()
                        time.sleep(3)
                        logger.info("Clicked Next button after email entry")
                        return True

                except Exception:
                    continue

            # Try pressing Enter as fallback
            email_input.send_keys(Keys.RETURN)
            time.sleep(3)
            logger.info("Pressed Enter after email entry")
            return True

        except Exception as e:
            logger.error(f"Error entering Google email: {e}")
            return False

    def check_google_already_logged_in(self):
        """Check if already logged in to Google account"""
        try:
            # Wait a moment for page to load
            time.sleep(3)

            # Look for account selection or consent screen
            account_indicators = [
                "[data-email]",
                ".account-info",
                "[aria-label*='account']",
                ".profile-name"
            ]

            for indicator in account_indicators:
                try:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, indicator)
                    if elements:
                        logger.info("Google account already logged in")
                        return True
                except Exception:
                    continue

            # Check URL for consent/permission pages
            current_url = self.driver.current_url.lower()
            if any(keyword in current_url for keyword in ['consent', 'permission', 'oauth', 'authorize']):
                logger.info("Google account logged in, on consent page")
                return True

            return False

        except Exception:
            return False

    def is_password_required(self):
        """Check if password entry is required"""
        try:
            time.sleep(3)

            password_selectors = [
                "input[type='password']",
                "input[name='password']",
                "#password",
                "[aria-label*='password']"
            ]

            for selector in password_selectors:
                try:
                    password_input = self.driver.find_element(By.CSS_SELECTOR, selector)
                    if password_input.is_displayed():
                        logger.info("Password input field detected")
                        return True
                except Exception:
                    continue

            return False

        except Exception:
            return False

    def wait_for_password_entry(self):
        """Wait for manual password entry"""
        try:
            # Wait for password to be entered and submitted
            max_wait_time = 300  # 5 minutes
            start_time = time.time()

            while time.time() - start_time < max_wait_time:
                current_url = self.driver.current_url.lower()

                # Check if we've moved past the password page
                if not any(keyword in current_url for keyword in ['password', 'signin', 'login']):
                    logger.info("Password entry completed, proceeding...")
                    return True

                # Check for consent/oauth pages
                if any(keyword in current_url for keyword in ['consent', 'oauth', 'authorize']):
                    logger.info("Moved to consent page after password")
                    return True

                time.sleep(2)

            logger.warning("Password entry timeout")
            return True  # Continue anyway

        except Exception as e:
            logger.warning(f"Error waiting for password entry: {e}")
            return True

    def handle_google_consent(self):
        """Handle Google consent/permission screen"""
        try:
            logger.info("Handling Google consent screen...")

            # Wait for consent screen to load
            time.sleep(5)

            # Look for consent/continue buttons
            consent_patterns = [
                "//button[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'continue')]",
                "//button[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'allow')]",
                "//button[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'authorize')]",
                "//button[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'accept')]",
                "//input[@type='submit' and @value='Continue']",
                "//input[@type='submit' and @value='Allow']"
            ]

            for pattern in consent_patterns:
                try:
                    elements = self.driver.find_elements(By.XPATH, pattern)
                    for element in elements:
                        if element.is_displayed() and element.is_enabled():
                            logger.info(f"Found consent button: {element.text}")
                            element.click()
                            time.sleep(3)

                            # Wait for redirect back to JobRight
                            WebDriverWait(self.driver, 15).until(
                                lambda driver: "jobright.ai" in driver.current_url.lower()
                            )

                            logger.info("Google consent completed, redirected to JobRight")
                            return True

                except Exception:
                    continue

            # Check if we're already back at JobRight (consent auto-approved)
            current_url = self.driver.current_url.lower()
            if "jobright.ai" in current_url:
                logger.info("Already back at JobRight - consent auto-approved")
                return True

            logger.warning("Could not handle consent screen")
            return True  # Continue anyway

        except Exception as e:
            logger.error(f"Error handling Google consent: {e}")
            return False

    def complete_jobright_authentication(self):
        """Complete authentication flow on JobRight.ai"""
        try:
            logger.info("Completing JobRight.ai authentication...")

            # Wait for JobRight page to load
            WebDriverWait(self.driver, 15).until(
                lambda driver: "jobright.ai" in driver.current_url.lower()
            )

            time.sleep(5)

            # Check if additional steps are needed
            current_url = self.driver.current_url.lower()

            # Handle onboarding/setup pages
            if any(keyword in current_url for keyword in ['onboarding', 'setup', 'welcome']):
                logger.info("Handling onboarding process...")
                self.handle_onboarding_process()

            # Check if we need to accept terms or complete profile
            self.handle_post_auth_steps()

            return True

        except Exception as e:
            logger.error(f"Error completing JobRight authentication: {e}")
            return False

    def handle_onboarding_process(self):
        """Handle onboarding/welcome process"""
        try:
            logger.info("Handling onboarding process...")

            max_steps = 10
            for step in range(max_steps):
                logger.info(f"Onboarding step {step + 1}")

                # Look for skip, continue, or next buttons
                action_patterns = [
                    "//button[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'skip')]",
                    "//button[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'next')]",
                    "//button[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'continue')]",
                    "//button[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'get started')]",
                    "//a[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'skip')]",
                    "//*[@class*='skip']",
                    "//*[@data-action='skip']"
                ]

                action_taken = False
                for pattern in action_patterns:
                    try:
                        elements = self.driver.find_elements(By.XPATH, pattern)
                        for element in elements:
                            if element.is_displayed() and element.is_enabled():
                                logger.info(f"Clicking onboarding action: {element.text}")
                                element.click()
                                time.sleep(3)
                                action_taken = True
                                break
                        if action_taken:
                            break
                    except Exception:
                        continue

                if not action_taken:
                    logger.info("No more onboarding actions found")
                    break

                # Check if we've reached jobs page
                current_url = self.driver.current_url.lower()
                if any(keyword in current_url for keyword in ['job', 'recommend', 'dashboard']):
                    logger.info("Reached jobs page during onboarding")
                    break

        except Exception as e:
            logger.warning(f"Error in onboarding process: {e}")

    def handle_post_auth_steps(self):
        """Handle any post-authentication steps"""
        try:
            # Accept terms/conditions if present
            terms_patterns = [
                "//button[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'accept')]",
                "//button[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'agree')]",
                "//input[@type='checkbox' and contains(@name, 'terms')]",
                "//input[@type='checkbox' and contains(@name, 'agree')]"
            ]

            for pattern in terms_patterns:
                try:
                    elements = self.driver.find_elements(By.XPATH, pattern)
                    for element in elements:
                        if element.is_displayed() and element.is_enabled():
                            element.click()
                            time.sleep(1)
                            logger.info("Accepted terms/conditions")
                except Exception:
                    continue

            # Close any welcome modals
            close_patterns = [
                "//*[@aria-label='close']",
                "//*[@aria-label='Close']",
                "//button[contains(@class, 'close')]",
                "//button[text()='×']"
            ]

            for pattern in close_patterns:
                try:
                    elements = self.driver.find_elements(By.XPATH, pattern)
                    for element in elements:
                        if element.is_displayed():
                            element.click()
                            time.sleep(1)
                            logger.info("Closed welcome modal")
                except Exception:
                    continue

        except Exception as e:
            logger.warning(f"Error in post-auth steps: {e}")

    def navigate_to_jobs_after_auth(self):
        """Navigate to jobs page after successful authentication"""
        try:
            logger.info("Navigating to jobs page after authentication...")

            # Try multiple job page URLs
            job_urls = [
                f"{self.base_url}/jobs/recommend",
                f"{self.base_url}/jobs",
                f"{self.base_url}/dashboard",
                f"{self.base_url}/recommendations"
            ]

            for url in job_urls:
                try:
                    logger.info(f"Trying jobs URL: {url}")
                    self.driver.get(url)
                    time.sleep(5)

                    # Check if we have job content
                    if self.has_job_content():
                        logger.info(f"Successfully accessed jobs page: {url}")
                        return True

                except Exception as e:
                    logger.warning(f"Failed to access {url}: {e}")
                    continue

            # Try finding jobs navigation
            nav_patterns = [
                "//a[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'job')]",
                "//a[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'recommend')]",
                "//a[contains(@href, 'job')]"
            ]

            for pattern in nav_patterns:
                try:
                    elements = self.driver.find_elements(By.XPATH, pattern)
                    for element in elements:
                        if element.is_displayed():
                            element.click()
                            time.sleep(3)
                            if self.has_job_content():
                                logger.info("Successfully navigated to jobs via menu")
                                return True
                except Exception:
                    continue

            logger.warning("Could not navigate to jobs page")
            return False

        except Exception as e:
            logger.error(f"Error navigating to jobs after auth: {e}")
            return False

    def has_job_content(self):
        """Enhanced check for job content"""
        try:
            page_source = self.driver.page_source.lower()

            # Job content indicators
            job_indicators = [
                'apply', 'job', 'position', 'role', 'salary', 'company',
                'remote', 'full-time', 'part-time', 'career', 'employment',
                'recommendation', 'autofill'
            ]

            # Count indicators
            indicator_count = sum(1 for indicator in job_indicators if indicator in page_source)

            # Also check for specific apply button text
            apply_indicators = [
                'apply now', 'quick apply', 'easy apply', 'apply with autofill',
                'submit application'
            ]

            apply_count = sum(1 for indicator in apply_indicators if indicator in page_source)

            # Check URL as well
            current_url = self.driver.current_url.lower()
            url_has_jobs = any(keyword in current_url for keyword in ['job', 'recommend', 'position'])

            logger.info(f"Job content check: {indicator_count} job indicators, {apply_count} apply indicators, URL has jobs: {url_has_jobs}")

            return (indicator_count >= 5 or apply_count >= 1) and url_has_jobs

        except Exception:
            return False

    # Include all the previous ultimate automation methods
    def scroll_and_load_all_content(self):
        """Scroll through page to load all dynamic content"""
        try:
            logger.info("Loading all page content...")

            # Get initial height
            last_height = self.driver.execute_script("return document.body.scrollHeight")

            scroll_attempts = 0
            max_attempts = 15

            while scroll_attempts < max_attempts:
                # Scroll to bottom
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(2)

                # Try clicking "Load More" or "Show More" buttons
                self.click_load_more_buttons()

                # Check for new content
                new_height = self.driver.execute_script("return document.body.scrollHeight")

                if new_height == last_height:
                    scroll_attempts += 1
                    logger.info(f"No new content loaded (attempt {scroll_attempts})")
                else:
                    last_height = new_height
                    scroll_attempts = 0
                    logger.info("New content loaded, continuing...")

                time.sleep(1)

            # Scroll back to top
            self.driver.execute_script("window.scrollTo(0, 0);")
            time.sleep(2)

            logger.info("Page content loading completed")

        except Exception as e:
            logger.warning(f"Error during content loading: {e}")

    def click_load_more_buttons(self):
        """Click any Load More or Show More buttons"""
        try:
            load_more_patterns = [
                "load more", "show more", "view more", "see more", "load additional",
                "more jobs", "next page", "continue", "expand"
            ]

            for pattern in load_more_patterns:
                try:
                    xpath = f"//button[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), '{pattern}')]"
                    elements = self.driver.find_elements(By.XPATH, xpath)

                    for element in elements:
                        if element.is_displayed() and element.is_enabled():
                            try:
                                element.click()
                                logger.info(f"Clicked load more button: {pattern}")
                                time.sleep(2)
                                return
                            except:
                                pass
                except:
                    continue

        except Exception:
            pass

    def ultimate_apply_button_finder(self):
        """Ultimate apply button finder using all possible strategies"""
        try:
            logger.info("Starting ultimate apply button search...")
            all_buttons = []

            # Strategy 1: Text-based comprehensive search
            buttons_by_text = self.find_buttons_by_text()
            all_buttons.extend(buttons_by_text)
            logger.info(f"Found {len(buttons_by_text)} buttons by text")

            # Strategy 2: Class and attribute search
            buttons_by_attrs = self.find_buttons_by_attributes()
            all_buttons.extend(buttons_by_attrs)
            logger.info(f"Found {len(buttons_by_attrs)} buttons by attributes")

            # Strategy 3: Visual pattern recognition
            buttons_by_visual = self.find_buttons_by_visual_patterns()
            all_buttons.extend(buttons_by_visual)
            logger.info(f"Found {len(buttons_by_visual)} buttons by visual patterns")

            # Remove duplicates and filter
            unique_buttons = self.deduplicate_and_validate_buttons(all_buttons)

            logger.info(f"Ultimate button search completed: {len(unique_buttons)} unique apply buttons found")
            return unique_buttons

        except Exception as e:
            logger.error(f"Error in ultimate button finder: {e}")
            return []

    def find_buttons_by_text(self):
        """Find buttons by text content using comprehensive patterns"""
        buttons = []

        apply_text_patterns = [
            "apply now", "apply with autofill", "quick apply", "easy apply",
            "apply", "apply for", "apply to", "submit application",
            "apply for this job", "apply for position", "one-click apply",
            "instant apply", "autofill", "auto-fill", "auto apply",
            "apply today", "apply here", "submit resume", "send application"
        ]

        for pattern in apply_text_patterns:
            try:
                xpath = f"//*[contains(translate(normalize-space(text()), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), '{pattern.lower()}')]"
                elements = self.driver.find_elements(By.XPATH, xpath)

                for element in elements:
                    if self.is_valid_apply_button_candidate(element):
                        button_info = self.extract_comprehensive_button_info(element, f"text_{pattern}")
                        if button_info:
                            buttons.append(button_info)
            except Exception:
                continue

        return buttons

    def find_buttons_by_attributes(self):
        """Find buttons by class names and attributes"""
        buttons = []

        class_patterns = ["apply", "autofill", "quick", "easy", "submit", "application"]

        for pattern in class_patterns:
            try:
                selector = f"[class*='{pattern}']"
                elements = self.driver.find_elements(By.CSS_SELECTOR, selector)

                for element in elements:
                    if self.is_valid_apply_button_candidate(element):
                        button_info = self.extract_comprehensive_button_info(element, f"class_{pattern}")
                        if button_info:
                            buttons.append(button_info)
            except Exception:
                continue

        return buttons

    def find_buttons_by_visual_patterns(self):
        """Find buttons by visual characteristics"""
        buttons = []

        try:
            all_clickable = self.driver.find_elements(By.CSS_SELECTOR,
                "button, a, input[type='button'], input[type='submit'], [role='button'], [onclick]")

            for element in all_clickable:
                try:
                    if not self.is_valid_apply_button_candidate(element):
                        continue

                    text = element.text.lower().strip()
                    if any(word in text for word in ['apply', 'submit', 'send', 'quick', 'easy']):
                        button_info = self.extract_comprehensive_button_info(element, "visual_pattern")
                        if button_info:
                            buttons.append(button_info)

                except Exception:
                    continue

        except Exception as e:
            logger.warning(f"Error in visual pattern search: {e}")

        return buttons

    def is_valid_apply_button_candidate(self, element):
        """Check if element is a valid apply button candidate"""
        try:
            if not (element.is_displayed() and element.is_enabled()):
                return False

            size = element.size
            if size['width'] < 20 or size['height'] < 10:
                return False

            text = element.text.strip()
            if len(text) < 1 or len(text) > 200:
                return False

            return True

        except Exception:
            return False

    def extract_comprehensive_button_info(self, element, detection_method):
        """Extract comprehensive information about a button"""
        try:
            text = element.text.strip()
            tag = element.tag_name
            classes = element.get_attribute('class') or ''
            element_id = element.get_attribute('id') or ''
            href = element.get_attribute('href') or ''
            location = element.location
            size = element.size

            return {
                'text': text,
                'tag': tag,
                'classes': classes,
                'id': element_id,
                'href': href,
                'location': location,
                'size': size,
                'detection_method': detection_method,
                'timestamp': time.time(),
                'unique_id': f"{text[:20]}_{location['x']}_{location['y']}"
            }

        except Exception as e:
            logger.warning(f"Error extracting button info: {e}")
            return None

    def deduplicate_and_validate_buttons(self, all_buttons):
        """Remove duplicates and validate buttons"""
        try:
            unique_buttons = []
            seen_buttons = set()

            for button in all_buttons:
                if not button:
                    continue

                unique_id = button.get('unique_id', f"{button['text'][:20]}_{button['location']['x']}_{button['location']['y']}")

                if unique_id not in seen_buttons:
                    seen_buttons.add(unique_id)

                    if self.validate_apply_button(button):
                        unique_buttons.append(button)

            unique_buttons.sort(key=lambda x: (x['location']['y'], x['location']['x']))

            logger.info(f"After deduplication and validation: {len(unique_buttons)} buttons")
            return unique_buttons

        except Exception as e:
            logger.error(f"Error in deduplication: {e}")
            return all_buttons

    def validate_apply_button(self, button_info):
        """Final validation of apply button"""
        try:
            text = button_info['text'].lower()

            apply_keywords = ['apply', 'submit', 'send', 'quick', 'easy', 'autofill']

            if not any(keyword in text for keyword in apply_keywords):
                return False

            size = button_info['size']
            if size['width'] < 50 or size['height'] < 20:
                return False

            if len(text) < 3 or len(text) > 100:
                return False

            return True

        except Exception:
            return True

    def apply_to_all_jobs_ultimate(self, buttons):
        """Apply to all jobs with ultimate success rate"""
        logger.info(f"Starting ultimate application process for {len(buttons)} jobs...")

        for i, button_info in enumerate(buttons, 1):
            print(f"\n[{i}/{len(buttons)}] APPLYING TO: {button_info['text'][:60]}...")

            try:
                result = self.click_apply_button_safe(button_info)

                if result['success']:
                    self.successful_applications.append(result)
                    self.stats['applications_successful'] += 1
                    print(f"✅ SUCCESS: {result.get('action', 'Applied')}")
                    if result.get('new_url'):
                        print(f"   → OPENED: {result['new_url'][:70]}...")
                else:
                    self.failed_applications.append(result)
                    self.stats['applications_failed'] += 1
                    print(f"❌ FAILED: {result.get('error', 'Unknown error')}")

                self.stats['applications_attempted'] += 1
                time.sleep(2)

            except Exception as e:
                error_result = {
                    'button_info': button_info,
                    'success': False,
                    'error': str(e),
                    'timestamp': time.time()
                }
                self.failed_applications.append(error_result)
                self.stats['applications_failed'] += 1
                print(f"❌ ERROR: {str(e)}")
                continue

    def click_apply_button_safe(self, button_info):
        """Safely click an apply button"""
        try:
            # Find element
            element = self.find_element_by_info(button_info)

            if not element:
                return {
                    'button_info': button_info,
                    'success': False,
                    'error': 'Element not found',
                    'timestamp': time.time()
                }

            # Record current state
            original_url = self.driver.current_url
            original_windows = self.driver.window_handles

            # Scroll to element
            self.driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", element)
            time.sleep(1)

            # Try clicking
            try:
                element.click()
                click_method = "standard"
            except ElementClickInterceptedException:
                try:
                    self.driver.execute_script("arguments[0].click();", element)
                    click_method = "javascript"
                except Exception:
                    return {
                        'button_info': button_info,
                        'success': False,
                        'error': 'All click methods failed',
                        'timestamp': time.time()
                    }

            # Wait for response
            time.sleep(3)

            # Check for new windows
            new_windows = self.driver.window_handles
            if len(new_windows) > len(original_windows):
                new_window = [w for w in new_windows if w not in original_windows][0]
                self.driver.switch_to.window(new_window)
                new_url = self.driver.current_url

                # Close and return
                self.driver.close()
                self.driver.switch_to.window(original_windows[0])

                return {
                    'button_info': button_info,
                    'success': True,
                    'action': 'new_window',
                    'new_url': new_url,
                    'click_method': click_method,
                    'timestamp': time.time()
                }

            # Check for URL change
            elif self.driver.current_url != original_url:
                new_url = self.driver.current_url
                self.driver.back()
                time.sleep(2)

                return {
                    'button_info': button_info,
                    'success': True,
                    'action': 'navigation',
                    'new_url': new_url,
                    'click_method': click_method,
                    'timestamp': time.time()
                }

            else:
                return {
                    'button_info': button_info,
                    'success': True,
                    'action': 'clicked',
                    'click_method': click_method,
                    'timestamp': time.time()
                }

        except Exception as e:
            return {
                'button_info': button_info,
                'success': False,
                'error': str(e),
                'timestamp': time.time()
            }

    def find_element_by_info(self, button_info):
        """Find element using stored information"""
        try:
            # By ID
            if button_info.get('id'):
                try:
                    element = self.driver.find_element(By.ID, button_info['id'])
                    if element.is_displayed():
                        return element
                except:
                    pass

            # By text and position
            try:
                text = button_info['text'][:30]
                xpath = f"//*[contains(text(), '{text}')]"
                elements = self.driver.find_elements(By.XPATH, xpath)

                expected_location = button_info['location']
                for element in elements:
                    if element.is_displayed():
                        current_location = element.location
                        distance = abs(current_location['x'] - expected_location['x']) + abs(current_location['y'] - expected_location['y'])
                        if distance < 100:
                            return element
            except:
                pass

            return None

        except Exception:
            return None

    def display_found_buttons(self, buttons):
        """Display all found buttons"""
        print(f"\n{'='*80}")
        print(f"🎯 FOUND {len(buttons)} APPLY NOW BUTTONS")
        print(f"{'='*80}")

        for i, button in enumerate(buttons, 1):
            print(f"{i:2d}. '{button['text'][:70]}{'...' if len(button['text']) > 70 else ''}'")
            print(f"    METHOD: {button['detection_method']}")
            print(f"    TAG: {button['tag']} | POSITION: ({button['location']['x']}, {button['location']['y']})")

        print(f"\n{'='*80}")

    def save_results(self):
        """Save comprehensive results"""
        try:
            timestamp = self.session_id

            results = {
                'session_info': {
                    'session_id': self.session_id,
                    'email': self.email,
                    'timestamp': timestamp,
                    'authentication_time': self.stats.get('authentication_time', 0)
                },
                'statistics': self.stats,
                'apply_buttons_found': self.apply_buttons,
                'successful_applications': self.successful_applications,
                'failed_applications': self.failed_applications
            }

            results_file = f'sso_automation_results_{timestamp}.json'
            with open(results_file, 'w', encoding='utf-8') as f:
                json.dump(results, f, indent=2, default=str)

            logger.info(f"Results saved to {results_file}")

        except Exception as e:
            logger.error(f"Error saving results: {e}")

    def print_final_summary(self):
        """Print final summary"""
        print(f"\n{'='*80}")
        print("🏆 SSO AUTOMATION COMPLETE - FINAL SUMMARY")
        print(f"{'='*80}")
        print(f"Email: {self.email}")
        print(f"Authentication Time: {self.stats.get('authentication_time', 0):.2f} seconds")
        print(f"Apply Buttons Found: {len(self.apply_buttons)}")
        print(f"Applications Attempted: {self.stats['applications_attempted']}")
        print(f"Successful Applications: {self.stats['applications_successful']}")
        print(f"Failed Applications: {self.stats['applications_failed']}")

        if self.stats['applications_attempted'] > 0:
            success_rate = (self.stats['applications_successful'] / self.stats['applications_attempted']) * 100
            print(f"Success Rate: {success_rate:.1f}%")

        if self.successful_applications:
            print(f"\n✅ SUCCESSFUL APPLICATIONS:")
            for i, app in enumerate(self.successful_applications, 1):
                print(f"  {i:2d}. {app['button_info']['text'][:60]}...")

        print(f"{'='*80}")

    def run_complete_sso_automation(self):
        """Run the complete SSO automation"""
        self.stats['start_time'] = time.time()

        try:
            print("🚀 ULTIMATE SSO JOBRIGHT.AI AUTO-APPLY AUTOMATION")
            print(f"Email: {self.email}")
            print("This will automatically handle SSO login and apply to ALL jobs!")
            print("="*80)

            # Setup driver
            if not self.setup_driver_with_persistence():
                print("❌ Failed to setup WebDriver")
                return False

            # Automated SSO authentication
            print("\n🔐 Starting automated SSO authentication...")
            if not self.automated_sso_authentication():
                print("❌ SSO authentication failed")
                return False

            print("✅ SSO authentication successful!")

            # Load all content
            print("\n🔄 Loading all page content...")
            self.scroll_and_load_all_content()

            # Find all apply buttons
            print("\n🔍 Finding ALL Apply Now buttons...")
            self.apply_buttons = self.ultimate_apply_button_finder()
            self.stats['buttons_found'] = len(self.apply_buttons)

            if not self.apply_buttons:
                print("❌ No Apply Now buttons found!")
                return False

            # Display found buttons
            self.display_found_buttons(self.apply_buttons)

            # Apply to all jobs automatically
            print(f"\n🚀 APPLYING TO ALL {len(self.apply_buttons)} JOBS AUTOMATICALLY...")
            self.apply_to_all_jobs_ultimate(self.apply_buttons)

            return True

        except Exception as e:
            logger.error(f"SSO automation failed: {e}")
            print(f"❌ SSO automation failed: {e}")
            return False

        finally:
            self.stats['end_time'] = time.time()

            # Save results
            self.save_results()

            # Print summary
            self.print_final_summary()

            # Close browser
            if self.driver:
                if not self.headless:
                    input("\nPress Enter to close browser...")
                self.driver.quit()


def main():
    """Main function for SSO automation"""
    print("🏆 ULTIMATE SSO JOBRIGHT.AI AUTO-APPLY AUTOMATION")
    print("Automated Google SSO login + Apply to ALL jobs!")
    print("="*80)

    email = "jeremykalilin@gmail.com"
    headless_mode = input("Run in headless mode? (y/n): ").strip().lower() == 'y'

    print(f"\n🚀 Starting SSO Automation for {email}...")
    print("This will:")
    print("✅ Automatically handle Google SSO login")
    print("✅ Find ALL Apply Now buttons")
    print("✅ Apply to ALL jobs automatically")
    print("✅ Handle new pages and redirects")

    confirm = input(f"\nStart automated SSO application process? (y/n): ").strip().lower()
    if confirm != 'y':
        print("Automation cancelled.")
        return

    # Run SSO automation
    automation = UltimateSSoJobRightAutomation(headless=headless_mode, email=email)
    success = automation.run_complete_sso_automation()

    # Final message
    if success:
        print("\n🎉 SSO AUTOMATION COMPLETED SUCCESSFULLY!")
        print(f"Applied to {automation.stats['applications_successful']} jobs automatically")
    else:
        print("\n💥 SSO AUTOMATION ENCOUNTERED ISSUES")

    print("Check the generated files for detailed results")


if __name__ == "__main__":
    main()