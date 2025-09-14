#!/usr/bin/env python3
"""
Jobright Apply with Autofill Button Automation Script
This script navigates to Jobright.ai, finds all "Apply with autofill" buttons,
and clicks them to open new pages in the browser.
"""

import time
import json
import logging
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import TimeoutException, NoSuchElementException, ElementClickInterceptedException
from urllib.parse import urljoin, urlparse
import requests

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class JobrightAutofillAutomation:
    def __init__(self, headless=False):
        """Initialize the automation with Chrome WebDriver"""
        self.driver = None
        self.headless = headless
        self.base_url = "https://jobright.ai"
        self.results = []
        
    def setup_driver(self):
        """Setup Chrome WebDriver with appropriate options"""
        chrome_options = Options()
        if self.headless:
            chrome_options.add_argument("--headless")
        
        # Additional options for better compatibility
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("--user-agent=Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
        
        try:
            self.driver = webdriver.Chrome(options=chrome_options)
            logger.info("Chrome WebDriver initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Chrome WebDriver: {e}")
            raise
    
    def navigate_to_jobright(self):
        """Navigate to the Jobright jobs page"""
        try:
            url = f"{self.base_url}/jobs/recommend?pos=16"
            logger.info(f"Navigating to: {url}")
            self.driver.get(url)
            
            # Wait for page to load
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            # Additional wait for dynamic content
            time.sleep(3)
            logger.info("Successfully navigated to Jobright")
            return True
            
        except Exception as e:
            logger.error(f"Failed to navigate to Jobright: {e}")
            return False
    
    def find_apply_buttons(self):
        """Find all possible 'Apply with autofill' buttons using multiple strategies"""
        apply_buttons = []
        
        # Strategy 1: Look for buttons with text containing "apply" and "autofill"
        selectors = [
            "//button[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'apply') and contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'autofill')]",
            "//a[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'apply') and contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'autofill')]",
            "//*[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'apply with autofill')]",
            "//*[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'autofill') and contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'apply')]"
        ]
        
        for i, selector in enumerate(selectors):
            try:
                elements = self.driver.find_elements(By.XPATH, selector)
                logger.info(f"Strategy {i+1} found {len(elements)} elements")
                
                for element in elements:
                    try:
                        if element.is_displayed() and element.is_enabled():
                            button_info = {
                                'strategy': i+1,
                                'tag': element.tag_name,
                                'text': element.text.strip(),
                                'classes': element.get_attribute('class').split() if element.get_attribute('class') else [],
                                'id': element.get_attribute('id') or '',
                                'href': element.get_attribute('href') or '',
                                'onclick': element.get_attribute('onclick') or '',
                                'data_attributes': self._get_data_attributes(element),
                                'location': element.location,
                                'size': element.size,
                                'is_displayed': element.is_displayed(),
                                'is_enabled': element.is_enabled()
                            }
                            apply_buttons.append(button_info)
                            logger.info(f"Found button: {button_info['text']}")
                    except Exception as e:
                        logger.warning(f"Error processing element: {e}")
                        continue
                        
            except Exception as e:
                logger.warning(f"Strategy {i+1} failed: {e}")
                continue
        
        # Strategy 2: Look for common button classes and attributes
        class_selectors = [
            "button[class*='apply']",
            "a[class*='apply']",
            "button[class*='autofill']",
            "a[class*='autofill']",
            "[data-testid*='apply']",
            "[data-testid*='autofill']",
            "[aria-label*='apply']",
            "[aria-label*='autofill']"
        ]
        
        for selector in class_selectors:
            try:
                elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                for element in elements:
                    if element.is_displayed() and element.is_enabled():
                        text = element.text.strip().lower()
                        if 'apply' in text and 'autofill' in text:
                            button_info = {
                                'strategy': 'class_based',
                                'tag': element.tag_name,
                                'text': element.text.strip(),
                                'classes': element.get_attribute('class').split() if element.get_attribute('class') else [],
                                'id': element.get_attribute('id') or '',
                                'href': element.get_attribute('href') or '',
                                'onclick': element.get_attribute('onclick') or '',
                                'data_attributes': self._get_data_attributes(element),
                                'location': element.location,
                                'size': element.size,
                                'is_displayed': element.is_displayed(),
                                'is_enabled': element.is_enabled()
                            }
                            apply_buttons.append(button_info)
                            logger.info(f"Found button via class: {button_info['text']}")
            except Exception as e:
                logger.warning(f"Class selector failed: {e}")
                continue
        
        return apply_buttons
    
    def _get_data_attributes(self, element):
        """Extract data attributes from an element"""
        data_attrs = {}
        try:
            attributes = self.driver.execute_script(
                "var items = {}; "
                "for (index = 0; index < arguments[0].attributes.length; ++index) { "
                "items[arguments[0].attributes[index].name] = arguments[0].attributes[index].value "
                "}; "
                "return items;", element
            )
            data_attrs = {k: v for k, v in attributes.items() if k.startswith('data-')}
        except Exception as e:
            logger.warning(f"Could not extract data attributes: {e}")
        return data_attrs
    
    def click_apply_button(self, button_info):
        """Click an apply button and handle the new page/tab"""
        try:
            # Find the element again to ensure it's still available
            selector = f"//{button_info['tag']}[contains(text(), '{button_info['text']}')]"
            element = self.driver.find_element(By.XPATH, selector)
            
            # Get current window handles
            original_windows = self.driver.window_handles
            
            # Scroll to element if needed
            self.driver.execute_script("arguments[0].scrollIntoView(true);", element)
            time.sleep(1)
            
            # Try different click methods
            click_success = False
            
            # Method 1: Direct click
            try:
                element.click()
                click_success = True
                logger.info(f"Successfully clicked button: {button_info['text']}")
            except ElementClickInterceptedException:
                # Method 2: JavaScript click
                try:
                    self.driver.execute_script("arguments[0].click();", element)
                    click_success = True
                    logger.info(f"Successfully clicked button via JS: {button_info['text']}")
                except Exception as e:
                    logger.warning(f"JavaScript click failed: {e}")
            
            if click_success:
                # Wait for new window/tab to open
                time.sleep(2)
                new_windows = self.driver.window_handles
                
                if len(new_windows) > len(original_windows):
                    # New tab/window opened
                    new_window = [w for w in new_windows if w not in original_windows][0]
                    self.driver.switch_to.window(new_window)
                    
                    current_url = self.driver.current_url
                    logger.info(f"New page opened: {current_url}")
                    
                    # Store result
                    result = {
                        'button_info': button_info,
                        'new_url': current_url,
                        'success': True,
                        'timestamp': time.time()
                    }
                    
                    # Close the new tab and return to original
                    self.driver.close()
                    self.driver.switch_to.window(original_windows[0])
                    
                    return result
                else:
                    # Check if URL changed (same tab navigation)
                    current_url = self.driver.current_url
                    if current_url != f"{self.base_url}/jobs/recommend?pos=16":
                        logger.info(f"Navigated to new page: {current_url}")
                        result = {
                            'button_info': button_info,
                            'new_url': current_url,
                            'success': True,
                            'timestamp': time.time()
                        }
                        
                        # Navigate back
                        self.driver.back()
                        time.sleep(2)
                        return result
                    else:
                        logger.warning("No new page opened after click")
                        return {
                            'button_info': button_info,
                            'new_url': None,
                            'success': False,
                            'error': 'No new page opened',
                            'timestamp': time.time()
                        }
            else:
                return {
                    'button_info': button_info,
                    'new_url': None,
                    'success': False,
                    'error': 'Click failed',
                    'timestamp': time.time()
                }
                
        except Exception as e:
            logger.error(f"Error clicking button: {e}")
            return {
                'button_info': button_info,
                'new_url': None,
                'success': False,
                'error': str(e),
                'timestamp': time.time()
            }
    
    def run_automation(self):
        """Main automation process"""
        try:
            # Setup driver
            self.setup_driver()
            
            # Navigate to Jobright
            if not self.navigate_to_jobright():
                return False
            
            # Find all apply buttons
            logger.info("Searching for 'Apply with autofill' buttons...")
            apply_buttons = self.find_apply_buttons()
            
            if not apply_buttons:
                logger.warning("No 'Apply with autofill' buttons found")
                # Save page source for debugging
                with open('/home/calelin/awesome-apply/debug_page_source.html', 'w', encoding='utf-8') as f:
                    f.write(self.driver.page_source)
                logger.info("Page source saved to debug_page_source.html for analysis")
                return False
            
            logger.info(f"Found {len(apply_buttons)} apply buttons")
            
            # Click each button and track results
            for i, button_info in enumerate(apply_buttons):
                logger.info(f"Clicking button {i+1}/{len(apply_buttons)}: {button_info['text']}")
                result = self.click_apply_button(button_info)
                self.results.append(result)
                
                # Wait between clicks
                time.sleep(2)
            
            # Save results
            self.save_results()
            return True
            
        except Exception as e:
            logger.error(f"Automation failed: {e}")
            return False
        finally:
            if self.driver:
                self.driver.quit()
    
    def save_results(self):
        """Save results to JSON file"""
        try:
            with open('/home/calelin/awesome-apply/apply_autofill_results.json', 'w', encoding='utf-8') as f:
                json.dump(self.results, f, indent=2, default=str)
            logger.info("Results saved to apply_autofill_results.json")
        except Exception as e:
            logger.error(f"Failed to save results: {e}")

def main():
    """Main function"""
    print("Jobright Apply with Autofill Automation")
    print("=" * 50)
    
    # Run automation (set headless=False to see browser)
    automation = JobrightAutofillAutomation(headless=False)
    success = automation.run_automation()
    
    if success:
        print("\n✅ Automation completed successfully!")
        print(f"Found and processed {len(automation.results)} apply buttons")
        
        # Print summary
        successful_clicks = sum(1 for r in automation.results if r.get('success', False))
        print(f"Successfully opened {successful_clicks} new pages")
        
        for i, result in enumerate(automation.results):
            status = "✅" if result.get('success', False) else "❌"
            print(f"{status} Button {i+1}: {result['button_info']['text']}")
            if result.get('new_url'):
                print(f"   → Opened: {result['new_url']}")
    else:
        print("\n❌ Automation failed. Check the logs for details.")

if __name__ == "__main__":
    main()
