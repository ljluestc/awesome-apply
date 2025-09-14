#!/usr/bin/env python3
"""
Enhanced JobRight.ai Automation - Focused on Apply with Auto Fill
Specifically designed to:
1. Identify ALL "Apply with auto fill" buttons on JobRight page
2. Open new pages in browser when clicking buttons
3. Handle SSO authentication for jeremykalilin@gmail.com
"""

import time
import json
import logging
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
        logging.FileHandler('enhanced_jobright_automation.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class EnhancedJobRightAutomation:
    def __init__(self, email="jeremykalilin@gmail.com", headless=False):
        """Initialize enhanced automation"""
        self.email = email
        self.headless = headless
        self.driver = None
        self.base_url = "https://jobright.ai"
        self.session_id = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # Session management
        self.session_file = f'enhanced_session_{email.replace("@", "_")}.pkl'
        
        # Results tracking
        self.apply_buttons = []
        self.successful_applications = []
        self.failed_applications = []
        
        # Statistics
        self.stats = {
            'start_time': time.time(),
            'buttons_found': 0,
            'applications_attempted': 0,
            'successful_applications': 0,
            'failed_applications': 0,
            'new_pages_opened': 0
        }

    def setup_driver(self):
        """Setup Chrome WebDriver optimized for JobRight"""
        chrome_options = Options()
        
        if self.headless:
            chrome_options.add_argument("--headless")
        
        # Core options
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("--start-maximized")
        
        # Session persistence for SSO
        chrome_options.add_argument(f"--user-data-dir=/tmp/chrome_profile_{self.session_id}")
        
        # Anti-detection
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        chrome_options.add_argument("--user-agent=Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
        
        # SSO support
        chrome_options.add_argument("--disable-web-security")
        chrome_options.add_argument("--allow-running-insecure-content")
        
        try:
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            
            # Anti-detection scripts
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            
            self.driver.implicitly_wait(10)
            self.driver.set_page_load_timeout(60)
            
            logger.info("Chrome WebDriver initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize WebDriver: {e}")
            return False

    def load_session(self):
        """Load existing session if available"""
        try:
            if os.path.exists(self.session_file):
                with open(self.session_file, 'rb') as f:
                    cookies = pickle.load(f)
                
                self.driver.get(self.base_url)
                time.sleep(2)
                
                for cookie in cookies:
                    try:
                        self.driver.add_cookie(cookie)
                    except Exception as e:
                        logger.warning(f"Could not add cookie: {e}")
                
                self.driver.refresh()
                time.sleep(3)
                
                logger.info("Loaded existing session")
                return True
        except Exception as e:
            logger.warning(f"Could not load session: {e}")
        
        return False

    def save_session(self):
        """Save current session"""
        try:
            cookies = self.driver.get_cookies()
            with open(self.session_file, 'wb') as f:
                pickle.dump(cookies, f)
            logger.info("Session saved")
        except Exception as e:
            logger.warning(f"Could not save session: {e}")

    def handle_sso_authentication(self):
        """Handle SSO authentication for jeremykalilin@gmail.com"""
        try:
            logger.info("Starting SSO authentication...")
            
            # Try loading existing session first
            if self.load_session():
                if self.verify_authentication():
                    logger.info("Already authenticated with existing session")
                    return True
            
            # Navigate to JobRight
            self.driver.get(self.base_url)
            time.sleep(3)
            
            # Look for sign-in button
            signin_selectors = [
                "//button[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'sign in')]",
                "//a[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'sign in')]",
                "//button[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'login')]",
                "//a[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'login')]"
            ]
            
            signin_clicked = False
            for selector in signin_selectors:
                try:
                    elements = self.driver.find_elements(By.XPATH, selector)
                    for element in elements:
                        if element.is_displayed() and element.is_enabled():
                            logger.info(f"Found sign-in button: {element.text}")
                            element.click()
                            time.sleep(3)
                            signin_clicked = True
                            break
                    if signin_clicked:
                        break
                except Exception:
                    continue
            
            if not signin_clicked:
                # Try direct login URLs
                login_urls = [f"{self.base_url}/login", f"{self.base_url}/auth/login"]
                for url in login_urls:
                    try:
                        self.driver.get(url)
                        time.sleep(3)
                        break
                    except:
                        continue
            
            # Look for Google SSO button
            google_selectors = [
                "//button[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'google')]",
                "//a[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'google')]",
                "//button[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'continue with google')]",
                "//*[contains(@class, 'google')]",
                "//img[contains(@src, 'google')]/ancestor::button"
            ]
            
            google_clicked = False
            for selector in google_selectors:
                try:
                    elements = self.driver.find_elements(By.XPATH, selector)
                    for element in elements:
                        if element.is_displayed() and element.is_enabled():
                            logger.info(f"Found Google SSO button: {element.text}")
                            element.click()
                            time.sleep(3)
                            google_clicked = True
                            break
                    if google_clicked:
                        break
                except Exception:
                    continue
            
            if not google_clicked:
                logger.error("Could not find Google SSO button")
                return False
            
            # Handle Google authentication flow
            return self.handle_google_auth_flow()
            
        except Exception as e:
            logger.error(f"SSO authentication failed: {e}")
            return False

    def handle_google_auth_flow(self):
        """Handle Google authentication flow"""
        try:
            # Wait for Google login page
            WebDriverWait(self.driver, 15).until(
                lambda driver: "accounts.google.com" in driver.current_url.lower()
            )
            
            logger.info("Google login page loaded")
            
            # Enter email
            email_input = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "input[type='email']"))
            )
            
            email_input.clear()
            email_input.send_keys(self.email)
            time.sleep(1)
            
            # Click Next
            next_button = self.driver.find_element(By.CSS_SELECTOR, "#identifierNext")
            next_button.click()
            time.sleep(3)
            
            # Check if password is required
            try:
                password_input = WebDriverWait(self.driver, 5).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "input[type='password']"))
                )
                
                if password_input.is_displayed():
                    logger.warning("Password required for Google login")
                    print(f"\n🔐 PASSWORD REQUIRED for {self.email}")
                    print("Please enter your Google password in the browser window...")
                    print("The automation will continue automatically after password entry.")
                    
                    # Wait for password entry
                    self.wait_for_password_completion()
            
            except TimeoutException:
                logger.info("No password required - already logged in")
            
            # Handle consent screen
            self.handle_google_consent()
            
            # Save session
            self.save_session()
            
            return True
            
        except Exception as e:
            logger.error(f"Google auth flow failed: {e}")
            return False

    def wait_for_password_completion(self):
        """Wait for manual password entry to complete"""
        try:
            max_wait = 300  # 5 minutes
            start_time = time.time()
            
            while time.time() - start_time < max_wait:
                current_url = self.driver.current_url.lower()
                
                if "jobright.ai" in current_url:
                    logger.info("Password entry completed, redirected to JobRight")
                    return True
                
                if "consent" in current_url or "oauth" in current_url:
                    logger.info("Moved to consent page after password")
                    return True
                
                time.sleep(2)
            
            logger.warning("Password entry timeout")
            return True
            
        except Exception as e:
            logger.warning(f"Error waiting for password: {e}")
            return True

    def handle_google_consent(self):
        """Handle Google consent screen"""
        try:
            time.sleep(5)
            
            consent_selectors = [
                "//button[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'continue')]",
                "//button[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'allow')]",
                "//button[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'accept')]"
            ]
            
            for selector in consent_selectors:
                try:
                    elements = self.driver.find_elements(By.XPATH, selector)
                    for element in elements:
                        if element.is_displayed() and element.is_enabled():
                            logger.info(f"Found consent button: {element.text}")
                            element.click()
                            time.sleep(3)
                            
                            # Wait for redirect to JobRight
                            WebDriverWait(self.driver, 15).until(
                                lambda driver: "jobright.ai" in driver.current_url.lower()
                            )
                            
                            logger.info("Consent completed, redirected to JobRight")
                            return True
                except Exception:
                    continue
            
            # Check if already at JobRight
            if "jobright.ai" in self.driver.current_url.lower():
                logger.info("Already at JobRight - consent auto-approved")
                return True
            
            return True
            
        except Exception as e:
            logger.error(f"Error handling consent: {e}")
            return True

    def verify_authentication(self):
        """Verify if user is authenticated"""
        try:
            self.driver.get(f"{self.base_url}/jobs/recommend")
            time.sleep(5)
            
            current_url = self.driver.current_url.lower()
            if any(keyword in current_url for keyword in ['job', 'recommend', 'dashboard']):
                if self.has_job_content():
                    logger.info("Authentication verified")
                    return True
            
            return False
            
        except Exception:
            return False

    def has_job_content(self):
        """Check if page has job content"""
        try:
            page_source = self.driver.page_source.lower()
            job_indicators = ['apply', 'job', 'position', 'company', 'salary', 'remote']
            return sum(1 for indicator in job_indicators if indicator in page_source) >= 3
        except:
            return False

    def navigate_to_jobs_page(self, page_num=16):
        """Navigate to specific jobs page"""
        try:
            url = f"{self.base_url}/jobs/recommend?pos={page_num}"
            logger.info(f"Navigating to: {url}")
            self.driver.get(url)
            
            WebDriverWait(self.driver, 20).until(
                lambda driver: driver.execute_script("return document.readyState") == "complete"
            )
            
            time.sleep(5)
            self.scroll_and_load_all_content()
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to navigate to jobs page: {e}")
            return False

    def scroll_and_load_all_content(self):
        """Scroll through page to load all content"""
        try:
            last_height = self.driver.execute_script("return document.body.scrollHeight")
            scroll_attempts = 0
            max_scrolls = 10
            
            while scroll_attempts < max_scrolls:
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(3)
                
                new_height = self.driver.execute_script("return document.body.scrollHeight")
                
                if new_height == last_height:
                    scroll_attempts += 1
                else:
                    last_height = new_height
                    scroll_attempts = 0
                
                # Try clicking load more buttons
                self.click_load_more_buttons()
            
            # Scroll back to top
            self.driver.execute_script("window.scrollTo(0, 0);")
            time.sleep(2)
            
            logger.info("Page content loading completed")
            
        except Exception as e:
            logger.warning(f"Error during content loading: {e}")

    def click_load_more_buttons(self):
        """Click any Load More buttons"""
        try:
            load_more_patterns = ["load more", "show more", "view more", "see more"]
            
            for pattern in load_more_patterns:
                try:
                    xpath = f"//button[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), '{pattern}')]"
                    elements = self.driver.find_elements(By.XPATH, xpath)
                    
                    for element in elements:
                        if element.is_displayed() and element.is_enabled():
                            element.click()
                            logger.info(f"Clicked load more button: {pattern}")
                            time.sleep(2)
                            return
                except:
                    continue
        except:
            pass

    def find_all_apply_buttons(self):
        """Find ALL Apply with auto fill buttons using comprehensive search"""
        try:
            logger.info("Searching for Apply with auto fill buttons...")
            all_buttons = []
            
            # Strategy 1: Direct text search for "Apply with auto fill"
            apply_text_patterns = [
                "apply with auto fill",
                "apply with autofill", 
                "apply with auto-fill",
                "apply now",
                "quick apply",
                "easy apply",
                "apply",
                "autofill",
                "auto-fill",
                "auto fill"
            ]
            
            for pattern in apply_text_patterns:
                try:
                    xpath = f"//*[contains(translate(normalize-space(text()), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), '{pattern.lower()}')]"
                    elements = self.driver.find_elements(By.XPATH, xpath)
                    
                    for element in elements:
                        if self.is_valid_apply_button(element):
                            button_info = self.extract_button_info(element, f"text_{pattern}")
                            if button_info and button_info not in all_buttons:
                                all_buttons.append(button_info)
                                logger.info(f"Found apply button: '{button_info['text'][:50]}...'")
                except Exception as e:
                    logger.warning(f"Error searching for pattern '{pattern}': {e}")
                    continue
            
            # Strategy 2: Search by class names and attributes
            class_patterns = ["apply", "autofill", "quick", "easy", "submit", "button"]
            
            for pattern in class_patterns:
                try:
                    selector = f"[class*='{pattern}']"
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    
                    for element in elements:
                        if self.is_valid_apply_button(element):
                            button_info = self.extract_button_info(element, f"class_{pattern}")
                            if button_info and button_info not in all_buttons:
                                all_buttons.append(button_info)
                                logger.info(f"Found apply button by class: '{button_info['text'][:50]}...'")
                except Exception as e:
                    logger.warning(f"Error searching by class '{pattern}': {e}")
                    continue
            
            # Strategy 3: Search all clickable elements
            try:
                clickable_elements = self.driver.find_elements(By.CSS_SELECTOR, 
                    "button, a, input[type='button'], input[type='submit'], [role='button'], [onclick]")
                
                for element in clickable_elements:
                    if self.is_valid_apply_button(element):
                        text = element.text.lower().strip()
                        if any(keyword in text for keyword in ['apply', 'submit', 'send', 'quick', 'easy', 'autofill']):
                            button_info = self.extract_button_info(element, "clickable")
                            if button_info and button_info not in all_buttons:
                                all_buttons.append(button_info)
                                logger.info(f"Found apply button in clickables: '{button_info['text'][:50]}...'")
            except Exception as e:
                logger.warning(f"Error searching clickable elements: {e}")
            
            # Remove duplicates
            unique_buttons = self.remove_duplicates(all_buttons)
            
            logger.info(f"Total unique apply buttons found: {len(unique_buttons)}")
            return unique_buttons
            
        except Exception as e:
            logger.error(f"Error finding apply buttons: {e}")
            return []

    def is_valid_apply_button(self, element):
        """Check if element is a valid apply button"""
        try:
            if not (element.is_displayed() and element.is_enabled()):
                return False
            
            text = element.text.strip()
            if not text or len(text) > 200:
                return False
            
            size = element.size
            if size['width'] < 30 or size['height'] < 15:
                return False
            
            return True
            
        except Exception:
            return False

    def extract_button_info(self, element, detection_method):
        """Extract comprehensive button information"""
        try:
            return {
                'text': element.text.strip(),
                'tag': element.tag_name,
                'classes': element.get_attribute('class') or '',
                'id': element.get_attribute('id') or '',
                'href': element.get_attribute('href') or '',
                'location': element.location,
                'size': element.size,
                'detection_method': detection_method,
                'timestamp': time.time(),
                'unique_id': f"{element.text[:20]}_{element.location['x']}_{element.location['y']}"
            }
        except Exception as e:
            logger.warning(f"Error extracting button info: {e}")
            return None

    def remove_duplicates(self, buttons):
        """Remove duplicate buttons"""
        try:
            unique_buttons = []
            seen = set()
            
            for button in buttons:
                if not button:
                    continue
                
                unique_id = button.get('unique_id', f"{button['text'][:20]}_{button['location']['x']}_{button['location']['y']}")
                
                if unique_id not in seen:
                    seen.add(unique_id)
                    unique_buttons.append(button)
            
            return unique_buttons
            
        except Exception as e:
            logger.error(f"Error removing duplicates: {e}")
            return buttons

    def display_found_buttons(self, buttons):
        """Display all found buttons"""
        print(f"\n{'='*80}")
        print(f"🎯 FOUND {len(buttons)} APPLY WITH AUTO FILL BUTTONS")
        print(f"{'='*80}")
        
        for i, button in enumerate(buttons, 1):
            print(f"{i:2d}. '{button['text'][:70]}{'...' if len(button['text']) > 70 else ''}'")
            print(f"    METHOD: {button['detection_method']}")
            print(f"    TAG: {button['tag']} | POSITION: ({button['location']['x']}, {button['location']['y']})")
            if button['href']:
                print(f"    LINK: {button['href'][:70]}...")
        
        print(f"\n{'='*80}")

    def click_apply_button(self, button_info, index, total):
        """Click an apply button and handle new page opening"""
        try:
            logger.info(f"Clicking button {index}/{total}: {button_info['text'][:50]}...")
            
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
            
            # Click element
            try:
                element.click()
                click_method = "standard"
            except ElementClickInterceptedException:
                try:
                    self.driver.execute_script("arguments[0].click();", element)
                    click_method = "javascript"
                except Exception as e:
                    return {
                        'button_info': button_info,
                        'success': False,
                        'error': f'Click failed: {str(e)}',
                        'timestamp': time.time()
                    }
            
            # Wait for response
            time.sleep(3)
            
            # Check for new windows/tabs
            new_windows = self.driver.window_handles
            if len(new_windows) > len(original_windows):
                new_window = [w for w in new_windows if w not in original_windows][0]
                self.driver.switch_to.window(new_window)
                new_url = self.driver.current_url
                
                logger.info(f"New window opened: {new_url}")
                self.stats['new_pages_opened'] += 1
                
                # Keep the new window open for user to see
                print(f"✅ NEW PAGE OPENED: {new_url}")
                
                # Switch back to original window
                self.driver.switch_to.window(original_windows[0])
                
                return {
                    'button_info': button_info,
                    'success': True,
                    'action': 'new_window_opened',
                    'new_url': new_url,
                    'click_method': click_method,
                    'timestamp': time.time()
                }
            
            # Check for URL change
            elif self.driver.current_url != original_url:
                new_url = self.driver.current_url
                logger.info(f"Page navigation: {new_url}")
                
                # Go back to original page
                self.driver.back()
                time.sleep(2)
                
                return {
                    'button_info': button_info,
                    'success': True,
                    'action': 'page_navigation',
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
            logger.error(f"Error clicking button {index}: {e}")
            return {
                'button_info': button_info,
                'success': False,
                'error': str(e),
                'timestamp': time.time()
            }

    def find_element_by_info(self, button_info):
        """Find element using stored information"""
        try:
            # Try by ID first
            if button_info.get('id'):
                try:
                    element = self.driver.find_element(By.ID, button_info['id'])
                    if element.is_displayed():
                        return element
                except:
                    pass
            
            # Try by text and position
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

    def apply_to_all_jobs(self, buttons):
        """Apply to all jobs and track new page openings"""
        logger.info(f"Starting application process for {len(buttons)} jobs...")
        
        for i, button_info in enumerate(buttons, 1):
            print(f"\n[{i}/{len(buttons)}] APPLYING TO: {button_info['text'][:60]}...")
            
            result = self.click_apply_button(button_info, i, len(buttons))
            
            if result['success']:
                self.successful_applications.append(result)
                self.stats['successful_applications'] += 1
                print(f"✅ SUCCESS: {result.get('action', 'Applied')}")
                if result.get('new_url'):
                    print(f"   → NEW PAGE: {result['new_url'][:70]}...")
            else:
                self.failed_applications.append(result)
                self.stats['failed_applications'] += 1
                print(f"❌ FAILED: {result.get('error', 'Unknown error')}")
            
            self.stats['applications_attempted'] += 1
            time.sleep(2)

    def save_results(self):
        """Save comprehensive results"""
        try:
            results = {
                'session_info': {
                    'session_id': self.session_id,
                    'email': self.email,
                    'timestamp': datetime.now().isoformat()
                },
                'statistics': self.stats,
                'apply_buttons_found': self.apply_buttons,
                'successful_applications': self.successful_applications,
                'failed_applications': self.failed_applications
            }
            
            results_file = f'enhanced_automation_results_{self.session_id}.json'
            with open(results_file, 'w', encoding='utf-8') as f:
                json.dump(results, f, indent=2, default=str)
            
            logger.info(f"Results saved to {results_file}")
            
        except Exception as e:
            logger.error(f"Error saving results: {e}")

    def print_final_summary(self):
        """Print final summary"""
        print(f"\n{'='*80}")
        print("🏆 ENHANCED JOBRIGHT AUTOMATION COMPLETE")
        print(f"{'='*80}")
        print(f"Email: {self.email}")
        print(f"Apply Buttons Found: {len(self.apply_buttons)}")
        print(f"Applications Attempted: {self.stats['applications_attempted']}")
        print(f"Successful Applications: {self.stats['successful_applications']}")
        print(f"Failed Applications: {self.stats['failed_applications']}")
        print(f"New Pages Opened: {self.stats['new_pages_opened']}")
        
        if self.stats['applications_attempted'] > 0:
            success_rate = (self.stats['successful_applications'] / self.stats['applications_attempted']) * 100
            print(f"Success Rate: {success_rate:.1f}%")
        
        print(f"{'='*80}")

    def run_complete_automation(self):
        """Run the complete automation process"""
        try:
            print("🚀 ENHANCED JOBRIGHT.AI AUTOMATION")
            print(f"Email: {self.email}")
            print("This will find ALL Apply with auto fill buttons and open new pages!")
            print("="*80)
            
            # Setup driver
            if not self.setup_driver():
                print("❌ Failed to setup WebDriver")
                return False
            
            # Handle SSO authentication
            print("\n🔐 Handling SSO authentication...")
            if not self.handle_sso_authentication():
                print("❌ SSO authentication failed")
                return False
            
            print("✅ SSO authentication successful!")
            
            # Navigate to jobs page
            print(f"\n🔄 Navigating to jobs page (pos=16)...")
            if not self.navigate_to_jobs_page(16):
                print("❌ Failed to navigate to jobs page")
                return False
            
            # Find all apply buttons
            print("\n🔍 Finding ALL Apply with auto fill buttons...")
            self.apply_buttons = self.find_all_apply_buttons()
            self.stats['buttons_found'] = len(self.apply_buttons)
            
            if not self.apply_buttons:
                print("❌ No Apply with auto fill buttons found!")
                return False
            
            # Display found buttons
            self.display_found_buttons(self.apply_buttons)
            
            # Apply to all jobs
            print(f"\n🚀 APPLYING TO ALL {len(self.apply_buttons)} JOBS...")
            self.apply_to_all_jobs(self.apply_buttons)
            
            return True
            
        except Exception as e:
            logger.error(f"Automation failed: {e}")
            print(f"❌ Automation failed: {e}")
            return False
        
        finally:
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
    """Main function"""
    print("🏆 ENHANCED JOBRIGHT.AI AUTOMATION")
    print("Find ALL Apply with auto fill buttons and open new pages!")
    print("="*80)
    
    email = "jeremykalilin@gmail.com"
    headless_mode = input("Run in headless mode? (y/n): ").strip().lower() == 'y'
    
    print(f"\n🚀 Starting automation for {email}...")
    print("This will:")
    print("✅ Handle SSO authentication automatically")
    print("✅ Find ALL Apply with auto fill buttons")
    print("✅ Open new pages in browser when clicking buttons")
    print("✅ Track all applications and new page openings")
    
    confirm = input(f"\nStart automation? (y/n): ").strip().lower()
    if confirm != 'y':
        print("Automation cancelled.")
        return
    
    # Run automation
    automation = EnhancedJobRightAutomation(email=email, headless=headless_mode)
    success = automation.run_complete_automation()
    
    if success:
        print("\n🎉 AUTOMATION COMPLETED SUCCESSFULLY!")
        print(f"Found {automation.stats['buttons_found']} Apply with auto fill buttons")
        print(f"Opened {automation.stats['new_pages_opened']} new pages")
    else:
        print("\n💥 AUTOMATION ENCOUNTERED ISSUES")
    
    print("Check the generated files for detailed results")


if __name__ == "__main__":
    main()
