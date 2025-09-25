#!/usr/bin/env python3
"""
JobRight.ai Site Scraper and Clone Builder
Scrapes the exact design and builds a perfect replica
"""

import sys
sys.path.append('/home/calelin/awesome-apply/venv/lib/python3.13/site-packages')

import requests
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import json
import re
from bs4 import BeautifulSoup
import base64
import os

class JobRightScraper:
    """Scrape JobRight.ai for exact design replication"""

    def __init__(self):
        self.setup_driver()
        self.design_data = {
            'html_structure': '',
            'css_styles': '',
            'javascript': '',
            'components': [],
            'colors': [],
            'fonts': [],
            'layout_structure': {},
            'interactive_elements': []
        }

    def setup_driver(self):
        """Setup Chrome driver for scraping"""
        options = Options()
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-gpu')
        options.add_argument('--window-size=1920,1080')
        options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36')

        try:
            self.driver = webdriver.Chrome(options=options)
            print("✅ Chrome driver initialized")
        except Exception as e:
            print(f"❌ Failed to initialize Chrome driver: {e}")
            self.driver = None

    def scrape_jobright_design(self):
        """Scrape JobRight.ai for complete design analysis"""
        if not self.driver:
            print("❌ No driver available")
            return

        try:
            print("🔍 Analyzing JobRight.ai design...")
            self.driver.get("https://jobright.ai/jobs")

            # Wait for page to load
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            time.sleep(5)

            # Get complete HTML structure
            self.design_data['html_structure'] = self.driver.page_source

            # Extract CSS styles
            self.extract_styles()

            # Extract JavaScript
            self.extract_javascript()

            # Analyze layout components
            self.analyze_components()

            # Extract color palette
            self.extract_colors()

            # Analyze typography
            self.analyze_typography()

            # Map interactive elements
            self.map_interactive_elements()

            print("✅ Complete design analysis completed")

        except Exception as e:
            print(f"❌ Failed to scrape design: {e}")
        finally:
            if self.driver:
                self.driver.quit()

    def extract_styles(self):
        """Extract all CSS styles from the page"""
        try:
            # Get all stylesheets
            stylesheets = self.driver.find_elements(By.TAG_NAME, "link")
            style_tags = self.driver.find_elements(By.TAG_NAME, "style")

            css_content = ""

            # Extract inline styles
            for style in style_tags:
                css_content += style.get_attribute('innerHTML') + "\n"

            # Extract linked stylesheets
            for link in stylesheets:
                if link.get_attribute('rel') == 'stylesheet':
                    href = link.get_attribute('href')
                    if href:
                        try:
                            response = requests.get(href, timeout=10)
                            css_content += f"\n/* {href} */\n" + response.text + "\n"
                        except:
                            pass

            self.design_data['css_styles'] = css_content
            print("✅ CSS styles extracted")

        except Exception as e:
            print(f"⚠️ CSS extraction failed: {e}")

    def extract_javascript(self):
        """Extract JavaScript from the page"""
        try:
            script_tags = self.driver.find_elements(By.TAG_NAME, "script")
            js_content = ""

            for script in script_tags:
                src = script.get_attribute('src')
                if src:
                    try:
                        response = requests.get(src, timeout=10)
                        js_content += f"\n/* {src} */\n" + response.text + "\n"
                    except:
                        pass
                else:
                    js_content += script.get_attribute('innerHTML') + "\n"

            self.design_data['javascript'] = js_content[:50000]  # Limit size
            print("✅ JavaScript extracted")

        except Exception as e:
            print(f"⚠️ JavaScript extraction failed: {e}")

    def analyze_components(self):
        """Analyze page components and layout structure"""
        try:
            # Find major layout components
            components = []

            # Header/Navigation
            headers = self.driver.find_elements(By.CSS_SELECTOR, "header, nav, .header, .navbar")
            for header in headers:
                components.append({
                    'type': 'header',
                    'html': header.get_attribute('outerHTML')[:2000],
                    'classes': header.get_attribute('class'),
                    'styles': self.driver.execute_script("return window.getComputedStyle(arguments[0])", header)
                })

            # Main content areas
            mains = self.driver.find_elements(By.CSS_SELECTOR, "main, .main-content, .content, .container")
            for main in mains:
                components.append({
                    'type': 'main',
                    'html': main.get_attribute('outerHTML')[:2000],
                    'classes': main.get_attribute('class'),
                    'styles': self.get_element_styles(main)
                })

            # Job cards/listings
            job_cards = self.driver.find_elements(By.CSS_SELECTOR, ".job-card, .job-item, .listing, [class*='job']")
            for card in job_cards[:3]:  # Limit to first 3
                components.append({
                    'type': 'job_card',
                    'html': card.get_attribute('outerHTML')[:1000],
                    'classes': card.get_attribute('class'),
                    'styles': self.get_element_styles(card)
                })

            # Search/Filter components
            search_elements = self.driver.find_elements(By.CSS_SELECTOR, ".search, .filter, input[type='search'], .search-bar")
            for search in search_elements:
                components.append({
                    'type': 'search',
                    'html': search.get_attribute('outerHTML')[:1000],
                    'classes': search.get_attribute('class'),
                    'styles': self.get_element_styles(search)
                })

            # Buttons
            buttons = self.driver.find_elements(By.CSS_SELECTOR, "button, .btn, .button, [role='button']")
            for btn in buttons[:5]:  # Limit to first 5
                components.append({
                    'type': 'button',
                    'html': btn.get_attribute('outerHTML')[:500],
                    'classes': btn.get_attribute('class'),
                    'text': btn.text,
                    'styles': self.get_element_styles(btn)
                })

            self.design_data['components'] = components
            print(f"✅ {len(components)} components analyzed")

        except Exception as e:
            print(f"⚠️ Component analysis failed: {e}")

    def get_element_styles(self, element):
        """Get computed styles for an element"""
        try:
            return {
                'backgroundColor': element.value_of_css_property('background-color'),
                'color': element.value_of_css_property('color'),
                'fontSize': element.value_of_css_property('font-size'),
                'fontFamily': element.value_of_css_property('font-family'),
                'padding': element.value_of_css_property('padding'),
                'margin': element.value_of_css_property('margin'),
                'borderRadius': element.value_of_css_property('border-radius'),
                'boxShadow': element.value_of_css_property('box-shadow'),
                'display': element.value_of_css_property('display'),
                'width': element.value_of_css_property('width'),
                'height': element.value_of_css_property('height')
            }
        except:
            return {}

    def extract_colors(self):
        """Extract color palette from the design"""
        colors = set()

        try:
            # Extract colors from CSS
            css_content = self.design_data.get('css_styles', '')

            # Find hex colors
            hex_colors = re.findall(r'#[0-9A-Fa-f]{6}|#[0-9A-Fa-f]{3}', css_content)
            colors.update(hex_colors)

            # Find rgb colors
            rgb_colors = re.findall(r'rgb\(\s*\d+\s*,\s*\d+\s*,\s*\d+\s*\)', css_content)
            colors.update(rgb_colors)

            # Find rgba colors
            rgba_colors = re.findall(r'rgba\(\s*\d+\s*,\s*\d+\s*,\s*\d+\s*,\s*[\d.]+\s*\)', css_content)
            colors.update(rgba_colors)

            self.design_data['colors'] = list(colors)
            print(f"✅ {len(colors)} colors extracted")

        except Exception as e:
            print(f"⚠️ Color extraction failed: {e}")

    def analyze_typography(self):
        """Analyze typography used in the design"""
        try:
            fonts = set()
            css_content = self.design_data.get('css_styles', '')

            # Extract font families
            font_matches = re.findall(r'font-family\s*:\s*([^;}]+)', css_content, re.IGNORECASE)
            for match in font_matches:
                fonts.add(match.strip().strip('"\''))

            self.design_data['fonts'] = list(fonts)
            print(f"✅ {len(fonts)} fonts identified")

        except Exception as e:
            print(f"⚠️ Typography analysis failed: {e}")

    def map_interactive_elements(self):
        """Map all interactive elements"""
        try:
            interactive_elements = []

            if self.driver:
                # Find all clickable elements
                clickables = self.driver.find_elements(By.CSS_SELECTOR, "button, a, input, select, [onclick], [role='button']")

                for element in clickables[:20]:  # Limit to first 20
                    try:
                        interactive_elements.append({
                            'tag': element.tag_name,
                            'text': element.text[:100],
                            'classes': element.get_attribute('class'),
                            'id': element.get_attribute('id'),
                            'type': element.get_attribute('type'),
                            'href': element.get_attribute('href'),
                            'onclick': element.get_attribute('onclick'),
                            'position': {
                                'x': element.location['x'],
                                'y': element.location['y']
                            },
                            'size': {
                                'width': element.size['width'],
                                'height': element.size['height']
                            }
                        })
                    except:
                        continue

            self.design_data['interactive_elements'] = interactive_elements
            print(f"✅ {len(interactive_elements)} interactive elements mapped")

        except Exception as e:
            print(f"⚠️ Interactive elements mapping failed: {e}")

    def save_design_data(self, filename="jobright_design_data.json"):
        """Save all scraped design data"""
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(self.design_data, f, indent=2, ensure_ascii=False)

            print(f"✅ Design data saved to {filename}")

            # Also save HTML separately
            with open("jobright_source.html", 'w', encoding='utf-8') as f:
                f.write(self.design_data.get('html_structure', ''))

            # Save CSS separately
            with open("jobright_styles.css", 'w', encoding='utf-8') as f:
                f.write(self.design_data.get('css_styles', ''))

            print("✅ HTML and CSS files saved separately")

        except Exception as e:
            print(f"❌ Failed to save design data: {e}")

def main():
    """Main scraping execution"""
    print("🎯 JOBRIGHT.AI DESIGN SCRAPER")
    print("=" * 50)

    scraper = JobRightScraper()
    scraper.scrape_jobright_design()
    scraper.save_design_data()

    # Print summary
    print("\n📊 SCRAPING SUMMARY")
    print("=" * 50)
    print(f"HTML Structure: {len(scraper.design_data.get('html_structure', ''))} characters")
    print(f"CSS Styles: {len(scraper.design_data.get('css_styles', ''))} characters")
    print(f"Components: {len(scraper.design_data.get('components', []))} found")
    print(f"Colors: {len(scraper.design_data.get('colors', []))} extracted")
    print(f"Fonts: {len(scraper.design_data.get('fonts', []))} identified")
    print(f"Interactive Elements: {len(scraper.design_data.get('interactive_elements', []))} mapped")

if __name__ == "__main__":
    main()