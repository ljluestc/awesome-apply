#!/usr/bin/env python3
"""
Selenium-based JobRight.ai Scraper
Handles JavaScript rendering and dynamic content loading
"""

import json
import time
import re
from datetime import datetime
import logging
from urllib.parse import urljoin

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

try:
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.common.action_chains import ActionChains
    from selenium.common.exceptions import TimeoutException, NoSuchElementException
    SELENIUM_AVAILABLE = True
except ImportError:
    SELENIUM_AVAILABLE = False
    logger.warning("Selenium not available. Install with: pip install selenium")

class SeleniumJobRightScraper:
    def __init__(self):
        self.base_url = "https://jobright.ai"
        self.recommend_url = "https://jobright.ai/jobs/recommend"
        self.driver = None
        self.job_links = []
        self.job_data = []

    def setup_driver(self):
        """Setup Chrome driver with appropriate options"""
        if not SELENIUM_AVAILABLE:
            raise ImportError("Selenium not available")

        chrome_options = Options()
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")

        # Add these for headless operation if needed
        # chrome_options.add_argument("--headless")

        try:
            self.driver = webdriver.Chrome(options=chrome_options)
            self.driver.set_page_load_timeout(30)
            logger.info("Chrome driver initialized successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to initialize Chrome driver: {e}")
            return False

    def wait_for_page_load(self, timeout=20):
        """Wait for page to fully load including JavaScript"""
        try:
            # Wait for page to load
            WebDriverWait(self.driver, timeout).until(
                lambda driver: driver.execute_script("return document.readyState") == "complete"
            )

            # Additional wait for potential AJAX content
            time.sleep(3)

            return True
        except TimeoutException:
            logger.warning("Page load timeout")
            return False

    def scroll_and_load_content(self):
        """Scroll through page to trigger lazy loading"""
        logger.info("Scrolling to load dynamic content...")

        # Get initial page height
        last_height = self.driver.execute_script("return document.body.scrollHeight")

        scroll_attempts = 0
        max_scrolls = 10

        while scroll_attempts < max_scrolls:
            # Scroll down to bottom
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")

            # Wait for new content to load
            time.sleep(2)

            # Calculate new scroll height
            new_height = self.driver.execute_script("return document.body.scrollHeight")

            if new_height == last_height:
                break

            last_height = new_height
            scroll_attempts += 1
            logger.info(f"Scroll attempt {scroll_attempts}, page height: {new_height}")

        # Scroll back to top
        self.driver.execute_script("window.scrollTo(0, 0);")
        time.sleep(1)

    def extract_job_cards(self):
        """Extract job information from job cards"""
        logger.info("Extracting job cards...")

        job_cards = []

        # Try multiple selectors for job cards
        card_selectors = [
            "[class*='job-card']",
            "[class*='JobCard']",
            "[class*='job-item']",
            "[class*='recommendation']",
            ".ant-card",
            "[data-testid*='job']",
            "article",
            "[role='article']"
        ]

        for selector in card_selectors:
            try:
                elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                if elements:
                    logger.info(f"Found {len(elements)} elements with selector: {selector}")

                    for element in elements:
                        try:
                            job_info = self.extract_job_info_from_element(element)
                            if job_info:
                                job_cards.append(job_info)
                        except Exception as e:
                            logger.debug(f"Error extracting from element: {e}")
                            continue

            except Exception as e:
                logger.debug(f"Selector {selector} failed: {e}")
                continue

        return job_cards

    def extract_job_info_from_element(self, element):
        """Extract job information from a single element"""
        job_info = {}

        try:
            # Try to get job title
            title_selectors = ["h1", "h2", "h3", "h4", "[class*='title']", "[class*='name']"]
            for selector in title_selectors:
                try:
                    title_elem = element.find_element(By.CSS_SELECTOR, selector)
                    job_info['title'] = title_elem.text.strip()
                    break
                except:
                    continue

            # Try to get company name
            company_selectors = ["[class*='company']", "[class*='employer']", "span", "div"]
            for selector in company_selectors:
                try:
                    elements = element.find_elements(By.CSS_SELECTOR, selector)
                    for elem in elements:
                        text = elem.text.strip()
                        if text and not job_info.get('company') and len(text) < 100:
                            job_info['company'] = text
                            break
                    if job_info.get('company'):
                        break
                except:
                    continue

            # Try to get job links
            link_elements = element.find_elements(By.TAG_NAME, "a")
            links = []
            for link in link_elements:
                href = link.get_attribute('href')
                if href:
                    links.append(href)

            job_info['links'] = links

            # Get element HTML for further analysis
            job_info['html_snippet'] = element.get_attribute('outerHTML')[:500]

            # Get all data attributes
            data_attrs = {}
            for attr in element.get_property('attributes') or []:
                attr_name = attr.get('name', '')
                if attr_name.startswith('data-'):
                    data_attrs[attr_name] = element.get_attribute(attr_name)

            job_info['data_attributes'] = data_attrs

            return job_info if job_info.get('title') or job_info.get('links') else None

        except Exception as e:
            logger.debug(f"Error extracting job info: {e}")
            return None

    def extract_all_links(self):
        """Extract all links from the page"""
        logger.info("Extracting all links from page...")

        links = []
        try:
            link_elements = self.driver.find_elements(By.TAG_NAME, "a")
            for element in link_elements:
                href = element.get_attribute('href')
                if href:
                    text = element.text.strip()
                    links.append({
                        'url': href,
                        'text': text,
                        'class': element.get_attribute('class'),
                        'data_attributes': self.get_data_attributes(element)
                    })

            logger.info(f"Found {len(links)} total links")
            return links

        except Exception as e:
            logger.error(f"Error extracting links: {e}")
            return []

    def get_data_attributes(self, element):
        """Get all data attributes from an element"""
        data_attrs = {}
        try:
            for attr in element.get_property('attributes') or []:
                attr_name = attr.get('name', '')
                if attr_name.startswith('data-'):
                    data_attrs[attr_name] = element.get_attribute(attr_name)
        except:
            pass
        return data_attrs

    def capture_network_requests(self):
        """Capture network requests to find API calls"""
        logger.info("Analyzing network requests...")

        try:
            # Get performance logs
            logs = self.driver.get_log('performance')
            network_requests = []

            for entry in logs:
                message = json.loads(entry['message'])
                if message.get('message', {}).get('method') == 'Network.requestWillBeSent':
                    request = message['message']['params']['request']
                    url = request.get('url', '')
                    if 'job' in url.lower() or 'api' in url.lower():
                        network_requests.append({
                            'url': url,
                            'method': request.get('method', ''),
                            'headers': request.get('headers', {})
                        })

            logger.info(f"Found {len(network_requests)} relevant network requests")
            return network_requests

        except Exception as e:
            logger.warning(f"Could not capture network requests: {e}")
            return []

    def run_extraction(self):
        """Run the complete extraction process"""
        if not self.setup_driver():
            return None

        try:
            logger.info(f"Navigating to {self.recommend_url}")
            self.driver.get(self.recommend_url)

            if not self.wait_for_page_load():
                logger.warning("Page may not have loaded completely")

            # Scroll to load dynamic content
            self.scroll_and_load_content()

            # Extract job cards
            job_cards = self.extract_job_cards()

            # Extract all links
            all_links = self.extract_all_links()

            # Capture network requests
            network_requests = self.capture_network_requests()

            # Get page source for additional analysis
            page_source = self.driver.page_source

            results = {
                'timestamp': datetime.now().isoformat(),
                'source_url': self.recommend_url,
                'extraction_method': 'selenium',
                'job_cards': job_cards,
                'all_links': all_links,
                'network_requests': network_requests,
                'page_title': self.driver.title,
                'current_url': self.driver.current_url,
                'total_job_cards': len(job_cards),
                'total_links': len(all_links),
                'page_source_length': len(page_source)
            }

            logger.info(f"Extraction complete. Found {len(job_cards)} job cards and {len(all_links)} links")
            return results, page_source

        except Exception as e:
            logger.error(f"Extraction failed: {e}")
            return None, None

        finally:
            if self.driver:
                self.driver.quit()

    def save_results(self, results, page_source=None):
        """Save results to files"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # Save main results
        json_file = f"/home/calelin/awesome-apply/selenium_jobright_{timestamp}.json"
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)

        # Save page source
        if page_source:
            html_file = f"/home/calelin/awesome-apply/jobright_page_source_{timestamp}.html"
            with open(html_file, 'w', encoding='utf-8') as f:
                f.write(page_source)
        else:
            html_file = None

        # Create summary text file
        txt_file = f"/home/calelin/awesome-apply/selenium_jobright_summary_{timestamp}.txt"
        with open(txt_file, 'w', encoding='utf-8') as f:
            f.write("JobRight.ai Selenium Extraction Summary\n")
            f.write("="*50 + "\n")
            f.write(f"Timestamp: {results['timestamp']}\n")
            f.write(f"Source URL: {results['source_url']}\n")
            f.write(f"Job Cards Found: {results['total_job_cards']}\n")
            f.write(f"Total Links Found: {results['total_links']}\n\n")

            # Job cards section
            f.write("JOB CARDS:\n")
            f.write("-" * 20 + "\n")
            for i, card in enumerate(results['job_cards'], 1):
                f.write(f"{i}. {card.get('title', 'No Title')}\n")
                f.write(f"   Company: {card.get('company', 'Unknown')}\n")
                if card.get('links'):
                    f.write(f"   Links: {len(card['links'])} found\n")
                    for link in card['links'][:3]:  # Show first 3 links
                        f.write(f"     - {link}\n")
                f.write("\n")

            # All links section
            f.write("\nALL LINKS:\n")
            f.write("-" * 20 + "\n")
            for i, link in enumerate(results['all_links'], 1):
                f.write(f"{i:3d}. {link['url']}\n")
                if link.get('text'):
                    f.write(f"     Text: {link['text'][:50]}...\n")

        return json_file, txt_file, html_file

def main():
    """Main execution function"""
    if not SELENIUM_AVAILABLE:
        print("Error: Selenium not available. Install with: pip install selenium")
        print("Also ensure Chrome/Chromium and ChromeDriver are installed.")
        return

    scraper = SeleniumJobRightScraper()
    results, page_source = scraper.run_extraction()

    if results:
        json_file, txt_file, html_file = scraper.save_results(results, page_source)

        print(f"\nSelenium Extraction Results:")
        print(f"Job cards found: {results['total_job_cards']}")
        print(f"Total links found: {results['total_links']}")
        print(f"Files saved:")
        print(f"  JSON: {json_file}")
        print(f"  Summary: {txt_file}")
        if html_file:
            print(f"  HTML Source: {html_file}")
    else:
        print("Extraction failed!")

if __name__ == "__main__":
    main()