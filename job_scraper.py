#!/usr/bin/env python3
"""
JobRight.ai Job Scraper
Identifies all 'Apply with autofill' buttons and their target pages
"""

import requests
from bs4 import BeautifulSoup
import json
import time
from urllib.parse import urljoin, urlparse
import re

class JobRightScraper:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        self.base_url = "https://jobright.ai"
        self.jobs_data = []
    
    def scrape_job_page(self, url):
        """Scrape the job recommendation page"""
        try:
            print(f"Scraping: {url}")
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Look for various patterns of "Apply with autofill" buttons
            autofill_buttons = []
            
            # Search for buttons with text containing "Apply with autofill" or similar
            buttons = soup.find_all(['button', 'a', 'div'], string=re.compile(r'Apply.*[Aa]utofill|autofill.*[Aa]pply', re.I))
            autofill_buttons.extend(buttons)
            
            # Search for buttons with onclick or href attributes
            clickable_elements = soup.find_all(['button', 'a', 'div'], 
                onclick=re.compile(r'apply|autofill', re.I))
            autofill_buttons.extend(clickable_elements)
            
            # Search for elements with classes containing apply/autofill
            class_elements = soup.find_all(class_=re.compile(r'apply|autofill', re.I))
            autofill_buttons.extend(class_elements)
            
            # Search for data attributes
            data_elements = soup.find_all(attrs={'data-action': re.compile(r'apply|autofill', re.I)})
            autofill_buttons.extend(data_elements)
            
            # Remove duplicates
            autofill_buttons = list(set(autofill_buttons))
            
            print(f"Found {len(autofill_buttons)} potential autofill buttons")
            
            # Analyze each button
            for i, button in enumerate(autofill_buttons):
                button_info = self.analyze_button(button, i)
                if button_info:
                    self.jobs_data.append(button_info)
            
            return self.jobs_data
            
        except Exception as e:
            print(f"Error scraping {url}: {str(e)}")
            return []
    
    def analyze_button(self, button, index):
        """Analyze a button to extract its properties and target URL"""
        try:
            button_info = {
                'index': index,
                'tag': button.name,
                'text': button.get_text(strip=True),
                'classes': button.get('class', []),
                'id': button.get('id', ''),
                'href': '',
                'onclick': '',
                'data_attributes': {},
                'target_url': '',
                'parent_info': ''
            }
            
            # Extract href if it's a link
            if button.name == 'a':
                button_info['href'] = button.get('href', '')
                if button_info['href']:
                    button_info['target_url'] = urljoin(self.base_url, button_info['href'])
            
            # Extract onclick attribute
            button_info['onclick'] = button.get('onclick', '')
            
            # Extract data attributes
            for attr, value in button.attrs.items():
                if attr.startswith('data-'):
                    button_info['data_attributes'][attr] = value
            
            # Get parent element info for context
            parent = button.parent
            if parent:
                button_info['parent_info'] = {
                    'tag': parent.name,
                    'class': parent.get('class', []),
                    'id': parent.get('id', ''),
                    'text': parent.get_text(strip=True)[:100] + '...' if len(parent.get_text(strip=True)) > 100 else parent.get_text(strip=True)
                }
            
            # Try to extract job information from surrounding context
            job_info = self.extract_job_info(button)
            button_info.update(job_info)
            
            return button_info
            
        except Exception as e:
            print(f"Error analyzing button {index}: {str(e)}")
            return None
    
    def extract_job_info(self, button):
        """Extract job information from the button's context"""
        job_info = {
            'job_title': '',
            'company': '',
            'location': '',
            'job_id': ''
        }
        
        try:
            # Look for job title in nearby elements
            current = button
            for _ in range(5):  # Check up to 5 parent levels
                if current.parent:
                    current = current.parent
                    text = current.get_text(strip=True)
                    
                    # Look for common job title patterns
                    if not job_info['job_title'] and len(text) > 10 and len(text) < 100:
                        # Check if this looks like a job title
                        if any(keyword in text.lower() for keyword in ['engineer', 'developer', 'manager', 'analyst', 'specialist', 'coordinator']):
                            job_info['job_title'] = text
                    
                    # Look for company name
                    if not job_info['company'] and 'at ' in text.lower():
                        parts = text.split(' at ')
                        if len(parts) > 1:
                            job_info['company'] = parts[1].split()[0]
                    
                    # Look for location
                    if not job_info['location'] and any(loc in text.lower() for loc in ['remote', 'hybrid', 'new york', 'california', 'texas', 'florida']):
                        job_info['location'] = text
                
                if current.name == 'body':
                    break
            
            # Look for job ID in data attributes or nearby elements
            for attr, value in button.attrs.items():
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
                    response = self.session.head(job['target_url'], timeout=10)
                    job['url_status'] = response.status_code
                    job['url_accessible'] = response.status_code < 400
                except:
                    job['url_status'] = 'Error'
                    job['url_accessible'] = False
            else:
                job['url_accessible'] = False
    
    def save_results(self, filename='job_autofill_analysis.json'):
        """Save the analysis results to a JSON file"""
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(self.jobs_data, f, indent=2, ensure_ascii=False)
        print(f"Results saved to {filename}")
    
    def print_summary(self):
        """Print a summary of the findings"""
        print(f"\n{'='*60}")
        print("JOBRIGHT.AI AUTOFILL BUTTON ANALYSIS")
        print(f"{'='*60}")
        print(f"Total buttons found: {len(self.jobs_data)}")
        
        accessible_urls = sum(1 for job in self.jobs_data if job.get('url_accessible', False))
        print(f"Accessible target URLs: {accessible_urls}")
        
        print(f"\n{'='*60}")
        print("DETAILED FINDINGS:")
        print(f"{'='*60}")
        
        for i, job in enumerate(self.jobs_data, 1):
            print(f"\n{i}. Button Analysis:")
            print(f"   Text: {job['text']}")
            print(f"   Tag: {job['tag']}")
            print(f"   Classes: {job['classes']}")
            print(f"   ID: {job['id']}")
            print(f"   Href: {job['href']}")
            print(f"   Onclick: {job['onclick']}")
            print(f"   Target URL: {job['target_url']}")
            print(f"   URL Accessible: {job.get('url_accessible', 'N/A')}")
            print(f"   Job Title: {job['job_title']}")
            print(f"   Company: {job['company']}")
            print(f"   Location: {job['location']}")
            print(f"   Job ID: {job['job_id']}")
            print(f"   Parent Context: {job['parent_info']}")
            print("-" * 40)

def main():
    scraper = JobRightScraper()
    
    # Target URL
    target_url = "https://jobright.ai/jobs/recommend?pos=16"
    
    print("Starting JobRight.ai scraper...")
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
