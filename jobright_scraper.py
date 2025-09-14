#!/usr/bin/env python3
"""
Jobright Apply with Autofill Button Scraper
Identifies all "Apply with autofill" buttons and extracts their linked pages
"""

import requests
from bs4 import BeautifulSoup
import json
import time
import re
from urllib.parse import urljoin, urlparse
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class JobrightScraper:
    def __init__(self, base_url="https://jobright.ai"):
        self.base_url = base_url
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        })
        self.apply_buttons = []
        
    def get_page(self, url, max_retries=3):
        """Fetch a page with retry logic"""
        for attempt in range(max_retries):
            try:
                response = self.session.get(url, timeout=10)
                response.raise_for_status()
                return response
            except requests.RequestException as e:
                logger.warning(f"Attempt {attempt + 1} failed for {url}: {e}")
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)  # Exponential backoff
                else:
                    logger.error(f"Failed to fetch {url} after {max_retries} attempts")
                    return None
    
    def find_apply_buttons(self, soup, page_url):
        """Find all Apply with autofill buttons on the page"""
        buttons = []
        
        # Look for various patterns that might indicate "Apply with autofill" buttons
        patterns = [
            r'apply.*autofill',
            r'autofill.*apply',
            r'apply.*auto.*fill',
            r'quick.*apply',
            r'one.*click.*apply',
            r'instant.*apply'
        ]
        
        # Search in text content, buttons, links, and other elements
        for element in soup.find_all(['a', 'button', 'div', 'span'], text=re.compile('|'.join(patterns), re.IGNORECASE)):
            if element:
                button_info = self.extract_button_info(element, page_url)
                if button_info:
                    buttons.append(button_info)
        
        # Also search for elements with specific classes or attributes that might indicate apply buttons
        for element in soup.find_all(['a', 'button'], class_=re.compile(r'apply|autofill|quick', re.IGNORECASE)):
            if element:
                button_info = self.extract_button_info(element, page_url)
                if button_info:
                    buttons.append(button_info)
        
        # Search for data attributes that might contain apply information
        for element in soup.find_all(attrs={'data-action': re.compile(r'apply|autofill', re.IGNORECASE)}):
            if element:
                button_info = self.extract_button_info(element, page_url)
                if button_info:
                    buttons.append(button_info)
        
        return buttons
    
    def extract_button_info(self, element, page_url):
        """Extract information from a potential apply button"""
        try:
            text = element.get_text(strip=True).lower()
            
            # Check if this looks like an apply button
            if any(keyword in text for keyword in ['apply', 'autofill', 'quick apply', 'one click']):
                button_info = {
                    'text': element.get_text(strip=True),
                    'page_url': page_url,
                    'element_type': element.name,
                    'classes': element.get('class', []),
                    'attributes': dict(element.attrs) if element.attrs else {},
                }
                
                # Extract the link/action
                if element.name == 'a' and element.get('href'):
                    button_info['link'] = urljoin(page_url, element.get('href'))
                elif element.get('onclick'):
                    button_info['onclick'] = element.get('onclick')
                elif element.get('data-href'):
                    button_info['link'] = urljoin(page_url, element.get('data-href'))
                elif element.get('data-url'):
                    button_info['link'] = urljoin(page_url, element.get('data-url'))
                
                return button_info
        except Exception as e:
            logger.warning(f"Error extracting button info: {e}")
        
        return None
    
    def scrape_job_page(self, url):
        """Scrape a specific job page for apply buttons"""
        logger.info(f"Scraping job page: {url}")
        response = self.get_page(url)
        if not response:
            return []
        
        soup = BeautifulSoup(response.content, 'html.parser')
        buttons = self.find_apply_buttons(soup, url)
        
        logger.info(f"Found {len(buttons)} apply buttons on {url}")
        return buttons
    
    def scrape_recommendations_page(self, url):
        """Scrape the main recommendations page"""
        logger.info(f"Scraping recommendations page: {url}")
        response = self.get_page(url)
        if not response:
            return []
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Find all job links on the recommendations page
        job_links = []
        
        # Look for various patterns that might be job links
        for link in soup.find_all('a', href=True):
            href = link.get('href')
            if href and ('job' in href.lower() or 'position' in href.lower() or 'career' in href.lower()):
                full_url = urljoin(url, href)
                job_links.append(full_url)
        
        # Also look for data attributes that might contain job URLs
        for element in soup.find_all(attrs={'data-job-url': True}):
            job_url = element.get('data-job-url')
            if job_url:
                full_url = urljoin(url, job_url)
                job_links.append(full_url)
        
        logger.info(f"Found {len(job_links)} potential job links")
        return job_links
    
    def run_full_scrape(self, start_url):
        """Run the complete scraping process"""
        logger.info("Starting Jobright scraping process...")
        
        # First, scrape the recommendations page to find job links
        job_links = self.scrape_recommendations_page(start_url)
        
        all_apply_buttons = []
        
        # Scrape each job page for apply buttons
        for job_url in job_links[:10]:  # Limit to first 10 jobs for testing
            try:
                buttons = self.scrape_job_page(job_url)
                all_apply_buttons.extend(buttons)
                time.sleep(1)  # Be respectful to the server
            except Exception as e:
                logger.error(f"Error scraping {job_url}: {e}")
        
        # Also check the main page for any apply buttons
        main_page_buttons = self.scrape_job_page(start_url)
        all_apply_buttons.extend(main_page_buttons)
        
        return all_apply_buttons
    
    def save_results(self, buttons, filename="apply_buttons.json"):
        """Save the results to a JSON file"""
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(buttons, f, indent=2, ensure_ascii=False)
        logger.info(f"Results saved to {filename}")
    
    def print_results(self, buttons):
        """Print the results in a readable format"""
        print("\n" + "="*80)
        print("APPLY WITH AUTOFILL BUTTONS FOUND")
        print("="*80)
        
        if not buttons:
            print("No apply buttons found.")
            return
        
        for i, button in enumerate(buttons, 1):
            print(f"\n{i}. Button Text: {button['text']}")
            print(f"   Page URL: {button['page_url']}")
            print(f"   Element Type: {button['element_type']}")
            if 'link' in button:
                print(f"   Link: {button['link']}")
            if 'onclick' in button:
                print(f"   OnClick: {button['onclick']}")
            if button['classes']:
                print(f"   Classes: {', '.join(button['classes'])}")
            print("-" * 40)

def main():
    scraper = JobrightScraper()
    
    # Start URL from the user's request
    start_url = "https://jobright.ai/jobs/recommend?pos=16"
    
    try:
        # Run the scraping process
        apply_buttons = scraper.run_full_scrape(start_url)
        
        # Print results
        scraper.print_results(apply_buttons)
        
        # Save results
        scraper.save_results(apply_buttons)
        
        print(f"\nTotal apply buttons found: {len(apply_buttons)}")
        
    except Exception as e:
        logger.error(f"Scraping failed: {e}")

if __name__ == "__main__":
    main()


