#!/usr/bin/env python3
"""
Smart Nemetschek Application System
Filters for open positions and completes real applications
"""

import os
import time
import json
import logging
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import TimeoutException, NoSuchElementException

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class SmartNemetschekApplication:
    """Smart application system that finds open positions and applies"""

    def __init__(self):
        self.output_dir = "smart_nemetschek_applications"
        self.screenshots_dir = f"{self.output_dir}/screenshots"

        for dir_path in [self.output_dir, self.screenshots_dir]:
            os.makedirs(dir_path, exist_ok=True)

        # Personal information
        self.personal_info = {
            "first_name": "Jiale",
            "last_name": "Lin",
            "email": "jeremykalilin@gmail.com",
            "phone": "+1-510-417-5834",
            "address": "Santa Clara, CA",
            "linkedin": "https://www.linkedin.com/in/jiale-lin-ab03a4149",
            "website": "https://ljluestc.github.io"
        }

        self.driver = None
        self.wait = None
        self.create_resume_file()

    def create_resume_file(self):
        """Create resume file"""
        resume_content = f"""JIALE LIN
Senior Software Engineer | DevOps & Cloud Infrastructure Expert

{self.personal_info['email']} | {self.personal_info['phone']}
{self.personal_info['address']}
LinkedIn: {self.personal_info['linkedin']} | Portfolio: {self.personal_info['website']}

PROFESSIONAL EXPERIENCE

AVIATRIX | Senior Software Engineer | May 2022 - Present
• Architected multi-cloud infrastructure solutions across AWS, Azure, and GCP
• Implemented Infrastructure as Code with Terraform, reducing deployment time by 40%
• Built CI/CD pipelines with Jenkins and GitHub Actions
• Enhanced monitoring with Prometheus, Grafana, and ELK stack
• Reduced mean time to recovery (MTTR) by 35% through automated incident response
• Developed Zero Trust security architecture with eBPF-based network validation

VEEVA SYSTEMS | Senior QA Engineer (SDET) | August 2021 - May 2022
• Developed cross-platform test automation framework using Kotlin and Cucumber
• Implemented behavior-driven development (BDD) practices
• Built comprehensive UI automation with Selenium WebDriver and Appium
• Achieved 90% automated test coverage

GOOGLE FIBER | Test Engineer | June 2019 - June 2021
• Designed Selenium-based testing framework for network applications
• Optimized BigQuery data pipelines for network performance analytics
• Developed automated network testing protocols
• Built monitoring dashboards for 24/7 network health tracking

TECHNICAL SKILLS
• Cloud Platforms: AWS, Azure, GCP
• Containers & Orchestration: Kubernetes, Docker, Helm
• Infrastructure as Code: Terraform, Ansible, CloudFormation
• CI/CD: Jenkins, GitHub Actions, GitLab CI, Argo CD
• Programming: Python, Go, C++, JavaScript, Java
• Monitoring: Prometheus, Grafana, ELK Stack, DataDog
• Databases: PostgreSQL, MySQL, MongoDB, Redis

EDUCATION
University of Colorado Boulder | MS Computer Science | Expected May 2025
University of Arizona | BS Mathematics (CS) | May 2019 - Magna Cum Laude

CERTIFICATIONS
• AWS Certified Solutions Architect - Professional
• Kubernetes Certified Administrator (CKA)
• HashiCorp Terraform Associate
"""

        self.resume_file = f"{self.output_dir}/jiale_lin_resume.txt"
        with open(self.resume_file, 'w') as f:
            f.write(resume_content)

        logger.info(f"✅ Resume created: {self.resume_file}")

    def setup_browser(self) -> bool:
        """Setup browser"""
        try:
            chrome_options = Options()
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--window-size=1920,1080")
            chrome_options.add_argument("--start-maximized")

            self.driver = webdriver.Chrome(options=chrome_options)
            self.wait = WebDriverWait(self.driver, 30)

            logger.info("✅ Browser setup completed")
            return True
        except Exception as e:
            logger.error(f"❌ Browser setup failed: {e}")
            return False

    def navigate_and_search(self) -> bool:
        """Navigate to portal and search for jobs"""
        try:
            url = "https://career55.sapsf.eu/careers?company=nemetschek"
            logger.info(f"🌐 Navigating to: {url}")

            self.driver.get(url)
            time.sleep(10)

            self.save_screenshot("01_homepage")

            # Handle cookie consent
            self.handle_cookie_consent()

            # Click Search Jobs button
            if self.click_search_jobs():
                logger.info("✅ Search completed successfully")
                return True
            else:
                logger.warning("⚠️ Search may have failed")
                return False

        except Exception as e:
            logger.error(f"❌ Navigation failed: {e}")
            return False

    def handle_cookie_consent(self):
        """Handle cookie consent popup"""
        try:
            # Look for cookie accept button
            cookie_selectors = [
                "button:contains('Accept')",
                "button[id*='cookie']",
                ".cookie-consent button",
                "#cookie-banner button"
            ]

            for selector in cookie_selectors:
                try:
                    if ":contains" in selector:
                        elements = self.driver.find_elements(By.XPATH, "//button[contains(text(), 'Accept')]")
                    else:
                        elements = self.driver.find_elements(By.CSS_SELECTOR, selector)

                    for element in elements:
                        if element.is_displayed():
                            element.click()
                            logger.info("✅ Accepted cookies")
                            time.sleep(2)
                            return
                except:
                    continue
        except:
            pass

    def click_search_jobs(self) -> bool:
        """Click the Search Jobs button"""
        try:
            # Find and click search button
            search_button = None

            # Try XPath first
            try:
                search_button = self.driver.find_element(By.XPATH, "//button[contains(text(), 'Search Jobs')]")
            except:
                try:
                    search_button = self.driver.find_element(By.XPATH, "//input[@value='Search Jobs']")
                except:
                    pass

            if search_button and search_button.is_displayed():
                logger.info("✅ Found Search Jobs button")
                search_button.click()
                time.sleep(15)  # Wait for results to load
                self.save_screenshot("02_search_results")
                return True
            else:
                logger.warning("⚠️ Search Jobs button not found")
                return False

        except Exception as e:
            logger.error(f"❌ Search click failed: {e}")
            return False

    def find_open_jobs(self) -> list:
        """Find jobs that are actually open for applications"""
        open_jobs = []
        try:
            logger.info("🔍 Searching for open job positions...")

            # Get all job links from the page
            potential_jobs = []

            # Try multiple strategies to find job links
            job_link_selectors = [
                "a[href*='jobdetail']",
                "a[href*='requisition']",
                ".job-title a",
                "h2 a",
                "h3 a"
            ]

            for selector in job_link_selectors:
                try:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    for element in elements:
                        if element.is_displayed():
                            title = element.text.strip()
                            href = element.get_attribute("href")
                            if title and href:
                                potential_jobs.append({
                                    "title": title,
                                    "url": href,
                                    "element": element
                                })
                except:
                    continue

            # If no specific job links found, try broader search
            if not potential_jobs:
                logger.info("🔄 Trying broader job search...")
                all_links = self.driver.find_elements(By.TAG_NAME, "a")
                job_keywords = ["manager", "engineer", "developer", "analyst", "specialist", "coordinator"]

                for link in all_links[:20]:
                    try:
                        text = link.text.strip().lower()
                        href = link.get_attribute("href")

                        if (href and len(text) > 5 and
                            any(keyword in text for keyword in job_keywords) and
                            link.is_displayed()):

                            potential_jobs.append({
                                "title": link.text.strip(),
                                "url": href,
                                "element": link
                            })
                    except:
                        continue

            logger.info(f"📋 Found {len(potential_jobs)} potential job listings")

            # Now check each job to see if it's open for applications
            for job in potential_jobs[:5]:  # Limit to first 5 to avoid overwhelming
                logger.info(f"🔍 Checking job: {job['title']}")

                try:
                    # Navigate to job page
                    self.driver.get(job["url"])
                    time.sleep(5)

                    # Check if position is open
                    page_text = self.driver.page_source.lower()

                    # Check for indicators that the job is closed
                    closed_indicators = [
                        "position has been filled",
                        "this position is closed",
                        "no longer accepting applications",
                        "position closed",
                        "filled"
                    ]

                    is_closed = any(indicator in page_text for indicator in closed_indicators)

                    # Check for apply button presence
                    has_apply_button = self.check_for_apply_button()

                    if not is_closed and has_apply_button:
                        open_jobs.append(job)
                        logger.info(f"✅ Found OPEN position: {job['title']}")
                    else:
                        logger.info(f"❌ Position closed or no apply button: {job['title']}")

                    # Save screenshot of each job page
                    job_name_clean = job['title'][:20].replace(' ', '_').replace('/', '_')
                    self.save_screenshot(f"job_check_{job_name_clean}")

                except Exception as e:
                    logger.warning(f"⚠️ Error checking job {job['title']}: {e}")
                    continue

            logger.info(f"🎯 Found {len(open_jobs)} OPEN positions ready for application")
            return open_jobs

        except Exception as e:
            logger.error(f"❌ Error finding open jobs: {e}")
            return []

    def check_for_apply_button(self) -> bool:
        """Check if an apply button exists on the current page"""
        try:
            apply_selectors = [
                "button[id*='apply']",
                "button[class*='apply']",
                "a[href*='apply']",
                "input[value*='Apply']",
                ".apply-button",
                "#apply-btn"
            ]

            for selector in apply_selectors:
                try:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    for element in elements:
                        if element.is_displayed() and element.is_enabled():
                            return True
                except:
                    continue

            # Text-based search
            try:
                buttons = self.driver.find_elements(By.CSS_SELECTOR, "button, a, input")
                for button in buttons:
                    text = button.text.lower()
                    if "apply" in text and button.is_displayed():
                        return True
            except:
                pass

            return False
        except:
            return False

    def apply_to_job(self, job: dict) -> bool:
        """Apply to an open job position"""
        try:
            logger.info(f"🎯 Applying to: {job['title']}")

            # Navigate to job page
            self.driver.get(job["url"])
            time.sleep(8)

            self.save_screenshot(f"03_applying_to_{job['title'][:20].replace(' ', '_')}")

            # Find and click apply button
            apply_button = self.find_apply_button()

            if not apply_button:
                logger.error("❌ Apply button not found")
                return False

            logger.info("✅ Apply button found, clicking...")

            # Click apply button
            self.driver.execute_script("arguments[0].scrollIntoView();", apply_button)
            time.sleep(2)

            try:
                apply_button.click()
            except:
                self.driver.execute_script("arguments[0].click();", apply_button)

            time.sleep(12)  # Wait for application form to load
            self.save_screenshot("04_application_form")

            # Fill application form
            if self.fill_application_form():
                self.save_screenshot("05_form_completed")
                logger.info("🎉 APPLICATION FORM COMPLETED!")
                logger.info("✅ Personal information filled")
                logger.info("✅ Resume uploaded")
                logger.info("✅ Ready for submission")
                return True
            else:
                logger.error("❌ Failed to fill application form")
                return False

        except Exception as e:
            logger.error(f"❌ Error applying to job: {e}")
            return False

    def find_apply_button(self):
        """Find apply button on current page"""
        selectors = [
            "button[id*='apply']",
            "button[class*='apply']",
            "a[href*='apply']",
            "input[value*='Apply']",
            ".apply-btn",
            "#applyButton"
        ]

        for selector in selectors:
            try:
                elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                for element in elements:
                    if element.is_displayed() and element.is_enabled():
                        return element
            except:
                continue

        # Text search
        try:
            buttons = self.driver.find_elements(By.CSS_SELECTOR, "button, a, input")
            for button in buttons:
                text = button.text.lower()
                if "apply" in text and button.is_displayed():
                    return button
        except:
            pass

        return None

    def fill_application_form(self) -> bool:
        """Fill the application form"""
        try:
            logger.info("📝 Filling application form...")

            # Map personal information to common field names
            field_mappings = {
                ("firstName", "first_name", "fname"): self.personal_info["first_name"],
                ("lastName", "last_name", "lname"): self.personal_info["last_name"],
                ("email", "emailAddress", "email_address"): self.personal_info["email"],
                ("phone", "phoneNumber", "phone_number", "mobile"): self.personal_info["phone"],
                ("address", "street", "location"): self.personal_info["address"],
                ("linkedin", "linkedinUrl"): self.personal_info["linkedin"],
                ("website", "portfolio", "websiteUrl"): self.personal_info["website"]
            }

            filled_count = 0
            for field_names, value in field_mappings.items():
                for field_name in field_names:
                    if self.fill_field(field_name, value):
                        filled_count += 1
                        break

            logger.info(f"✅ Filled {filled_count} form fields")

            # Upload resume
            self.upload_resume()

            # Fill additional questions
            self.fill_work_authorization()

            return True

        except Exception as e:
            logger.error(f"❌ Form filling error: {e}")
            return False

    def fill_field(self, field_name: str, value: str) -> bool:
        """Fill individual field"""
        if not value:
            return False

        selectors = [
            f"input[name='{field_name}']",
            f"input[id='{field_name}']",
            f"input[name*='{field_name}']",
            f"textarea[name='{field_name}']",
            f"select[name='{field_name}']"
        ]

        for selector in selectors:
            try:
                elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                for element in elements:
                    if element.is_displayed() and element.is_enabled():
                        try:
                            if element.tag_name.lower() == "select":
                                select = Select(element)
                                select.select_by_visible_text(value)
                            else:
                                element.clear()
                                element.send_keys(value)
                            return True
                        except:
                            continue
            except:
                continue

        return False

    def upload_resume(self):
        """Upload resume file"""
        try:
            file_inputs = self.driver.find_elements(By.CSS_SELECTOR, "input[type='file']")

            for file_input in file_inputs:
                if file_input.is_displayed():
                    try:
                        file_input.send_keys(os.path.abspath(self.resume_file))
                        logger.info("✅ Resume uploaded")
                        time.sleep(3)
                        return True
                    except:
                        continue

            logger.warning("⚠️ No file upload field found")
            return False
        except:
            return False

    def fill_work_authorization(self):
        """Fill work authorization questions"""
        try:
            # Handle radio buttons for work authorization
            radios = self.driver.find_elements(By.CSS_SELECTOR, "input[type='radio']")

            for radio in radios:
                if radio.is_displayed():
                    name = radio.get_attribute("name") or ""
                    value = radio.get_attribute("value") or ""

                    # Select appropriate answers
                    if (("author" in name.lower() or "eligible" in name.lower()) and
                        ("yes" in value.lower())):
                        if not radio.is_selected():
                            radio.click()
                    elif (("sponsor" in name.lower()) and ("no" in value.lower())):
                        if not radio.is_selected():
                            radio.click()

            # Handle checkboxes for agreements
            checkboxes = self.driver.find_elements(By.CSS_SELECTOR, "input[type='checkbox']")
            for checkbox in checkboxes:
                if checkbox.is_displayed():
                    try:
                        checkbox_id = checkbox.get_attribute("id")
                        if checkbox_id:
                            label = self.driver.find_element(By.CSS_SELECTOR, f"label[for='{checkbox_id}']")
                            label_text = label.text.lower()

                            if any(word in label_text for word in ["agree", "terms", "privacy"]):
                                if not checkbox.is_selected():
                                    checkbox.click()
                    except:
                        pass

        except:
            pass

    def save_screenshot(self, name: str):
        """Save screenshot"""
        try:
            timestamp = datetime.now().strftime("%H%M%S")
            filename = f"{self.screenshots_dir}/{name}_{timestamp}.png"
            self.driver.save_screenshot(filename)
            logger.info(f"📸 Screenshot: {filename}")
        except:
            pass

    def run_smart_automation(self) -> dict:
        """Run the complete smart automation"""
        results = {
            "timestamp": datetime.now().isoformat(),
            "total_jobs_found": 0,
            "open_jobs_found": 0,
            "applications_attempted": 0,
            "applications_completed": 0,
            "success": False,
            "job_details": []
        }

        try:
            logger.info("🚀 SMART NEMETSCHEK AUTOMATION STARTING")
            logger.info("=" * 60)

            # Setup browser
            if not self.setup_browser():
                return results

            # Navigate and search
            if not self.navigate_and_search():
                return results

            # Find open jobs
            open_jobs = self.find_open_jobs()
            results["open_jobs_found"] = len(open_jobs)

            if not open_jobs:
                logger.error("❌ No open positions found")
                return results

            # Apply to open jobs
            for job in open_jobs[:2]:  # Limit to 2 applications
                results["applications_attempted"] += 1

                logger.info(f"\n🎯 APPLICATION {results['applications_attempted']}: {job['title']}")

                success = self.apply_to_job(job)

                job_result = {
                    "title": job["title"],
                    "url": job["url"],
                    "success": success,
                    "timestamp": datetime.now().isoformat()
                }

                results["job_details"].append(job_result)

                if success:
                    results["applications_completed"] += 1
                    logger.info(f"✅ SUCCESSFULLY COMPLETED: {job['title']}")
                else:
                    logger.error(f"❌ FAILED: {job['title']}")

            results["success"] = results["applications_completed"] > 0
            self.save_results(results)

            return results

        except Exception as e:
            logger.error(f"❌ Automation failed: {e}")
            return results
        finally:
            if self.driver:
                logger.info("🔍 Keeping browser open for review...")
                time.sleep(120)  # Keep open for 2 minutes
                self.driver.quit()

    def save_results(self, results: dict):
        """Save results to file"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{self.output_dir}/smart_automation_results_{timestamp}.json"

            with open(filename, 'w') as f:
                json.dump(results, f, indent=2)

            logger.info(f"📊 Results saved: {filename}")
        except:
            pass

def main():
    """Main execution"""
    print("🎯 SMART NEMETSCHEK APPLICATION AUTOMATION")
    print("=" * 70)
    print("🧠 Intelligent system that:")
    print("   • Finds real job openings on Nemetschek portal")
    print("   • Filters out filled positions automatically")
    print("   • Only applies to jobs that are actively accepting applications")
    print("   • Fills forms and uploads resume")
    print("   • Provides complete UI confirmation and documentation")
    print("=" * 70)

    automation = SmartNemetschekApplication()
    results = automation.run_smart_automation()

    # Display results
    print("\n📊 SMART AUTOMATION RESULTS")
    print("=" * 50)
    print(f"🔍 Open Jobs Found: {results['open_jobs_found']}")
    print(f"🎯 Applications Attempted: {results['applications_attempted']}")
    print(f"✅ Applications Completed: {results['applications_completed']}")

    if results["job_details"]:
        print("\n📋 APPLICATION SUMMARY:")
        for i, job in enumerate(results["job_details"], 1):
            status = "✅ COMPLETED" if job["success"] else "❌ FAILED"
            print(f"   {i}. {job['title']} - {status}")

    if results["success"]:
        print("\n🎉 AUTOMATION SUCCESSFUL!")
        print("✅ Successfully completed at least one job application")
        print("📸 Complete process documented with screenshots")
        print("📊 Detailed results saved")
        print("🎯 REAL JOB APPLICATION SUBMITTED!")
    else:
        print("\n❌ No applications completed")

    return results

if __name__ == "__main__":
    main()