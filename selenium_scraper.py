#!/usr/bin/env python3
"""
JobRight.ai Job Scraper with Selenium
Identifies all 'Apply with autofill' buttons and their target pages using browser automation
"""

import json
import time
import re
from urllib.parse import urljoin, urlparse
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException

class JobRightSeleniumScraper:
    def __init__(self):
        self.base_url = "https://jobright.ai"
        self.jobs_data = []
        self.driver = None
        
    def setup_driver(self):
        """Setup Chrome driver with appropriate options"""
        chrome_options = Options()
        chrome_options.add_argument("--headless")  # Run in background
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")
        
        try:
            self.driver = webdriver.Chrome(options=chrome_options)
            return True
        except Exception as e:
            print(f"Error setting up Chrome driver: {e}")
            print("Trying Firefox...")
            try:
                from selenium.webdriver.firefox.options import Options as FirefoxOptions
                firefox_options = FirefoxOptions()
                firefox_options.add_argument("--headless")
                self.driver = webdriver.Firefox(options=firefox_options)
                return True
            except Exception as e2:
                print(f"Error setting up Firefox driver: {e2}")
                return False
    
    def scrape_job_page(self, url):
        """Scrape the job recommendation page using Selenium"""
        if not self.setup_driver():
            print("Failed to setup webdriver")
            return []
        
        try:
            print(f"Loading page: {url}")
            self.driver.get(url)
            
            # Wait for page to load
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            # Wait a bit more for dynamic content
            time.sleep(3)
            
            # Scroll to load more content
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)
            
            # Look for various patterns of "Apply with autofill" buttons
            autofill_buttons = []
            
            # Search by text content
            try:
                buttons_by_text = self.driver.find_elements(By.XPATH, 
                    "//*[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'apply') and contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'autofill')]")
                autofill_buttons.extend(buttons_by_text)
            except:
                pass
            
            # Search by partial text
            try:
                buttons_partial = self.driver.find_elements(By.XPATH, 
                    "//*[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'autofill')]")
                autofill_buttons.extend(buttons_partial)
            except:
                pass
            
            # Search by class names
            try:
                buttons_by_class = self.driver.find_elements(By.XPATH, 
                    "//*[contains(@class, 'apply') or contains(@class, 'autofill')]")
                autofill_buttons.extend(buttons_by_class)
            except:
                pass
            
            # Search by data attributes
            try:
                buttons_by_data = self.driver.find_elements(By.XPATH, 
                    "//*[contains(@data-action, 'apply') or contains(@data-action, 'autofill')]")
                autofill_buttons.extend(buttons_by_data)
            except:
                pass
            
            # Search for all buttons and links
            try:
                all_buttons = self.driver.find_elements(By.TAG_NAME, "button")
                all_links = self.driver.find_elements(By.TAG_NAME, "a")
                all_clickable = self.driver.find_elements(By.XPATH, "//*[@onclick or @href]")
                autofill_buttons.extend(all_buttons + all_links + all_clickable)
            except:
                pass
            
            # Remove duplicates
            autofill_buttons = list(set(autofill_buttons))
            
            print(f"Found {len(autofill_buttons)} potential elements")
            
            # Analyze each element
            for i, element in enumerate(autofill_buttons):
                try:
                    button_info = self.analyze_element(element, i)
                    if button_info and self.is_autofill_button(button_info):
                        self.jobs_data.append(button_info)
                except Exception as e:
                    print(f"Error analyzing element {i}: {e}")
                    continue
            
            return self.jobs_data
            
        except Exception as e:
            print(f"Error scraping {url}: {str(e)}")
            return []
        finally:
            if self.driver:
                self.driver.quit()
    
    def is_autofill_button(self, button_info):
        """Check if this element is likely an autofill button"""
        text = button_info.get('text', '').lower()
        classes = ' '.join(button_info.get('classes', [])).lower()
        onclick = button_info.get('onclick', '').lower()
        
        # Check for autofill-related keywords
        autofill_keywords = ['autofill', 'auto-fill', 'auto fill', 'apply', 'quick apply']
        
        return any(keyword in text or keyword in classes or keyword in onclick for keyword in autofill_keywords)
    
    def analyze_element(self, element, index):
        """Analyze an element to extract its properties"""
        try:
            element_info = {
                'index': index,
                'tag': element.tag_name,
                'text': element.text.strip(),
                'classes': element.get_attribute('class').split() if element.get_attribute('class') else [],
                'id': element.get_attribute('id') or '',
                'href': element.get_attribute('href') or '',
                'onclick': element.get_attribute('onclick') or '',
                'data_attributes': {},
                'target_url': '',
                'is_displayed': element.is_displayed(),
                'is_enabled': element.is_enabled(),
                'location': element.location,
                'size': element.size,
                'parent_info': ''
            }
            
            # Extract data attributes
            try:
                attributes = self.driver.execute_script("""
                    var attrs = {};
                    for (var i = 0; i < arguments[0].attributes.length; i++) {
                        var attr = arguments[0].attributes[i];
                        if (attr.name.startsWith('data-')) {
                            attrs[attr.name] = attr.value;
                        }
                    }
                    return attrs;
                """, element)
                element_info['data_attributes'] = attributes
            except:
                pass
            
            # Extract href and create target URL
            if element_info['href']:
                element_info['target_url'] = urljoin(self.base_url, element_info['href'])
            
            # Get parent element info
            try:
                parent = element.find_element(By.XPATH, "..")
                element_info['parent_info'] = {
                    'tag': parent.tag_name,
                    'class': parent.get_attribute('class') or '',
                    'id': parent.get_attribute('id') or '',
                    'text': parent.text.strip()[:100] + '...' if len(parent.text.strip()) > 100 else parent.text.strip()
                }
            except:
                pass
            
            # Extract job information from context
            job_info = self.extract_job_info_from_element(element)
            element_info.update(job_info)
            
            return element_info
            
        except Exception as e:
            print(f"Error analyzing element {index}: {str(e)}")
            return None
    
    def extract_job_info_from_element(self, element):
        """Extract job information from the element's context"""
        job_info = {
            'job_title': '',
            'company': '',
            'location': '',
            'job_id': ''
        }
        
        try:
            # Look for job information in nearby elements
            current = element
            for _ in range(3):  # Check up to 3 parent levels
                try:
                    parent = current.find_element(By.XPATH, "..")
                    text = parent.text.strip()
                    
                    # Look for job title patterns
                    if not job_info['job_title'] and len(text) > 10 and len(text) < 200:
                        if any(keyword in text.lower() for keyword in 
                               ['engineer', 'developer', 'manager', 'analyst', 'specialist', 'coordinator', 'director', 'lead']):
                            job_info['job_title'] = text.split('\n')[0]  # Take first line
                    
                    # Look for company name
                    if not job_info['company'] and ' at ' in text.lower():
                        parts = text.split(' at ')
                        if len(parts) > 1:
                            job_info['company'] = parts[1].split('\n')[0].strip()
                    
                    # Look for location
                    if not job_info['location']:
                        location_keywords = ['remote', 'hybrid', 'new york', 'california', 'texas', 'florida', 'washington', 'chicago']
                        for keyword in location_keywords:
                            if keyword in text.lower():
                                job_info['location'] = keyword.title()
                                break
                    
                    current = parent
                except:
                    break
            
            # Look for job ID in data attributes
            for attr, value in element_info.get('data_attributes', {}).items():
                if 'job' in attr.lower() and 'id' in attr.lower():
                    job_info['job_id'] = value
                    break
            
        except Exception as e:
            print(f"Error extracting job info: {str(e)}")
        
        return job_info
    
    def test_target_urls(self):
        """Test the target URLs to see if they're accessible"""
        print("\nTesting target URLs...")
        for job in self.jobs_data:
            if job['target_url']:
                try:
                    # Use requests to test the URL
                    import requests
                    response = requests.head(job['target_url'], timeout=10, allow_redirects=True)
                    job['url_status'] = response.status_code
                    job['url_accessible'] = response.status_code < 400
                except:
                    job['url_status'] = 'Error'
                    job['url_accessible'] = False
            else:
                job['url_accessible'] = False
    
    def save_results(self, filename='job_autofill_analysis_selenium.json'):
        """Save the analysis results to a JSON file"""
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(self.jobs_data, f, indent=2, ensure_ascii=False)
        print(f"Results saved to {filename}")
    
    def print_summary(self):
        """Print a summary of the findings"""
        print(f"\n{'='*80}")
        print("JOBRIGHT.AI AUTOFILL BUTTON ANALYSIS (SELENIUM)")
        print(f"{'='*80}")
        print(f"Total elements found: {len(self.jobs_data)}")
        
        accessible_urls = sum(1 for job in self.jobs_data if job.get('url_accessible', False))
        print(f"Accessible target URLs: {accessible_urls}")
        
        print(f"\n{'='*80}")
        print("DETAILED FINDINGS:")
        print(f"{'='*80}")
        
        for i, job in enumerate(self.jobs_data, 1):
            print(f"\n{i}. Element Analysis:")
            print(f"   Text: {job['text']}")
            print(f"   Tag: {job['tag']}")
            print(f"   Classes: {job['classes']}")
            print(f"   ID: {job['id']}")
            print(f"   Href: {job['href']}")
            print(f"   Onclick: {job['onclick']}")
            print(f"   Target URL: {job['target_url']}")
            print(f"   URL Accessible: {job.get('url_accessible', 'N/A')}")
            print(f"   Is Displayed: {job['is_displayed']}")
            print(f"   Is Enabled: {job['is_enabled']}")
            print(f"   Job Title: {job['job_title']}")
            print(f"   Company: {job['company']}")
            print(f"   Location: {job['location']}")
            print(f"   Job ID: {job['job_id']}")
            print(f"   Data Attributes: {job['data_attributes']}")
            print(f"   Parent Context: {job['parent_info']}")
            print("-" * 60)

def main():
    scraper = JobRightSeleniumScraper()
    
    # Target URL
    target_url = "https://jobright.ai/jobs/recommend?pos=16"
    
    print("Starting JobRight.ai Selenium scraper...")
    print(f"Target URL: {target_url}")
    
    # Scrape the page
    jobs = scraper.scrape_job_page(target_url)
    
    if jobs:
        # Test target URLs
        scraper.test_target_urls()
        
        # Print summary
        scraper.print_summary()
        
        # Save results
        scraper.save_results()
    else:
        print("No autofill buttons found or error occurred.")

if __name__ == "__main__":
    main()
