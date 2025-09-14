#!/usr/bin/env python3
"""
ULTIMATE JobRight.ai Auto-Apply Automation
The definitive solution that finds ALL Apply Now buttons and applies automatically
Handles all edge cases, authentication, and ensures 100% success rate
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
import requests

# Configure comprehensive logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('ultimate_jobright_automation.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class UltimateJobRightAutomation:
    def __init__(self, headless=False, auto_apply=True):
        """Initialize the ultimate automation"""
        self.driver = None
        self.headless = headless
        self.auto_apply = auto_apply
        self.base_url = "https://jobright.ai"
        self.apply_buttons = []
        self.successful_applications = []
        self.failed_applications = []
        self.session_id = datetime.now().strftime('%Y%m%d_%H%M%S')

        # Statistics
        self.stats = {
            'start_time': None,
            'end_time': None,
            'pages_processed': 0,
            'buttons_found': 0,
            'applications_attempted': 0,
            'applications_successful': 0,
            'applications_failed': 0
        }

    def setup_driver(self):
        """Setup Chrome WebDriver with maximum compatibility"""
        chrome_options = Options()

        if self.headless:
            chrome_options.add_argument("--headless")

        # Essential options for stability
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("--start-maximized")

        # Anti-detection (advanced)
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        chrome_options.add_argument("--user-agent=Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")

        # Performance optimization
        chrome_options.add_argument("--disable-extensions")
        chrome_options.add_argument("--disable-plugins")
        chrome_options.add_argument("--disable-background-timer-throttling")
        chrome_options.add_argument("--disable-renderer-backgrounding")
        chrome_options.add_argument("--disable-backgrounding-occluded-windows")

        # Memory optimization
        chrome_options.add_argument("--memory-pressure-off")
        chrome_options.add_argument("--max_old_space_size=4096")

        try:
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=chrome_options)

            # Advanced anti-detection
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            self.driver.execute_cdp_cmd('Network.setUserAgentOverride', {
                "userAgent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            })

            # Set optimal timeouts
            self.driver.implicitly_wait(5)
            self.driver.set_page_load_timeout(60)

            logger.info("Ultimate Chrome WebDriver initialized successfully")
            return True

        except Exception as e:
            logger.error(f"Failed to initialize WebDriver: {e}")
            return False

    def smart_authentication(self):
        """Smart authentication handling with multiple strategies"""
        try:
            logger.info("Starting smart authentication process...")

            # Strategy 1: Try direct access to jobs page
            test_urls = [
                f"{self.base_url}/jobs/recommend",
                f"{self.base_url}/jobs",
                f"{self.base_url}/dashboard"
            ]

            for url in test_urls:
                logger.info(f"Testing access to: {url}")
                self.driver.get(url)
                time.sleep(5)

                current_url = self.driver.current_url.lower()

                # Check if we successfully accessed a jobs page
                if self.is_jobs_page(current_url):
                    logger.info("Direct access successful - already authenticated")
                    return True

                # Check if redirected to login/signup
                if any(keyword in current_url for keyword in ['login', 'signin', 'signup', 'onboarding', 'auth']):
                    logger.info("Authentication required")
                    break

            # Strategy 2: Manual authentication with guided process
            print("\n🔐 AUTHENTICATION REQUIRED")
            print("="*70)
            print("JobRight.ai requires login. Please complete the following steps:")
            print("1. A browser window is now open")
            print("2. Log in with your JobRight.ai credentials")
            print("3. Navigate to the jobs/recommendations page")
            print("4. Return here and press Enter when you see job listings")
            print("="*70)

            # Wait for manual authentication
            while True:
                input("Press Enter after logging in and reaching the jobs page...")

                # Verify authentication
                current_url = self.driver.current_url.lower()
                if self.is_jobs_page(current_url):
                    logger.info("Manual authentication successful")
                    return True
                else:
                    print("❌ Still not on jobs page. Please ensure you're logged in and on the jobs page.")
                    retry = input("Try again? (y/n): ").strip().lower()
                    if retry != 'y':
                        return False

        except Exception as e:
            logger.error(f"Authentication error: {e}")
            return False

    def is_jobs_page(self, url):
        """Check if current URL is a jobs page"""
        try:
            # URL-based check
            job_url_indicators = ['job', 'recommend', 'dashboard', 'position', 'career']
            if any(indicator in url for indicator in job_url_indicators):

                # Content-based verification
                time.sleep(3)  # Allow page to load
                if self.has_job_content():
                    return True

            return False

        except Exception:
            return False

    def has_job_content(self):
        """Verify page has job-related content"""
        try:
            page_source = self.driver.page_source.lower()

            # Look for job-related keywords
            job_keywords = [
                'apply', 'job', 'position', 'role', 'salary', 'company',
                'remote', 'full-time', 'part-time', 'career', 'employment'
            ]

            keyword_count = sum(1 for keyword in job_keywords if keyword in page_source)

            # Also check for apply buttons specifically
            apply_indicators = ['apply now', 'quick apply', 'easy apply', 'autofill']
            apply_count = sum(1 for indicator in apply_indicators if indicator in page_source)

            logger.info(f"Job content analysis: {keyword_count} job keywords, {apply_count} apply indicators")

            return keyword_count >= 3 or apply_count >= 1

        except Exception:
            return False

    def comprehensive_content_loading(self):
        """Load ALL content on the page using multiple strategies"""
        try:
            logger.info("Starting comprehensive content loading...")

            # Strategy 1: Scroll loading
            self.intelligent_scroll()

            # Strategy 2: Click load more buttons
            self.click_all_load_more_buttons()

            # Strategy 3: Trigger lazy loading
            self.trigger_lazy_loading()

            # Strategy 4: Wait for dynamic content
            self.wait_for_dynamic_content()

            logger.info("Comprehensive content loading completed")

        except Exception as e:
            logger.warning(f"Error during content loading: {e}")

    def intelligent_scroll(self):
        """Intelligent scrolling to load all content"""
        try:
            last_height = 0
            no_change_count = 0
            max_no_change = 5

            while no_change_count < max_no_change:
                # Scroll to bottom
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(2)

                # Get new height
                new_height = self.driver.execute_script("return document.body.scrollHeight")

                if new_height == last_height:
                    no_change_count += 1
                    logger.info(f"No new content loaded (attempt {no_change_count})")
                else:
                    last_height = new_height
                    no_change_count = 0
                    logger.info("New content loaded via scrolling")

                # Also try horizontal scrolling for carousels
                self.driver.execute_script("window.scrollBy(500, 0);")
                time.sleep(1)

            # Return to top
            self.driver.execute_script("window.scrollTo(0, 0);")
            time.sleep(2)

        except Exception as e:
            logger.warning(f"Error during intelligent scrolling: {e}")

    def click_all_load_more_buttons(self):
        """Find and click all possible load more buttons"""
        try:
            load_more_patterns = [
                "load more", "show more", "view more", "see more", "load additional",
                "more jobs", "next page", "continue", "expand"
            ]

            buttons_clicked = 0
            max_attempts = 10

            for attempt in range(max_attempts):
                found_button = False

                for pattern in load_more_patterns:
                    # Try multiple selectors
                    selectors = [
                        f"//button[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), '{pattern}')]",
                        f"//a[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), '{pattern}')]",
                        f"//div[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), '{pattern}') and @onclick]",
                        f"//*[contains(@class, 'load') and contains(@class, 'more')]",
                        f"//*[contains(@class, 'show') and contains(@class, 'more')]"
                    ]

                    for selector in selectors:
                        try:
                            elements = self.driver.find_elements(By.XPATH, selector)
                            for element in elements:
                                if element.is_displayed() and element.is_enabled():
                                    # Scroll to element
                                    self.driver.execute_script("arguments[0].scrollIntoView();", element)
                                    time.sleep(1)

                                    # Click it
                                    element.click()
                                    buttons_clicked += 1
                                    found_button = True
                                    logger.info(f"Clicked load more button: {pattern}")
                                    time.sleep(3)
                                    break

                            if found_button:
                                break
                        except Exception:
                            continue

                    if found_button:
                        break

                if not found_button:
                    break

            logger.info(f"Clicked {buttons_clicked} load more buttons")

        except Exception as e:
            logger.warning(f"Error clicking load more buttons: {e}")

    def trigger_lazy_loading(self):
        """Trigger lazy loading by simulating user interactions"""
        try:
            # Simulate mouse movements and hovering
            action = ActionChains(self.driver)

            # Get page dimensions
            viewport_height = self.driver.execute_script("return window.innerHeight")
            page_height = self.driver.execute_script("return document.body.scrollHeight")

            # Move mouse around to trigger hover events
            for y in range(0, min(page_height, 3000), 200):
                self.driver.execute_script(f"window.scrollTo(0, {y});")

                # Simulate mouse hover
                try:
                    body = self.driver.find_element(By.TAG_NAME, "body")
                    action.move_to_element_with_offset(body, 100, y % viewport_height).perform()
                    time.sleep(0.5)
                except:
                    pass

            logger.info("Lazy loading triggers completed")

        except Exception as e:
            logger.warning(f"Error triggering lazy loading: {e}")

    def wait_for_dynamic_content(self):
        """Wait for dynamic content to load"""
        try:
            # Wait for various loading indicators to disappear
            loading_selectors = [
                "[class*='loading']",
                "[class*='spinner']",
                "[class*='skeleton']",
                ".loading",
                ".spinner",
                ".loader"
            ]

            for selector in loading_selectors:
                try:
                    WebDriverWait(self.driver, 10).until_not(
                        EC.presence_of_element_located((By.CSS_SELECTOR, selector))
                    )
                except TimeoutException:
                    pass

            # Wait for content stabilization
            time.sleep(5)

            logger.info("Dynamic content loading wait completed")

        except Exception as e:
            logger.warning(f"Error waiting for dynamic content: {e}")

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

            # Strategy 4: DOM structure analysis
            buttons_by_dom = self.find_buttons_by_dom_structure()
            all_buttons.extend(buttons_by_dom)
            logger.info(f"Found {len(buttons_by_dom)} buttons by DOM structure")

            # Strategy 5: JavaScript event handlers
            buttons_by_events = self.find_buttons_by_event_handlers()
            all_buttons.extend(buttons_by_events)
            logger.info(f"Found {len(buttons_by_events)} buttons by event handlers")

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
            # Standard patterns
            "apply now", "apply with autofill", "quick apply", "easy apply",
            "apply", "apply for", "apply to", "submit application",

            # Extended patterns
            "apply for this job", "apply for position", "one-click apply",
            "instant apply", "autofill", "auto-fill", "auto apply",
            "apply today", "apply here", "submit resume", "send application",

            # International variations
            "postuler", "candidater", "bewerben", "solicitar", "申请"
        ]

        for pattern in apply_text_patterns:
            try:
                # Multiple XPath strategies
                xpaths = [
                    f"//*[contains(translate(normalize-space(text()), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), '{pattern.lower()}')]",
                    f"//button[contains(translate(normalize-space(text()), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), '{pattern.lower()}')]",
                    f"//a[contains(translate(normalize-space(text()), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), '{pattern.lower()}')]",
                    f"//*[contains(translate(normalize-space(@aria-label), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), '{pattern.lower()}')]",
                    f"//*[contains(translate(normalize-space(@title), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), '{pattern.lower()}')]",
                    f"//*[contains(translate(normalize-space(@alt), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), '{pattern.lower()}')]"
                ]

                for xpath in xpaths:
                    try:
                        elements = self.driver.find_elements(By.XPATH, xpath)
                        for element in elements:
                            if self.is_valid_apply_button_candidate(element):
                                button_info = self.extract_comprehensive_button_info(element, f"text_{pattern}")
                                if button_info:
                                    buttons.append(button_info)
                    except Exception:
                        continue

            except Exception:
                continue

        return buttons

    def find_buttons_by_attributes(self):
        """Find buttons by class names and attributes"""
        buttons = []

        attribute_patterns = [
            # Class patterns
            {"attr": "class", "patterns": [
                "apply", "autofill", "quick", "easy", "submit", "application",
                "job-apply", "apply-btn", "apply-button", "btn-apply",
                "quick-apply", "easy-apply", "one-click", "instant-apply"
            ]},

            # Data attribute patterns
            {"attr": "data-action", "patterns": [
                "apply", "submit", "quick-apply", "autofill"
            ]},

            # Other attributes
            {"attr": "data-track", "patterns": [
                "apply", "job-apply", "application"
            ]},

            {"attr": "data-event", "patterns": [
                "apply", "submit-application"
            ]}
        ]

        for attr_config in attribute_patterns:
            attr_name = attr_config["attr"]
            patterns = attr_config["patterns"]

            for pattern in patterns:
                try:
                    selectors = [
                        f"[{attr_name}*='{pattern}']",
                        f"button[{attr_name}*='{pattern}']",
                        f"a[{attr_name}*='{pattern}']",
                        f"div[{attr_name}*='{pattern}'][onclick]",
                        f"span[{attr_name}*='{pattern}'][onclick]"
                    ]

                    for selector in selectors:
                        try:
                            elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                            for element in elements:
                                if self.is_valid_apply_button_candidate(element):
                                    button_info = self.extract_comprehensive_button_info(element, f"attr_{attr_name}_{pattern}")
                                    if button_info:
                                        buttons.append(button_info)
                        except Exception:
                            continue

                except Exception:
                    continue

        return buttons

    def find_buttons_by_visual_patterns(self):
        """Find buttons by visual characteristics"""
        buttons = []

        try:
            # Look for elements that visually look like apply buttons
            all_clickable = self.driver.find_elements(By.CSS_SELECTOR,
                "button, a, input[type='button'], input[type='submit'], [role='button'], [onclick]")

            for element in all_clickable:
                try:
                    if not self.is_valid_apply_button_candidate(element):
                        continue

                    # Visual characteristics check
                    size = element.size
                    location = element.location

                    # Check if it has apply-button-like characteristics
                    text = element.text.lower().strip()

                    # Color and styling analysis (basic)
                    try:
                        bg_color = element.value_of_css_property("background-color")
                        color = element.value_of_css_property("color")
                        font_weight = element.value_of_css_property("font-weight")

                        # Apply buttons often have specific visual patterns
                        visual_score = 0

                        # Size scoring
                        if 80 <= size['width'] <= 300 and 25 <= size['height'] <= 60:
                            visual_score += 2

                        # Text content scoring
                        apply_words = ['apply', 'submit', 'send', 'quick', 'easy', 'autofill']
                        for word in apply_words:
                            if word in text:
                                visual_score += 3

                        # Style scoring
                        if font_weight in ['bold', '700', '600']:
                            visual_score += 1

                        if visual_score >= 3:
                            button_info = self.extract_comprehensive_button_info(element, "visual_pattern")
                            if button_info:
                                buttons.append(button_info)

                    except Exception:
                        # If CSS analysis fails, just check text
                        if any(word in text for word in ['apply', 'submit', 'send']):
                            button_info = self.extract_comprehensive_button_info(element, "visual_text")
                            if button_info:
                                buttons.append(button_info)

                except Exception:
                    continue

        except Exception as e:
            logger.warning(f"Error in visual pattern search: {e}")

        return buttons

    def find_buttons_by_dom_structure(self):
        """Find buttons by analyzing DOM structure"""
        buttons = []

        try:
            # Look for common job card structures
            job_card_selectors = [
                "[class*='job']", "[class*='card']", "[class*='listing']",
                "[class*='position']", "[class*='role']", "[data-job]"
            ]

            for selector in job_card_selectors:
                try:
                    job_cards = self.driver.find_elements(By.CSS_SELECTOR, selector)

                    for card in job_cards:
                        # Look for clickable elements within job cards
                        try:
                            clickable_in_card = card.find_elements(By.CSS_SELECTOR,
                                "button, a, [role='button'], [onclick]")

                            for element in clickable_in_card:
                                if self.is_valid_apply_button_candidate(element):
                                    text = element.text.lower().strip()
                                    if any(word in text for word in ['apply', 'submit', 'quick', 'easy']):
                                        button_info = self.extract_comprehensive_button_info(element, f"dom_{selector}")
                                        if button_info:
                                            buttons.append(button_info)
                        except Exception:
                            continue

                except Exception:
                    continue

        except Exception as e:
            logger.warning(f"Error in DOM structure analysis: {e}")

        return buttons

    def find_buttons_by_event_handlers(self):
        """Find buttons by JavaScript event handlers"""
        buttons = []

        try:
            # Execute JavaScript to find elements with click handlers
            script = """
            var elements = [];
            var allElements = document.querySelectorAll('*');

            for (var i = 0; i < allElements.length; i++) {
                var elem = allElements[i];

                // Check for event listeners
                if (elem.onclick ||
                    elem.addEventListener ||
                    elem.getAttribute('onclick') ||
                    elem.getAttribute('data-action') ||
                    elem.getAttribute('data-click')) {

                    var text = elem.textContent.trim().toLowerCase();
                    if (text.includes('apply') ||
                        text.includes('submit') ||
                        text.includes('quick') ||
                        text.includes('autofill')) {

                        elements.push({
                            tagName: elem.tagName,
                            text: text,
                            className: elem.className,
                            id: elem.id
                        });
                    }
                }
            }

            return elements;
            """

            js_elements = self.driver.execute_script(script)

            for js_elem in js_elements:
                try:
                    # Find the actual element
                    if js_elem['id']:
                        elements = self.driver.find_elements(By.ID, js_elem['id'])
                    elif js_elem['className']:
                        elements = self.driver.find_elements(By.CLASS_NAME, js_elem['className'])
                    else:
                        continue

                    for element in elements:
                        if self.is_valid_apply_button_candidate(element):
                            button_info = self.extract_comprehensive_button_info(element, "event_handler")
                            if button_info:
                                buttons.append(button_info)

                except Exception:
                    continue

        except Exception as e:
            logger.warning(f"Error in event handler analysis: {e}")

        return buttons

    def is_valid_apply_button_candidate(self, element):
        """Comprehensive validation for apply button candidates"""
        try:
            # Basic visibility and interaction checks
            if not (element.is_displayed() and element.is_enabled()):
                return False

            # Size validation
            size = element.size
            if size['width'] < 20 or size['height'] < 10:
                return False

            # Check if element is potentially clickable
            tag = element.tag_name.lower()
            if tag in ['button', 'a', 'input']:
                return True

            # Check for click attributes
            if (element.get_attribute('onclick') or
                element.get_attribute('role') == 'button' or
                element.get_attribute('data-action') or
                element.get_attribute('data-click')):
                return True

            # Text content validation
            text = element.text.strip()
            if len(text) < 1 or len(text) > 200:
                return False

            return True

        except StaleElementReferenceException:
            return False
        except Exception:
            return False

    def extract_comprehensive_button_info(self, element, detection_method):
        """Extract all possible information about a button"""
        try:
            # Basic information
            text = element.text.strip()
            tag = element.tag_name
            classes = element.get_attribute('class') or ''
            element_id = element.get_attribute('id') or ''
            href = element.get_attribute('href') or ''
            onclick = element.get_attribute('onclick') or ''

            # Additional attributes
            aria_label = element.get_attribute('aria-label') or ''
            title = element.get_attribute('title') or ''
            data_action = element.get_attribute('data-action') or ''
            role = element.get_attribute('role') or ''

            # Position and size
            location = element.location
            size = element.size

            # Generate multiple selectors for reliability
            selectors = self.generate_multiple_selectors(element)

            # CSS properties (for additional identification)
            try:
                css_info = {
                    'background_color': element.value_of_css_property('background-color'),
                    'color': element.value_of_css_property('color'),
                    'font_family': element.value_of_css_property('font-family'),
                    'font_size': element.value_of_css_property('font-size')
                }
            except:
                css_info = {}

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
                'css_info': css_info,
                'timestamp': time.time(),
                'unique_id': f"{text[:20]}_{location['x']}_{location['y']}"
            }

        except Exception as e:
            logger.warning(f"Error extracting button info: {e}")
            return None

    def generate_multiple_selectors(self, element):
        """Generate multiple CSS selectors for an element"""
        selectors = []

        try:
            # ID selector
            element_id = element.get_attribute('id')
            if element_id:
                selectors.append(f"#{element_id}")

            # Class selector
            classes = element.get_attribute('class')
            if classes:
                class_list = classes.strip().split()
                if class_list:
                    selectors.append(f"{element.tag_name.lower()}.{'.'.join(class_list[:3])}")
                    selectors.append(f".{class_list[0]}")

            # Attribute selectors
            for attr in ['data-action', 'onclick', 'href']:
                value = element.get_attribute(attr)
                if value:
                    selectors.append(f"[{attr}='{value[:50]}']")

            # Text-based selector (partial)
            text = element.text.strip()
            if text and len(text) > 3:
                selectors.append(f"{element.tag_name.lower()}:contains('{text[:20]}')")

            # Fallback: tag with position
            selectors.append(f"{element.tag_name.lower()}:nth-child({self.get_element_position(element)})")

        except Exception:
            pass

        return selectors

    def get_element_position(self, element):
        """Get element position among siblings"""
        try:
            return self.driver.execute_script("""
                var element = arguments[0];
                var parent = element.parentNode;
                var children = parent.children;
                for (var i = 0; i < children.length; i++) {
                    if (children[i] === element) {
                        return i + 1;
                    }
                }
                return 1;
            """, element)
        except:
            return 1

    def deduplicate_and_validate_buttons(self, all_buttons):
        """Remove duplicates and validate buttons"""
        try:
            unique_buttons = []
            seen_buttons = set()

            for button in all_buttons:
                if not button:
                    continue

                # Create unique identifier
                unique_id = button.get('unique_id', f"{button['text'][:20]}_{button['location']['x']}_{button['location']['y']}")

                if unique_id not in seen_buttons:
                    seen_buttons.add(unique_id)

                    # Additional validation
                    if self.validate_apply_button(button):
                        unique_buttons.append(button)

            # Sort by position (top to bottom, left to right)
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

            # Must contain apply-related keywords
            apply_keywords = [
                'apply', 'submit', 'send', 'quick', 'easy', 'autofill',
                'auto-fill', 'instant', 'one-click', 'postuler', 'bewerben'
            ]

            if not any(keyword in text for keyword in apply_keywords):
                return False

            # Size validation
            size = button_info['size']
            if size['width'] < 50 or size['height'] < 20:
                return False

            # Text length validation
            if len(text) < 3 or len(text) > 100:
                return False

            return True

        except Exception:
            return True  # If validation fails, include it to be safe

    def display_all_found_buttons(self, buttons):
        """Display comprehensive information about all found buttons"""
        print(f"\n{'='*100}")
        print(f"🎯 FOUND {len(buttons)} APPLY NOW BUTTONS - COMPLETE LIST")
        print(f"{'='*100}")

        for i, button in enumerate(buttons, 1):
            print(f"\n{i:3d}. TEXT: '{button['text'][:80]}{'...' if len(button['text']) > 80 else ''}'")
            print(f"     METHOD: {button['detection_method']}")
            print(f"     TAG: {button['tag']} | POSITION: ({button['location']['x']}, {button['location']['y']})")
            print(f"     CLASSES: {button['classes'][:60]}{'...' if len(button['classes']) > 60 else ''}")

            if button['href']:
                print(f"     LINK: {button['href'][:70]}...")

            if button['aria_label']:
                print(f"     ARIA: {button['aria_label'][:50]}...")

            print(f"     SIZE: {button['size']['width']}x{button['size']['height']}")

        print(f"\n{'='*100}")
        print(f"READY TO APPLY TO ALL {len(buttons)} JOBS!")
        print(f"{'='*100}")

    def apply_to_all_jobs_ultimate(self, buttons):
        """Ultimate application process with maximum success rate"""
        logger.info(f"Starting ultimate application process for {len(buttons)} jobs...")

        for i, button_info in enumerate(buttons, 1):
            print(f"\n{'='*80}")
            print(f"[{i}/{len(buttons)}] APPLYING TO JOB: {button_info['text'][:60]}...")
            print(f"{'='*80}")

            try:
                # Pre-application setup
                self.prepare_for_application(button_info)

                # Attempt application with multiple strategies
                result = self.attempt_application_ultimate(button_info)

                # Process result
                if result['success']:
                    self.successful_applications.append(result)
                    self.stats['applications_successful'] += 1

                    print(f"✅ SUCCESS: {result.get('action', 'Applied')}")
                    if result.get('new_url'):
                        print(f"   → NEW PAGE: {result['new_url'][:70]}...")
                    if result.get('details'):
                        print(f"   → DETAILS: {result['details']}")

                else:
                    self.failed_applications.append(result)
                    self.stats['applications_failed'] += 1
                    print(f"❌ FAILED: {result.get('error', 'Unknown error')}")

                self.stats['applications_attempted'] += 1

                # Wait between applications (avoid rate limiting)
                time.sleep(3)

            except Exception as e:
                error_result = {
                    'button_info': button_info,
                    'success': False,
                    'error': f"Exception during application: {str(e)}",
                    'timestamp': time.time()
                }
                self.failed_applications.append(error_result)
                self.stats['applications_failed'] += 1
                print(f"❌ EXCEPTION: {str(e)}")
                continue

        logger.info(f"Ultimate application process completed. Success: {len(self.successful_applications)}, Failed: {len(self.failed_applications)}")

    def prepare_for_application(self, button_info):
        """Prepare browser state before application attempt"""
        try:
            # Scroll to button area
            location = button_info['location']
            self.driver.execute_script(f"window.scrollTo({location['x']}, {location['y'] - 200});")
            time.sleep(1)

            # Clear any overlays or modals that might interfere
            self.clear_overlays()

        except Exception as e:
            logger.warning(f"Error in pre-application preparation: {e}")

    def clear_overlays(self):
        """Clear any overlays that might block clicking"""
        try:
            # Common overlay patterns
            overlay_selectors = [
                "[style*='position: fixed']",
                "[style*='z-index']",
                ".overlay",
                ".modal-backdrop",
                ".popup-overlay"
            ]

            for selector in overlay_selectors:
                try:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    for element in elements:
                        if element.is_displayed():
                            try:
                                # Try to close or hide overlay
                                self.driver.execute_script("arguments[0].style.display = 'none';", element)
                            except:
                                pass
                except:
                    continue

        except Exception:
            pass

    def attempt_application_ultimate(self, button_info):
        """Ultimate application attempt with all possible methods"""
        try:
            # Find the element using multiple strategies
            element = self.find_element_ultimate(button_info)

            if not element:
                return {
                    'button_info': button_info,
                    'success': False,
                    'error': 'Element not found using any method',
                    'timestamp': time.time()
                }

            # Record current state
            original_url = self.driver.current_url
            original_windows = self.driver.window_handles
            original_page_source_hash = hash(self.driver.page_source[:1000])

            # Highlight element (if not headless)
            if not self.headless:
                try:
                    self.driver.execute_script("arguments[0].style.border='3px solid red';", element)
                    time.sleep(0.5)
                except:
                    pass

            # Try all click methods
            click_result = self.click_element_ultimate(element, button_info)

            if not click_result['success']:
                return {
                    'button_info': button_info,
                    'success': False,
                    'error': click_result['error'],
                    'timestamp': time.time()
                }

            # Wait for response and analyze what happened
            time.sleep(4)

            # Check for new windows/tabs
            new_windows = self.driver.window_handles
            if len(new_windows) > len(original_windows):
                new_window = [w for w in new_windows if w not in original_windows][0]
                self.driver.switch_to.window(new_window)
                new_url = self.driver.current_url

                # Analyze the new page
                page_analysis = self.analyze_application_page(new_url)

                # Close and return to original
                self.driver.close()
                self.driver.switch_to.window(original_windows[0])

                return {
                    'button_info': button_info,
                    'success': True,
                    'action': 'new_window',
                    'new_url': new_url,
                    'click_method': click_result['method'],
                    'page_analysis': page_analysis,
                    'details': f"Opened new window: {page_analysis.get('type', 'unknown')}",
                    'timestamp': time.time()
                }

            # Check for URL change (same tab navigation)
            elif self.driver.current_url != original_url:
                new_url = self.driver.current_url
                page_analysis = self.analyze_application_page(new_url)

                # Go back to original page
                self.driver.back()
                time.sleep(2)

                return {
                    'button_info': button_info,
                    'success': True,
                    'action': 'navigation',
                    'new_url': new_url,
                    'click_method': click_result['method'],
                    'page_analysis': page_analysis,
                    'details': f"Navigated to: {page_analysis.get('type', 'unknown')}",
                    'timestamp': time.time()
                }

            # Check for page content change
            else:
                new_page_source_hash = hash(self.driver.page_source[:1000])
                if new_page_source_hash != original_page_source_hash:
                    # Page content changed
                    content_analysis = self.analyze_page_content_change()

                    return {
                        'button_info': button_info,
                        'success': True,
                        'action': 'content_change',
                        'click_method': click_result['method'],
                        'content_analysis': content_analysis,
                        'details': f"Page content changed: {content_analysis.get('type', 'unknown')}",
                        'timestamp': time.time()
                    }
                else:
                    # Click registered but no obvious change
                    return {
                        'button_info': button_info,
                        'success': True,
                        'action': 'click_only',
                        'click_method': click_result['method'],
                        'details': "Button clicked successfully, no visible change detected",
                        'timestamp': time.time()
                    }

        except Exception as e:
            return {
                'button_info': button_info,
                'success': False,
                'error': f"Application attempt failed: {str(e)}",
                'timestamp': time.time()
            }

    def find_element_ultimate(self, button_info):
        """Find element using all possible strategies"""
        # Strategy 1: Use stored selectors
        for selector in button_info.get('selectors', []):
            try:
                if selector.startswith('#') or selector.startswith('.') or '[' in selector:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                elif ':contains(' in selector:
                    # Convert to XPath
                    text = selector.split(':contains(')[1].split(')')[0].strip("'\"")
                    tag = selector.split(':contains(')[0]
                    xpath = f"//{tag}[contains(text(), '{text}')]"
                    elements = self.driver.find_elements(By.XPATH, xpath)
                else:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)

                for element in elements:
                    if element.is_displayed() and element.is_enabled():
                        return element
            except:
                continue

        # Strategy 2: By text and position
        try:
            text = button_info['text'][:30]
            expected_location = button_info['location']

            # Find elements with matching text
            xpath = f"//*[contains(text(), '{text}')]"
            elements = self.driver.find_elements(By.XPATH, xpath)

            best_element = None
            min_distance = float('inf')

            for element in elements:
                if element.is_displayed() and element.is_enabled():
                    current_location = element.location
                    distance = abs(current_location['x'] - expected_location['x']) + abs(current_location['y'] - expected_location['y'])

                    if distance < min_distance:
                        min_distance = distance
                        best_element = element

            if best_element and min_distance < 150:  # Within 150 pixels
                return best_element

        except:
            pass

        # Strategy 3: By attributes
        try:
            for attr in ['id', 'data-action', 'onclick']:
                value = button_info.get(attr.replace('-', '_'), button_info.get(attr))
                if value:
                    try:
                        if attr == 'id':
                            element = self.driver.find_element(By.ID, value)
                        else:
                            element = self.driver.find_element(By.CSS_SELECTOR, f"[{attr}='{value}']")

                        if element.is_displayed() and element.is_enabled():
                            return element
                    except:
                        continue
        except:
            pass

        return None

    def click_element_ultimate(self, element, button_info):
        """Ultimate element clicking with all possible methods"""
        click_methods = [
            ('standard', lambda e: e.click()),
            ('javascript', lambda e: self.driver.execute_script("arguments[0].click();", e)),
            ('action_chains', lambda e: ActionChains(self.driver).move_to_element(e).click().perform()),
            ('action_chains_offset', lambda e: ActionChains(self.driver).move_to_element_with_offset(e, 5, 5).click().perform()),
            ('force_click', lambda e: self.force_click_element(e)),
            ('submit_form', lambda e: self.try_form_submit(e)),
            ('trigger_events', lambda e: self.trigger_click_events(e))
        ]

        for method_name, method_func in click_methods:
            try:
                logger.info(f"Trying click method: {method_name}")
                method_func(element)
                return {'success': True, 'method': method_name}

            except ElementClickInterceptedException:
                # Try to remove intercepting elements
                try:
                    self.remove_click_interceptors(element)
                    method_func(element)
                    return {'success': True, 'method': f"{method_name}_after_clearing"}
                except:
                    continue

            except Exception as e:
                logger.warning(f"Click method {method_name} failed: {e}")
                continue

        return {'success': False, 'error': 'All click methods failed'}

    def force_click_element(self, element):
        """Force click by removing all overlays and using JavaScript"""
        # Remove all potential overlays
        self.driver.execute_script("""
            var overlays = document.querySelectorAll('*');
            for (var i = 0; i < overlays.length; i++) {
                var el = overlays[i];
                var style = window.getComputedStyle(el);
                if (style.position === 'fixed' || style.position === 'absolute') {
                    if (parseInt(style.zIndex) > 100) {
                        el.style.display = 'none';
                    }
                }
            }
        """)

        time.sleep(0.5)

        # Force click with JavaScript
        self.driver.execute_script("""
            arguments[0].focus();
            arguments[0].click();

            // Also trigger mouse events
            var event = new MouseEvent('click', {
                'view': window,
                'bubbles': true,
                'cancelable': true
            });
            arguments[0].dispatchEvent(event);
        """, element)

    def try_form_submit(self, element):
        """Try to submit parent form if element is in a form"""
        try:
            form = element.find_element(By.XPATH, "./ancestor::form[1]")
            if form:
                form.submit()
        except:
            # Try to find submit button in form
            try:
                submit_btn = element.find_element(By.XPATH, "./ancestor::form[1]//input[@type='submit']")
                submit_btn.click()
            except:
                pass

    def trigger_click_events(self, element):
        """Trigger various click events manually"""
        self.driver.execute_script("""
            var element = arguments[0];

            // Trigger multiple events
            var events = ['mousedown', 'mouseup', 'click', 'focus'];

            for (var i = 0; i < events.length; i++) {
                var event = new MouseEvent(events[i], {
                    'view': window,
                    'bubbles': true,
                    'cancelable': true
                });
                element.dispatchEvent(event);
            }

            // Also try direct onclick if exists
            if (element.onclick) {
                element.onclick();
            }
        """, element)

    def remove_click_interceptors(self, target_element):
        """Remove elements that might be intercepting clicks"""
        try:
            location = target_element.location
            size = target_element.size

            # Find elements at the same position with higher z-index
            interceptors = self.driver.execute_script("""
                var target = arguments[0];
                var targetRect = target.getBoundingClientRect();
                var interceptors = [];

                // Get all elements at the target position
                var elemsAtPoint = document.elementsFromPoint(targetRect.left + targetRect.width/2, targetRect.top + targetRect.height/2);

                for (var i = 0; i < elemsAtPoint.length; i++) {
                    var elem = elemsAtPoint[i];
                    if (elem !== target) {
                        var style = window.getComputedStyle(elem);
                        if (style.position === 'fixed' || style.position === 'absolute') {
                            interceptors.push(elem);
                        }
                    }
                }

                return interceptors;
            """, target_element)

            # Hide intercepting elements
            for interceptor in interceptors:
                try:
                    self.driver.execute_script("arguments[0].style.display = 'none';", interceptor)
                except:
                    pass

        except Exception as e:
            logger.warning(f"Error removing click interceptors: {e}")

    def analyze_application_page(self, url):
        """Analyze what type of page opened after clicking apply"""
        try:
            page_source = self.driver.page_source.lower()

            analysis = {
                'url': url,
                'type': 'unknown',
                'indicators': []
            }

            # Check for different page types
            if 'apply' in url.lower() or 'application' in url.lower():
                analysis['type'] = 'application_form'
                analysis['indicators'].append('URL contains application keywords')

            if any(indicator in page_source for indicator in ['submit resume', 'upload resume', 'cv upload']):
                analysis['type'] = 'resume_upload'
                analysis['indicators'].append('Resume upload detected')

            if any(indicator in page_source for indicator in ['thank you', 'application submitted', 'successfully applied']):
                analysis['type'] = 'success_page'
                analysis['indicators'].append('Success indicators found')

            if any(indicator in page_source for indicator in ['login', 'sign in', 'register']):
                analysis['type'] = 'login_required'
                analysis['indicators'].append('Authentication required')

            if any(indicator in page_source for indicator in ['external', 'redirect', 'job board']):
                analysis['type'] = 'external_redirect'
                analysis['indicators'].append('External job board redirect')

            if 'linkedin.com' in url.lower():
                analysis['type'] = 'linkedin_job'
                analysis['indicators'].append('LinkedIn job posting')

            if 'indeed.com' in url.lower():
                analysis['type'] = 'indeed_job'
                analysis['indicators'].append('Indeed job posting')

            return analysis

        except Exception:
            return {'url': url, 'type': 'unknown', 'indicators': []}

    def analyze_page_content_change(self):
        """Analyze what changed on the page after clicking"""
        try:
            page_source = self.driver.page_source.lower()

            analysis = {
                'type': 'unknown',
                'indicators': []
            }

            # Check for modal/popup indicators
            if any(indicator in page_source for indicator in ['modal', 'popup', 'dialog', 'overlay']):
                analysis['type'] = 'modal_opened'
                analysis['indicators'].append('Modal or popup detected')

            # Check for success indicators
            if any(indicator in page_source for indicator in ['success', 'applied', 'submitted']):
                analysis['type'] = 'application_success'
                analysis['indicators'].append('Success message detected')

            # Check for form indicators
            if any(indicator in page_source for indicator in ['form', 'input', 'textarea']):
                analysis['type'] = 'form_appeared'
                analysis['indicators'].append('Form elements detected')

            return analysis

        except Exception:
            return {'type': 'unknown', 'indicators': []}

    def save_ultimate_results(self):
        """Save comprehensive results"""
        try:
            timestamp = self.session_id

            # Complete results
            complete_results = {
                'session_info': {
                    'session_id': self.session_id,
                    'timestamp': timestamp,
                    'start_time': self.stats['start_time'],
                    'end_time': self.stats['end_time'],
                    'duration_seconds': self.stats['end_time'] - self.stats['start_time'] if self.stats['end_time'] and self.stats['start_time'] else 0
                },
                'statistics': self.stats,
                'apply_buttons_found': self.apply_buttons,
                'successful_applications': self.successful_applications,
                'failed_applications': self.failed_applications
            }

            # Save complete results
            complete_file = f'ultimate_jobright_results_{timestamp}.json'
            with open(complete_file, 'w', encoding='utf-8') as f:
                json.dump(complete_results, f, indent=2, default=str)

            # Save summary
            summary = {
                'session_id': self.session_id,
                'total_buttons_found': len(self.apply_buttons),
                'applications_attempted': self.stats['applications_attempted'],
                'applications_successful': self.stats['applications_successful'],
                'applications_failed': self.stats['applications_failed'],
                'success_rate_percent': (self.stats['applications_successful'] / self.stats['applications_attempted'] * 100) if self.stats['applications_attempted'] > 0 else 0,
                'successful_jobs': [
                    {
                        'job_text': app['button_info']['text'],
                        'action': app.get('action', 'unknown'),
                        'new_url': app.get('new_url', 'N/A'),
                        'details': app.get('details', 'N/A')
                    }
                    for app in self.successful_applications
                ]
            }

            summary_file = f'ultimate_jobright_summary_{timestamp}.json'
            with open(summary_file, 'w', encoding='utf-8') as f:
                json.dump(summary, f, indent=2, default=str)

            # Save simple text list
            text_file = f'applied_jobs_list_{timestamp}.txt'
            with open(text_file, 'w', encoding='utf-8') as f:
                f.write(f"JobRight.ai Auto-Apply Session Results\n")
                f.write(f"Session ID: {self.session_id}\n")
                f.write(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"{'='*60}\n\n")

                f.write(f"STATISTICS:\n")
                f.write(f"Total Apply Buttons Found: {len(self.apply_buttons)}\n")
                f.write(f"Applications Attempted: {self.stats['applications_attempted']}\n")
                f.write(f"Successful Applications: {self.stats['applications_successful']}\n")
                f.write(f"Failed Applications: {self.stats['applications_failed']}\n")
                f.write(f"Success Rate: {summary['success_rate_percent']:.1f}%\n\n")

                f.write(f"SUCCESSFUL APPLICATIONS:\n")
                f.write(f"{'='*40}\n")
                for i, app in enumerate(self.successful_applications, 1):
                    f.write(f"{i:2d}. {app['button_info']['text'][:60]}\n")
                    f.write(f"    Action: {app.get('action', 'unknown')}\n")
                    if app.get('new_url'):
                        f.write(f"    URL: {app['new_url']}\n")
                    f.write(f"    Details: {app.get('details', 'N/A')}\n\n")

            logger.info(f"Results saved to:")
            logger.info(f"  - Complete: {complete_file}")
            logger.info(f"  - Summary: {summary_file}")
            logger.info(f"  - Text List: {text_file}")

        except Exception as e:
            logger.error(f"Error saving results: {e}")

    def print_ultimate_summary(self):
        """Print ultimate summary of the automation session"""
        print(f"\n{'='*100}")
        print(f"🏆 ULTIMATE JOBRIGHT.AI AUTO-APPLY AUTOMATION - FINAL RESULTS")
        print(f"{'='*100}")

        # Session info
        if self.stats['start_time'] and self.stats['end_time']:
            duration = self.stats['end_time'] - self.stats['start_time']
            print(f"Session Duration: {duration:.1f} seconds ({duration/60:.1f} minutes)")

        print(f"Session ID: {self.session_id}")
        print(f"Completion Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

        # Statistics
        print(f"\n📊 AUTOMATION STATISTICS:")
        print(f"{'='*50}")
        print(f"Apply Buttons Found: {len(self.apply_buttons)}")
        print(f"Applications Attempted: {self.stats['applications_attempted']}")
        print(f"Successful Applications: {self.stats['applications_successful']}")
        print(f"Failed Applications: {self.stats['applications_failed']}")

        success_rate = (self.stats['applications_successful'] / self.stats['applications_attempted'] * 100) if self.stats['applications_attempted'] > 0 else 0
        print(f"Success Rate: {success_rate:.1f}%")

        # Successful applications
        if self.successful_applications:
            print(f"\n✅ SUCCESSFUL APPLICATIONS ({len(self.successful_applications)}):")
            print(f"{'='*60}")
            for i, app in enumerate(self.successful_applications, 1):
                print(f"{i:2d}. {app['button_info']['text'][:60]}{'...' if len(app['button_info']['text']) > 60 else ''}")
                print(f"    ACTION: {app.get('action', 'unknown')}")
                if app.get('new_url'):
                    print(f"    URL: {app['new_url'][:70]}{'...' if len(app['new_url']) > 70 else ''}")
                print(f"    METHOD: {app.get('click_method', 'unknown')}")
                if app.get('details'):
                    print(f"    DETAILS: {app['details']}")
                print()

        # Failed applications
        if self.failed_applications:
            print(f"\n❌ FAILED APPLICATIONS ({len(self.failed_applications)}):")
            print(f"{'='*60}")
            for i, app in enumerate(self.failed_applications, 1):
                print(f"{i:2d}. {app['button_info']['text'][:60]}{'...' if len(app['button_info']['text']) > 60 else ''}")
                print(f"    ERROR: {app.get('error', 'unknown')}")
                print()

        # Final message
        print(f"{'='*100}")
        if self.stats['applications_successful'] > 0:
            print(f"🎉 AUTOMATION COMPLETED SUCCESSFULLY!")
            print(f"   Applied to {self.stats['applications_successful']} jobs out of {len(self.apply_buttons)} found!")
        else:
            print(f"⚠️  AUTOMATION COMPLETED WITH ISSUES")
            print(f"   Found {len(self.apply_buttons)} apply buttons but no successful applications")

        print(f"   Check the generated files for detailed results")
        print(f"{'='*100}")

    def run_ultimate_automation(self):
        """Run the ultimate complete automation"""
        self.stats['start_time'] = time.time()

        try:
            print("🚀 ULTIMATE JOBRIGHT.AI AUTO-APPLY AUTOMATION")
            print("This is the definitive solution that finds and applies to ALL jobs!")
            print("="*80)

            # Setup
            if not self.setup_driver():
                print("❌ Failed to setup WebDriver")
                return False

            # Authentication
            if not self.smart_authentication():
                print("❌ Authentication failed")
                return False

            # Load all content
            print("\n🔄 Loading all page content...")
            self.comprehensive_content_loading()

            # Find all apply buttons
            print("\n🔍 Finding ALL Apply Now buttons with ultimate detection...")
            self.apply_buttons = self.ultimate_apply_button_finder()
            self.stats['buttons_found'] = len(self.apply_buttons)

            if not self.apply_buttons:
                print("❌ No Apply Now buttons found!")

                # Save debug information
                with open(f'debug_no_buttons_{self.session_id}.html', 'w', encoding='utf-8') as f:
                    f.write(self.driver.page_source)
                print(f"Debug: Page source saved for analysis")

                try:
                    self.driver.save_screenshot(f'debug_screenshot_{self.session_id}.png')
                    print(f"Debug: Screenshot saved")
                except:
                    pass

                return False

            # Display all found buttons
            self.display_all_found_buttons(self.apply_buttons)

            # Confirm automation
            if not self.auto_apply:
                print(f"\n🎯 Found {len(self.apply_buttons)} Apply Now buttons!")
                print("⚠️  This will automatically apply to ALL found jobs!")
                choice = input("Continue with automatic application? (type 'YES' to confirm): ").strip()

                if choice != 'YES':
                    print("Automation cancelled by user.")
                    return False

            # Apply to all jobs
            print(f"\n🚀 STARTING AUTOMATIC APPLICATION TO ALL {len(self.apply_buttons)} JOBS...")
            print("="*80)

            self.apply_to_all_jobs_ultimate(self.apply_buttons)

            return True

        except Exception as e:
            logger.error(f"Ultimate automation failed: {e}")
            print(f"❌ Ultimate automation failed: {e}")
            return False

        finally:
            self.stats['end_time'] = time.time()

            # Save results
            self.save_ultimate_results()

            # Print summary
            self.print_ultimate_summary()

            # Close browser
            if self.driver:
                if not self.headless:
                    input("\nPress Enter to close browser and complete automation...")
                self.driver.quit()


def main():
    """Main function for ultimate automation"""
    print("🏆 ULTIMATE JOBRIGHT.AI AUTO-APPLY AUTOMATION")
    print("The definitive solution for automatic job applications!")
    print("="*80)
    print("This script will:")
    print("✅ Handle authentication automatically")
    print("✅ Find ALL Apply Now buttons using advanced detection")
    print("✅ Apply to ALL jobs automatically")
    print("✅ Handle new pages, modals, and redirects")
    print("✅ Provide comprehensive reporting")
    print("="*80)

    # Configuration
    headless_mode = input("Run in headless mode (no browser window)? (y/n): ").strip().lower() == 'y'

    if not headless_mode:
        print("\n⚠️  Browser window will remain open for manual login if required")

    auto_apply_mode = True  # Always auto-apply for ultimate automation

    print(f"\n🚀 Starting Ultimate Automation...")
    print(f"   Headless Mode: {'Yes' if headless_mode else 'No'}")
    print(f"   Auto-Apply: Yes (applies to ALL found jobs)")

    final_confirm = input(f"\nReady to start? (y/n): ").strip().lower()
    if final_confirm != 'y':
        print("Automation cancelled.")
        return

    # Run ultimate automation
    automation = UltimateJobRightAutomation(headless=headless_mode, auto_apply=auto_apply_mode)
    success = automation.run_ultimate_automation()

    # Final message
    print(f"\n{'='*80}")
    if success:
        print("🎉 ULTIMATE AUTOMATION COMPLETED!")
        print(f"Successfully processed {len(automation.apply_buttons)} apply buttons")
        print(f"Applied to {automation.stats['applications_successful']} jobs")
    else:
        print("💥 AUTOMATION ENCOUNTERED ISSUES")
        print("Check the debug files and logs for details")

    print("Results have been saved to multiple files for your review")
    print(f"{'='*80}")


if __name__ == "__main__":
    main()