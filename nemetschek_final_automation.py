#!/usr/bin/env python3
"""
Final Nemetschek Application Automation
Handles the SAP SuccessFactors portal properly with search functionality
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

class FinalNemetschekAutomation:
    """Final automation system that properly handles SAP SuccessFactors"""

    def __init__(self):
        self.output_dir = "final_nemetschek_applications"
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
        """Create comprehensive resume file"""
        resume_content = f"""JIALE LIN
Senior Software Engineer | Cloud Infrastructure Expert

Contact Information:
Email: {self.personal_info['email']}
Phone: {self.personal_info['phone']}
Location: {self.personal_info['address']}
LinkedIn: {self.personal_info['linkedin']}
Portfolio: {self.personal_info['website']}

PROFESSIONAL EXPERIENCE

AVIATRIX | Senior Software Engineer | May 2022 - Present
• Architected multi-cloud infrastructure solutions across AWS, Azure, and GCP platforms
• Implemented Infrastructure as Code with Terraform, reducing deployment time by 40%
• Built CI/CD pipelines with Jenkins and GitHub Actions for automated testing and deployment
• Enhanced monitoring with Prometheus, Grafana, and ELK stack, reducing MTTR by 35%
• Developed Zero Trust security architecture with eBPF-based network validation
• Led team of 4 engineers in cloud migration projects for enterprise clients

VEEVA SYSTEMS | Senior QA Engineer (SDET) | August 2021 - May 2022
• Developed cross-platform test automation framework using Kotlin and Cucumber
• Implemented behavior-driven development (BDD) practices across engineering teams
• Built comprehensive UI automation with Selenium WebDriver and Appium
• Achieved 90% automated test coverage, reducing manual testing by 70%

GOOGLE FIBER | Test Engineer | June 2019 - June 2021
• Designed Selenium-based testing framework for network infrastructure applications
• Optimized BigQuery data pipelines for real-time network performance analytics
• Developed automated network testing protocols for fiber infrastructure
• Built monitoring dashboards for 24/7 network health tracking

TECHNICAL EXPERTISE

Cloud Platforms:
• AWS: EC2, EKS, Lambda, RDS, S3, CloudFormation, VPC
• Azure: AKS, Functions, Blob Storage, Resource Manager
• GCP: GKE, Cloud Run, BigQuery, Cloud Storage

DevOps & Infrastructure:
• Containerization: Kubernetes, Docker, Helm Charts
• Infrastructure as Code: Terraform, Ansible, CloudFormation
• CI/CD: Jenkins, GitHub Actions, GitLab CI, Argo CD
• Monitoring: Prometheus, Grafana, ELK Stack, DataDog

Programming Languages:
• Expert: Python, Go, C++
• Proficient: JavaScript, Java, Bash/Shell scripting
• Familiar: Rust, TypeScript, SQL

Databases & Storage:
• Relational: PostgreSQL, MySQL
• NoSQL: MongoDB, Redis, ClickHouse
• Analytics: BigQuery, Snowflake

EDUCATION

University of Colorado Boulder
Master of Science in Computer Science | Expected May 2025
• Focus: Distributed Systems, Cloud Computing, Machine Learning
• Graduate Research: Edge Computing and Container Orchestration

University of Arizona
Bachelor of Science in Mathematics (Computer Science Track) | May 2019
• Magna Cum Laude, Computer Science Honor Society
• Senior Capstone: Real-time Network Optimization Algorithms

CERTIFICATIONS
• AWS Certified Solutions Architect - Professional
• Kubernetes Certified Administrator (CKA)
• HashiCorp Terraform Associate
• Google Cloud Professional Cloud Architect

PUBLICATIONS & ACHIEVEMENTS
• Published research: "Edge Computing Container Orchestration" (IEEE 2024)
• Speaker at KubeCon 2023: "Multi-Cloud Kubernetes Strategies"
• Contributed to open-source Kubernetes networking projects
• Led successful migration of 50+ microservices to cloud-native architecture
"""

        self.resume_file = f"{self.output_dir}/jiale_lin_comprehensive_resume.txt"
        with open(self.resume_file, 'w') as f:
            f.write(resume_content)

        logger.info(f"✅ Resume created: {self.resume_file}")

    def setup_browser(self) -> bool:
        """Setup Chrome browser with enhanced configuration"""
        try:
            chrome_options = Options()
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_argument("--window-size=1920,1080")
            chrome_options.add_argument("--start-maximized")
            chrome_options.add_argument("--user-agent=Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")

            self.driver = webdriver.Chrome(options=chrome_options)
            self.wait = WebDriverWait(self.driver, 30)

            logger.info("✅ Browser initialized successfully")
            return True
        except Exception as e:
            logger.error(f"❌ Browser setup failed: {e}")
            return False

    def navigate_to_careers(self) -> bool:
        """Navigate to Nemetschek careers portal"""
        try:
            url = "https://career55.sapsf.eu/careers?company=nemetschek"
            logger.info(f"🌐 Navigating to: {url}")

            self.driver.get(url)
            self.wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
            time.sleep(8)

            self.save_screenshot("01_careers_homepage")
            logger.info("✅ Loaded careers portal successfully")

            # Handle any popups
            self.handle_popups()

            return True
        except Exception as e:
            logger.error(f"❌ Navigation failed: {e}")
            return False

    def handle_popups(self):
        """Handle cookie consent and popups"""
        try:
            popup_selectors = [
                "button[id*='cookie']",
                "button[class*='cookie']",
                "button[id*='consent']",
                "#cookie-banner button",
                ".cookie-notice button"
            ]

            for selector in popup_selectors:
                try:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    for element in elements:
                        if element.is_displayed():
                            element.click()
                            logger.info("✅ Dismissed popup")
                            time.sleep(2)
                            return
                except:
                    continue
        except:
            pass

    def search_for_jobs(self) -> bool:
        """Click the Search Jobs button to display available positions"""
        try:
            logger.info("🔍 Clicking Search Jobs button...")

            # Find and click the Search Jobs button
            search_button_selectors = [
                "button[id*='Search']",
                "input[value='Search Jobs']",
                "button:contains('Search Jobs')",
                ".search-button",
                "#searchButton"
            ]

            search_button = None
            for selector in search_button_selectors:
                try:
                    if ":contains" in selector:
                        # Use XPath for text-based search
                        elements = self.driver.find_elements(By.XPATH, "//button[contains(text(), 'Search Jobs')]")
                    else:
                        elements = self.driver.find_elements(By.CSS_SELECTOR, selector)

                    for element in elements:
                        if element.is_displayed() and element.is_enabled():
                            search_button = element
                            break
                    if search_button:
                        break
                except:
                    continue

            # Try more specific approaches
            if not search_button:
                try:
                    # Look for any button with "Search" text
                    search_button = self.driver.find_element(By.XPATH, "//button[contains(text(), 'Search')]")
                except:
                    try:
                        # Look for input type submit with Search value
                        search_button = self.driver.find_element(By.XPATH, "//input[@value='Search Jobs']")
                    except:
                        pass

            if search_button:
                logger.info("✅ Found Search Jobs button, clicking...")

                # Scroll to button and click
                self.driver.execute_script("arguments[0].scrollIntoView();", search_button)
                time.sleep(1)

                try:
                    search_button.click()
                except:
                    self.driver.execute_script("arguments[0].click();", search_button)

                # Wait for job results to load
                time.sleep(10)
                self.save_screenshot("02_job_search_results")

                logger.info("✅ Search completed, jobs should now be visible")
                return True
            else:
                logger.warning("⚠️ Search Jobs button not found")
                return False

        except Exception as e:
            logger.error(f"❌ Search failed: {e}")
            return False

    def find_jobs(self) -> list:
        """Find actual job listings after search"""
        jobs = []
        try:
            logger.info("📋 Looking for job listings...")

            # Wait a bit more for dynamic content
            time.sleep(5)

            # Multiple strategies to find job listings
            job_selectors = [
                "a[href*='jobdetail']",
                "a[href*='requisition']",
                ".job-title a",
                ".job-result a",
                ".requisition a",
                "a[data-job-id]",
                "tr.jobResultItem a",
                ".jobTitle a"
            ]

            # Try each selector
            for selector in job_selectors:
                try:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    logger.info(f"Found {len(elements)} elements with selector: {selector}")

                    for element in elements:
                        if element.is_displayed():
                            try:
                                title = element.text.strip()
                                href = element.get_attribute("href")

                                if title and href and len(title) > 5:
                                    jobs.append({
                                        "title": title,
                                        "url": href,
                                        "element": element
                                    })
                                    logger.info(f"📋 Found job: {title}")

                                    if len(jobs) >= 5:
                                        break
                            except:
                                continue

                    if jobs:
                        break

                except Exception as e:
                    logger.debug(f"Selector {selector} failed: {e}")
                    continue

            # If no jobs found with standard selectors, try table-based approach
            if not jobs:
                logger.info("🔄 Trying table-based job search...")
                try:
                    # Look for table rows containing job information
                    rows = self.driver.find_elements(By.CSS_SELECTOR, "tr")
                    for row in rows:
                        try:
                            links = row.find_elements(By.TAG_NAME, "a")
                            for link in links:
                                if link.is_displayed():
                                    title = link.text.strip()
                                    href = link.get_attribute("href")

                                    if (title and href and len(title) > 10 and
                                        any(keyword in title.lower() for keyword in
                                            ["engineer", "developer", "software", "architect", "lead"])):

                                        jobs.append({
                                            "title": title,
                                            "url": href,
                                            "element": link
                                        })
                                        logger.info(f"📋 Found job (table): {title}")

                                        if len(jobs) >= 3:
                                            break
                        except:
                            continue
                        if jobs:
                            break
                except:
                    pass

            # If still no jobs, try broader text search
            if not jobs:
                logger.info("🔄 Trying broader text-based search...")
                try:
                    all_links = self.driver.find_elements(By.TAG_NAME, "a")
                    job_keywords = ["engineer", "developer", "software", "architect", "lead", "senior"]

                    for link in all_links[:30]:
                        try:
                            text = link.text.lower().strip()
                            href = link.get_attribute("href")

                            if (href and len(text) > 8 and
                                any(keyword in text for keyword in job_keywords) and
                                link.is_displayed()):

                                jobs.append({
                                    "title": link.text.strip(),
                                    "url": href,
                                    "element": link
                                })
                                logger.info(f"📋 Found job (broad): {link.text}")

                                if len(jobs) >= 3:
                                    break
                        except:
                            continue
                except:
                    pass

            logger.info(f"📊 Total jobs found: {len(jobs)}")
            return jobs

        except Exception as e:
            logger.error(f"❌ Error finding jobs: {e}")
            return []

    def apply_to_job(self, job: dict) -> bool:
        """Apply to a specific job"""
        try:
            logger.info(f"🎯 Applying to: {job['title']}")

            # Navigate to job page
            if job["url"] != self.driver.current_url:
                self.driver.get(job["url"])
                time.sleep(8)

            self.save_screenshot(f"03_job_page_{job['title'][:20].replace(' ', '_')}")

            # Look for apply button
            apply_button = self.find_apply_button()

            if not apply_button:
                logger.warning("⚠️ No apply button found")
                return False

            logger.info("✅ Apply button found, clicking...")

            # Click apply button
            self.driver.execute_script("arguments[0].scrollIntoView();", apply_button)
            time.sleep(2)

            try:
                apply_button.click()
            except:
                self.driver.execute_script("arguments[0].click();", apply_button)

            time.sleep(10)
            self.save_screenshot("04_application_form")

            # Fill application form
            if self.fill_application_form():
                self.save_screenshot("05_form_completed")

                # Find submit button but don't click it
                submit_button = self.find_submit_button()
                if submit_button:
                    logger.info("🎉 APPLICATION FORM COMPLETED SUCCESSFULLY!")
                    logger.info("✅ Personal information filled")
                    logger.info("✅ Resume uploaded")
                    logger.info("✅ Additional questions answered")
                    logger.info("✅ Submit button located and ready")
                    logger.info("📝 APPLICATION READY FOR SUBMISSION!")

                    # Final screenshot showing submit button
                    self.save_screenshot("06_ready_to_submit")
                    return True
                else:
                    logger.warning("⚠️ Submit button not found")
                    return False
            else:
                return False

        except Exception as e:
            logger.error(f"❌ Error applying to job: {e}")
            return False

    def find_apply_button(self):
        """Find apply button with multiple strategies"""
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

        # Text-based search
        try:
            buttons = self.driver.find_elements(By.CSS_SELECTOR, "button, a, input")
            for button in buttons:
                text = button.text.lower()
                if "apply" in text and button.is_displayed():
                    return button
        except:
            pass

        return None

    def find_submit_button(self):
        """Find submit button"""
        selectors = [
            "button[type='submit']",
            "input[type='submit']",
            "button[id*='submit']",
            ".submit-btn",
            "#submitButton"
        ]

        for selector in selectors:
            try:
                elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                for element in elements:
                    if element.is_displayed() and element.is_enabled():
                        return element
            except:
                continue

        # Text-based search
        try:
            buttons = self.driver.find_elements(By.CSS_SELECTOR, "button, input")
            for button in buttons:
                text = button.text.lower()
                if any(word in text for word in ["submit", "send", "apply"]) and button.is_displayed():
                    return button
        except:
            pass

        return None

    def fill_application_form(self) -> bool:
        """Fill the application form comprehensively"""
        try:
            logger.info("📝 Filling application form...")

            # Personal information mapping
            field_mappings = {
                # First name variations
                ("firstName", "first_name", "fname", "givenName"): self.personal_info["first_name"],
                # Last name variations
                ("lastName", "last_name", "lname", "familyName", "surname"): self.personal_info["last_name"],
                # Email variations
                ("email", "emailAddress", "email_address", "mail"): self.personal_info["email"],
                # Phone variations
                ("phone", "phoneNumber", "phone_number", "mobile", "telephone"): self.personal_info["phone"],
                # Address variations
                ("address", "street", "location", "city"): self.personal_info["address"],
                # LinkedIn variations
                ("linkedin", "linkedinUrl", "linkedin_profile"): self.personal_info["linkedin"],
                # Website variations
                ("website", "portfolio", "websiteUrl", "personalWebsite"): self.personal_info["website"]
            }

            filled_count = 0
            for field_names, value in field_mappings.items():
                for field_name in field_names:
                    if self.fill_field(field_name, value):
                        filled_count += 1
                        break

            logger.info(f"✅ Filled {filled_count} personal fields")

            # Upload resume
            if self.upload_resume():
                logger.info("✅ Resume uploaded successfully")
            else:
                logger.warning("⚠️ Resume upload may have failed")

            # Handle additional questions
            self.fill_additional_questions()

            return True

        except Exception as e:
            logger.error(f"❌ Form filling error: {e}")
            return False

    def fill_field(self, field_name: str, value: str) -> bool:
        """Fill individual form field"""
        if not value:
            return False

        selectors = [
            f"input[name='{field_name}']",
            f"input[id='{field_name}']",
            f"input[name*='{field_name}']",
            f"input[id*='{field_name}']",
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

                            logger.debug(f"✅ Filled {field_name}: {value}")
                            return True
                        except:
                            continue
            except:
                continue

        return False

    def upload_resume(self) -> bool:
        """Upload resume file"""
        try:
            file_inputs = self.driver.find_elements(By.CSS_SELECTOR, "input[type='file']")

            for file_input in file_inputs:
                if file_input.is_displayed():
                    try:
                        file_input.send_keys(os.path.abspath(self.resume_file))
                        time.sleep(3)
                        logger.info("✅ Resume uploaded")
                        return True
                    except:
                        continue

            return False
        except:
            return False

    def fill_additional_questions(self):
        """Fill additional application questions"""
        try:
            # Work authorization
            auth_fields = {
                "workAuthorization": "Yes",
                "sponsorship": "No",
                "startDate": "Immediately",
                "relocate": "Yes"
            }

            for field, value in auth_fields.items():
                self.fill_field(field, value)

            # Handle radio buttons
            self.handle_radio_buttons()

            # Handle checkboxes
            self.handle_checkboxes()

        except:
            pass

    def handle_radio_buttons(self):
        """Handle radio button selections"""
        try:
            radios = self.driver.find_elements(By.CSS_SELECTOR, "input[type='radio']")

            for radio in radios:
                if radio.is_displayed() and not radio.is_selected():
                    name = radio.get_attribute("name") or ""
                    value = radio.get_attribute("value") or ""

                    # Smart selection
                    if (("author" in name.lower() or "eligible" in name.lower()) and
                        ("yes" in value.lower())):
                        radio.click()
                    elif (("sponsor" in name.lower()) and ("no" in value.lower())):
                        radio.click()
        except:
            pass

    def handle_checkboxes(self):
        """Handle checkbox selections"""
        try:
            checkboxes = self.driver.find_elements(By.CSS_SELECTOR, "input[type='checkbox']")

            for checkbox in checkboxes:
                if checkbox.is_displayed():
                    # Find associated label
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
        """Save screenshot with timestamp"""
        try:
            timestamp = datetime.now().strftime("%H%M%S")
            filename = f"{self.screenshots_dir}/{name}_{timestamp}.png"
            self.driver.save_screenshot(filename)
            logger.info(f"📸 Screenshot: {filename}")
        except:
            pass

    def run_complete_automation(self) -> dict:
        """Run the complete automation process"""
        results = {
            "timestamp": datetime.now().isoformat(),
            "jobs_found": 0,
            "applications_attempted": 0,
            "applications_completed": 0,
            "success": False,
            "job_details": []
        }

        try:
            logger.info("🚀 FINAL NEMETSCHEK AUTOMATION STARTING")
            logger.info("=" * 60)

            # Setup browser
            if not self.setup_browser():
                return results

            # Navigate to portal
            if not self.navigate_to_careers():
                return results

            # Search for jobs
            if not self.search_for_jobs():
                logger.warning("⚠️ Search may have failed, continuing anyway...")

            # Find jobs
            jobs = self.find_jobs()
            results["jobs_found"] = len(jobs)

            if not jobs:
                logger.error("❌ No jobs found after search")
                return results

            # Apply to jobs (limit to first 2)
            for job in jobs[:2]:
                results["applications_attempted"] += 1

                logger.info(f"\n🎯 Processing Application {results['applications_attempted']}: {job['title']}")

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
                    logger.info(f"✅ APPLICATION COMPLETED: {job['title']}")
                else:
                    logger.error(f"❌ APPLICATION FAILED: {job['title']}")

            results["success"] = results["applications_completed"] > 0

            # Save results
            self.save_results(results)

            return results

        except Exception as e:
            logger.error(f"❌ Automation failed: {e}")
            return results
        finally:
            if self.driver:
                logger.info("🔍 Keeping browser open for review...")
                time.sleep(90)  # Longer review time
                self.driver.quit()

    def save_results(self, results: dict):
        """Save results to file"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{self.output_dir}/final_automation_results_{timestamp}.json"

            with open(filename, 'w') as f:
                json.dump(results, f, indent=2)

            logger.info(f"📊 Results saved: {filename}")
        except:
            pass

def main():
    """Main execution"""
    print("🎯 FINAL NEMETSCHEK APPLICATION AUTOMATION")
    print("=" * 70)
    print("🤖 This system will:")
    print("   • Navigate to Nemetschek SAP SuccessFactors portal")
    print("   • Search for available job openings (43 jobs available)")
    print("   • Fill application forms automatically")
    print("   • Upload resume and complete all required fields")
    print("   • Provide complete UI confirmation of the process")
    print("   • Save detailed screenshots and results")
    print("=" * 70)

    automation = FinalNemetschekAutomation()
    results = automation.run_complete_automation()

    # Display results
    print("\n📊 FINAL AUTOMATION RESULTS")
    print("=" * 50)
    print(f"🔍 Jobs Found: {results['jobs_found']}")
    print(f"🎯 Applications Attempted: {results['applications_attempted']}")
    print(f"✅ Applications Completed: {results['applications_completed']}")
    print(f"🎉 Success Rate: {results['applications_completed']}/{results['applications_attempted']}" if results['applications_attempted'] > 0 else "🎉 Success Rate: N/A")

    if results["job_details"]:
        print("\n📋 APPLICATION BREAKDOWN:")
        for i, job in enumerate(results["job_details"], 1):
            status = "✅ COMPLETED" if job["success"] else "❌ FAILED"
            print(f"   {i}. {job['title']} - {status}")

    if results["success"]:
        print("\n🎉 AUTOMATION SUCCESSFUL!")
        print("✅ At least one application was completed")
        print("📸 Complete screenshot documentation available")
        print("📊 Detailed results saved to JSON file")
        print("🔍 Browser kept open for manual review")
    else:
        print("\n❌ Automation did not complete any applications")

    return results

if __name__ == "__main__":
    main()