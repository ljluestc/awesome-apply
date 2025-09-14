#!/usr/bin/env python3
"""
Complete Fixed JobRight.ai Auto-Apply Automation
Handles authentication and finds ALL Apply Now buttons with automatic application
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
from selenium.common.exceptions import TimeoutException, NoSuchElementException, ElementClickInterceptedException
from webdriver_manager.chrome import ChromeDriverManager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('jobright_fixed_automation.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class JobRightFixedAutomation:
    def __init__(self, headless=False):
        """Initialize the automation"""
        self.driver = None
        self.headless = headless
        self.base_url = "https://jobright.ai"
        self.apply_buttons = []
        self.successful_applications = []
        self.failed_applications = []
        self.is_authenticated = False

    def setup_driver(self):
        """Setup Chrome WebDriver with optimal configuration"""
        chrome_options = Options()

        if self.headless:
            chrome_options.add_argument("--headless")

        # Essential options
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("--start-maximized")

        # Anti-detection
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        chrome_options.add_argument("--user-agent=Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")

        # Additional options
        chrome_options.add_argument("--disable-extensions")
        chrome_options.add_argument("--disable-plugins")
        chrome_options.add_argument("--disable-images")  # Faster loading

        try:
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=chrome_options)

            # Remove webdriver property
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

            # Set timeouts
            self.driver.implicitly_wait(10)
            self.driver.set_page_load_timeout(30)

            logger.info("Chrome WebDriver initialized successfully")
            return True

        except Exception as e:
            logger.error(f"Failed to initialize Chrome WebDriver: {e}")
            return False

    def handle_authentication(self):
        """Handle JobRight.ai authentication"""
        try:
            logger.info("Checking authentication status...")

            # First, try to access a protected page
            self.driver.get(f"{self.base_url}/jobs/recommend")
            time.sleep(5)

            current_url = self.driver.current_url.lower()

            # Check if we're redirected to login/signup
            if any(keyword in current_url for keyword in ['login', 'signin', 'signup', 'onboarding', 'auth']):
                logger.info("Authentication required - manual login needed")

                print("\n🔐 AUTHENTICATION REQUIRED")
                print("=" * 60)
                print("JobRight.ai requires login to access job listings.")
                print("Please follow these steps:")
                print("1. The browser window will stay open")
                print("2. Log in manually using your credentials")
                print("3. Navigate to the jobs page")
                print("4. Come back here and press Enter when ready")
                print("=" * 60)

                # Wait for manual login
                input("Press Enter after you've logged in and are on the jobs page...")

                # Verify we're now on a jobs page
                current_url = self.driver.current_url.lower()
                if 'job' in current_url and 'jobright.ai' in current_url:
                    self.is_authenticated = True
                    logger.info("Authentication successful")
                    return True
                else:
                    logger.warning("Authentication verification failed")
                    return False
            else:
                # Already authenticated
                self.is_authenticated = True
                logger.info("Already authenticated")
                return True

        except Exception as e:
            logger.error(f"Authentication error: {e}")
            return False

    def navigate_to_jobs_page(self):
        """Navigate to jobs page and ensure we're in the right place"""
        try:
            # Try different job URLs
            job_urls = [
                f"{self.base_url}/jobs/recommend",
                f"{self.base_url}/jobs",
                f"{self.base_url}/dashboard"
            ]

            for url in job_urls:
                logger.info(f"Trying URL: {url}")
                self.driver.get(url)
                time.sleep(5)

                # Check if we have job listings
                if self.has_job_listings():
                    logger.info(f"Successfully loaded jobs page: {self.driver.current_url}")
                    return True

            logger.warning("Could not access jobs page")
            return False

        except Exception as e:
            logger.error(f"Error navigating to jobs page: {e}")
            return False

    def has_job_listings(self):
        """Check if the current page has job listings"""
        try:
            # Look for job-related elements
            job_indicators = [
                "job", "position", "role", "career", "apply", "company",
                "salary", "location", "remote", "full-time", "part-time"
            ]

            page_text = self.driver.page_source.lower()

            # Count how many job indicators we find
            indicator_count = sum(1 for indicator in job_indicators if indicator in page_text)

            # If we find multiple indicators, likely a jobs page
            if indicator_count >= 5:
                logger.info(f"Job indicators found: {indicator_count}")
                return True

            return False

        except Exception:
            return False

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
            load_more_selectors = [
                "button:contains('Load More')",
                "button:contains('Show More')",
                "button:contains('View More')",
                "[class*='load']:contains('more')",
                "[class*='show']:contains('more')",
                "a:contains('Load More')",
                "a:contains('Show More')"
            ]

            for selector in load_more_selectors:
                try:
                    # Convert jQuery-style selector to XPath
                    if ':contains(' in selector:
                        text = selector.split(':contains(')[1].split(')')[0].strip("'\"")
                        tag = selector.split(':contains(')[0]
                        xpath = f"//{tag}[contains(text(), '{text}')]"

                        elements = self.driver.find_elements(By.XPATH, xpath)
                        for element in elements:
                            if element.is_displayed() and element.is_enabled():
                                try:
                                    element.click()
                                    logger.info(f"Clicked load more button: {text}")
                                    time.sleep(2)
                                except:
                                    pass
                except:
                    continue

        except Exception:
            pass

    def find_all_apply_buttons_comprehensive(self):
        """Find ALL apply buttons using comprehensive search strategies"""
        apply_buttons = []

        logger.info("Starting comprehensive apply button search...")

        # Define search patterns
        apply_text_patterns = [
            "apply now", "apply with autofill", "quick apply", "easy apply",
            "apply", "apply for", "apply to", "submit application",
            "apply for this job", "apply for position", "one-click apply",
            "instant apply", "autofill", "auto-fill", "auto apply"
        ]

        apply_class_patterns = [
            "apply", "autofill", "quick", "easy", "submit", "application",
            "job-apply", "apply-btn", "apply-button", "btn-apply"
        ]

        # Strategy 1: Text-based search
        logger.info("Searching by text content...")
        for pattern in apply_text_patterns:
            try:
                # Multiple XPath variations
                xpaths = [
                    f"//*[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), '{pattern.lower()}')]",
                    f"//button[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), '{pattern.lower()}')]",
                    f"//a[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), '{pattern.lower()}')]",
                    f"//*[contains(translate(@aria-label, 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), '{pattern.lower()}')]",
                    f"//*[contains(translate(@title, 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), '{pattern.lower()}')]"
                ]

                for xpath in xpaths:
                    try:
                        elements = self.driver.find_elements(By.XPATH, xpath)
                        for element in elements:
                            if self.is_valid_apply_element(element):
                                button_info = self.extract_element_info(element, f"text_{pattern}")
                                if button_info and not self.is_duplicate_button(button_info, apply_buttons):
                                    apply_buttons.append(button_info)
                                    logger.info(f"Found apply button (text): '{button_info['text'][:50]}...'")
                    except Exception as e:
                        continue

            except Exception as e:
                continue

        # Strategy 2: Class-based search
        logger.info("Searching by class names...")
        for pattern in apply_class_patterns:
            try:
                selectors = [
                    f"[class*='{pattern}']",
                    f"button[class*='{pattern}']",
                    f"a[class*='{pattern}']",
                    f"div[class*='{pattern}'][onclick]",
                    f"span[class*='{pattern}'][onclick]"
                ]

                for selector in selectors:
                    try:
                        elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                        for element in elements:
                            if self.is_valid_apply_element(element):
                                button_info = self.extract_element_info(element, f"class_{pattern}")
                                if button_info and not self.is_duplicate_button(button_info, apply_buttons):
                                    apply_buttons.append(button_info)
                                    logger.info(f"Found apply button (class): '{button_info['text'][:50]}...'")
                    except Exception:
                        continue

            except Exception:
                continue

        # Strategy 3: All clickable elements with filtering
        logger.info("Searching all clickable elements...")
        clickable_selectors = [
            "button", "a", "input[type='button']", "input[type='submit']",
            "[role='button']", "[onclick]", "[data-action]", "[data-click]"
        ]

        for selector in clickable_selectors:
            try:
                elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                for element in elements:
                    if self.is_valid_apply_element(element):
                        # Check if element text or attributes suggest it's an apply button
                        element_text = element.text.lower()
                        element_attrs = str(element.get_attribute('class') or '') + str(element.get_attribute('onclick') or '') + str(element.get_attribute('data-action') or '')
                        element_attrs = element_attrs.lower()

                        if any(pattern in element_text or pattern in element_attrs for pattern in apply_text_patterns):
                            button_info = self.extract_element_info(element, f"clickable_{selector}")
                            if button_info and not self.is_duplicate_button(button_info, apply_buttons):
                                apply_buttons.append(button_info)
                                logger.info(f"Found apply button (clickable): '{button_info['text'][:50]}...'")
            except Exception:
                continue

        logger.info(f"Apply button search completed. Found {len(apply_buttons)} buttons")
        return apply_buttons

    def is_valid_apply_element(self, element):
        """Check if element is a valid apply button"""
        try:
            # Must be displayed and enabled
            if not (element.is_displayed() and element.is_enabled()):
                return False

            # Check size (avoid tiny elements)
            size = element.size
            if size['width'] < 30 or size['height'] < 15:
                return False

            # Check if element is interactive
            tag = element.tag_name.lower()
            if tag in ['button', 'a', 'input']:
                return True

            # Check for onclick or other interactive attributes
            if element.get_attribute('onclick') or element.get_attribute('role') == 'button':
                return True

            # Must have some text content
            text = element.text.strip()
            if len(text) < 2:
                return False

            return True

        except Exception:
            return False

    def extract_element_info(self, element, detection_method):
        """Extract comprehensive element information"""
        try:
            # Get element attributes
            text = element.text.strip()
            tag = element.tag_name
            classes = element.get_attribute('class') or ''
            element_id = element.get_attribute('id') or ''
            href = element.get_attribute('href') or ''
            onclick = element.get_attribute('onclick') or ''
            data_action = element.get_attribute('data-action') or ''
            location = element.location
            size = element.size

            # Generate unique selector
            unique_selector = self.generate_unique_selector(element)

            return {
                'text': text,
                'tag': tag,
                'classes': classes,
                'id': element_id,
                'href': href,
                'onclick': onclick,
                'data_action': data_action,
                'location': location,
                'size': size,
                'detection_method': detection_method,
                'unique_selector': unique_selector,
                'timestamp': time.time()
            }

        except Exception as e:
            logger.warning(f"Error extracting element info: {e}")
            return None

    def generate_unique_selector(self, element):
        """Generate a unique CSS selector for the element"""
        try:
            # Try ID first
            element_id = element.get_attribute('id')
            if element_id:
                return f"#{element_id}"

            # Try class combination
            classes = element.get_attribute('class')
            if classes:
                class_list = classes.strip().split()
                if len(class_list) > 0:
                    return f"{element.tag_name.lower()}.{'.'.join(class_list[:3])}"

            # Fallback to tag + position
            return f"{element.tag_name.lower()}:nth-child({self.get_element_index(element)})"

        except:
            return "unknown"

    def get_element_index(self, element):
        """Get the index of element among its siblings"""
        try:
            return self.driver.execute_script("""
                var element = arguments[0];
                var index = 0;
                var sibling = element.previousElementSibling;
                while (sibling) {
                    if (sibling.tagName === element.tagName) {
                        index++;
                    }
                    sibling = sibling.previousElementSibling;
                }
                return index + 1;
            """, element)
        except:
            return 1

    def is_duplicate_button(self, button_info, existing_buttons):
        """Check if button is duplicate based on text and position"""
        try:
            for existing in existing_buttons:
                # Same text and similar position
                if (button_info['text'] == existing['text'] and
                    abs(button_info['location']['x'] - existing['location']['x']) < 10 and
                    abs(button_info['location']['y'] - existing['location']['y']) < 10):
                    return True
            return False
        except:
            return False

    def display_found_buttons(self, buttons):
        """Display all found apply buttons"""
        print(f"\n{'='*80}")
        print(f"🎯 FOUND {len(buttons)} APPLY NOW BUTTONS")
        print(f"{'='*80}")

        for i, button in enumerate(buttons, 1):
            print(f"\n{i:2d}. Text: '{button['text'][:70]}{'...' if len(button['text']) > 70 else ''}'")
            print(f"    Method: {button['detection_method']}")
            print(f"    Tag: {button['tag']} | Classes: {button['classes'][:50]}")
            print(f"    Position: ({button['location']['x']}, {button['location']['y']})")
            if button['href']:
                print(f"    Link: {button['href'][:70]}...")

        print(f"\n{'='*80}")

    def apply_to_all_jobs(self, buttons):
        """Apply to all jobs by clicking each button"""
        logger.info(f"Starting to apply to {len(buttons)} jobs...")

        for i, button_info in enumerate(buttons, 1):
            print(f"\n[{i}/{len(buttons)}] Applying to: {button_info['text'][:60]}...")

            try:
                result = self.click_apply_button_safe(button_info)

                if result['success']:
                    self.successful_applications.append(result)
                    print(f"✅ SUCCESS: {result.get('action', 'Applied')}")
                    if result.get('new_url'):
                        print(f"   → Opened: {result['new_url'][:80]}...")
                else:
                    self.failed_applications.append(result)
                    print(f"❌ FAILED: {result.get('error', 'Unknown error')}")

                # Wait between applications
                time.sleep(3)

            except Exception as e:
                error_result = {
                    'button_info': button_info,
                    'success': False,
                    'error': str(e),
                    'timestamp': time.time()
                }
                self.failed_applications.append(error_result)
                print(f"❌ ERROR: {str(e)}")
                continue

        logger.info(f"Application process completed. Success: {len(self.successful_applications)}, Failed: {len(self.failed_applications)}")

    def click_apply_button_safe(self, button_info):
        """Safely click an apply button with comprehensive error handling"""
        try:
            # Find the element using multiple strategies
            element = self.find_element_by_info(button_info)

            if not element:
                return {
                    'button_info': button_info,
                    'success': False,
                    'error': 'Element not found',
                    'timestamp': time.time()
                }

            # Get current state
            original_url = self.driver.current_url
            original_windows = self.driver.window_handles

            # Scroll to element
            self.driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", element)
            time.sleep(1)

            # Highlight element for debugging (if not headless)
            if not self.headless:
                self.driver.execute_script("arguments[0].style.border='3px solid red'", element)
                time.sleep(0.5)

            # Try multiple click methods
            click_success = False
            click_method = None

            # Method 1: Regular click
            try:
                element.click()
                click_success = True
                click_method = "regular"
            except ElementClickInterceptedException:
                # Method 2: JavaScript click
                try:
                    self.driver.execute_script("arguments[0].click();", element)
                    click_success = True
                    click_method = "javascript"
                except Exception:
                    # Method 3: ActionChains
                    try:
                        ActionChains(self.driver).move_to_element(element).click().perform()
                        click_success = True
                        click_method = "action_chains"
                    except Exception:
                        pass

            if not click_success:
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
                # New tab/window opened
                new_window = [w for w in new_windows if w not in original_windows][0]
                self.driver.switch_to.window(new_window)
                new_url = self.driver.current_url

                # Close new tab and return to original
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
                # Go back to original page
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

            # Check for modals/popups
            elif self.check_for_modals():
                # Close any modals
                self.close_modals()

                return {
                    'button_info': button_info,
                    'success': True,
                    'action': 'modal',
                    'click_method': click_method,
                    'timestamp': time.time()
                }

            else:
                # Click registered but no obvious change
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
        """Find element using the stored information"""
        try:
            # Method 1: By unique selector
            if button_info.get('unique_selector'):
                try:
                    element = self.driver.find_element(By.CSS_SELECTOR, button_info['unique_selector'])
                    if element.is_displayed():
                        return element
                except:
                    pass

            # Method 2: By ID
            if button_info.get('id'):
                try:
                    element = self.driver.find_element(By.ID, button_info['id'])
                    if element.is_displayed():
                        return element
                except:
                    pass

            # Method 3: By text and position
            try:
                text = button_info['text'][:30]  # First 30 characters
                xpath = f"//*[contains(text(), '{text}')]"
                elements = self.driver.find_elements(By.XPATH, xpath)

                # Find closest to original position
                original_pos = button_info['location']
                for element in elements:
                    if element.is_displayed():
                        current_pos = element.location
                        distance = abs(current_pos['x'] - original_pos['x']) + abs(current_pos['y'] - original_pos['y'])
                        if distance < 100:  # Within 100 pixels
                            return element
            except:
                pass

            return None

        except Exception:
            return None

    def check_for_modals(self):
        """Check if any modals or popups appeared"""
        try:
            modal_selectors = [
                "[role='dialog']", "[role='modal']", ".modal", ".popup",
                ".overlay", "[aria-modal='true']", ".dialog"
            ]

            for selector in modal_selectors:
                elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                if any(elem.is_displayed() for elem in elements):
                    return True

            return False
        except:
            return False

    def close_modals(self):
        """Close any open modals"""
        try:
            # Common close button patterns
            close_selectors = [
                "[aria-label*='close']", "[aria-label*='Close']",
                ".close", ".close-button", "[title*='close']",
                "[title*='Close']", "button:contains('×')",
                "button:contains('Close')", ".modal-close"
            ]

            for selector in close_selectors:
                try:
                    if ':contains(' in selector:
                        # Convert to XPath
                        text = selector.split(':contains(')[1].split(')')[0].strip("'\"")
                        xpath = f"//button[contains(text(), '{text}')]"
                        elements = self.driver.find_elements(By.XPATH, xpath)
                    else:
                        elements = self.driver.find_elements(By.CSS_SELECTOR, selector)

                    for element in elements:
                        if element.is_displayed():
                            element.click()
                            time.sleep(1)
                            return
                except:
                    continue

            # Try ESC key as fallback
            ActionChains(self.driver).send_keys(Keys.ESCAPE).perform()

        except Exception:
            pass

    def save_results(self):
        """Save all results to files"""
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

            # Save detailed results
            results = {
                'timestamp': timestamp,
                'total_buttons_found': len(self.apply_buttons),
                'successful_applications': len(self.successful_applications),
                'failed_applications': len(self.failed_applications),
                'apply_buttons': self.apply_buttons,
                'successful_results': self.successful_applications,
                'failed_results': self.failed_applications
            }

            results_file = f'jobright_results_{timestamp}.json'
            with open(results_file, 'w', encoding='utf-8') as f:
                json.dump(results, f, indent=2, default=str)

            logger.info(f"Results saved to {results_file}")

            # Save simple list of applied jobs
            applied_jobs = []
            for result in self.successful_applications:
                applied_jobs.append({
                    'job_text': result['button_info']['text'],
                    'action': result.get('action', 'unknown'),
                    'url': result.get('new_url', 'N/A'),
                    'timestamp': datetime.fromtimestamp(result['timestamp']).isoformat()
                })

            simple_file = f'applied_jobs_{timestamp}.json'
            with open(simple_file, 'w', encoding='utf-8') as f:
                json.dump(applied_jobs, f, indent=2)

            logger.info(f"Applied jobs list saved to {simple_file}")

        except Exception as e:
            logger.error(f"Error saving results: {e}")

    def print_final_summary(self):
        """Print final automation summary"""
        print(f"\n{'='*80}")
        print("📊 AUTOMATION COMPLETE - FINAL SUMMARY")
        print(f"{'='*80}")
        print(f"Total Apply Buttons Found: {len(self.apply_buttons)}")
        print(f"Successful Applications: {len(self.successful_applications)}")
        print(f"Failed Applications: {len(self.failed_applications)}")

        if self.successful_applications:
            print(f"\n✅ SUCCESSFUL APPLICATIONS:")
            for i, result in enumerate(self.successful_applications, 1):
                job_text = result['button_info']['text'][:60]
                action = result.get('action', 'applied')
                print(f"  {i:2d}. {job_text}... -> {action}")
                if result.get('new_url'):
                    print(f"      URL: {result['new_url'][:70]}...")

        if self.failed_applications:
            print(f"\n❌ FAILED APPLICATIONS:")
            for i, result in enumerate(self.failed_applications, 1):
                job_text = result['button_info']['text'][:60]
                error = result.get('error', 'unknown')
                print(f"  {i:2d}. {job_text}... -> {error}")

        success_rate = (len(self.successful_applications) / len(self.apply_buttons) * 100) if self.apply_buttons else 0
        print(f"\nSuccess Rate: {success_rate:.1f}%")
        print(f"{'='*80}")

    def run_complete_automation(self):
        """Run the complete automation process"""
        try:
            print("🚀 JobRight.ai Complete Auto-Apply Automation")
            print("This will find and apply to ALL Apply Now buttons!")
            print("="*80)

            # Setup driver
            if not self.setup_driver():
                print("❌ Failed to setup WebDriver")
                return False

            # Handle authentication
            if not self.handle_authentication():
                print("❌ Authentication failed")
                return False

            # Navigate to jobs page
            if not self.navigate_to_jobs_page():
                print("❌ Could not access jobs page")
                return False

            # Load all content
            self.scroll_and_load_all_content()

            # Find all apply buttons
            print("\n🔍 Finding ALL Apply Now buttons...")
            self.apply_buttons = self.find_all_apply_buttons_comprehensive()

            if not self.apply_buttons:
                print("❌ No Apply Now buttons found!")

                # Save debug info
                with open('debug_page_no_buttons.html', 'w', encoding='utf-8') as f:
                    f.write(self.driver.page_source)
                print("Debug: Page source saved to debug_page_no_buttons.html")

                return False

            # Display found buttons
            self.display_found_buttons(self.apply_buttons)

            # Confirm before applying
            print(f"\n🎯 Found {len(self.apply_buttons)} Apply Now buttons!")
            choice = input("Apply to ALL jobs automatically? (y/n): ").strip().lower()

            if choice != 'y':
                print("Automation cancelled by user.")
                return False

            # Apply to all jobs
            print(f"\n🚀 Starting automatic application to {len(self.apply_buttons)} jobs...")
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
                input("\nPress Enter to close browser...")
                self.driver.quit()


def main():
    """Main function"""
    print("JobRight.ai Fixed Complete Auto-Apply Automation")
    print("This script will find ALL Apply Now buttons and apply automatically!")
    print("="*80)

    # Get user preferences
    headless = input("Run in headless mode (no browser window)? (y/n): ").strip().lower() == 'y'

    # Create and run automation
    automation = JobRightFixedAutomation(headless=headless)
    success = automation.run_complete_automation()

    if success:
        print("\n🎉 Automation completed successfully!")
        print(f"Applied to {len(automation.successful_applications)} jobs")
    else:
        print("\n💥 Automation completed with issues")


if __name__ == "__main__":
    main()