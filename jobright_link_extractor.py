#!/usr/bin/env python3
"""
Extract all job links from jobright.ai recommend page
"""

import time
import json
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def setup_driver():
    """Setup Chrome driver with necessary options"""
    chrome_options = Options()
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)

    driver = webdriver.Chrome(options=chrome_options)
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

    return driver

def extract_job_links(driver, url):
    """Extract all job links from the page"""
    logger.info(f"Navigating to {url}")
    driver.get(url)

    # Wait for page to load and execute JavaScript
    logger.info("Waiting for page to fully load...")
    time.sleep(15)

    # Try to trigger any lazy loading by scrolling
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight/4);")
    time.sleep(3)
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight/2);")
    time.sleep(3)
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    time.sleep(5)
    driver.execute_script("window.scrollTo(0, 0);")
    time.sleep(3)

    job_links = []

    try:
        logger.info(f"Page title: {driver.title}")

        # Wait for content to be loaded
        try:
            WebDriverWait(driver, 30).until(
                lambda d: d.execute_script("return document.readyState") == "complete"
            )
            time.sleep(5)
        except TimeoutException:
            logger.warning("Page readyState timeout, continuing anyway...")

        # Try multiple selectors for job cards
        job_card_selectors = [
            "[data-testid='job-card']",
            ".job-card",
            "[class*='job']",
            "[class*='JobCard']",
            ".JobItem",
            "[data-cy='job-card']",
            "article",
            "[role='article']",
            ".card",
            "div[class*='Card']",
            "div[class*='Item']"
        ]

        job_cards = []
        for selector in job_card_selectors:
            try:
                elements = driver.find_elements(By.CSS_SELECTOR, selector)
                if elements:
                    # Check if these elements actually have content
                    content_count = 0
                    for elem in elements:
                        if elem.text.strip() or elem.find_elements(By.TAG_NAME, "a"):
                            content_count += 1

                    if content_count > 5:  # Only use if at least 5 elements have content
                        job_cards = elements
                        logger.info(f"Found {len(job_cards)} job cards using selector: {selector} ({content_count} with content)")
                        break
                    else:
                        logger.debug(f"Selector {selector} found {len(elements)} elements but only {content_count} with content")
            except Exception as e:
                logger.debug(f"Selector {selector} failed: {e}")
                continue

        if not job_cards:
            logger.warning("No job cards found with initial selectors, trying alternative approach...")
            # Look for any elements that contain job-like content
            all_elements = driver.find_elements(By.XPATH, "//*[contains(text(), 'Apply') or contains(text(), 'Job') or contains(text(), '$') or contains(text(), 'hour')]")
            logger.info(f"Found {len(all_elements)} elements with job-related text")

            # Try to find their parent containers
            parent_elements = set()
            for elem in all_elements[:20]:
                try:
                    parent = elem.find_element(By.XPATH, "..")
                    if parent:
                        parent_elements.add(parent)
                except:
                    continue

            job_cards = list(parent_elements)
            logger.info(f"Using {len(job_cards)} parent elements as job cards")

        if not job_cards:
            logger.warning("No job cards found, trying alternative approach...")
            # Look for any links that might be job-related
            all_links = driver.find_elements(By.TAG_NAME, "a")
            for link in all_links:
                href = link.get_attribute('href')
                if href and any(keyword in href.lower() for keyword in ['/job/', '/position/', '/apply', 'jobright.ai']):
                    text = link.text.strip() or "No text"
                    job_info = {
                        "title": text,
                        "link": href,
                        "index": len(job_links) + 1
                    }
                    job_links.append(job_info)
                    logger.info(f"Found potential job link: {text} - {href}")

            if job_links:
                logger.info(f"Found {len(job_links)} potential job links using alternative method")
                return job_links
            else:
                logger.warning("No job links found with any method")
                return job_links

        # Scroll to load more jobs
        logger.info("Scrolling to load more jobs...")
        last_height = driver.execute_script("return document.body.scrollHeight")

        while True:
            # Scroll down to bottom
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")

            # Wait for new content to load
            time.sleep(3)

            # Calculate new scroll height and compare with last scroll height
            new_height = driver.execute_script("return document.body.scrollHeight")
            if new_height == last_height:
                break
            last_height = new_height

        # Use the job_cards we already found from the earlier selectors
        logger.info(f"Processing {len(job_cards)} job cards")

        for i, card in enumerate(job_cards):
            try:
                job_link = None
                job_title = "Unknown"

                # First try to get job title
                try:
                    title_selectors = [
                        "h3", "h2", "h1", ".job-title", "[data-testid='job-title']",
                        "a[href*='/job/']", "a[href*='/position/']"
                    ]
                    for title_sel in title_selectors:
                        title_elements = card.find_elements(By.CSS_SELECTOR, title_sel)
                        if title_elements:
                            job_title = title_elements[0].text.strip()
                            if job_title and len(job_title) > 3:
                                break
                except Exception as e:
                    logger.debug(f"Error getting title for card {i+1}: {e}")

                # Try multiple approaches to find links
                all_links = card.find_elements(By.TAG_NAME, "a")
                buttons = card.find_elements(By.TAG_NAME, "button")

                # First look for explicit job/apply links
                for link in all_links:
                    href = link.get_attribute('href')
                    if href:
                        if any(keyword in href.lower() for keyword in ['/job/', '/position/', 'apply', 'careers']):
                            job_link = href
                            link_text = link.text.strip()
                            if link_text and len(link_text) > 3:
                                job_title = link_text
                            break

                # If no explicit job link, look for external links (company websites)
                if not job_link:
                    for link in all_links:
                        href = link.get_attribute('href')
                        if href and 'http' in href and 'jobright.ai' not in href.lower():
                            # This could be a company careers page
                            job_link = href
                            link_text = link.text.strip()
                            if link_text and len(link_text) > 3:
                                job_title = link_text
                            break

                # Check buttons for onclick handlers or data attributes
                if not job_link:
                    for button in buttons:
                        button_text = button.text.strip().lower()
                        if any(keyword in button_text for keyword in ['apply', 'view', 'details', 'more']):
                            # Look for data attributes
                            data_attrs = ['data-url', 'data-href', 'data-link', 'data-job-url']
                            for attr in data_attrs:
                                attr_value = button.get_attribute(attr)
                                if attr_value:
                                    job_link = attr_value
                                    break

                            if job_link:
                                break

                            # Look for onclick handlers
                            onclick = button.get_attribute('onclick')
                            if onclick:
                                import re
                                url_match = re.search(r'https?://[^\'"]+', onclick)
                                if url_match:
                                    job_link = url_match.group()
                                    break

                # If still no luck, try to extract from any clickable element
                if not job_link:
                    clickable_elements = card.find_elements(By.XPATH, ".//*[@onclick or @href]")
                    for elem in clickable_elements:
                        href = elem.get_attribute('href')
                        onclick = elem.get_attribute('onclick')

                        if href and 'http' in href:
                            job_link = href
                            elem_text = elem.text.strip()
                            if elem_text and len(elem_text) > 3:
                                job_title = elem_text
                            break
                        elif onclick:
                            import re
                            url_match = re.search(r'https?://[^\'"]+', onclick)
                            if url_match:
                                job_link = url_match.group()
                                elem_text = elem.text.strip()
                                if elem_text and len(elem_text) > 3:
                                    job_title = elem_text
                                break


                if job_link:
                    job_info = {
                        "title": job_title,
                        "link": job_link,
                        "index": i + 1
                    }
                    job_links.append(job_info)
                    logger.info(f"Found job {i+1}: {job_title} - {job_link}")
                else:
                    # Debug: show what we found in this card
                    card_text = card.text.strip()[:100] if card.text else "No text"
                    logger.warning(f"No job link found for card {i+1}: {card_text}")

                    # Show all links in this card for debugging
                    all_links = card.find_elements(By.TAG_NAME, "a")
                    if all_links:
                        logger.info(f"  Links in card {i+1}:")
                        for j, link in enumerate(all_links[:3]):  # Show first 3 links
                            href = link.get_attribute('href')
                            text = link.text.strip()[:50] if link.text else "No text"
                            logger.info(f"    {j+1}. {text} -> {href}")
                    else:
                        logger.info(f"  No links found in card {i+1}")

            except Exception as e:
                logger.error(f"Error processing job card {i+1}: {e}")
                continue

    except TimeoutException:
        logger.error("Timeout waiting for job listings to load")
    except Exception as e:
        logger.error(f"Error extracting job links: {e}")

    return job_links

def main():
    """Main function to extract all job links"""
    url = "https://jobright.ai/jobs/recommend"

    driver = setup_driver()

    try:
        job_links = extract_job_links(driver, url)

        # Save results
        results = {
            "url": url,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "total_jobs": len(job_links),
            "jobs": job_links
        }

        output_file = f"jobright_links_{time.strftime('%Y%m%d_%H%M%S')}.json"
        with open(output_file, 'w') as f:
            json.dump(results, f, indent=2)

        # Also save as simple text file
        text_file = f"jobright_links_{time.strftime('%Y%m%d_%H%M%S')}.txt"
        with open(text_file, 'w') as f:
            f.write(f"JobRight.ai Job Links - {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Total jobs found: {len(job_links)}\n\n")
            for job in job_links:
                f.write(f"{job['index']}. {job['title']}\n")
                f.write(f"   {job['link']}\n\n")

        logger.info(f"Successfully extracted {len(job_links)} job links")
        logger.info(f"Results saved to {output_file} and {text_file}")

        # Print summary
        print(f"\n=== JOBRIGHT.AI JOB LINKS EXTRACTED ===")
        print(f"Total jobs found: {len(job_links)}")
        print(f"Results saved to: {output_file}")
        print(f"Text file saved to: {text_file}")
        print("\nFirst 5 job links:")
        for i, job in enumerate(job_links[:5]):
            print(f"{i+1}. {job['title']}")
            print(f"   {job['link']}")

        if len(job_links) > 5:
            print(f"\n... and {len(job_links) - 5} more jobs")

        return job_links

    finally:
        driver.quit()

if __name__ == "__main__":
    main()