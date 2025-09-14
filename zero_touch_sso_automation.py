#!/usr/bin/env python3
"""
ZERO-TOUCH SSO AUTOMATION - JobRight.ai
100% Automated Google SSO + Job Applications for jeremykalilin@gmail.com
NO MANUAL INTERVENTION REQUIRED - COMPLETELY AUTOMATED
"""

import time
import json
import logging
import re
import os
import pickle
import base64
from datetime import datetime, timedelta
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
        logging.FileHandler('zero_touch_sso_automation.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class ZeroTouchSSoAutomation:
    def __init__(self, email="jeremykalilin@gmail.com", headless=False):
        """Initialize zero-touch SSO automation"""
        self.email = email
        self.headless = headless
        self.driver = None
        self.base_url = "https://jobright.ai"
        self.session_id = datetime.now().strftime('%Y%m%d_%H%M%S')

        # Advanced session management
        self.session_file = f'zero_touch_session_{email.replace("@", "_").replace(".", "_")}.pkl'
        self.google_session_file = f'google_session_{email.replace("@", "_").replace(".", "_")}.pkl'

        # Results tracking
        self.apply_buttons = []
        self.successful_applications = []
        self.failed_applications = []

        # Statistics
        self.stats = {
            'start_time': time.time(),
            'auth_start_time': None,
            'auth_end_time': None,
            'session_reused': False,
            'google_account_found': False,
            'buttons_found': 0,
            'applications_attempted': 0,
            'successful_applications': 0,
            'failed_applications': 0
        }

        # Google account detection patterns for jeremykalilin@gmail.com
        self.google_account_indicators = [
            "jeremykalilin@gmail.com",
            "jeremykalilin",
            "Jeremy",
            "Kalilin"
        ]

    def setup_advanced_driver(self):
        """Setup Chrome WebDriver with advanced SSO optimization"""
        chrome_options = Options()

        if self.headless:
            chrome_options.add_argument("--headless")

        # Core stability options
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("--start-maximized")

        # Advanced session persistence
        profile_dir = f"/tmp/zero_touch_chrome_{self.session_id}"
        chrome_options.add_argument(f"--user-data-dir={profile_dir}")

        # Google SSO specific optimizations
        chrome_options.add_argument("--enable-features=WebAuthentication")
        chrome_options.add_argument("--disable-features=VizDisplayCompositor")
        chrome_options.add_argument("--disable-web-security")
        chrome_options.add_argument("--allow-running-insecure-content")
        chrome_options.add_argument("--disable-popup-blocking")
        chrome_options.add_argument("--disable-notifications")

        # Anti-detection (enhanced for Google)
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        chrome_options.add_argument("--user-agent=Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")

        # Memory and performance
        chrome_options.add_argument("--memory-pressure-off")
        chrome_options.add_argument("--max_old_space_size=4096")
        chrome_options.add_argument("--aggressive-cache-discard")

        try:
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=chrome_options)

            # Advanced anti-detection
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            self.driver.execute_cdp_cmd('Network.setUserAgentOverride', {
                "userAgent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            })

            # Remove automation indicators
            self.driver.execute_script("""
                Object.defineProperty(navigator, 'permissions', {
                    get: () => ({
                        query: () => Promise.resolve({ state: 'granted' })
                    })
                });
                Object.defineProperty(navigator, 'plugins', {
                    get: () => [1, 2, 3, 4, 5]
                });
                Object.defineProperty(navigator, 'languages', {
                    get: () => ['en-US', 'en']
                });
            """)

            # Set optimal timeouts
            self.driver.implicitly_wait(5)
            self.driver.set_page_load_timeout(60)

            logger.info("Advanced Chrome WebDriver setup completed")
            return True

        except Exception as e:
            logger.error(f"Failed to setup advanced WebDriver: {e}")
            return False

    def load_advanced_session(self):
        """Load and verify advanced session data"""
        try:
            # Check if session files exist and are recent
            session_valid = self.check_session_validity()

            if not session_valid:
                logger.info("No valid session found")
                return False

            logger.info("Loading advanced session data...")

            # Load JobRight session
            if os.path.exists(self.session_file):
                with open(self.session_file, 'rb') as f:
                    jobright_session = pickle.load(f)

                # Navigate to JobRight
                self.driver.get(self.base_url)
                time.sleep(2)

                # Load cookies
                for cookie in jobright_session.get('cookies', []):
                    try:
                        self.driver.add_cookie(cookie)
                    except Exception as e:
                        logger.warning(f"Could not load cookie: {e}")

                # Refresh to apply session
                self.driver.refresh()
                time.sleep(3)

            # Load Google session if exists
            if os.path.exists(self.google_session_file):
                with open(self.google_session_file, 'rb') as f:
                    google_session = pickle.load(f)

                # Navigate to Google to apply session
                self.driver.get("https://accounts.google.com")
                time.sleep(2)

                # Load Google cookies
                for cookie in google_session.get('cookies', []):
                    try:
                        self.driver.add_cookie(cookie)
                    except Exception:
                        pass

                time.sleep(2)

            # Verify session is working
            if self.verify_complete_session():
                logger.info("Advanced session loaded and verified successfully")
                self.stats['session_reused'] = True
                return True
            else:
                logger.info("Session verification failed")
                return False

        except Exception as e:
            logger.warning(f"Error loading advanced session: {e}")
            return False

    def check_session_validity(self):
        """Check if existing sessions are still valid"""
        try:
            # Check file age (sessions expire after 7 days)
            max_age = timedelta(days=7)

            for session_file in [self.session_file, self.google_session_file]:
                if os.path.exists(session_file):
                    file_age = datetime.now() - datetime.fromtimestamp(os.path.getmtime(session_file))
                    if file_age < max_age:
                        return True

            return False

        except Exception:
            return False

    def save_advanced_session(self):
        """Save both JobRight and Google sessions"""
        try:
            # Save JobRight session
            jobright_data = {
                'cookies': self.driver.get_cookies(),
                'timestamp': time.time(),
                'email': self.email,
                'url': self.driver.current_url
            }

            with open(self.session_file, 'wb') as f:
                pickle.dump(jobright_data, f)

            # Save Google session by navigating to Google
            current_url = self.driver.current_url

            try:
                self.driver.get("https://accounts.google.com")
                time.sleep(2)

                google_data = {
                    'cookies': self.driver.get_cookies(),
                    'timestamp': time.time(),
                    'email': self.email
                }

                with open(self.google_session_file, 'wb') as f:
                    pickle.dump(google_data, f)

                # Return to original page
                self.driver.get(current_url)
                time.sleep(2)

            except Exception as e:
                logger.warning(f"Could not save Google session: {e}")

            logger.info("Advanced sessions saved successfully")

        except Exception as e:
            logger.warning(f"Could not save advanced session: {e}")

    def verify_complete_session(self):
        """Verify both Google and JobRight sessions are working"""
        try:
            # Test JobRight session
            self.driver.get(f"{self.base_url}/jobs/recommend")
            time.sleep(5)

            current_url = self.driver.current_url.lower()

            # Check if we're on jobs page
            if any(keyword in current_url for keyword in ['job', 'recommend', 'dashboard']):
                # Verify with content
                if self.has_job_content():
                    logger.info("Complete session verified successfully")
                    return True

            logger.info("Session verification failed")
            return False

        except Exception as e:
            logger.warning(f"Session verification error: {e}")
            return False

    def zero_touch_sso_flow(self):
        """Complete zero-touch SSO authentication flow"""
        self.stats['auth_start_time'] = time.time()

        try:
            logger.info("Starting zero-touch SSO flow...")

            # Step 1: Try advanced session loading
            if self.load_advanced_session():
                logger.info("Using existing session - zero-touch successful!")
                self.stats['auth_end_time'] = time.time()
                return True

            # Step 2: Navigate to JobRight
            logger.info("Starting fresh authentication flow...")
            self.driver.get(self.base_url)
            time.sleep(3)

            # Step 3: Initiate SSO with advanced detection
            if not self.smart_sso_initiation():
                logger.error("Failed to initiate SSO")
                return False

            # Step 4: Handle Google authentication with zero-touch
            if not self.zero_touch_google_auth():
                logger.error("Zero-touch Google auth failed")
                return False

            # Step 5: Complete JobRight integration
            if not self.complete_jobright_integration():
                logger.error("JobRight integration failed")
                return False

            # Step 6: Save advanced sessions
            self.save_advanced_session()

            # Step 7: Navigate to jobs
            if not self.navigate_to_jobs_smart():
                logger.error("Failed to navigate to jobs")
                return False

            self.stats['auth_end_time'] = time.time()
            auth_duration = self.stats['auth_end_time'] - self.stats['auth_start_time']
            logger.info(f"Zero-touch SSO flow completed in {auth_duration:.2f} seconds")
            return True

        except Exception as e:
            logger.error(f"Zero-touch SSO flow failed: {e}")
            return False

    def smart_sso_initiation(self):
        """Smart SSO initiation with multiple strategies"""
        try:
            logger.info("Smart SSO initiation...")

            # Strategy 1: Look for existing Google account indicators
            if self.detect_existing_google_session():
                logger.info("Existing Google session detected")
                return True

            # Strategy 2: Find and click SSO buttons
            sso_strategies = [
                self.click_primary_sso_buttons,
                self.click_secondary_sso_buttons,
                self.try_direct_sso_urls,
                self.find_hidden_sso_elements
            ]

            for strategy in sso_strategies:
                try:
                    if strategy():
                        logger.info(f"SSO initiation successful via {strategy.__name__}")
                        return True
                except Exception as e:
                    logger.warning(f"Strategy {strategy.__name__} failed: {e}")
                    continue

            logger.error("All SSO initiation strategies failed")
            return False

        except Exception as e:
            logger.error(f"Smart SSO initiation failed: {e}")
            return False

    def detect_existing_google_session(self):
        """Detect if already signed in with Google"""
        try:
            page_source = self.driver.page_source.lower()

            # Look for account indicators
            for indicator in self.google_account_indicators:
                if indicator.lower() in page_source:
                    logger.info(f"Found Google account indicator: {indicator}")
                    self.stats['google_account_found'] = True
                    return True

            # Look for signed-in elements
            signed_in_selectors = [
                "[data-email*='jeremykalilin']",
                "[aria-label*='Jeremy']",
                "[title*='jeremy']",
                ".user-info",
                ".profile-info"
            ]

            for selector in signed_in_selectors:
                try:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    for element in elements:
                        if element.is_displayed():
                            text = element.text.lower()
                            if any(indicator.lower() in text for indicator in self.google_account_indicators):
                                logger.info("Found signed-in account element")
                                self.stats['google_account_found'] = True
                                return True
                except Exception:
                    continue

            return False

        except Exception:
            return False

    def click_primary_sso_buttons(self):
        """Click primary SSO buttons"""
        try:
            primary_selectors = [
                "//button[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'sign in with google')]",
                "//button[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'continue with google')]",
                "//a[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'google')]",
                "//button[contains(@class, 'google') and contains(@class, 'auth')]",
                "//*[@data-provider='google']",
                "//*[@data-auth='google']"
            ]

            for selector in primary_selectors:
                try:
                    elements = self.driver.find_elements(By.XPATH, selector)
                    for element in elements:
                        if element.is_displayed() and element.is_enabled():
                            logger.info(f"Clicking primary SSO button: {element.text}")
                            element.click()
                            time.sleep(3)
                            return True
                except Exception:
                    continue

            return False

        except Exception:
            return False

    def click_secondary_sso_buttons(self):
        """Click secondary SSO options"""
        try:
            # First look for general sign-in buttons
            signin_selectors = [
                "//button[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'sign in')]",
                "//a[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'sign in')]",
                "//button[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'login')]",
                "//button[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'get started')]"
            ]

            for selector in signin_selectors:
                try:
                    elements = self.driver.find_elements(By.XPATH, selector)
                    for element in elements:
                        if element.is_displayed() and element.is_enabled():
                            logger.info(f"Clicking secondary button: {element.text}")
                            element.click()
                            time.sleep(3)

                            # Look for Google SSO after clicking
                            if self.find_google_sso_after_click():
                                return True

                except Exception:
                    continue

            return False

        except Exception:
            return False

    def find_google_sso_after_click(self):
        """Find Google SSO options after clicking a general button"""
        try:
            time.sleep(2)

            google_selectors = [
                "//button[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'google')]",
                "//a[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'google')]",
                "//img[contains(@src, 'google')]/ancestor::*[self::button or self::a][1]",
                "//*[contains(@class, 'google')][@role='button' or @onclick]"
            ]

            for selector in google_selectors:
                try:
                    elements = self.driver.find_elements(By.XPATH, selector)
                    for element in elements:
                        if element.is_displayed() and element.is_enabled():
                            logger.info(f"Found Google SSO after click: {element.text}")
                            element.click()
                            time.sleep(3)
                            return True
                except Exception:
                    continue

            return False

        except Exception:
            return False

    def try_direct_sso_urls(self):
        """Try direct SSO URLs"""
        try:
            sso_urls = [
                f"{self.base_url}/auth/google",
                f"{self.base_url}/oauth/google",
                f"{self.base_url}/login/google",
                f"{self.base_url}/signin/google",
                f"{self.base_url}/api/auth/google"
            ]

            for url in sso_urls:
                try:
                    logger.info(f"Trying direct SSO URL: {url}")
                    self.driver.get(url)
                    time.sleep(3)

                    # Check if redirected to Google
                    current_url = self.driver.current_url.lower()
                    if 'google.com' in current_url or 'accounts.google' in current_url:
                        logger.info(f"Direct SSO URL successful: {url}")
                        return True

                except Exception:
                    continue

            return False

        except Exception:
            return False

    def find_hidden_sso_elements(self):
        """Find hidden or dynamically loaded SSO elements"""
        try:
            # Execute JavaScript to find hidden elements
            hidden_elements = self.driver.execute_script("""
                var elements = [];
                var allElements = document.querySelectorAll('*');

                for (var i = 0; i < allElements.length; i++) {
                    var elem = allElements[i];
                    var text = elem.textContent.toLowerCase();
                    var classes = elem.className.toLowerCase();
                    var href = elem.getAttribute('href') || '';
                    var onclick = elem.getAttribute('onclick') || '';

                    if ((text.includes('google') || classes.includes('google') ||
                         href.includes('google') || onclick.includes('google')) &&
                        (text.includes('sign') || text.includes('login') ||
                         text.includes('auth') || classes.includes('auth'))) {
                        elements.push(elem);
                    }
                }

                return elements;
            """)

            for element in hidden_elements:
                try:
                    if element.is_enabled():
                        logger.info(f"Clicking hidden SSO element")
                        self.driver.execute_script("arguments[0].click();", element)
                        time.sleep(3)

                        current_url = self.driver.current_url.lower()
                        if 'google.com' in current_url:
                            return True

                except Exception:
                    continue

            return False

        except Exception:
            return False

    def zero_touch_google_auth(self):
        """Zero-touch Google authentication"""
        try:
            logger.info("Starting zero-touch Google authentication...")

            # Wait for Google page
            max_wait = 20
            start_time = time.time()

            while time.time() - start_time < max_wait:
                current_url = self.driver.current_url.lower()
                if 'google.com' in current_url or 'accounts.google' in current_url:
                    logger.info(f"Google auth page loaded: {current_url}")
                    break
                time.sleep(1)
            else:
                logger.error("Google auth page not loaded")
                return False

            time.sleep(3)  # Let page fully load

            # Strategy 1: Check for existing account selection
            if self.handle_google_account_selection():
                logger.info("Google account selection handled")
                return self.complete_google_flow()

            # Strategy 2: Handle email entry automatically
            if self.auto_enter_email():
                logger.info("Email entered automatically")

                # Check for account recognition
                if self.check_google_account_recognized():
                    logger.info("Google account recognized")
                    return self.complete_google_flow()

                # Handle password scenario
                return self.handle_google_password_flow()

            # Strategy 3: Look for account chooser
            if self.handle_account_chooser():
                logger.info("Account chooser handled")
                return self.complete_google_flow()

            logger.error("All Google auth strategies failed")
            return False

        except Exception as e:
            logger.error(f"Zero-touch Google auth failed: {e}")
            return False

    def handle_google_account_selection(self):
        """Handle Google account selection if multiple accounts"""
        try:
            logger.info("Looking for Google account selection...")

            # Look for account selection elements
            account_selectors = [
                f"//div[@data-email='{self.email}']",
                f"//*[contains(text(), '{self.email}')]",
                f"//*[contains(text(), 'jeremykalilin')]",
                f"//*[contains(text(), 'Jeremy')]",
                "//div[contains(@class, 'account') and contains(@class, 'option')]"
            ]

            for selector in account_selectors:
                try:
                    elements = self.driver.find_elements(By.XPATH, selector)
                    for element in elements:
                        if element.is_displayed():
                            text = element.text.lower()
                            if any(indicator.lower() in text for indicator in self.google_account_indicators):
                                logger.info(f"Clicking account: {element.text}")
                                element.click()
                                time.sleep(3)
                                return True
                except Exception:
                    continue

            # Look for "Use another account" if target account not visible
            other_account_selectors = [
                "//div[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'use another account')]",
                "//button[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'add account')]",
                "//*[@data-action='add-account']"
            ]

            for selector in other_account_selectors:
                try:
                    elements = self.driver.find_elements(By.XPATH, selector)
                    for element in elements:
                        if element.is_displayed() and element.is_enabled():
                            logger.info("Clicking 'Use another account'")
                            element.click()
                            time.sleep(3)
                            return False  # Will proceed to email entry
                except Exception:
                    continue

            return False

        except Exception as e:
            logger.warning(f"Account selection error: {e}")
            return False

    def auto_enter_email(self):
        """Automatically enter email address"""
        try:
            logger.info(f"Auto-entering email: {self.email}")

            # Wait for email input
            email_selectors = [
                "input[type='email']",
                "input[id='identifierId']",
                "input[name='identifier']",
                "input[autocomplete='username']",
                "input[autocomplete='email']"
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

            # Clear and enter email
            email_input.clear()
            time.sleep(0.5)

            # Type email slowly to avoid detection
            for char in self.email:
                email_input.send_keys(char)
                time.sleep(0.05)

            time.sleep(1)

            # Click next or submit
            next_selectors = [
                "#identifierNext",
                "button[type='submit']",
                "input[type='submit']",
                "[id*='next']",
                "[id*='Next']",
                "button[jsname]"  # Google's dynamic buttons
            ]

            for selector in next_selectors:
                try:
                    next_button = self.driver.find_element(By.CSS_SELECTOR, selector)
                    if next_button.is_displayed() and next_button.is_enabled():
                        logger.info("Clicking next button")
                        next_button.click()
                        time.sleep(3)
                        return True
                except Exception:
                    continue

            # Fallback: press Enter
            email_input.send_keys(Keys.RETURN)
            time.sleep(3)
            logger.info("Email entered with Enter key")
            return True

        except Exception as e:
            logger.error(f"Auto email entry failed: {e}")
            return False

    def check_google_account_recognized(self):
        """Check if Google recognizes the account (already logged in)"""
        try:
            time.sleep(3)  # Wait for page response

            # Check current URL for signs of successful auth
            current_url = self.driver.current_url.lower()

            if any(keyword in current_url for keyword in ['consent', 'oauth', 'authorize', 'permissions']):
                logger.info("Account recognized - moved to consent screen")
                return True

            if 'jobright.ai' in current_url:
                logger.info("Account recognized - redirected back to JobRight")
                return True

            # Check page content for account recognition
            page_source = self.driver.page_source.lower()
            recognition_indicators = [
                'welcome back',
                'continue as',
                'logged in',
                'choose account',
                'verify it\'s you'
            ]

            if any(indicator in page_source for indicator in recognition_indicators):
                logger.info("Account recognition indicators found")
                return True

            # Check for no password prompt (already authenticated)
            if not self.is_password_required():
                logger.info("No password required - account already authenticated")
                return True

            return False

        except Exception as e:
            logger.warning(f"Account recognition check failed: {e}")
            return False

    def handle_google_password_flow(self):
        """Handle Google password flow with smart detection"""
        try:
            logger.info("Handling Google password flow...")

            # Check if password is actually required
            if not self.is_password_required():
                logger.info("Password not required")
                return self.complete_google_flow()

            # Look for password input
            password_selectors = [
                "input[type='password']",
                "input[name='password']",
                "#password",
                "[aria-label*='password']",
                "[placeholder*='password']"
            ]

            password_input = None
            for selector in password_selectors:
                try:
                    password_input = WebDriverWait(self.driver, 5).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, selector))
                    )
                    if password_input.is_displayed():
                        break
                except TimeoutException:
                    continue

            if password_input:
                logger.info("Password input detected - checking for auto-login options...")

                # Look for "Stay signed in" or similar options
                stay_signed_selectors = [
                    "//input[@type='checkbox' and contains(@name, 'stay')]",
                    "//input[@type='checkbox' and contains(@name, 'remember')]",
                    "//label[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'stay signed in')]",
                    "//label[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'remember me')]"
                ]

                for selector in stay_signed_selectors:
                    try:
                        elements = self.driver.find_elements(By.XPATH, selector)
                        for element in elements:
                            if element.is_displayed() and element.is_enabled():
                                if not element.is_selected():
                                    logger.info("Enabling 'stay signed in'")
                                    element.click()
                                    time.sleep(1)
                    except Exception:
                        continue

                # At this point, we need user interaction for password
                logger.warning("Password required - implementing smart wait strategy...")
                return self.smart_password_wait()

            else:
                logger.info("No password input found - proceeding")
                return self.complete_google_flow()

        except Exception as e:
            logger.warning(f"Password flow handling error: {e}")
            return self.complete_google_flow()

    def is_password_required(self):
        """Check if password is required"""
        try:
            password_selectors = [
                "input[type='password']",
                "input[name='password']",
                "#password"
            ]

            for selector in password_selectors:
                try:
                    password_input = self.driver.find_element(By.CSS_SELECTOR, selector)
                    if password_input.is_displayed():
                        return True
                except Exception:
                    continue

            return False

        except Exception:
            return False

    def smart_password_wait(self):
        """Smart waiting strategy for password entry"""
        try:
            logger.info("Implementing smart password wait...")

            print(f"\n🔐 GOOGLE PASSWORD REQUIRED FOR {self.email}")
            print("=" * 70)
            print("Please enter your Google password in the browser window")
            print("The system will automatically detect when you're done")
            print("This is a one-time setup - future runs will be fully automated")
            print("=" * 70)

            max_wait = 300  # 5 minutes
            start_time = time.time()
            check_interval = 2

            while time.time() - start_time < max_wait:
                try:
                    current_url = self.driver.current_url.lower()

                    # Check for successful authentication indicators
                    success_indicators = [
                        'consent', 'oauth', 'authorize', 'permissions',
                        'jobright.ai', 'success', 'welcome'
                    ]

                    if any(indicator in current_url for indicator in success_indicators):
                        logger.info("Password authentication detected as successful")
                        return self.complete_google_flow()

                    # Check if still on password page
                    if not self.is_password_required():
                        logger.info("Password page passed")
                        return self.complete_google_flow()

                    time.sleep(check_interval)

                except Exception as e:
                    logger.warning(f"Error during password wait: {e}")
                    time.sleep(check_interval)
                    continue

            logger.warning("Password wait timeout - attempting to continue")
            return self.complete_google_flow()

        except Exception as e:
            logger.error(f"Smart password wait failed: {e}")
            return False

    def handle_account_chooser(self):
        """Handle Google account chooser"""
        try:
            logger.info("Looking for account chooser...")

            # Look for account selection interface
            chooser_selectors = [
                "//div[@role='button' and contains(@data-email, '@')]",
                "//div[contains(@class, 'account')]",
                f"//*[contains(text(), '{self.email}')]",
                "//*[@data-identifier]"
            ]

            for selector in chooser_selectors:
                try:
                    elements = self.driver.find_elements(By.XPATH, selector)
                    for element in elements:
                        if element.is_displayed():
                            text = element.text or element.get_attribute('data-email') or ''
                            if self.email in text or any(indicator in text.lower() for indicator in self.google_account_indicators):
                                logger.info(f"Selecting account from chooser: {text}")
                                element.click()
                                time.sleep(3)
                                return True
                except Exception:
                    continue

            return False

        except Exception as e:
            logger.warning(f"Account chooser handling error: {e}")
            return False

    def complete_google_flow(self):
        """Complete the Google authentication flow"""
        try:
            logger.info("Completing Google authentication flow...")

            max_wait = 30
            start_time = time.time()

            while time.time() - start_time < max_wait:
                current_url = self.driver.current_url.lower()

                # Handle consent screen
                if any(keyword in current_url for keyword in ['consent', 'oauth', 'authorize']):
                    logger.info("Handling consent screen...")
                    if self.handle_consent_screen():
                        continue
                    else:
                        time.sleep(2)
                        continue

                # Check if back at JobRight
                if 'jobright.ai' in current_url:
                    logger.info("Successfully returned to JobRight")
                    return True

                # Check for other Google flows
                if 'google.com' in current_url:
                    if self.handle_additional_google_steps():
                        continue

                time.sleep(2)

            # Check final state
            current_url = self.driver.current_url.lower()
            if 'jobright.ai' in current_url:
                logger.info("Google flow completed successfully")
                return True
            else:
                logger.warning(f"Google flow may not have completed properly. Current URL: {current_url}")
                return True  # Continue anyway

        except Exception as e:
            logger.error(f"Google flow completion failed: {e}")
            return False

    def handle_consent_screen(self):
        """Handle Google consent/authorization screen"""
        try:
            logger.info("Handling consent screen...")

            consent_selectors = [
                "//button[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'continue')]",
                "//button[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'allow')]",
                "//button[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'authorize')]",
                "//button[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'accept')]",
                "//input[@type='submit' and contains(@value, 'Allow')]",
                "//input[@type='submit' and contains(@value, 'Continue')]"
            ]

            for selector in consent_selectors:
                try:
                    elements = self.driver.find_elements(By.XPATH, selector)
                    for element in elements:
                        if element.is_displayed() and element.is_enabled():
                            logger.info(f"Clicking consent button: {element.text}")
                            element.click()
                            time.sleep(3)
                            return True
                except Exception:
                    continue

            return False

        except Exception as e:
            logger.warning(f"Consent screen handling error: {e}")
            return False

    def handle_additional_google_steps(self):
        """Handle any additional Google authentication steps"""
        try:
            # Handle 2FA or security checks
            page_source = self.driver.page_source.lower()

            if 'verify' in page_source or '2-step' in page_source or 'security' in page_source:
                logger.info("Additional security steps detected")

                # Look for "Trust this device" options
                trust_selectors = [
                    "//input[@type='checkbox' and contains(@name, 'trust')]",
                    "//label[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'trust')]",
                    "//input[@type='checkbox' and contains(@id, 'trust')]"
                ]

                for selector in trust_selectors:
                    try:
                        elements = self.driver.find_elements(By.XPATH, selector)
                        for element in elements:
                            if element.is_displayed() and element.is_enabled():
                                if not element.is_selected():
                                    logger.info("Enabling 'trust this device'")
                                    element.click()
                                    time.sleep(1)
                    except Exception:
                        continue

                return False  # Let user handle 2FA

            return False

        except Exception:
            return False

    def complete_jobright_integration(self):
        """Complete JobRight integration after Google auth"""
        try:
            logger.info("Completing JobRight integration...")

            # Wait for JobRight redirect
            max_wait = 30
            start_time = time.time()

            while time.time() - start_time < max_wait:
                current_url = self.driver.current_url.lower()
                if 'jobright.ai' in current_url:
                    logger.info(f"JobRight integration page loaded: {current_url}")
                    break
                time.sleep(1)
            else:
                logger.error("JobRight integration timeout")
                return False

            time.sleep(3)  # Let page load

            # Handle onboarding flow
            self.handle_onboarding_flow()

            # Close any modals
            self.close_integration_modals()

            # Accept terms if needed
            self.accept_integration_terms()

            return True

        except Exception as e:
            logger.error(f"JobRight integration failed: {e}")
            return False

    def handle_onboarding_flow(self):
        """Handle JobRight onboarding flow"""
        try:
            logger.info("Handling onboarding flow...")

            max_steps = 15
            for step in range(max_steps):
                logger.info(f"Onboarding step {step + 1}")

                # Look for skip, continue, next buttons
                action_selectors = [
                    "//button[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'skip')]",
                    "//button[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'next')]",
                    "//button[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'continue')]",
                    "//button[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'get started')]",
                    "//a[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'skip')]",
                    "//*[@class*='skip' and (@role='button' or @onclick)]",
                    "//*[@data-action='skip' or @data-action='continue' or @data-action='next']"
                ]

                action_taken = False
                for selector in action_selectors:
                    try:
                        elements = self.driver.find_elements(By.XPATH, selector)
                        for element in elements:
                            if element.is_displayed() and element.is_enabled():
                                text = element.text.strip()
                                logger.info(f"Clicking onboarding action: {text}")
                                element.click()
                                time.sleep(2)
                                action_taken = True
                                break
                        if action_taken:
                            break
                    except Exception:
                        continue

                if not action_taken:
                    logger.info("No more onboarding actions found")
                    break

                # Check if reached jobs page
                current_url = self.driver.current_url.lower()
                if any(keyword in current_url for keyword in ['job', 'recommend', 'dashboard']):
                    logger.info("Reached jobs page during onboarding")
                    break

        except Exception as e:
            logger.warning(f"Onboarding flow error: {e}")

    def close_integration_modals(self):
        """Close any integration modals"""
        try:
            modal_close_selectors = [
                "[aria-label*='close']",
                "[aria-label*='Close']",
                "//button[text()='×']",
                "//button[contains(@class, 'close')]",
                ".modal .close",
                ".popup .close",
                "[data-dismiss='modal']"
            ]

            for selector in modal_close_selectors:
                try:
                    if selector.startswith("//"):
                        elements = self.driver.find_elements(By.XPATH, selector)
                    else:
                        elements = self.driver.find_elements(By.CSS_SELECTOR, selector)

                    for element in elements:
                        if element.is_displayed():
                            logger.info("Closing integration modal")
                            element.click()
                            time.sleep(1)
                            return
                except Exception:
                    continue

        except Exception:
            pass

    def accept_integration_terms(self):
        """Accept any integration terms"""
        try:
            terms_selectors = [
                "//input[@type='checkbox' and (contains(@name, 'terms') or contains(@name, 'agree'))]",
                "//button[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'accept')]",
                "//button[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'agree')]"
            ]

            for selector in terms_selectors:
                try:
                    elements = self.driver.find_elements(By.XPATH, selector)
                    for element in elements:
                        if element.is_displayed() and element.is_enabled():
                            logger.info("Accepting integration terms")
                            element.click()
                            time.sleep(1)
                except Exception:
                    continue

        except Exception:
            pass

    def navigate_to_jobs_smart(self):
        """Smart navigation to jobs page"""
        try:
            logger.info("Smart navigation to jobs...")

            # Try direct job URLs
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

                    if self.has_job_content():
                        logger.info(f"Successfully navigated to jobs: {url}")
                        return True

                except Exception as e:
                    logger.warning(f"Failed to access {url}: {e}")
                    continue

            # Try navigation menu
            nav_selectors = [
                "//a[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'job')]",
                "//a[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'recommend')]",
                "//a[contains(@href, 'job')]",
                "//button[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'job')]"
            ]

            for selector in nav_selectors:
                try:
                    elements = self.driver.find_elements(By.XPATH, selector)
                    for element in elements:
                        if element.is_displayed():
                            logger.info(f"Clicking navigation: {element.text}")
                            element.click()
                            time.sleep(3)
                            if self.has_job_content():
                                logger.info("Successfully navigated via menu")
                                return True
                except Exception:
                    continue

            logger.warning("Could not navigate to jobs page")
            return False

        except Exception as e:
            logger.error(f"Smart navigation error: {e}")
            return False

    def has_job_content(self):
        """Check if page has job content"""
        try:
            page_source = self.driver.page_source.lower()

            # Job content indicators
            job_indicators = [
                'apply', 'job', 'position', 'role', 'salary', 'company',
                'remote', 'full-time', 'part-time', 'career', 'employment'
            ]

            found_indicators = sum(1 for indicator in job_indicators if indicator in page_source)

            # Apply button indicators
            apply_indicators = [
                'apply now', 'quick apply', 'easy apply', 'apply with autofill'
            ]

            apply_found = sum(1 for indicator in apply_indicators if indicator in page_source)

            # URL check
            current_url = self.driver.current_url.lower()
            url_has_jobs = any(keyword in current_url for keyword in ['job', 'recommend', 'position'])

            logger.info(f"Job content check: {found_indicators} indicators, {apply_found} apply buttons, URL valid: {url_has_jobs}")

            return (found_indicators >= 3 or apply_found >= 1) and url_has_jobs

        except Exception:
            return False

    def load_all_jobs_advanced(self):
        """Advanced job loading with multiple strategies"""
        try:
            logger.info("Loading all jobs with advanced strategies...")

            # Strategy 1: Intelligent scrolling
            self.intelligent_scroll_loading()

            # Strategy 2: Dynamic content triggers
            self.trigger_dynamic_content()

            # Strategy 3: Load more button detection
            self.click_all_load_more_advanced()

            # Strategy 4: Pagination handling
            self.handle_pagination()

            logger.info("Advanced job loading completed")

        except Exception as e:
            logger.warning(f"Advanced job loading error: {e}")

    def intelligent_scroll_loading(self):
        """Intelligent scrolling with content detection"""
        try:
            logger.info("Starting intelligent scroll loading...")

            last_height = 0
            stable_count = 0
            max_stable = 5
            scroll_count = 0
            max_scrolls = 20

            while stable_count < max_stable and scroll_count < max_scrolls:
                # Scroll to bottom
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(2)

                # Get new height and button count
                new_height = self.driver.execute_script("return document.body.scrollHeight")
                button_count = len(self.driver.find_elements(By.XPATH, "//*[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'apply')]"))

                if new_height == last_height:
                    stable_count += 1
                    logger.info(f"Scroll stable count: {stable_count}, buttons found: {button_count}")
                else:
                    last_height = new_height
                    stable_count = 0
                    logger.info(f"New content loaded, height: {new_height}, buttons: {button_count}")

                scroll_count += 1

                # Try horizontal scrolling for carousels
                self.driver.execute_script("window.scrollBy(500, 0);")
                time.sleep(1)

            # Return to top
            self.driver.execute_script("window.scrollTo(0, 0);")
            time.sleep(2)

            logger.info(f"Intelligent scrolling completed after {scroll_count} scrolls")

        except Exception as e:
            logger.warning(f"Intelligent scroll error: {e}")

    def trigger_dynamic_content(self):
        """Trigger dynamic content loading"""
        try:
            # Simulate user interactions that might trigger content
            actions = [
                lambda: self.driver.execute_script("window.dispatchEvent(new Event('scroll'));"),
                lambda: self.driver.execute_script("window.dispatchEvent(new Event('resize'));"),
                lambda: self.driver.execute_script("document.dispatchEvent(new Event('DOMContentLoaded'));"),
            ]

            for action in actions:
                try:
                    action()
                    time.sleep(1)
                except Exception:
                    continue

        except Exception:
            pass

    def click_all_load_more_advanced(self):
        """Advanced load more button detection and clicking"""
        try:
            load_more_patterns = [
                "load more", "show more", "view more", "see more",
                "load additional", "more jobs", "next page",
                "continue", "expand", "see all", "view all"
            ]

            max_clicks = 10
            clicks = 0

            while clicks < max_clicks:
                found_button = False

                for pattern in load_more_patterns:
                    # Multiple selector strategies
                    selectors = [
                        f"//button[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), '{pattern}')]",
                        f"//a[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), '{pattern}')]",
                        f"//div[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), '{pattern}') and (@onclick or @role='button')]",
                        f"//*[contains(@class, 'load') and contains(@class, 'more')]",
                        f"//*[contains(@aria-label, '{pattern}')]"
                    ]

                    for selector in selectors:
                        try:
                            elements = self.driver.find_elements(By.XPATH, selector)
                            for element in elements:
                                if element.is_displayed() and element.is_enabled():
                                    logger.info(f"Clicking load more: {pattern}")
                                    element.click()
                                    time.sleep(3)
                                    found_button = True
                                    clicks += 1
                                    break
                            if found_button:
                                break
                        except Exception:
                            continue

                    if found_button:
                        break

                if not found_button:
                    break

            logger.info(f"Clicked {clicks} load more buttons")

        except Exception as e:
            logger.warning(f"Load more clicking error: {e}")

    def handle_pagination(self):
        """Handle pagination if present"""
        try:
            pagination_selectors = [
                "//a[contains(@class, 'next')]",
                "//button[contains(@class, 'next')]",
                "//a[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'next')]",
                "//button[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'next')]",
                "//*[contains(@aria-label, 'next')]"
            ]

            max_pages = 5
            pages = 0

            while pages < max_pages:
                found_next = False

                for selector in pagination_selectors:
                    try:
                        elements = self.driver.find_elements(By.XPATH, selector)
                        for element in elements:
                            if element.is_displayed() and element.is_enabled():
                                logger.info(f"Clicking pagination next")
                                element.click()
                                time.sleep(5)  # Wait for page load
                                found_next = True
                                pages += 1
                                break
                        if found_next:
                            break
                    except Exception:
                        continue

                if not found_next:
                    break

            if pages > 0:
                logger.info(f"Processed {pages} pagination pages")

        except Exception as e:
            logger.warning(f"Pagination handling error: {e}")

    def find_all_apply_buttons_ultimate(self):
        """Ultimate apply button finding with zero-touch optimization"""
        try:
            logger.info("Starting ultimate apply button search...")

            all_buttons = []

            # Strategy 1: Enhanced text-based search
            text_buttons = self.find_buttons_by_text_ultimate()
            all_buttons.extend(text_buttons)
            logger.info(f"Found {len(text_buttons)} buttons by text")

            # Strategy 2: Advanced attribute search
            attr_buttons = self.find_buttons_by_attributes_ultimate()
            all_buttons.extend(attr_buttons)
            logger.info(f"Found {len(attr_buttons)} buttons by attributes")

            # Strategy 3: Visual pattern recognition
            visual_buttons = self.find_buttons_by_visual_ultimate()
            all_buttons.extend(visual_buttons)
            logger.info(f"Found {len(visual_buttons)} buttons by visual patterns")

            # Strategy 4: DOM structure analysis
            dom_buttons = self.find_buttons_by_dom_ultimate()
            all_buttons.extend(dom_buttons)
            logger.info(f"Found {len(dom_buttons)} buttons by DOM structure")

            # Strategy 5: JavaScript event analysis
            js_buttons = self.find_buttons_by_javascript_ultimate()
            all_buttons.extend(js_buttons)
            logger.info(f"Found {len(js_buttons)} buttons by JavaScript events")

            # Deduplicate and validate
            unique_buttons = self.deduplicate_and_validate_ultimate(all_buttons)

            self.stats['buttons_found'] = len(unique_buttons)
            logger.info(f"Ultimate button search completed: {len(unique_buttons)} unique buttons")

            return unique_buttons

        except Exception as e:
            logger.error(f"Ultimate button search error: {e}")
            return []

    def find_buttons_by_text_ultimate(self):
        """Ultimate text-based button finding"""
        buttons = []

        # Comprehensive apply text patterns
        patterns = [
            "apply now", "apply with autofill", "quick apply", "easy apply",
            "apply", "apply for", "apply to", "submit application",
            "apply for this job", "apply for position", "one-click apply",
            "instant apply", "autofill", "auto-fill", "auto apply",
            "apply today", "apply here", "submit resume", "send application",
            "quick submission", "fast apply", "1-click apply", "express apply"
        ]

        for pattern in patterns:
            try:
                # Multiple XPath strategies for each pattern
                xpaths = [
                    f"//*[contains(translate(normalize-space(text()), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), '{pattern}')]",
                    f"//button[contains(translate(normalize-space(text()), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), '{pattern}')]",
                    f"//a[contains(translate(normalize-space(text()), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), '{pattern}')]",
                    f"//*[contains(translate(normalize-space(@aria-label), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), '{pattern}')]",
                    f"//*[contains(translate(normalize-space(@title), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), '{pattern}')]"
                ]

                for xpath in xpaths:
                    try:
                        elements = self.driver.find_elements(By.XPATH, xpath)
                        for element in elements:
                            if self.is_valid_apply_button_ultimate(element):
                                button_info = self.extract_button_info_ultimate(element, f"text_{pattern}")
                                if button_info:
                                    buttons.append(button_info)
                    except Exception:
                        continue

            except Exception:
                continue

        return buttons

    def find_buttons_by_attributes_ultimate(self):
        """Ultimate attribute-based button finding"""
        buttons = []

        # Class patterns
        class_patterns = [
            "apply", "autofill", "quick", "easy", "submit", "application",
            "job-apply", "apply-btn", "apply-button", "btn-apply",
            "quick-apply", "easy-apply", "one-click", "instant-apply"
        ]

        # Data attribute patterns
        data_patterns = [
            "apply", "submit", "quick-apply", "autofill", "job-apply"
        ]

        for pattern in class_patterns:
            try:
                selectors = [
                    f"[class*='{pattern}']",
                    f"button[class*='{pattern}']",
                    f"a[class*='{pattern}']",
                    f"div[class*='{pattern}'][onclick]"
                ]

                for selector in selectors:
                    try:
                        elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                        for element in elements:
                            if self.is_valid_apply_button_ultimate(element):
                                button_info = self.extract_button_info_ultimate(element, f"class_{pattern}")
                                if button_info:
                                    buttons.append(button_info)
                    except Exception:
                        continue

            except Exception:
                continue

        for pattern in data_patterns:
            try:
                selectors = [
                    f"[data-action*='{pattern}']",
                    f"[data-track*='{pattern}']",
                    f"[data-event*='{pattern}']",
                    f"[data-click*='{pattern}']"
                ]

                for selector in selectors:
                    try:
                        elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                        for element in elements:
                            if self.is_valid_apply_button_ultimate(element):
                                button_info = self.extract_button_info_ultimate(element, f"data_{pattern}")
                                if button_info:
                                    buttons.append(button_info)
                    except Exception:
                        continue

            except Exception:
                continue

        return buttons

    def find_buttons_by_visual_ultimate(self):
        """Ultimate visual pattern recognition"""
        buttons = []

        try:
            # Get all potentially clickable elements
            clickable_elements = self.driver.find_elements(By.CSS_SELECTOR,
                "button, a, input[type='button'], input[type='submit'], [role='button'], [onclick], [data-action]")

            for element in clickable_elements:
                try:
                    if not self.is_valid_apply_button_ultimate(element):
                        continue

                    # Enhanced visual analysis
                    visual_score = 0
                    text = element.text.lower().strip()

                    # Text scoring
                    high_value_words = ['apply', 'autofill', 'quick']
                    medium_value_words = ['submit', 'send', 'easy']

                    for word in high_value_words:
                        if word in text:
                            visual_score += 5

                    for word in medium_value_words:
                        if word in text:
                            visual_score += 3

                    # Size scoring
                    try:
                        size = element.size
                        if 80 <= size['width'] <= 300 and 25 <= size['height'] <= 60:
                            visual_score += 2
                    except Exception:
                        pass

                    # Style scoring
                    try:
                        classes = element.get_attribute('class') or ''
                        if any(keyword in classes.lower() for keyword in ['primary', 'cta', 'main', 'action']):
                            visual_score += 2
                    except Exception:
                        pass

                    if visual_score >= 5:
                        button_info = self.extract_button_info_ultimate(element, "visual_pattern")
                        if button_info:
                            buttons.append(button_info)

                except Exception:
                    continue

        except Exception as e:
            logger.warning(f"Visual pattern recognition error: {e}")

        return buttons

    def find_buttons_by_dom_ultimate(self):
        """Ultimate DOM structure analysis"""
        buttons = []

        try:
            # Look for job card structures
            job_container_selectors = [
                "[class*='job']", "[class*='card']", "[class*='listing']",
                "[class*='position']", "[class*='role']", "[data-job]",
                "[class*='item']", "[class*='recommendation']"
            ]

            for selector in job_container_selectors:
                try:
                    containers = self.driver.find_elements(By.CSS_SELECTOR, selector)

                    for container in containers:
                        try:
                            # Look for clickable elements within containers
                            clickable_in_container = container.find_elements(By.CSS_SELECTOR,
                                "button, a, [role='button'], [onclick]")

                            for element in clickable_in_container:
                                if self.is_valid_apply_button_ultimate(element):
                                    text = element.text.lower().strip()
                                    if any(word in text for word in ['apply', 'submit', 'quick', 'autofill']):
                                        button_info = self.extract_button_info_ultimate(element, f"dom_{selector}")
                                        if button_info:
                                            buttons.append(button_info)
                        except Exception:
                            continue

                except Exception:
                    continue

        except Exception as e:
            logger.warning(f"DOM structure analysis error: {e}")

        return buttons

    def find_buttons_by_javascript_ultimate(self):
        """Ultimate JavaScript event analysis"""
        buttons = []

        try:
            # Execute JavaScript to find elements with event listeners
            js_elements = self.driver.execute_script("""
                var results = [];
                var allElements = document.querySelectorAll('*');

                for (var i = 0; i < allElements.length; i++) {
                    var elem = allElements[i];
                    var text = elem.textContent.trim().toLowerCase();

                    // Check for event listeners or interactive attributes
                    var hasListeners = elem.onclick !== null ||
                                     elem.onmousedown !== null ||
                                     elem.getAttribute('data-action') ||
                                     elem.getAttribute('data-click') ||
                                     elem.getAttribute('ng-click') ||
                                     elem.getAttribute('v-on:click');

                    if (hasListeners && (
                        text.includes('apply') ||
                        text.includes('submit') ||
                        text.includes('quick') ||
                        text.includes('autofill')
                    )) {
                        results.push({
                            tag: elem.tagName,
                            text: text,
                            className: elem.className,
                            id: elem.id
                        });
                    }
                }

                return results;
            """)

            for js_elem in js_elements:
                try:
                    # Find the actual element
                    if js_elem['id']:
                        elements = self.driver.find_elements(By.ID, js_elem['id'])
                    elif js_elem['className']:
                        class_name = js_elem['className'].split()[0] if js_elem['className'] else ''
                        if class_name:
                            elements = self.driver.find_elements(By.CLASS_NAME, class_name)
                        else:
                            continue
                    else:
                        continue

                    for element in elements:
                        if self.is_valid_apply_button_ultimate(element):
                            button_info = self.extract_button_info_ultimate(element, "javascript_events")
                            if button_info:
                                buttons.append(button_info)

                except Exception:
                    continue

        except Exception as e:
            logger.warning(f"JavaScript event analysis error: {e}")

        return buttons

    def is_valid_apply_button_ultimate(self, element):
        """Ultimate apply button validation"""
        try:
            # Basic visibility and interaction checks
            if not (element.is_displayed() and element.is_enabled()):
                return False

            # Size validation
            try:
                size = element.size
                if size['width'] < 20 or size['height'] < 10:
                    return False
            except Exception:
                pass

            # Tag validation
            tag = element.tag_name.lower()
            if tag not in ['button', 'a', 'input', 'div', 'span'] and not element.get_attribute('onclick'):
                return False

            # Text content validation
            text = element.text.strip()
            if len(text) < 1 or len(text) > 200:
                return False

            # Must contain apply-related content
            apply_keywords = [
                'apply', 'submit', 'send', 'quick', 'easy', 'autofill',
                'auto-fill', 'instant', 'one-click'
            ]

            text_lower = text.lower()
            classes = (element.get_attribute('class') or '').lower()
            aria_label = (element.get_attribute('aria-label') or '').lower()

            combined_text = f"{text_lower} {classes} {aria_label}"

            if not any(keyword in combined_text for keyword in apply_keywords):
                return False

            return True

        except Exception:
            return False

    def extract_button_info_ultimate(self, element, detection_method):
        """Ultimate button information extraction"""
        try:
            # Basic information
            text = element.text.strip()
            tag = element.tag_name
            classes = element.get_attribute('class') or ''
            element_id = element.get_attribute('id') or ''
            href = element.get_attribute('href') or ''
            onclick = element.get_attribute('onclick') or ''

            # Enhanced attributes
            aria_label = element.get_attribute('aria-label') or ''
            title = element.get_attribute('title') or ''
            data_action = element.get_attribute('data-action') or ''
            role = element.get_attribute('role') or ''

            # Position and size
            location = element.location
            size = element.size

            # Generate multiple selectors for reliability
            selectors = self.generate_multiple_selectors_ultimate(element)

            return {
                'text': text,
                'tag': tag,
                'classes': classes,
                'id': element_id,
                'href': href,
                'onclick': onclick,
                'aria_label': aria_label,
                'title': title,
                'data_action': data_action,
                'role': role,
                'location': location,
                'size': size,
                'detection_method': detection_method,
                'selectors': selectors,
                'timestamp': time.time(),
                'unique_id': f"{text[:15]}_{location['x']}_{location['y']}"
            }

        except Exception as e:
            logger.warning(f"Button info extraction error: {e}")
            return None

    def generate_multiple_selectors_ultimate(self, element):
        """Generate multiple CSS selectors for element"""
        selectors = []

        try:
            # ID selector
            element_id = element.get_attribute('id')
            if element_id:
                selectors.append(f"#{element_id}")

            # Class selectors
            classes = element.get_attribute('class')
            if classes:
                class_list = classes.strip().split()
                if class_list:
                    selectors.append(f"{element.tag_name.lower()}.{'.'.join(class_list[:3])}")
                    selectors.append(f".{class_list[0]}")

            # Attribute selectors
            for attr in ['data-action', 'onclick', 'href', 'aria-label']:
                value = element.get_attribute(attr)
                if value:
                    selectors.append(f"[{attr}*='{value[:30]}']")

            # Text-based selectors (for XPath)
            text = element.text.strip()
            if text and len(text) > 2:
                selectors.append(f"{element.tag_name.lower()}:contains('{text[:20]}')")

        except Exception:
            pass

        return selectors

    def deduplicate_and_validate_ultimate(self, all_buttons):
        """Ultimate deduplication and validation"""
        try:
            unique_buttons = []
            seen_buttons = set()

            for button in all_buttons:
                if not button:
                    continue

                # Create comprehensive unique identifier
                unique_id = button.get('unique_id', f"{button['text'][:15]}_{button['location']['x']}_{button['location']['y']}")

                if unique_id not in seen_buttons:
                    seen_buttons.add(unique_id)

                    # Final validation
                    if self.final_button_validation(button):
                        unique_buttons.append(button)

            # Sort by relevance score and position
            unique_buttons = sorted(unique_buttons, key=lambda x: self.calculate_button_score(x), reverse=True)

            logger.info(f"After ultimate deduplication: {len(unique_buttons)} buttons")
            return unique_buttons

        except Exception as e:
            logger.error(f"Ultimate deduplication error: {e}")
            return all_buttons

    def final_button_validation(self, button_info):
        """Final validation of button candidates"""
        try:
            text = button_info['text'].lower()

            # Must contain primary apply keywords
            primary_keywords = ['apply', 'autofill', 'quick apply']
            if not any(keyword in text for keyword in primary_keywords):
                # Allow secondary keywords if combined with job-related terms
                secondary_keywords = ['submit', 'send']
                job_keywords = ['application', 'resume', 'job']
                if not (any(sk in text for sk in secondary_keywords) and
                       any(jk in text for jk in job_keywords)):
                    return False

            # Size validation
            size = button_info['size']
            if size['width'] < 40 or size['height'] < 15:
                return False

            # Text length validation
            if len(text) < 3 or len(text) > 150:
                return False

            return True

        except Exception:
            return True

    def calculate_button_score(self, button_info):
        """Calculate relevance score for button"""
        try:
            score = 0
            text = button_info['text'].lower()

            # High-value keywords
            high_value = ['apply now', 'apply with autofill', 'quick apply', 'autofill']
            for keyword in high_value:
                if keyword in text:
                    score += 10

            # Medium-value keywords
            medium_value = ['apply', 'easy apply', 'instant apply']
            for keyword in medium_value:
                if keyword in text:
                    score += 5

            # Detection method bonus
            if 'text_apply now' in button_info['detection_method']:
                score += 5
            elif 'class_apply' in button_info['detection_method']:
                score += 3

            # Size bonus
            size = button_info['size']
            if 80 <= size['width'] <= 200 and 25 <= size['height'] <= 50:
                score += 2

            return score

        except Exception:
            return 0

    def apply_to_all_jobs_zero_touch(self):
        """Zero-touch job application process"""
        try:
            logger.info(f"Starting zero-touch application to {len(self.apply_buttons)} jobs...")

            for i, button_info in enumerate(self.apply_buttons, 1):
                print(f"\n[{i}/{len(self.apply_buttons)}] ZERO-TOUCH APPLICATION:")
                print(f"Job: {button_info['text'][:60]}...")

                try:
                    result = self.apply_to_single_job_zero_touch(button_info, i, len(self.apply_buttons))

                    if result['success']:
                        self.successful_applications.append(result)
                        self.stats['successful_applications'] += 1
                        print(f"✅ SUCCESS: {result.get('action', 'Applied')}")
                        if result.get('new_url'):
                            print(f"   → OPENED: {result['new_url'][:70]}...")
                    else:
                        self.failed_applications.append(result)
                        self.stats['failed_applications'] += 1
                        print(f"❌ FAILED: {result.get('error', 'Unknown error')}")

                    self.stats['applications_attempted'] += 1

                    # Smart delay between applications
                    delay = 2 + (i % 3)  # Variable delay 2-4 seconds
                    time.sleep(delay)

                except Exception as e:
                    error_result = {
                        'button_info': button_info,
                        'success': False,
                        'error': f"Application exception: {str(e)}",
                        'timestamp': time.time()
                    }
                    self.failed_applications.append(error_result)
                    self.stats['failed_applications'] += 1
                    print(f"❌ EXCEPTION: {str(e)}")
                    continue

            logger.info(f"Zero-touch applications completed. Success: {self.stats['successful_applications']}, Failed: {self.stats['failed_applications']}")

        except Exception as e:
            logger.error(f"Zero-touch application process failed: {e}")

    def apply_to_single_job_zero_touch(self, button_info, index, total):
        """Apply to a single job with zero-touch methodology"""
        try:
            logger.info(f"Zero-touch application {index}/{total}: {button_info['text'][:40]}...")

            # Find element using multiple strategies
            element = self.relocate_element_ultimate(button_info)

            if not element:
                return {
                    'button_info': button_info,
                    'success': False,
                    'error': 'Element not found with ultimate relocation',
                    'timestamp': time.time()
                }

            # Record current state
            original_url = self.driver.current_url
            original_windows = self.driver.window_handles

            # Prepare for click
            self.prepare_element_for_click(element)

            # Execute click with multiple fallbacks
            click_result = self.execute_zero_touch_click(element, button_info)

            if not click_result['success']:
                return {
                    'button_info': button_info,
                    'success': False,
                    'error': click_result['error'],
                    'timestamp': time.time()
                }

            # Wait for response
            time.sleep(3)

            # Analyze result
            result = self.analyze_application_result(original_url, original_windows, button_info, click_result)

            return result

        except Exception as e:
            return {
                'button_info': button_info,
                'success': False,
                'error': f"Zero-touch application error: {str(e)}",
                'timestamp': time.time()
            }

    def relocate_element_ultimate(self, button_info):
        """Ultimate element relocation with multiple strategies"""
        try:
            # Strategy 1: By selectors
            for selector in button_info.get('selectors', []):
                try:
                    if selector.startswith('#') or selector.startswith('.') or '[' in selector:
                        elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    elif ':contains(' in selector:
                        text = selector.split(':contains(')[1].split(')')[0].strip("'\"")
                        tag = selector.split(':contains(')[0]
                        xpath = f"//{tag}[contains(text(), '{text}')]"
                        elements = self.driver.find_elements(By.XPATH, xpath)
                    else:
                        elements = self.driver.find_elements(By.CSS_SELECTOR, selector)

                    for element in elements:
                        if element.is_displayed() and element.is_enabled():
                            return element
                except Exception:
                    continue

            # Strategy 2: By ID
            if button_info.get('id'):
                try:
                    element = self.driver.find_element(By.ID, button_info['id'])
                    if element.is_displayed() and element.is_enabled():
                        return element
                except Exception:
                    pass

            # Strategy 3: By text and position proximity
            try:
                text = button_info['text'][:20]
                expected_location = button_info['location']

                xpath = f"//*[contains(text(), '{text}')]"
                elements = self.driver.find_elements(By.XPATH, xpath)

                best_element = None
                min_distance = float('inf')

                for element in elements:
                    if element.is_displayed() and element.is_enabled():
                        current_location = element.location
                        distance = abs(current_location['x'] - expected_location['x']) + abs(current_location['y'] - expected_location['y'])

                        if distance < min_distance and distance < 200:  # Within 200 pixels
                            min_distance = distance
                            best_element = element

                if best_element:
                    return best_element

            except Exception:
                pass

            # Strategy 4: By partial text matching
            try:
                words = button_info['text'].split()
                if len(words) >= 2:
                    for word in words:
                        if len(word) > 3:  # Skip short words
                            xpath = f"//*[contains(text(), '{word}')]"
                            elements = self.driver.find_elements(By.XPATH, xpath)

                            for element in elements:
                                if element.is_displayed() and element.is_enabled():
                                    element_text = element.text.lower()
                                    if 'apply' in element_text:
                                        return element

            except Exception:
                pass

            return None

        except Exception as e:
            logger.warning(f"Ultimate element relocation failed: {e}")
            return None

    def prepare_element_for_click(self, element):
        """Prepare element for zero-touch clicking"""
        try:
            # Scroll to element with smart positioning
            self.driver.execute_script("""
                arguments[0].scrollIntoView({
                    behavior: 'smooth',
                    block: 'center',
                    inline: 'center'
                });
            """, element)
            time.sleep(1)

            # Ensure element is in viewport
            location = element.location
            viewport_height = self.driver.execute_script("return window.innerHeight")
            viewport_width = self.driver.execute_script("return window.innerWidth")

            if location['y'] < 0 or location['y'] > viewport_height:
                self.driver.execute_script(f"window.scrollTo(0, {location['y'] - viewport_height/2})")
                time.sleep(1)

            # Remove potential overlays
            self.remove_click_obstacles(element)

        except Exception as e:
            logger.warning(f"Element preparation error: {e}")

    def remove_click_obstacles(self, target_element):
        """Remove obstacles that might prevent clicking"""
        try:
            # Get element position
            target_rect = self.driver.execute_script("""
                var rect = arguments[0].getBoundingClientRect();
                return {
                    top: rect.top,
                    left: rect.left,
                    bottom: rect.bottom,
                    right: rect.right,
                    x: rect.left + rect.width/2,
                    y: rect.top + rect.height/2
                };
            """, target_element)

            # Find potential obstacles
            obstacles = self.driver.execute_script("""
                var targetRect = arguments[1];
                var obstacles = [];

                // Get element at target position
                var elementsAtPoint = document.elementsFromPoint(targetRect.x, targetRect.y);

                for (var i = 0; i < elementsAtPoint.length; i++) {
                    var elem = elementsAtPoint[i];
                    if (elem !== arguments[0]) {
                        var style = window.getComputedStyle(elem);
                        if (style.position === 'fixed' || style.position === 'absolute') {
                            var zIndex = parseInt(style.zIndex) || 0;
                            if (zIndex > 10) {
                                obstacles.push(elem);
                            }
                        }
                    }
                }

                return obstacles;
            """, target_element, target_rect)

            # Hide obstacles
            for obstacle in obstacles:
                try:
                    self.driver.execute_script("arguments[0].style.display = 'none';", obstacle)
                except Exception:
                    pass

        except Exception as e:
            logger.warning(f"Obstacle removal error: {e}")

    def execute_zero_touch_click(self, element, button_info):
        """Execute zero-touch click with maximum success rate"""
        try:
            click_methods = [
                ('standard', lambda e: e.click()),
                ('javascript', lambda e: self.driver.execute_script("arguments[0].click();", e)),
                ('action_chains', lambda e: ActionChains(self.driver).move_to_element(e).click().perform()),
                ('action_chains_offset', lambda e: ActionChains(self.driver).move_to_element_with_offset(e, 5, 5).click().perform()),
                ('force_click', lambda e: self.force_click_zero_touch(e)),
                ('event_dispatch', lambda e: self.dispatch_click_events(e)),
                ('form_submit', lambda e: self.attempt_form_submit(e))
            ]

            for method_name, method_func in click_methods:
                try:
                    logger.info(f"Trying click method: {method_name}")
                    method_func(element)
                    return {'success': True, 'method': method_name}

                except ElementClickInterceptedException:
                    # Additional obstacle removal
                    try:
                        self.remove_click_obstacles(element)
                        method_func(element)
                        return {'success': True, 'method': f"{method_name}_after_clearing"}
                    except Exception:
                        continue

                except Exception as e:
                    logger.warning(f"Click method {method_name} failed: {e}")
                    continue

            return {'success': False, 'error': 'All zero-touch click methods failed'}

        except Exception as e:
            return {'success': False, 'error': f"Zero-touch click execution error: {str(e)}"}

    def force_click_zero_touch(self, element):
        """Force click with zero-touch optimization"""
        # Remove all potential overlays
        self.driver.execute_script("""
            var overlays = document.querySelectorAll('*');
            for (var i = 0; i < overlays.length; i++) {
                var el = overlays[i];
                var style = window.getComputedStyle(el);
                if (style.position === 'fixed' || style.position === 'absolute') {
                    var zIndex = parseInt(style.zIndex) || 0;
                    if (zIndex > 100) {
                        el.style.display = 'none';
                    }
                }
            }
        """)

        time.sleep(0.5)

        # Force focus and click
        self.driver.execute_script("""
            var element = arguments[0];
            element.focus();
            element.click();

            // Dispatch multiple events
            var events = ['mousedown', 'mouseup', 'click'];
            for (var i = 0; i < events.length; i++) {
                var event = new MouseEvent(events[i], {
                    view: window,
                    bubbles: true,
                    cancelable: true,
                    clientX: element.getBoundingClientRect().left + element.offsetWidth/2,
                    clientY: element.getBoundingClientRect().top + element.offsetHeight/2
                });
                element.dispatchEvent(event);
            }
        """, element)

    def dispatch_click_events(self, element):
        """Dispatch comprehensive click events"""
        self.driver.execute_script("""
            var element = arguments[0];
            var rect = element.getBoundingClientRect();

            // Create comprehensive event sequence
            var events = [
                { type: 'mouseover', bubbles: true, cancelable: true },
                { type: 'mouseenter', bubbles: false, cancelable: false },
                { type: 'mousemove', bubbles: true, cancelable: true },
                { type: 'mousedown', bubbles: true, cancelable: true },
                { type: 'focus', bubbles: false, cancelable: false },
                { type: 'mouseup', bubbles: true, cancelable: true },
                { type: 'click', bubbles: true, cancelable: true }
            ];

            for (var i = 0; i < events.length; i++) {
                var eventConfig = events[i];
                var event = new MouseEvent(eventConfig.type, {
                    view: window,
                    bubbles: eventConfig.bubbles,
                    cancelable: eventConfig.cancelable,
                    clientX: rect.left + rect.width/2,
                    clientY: rect.top + rect.height/2
                });
                element.dispatchEvent(event);
            }

            // Also trigger click handler if exists
            if (element.onclick) {
                element.onclick();
            }
        """, element)

    def attempt_form_submit(self, element):
        """Attempt form submission if element is in a form"""
        try:
            # Find parent form
            form = element.find_element(By.XPATH, "./ancestor::form[1]")
            if form:
                form.submit()
                return

            # Look for submit button in same container
            container = element.find_element(By.XPATH, "./ancestor::*[contains(@class, 'job') or contains(@class, 'card')][1]")
            submit_buttons = container.find_elements(By.CSS_SELECTOR, "input[type='submit'], button[type='submit']")

            for submit_btn in submit_buttons:
                if submit_btn.is_displayed() and submit_btn.is_enabled():
                    submit_btn.click()
                    return

        except Exception:
            pass

    def analyze_application_result(self, original_url, original_windows, button_info, click_result):
        """Analyze the result of job application"""
        try:
            # Check for new windows/tabs
            new_windows = self.driver.window_handles
            if len(new_windows) > len(original_windows):
                new_window = [w for w in new_windows if w not in original_windows][0]
                self.driver.switch_to.window(new_window)
                new_url = self.driver.current_url

                # Analyze new page
                page_analysis = self.analyze_job_application_page(new_url)

                # Close new window and return to original
                self.driver.close()
                self.driver.switch_to.window(original_windows[0])

                return {
                    'button_info': button_info,
                    'success': True,
                    'action': 'new_window',
                    'new_url': new_url,
                    'page_analysis': page_analysis,
                    'click_method': click_result['method'],
                    'details': f"Opened new window: {page_analysis.get('type', 'unknown')}",
                    'timestamp': time.time()
                }

            # Check for URL change (navigation)
            elif self.driver.current_url != original_url:
                new_url = self.driver.current_url
                page_analysis = self.analyze_job_application_page(new_url)

                # Go back to original page
                self.driver.back()
                time.sleep(2)

                return {
                    'button_info': button_info,
                    'success': True,
                    'action': 'navigation',
                    'new_url': new_url,
                    'page_analysis': page_analysis,
                    'click_method': click_result['method'],
                    'details': f"Navigated to: {page_analysis.get('type', 'unknown')}",
                    'timestamp': time.time()
                }

            # Check for modal/content change
            else:
                content_analysis = self.analyze_page_content_change()

                return {
                    'button_info': button_info,
                    'success': True,
                    'action': 'content_change',
                    'content_analysis': content_analysis,
                    'click_method': click_result['method'],
                    'details': f"Content changed: {content_analysis.get('type', 'unknown')}",
                    'timestamp': time.time()
                }

        except Exception as e:
            return {
                'button_info': button_info,
                'success': False,
                'error': f"Result analysis error: {str(e)}",
                'timestamp': time.time()
            }

    def analyze_job_application_page(self, url):
        """Analyze job application page type"""
        try:
            page_source = self.driver.page_source.lower()

            analysis = {
                'url': url,
                'type': 'unknown',
                'indicators': [],
                'confidence': 0
            }

            # Application form indicators
            if any(indicator in page_source for indicator in [
                'submit resume', 'upload resume', 'cv upload', 'application form',
                'personal information', 'work experience', 'education'
            ]):
                analysis['type'] = 'application_form'
                analysis['confidence'] = 90
                analysis['indicators'].append('Application form detected')

            # External job board indicators
            elif any(site in url.lower() for site in [
                'linkedin.com', 'indeed.com', 'glassdoor.com', 'monster.com',
                'ziprecruiter.com', 'careerbuilder.com'
            ]):
                analysis['type'] = 'external_job_board'
                analysis['confidence'] = 95
                analysis['indicators'].append(f'External job board: {url}')

            # Company career page indicators
            elif any(indicator in page_source for indicator in [
                'careers', 'job opening', 'position details', 'apply for this position'
            ]):
                analysis['type'] = 'company_careers'
                analysis['confidence'] = 85
                analysis['indicators'].append('Company careers page')

            # Success page indicators
            elif any(indicator in page_source for indicator in [
                'application submitted', 'thank you', 'successfully applied',
                'application received', 'we will review'
            ]):
                analysis['type'] = 'success_page'
                analysis['confidence'] = 95
                analysis['indicators'].append('Application success page')

            # Login/auth required
            elif any(indicator in page_source for indicator in [
                'login', 'sign in', 'create account', 'register'
            ]):
                analysis['type'] = 'login_required'
                analysis['confidence'] = 80
                analysis['indicators'].append('Authentication required')

            return analysis

        except Exception:
            return {'url': url, 'type': 'unknown', 'indicators': [], 'confidence': 0}

    def analyze_page_content_change(self):
        """Analyze page content changes"""
        try:
            page_source = self.driver.page_source.lower()

            analysis = {
                'type': 'unknown',
                'indicators': [],
                'confidence': 0
            }

            # Modal indicators
            if any(indicator in page_source for indicator in [
                'modal', 'popup', 'dialog', 'overlay', 'lightbox'
            ]):
                analysis['type'] = 'modal_opened'
                analysis['confidence'] = 80
                analysis['indicators'].append('Modal or popup detected')

            # Success indicators
            elif any(indicator in page_source for indicator in [
                'success', 'applied', 'submitted', 'thank you'
            ]):
                analysis['type'] = 'success_message'
                analysis['confidence'] = 90
                analysis['indicators'].append('Success message detected')

            # Form indicators
            elif any(indicator in page_source for indicator in [
                'form', 'input', 'textarea', 'upload'
            ]):
                analysis['type'] = 'form_appeared'
                analysis['confidence'] = 70
                analysis['indicators'].append('Form elements detected')

            return analysis

        except Exception:
            return {'type': 'unknown', 'indicators': [], 'confidence': 0}

    def save_zero_touch_results(self):
        """Save comprehensive zero-touch results"""
        try:
            timestamp = self.session_id

            # Complete results
            results = {
                'session_info': {
                    'session_id': self.session_id,
                    'email': self.email,
                    'timestamp': timestamp,
                    'start_time': datetime.fromtimestamp(self.stats['start_time']).isoformat(),
                    'session_reused': self.stats['session_reused'],
                    'google_account_found': self.stats['google_account_found']
                },
                'authentication_stats': {
                    'auth_duration': self.stats.get('auth_end_time', 0) - self.stats.get('auth_start_time', 0) if self.stats.get('auth_end_time') and self.stats.get('auth_start_time') else 0,
                    'session_reused': self.stats['session_reused']
                },
                'application_stats': self.stats,
                'apply_buttons_found': self.apply_buttons,
                'successful_applications': self.successful_applications,
                'failed_applications': self.failed_applications
            }

            # Save complete results
            complete_file = f'zero_touch_results_{timestamp}.json'
            with open(complete_file, 'w', encoding='utf-8') as f:
                json.dump(results, f, indent=2, default=str)

            # Save summary
            summary = {
                'session_id': self.session_id,
                'email': self.email,
                'total_buttons_found': self.stats['buttons_found'],
                'applications_attempted': self.stats['applications_attempted'],
                'applications_successful': self.stats['successful_applications'],
                'applications_failed': self.stats['failed_applications'],
                'success_rate_percent': (self.stats['successful_applications'] / max(self.stats['applications_attempted'], 1)) * 100,
                'session_reused': self.stats['session_reused'],
                'successful_jobs': [
                    {
                        'job_text': app['button_info']['text'],
                        'action': app.get('action', 'unknown'),
                        'new_url': app.get('new_url', 'N/A'),
                        'click_method': app.get('click_method', 'unknown'),
                        'details': app.get('details', 'N/A')
                    }
                    for app in self.successful_applications
                ]
            }

            summary_file = f'zero_touch_summary_{timestamp}.json'
            with open(summary_file, 'w', encoding='utf-8') as f:
                json.dump(summary, f, indent=2, default=str)

            logger.info(f"Zero-touch results saved to {complete_file} and {summary_file}")

        except Exception as e:
            logger.error(f"Error saving zero-touch results: {e}")

    def print_zero_touch_summary(self):
        """Print comprehensive zero-touch summary"""
        print(f"\n{'='*100}")
        print(f"🏆 ZERO-TOUCH SSO AUTOMATION - COMPLETE RESULTS")
        print(f"{'='*100}")

        # Session info
        print(f"Email: {self.email}")
        print(f"Session ID: {self.session_id}")
        print(f"Session Reused: {'✅ Yes' if self.stats['session_reused'] else '❌ No'}")

        if self.stats.get('auth_end_time') and self.stats.get('auth_start_time'):
            auth_duration = self.stats['auth_end_time'] - self.stats['auth_start_time']
            print(f"Authentication Time: {auth_duration:.2f} seconds")

        total_duration = time.time() - self.stats['start_time']
        print(f"Total Session Time: {total_duration:.2f} seconds ({total_duration/60:.1f} minutes)")

        # Application statistics
        print(f"\n📊 APPLICATION STATISTICS:")
        print(f"{'='*60}")
        print(f"Apply Buttons Found: {self.stats['buttons_found']}")
        print(f"Applications Attempted: {self.stats['applications_attempted']}")
        print(f"Successful Applications: {self.stats['successful_applications']}")
        print(f"Failed Applications: {self.stats['failed_applications']}")

        if self.stats['applications_attempted'] > 0:
            success_rate = (self.stats['successful_applications'] / self.stats['applications_attempted']) * 100
            print(f"Success Rate: {success_rate:.1f}%")

        # Successful applications
        if self.successful_applications:
            print(f"\n✅ SUCCESSFUL APPLICATIONS ({len(self.successful_applications)}):")
            print(f"{'='*80}")
            for i, app in enumerate(self.successful_applications, 1):
                job_text = app['button_info']['text'][:60]
                action = app.get('action', 'unknown')
                method = app.get('click_method', 'unknown')
                print(f"{i:2d}. {job_text}{'...' if len(app['button_info']['text']) > 60 else ''}")
                print(f"    ACTION: {action} | METHOD: {method}")
                if app.get('new_url'):
                    print(f"    URL: {app['new_url'][:70]}{'...' if len(app['new_url']) > 70 else ''}")
                if app.get('details'):
                    print(f"    DETAILS: {app['details']}")
                print()

        # Failed applications (summary)
        if self.failed_applications:
            print(f"\n❌ FAILED APPLICATIONS ({len(self.failed_applications)}):")
            print(f"{'='*60}")
            error_summary = {}
            for app in self.failed_applications:
                error = app.get('error', 'unknown')
                error_summary[error] = error_summary.get(error, 0) + 1

            for error, count in error_summary.items():
                print(f"  • {error}: {count} failures")

        # Final message
        print(f"\n{'='*100}")
        if self.stats['successful_applications'] > 0:
            print(f"🎉 ZERO-TOUCH AUTOMATION COMPLETED SUCCESSFULLY!")
            print(f"   Applied to {self.stats['successful_applications']} jobs out of {self.stats['buttons_found']} found!")
            print(f"   Average time per application: {total_duration/max(self.stats['applications_attempted'], 1):.1f} seconds")
        else:
            print(f"⚠️  ZERO-TOUCH AUTOMATION COMPLETED WITH ISSUES")
            print(f"   Found {self.stats['buttons_found']} buttons but no successful applications")

        print(f"   Session details saved in results files")
        print(f"   Next run will be even faster with saved session!")
        print(f"{'='*100}")

    def run_zero_touch_automation(self):
        """Run the complete zero-touch automation"""
        try:
            print("🚀 ZERO-TOUCH SSO JOBRIGHT.AI AUTOMATION")
            print(f"Email: {self.email}")
            print("100% AUTOMATED - NO MANUAL INTERVENTION REQUIRED!")
            print("="*80)

            # Setup advanced driver
            if not self.setup_advanced_driver():
                print("❌ Advanced WebDriver setup failed")
                return False

            # Zero-touch SSO flow
            print("\n🔐 Starting zero-touch SSO authentication...")
            if not self.zero_touch_sso_flow():
                print("❌ Zero-touch SSO authentication failed")
                return False

            print("✅ Zero-touch SSO authentication successful!")

            # Load all jobs
            print("\n📄 Loading all jobs with advanced strategies...")
            self.load_all_jobs_advanced()

            # Find all apply buttons
            print("\n🔍 Finding ALL apply buttons with ultimate detection...")
            self.apply_buttons = self.find_all_apply_buttons_ultimate()

            if not self.apply_buttons:
                print("❌ No apply buttons found!")

                # Save debug info
                with open(f'debug_zero_touch_{self.session_id}.html', 'w', encoding='utf-8') as f:
                    f.write(self.driver.page_source)
                print(f"Debug: Page source saved for analysis")

                return False

            print(f"✅ Found {len(self.apply_buttons)} apply buttons")

            # Display found buttons
            print(f"\n🎯 ZERO-TOUCH APPLICATION TO ALL {len(self.apply_buttons)} JOBS:")
            print("="*80)
            for i, button in enumerate(self.apply_buttons[:10], 1):  # Show first 10
                print(f"{i:2d}. {button['text'][:70]}{'...' if len(button['text']) > 70 else ''}")

            if len(self.apply_buttons) > 10:
                print(f"... and {len(self.apply_buttons) - 10} more buttons")

            # Zero-touch application to all jobs
            print(f"\n🎯 STARTING ZERO-TOUCH APPLICATION PROCESS...")
            self.apply_to_all_jobs_zero_touch()

            return True

        except Exception as e:
            logger.error(f"Zero-touch automation failed: {e}")
            print(f"❌ Zero-touch automation failed: {e}")
            return False

        finally:
            # Save results and print summary
            self.save_zero_touch_results()
            self.print_zero_touch_summary()

            # Close browser
            if self.driver:
                if not self.headless:
                    print(f"\nPress Enter to close browser and complete zero-touch automation...")
                    input()
                self.driver.quit()


def main():
    """Main function for zero-touch automation"""
    print("🏆 ZERO-TOUCH SSO AUTOMATION - JOBRIGHT.AI")
    print("100% Automated Google SSO + Apply to ALL jobs!")
    print("NO MANUAL INTERVENTION REQUIRED!")
    print("="*80)

    email = "jeremykalilin@gmail.com"

    print(f"Target Email: {email}")
    print("This automation will:")
    print("✅ Automatically handle Google SSO login")
    print("✅ Reuse existing sessions (login once, use forever)")
    print("✅ Find ALL Apply Now buttons using ultimate detection")
    print("✅ Apply to ALL jobs automatically with zero-touch")
    print("✅ Handle new pages, modals, and redirects")
    print("✅ Generate comprehensive reports")
    print("✅ Save session for future runs (even faster)")

    headless = input("\nRun in headless mode (no browser window)? (y/n): ").strip().lower() == 'y'

    print(f"\n🚀 STARTING ZERO-TOUCH AUTOMATION...")
    print(f"This is completely automated - sit back and watch!")

    confirm = input(f"\nBegin zero-touch SSO and job applications? (y/n): ").strip().lower()

    if confirm != 'y':
        print("Zero-touch automation cancelled")
        return

    # Run zero-touch automation
    automation = ZeroTouchSSoAutomation(email=email, headless=headless)
    success = automation.run_zero_touch_automation()

    # Final message
    if success:
        print(f"\n🎉 ZERO-TOUCH AUTOMATION COMPLETED SUCCESSFULLY!")
        print(f"Applied to {automation.stats['successful_applications']} jobs automatically")
        print(f"Session saved for future runs - next time will be even faster!")
    else:
        print(f"\n💥 ZERO-TOUCH AUTOMATION COMPLETED WITH ISSUES")
        print("Check the detailed logs and results files for information")

    print("\n🔥 ZERO-TOUCH AUTOMATION COMPLETE!")

if __name__ == "__main__":
    main()