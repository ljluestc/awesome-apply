#!/usr/bin/env python3
"""
Enhanced Jobright Apply with Autofill Button Automation Script
This script uses webdriver-manager for automatic Chrome driver management
and provides more robust button detection and clicking.
"""

import time
import json
import logging
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
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class EnhancedJobrightAutofillAutomation:
    def __init__(self, headless=False):
        """Initialize the automation with Chrome WebDriver"""
        self.driver = None
        self.headless = headless
        self.base_url = "https://jobright.ai"
        self.results = []
        
    def setup_driver(self):
        """Setup Chrome WebDriver with automatic driver management"""
        chrome_options = Options()
        if self.headless:
            chrome_options.add_argument("--headless")
        
        # Additional options for better compatibility
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        chrome_options.add_argument("--user-agent=Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
        
        try:
            # Use webdriver-manager to automatically manage Chrome driver
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            
            # Execute script to remove webdriver property
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            
            logger.info("Chrome WebDriver initialized successfully with webdriver-manager")
        except Exception as e:
            logger.error(f"Failed to initialize Chrome WebDriver: {e}")
            raise
    
    def navigate_to_jobright(self):
        """Navigate to the Jobright jobs page with enhanced waiting"""
        try:
            url = f"{self.base_url}/jobs/recommend?pos=16"
            logger.info(f"Navigating to: {url}")
            self.driver.get(url)
            
            # Wait for page to load with multiple conditions
            WebDriverWait(self.driver, 15).until(
                lambda driver: driver.execute_script("return document.readyState") == "complete"
            )
            
            # Additional wait for dynamic content
            time.sleep(5)
            
            # Check if we're on the right page
            current_url = self.driver.current_url
            if "jobright.ai" in current_url:
                logger.info("Successfully navigated to Jobright")
                return True
            else:
                logger.warning(f"Unexpected URL after navigation: {current_url}")
                return False
                
        except Exception as e:
            logger.error(f"Failed to navigate to Jobright: {e}")
            return False
    
    def find_apply_buttons_comprehensive(self):
        """Comprehensive search for apply buttons using multiple strategies"""
        apply_buttons = []
        
        # Strategy 1: Text-based XPath searches
        text_selectors = [
            "//*[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'apply with autofill')]",
            "//*[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'apply') and contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'autofill')]",
            "//button[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'apply')]",
            "//a[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'apply')]",
            "//*[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'quick apply')]",
            "//*[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'one-click apply')]"
        ]
        
        for i, selector in enumerate(text_selectors):
            try:
                elements = self.driver.find_elements(By.XPATH, selector)
                logger.info(f"Text strategy {i+1} found {len(elements)} elements")
                
                for element in elements:
                    if self._is_valid_button(element):
                        button_info = self._extract_button_info(element, f"text_{i+1}")
                        apply_buttons.append(button_info)
                        logger.info(f"Found button: {button_info['text']}")
            except Exception as e:
                logger.warning(f"Text strategy {i+1} failed: {e}")
        
        # Strategy 2: CSS class and attribute searches
        css_selectors = [
            "button[class*='apply']",
            "a[class*='apply']",
            "button[class*='autofill']",
            "a[class*='autofill']",
            "button[class*='quick']",
            "a[class*='quick']",
            "[data-testid*='apply']",
            "[data-testid*='autofill']",
            "[aria-label*='apply']",
            "[aria-label*='autofill']",
            "[title*='apply']",
            "[title*='autofill']",
            "button[type='submit']",
            "input[type='submit']"
        ]
        
        for selector in css_selectors:
            try:
                elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                for element in elements:
                    if self._is_valid_button(element):
                        button_info = self._extract_button_info(element, "css_class")
                        # Only add if it contains apply/autofill related text
                        if any(keyword in button_info['text'].lower() for keyword in ['apply', 'autofill', 'quick', 'submit']):
                            apply_buttons.append(button_info)
                            logger.info(f"Found button via CSS: {button_info['text']}")
            except Exception as e:
                logger.warning(f"CSS selector failed: {e}")
        
        # Strategy 3: Look for job cards and find apply buttons within them
        try:
            job_cards = self.driver.find_elements(By.CSS_SELECTOR, "[class*='job'], [class*='card'], [class*='listing']")
            logger.info(f"Found {len(job_cards)} potential job cards")
            
            for card in job_cards:
                try:
                    # Look for buttons within each job card
                    buttons = card.find_elements(By.TAG_NAME, "button")
                    buttons.extend(card.find_elements(By.TAG_NAME, "a"))
                    
                    for button in buttons:
                        if self._is_valid_button(button):
                            button_info = self._extract_button_info(button, "job_card")
                            if any(keyword in button_info['text'].lower() for keyword in ['apply', 'autofill', 'quick']):
                                apply_buttons.append(button_info)
                                logger.info(f"Found button in job card: {button_info['text']}")
                except Exception as e:
                    logger.warning(f"Error processing job card: {e}")
                    continue
        except Exception as e:
            logger.warning(f"Job card strategy failed: {e}")
        
        # Remove duplicates based on text and location
        unique_buttons = []
        seen = set()
        for button in apply_buttons:
            key = (button['text'], button['location']['x'], button['location']['y'])
            if key not in seen:
                seen.add(key)
                unique_buttons.append(button)
        
        logger.info(f"Found {len(unique_buttons)} unique apply buttons")
        return unique_buttons
    
    def _is_valid_button(self, element):
        """Check if element is a valid clickable button"""
        try:
            return (element.is_displayed() and 
                    element.is_enabled() and 
                    element.tag_name.lower() in ['button', 'a', 'input', 'div', 'span'])
        except:
            return False
    
    def _extract_button_info(self, element, strategy):
        """Extract comprehensive information about a button"""
        try:
            return {
                'strategy': strategy,
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
                'is_enabled': element.is_enabled(),
                'parent_info': self._get_parent_info(element)
            }
        except Exception as e:
            logger.warning(f"Error extracting button info: {e}")
            return {
                'strategy': strategy,
                'tag': 'unknown',
                'text': 'unknown',
                'classes': [],
                'id': '',
                'href': '',
                'onclick': '',
                'data_attributes': {},
                'location': {'x': 0, 'y': 0},
                'size': {'width': 0, 'height': 0},
                'is_displayed': False,
                'is_enabled': False,
                'parent_info': {}
            }
    
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
    
    def _get_parent_info(self, element):
        """Get information about the parent element"""
        try:
            parent = element.find_element(By.XPATH, "..")
            return {
                'tag': parent.tag_name,
                'class': parent.get_attribute('class') or '',
                'id': parent.get_attribute('id') or '',
                'text': parent.text[:100] + '...' if len(parent.text) > 100 else parent.text
            }
        except:
            return {}
    
    def click_apply_button_enhanced(self, button_info):
        """Enhanced button clicking with multiple fallback methods"""
        try:
            # Find the element using multiple strategies
            element = None
            
            # Try to find by text first
            if button_info['text']:
                try:
                    xpath = f"//{button_info['tag']}[contains(text(), '{button_info['text']}')]"
                    element = self.driver.find_element(By.XPATH, xpath)
                except:
                    pass
            
            # Try to find by ID
            if not element and button_info['id']:
                try:
                    element = self.driver.find_element(By.ID, button_info['id'])
                except:
                    pass
            
            # Try to find by class
            if not element and button_info['classes']:
                try:
                    class_selector = f"{button_info['tag']}.{'.'.join(button_info['classes'])}"
                    element = self.driver.find_element(By.CSS_SELECTOR, class_selector)
                except:
                    pass
            
            if not element:
                logger.warning(f"Could not relocate button: {button_info['text']}")
                return {
                    'button_info': button_info,
                    'new_url': None,
                    'success': False,
                    'error': 'Could not relocate button',
                    'timestamp': time.time()
                }
            
            # Get current window handles
            original_windows = self.driver.window_handles
            
            # Scroll to element
            self.driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", element)
            time.sleep(1)
            
            # Try multiple click methods
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
                    # Method 3: ActionChains click
                    try:
                        ActionChains(self.driver).move_to_element(element).click().perform()
                        click_success = True
                        logger.info(f"Successfully clicked button via ActionChains: {button_info['text']}")
                    except Exception as e2:
                        logger.warning(f"All click methods failed: {e}, {e2}")
            
            if click_success:
                # Wait for navigation
                time.sleep(3)
                new_windows = self.driver.window_handles
                
                if len(new_windows) > len(original_windows):
                    # New tab/window opened
                    new_window = [w for w in new_windows if w not in original_windows][0]
                    self.driver.switch_to.window(new_window)
                    
                    current_url = self.driver.current_url
                    logger.info(f"New page opened: {current_url}")
                    
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
            apply_buttons = self.find_apply_buttons_comprehensive()
            
            if not apply_buttons:
                logger.warning("No apply buttons found")
                # Save page source for debugging
                with open('/home/calelin/awesome-apply/debug_page_source_enhanced.html', 'w', encoding='utf-8') as f:
                    f.write(self.driver.page_source)
                logger.info("Page source saved to debug_page_source_enhanced.html for analysis")
                
                # Also save a screenshot
                try:
                    self.driver.save_screenshot('/home/calelin/awesome-apply/debug_screenshot.png')
                    logger.info("Screenshot saved to debug_screenshot.png")
                except Exception as e:
                    logger.warning(f"Could not save screenshot: {e}")
                
                return False
            
            logger.info(f"Found {len(apply_buttons)} apply buttons")
            
            # Click each button and track results
            for i, button_info in enumerate(apply_buttons):
                logger.info(f"Clicking button {i+1}/{len(apply_buttons)}: {button_info['text']}")
                result = self.click_apply_button_enhanced(button_info)
                self.results.append(result)
                
                # Wait between clicks
                time.sleep(3)
            
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
            with open('/home/calelin/awesome-apply/apply_autofill_results_enhanced.json', 'w', encoding='utf-8') as f:
                json.dump(self.results, f, indent=2, default=str)
            logger.info("Results saved to apply_autofill_results_enhanced.json")
        except Exception as e:
            logger.error(f"Failed to save results: {e}")

def main():
    """Main function"""
    print("Enhanced Jobright Apply with Autofill Automation")
    print("=" * 60)
    
    # Run automation (set headless=False to see browser)
    automation = EnhancedJobrightAutofillAutomation(headless=False)
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
        print("Debug files created:")
        print("- debug_page_source_enhanced.html")
        print("- debug_screenshot.png")

if __name__ == "__main__":
    main()
