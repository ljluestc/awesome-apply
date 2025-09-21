#!/usr/bin/env python3
"""
HYBRID JOB APPLICATION AUTOMATION
Combines comprehensive search with intelligent job filtering
Balance between finding jobs and applying to actual positions
"""

import sys
import os
import time
import json
import logging
import random
import traceback
from datetime import datetime
from typing import List, Dict, Any, Optional

# Add venv path
sys.path.append('/home/calelin/awesome-apply/venv/lib/python3.13/site-packages')

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import *
import urllib.parse

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('hybrid_job_applier.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class HybridJobApplier:
    def __init__(self):
        """Initialize hybrid job application automation"""
        self.driver = None
        self.session_id = datetime.now().strftime('%Y%m%d_%H%M%S')

        # Success tracking
        self.applied_jobs = []
        self.session_stats = {
            'start_time': time.time(),
            'platforms_tried': 0,
            'elements_found': 0,
            'job_applications': 0,
            'external_links_opened': 0,
            'failed_attempts': 0
        }

        # Comprehensive platform list
        self.platforms = [
            {
                'name': 'JobRight_EntryLevel',
                'url': 'https://jobright.ai/entry-level-jobs',
                'strategy': 'comprehensive_with_filtering'
            },
            {
                'name': 'JobRight_SoftwareSearch',
                'url': 'https://jobright.ai/s?keyword=software%20engineer&location=San%20Jose%2C%20CA',
                'strategy': 'comprehensive_with_filtering'
            },
            {
                'name': 'LinkedIn_Jobs',
                'url': 'https://www.linkedin.com/jobs/search?keywords=software&location=San%20Jose%2C%20CA&distance=25&f_TPR=r86400',
                'strategy': 'linkedin_specific'
            },
            {
                'name': 'Indeed_Jobs',
                'url': 'https://indeed.com/jobs?q=software+engineer&l=San+Jose%2C+CA&fromage=1',
                'strategy': 'indeed_specific'
            }
        ]

    def setup_driver(self):
        """Setup Chrome WebDriver"""
        try:
            chrome_options = Options()

            # Use persistent profile
            user_data_dir = f"/tmp/chrome_hybrid_{self.session_id}"
            chrome_options.add_argument(f"--user-data-dir={user_data_dir}")
            chrome_options.add_argument("--profile-directory=Default")

            # Optimization
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

            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

            logger.info("✅ WebDriver setup successfully")
            return True

        except Exception as e:
            logger.error(f"❌ Failed to setup WebDriver: {e}")
            return False

    def wait_random(self, min_seconds=2, max_seconds=5):
        """Human-like random wait"""
        wait_time = random.uniform(min_seconds, max_seconds)
        time.sleep(wait_time)

    def intelligent_scroll(self):
        """Intelligent scrolling to load content"""
        try:
            # Initial scroll to load content
            for i in range(6):
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                self.wait_random(2, 3)

            logger.info("📜 Intelligent scrolling completed")

        except Exception as e:
            logger.error(f"❌ Error during scrolling: {e}")

    def find_all_interactive_elements(self):
        """Find all potentially useful interactive elements"""
        try:
            interactive_elements = []

            # Comprehensive selectors for different types of elements
            selectors = [
                # Direct apply buttons and links
                "button",
                "a[href]",
                "[role='button']",
                "input[type='submit']",

                # Specific job-related selectors
                "*[class*='apply']",
                "*[class*='job']",
                "*[data-testid*='apply']",
                "*[data-testid*='job']",
                "*[id*='apply']",
                "*[id*='job']",
                "*[aria-label*='apply']",
                "*[aria-label*='Apply']",

                # Generic clickable elements
                "*[onclick]",
                "*[data-tracking-control-name]",
                ".card",
                ".item",
                ".link"
            ]

            # Find elements using each selector
            for selector in selectors:
                try:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    for element in elements:
                        if element.is_displayed() and element.is_enabled():
                            try:
                                text = element.text.strip()
                                href = element.get_attribute('href') or ''
                                classes = element.get_attribute('class') or ''
                                onclick = element.get_attribute('onclick') or ''
                                aria_label = element.get_attribute('aria-label') or ''

                                # Basic filtering - remove obviously non-job elements
                                if self.is_potentially_useful(text, href, classes, onclick, aria_label):
                                    interactive_elements.append({
                                        'element': element,
                                        'text': text,
                                        'href': href,
                                        'classes': classes,
                                        'onclick': onclick,
                                        'aria_label': aria_label,
                                        'selector': selector,
                                        'score': self.score_element(text, href, classes, onclick, aria_label)
                                    })

                            except Exception:
                                continue

                except Exception:
                    continue

            # Sort by score (higher score = more likely to be useful)
            interactive_elements.sort(key=lambda x: x['score'], reverse=True)

            # Remove duplicates (same element found by multiple selectors)
            unique_elements = []
            seen_elements = set()

            for elem_info in interactive_elements:
                elem = elem_info['element']
                if elem not in seen_elements:
                    seen_elements.add(elem)
                    unique_elements.append(elem_info)

            logger.info(f"🔍 Found {len(unique_elements)} potentially useful interactive elements")
            return unique_elements

        except Exception as e:
            logger.error(f"❌ Error finding interactive elements: {e}")
            return []

    def is_potentially_useful(self, text: str, href: str, classes: str, onclick: str, aria_label: str) -> bool:
        """Basic filtering to remove obviously non-useful elements"""
        try:
            combined_text = f"{text} {href} {classes} {onclick} {aria_label}".lower()

            # Exclude obvious non-job elements
            exclude_keywords = [
                'cookie', 'privacy', 'terms', 'policy', 'about', 'contact', 'help',
                'support', 'login', 'signup', 'register', 'search', 'filter',
                'sort', 'menu', 'navigation', 'nav', 'footer', 'header',
                'sidebar', 'toggle', 'close', 'dismiss', 'cancel'
            ]

            # If element contains exclude keywords and no useful keywords, skip it
            has_exclude = any(keyword in combined_text for keyword in exclude_keywords)

            # Include keywords that suggest usefulness
            include_keywords = [
                'apply', 'job', 'position', 'career', 'opportunity', 'role',
                'hire', 'work', 'company', 'submit', 'send', 'view', 'details',
                'engineer', 'developer', 'analyst', 'manager', 'intern'
            ]

            has_include = any(keyword in combined_text for keyword in include_keywords)

            # Include if it has useful keywords, or if it doesn't have exclude keywords
            return has_include or not has_exclude

        except Exception:
            return True  # If unsure, include it

    def score_element(self, text: str, href: str, classes: str, onclick: str, aria_label: str) -> int:
        """Score element based on how likely it is to be useful for job applications"""
        try:
            score = 0
            combined_text = f"{text} {href} {classes} {onclick} {aria_label}".lower()

            # High-value keywords
            high_value = ['apply', 'submit application', 'easy apply', 'quick apply', 'apply now']
            for keyword in high_value:
                if keyword in combined_text:
                    score += 10

            # Medium-value keywords
            medium_value = ['job', 'position', 'career', 'opportunity', 'role', 'hire', 'work']
            for keyword in medium_value:
                if keyword in combined_text:
                    score += 5

            # Job title keywords
            job_titles = ['engineer', 'developer', 'analyst', 'manager', 'specialist', 'coordinator', 'intern']
            for title in job_titles:
                if title in combined_text:
                    score += 3

            # External links bonus
            if 'target="_blank"' in str(onclick) or href.startswith('http') and 'apply' in href:
                score += 5

            # Button elements get a small bonus
            if 'button' in classes or onclick:
                score += 2

            # Penalty for obvious non-job elements
            penalties = ['cookie', 'privacy', 'menu', 'navigation', 'footer', 'header']
            for penalty in penalties:
                if penalty in combined_text:
                    score -= 5

            return max(0, score)  # Ensure non-negative score

        except Exception:
            return 1  # Default score

    def smart_click_element(self, element_info: Dict[str, Any]) -> bool:
        """Smart clicking with multiple strategies"""
        try:
            element = element_info['element']

            # Scroll to element
            self.driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", element)
            self.wait_random(1, 2)

            # Multiple click strategies
            strategies = [
                lambda: element.click(),
                lambda: self.driver.execute_script("arguments[0].click();", element),
                lambda: ActionChains(self.driver).move_to_element(element).click().perform(),
                lambda: element.send_keys(Keys.ENTER),
                lambda: self.driver.execute_script("arguments[0].focus(); arguments[0].click();", element)
            ]

            for i, strategy in enumerate(strategies):
                try:
                    strategy()
                    logger.info(f"✅ Click strategy {i+1} successful")
                    return True
                except Exception:
                    continue

            logger.warning("⚠️ All click strategies failed")
            return False

        except Exception as e:
            logger.error(f"❌ Error in smart click: {e}")
            return False

    def verify_action_success(self, original_url: str, element_info: Dict[str, Any]) -> bool:
        """Verify if clicking the element resulted in a successful action"""
        try:
            self.wait_random(3, 5)

            current_url = self.driver.current_url
            current_title = self.driver.title
            window_count = len(self.driver.window_handles)

            # Success indicators
            url_changed = current_url != original_url
            new_window = window_count > 1

            # Check for job/application-related content
            page_content = self.driver.page_source.lower()
            application_indicators = [
                'apply', 'application', 'job', 'position', 'career',
                'resume', 'cv', 'submit', 'hiring', 'recruit'
            ]

            content_relevant = any(indicator in page_content for indicator in application_indicators)

            # Check URL for application-related keywords
            url_relevant = any(indicator in current_url.lower() for indicator in application_indicators)

            # Check title for application-related keywords
            title_relevant = any(indicator in current_title.lower() for indicator in application_indicators)

            # Determine success
            is_successful = (url_changed and (content_relevant or url_relevant or title_relevant)) or new_window

            if is_successful:
                logger.info("🎉 ✅ ACTION SUCCESS DETECTED!")
                logger.info(f"    URL changed: {url_changed}")
                logger.info(f"    New window: {new_window}")
                logger.info(f"    Content relevant: {content_relevant}")
                logger.info(f"    Current URL: {current_url}")
                logger.info(f"    Page title: {current_title}")

                # Handle new window
                if new_window:
                    try:
                        self.driver.switch_to.window(self.driver.window_handles[-1])
                        self.wait_random(3, 5)

                        # Check if it's a useful page
                        new_url = self.driver.current_url
                        new_title = self.driver.title

                        logger.info(f"    New window URL: {new_url}")
                        logger.info(f"    New window title: {new_title}")

                        # Look for additional apply opportunities
                        additional_applies = self.find_all_interactive_elements()
                        if additional_applies:
                            logger.info(f"    Found {len(additional_applies)} additional elements in new window")

                            # Try the top-scored element
                            for apply_elem in additional_applies[:3]:
                                if apply_elem['score'] >= 5:  # Only try high-scoring elements
                                    if self.smart_click_element(apply_elem):
                                        logger.info("    ✅ Successfully clicked additional element")
                                        break

                        # Close new window and return
                        self.wait_random(2, 3)
                        self.driver.close()
                        self.driver.switch_to.window(self.driver.window_handles[0])

                        self.session_stats['external_links_opened'] += 1

                    except Exception as e:
                        logger.warning(f"    ⚠️ Error handling new window: {e}")
                        try:
                            self.driver.switch_to.window(self.driver.window_handles[0])
                        except:
                            pass

                # Record success
                self.applied_jobs.append({
                    'timestamp': datetime.now().isoformat(),
                    'element_text': element_info['text'][:100],
                    'original_url': original_url,
                    'result_url': current_url,
                    'result_title': current_title,
                    'element_score': element_info['score'],
                    'success_type': 'new_window' if new_window else 'navigation'
                })

                self.session_stats['job_applications'] += 1
                return True

            else:
                logger.info("ℹ️ Action completed but no clear success indicators")
                return False

        except Exception as e:
            logger.error(f"❌ Error verifying action success: {e}")
            return False

    def process_platform(self, platform: Dict[str, str]) -> int:
        """Process a platform with hybrid approach"""
        try:
            logger.info(f"\n🎯 PROCESSING PLATFORM: {platform['name']}")
            logger.info(f"🔗 URL: {platform['url']}")
            logger.info(f"📋 Strategy: {platform['strategy']}")
            logger.info("=" * 60)

            # Navigate to platform
            self.driver.get(platform['url'])
            self.wait_random(5, 8)

            logger.info(f"📍 Arrived at: {self.driver.current_url}")
            logger.info(f"📑 Page title: {self.driver.title}")

            # Load content
            self.intelligent_scroll()

            # Find interactive elements
            interactive_elements = self.find_all_interactive_elements()

            if not interactive_elements:
                logger.warning(f"⚠️ No interactive elements found on {platform['name']}")
                return 0

            self.session_stats['elements_found'] += len(interactive_elements)
            successful_actions = 0

            # Process elements by score (highest first)
            for i, element_info in enumerate(interactive_elements):
                try:
                    logger.info(f"\n[ELEMENT {i+1}/{len(interactive_elements)}] Score: {element_info['score']}")
                    logger.info(f"Text: '{element_info['text'][:80]}'")
                    logger.info(f"Href: {element_info['href'][:60]}")

                    # Skip very low-scoring elements
                    if element_info['score'] < 1:
                        logger.info("⏩ Skipping low-score element")
                        continue

                    original_url = self.driver.current_url
                    original_window_count = len(self.driver.window_handles)

                    # Try to click the element
                    if self.smart_click_element(element_info):
                        # Verify success
                        if self.verify_action_success(original_url, element_info):
                            successful_actions += 1
                            logger.info(f"✅ SUCCESSFUL ACTION #{successful_actions}")

                            # Check if we should continue
                            if successful_actions >= 10:
                                logger.info("\n🎉 REACHED ACTION GOAL FOR THIS PLATFORM!")
                                break
                        else:
                            logger.info("ℹ️ Click successful but no clear result")
                            self.session_stats['failed_attempts'] += 1
                    else:
                        logger.info("⚠️ Failed to click element")
                        self.session_stats['failed_attempts'] += 1

                    # Brief delay between attempts
                    self.wait_random(2, 4)

                    # Return to original page if needed
                    if self.driver.current_url != original_url:
                        try:
                            self.driver.get(platform['url'])
                            self.wait_random(3, 5)
                            break  # Start fresh with new elements
                        except Exception:
                            pass

                except Exception as e:
                    logger.error(f"❌ Error processing element {i+1}: {e}")
                    continue

            logger.info(f"\n📊 PLATFORM RESULTS: {platform['name']}")
            logger.info(f"    ✅ Successful actions: {successful_actions}")
            logger.info(f"    📋 Elements processed: {len(interactive_elements)}")
            logger.info(f"    📈 Success rate: {(successful_actions/len(interactive_elements)*100):.1f}%" if interactive_elements else "0%")

            return successful_actions

        except Exception as e:
            logger.error(f"❌ Error processing platform {platform['name']}: {e}")
            return 0

    def run_hybrid_automation(self):
        """Main hybrid automation"""
        logger.info("🚀 HYBRID JOB APPLICATION AUTOMATION")
        logger.info("🎯 Comprehensive search with intelligent filtering")
        logger.info("⚡ Balanced approach for maximum success")
        logger.info("=" * 80)

        try:
            if not self.setup_driver():
                return False

            total_successful_actions = 0

            # Process each platform
            for platform in self.platforms:
                try:
                    self.session_stats['platforms_tried'] += 1

                    successful_actions = self.process_platform(platform)
                    total_successful_actions += successful_actions

                    # Progress update
                    runtime = (time.time() - self.session_stats['start_time']) / 60
                    logger.info(f"\n📊 OVERALL PROGRESS:")
                    logger.info(f"    🏢 Platforms tried: {self.session_stats['platforms_tried']}")
                    logger.info(f"    🔍 Elements found: {self.session_stats['elements_found']}")
                    logger.info(f"    ✅ Successful actions: {total_successful_actions}")
                    logger.info(f"    🔗 External links opened: {self.session_stats['external_links_opened']}")
                    logger.info(f"    ❌ Failed attempts: {self.session_stats['failed_attempts']}")
                    logger.info(f"    ⏱️ Runtime: {runtime:.1f} minutes")

                    # Check if goal reached
                    if total_successful_actions >= 20:
                        logger.info("\n🎉 🎉 🎉 MISSION ACCOMPLISHED! 🎉 🎉 🎉")
                        logger.info(f"✅ Successfully completed {total_successful_actions} actions!")
                        break

                except Exception as e:
                    logger.error(f"❌ Error with platform {platform['name']}: {e}")
                    continue

            # Final results
            logger.info("\n🏁 HYBRID AUTOMATION COMPLETED")
            logger.info(f"✅ Total successful actions: {total_successful_actions}")

            if self.applied_jobs:
                logger.info("\n📋 SUCCESSFUL ACTIONS:")
                for i, action in enumerate(self.applied_jobs, 1):
                    logger.info(f"  {i:2d}. Element: {action['element_text']}")
                    logger.info(f"      Result URL: {action['result_url']}")
                    logger.info(f"      Type: {action['success_type']}")
                    logger.info(f"      Score: {action['element_score']}")
                    logger.info(f"      Time: {action['timestamp']}")
                    logger.info("")

            return total_successful_actions > 0

        except Exception as e:
            logger.error(f"❌ Fatal automation error: {e}")
            traceback.print_exc()
            return False

    def cleanup(self):
        """Clean up resources"""
        if self.driver:
            try:
                self.driver.quit()
                logger.info("🧹 Resources cleaned up")
            except:
                pass

def main():
    applier = HybridJobApplier()

    try:
        logger.info("🌟 HYBRID JOB APPLICATION AUTOMATION")
        logger.info("🎯 Comprehensive search with intelligent scoring")

        success = applier.run_hybrid_automation()

        if success:
            logger.info("\n🎉 🎉 🎉 SUCCESS! 🎉 🎉 🎉")
            logger.info("✅ Successfully completed job application actions!")
        else:
            logger.warning("\n⚠️ No successful actions completed")

    except KeyboardInterrupt:
        logger.info("\n⏹️ Automation stopped by user")
    except Exception as e:
        logger.error(f"\n❌ Fatal error: {e}")
        traceback.print_exc()
    finally:
        applier.cleanup()

        # Final stats
        runtime = (time.time() - applier.session_stats['start_time']) / 60
        logger.info("\n" + "="*60)
        logger.info("📊 FINAL STATISTICS")
        logger.info("="*60)
        logger.info(f"✅ Successful actions: {applier.session_stats['job_applications']}")
        logger.info(f"🔍 Elements found: {applier.session_stats['elements_found']}")
        logger.info(f"🔗 External links opened: {applier.session_stats['external_links_opened']}")
        logger.info(f"🏢 Platforms tried: {applier.session_stats['platforms_tried']}")
        logger.info(f"❌ Failed attempts: {applier.session_stats['failed_attempts']}")
        logger.info(f"⏱️ Total runtime: {runtime:.1f} minutes")

if __name__ == "__main__":
    main()