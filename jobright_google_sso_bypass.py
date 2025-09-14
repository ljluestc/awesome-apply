#!/usr/bin/env python3
"""
JobRight.ai Google SSO Bypass Script
This script uses your existing Chrome profile to bypass Google SSO authentication
"""

import time
import logging
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import os

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class JobRightGoogleSSOBypass:
    def __init__(self):
        self.driver = None
        self.base_url = "https://jobright.ai"

    def setup_driver_with_google_profile(self):
        """Setup Chrome with existing Google profile"""
        chrome_options = Options()
        
        # Get Chrome profile path
        home_dir = os.path.expanduser("~")
        chrome_profile_path = os.path.join(home_dir, ".config/google-chrome")
        
        # Check if profile exists
        if not os.path.exists(chrome_profile_path):
            logger.error(f"Chrome profile not found at: {chrome_profile_path}")
            return False
        
        # Configure Chrome options for profile usage
        chrome_options.add_argument(f"--user-data-dir={chrome_profile_path}")
        chrome_options.add_argument("--profile-directory=Default")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("--start-maximized")
        
        # Anti-detection
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        
        try:
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            self.driver.implicitly_wait(10)
            
            logger.info("Chrome WebDriver initialized with Google profile")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize Chrome WebDriver: {e}")
            return False

    def test_google_signin(self):
        """Test if Google sign-in is working"""
        try:
            # Go to Google to test authentication
            logger.info("Testing Google authentication...")
            self.driver.get("https://accounts.google.com")
            time.sleep(3)
            
            # Check if already signed in
            if "myaccount.google.com" in self.driver.current_url or "accounts.google.com" in self.driver.current_url:
                # Look for profile picture or sign-out button
                try:
                    profile_elements = self.driver.find_elements(By.CSS_SELECTOR, "[data-testid='account-menu-button'], [aria-label*='Google Account'], img[alt*='Profile']")
                    if profile_elements:
                        logger.info("✅ Google authentication successful - already signed in")
                        return True
                except:
                    pass
            
            logger.warning("⚠️  Not signed in to Google. Please sign in manually first.")
            return False
            
        except Exception as e:
            logger.error(f"Error testing Google sign-in: {e}")
            return False

    def navigate_to_jobright(self):
        """Navigate to JobRight and handle authentication"""
        try:
            logger.info("Navigating to JobRight...")
            self.driver.get(f"{self.base_url}/jobs/recommend?pos=0")
            time.sleep(5)
            
            current_url = self.driver.current_url
            logger.info(f"Current URL: {current_url}")
            
            # Check if redirected to Google SSO
            if "accounts.google.com" in current_url or "google.com" in current_url:
                logger.info("🔐 Detected Google SSO page")
                
                # Wait for user to complete authentication manually
                print("\n" + "="*60)
                print("🔐 GOOGLE SSO DETECTED")
                print("="*60)
                print("Please complete the Google sign-in process manually in the browser window.")
                print("The script will continue automatically once you're signed in.")
                print("="*60)
                
                # Wait for redirect back to JobRight
                max_wait = 300  # 5 minutes
                wait_time = 0
                
                while wait_time < max_wait:
                    time.sleep(2)
                    wait_time += 2
                    current_url = self.driver.current_url
                    
                    if "jobright.ai" in current_url:
                        logger.info("✅ Successfully authenticated and redirected to JobRight")
                        return True
                    
                    if wait_time % 30 == 0:  # Every 30 seconds
                        print(f"⏳ Still waiting for authentication... ({wait_time}s elapsed)")
                
                logger.error("❌ Authentication timeout - please try again")
                return False
            
            elif "jobright.ai" in current_url:
                logger.info("✅ Successfully loaded JobRight")
                return True
            else:
                logger.warning(f"⚠️  Unexpected URL: {current_url}")
                return False
                
        except Exception as e:
            logger.error(f"Error navigating to JobRight: {e}")
            return False

    def find_apply_buttons(self):
        """Find all apply buttons on the page"""
        try:
            logger.info("Searching for apply buttons...")
            
            # Wait for page to load
            time.sleep(3)
            
            # Scroll to load all content
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)
            self.driver.execute_script("window.scrollTo(0, 0);")
            time.sleep(2)
            
            # Search for apply buttons
            apply_selectors = [
                "button:contains('Apply')",
                "button:contains('apply')",
                "a:contains('Apply')",
                "a:contains('apply')",
                "[data-testid*='apply']",
                ".apply-button",
                ".job-apply",
                "button[class*='apply']"
            ]
            
            found_buttons = []
            
            for selector in apply_selectors:
                try:
                    if ":contains" in selector:
                        # Use XPath for text-based selectors
                        xpath = f"//button[contains(text(), 'Apply') or contains(text(), 'apply')] | //a[contains(text(), 'Apply') or contains(text(), 'apply')]"
                        elements = self.driver.find_elements(By.XPATH, xpath)
                    else:
                        elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    
                    for element in elements:
                        if element.is_displayed() and element.is_enabled():
                            button_text = element.text.strip()
                            if button_text and "apply" in button_text.lower():
                                found_buttons.append({
                                    'element': element,
                                    'text': button_text,
                                    'tag': element.tag_name
                                })
                                logger.info(f"Found apply button: '{button_text}'")
                
                except Exception as e:
                    logger.warning(f"Error with selector {selector}: {e}")
                    continue
            
            # Remove duplicates
            unique_buttons = []
            seen_texts = set()
            
            for button in found_buttons:
                if button['text'].lower() not in seen_texts:
                    seen_texts.add(button['text'].lower())
                    unique_buttons.append(button)
            
            logger.info(f"Found {len(unique_buttons)} unique apply buttons")
            return unique_buttons
            
        except Exception as e:
            logger.error(f"Error finding apply buttons: {e}")
            return []

    def click_apply_button(self, button_info):
        """Click an apply button"""
        try:
            element = button_info['element']
            text = button_info['text']
            
            logger.info(f"Clicking apply button: '{text}'")
            
            # Scroll to button
            self.driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", element)
            time.sleep(1)
            
            # Try to click
            try:
                element.click()
            except:
                # Fallback to JavaScript click
                self.driver.execute_script("arguments[0].click();", element)
            
            time.sleep(3)
            
            # Check for new window or URL change
            if len(self.driver.window_handles) > 1:
                logger.info("New window/tab opened")
                # Switch to new window
                self.driver.switch_to.window(self.driver.window_handles[-1])
                time.sleep(2)
                logger.info(f"New window URL: {self.driver.current_url}")
                # Close new window and return to main
                self.driver.close()
                self.driver.switch_to.window(self.driver.window_handles[0])
            elif self.driver.current_url != f"{self.base_url}/jobs/recommend?pos=0":
                logger.info(f"Page navigated to: {self.driver.current_url}")
                # Go back
                self.driver.back()
                time.sleep(2)
            
            return True
            
        except Exception as e:
            logger.error(f"Error clicking apply button: {e}")
            return False

    def run_automation(self):
        """Run the complete automation"""
        try:
            print("🚀 JobRight.ai Google SSO Bypass Automation")
            print("="*60)
            
            # Setup driver
            if not self.setup_driver_with_google_profile():
                print("❌ Failed to setup Chrome with Google profile")
                return False
            
            # Test Google authentication
            if not self.test_google_signin():
                print("⚠️  Google authentication test failed, but continuing...")
            
            # Navigate to JobRight
            if not self.navigate_to_jobright():
                print("❌ Failed to navigate to JobRight")
                return False
            
            # Find apply buttons
            apply_buttons = self.find_apply_buttons()
            
            if not apply_buttons:
                print("❌ No apply buttons found!")
                print("Debug: Saving page source...")
                with open('/home/calelin/awesome-apply/debug_page_source.html', 'w', encoding='utf-8') as f:
                    f.write(self.driver.page_source)
                return False
            
            print(f"\n✅ Found {len(apply_buttons)} apply buttons:")
            for i, button in enumerate(apply_buttons, 1):
                print(f"  {i}. {button['text']}")
            
            # Ask user if they want to apply
            choice = input(f"\nDo you want to apply to all {len(apply_buttons)} jobs? (y/n): ").strip().lower()
            if choice != 'y':
                print("Automation cancelled.")
                return True
            
            # Apply to all jobs
            print(f"\n🎯 Applying to {len(apply_buttons)} jobs...")
            successful_applications = 0
            
            for i, button in enumerate(apply_buttons, 1):
                print(f"\n[{i}/{len(apply_buttons)}] Applying to: {button['text']}")
                
                if self.click_apply_button(button):
                    successful_applications += 1
                    print("✅ Application successful")
                else:
                    print("❌ Application failed")
                
                # Wait between applications
                time.sleep(2)
            
            print(f"\n🎉 Automation completed!")
            print(f"✅ Successful applications: {successful_applications}/{len(apply_buttons)}")
            
            return True
            
        except Exception as e:
            logger.error(f"Automation failed: {e}")
            print(f"❌ Automation failed: {e}")
            return False
        
        finally:
            if self.driver:
                input("\nPress Enter to close the browser...")
                self.driver.quit()

def main():
    """Main function"""
    automation = JobRightGoogleSSOBypass()
    automation.run_automation()

if __name__ == "__main__":
    main()
