#!/usr/bin/env python3
"""
Interactive job link extractor for jobright.ai using click simulation
"""

import time
import json
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import TimeoutException, NoSuchElementException, ElementClickInterceptedException
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

def extract_job_links_interactive(driver, url):
    """Extract job links by simulating user interactions"""
    logger.info(f"Navigating to {url}")
    driver.get(url)

    # Wait for page to load
    time.sleep(20)

    job_links = []

    try:
        logger.info(f"Page title: {driver.title}")

        # Trigger initial scroll and wait for content
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight/4);")
        time.sleep(5)
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight/2);")
        time.sleep(5)
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(5)
        driver.execute_script("window.scrollTo(0, 0);")
        time.sleep(3)

        # Look for job elements with text
        job_elements = driver.find_elements(By.XPATH, "//*[contains(text(), 'Software Engineer') or contains(text(), 'Manager') or contains(text(), 'Developer') or contains(text(), 'Analyst') or contains(text(), 'Designer')]")
        logger.info(f"Found {len(job_elements)} potential job title elements")

        # Try to find clickable parent elements
        job_cards = set()
        for element in job_elements:
            try:
                # Look for clickable parent containers
                parent = element
                for _ in range(5):  # Go up 5 levels max
                    parent = parent.find_element(By.XPATH, "..")
                    if parent.tag_name.lower() in ['div', 'article', 'section']:
                        # Check if this parent has clickable elements
                        clickable_children = parent.find_elements(By.XPATH, ".//*[@onclick or contains(@class, 'btn') or contains(@class, 'button') or contains(@class, 'apply') or contains(@class, 'link')]")
                        if clickable_children:
                            job_cards.add(parent)
                            break
            except:
                continue

        job_cards = list(job_cards)
        logger.info(f"Found {len(job_cards)} job card containers")

        # Process each job card
        for i, card in enumerate(job_cards[:10]):  # Limit to first 10 for testing
            try:
                # Get job title
                job_title = "Unknown"
                title_element = None

                # Look for title text
                title_texts = card.find_elements(By.XPATH, ".//*[contains(text(), 'Engineer') or contains(text(), 'Manager') or contains(text(), 'Developer') or contains(text(), 'Designer') or contains(text(), 'Analyst')]")
                if title_texts:
                    job_title = title_texts[0].text.strip()
                    title_element = title_texts[0]

                logger.info(f"Processing job {i+1}: {job_title}")

                # Try to click on the job card or title to see if it navigates
                job_link = None

                # Method 1: Try clicking the title element
                if title_element:
                    try:
                        # Store current window handles
                        original_windows = driver.window_handles
                        original_url = driver.current_url

                        # Click the title
                        ActionChains(driver).move_to_element(title_element).click().perform()
                        time.sleep(3)

                        # Check if new tab/window opened
                        new_windows = driver.window_handles
                        if len(new_windows) > len(original_windows):
                            # New window opened
                            driver.switch_to.window(new_windows[-1])
                            job_link = driver.current_url
                            driver.close()
                            driver.switch_to.window(original_windows[0])
                            logger.info(f"Found job link via title click: {job_link}")
                        elif driver.current_url != original_url:
                            # Same window navigation
                            job_link = driver.current_url
                            driver.back()
                            time.sleep(2)
                            logger.info(f"Found job link via navigation: {job_link}")
                    except Exception as e:
                        logger.debug(f"Title click failed: {e}")

                # Method 2: Try clicking buttons in the card
                if not job_link:
                    buttons = card.find_elements(By.XPATH, ".//button[contains(text(), 'Apply') or contains(text(), 'View') or contains(text(), 'Details') or contains(@class, 'apply') or contains(@class, 'btn')]")

                    for button in buttons:
                        try:
                            original_windows = driver.window_handles
                            original_url = driver.current_url

                            # Scroll to button and click
                            driver.execute_script("arguments[0].scrollIntoView(true);", button)
                            time.sleep(1)
                            ActionChains(driver).move_to_element(button).click().perform()
                            time.sleep(3)

                            # Check for new window/navigation
                            new_windows = driver.window_handles
                            if len(new_windows) > len(original_windows):
                                driver.switch_to.window(new_windows[-1])
                                job_link = driver.current_url
                                driver.close()
                                driver.switch_to.window(original_windows[0])
                                logger.info(f"Found job link via button click: {job_link}")
                                break
                            elif driver.current_url != original_url:
                                job_link = driver.current_url
                                driver.back()
                                time.sleep(2)
                                logger.info(f"Found job link via button navigation: {job_link}")
                                break
                        except Exception as e:
                            logger.debug(f"Button click failed: {e}")
                            continue

                # Method 3: Try JavaScript execution to find hidden links
                if not job_link:
                    try:
                        # Execute JavaScript to find any data attributes or hidden URLs
                        js_result = driver.execute_script("""
                            var card = arguments[0];
                            var allElements = card.querySelectorAll('*');
                            var urls = [];

                            for (var i = 0; i < allElements.length; i++) {
                                var elem = allElements[i];

                                // Check data attributes
                                var attrs = ['data-url', 'data-href', 'data-link', 'data-job-url', 'data-apply-url'];
                                for (var j = 0; j < attrs.length; j++) {
                                    var val = elem.getAttribute(attrs[j]);
                                    if (val && val.startsWith('http')) {
                                        urls.push(val);
                                    }
                                }

                                // Check onclick handlers
                                var onclick = elem.getAttribute('onclick');
                                if (onclick && onclick.includes('http')) {
                                    var match = onclick.match(/https?:\/\/[^\s'"]+/);
                                    if (match) {
                                        urls.push(match[0]);
                                    }
                                }
                            }

                            return urls;
                        """, card)

                        if js_result:
                            job_link = js_result[0]
                            logger.info(f"Found job link via JavaScript: {job_link}")
                    except Exception as e:
                        logger.debug(f"JavaScript extraction failed: {e}")

                if job_link:
                    job_info = {
                        "title": job_title,
                        "link": job_link,
                        "index": i + 1
                    }
                    job_links.append(job_info)
                    logger.info(f"Successfully extracted job {i+1}: {job_title} - {job_link}")
                else:
                    logger.warning(f"Could not extract link for job {i+1}: {job_title}")

            except Exception as e:
                logger.error(f"Error processing job card {i+1}: {e}")
                continue

    except Exception as e:
        logger.error(f"Error in main extraction: {e}")

    return job_links

def main():
    """Main function to extract all job links"""
    url = "https://jobright.ai/jobs/recommend"

    driver = setup_driver()

    try:
        job_links = extract_job_links_interactive(driver, url)

        # Save results
        results = {
            "url": url,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "total_jobs": len(job_links),
            "jobs": job_links
        }

        output_file = f"jobright_interactive_links_{time.strftime('%Y%m%d_%H%M%S')}.json"
        with open(output_file, 'w') as f:
            json.dump(results, f, indent=2)

        # Also save as simple text file
        text_file = f"jobright_interactive_links_{time.strftime('%Y%m%d_%H%M%S')}.txt"
        with open(text_file, 'w') as f:
            f.write(f"JobRight.ai Interactive Job Links - {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Total jobs found: {len(job_links)}\n\n")
            for job in job_links:
                f.write(f"{job['index']}. {job['title']}\n")
                f.write(f"   {job['link']}\n\n")

        logger.info(f"Successfully extracted {len(job_links)} job links")
        logger.info(f"Results saved to {output_file} and {text_file}")

        # Print summary
        print(f"\n=== JOBRIGHT.AI INTERACTIVE JOB LINKS EXTRACTED ===")
        print(f"Total jobs found: {len(job_links)}")
        print(f"Results saved to: {output_file}")
        print(f"Text file saved to: {text_file}")
        print("\nAll job links:")
        for job in job_links:
            print(f"{job['index']}. {job['title']}")
            print(f"   {job['link']}")

        return job_links

    finally:
        driver.quit()

if __name__ == "__main__":
    main()