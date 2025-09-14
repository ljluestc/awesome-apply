#!/usr/bin/env python3
"""
Complete JobRight.ai Auto-Apply Automation Script
This script finds ALL "Apply Now" buttons and automatically applies to all jobs
with comprehensive error handling and logging.
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
from selenium.common.exceptions import TimeoutException, NoSuchElementException, ElementClickInterceptedException
from webdriver_manager.chrome import ChromeDriverManager
from urllib.parse import urljoin, urlparse
import requests

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/tmp/jobright_automation.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class JobRightCompleteAutomation:
    def __init__(self, headless=False, auto_apply=False):
        """Initialize the automation with Chrome WebDriver"""
        self.driver = None
        self.headless = headless
        self.auto_apply = auto_apply
        self.base_url = "https://jobright.ai"
        self.apply_buttons = []
        self.applied_jobs = []
        self.failed_applications = []
        self.session_stats = {
            'total_buttons_found': 0,
            'successful_applications': 0,
            'failed_applications': 0,
            'start_time': None,
            'end_time': None
        }

    def setup_driver(self):
        """Setup Chrome WebDriver with comprehensive options"""
        chrome_options = Options()

        if self.headless:
            chrome_options.add_argument("--headless")

        # Essential Chrome options for automation
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("--start-maximized")

        # Anti-detection options
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        chrome_options.add_argument("--user-agent=Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")

        # Privacy and security options
        chrome_options.add_argument("--disable-web-security")
        chrome_options.add_argument("--allow-running-insecure-content")
        chrome_options.add_argument("--disable-extensions")

        try:
            # Use webdriver-manager for automatic driver management
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=chrome_options)

            # Execute script to remove webdriver property
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

            # Set implicit wait
            self.driver.implicitly_wait(10)

            logger.info("Chrome WebDriver initialized successfully")
            return True

        except Exception as e:
            logger.error(f"Failed to initialize Chrome WebDriver: {e}")
            return False

    def navigate_to_jobright(self, page_num=1):
        """Navigate to JobRight jobs page"""
        try:
            url = f"{self.base_url}/jobs/recommend?pos={page_num}"
            logger.info(f"Navigating to: {url}")
            self.driver.get(url)

            # Wait for page load with multiple checks
            WebDriverWait(self.driver, 20).until(
                lambda driver: driver.execute_script("return document.readyState") == "complete"
            )

            # Additional wait for dynamic content
            time.sleep(5)

            # Scroll to load all content
            self.scroll_page_fully()

            current_url = self.driver.current_url
            if "jobright.ai" in current_url:
                logger.info(f"Successfully loaded page: {current_url}")
                return True
            else:
                logger.warning(f"Unexpected URL: {current_url}")
                return False

        except Exception as e:
            logger.error(f"Failed to navigate to JobRight: {e}")
            return False

    def scroll_page_fully(self):
        """Scroll through the entire page to load all dynamic content"""
        try:
            # Get initial page height
            last_height = self.driver.execute_script("return document.body.scrollHeight")

            scroll_attempts = 0
            max_scrolls = 10

            while scroll_attempts < max_scrolls:
                # Scroll down
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")

                # Wait for new content to load
                time.sleep(3)

                # Calculate new scroll height
                new_height = self.driver.execute_script("return document.body.scrollHeight")

                if new_height == last_height:
                    # No new content loaded, try a few more times
                    scroll_attempts += 1
                else:
                    # New content loaded, reset counter
                    last_height = new_height
                    scroll_attempts = 0

            # Scroll back to top
            self.driver.execute_script("window.scrollTo(0, 0);")
            time.sleep(2)

            logger.info("Page scrolling completed")

        except Exception as e:
            logger.warning(f"Error during page scrolling: {e}")

    def find_all_apply_buttons(self):
        """Find ALL apply buttons on the page using comprehensive search strategies"""
        apply_buttons = []

        # Define comprehensive search patterns
        apply_text_patterns = [
            "apply now", "apply with autofill", "apply", "quick apply",
            "easy apply", "one-click apply", "instant apply", "apply for this job",
            "submit application", "apply for position", "apply today",
            "autofill", "auto-fill", "auto fill"
        ]

        apply_class_patterns = [
            "apply", "autofill", "quick-apply", "job-apply", "btn-apply",
            "apply-button", "apply-btn", "application-btn"
        ]

        # Strategy 1: Search by text content
        logger.info("Searching for apply buttons by text content...")
        for pattern in apply_text_patterns:
            try:
                # Case-insensitive XPath search
                xpath = f"//*[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), '{pattern.lower()}')]"
                elements = self.driver.find_elements(By.XPATH, xpath)

                for element in elements:
                    if self.is_valid_apply_button(element):
                        button_info = self.extract_button_info(element, f"text_{pattern}")
                        if button_info and button_info not in apply_buttons:
                            apply_buttons.append(button_info)
                            logger.info(f"Found apply button by text '{pattern}': {button_info['text'][:50]}...")

            except Exception as e:
                logger.warning(f"Error searching for pattern '{pattern}': {e}")
                continue

        # Strategy 2: Search by class names
        logger.info("Searching for apply buttons by class names...")
        for pattern in apply_class_patterns:
            try:
                elements = self.driver.find_elements(By.CSS_SELECTOR, f"[class*='{pattern}']")

                for element in elements:
                    if self.is_valid_apply_button(element):
                        button_info = self.extract_button_info(element, f"class_{pattern}")
                        if button_info and button_info not in apply_buttons:
                            apply_buttons.append(button_info)
                            logger.info(f"Found apply button by class '{pattern}': {button_info['text'][:50]}...")

            except Exception as e:
                logger.warning(f"Error searching for class '{pattern}': {e}")
                continue

        # Strategy 3: Search all clickable elements and filter
        logger.info("Searching all clickable elements...")
        clickable_selectors = ["button", "a", "div[role='button']", "[onclick]"]

        for selector in clickable_selectors:
            try:
                elements = self.driver.find_elements(By.CSS_SELECTOR, selector)

                for element in elements:
                    if self.is_valid_apply_button(element):
                        element_text = element.text.strip().lower()

                        # Check if text contains apply-related keywords
                        if any(pattern in element_text for pattern in apply_text_patterns):
                            button_info = self.extract_button_info(element, f"clickable_{selector}")
                            if button_info and button_info not in apply_buttons:
                                apply_buttons.append(button_info)
                                logger.info(f"Found apply button in clickables: {button_info['text'][:50]}...")

            except Exception as e:
                logger.warning(f"Error searching clickable selector '{selector}': {e}")
                continue

        # Remove duplicates based on text and position
        unique_buttons = self.remove_duplicate_buttons(apply_buttons)

        logger.info(f"Total unique apply buttons found: {len(unique_buttons)}")
        return unique_buttons

    def is_valid_apply_button(self, element):
        """Check if element is a valid apply button"""
        try:
            # Must be displayed and enabled
            if not (element.is_displayed() and element.is_enabled()):
                return False

            # Must have text or be clickable
            text = element.text.strip()
            tag = element.tag_name.lower()

            if not text and tag not in ['button', 'a', 'input']:
                return False

            # Check for minimum size (avoid tiny elements)
            size = element.size
            if size['width'] < 50 or size['height'] < 20:
                return False

            return True

        except Exception:
            return False

    def extract_button_info(self, element, detection_method):
        """Extract comprehensive information about the button"""
        try:
            return {
                'element_id': id(element),
                'text': element.text.strip(),
                'tag': element.tag_name,
                'classes': element.get_attribute('class') or '',
                'id': element.get_attribute('id') or '',
                'href': element.get_attribute('href') or '',
                'onclick': element.get_attribute('onclick') or '',
                'location': element.location,
                'size': element.size,
                'detection_method': detection_method,
                'xpath': self.get_element_xpath(element),
                'timestamp_found': time.time()
            }
        except Exception as e:
            logger.warning(f"Error extracting button info: {e}")
            return None

    def get_element_xpath(self, element):
        """Get XPath of an element"""
        try:
            return self.driver.execute_script("""
                function getPathTo(element) {
                    if (element === document.body)
                        return element.tagName;

                    var ix = 0;
                    var siblings = element.parentNode.childNodes;
                    for (var i = 0; i < siblings.length; i++) {
                        var sibling = siblings[i];
                        if (sibling === element)
                            return getPathTo(element.parentNode) + '/' + element.tagName + '[' + (ix + 1) + ']';
                        if (sibling.nodeType === 1 && sibling.tagName === element.tagName)
                            ix++;
                    }
                }
                return getPathTo(arguments[0]).toLowerCase();
            """, element)
        except:
            return "unknown"

    def remove_duplicate_buttons(self, buttons):
        """Remove duplicate buttons based on text and position"""
        unique_buttons = []
        seen = set()

        for button in buttons:
            # Create unique key based on text and position
            key = (
                button['text'].lower().strip(),
                button['location']['x'],
                button['location']['y']
            )

            if key not in seen:
                seen.add(key)
                unique_buttons.append(button)

        return unique_buttons

    def display_found_buttons(self, buttons):
        """Display all found buttons to the user"""
        print(f"\n{'='*80}")
        print(f"🎯 FOUND {len(buttons)} APPLY NOW BUTTONS")
        print(f"{'='*80}")

        for i, button in enumerate(buttons, 1):
            print(f"\n{i:2d}. Button Text: '{button['text'][:80]}{'...' if len(button['text']) > 80 else ''}'")
            print(f"    Detection: {button['detection_method']}")
            print(f"    Tag: {button['tag']} | Classes: {button['classes'][:50]}")
            print(f"    Position: ({button['location']['x']}, {button['location']['y']})")
            if button['href']:
                print(f"    Link: {button['href'][:80]}...")

        print(f"\n{'='*80}")

    def click_apply_button(self, button_info, index, total):
        """Click an apply button with comprehensive error handling"""
        logger.info(f"Attempting to click button {index}/{total}: {button_info['text'][:50]}...")

        try:
            # Find the element using multiple strategies
            element = self.relocate_element(button_info)

            if not element:
                error_msg = "Could not relocate element"
                logger.warning(f"Button {index}: {error_msg}")
                return {
                    'button_info': button_info,
                    'success': False,
                    'error': error_msg,
                    'timestamp': time.time()
                }

            # Scroll to element and wait
            self.driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", element)
            time.sleep(2)

            # Get current state
            original_url = self.driver.current_url
            original_windows = self.driver.window_handles

            # Try multiple click strategies
            click_result = self.perform_click(element, button_info)

            if click_result['clicked']:
                # Wait for navigation/modal
                time.sleep(3)

                # Check for new windows/tabs
                new_windows = self.driver.window_handles
                if len(new_windows) > len(original_windows):
                    new_window = [w for w in new_windows if w not in original_windows][0]
                    self.driver.switch_to.window(new_window)
                    new_url = self.driver.current_url

                    logger.info(f"Button {index}: New window opened - {new_url}")

                    # Close new tab and return to main
                    self.driver.close()
                    self.driver.switch_to.window(original_windows[0])

                    return {
                        'button_info': button_info,
                        'success': True,
                        'action': 'new_window',
                        'target_url': new_url,
                        'timestamp': time.time()
                    }

                # Check for URL change
                elif self.driver.current_url != original_url:
                    new_url = self.driver.current_url
                    logger.info(f"Button {index}: Page navigation - {new_url}")

                    # Go back to main page
                    self.driver.back()
                    time.sleep(2)

                    return {
                        'button_info': button_info,
                        'success': True,
                        'action': 'navigation',
                        'target_url': new_url,
                        'timestamp': time.time()
                    }

                # Check for modal/popup
                else:
                    # Look for any modal or popup that might have appeared
                    modal_found = self.check_for_modal()
                    if modal_found:
                        logger.info(f"Button {index}: Modal/popup appeared")
                        return {
                            'button_info': button_info,
                            'success': True,
                            'action': 'modal',
                            'timestamp': time.time()
                        }
                    else:
                        logger.warning(f"Button {index}: Click successful but no visible change detected")
                        return {
                            'button_info': button_info,
                            'success': True,
                            'action': 'click_only',
                            'timestamp': time.time()
                        }
            else:
                return {
                    'button_info': button_info,
                    'success': False,
                    'error': click_result['error'],
                    'timestamp': time.time()
                }

        except Exception as e:
            error_msg = f"Unexpected error: {str(e)}"
            logger.error(f"Button {index}: {error_msg}")
            return {
                'button_info': button_info,
                'success': False,
                'error': error_msg,
                'timestamp': time.time()
            }

    def relocate_element(self, button_info):
        """Relocate an element using multiple strategies"""
        # Strategy 1: By XPath
        if button_info.get('xpath'):
            try:
                element = self.driver.find_element(By.XPATH, button_info['xpath'])
                if element.is_displayed():
                    return element
            except:
                pass

        # Strategy 2: By ID
        if button_info.get('id'):
            try:
                element = self.driver.find_element(By.ID, button_info['id'])
                if element.is_displayed():
                    return element
            except:
                pass

        # Strategy 3: By text and position
        try:
            text = button_info['text']
            expected_location = button_info['location']

            # Find all elements with matching text
            xpath = f"//*[contains(text(), '{text[:20]}')]"
            elements = self.driver.find_elements(By.XPATH, xpath)

            # Find the one closest to original position
            for element in elements:
                if element.is_displayed():
                    current_location = element.location
                    distance = abs(current_location['x'] - expected_location['x']) + abs(current_location['y'] - expected_location['y'])
                    if distance < 50:  # Within 50 pixels
                        return element

        except:
            pass

        return None

    def perform_click(self, element, button_info):
        """Perform click using multiple methods"""
        # Method 1: Standard click
        try:
            element.click()
            return {'clicked': True, 'method': 'standard'}
        except ElementClickInterceptedException:
            pass
        except Exception as e:
            logger.warning(f"Standard click failed: {e}")

        # Method 2: JavaScript click
        try:
            self.driver.execute_script("arguments[0].click();", element)
            return {'clicked': True, 'method': 'javascript'}
        except Exception as e:
            logger.warning(f"JavaScript click failed: {e}")

        # Method 3: ActionChains click
        try:
            ActionChains(self.driver).move_to_element(element).click().perform()
            return {'clicked': True, 'method': 'action_chains'}
        except Exception as e:
            logger.warning(f"ActionChains click failed: {e}")

        # Method 4: Force click (remove overlays first)
        try:
            # Remove potential overlays
            self.driver.execute_script("""
                var overlays = document.querySelectorAll('[style*="position: fixed"], [style*="position: absolute"]');
                for(var i = 0; i < overlays.length; i++) {
                    if(overlays[i].style.zIndex > 1000) {
                        overlays[i].style.display = 'none';
                    }
                }
            """)

            time.sleep(1)
            element.click()
            return {'clicked': True, 'method': 'force_click'}
        except Exception as e:
            logger.error(f"Force click failed: {e}")

        return {'clicked': False, 'error': 'All click methods failed'}

    def check_for_modal(self):
        """Check if a modal or popup appeared after clicking"""
        try:
            # Look for common modal indicators
            modal_selectors = [
                "[role='dialog']",
                "[role='modal']",
                ".modal",
                ".popup",
                ".overlay",
                "[aria-modal='true']"
            ]

            for selector in modal_selectors:
                elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                if any(elem.is_displayed() for elem in elements):
                    return True

            return False

        except:
            return False

    def save_session_results(self):
        """Save complete session results to file"""
        try:
            results = {
                'session_stats': self.session_stats,
                'apply_buttons_found': self.apply_buttons,
                'successful_applications': self.applied_jobs,
                'failed_applications': self.failed_applications,
                'timestamp': datetime.now().isoformat()
            }

            filename = f"jobright_session_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            filepath = os.path.join('/home/calelin/awesome-apply', filename)

            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(results, f, indent=2, default=str)

            logger.info(f"Session results saved to: {filename}")

        except Exception as e:
            logger.error(f"Failed to save session results: {e}")

    def print_session_summary(self):
        """Print comprehensive session summary"""
        print(f"\n{'='*80}")
        print("📊 AUTOMATION SESSION SUMMARY")
        print(f"{'='*80}")
        print(f"Start Time: {datetime.fromtimestamp(self.session_stats['start_time']).strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"End Time: {datetime.fromtimestamp(self.session_stats['end_time']).strftime('%Y-%m-%d %H:%M:%S')}")
        duration = self.session_stats['end_time'] - self.session_stats['start_time']
        print(f"Duration: {duration:.1f} seconds")
        print(f"\nButtons Found: {self.session_stats['total_buttons_found']}")
        print(f"Successful Applications: {self.session_stats['successful_applications']}")
        print(f"Failed Applications: {self.session_stats['failed_applications']}")

        if self.session_stats['successful_applications'] > 0:
            print(f"\n✅ SUCCESSFUL APPLICATIONS:")
            for i, app in enumerate(self.applied_jobs, 1):
                print(f"  {i}. {app['button_info']['text'][:60]}... -> {app.get('action', 'unknown')}")

        if self.session_stats['failed_applications'] > 0:
            print(f"\n❌ FAILED APPLICATIONS:")
            for i, app in enumerate(self.failed_applications, 1):
                print(f"  {i}. {app['button_info']['text'][:60]}... -> {app.get('error', 'unknown error')}")

        print(f"{'='*80}")

    def run_complete_automation(self):
        """Run the complete automation process"""
        self.session_stats['start_time'] = time.time()

        try:
            print("🚀 JobRight.ai Complete Auto-Apply Automation Starting...")
            print("="*80)

            # Setup WebDriver
            if not self.setup_driver():
                print("❌ Failed to setup WebDriver")
                return False

            # Navigate to JobRight
            if not self.navigate_to_jobright():
                print("❌ Failed to navigate to JobRight")
                return False

            # Find all apply buttons
            print("🔍 Searching for all Apply Now buttons...")
            self.apply_buttons = self.find_all_apply_buttons()
            self.session_stats['total_buttons_found'] = len(self.apply_buttons)

            if not self.apply_buttons:
                print("❌ No apply buttons found!")

                # Save debug info
                debug_file = '/home/calelin/awesome-apply/debug_no_buttons.html'
                with open(debug_file, 'w', encoding='utf-8') as f:
                    f.write(self.driver.page_source)
                print(f"Debug: Page source saved to {debug_file}")

                try:
                    self.driver.save_screenshot('/home/calelin/awesome-apply/debug_screenshot.png')
                    print("Debug: Screenshot saved to debug_screenshot.png")
                except:
                    pass

                return False

            # Display found buttons
            self.display_found_buttons(self.apply_buttons)

            # Ask user for confirmation unless auto_apply is True
            if not self.auto_apply:
                print(f"\nFound {len(self.apply_buttons)} apply buttons.")
                choice = input("Do you want to apply to ALL jobs? (y/n): ").strip().lower()
                if choice != 'y':
                    print("Automation cancelled by user.")
                    return False

            # Apply to all jobs
            print(f"\n🎯 Starting automatic application to {len(self.apply_buttons)} jobs...")

            for i, button_info in enumerate(self.apply_buttons, 1):
                print(f"\n[{i}/{len(self.apply_buttons)}] Applying to: {button_info['text'][:60]}...")

                result = self.click_apply_button(button_info, i, len(self.apply_buttons))

                if result['success']:
                    self.applied_jobs.append(result)
                    self.session_stats['successful_applications'] += 1
                    print(f"✅ SUCCESS: {result.get('action', 'applied')}")
                else:
                    self.failed_applications.append(result)
                    self.session_stats['failed_applications'] += 1
                    print(f"❌ FAILED: {result.get('error', 'unknown error')}")

                # Wait between applications
                time.sleep(2)

            return True

        except Exception as e:
            logger.error(f"Automation failed with error: {e}")
            print(f"❌ Automation failed: {e}")
            return False

        finally:
            self.session_stats['end_time'] = time.time()

            # Save results and print summary
            self.save_session_results()
            self.print_session_summary()

            # Close browser
            if self.driver:
                self.driver.quit()


def main():
    """Main function to run the automation"""
    print("JobRight.ai Complete Auto-Apply Automation")
    print("This script will find ALL 'Apply Now' buttons and automatically apply!")
    print("="*80)

    # Configuration
    headless_mode = input("Run in headless mode (no browser window)? (y/n): ").strip().lower() == 'y'
    auto_apply_mode = input("Automatically apply to ALL jobs without asking? (y/n): ").strip().lower() == 'y'

    if auto_apply_mode:
        print("⚠️  WARNING: Auto-apply mode enabled! Will apply to ALL found jobs automatically!")
        confirm = input("Are you sure? Type 'YES' to continue: ").strip()
        if confirm != 'YES':
            print("Automation cancelled.")
            return

    # Run automation
    automation = JobRightCompleteAutomation(headless=headless_mode, auto_apply=auto_apply_mode)
    success = automation.run_complete_automation()

    if success:
        print("\n🎉 Automation completed successfully!")
    else:
        print("\n💥 Automation completed with issues. Check logs for details.")

if __name__ == "__main__":
    main()