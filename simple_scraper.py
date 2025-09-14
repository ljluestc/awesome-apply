#!/usr/bin/env python3
"""
Simple JobRight.ai Job Scraper
Uses curl to fetch HTML and BeautifulSoup to parse
"""

import subprocess
import json
import re
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse

class SimpleJobRightScraper:
    def __init__(self):
        self.base_url = "https://jobright.ai"
        self.jobs_data = []
    
    def fetch_page_content(self, url):
        """Fetch page content using curl"""
        try:
            cmd = [
                'curl', '-s', '-L', 
                '-H', 'User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                '-H', 'Accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                '-H', 'Accept-Language: en-US,en;q=0.5',
                '-H', 'Accept-Encoding: gzip, deflate',
                '--compressed',
                url
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            if result.returncode == 0:
                return result.stdout
            else:
                print(f"Curl error: {result.stderr}")
                return None
        except Exception as e:
            print(f"Error fetching page: {e}")
            return None
    
    def scrape_job_page(self, url):
        """Scrape the job recommendation page"""
        print(f"Fetching page: {url}")
        html_content = self.fetch_page_content(url)
        
        if not html_content:
            print("Failed to fetch page content")
            return []
        
        print(f"Page content length: {len(html_content)} characters")
        
        # Save HTML content for debugging
        with open('page_content.html', 'w', encoding='utf-8') as f:
            f.write(html_content)
        print("HTML content saved to page_content.html")
        
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Look for various patterns of "Apply with autofill" buttons
        autofill_buttons = []
        
        # Search for buttons with text containing "Apply" and "autofill"
        buttons = soup.find_all(['button', 'a', 'div', 'span'], 
                               string=re.compile(r'Apply.*[Aa]utofill|autofill.*[Aa]pply', re.I))
        autofill_buttons.extend(buttons)
        
        # Search for buttons with text containing just "autofill"
        autofill_only = soup.find_all(['button', 'a', 'div', 'span'], 
                                    string=re.compile(r'[Aa]utofill', re.I))
        autofill_buttons.extend(autofill_only)
        
        # Search for buttons with text containing "Apply"
        apply_buttons = soup.find_all(['button', 'a', 'div', 'span'], 
                                    string=re.compile(r'[Aa]pply', re.I))
        autofill_buttons.extend(apply_buttons)
        
        # Search for elements with classes containing apply/autofill
        class_elements = soup.find_all(class_=re.compile(r'apply|autofill', re.I))
        autofill_buttons.extend(class_elements)
        
        # Search for elements with data attributes
        data_elements = soup.find_all(attrs={'data-action': re.compile(r'apply|autofill', re.I)})
        autofill_buttons.extend(data_elements)
        
        # Search for onclick attributes
        onclick_elements = soup.find_all(onclick=re.compile(r'apply|autofill', re.I))
        autofill_buttons.extend(onclick_elements)
        
        # Remove duplicates
        autofill_buttons = list(set(autofill_buttons))
        
        print(f"Found {len(autofill_buttons)} potential autofill elements")
        
        # Analyze each button
        for i, button in enumerate(autofill_buttons):
            button_info = self.analyze_button(button, i)
            if button_info:
                self.jobs_data.append(button_info)
        
        return self.jobs_data
    
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
                'parent_info': '',
                'is_autofill': False
            }
            
            # Check if this is likely an autofill button
            text_lower = button_info['text'].lower()
            classes_lower = ' '.join(button_info['classes']).lower()
            button_info['is_autofill'] = any(keyword in text_lower or keyword in classes_lower 
                                           for keyword in ['autofill', 'auto-fill', 'auto fill', 'apply'])
            
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
                    'text': parent.get_text(strip=True)[:200] + '...' if len(parent.get_text(strip=True)) > 200 else parent.get_text(strip=True)
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
            'job_id': '',
            'salary': '',
            'job_type': ''
        }
        
        try:
            # Look for job title in nearby elements
            current = button
            for _ in range(5):  # Check up to 5 parent levels
                if current.parent:
                    current = current.parent
                    text = current.get_text(strip=True)
                    
                    # Look for common job title patterns
                    if not job_info['job_title'] and len(text) > 10 and len(text) < 150:
                        # Check if this looks like a job title
                        job_keywords = ['engineer', 'developer', 'manager', 'analyst', 'specialist', 'coordinator', 'director', 'lead', 'senior', 'junior']
                        if any(keyword in text.lower() for keyword in job_keywords):
                            # Take the first line that looks like a job title
                            lines = text.split('\n')
                            for line in lines:
                                if len(line) > 10 and len(line) < 100 and any(keyword in line.lower() for keyword in job_keywords):
                                    job_info['job_title'] = line.strip()
                                    break
                    
                    # Look for company name
                    if not job_info['company'] and (' at ' in text.lower() or ' - ' in text.lower()):
                        if ' at ' in text.lower():
                            parts = text.split(' at ')
                            if len(parts) > 1:
                                job_info['company'] = parts[1].split('\n')[0].strip()
                        elif ' - ' in text.lower():
                            parts = text.split(' - ')
                            if len(parts) > 1:
                                job_info['company'] = parts[0].strip()
                    
                    # Look for location
                    if not job_info['location']:
                        location_keywords = ['remote', 'hybrid', 'new york', 'california', 'texas', 'florida', 'washington', 'chicago', 'boston', 'seattle']
                        for keyword in location_keywords:
                            if keyword in text.lower():
                                job_info['location'] = keyword.title()
                                break
                    
                    # Look for salary information
                    if not job_info['salary'] and ('$' in text or 'salary' in text.lower() or 'k' in text.lower()):
                        salary_pattern = r'\$[\d,]+(?:k|K)?(?:\s*-\s*\$[\d,]+(?:k|K)?)?'
                        salary_match = re.search(salary_pattern, text)
                        if salary_match:
                            job_info['salary'] = salary_match.group()
                    
                    # Look for job type
                    if not job_info['job_type']:
                        job_type_keywords = ['full-time', 'part-time', 'contract', 'freelance', 'internship', 'temporary']
                        for keyword in job_type_keywords:
                            if keyword in text.lower():
                                job_info['job_type'] = keyword.title()
                                break
                
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
                    cmd = ['curl', '-s', '-o', '/dev/null', '-w', '%{http_code}', job['target_url']]
                    result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
                    if result.returncode == 0:
                        job['url_status'] = result.stdout.strip()
                        job['url_accessible'] = result.stdout.strip() in ['200', '301', '302']
                    else:
                        job['url_status'] = 'Error'
                        job['url_accessible'] = False
                except:
                    job['url_status'] = 'Error'
                    job['url_accessible'] = False
            else:
                job['url_accessible'] = False
    
    def save_results(self, filename='job_autofill_analysis_simple.json'):
        """Save the analysis results to a JSON file"""
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(self.jobs_data, f, indent=2, ensure_ascii=False)
        print(f"Results saved to {filename}")
    
    def print_summary(self):
        """Print a summary of the findings"""
        print(f"\n{'='*80}")
        print("JOBRIGHT.AI AUTOFILL BUTTON ANALYSIS (SIMPLE)")
        print(f"{'='*80}")
        print(f"Total elements found: {len(self.jobs_data)}")
        
        autofill_buttons = [job for job in self.jobs_data if job.get('is_autofill', False)]
        print(f"Likely autofill buttons: {len(autofill_buttons)}")
        
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
            print(f"   Is Autofill: {job['is_autofill']}")
            print(f"   Job Title: {job['job_title']}")
            print(f"   Company: {job['company']}")
            print(f"   Location: {job['location']}")
            print(f"   Salary: {job['salary']}")
            print(f"   Job Type: {job['job_type']}")
            print(f"   Job ID: {job['job_id']}")
            print(f"   Data Attributes: {job['data_attributes']}")
            print(f"   Parent Context: {job['parent_info']}")
            print("-" * 60)

def main():
    scraper = SimpleJobRightScraper()
    
    # Target URL
    target_url = "https://jobright.ai/jobs/recommend?pos=16"
    
    print("Starting JobRight.ai Simple scraper...")
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
        print("No elements found or error occurred.")

if __name__ == "__main__":
    main()
