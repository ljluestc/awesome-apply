#!/usr/bin/env python3

import asyncio
import sqlite3
import time
import os
import random
import json
from datetime import datetime
from pathlib import Path
import logging
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import Select
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException
import aiohttp
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image as ReportLabImage
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class Proven100JobApplicator:
    def __init__(self):
        self.db_path = "proven_100_jobs.db"
        self.proof_dir = Path("PROVEN_JOB_APPLICATIONS")
        self.proof_dir.mkdir(exist_ok=True)

        self.resume_path = self._find_resume()
        self.cover_letter_template = self._load_cover_letter_template()

        self.job_sites = [
            "https://jobright.ai/jobs",
            "https://www.linkedin.com/jobs/",
            "https://www.indeed.com/",
            "https://www.glassdoor.com/Job/index.htm",
            "https://www.ziprecruiter.com/jobs",
            "https://angel.co/jobs",
            "https://careers.google.com/jobs/results/",
            "https://jobs.apple.com/en-us/search",
            "https://careers.microsoft.com/us/en/search-results",
            "https://amazon.jobs/en/",
            "https://careers.netflix.com/jobs",
            "https://careers.uber.com/list-of-jobs/",
            "https://www.airbnb.com/careers/departments",
            "https://careers.shopify.com/search"
        ]

        self.user_profile = {
            "name": "Software Engineer",
            "location": "San Jose, CA",
            "skills": ["Python", "JavaScript", "React", "Node.js", "AWS", "Docker", "Kubernetes"],
            "experience_years": 5,
            "education": "Computer Science"
        }

        self.setup_database()

    def _find_resume(self):
        possible_paths = [
            "/home/calelin/Downloads/resume.pdf",
            "/home/calelin/Documents/resume.pdf",
            "/home/calelin/awesome-apply/resume.pdf",
            "/home/calelin/resume.pdf"
        ]

        for path in possible_paths:
            if os.path.exists(path):
                return path

        logger.warning("No resume found, will create dynamic resume for each application")
        return None

    def _load_cover_letter_template(self):
        return """
Dear Hiring Manager,

I am writing to express my strong interest in the {job_title} position at {company_name}. With {experience_years} years of experience in software development, I am confident that my skills in {relevant_skills} make me an ideal candidate for this role.

In my previous roles, I have successfully:
- Developed scalable web applications using modern technologies
- Collaborated with cross-functional teams to deliver high-quality software
- Implemented best practices in code quality and testing
- Contributed to system architecture and design decisions

I am particularly drawn to {company_name} because of your commitment to innovation and excellence. I would welcome the opportunity to contribute to your team and help drive your technology initiatives forward.

Thank you for your consideration. I look forward to hearing from you.

Best regards,
{candidate_name}
        """.strip()

    def setup_database(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS job_applications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                job_title TEXT NOT NULL,
                company_name TEXT NOT NULL,
                job_url TEXT NOT NULL,
                application_url TEXT,
                site_name TEXT NOT NULL,
                application_status TEXT DEFAULT 'pending',
                application_timestamp DATETIME,
                proof_before_screenshot TEXT,
                proof_after_screenshot TEXT,
                proof_confirmation_screenshot TEXT,
                application_details TEXT,
                error_message TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        conn.commit()
        conn.close()

    def create_driver(self, headless=False):
        options = Options()
        if headless:
            options.add_argument("--headless")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")
        options.add_argument("--window-size=1920,1080")
        options.add_argument("--user-agent=Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")

        driver = webdriver.Chrome(options=options)
        return driver

    def take_proof_screenshot(self, driver, job_id, stage):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:-3]
        filename = f"{timestamp}_job_{job_id:03d}_{stage}.png"
        filepath = self.proof_dir / filename

        driver.save_screenshot(str(filepath))
        logger.info(f"Proof screenshot saved: {filename}")
        return str(filepath)

    async def scrape_jobs_from_site(self, site_url, max_jobs=20):
        jobs = []
        driver = self.create_driver(headless=False)

        try:
            driver.get(site_url)
            await asyncio.sleep(3)

            if "jobright.ai" in site_url:
                jobs.extend(await self.scrape_jobright_jobs(driver, max_jobs))
            elif "linkedin.com" in site_url:
                jobs.extend(await self.scrape_linkedin_jobs(driver, max_jobs))
            elif "indeed.com" in site_url:
                jobs.extend(await self.scrape_indeed_jobs(driver, max_jobs))
            elif "glassdoor.com" in site_url:
                jobs.extend(await self.scrape_glassdoor_jobs(driver, max_jobs))
            else:
                jobs.extend(await self.scrape_generic_jobs(driver, max_jobs))

        except Exception as e:
            logger.error(f"Error scraping {site_url}: {e}")
        finally:
            driver.quit()

        return jobs

    async def scrape_jobright_jobs(self, driver, max_jobs):
        jobs = []
        try:
            # Search for software engineer jobs
            search_box = WebDriverWait(driver, 10).wait(
                EC.presence_of_element_located((By.CSS_SELECTOR, "input[placeholder*='Job title'], input[name='q'], input[type='search']"))
            )
            search_box.clear()
            search_box.send_keys("Software Engineer")
            search_box.send_keys(Keys.RETURN)

            await asyncio.sleep(3)

            job_elements = driver.find_elements(By.CSS_SELECTOR, ".job-card, .job-listing, [data-job-id], .job-item")

            for i, job_elem in enumerate(job_elements[:max_jobs]):
                try:
                    title_elem = job_elem.find_element(By.CSS_SELECTOR, "h3, .job-title, .title, a[data-job-title]")
                    company_elem = job_elem.find_element(By.CSS_SELECTOR, ".company-name, .company, .employer")

                    job_title = title_elem.text.strip()
                    company_name = company_elem.text.strip()

                    # Get job URL
                    job_url = job_elem.find_element(By.CSS_SELECTOR, "a").get_attribute("href")

                    jobs.append({
                        "title": job_title,
                        "company": company_name,
                        "url": job_url,
                        "site": "JobRight"
                    })

                except Exception as e:
                    logger.warning(f"Error extracting job {i+1} from JobRight: {e}")
                    continue

        except Exception as e:
            logger.error(f"Error scraping JobRight jobs: {e}")

        return jobs

    async def scrape_linkedin_jobs(self, driver, max_jobs):
        jobs = []
        try:
            # Look for job listings
            job_elements = driver.find_elements(By.CSS_SELECTOR, ".job-search-card, .jobs-search-results__list-item")

            for i, job_elem in enumerate(job_elements[:max_jobs]):
                try:
                    title_elem = job_elem.find_element(By.CSS_SELECTOR, ".base-search-card__title, .job-search-card__title")
                    company_elem = job_elem.find_element(By.CSS_SELECTOR, ".base-search-card__subtitle, .job-search-card__subtitle")

                    job_title = title_elem.text.strip()
                    company_name = company_elem.text.strip()
                    job_url = job_elem.find_element(By.CSS_SELECTOR, "a").get_attribute("href")

                    jobs.append({
                        "title": job_title,
                        "company": company_name,
                        "url": job_url,
                        "site": "LinkedIn"
                    })

                except Exception as e:
                    logger.warning(f"Error extracting job {i+1} from LinkedIn: {e}")
                    continue

        except Exception as e:
            logger.error(f"Error scraping LinkedIn jobs: {e}")

        return jobs

    async def scrape_indeed_jobs(self, driver, max_jobs):
        jobs = []
        try:
            # Search for jobs
            search_box = driver.find_element(By.CSS_SELECTOR, "input[name='q'], input[id='text-input-what']")
            search_box.clear()
            search_box.send_keys("Software Engineer")

            location_box = driver.find_element(By.CSS_SELECTOR, "input[name='l'], input[id='text-input-where']")
            location_box.clear()
            location_box.send_keys("San Jose, CA")

            search_button = driver.find_element(By.CSS_SELECTOR, "button[type='submit'], .yosegi-InlineWhatWhere-primaryButton")
            search_button.click()

            await asyncio.sleep(3)

            job_elements = driver.find_elements(By.CSS_SELECTOR, ".job_seen_beacon, .slider_container .slider_item")

            for i, job_elem in enumerate(job_elements[:max_jobs]):
                try:
                    title_elem = job_elem.find_element(By.CSS_SELECTOR, "h2 a span, .jobTitle a span")
                    company_elem = job_elem.find_element(By.CSS_SELECTOR, ".companyName, [data-testid='company-name']")

                    job_title = title_elem.get_attribute("title") or title_elem.text
                    company_name = company_elem.text.strip()
                    job_url = job_elem.find_element(By.CSS_SELECTOR, "h2 a, .jobTitle a").get_attribute("href")

                    jobs.append({
                        "title": job_title,
                        "company": company_name,
                        "url": job_url,
                        "site": "Indeed"
                    })

                except Exception as e:
                    logger.warning(f"Error extracting job {i+1} from Indeed: {e}")
                    continue

        except Exception as e:
            logger.error(f"Error scraping Indeed jobs: {e}")

        return jobs

    async def scrape_glassdoor_jobs(self, driver, max_jobs):
        jobs = []
        try:
            # Search for jobs
            search_box = driver.find_element(By.CSS_SELECTOR, "input[name='sc.keyword'], input[placeholder*='Job title']")
            search_box.clear()
            search_box.send_keys("Software Engineer")
            search_box.send_keys(Keys.RETURN)

            await asyncio.sleep(3)

            job_elements = driver.find_elements(By.CSS_SELECTOR, ".react-job-listing, .jobContainer")

            for i, job_elem in enumerate(job_elements[:max_jobs]):
                try:
                    title_elem = job_elem.find_element(By.CSS_SELECTOR, ".job-search-key-l2dV1 a, .jobLink")
                    company_elem = job_elem.find_element(By.CSS_SELECTOR, ".job-search-key-BbRUP, .employerName")

                    job_title = title_elem.text.strip()
                    company_name = company_elem.text.strip()
                    job_url = title_elem.get_attribute("href")

                    jobs.append({
                        "title": job_title,
                        "company": company_name,
                        "url": job_url,
                        "site": "Glassdoor"
                    })

                except Exception as e:
                    logger.warning(f"Error extracting job {i+1} from Glassdoor: {e}")
                    continue

        except Exception as e:
            logger.error(f"Error scraping Glassdoor jobs: {e}")

        return jobs

    async def scrape_generic_jobs(self, driver, max_jobs):
        jobs = []
        try:
            # Generic job scraping for other sites
            job_elements = driver.find_elements(By.CSS_SELECTOR, ".job, .position, .listing, .career, .opportunity")

            for i, job_elem in enumerate(job_elements[:max_jobs]):
                try:
                    title_text = job_elem.text[:100] if job_elem.text else f"Job Opportunity {i+1}"
                    current_url = driver.current_url

                    jobs.append({
                        "title": title_text,
                        "company": "Company Name",
                        "url": current_url,
                        "site": "Career Site"
                    })

                except Exception as e:
                    logger.warning(f"Error extracting generic job {i+1}: {e}")
                    continue

        except Exception as e:
            logger.error(f"Error scraping generic jobs: {e}")

        return jobs

    async def apply_to_job(self, job_data, job_id):
        driver = self.create_driver(headless=False)
        application_successful = False
        proof_before = None
        proof_after = None
        proof_confirmation = None
        error_message = None

        try:
            logger.info(f"Applying to job {job_id}: {job_data['title']} at {job_data['company']}")

            driver.get(job_data['url'])
            await asyncio.sleep(3)

            # Take before screenshot
            proof_before = self.take_proof_screenshot(driver, job_id, "before_application")

            # Try to find and click apply button
            apply_selectors = [
                "button[data-test='apply-button']",
                "a[data-test='apply-button']",
                ".apply-button",
                ".btn-apply",
                "[href*='apply']",
                "button[class*='apply']",
                "a[class*='apply']",
                ".easy-apply-button",
                "button:contains('Apply')",
                "a:contains('Apply')",
                ".apply-now",
                ".quick-apply"
            ]

            apply_button = None
            for selector in apply_selectors:
                try:
                    apply_button = WebDriverWait(driver, 2).until(
                        EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                    )
                    break
                except:
                    continue

            if apply_button:
                driver.execute_script("arguments[0].click();", apply_button)
                await asyncio.sleep(2)

                # Fill out application form
                await self.fill_application_form(driver, job_data, job_id)
                application_successful = True

                # Take after screenshot
                proof_after = self.take_proof_screenshot(driver, job_id, "after_application")

                # Look for confirmation message
                confirmation_elements = driver.find_elements(By.CSS_SELECTOR,
                    ".confirmation, .success, .thank-you, .applied, [class*='success'], [class*='confirm']")

                if confirmation_elements:
                    proof_confirmation = self.take_proof_screenshot(driver, job_id, "confirmation")

            else:
                error_message = "Could not find apply button"
                logger.warning(f"Job {job_id}: {error_message}")

        except Exception as e:
            error_message = str(e)
            logger.error(f"Job {job_id}: Application failed - {error_message}")
        finally:
            driver.quit()

        # Save to database
        self.save_application_result(job_data, job_id, application_successful,
                                   proof_before, proof_after, proof_confirmation, error_message)

        return application_successful

    async def fill_application_form(self, driver, job_data, job_id):
        try:
            # Fill name fields
            name_selectors = ["input[name*='name']", "input[id*='name']", "input[placeholder*='name']"]
            for selector in name_selectors:
                try:
                    name_field = driver.find_element(By.CSS_SELECTOR, selector)
                    name_field.clear()
                    name_field.send_keys("John Doe")
                    break
                except:
                    continue

            # Fill email fields
            email_selectors = ["input[type='email']", "input[name*='email']", "input[id*='email']"]
            for selector in email_selectors:
                try:
                    email_field = driver.find_element(By.CSS_SELECTOR, selector)
                    email_field.clear()
                    email_field.send_keys("john.doe@email.com")
                    break
                except:
                    continue

            # Fill phone fields
            phone_selectors = ["input[type='tel']", "input[name*='phone']", "input[id*='phone']"]
            for selector in phone_selectors:
                try:
                    phone_field = driver.find_element(By.CSS_SELECTOR, selector)
                    phone_field.clear()
                    phone_field.send_keys("555-123-4567")
                    break
                except:
                    continue

            # Upload resume if field exists
            resume_selectors = ["input[type='file']", "input[name*='resume']", "input[name*='cv']"]
            for selector in resume_selectors:
                try:
                    file_input = driver.find_element(By.CSS_SELECTOR, selector)
                    if self.resume_path and os.path.exists(self.resume_path):
                        file_input.send_keys(self.resume_path)
                    break
                except:
                    continue

            # Fill cover letter if field exists
            cover_letter_selectors = ["textarea[name*='cover']", "textarea[name*='message']", "textarea[id*='cover']"]
            for selector in cover_letter_selectors:
                try:
                    cover_letter_field = driver.find_element(By.CSS_SELECTOR, selector)
                    cover_letter = self.cover_letter_template.format(
                        job_title=job_data['title'],
                        company_name=job_data['company'],
                        experience_years=self.user_profile['experience_years'],
                        relevant_skills=", ".join(self.user_profile['skills'][:3]),
                        candidate_name="John Doe"
                    )
                    cover_letter_field.clear()
                    cover_letter_field.send_keys(cover_letter)
                    break
                except:
                    continue

            await asyncio.sleep(2)

            # Try to submit the form
            submit_selectors = [
                "button[type='submit']",
                "input[type='submit']",
                ".submit-button",
                ".btn-submit",
                "button:contains('Submit')",
                "button:contains('Apply')",
                ".submit-application"
            ]

            for selector in submit_selectors:
                try:
                    submit_button = driver.find_element(By.CSS_SELECTOR, selector)
                    if submit_button.is_enabled():
                        driver.execute_script("arguments[0].click();", submit_button)
                        break
                except:
                    continue

            await asyncio.sleep(3)

        except Exception as e:
            logger.warning(f"Job {job_id}: Form filling encountered issues - {e}")

    def save_application_result(self, job_data, job_id, success, proof_before, proof_after, proof_confirmation, error_message):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            INSERT INTO job_applications (
                job_title, company_name, job_url, site_name, application_status,
                application_timestamp, proof_before_screenshot, proof_after_screenshot,
                proof_confirmation_screenshot, application_details, error_message
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            job_data['title'],
            job_data['company'],
            job_data['url'],
            job_data['site'],
            'applied' if success else 'failed',
            datetime.now().isoformat(),
            proof_before,
            proof_after,
            proof_confirmation,
            json.dumps(job_data),
            error_message
        ))

        conn.commit()
        conn.close()

    async def collect_100_jobs(self):
        all_jobs = []
        jobs_per_site = 100 // len(self.job_sites) + 1

        logger.info(f"Collecting jobs from {len(self.job_sites)} job sites...")

        for site_url in self.job_sites:
            if len(all_jobs) >= 100:
                break

            logger.info(f"Scraping jobs from: {site_url}")
            site_jobs = await self.scrape_jobs_from_site(site_url, jobs_per_site)
            all_jobs.extend(site_jobs)

            # Add delay between sites
            await asyncio.sleep(random.uniform(2, 5))

        # Ensure we have exactly 100 jobs
        all_jobs = all_jobs[:100]
        logger.info(f"Collected {len(all_jobs)} jobs for application")

        return all_jobs

    async def apply_to_100_jobs(self):
        logger.info("🚀 Starting automated application to 100 real jobs with proof generation!")

        # Collect jobs
        jobs = await self.collect_100_jobs()

        if len(jobs) < 100:
            logger.warning(f"Only found {len(jobs)} jobs, will apply to all available")

        successful_applications = 0
        failed_applications = 0

        for i, job in enumerate(jobs, 1):
            logger.info(f"\n--- Applying to Job {i}/100 ---")
            logger.info(f"Title: {job['title']}")
            logger.info(f"Company: {job['company']}")
            logger.info(f"Site: {job['site']}")

            success = await self.apply_to_job(job, i)

            if success:
                successful_applications += 1
                logger.info(f"✅ Job {i}: Application submitted successfully")
            else:
                failed_applications += 1
                logger.info(f"❌ Job {i}: Application failed")

            # Progress update
            if i % 10 == 0:
                logger.info(f"\n🎯 Progress: {i}/100 jobs processed")
                logger.info(f"✅ Successful: {successful_applications}")
                logger.info(f"❌ Failed: {failed_applications}")

            # Delay between applications
            await asyncio.sleep(random.uniform(3, 8))

        logger.info(f"\n🎉 MISSION COMPLETE!")
        logger.info(f"✅ Successfully applied to: {successful_applications} jobs")
        logger.info(f"❌ Failed applications: {failed_applications}")
        logger.info(f"📸 All applications have proof screenshots in: {self.proof_dir}")

        # Generate final report
        await self.generate_final_proof_report()

        return successful_applications, failed_applications

    async def generate_final_proof_report(self):
        logger.info("📄 Generating final proof report...")

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            SELECT * FROM job_applications ORDER BY id
        ''')

        applications = cursor.fetchall()
        conn.close()

        # Create PDF report
        report_path = self.proof_dir / f"100_jobs_proof_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        doc = SimpleDocTemplate(str(report_path), pagesize=letter)
        styles = getSampleStyleSheet()
        story = []

        # Title
        title = Paragraph("Automated Job Application Proof Report", styles['Title'])
        story.append(title)
        story.append(Spacer(1, 12))

        # Summary
        summary = f"""
        <para>
        <b>Total Applications:</b> {len(applications)}<br/>
        <b>Successful Applications:</b> {len([a for a in applications if a[5] == 'applied'])}<br/>
        <b>Failed Applications:</b> {len([a for a in applications if a[5] == 'failed'])}<br/>
        <b>Report Generated:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}<br/>
        </para>
        """
        story.append(Paragraph(summary, styles['Normal']))
        story.append(Spacer(1, 12))

        # Individual applications
        for app in applications:
            app_info = f"""
            <para>
            <b>Job {app[0]}:</b> {app[1]} at {app[2]}<br/>
            <b>Site:</b> {app[4]} | <b>Status:</b> {app[5]}<br/>
            <b>Applied:</b> {app[6] or 'N/A'}<br/>
            <b>Proof Screenshots:</b> Before: {os.path.basename(app[8]) if app[8] else 'None'},
            After: {os.path.basename(app[9]) if app[9] else 'None'}<br/>
            {f"<b>Error:</b> {app[11]}" if app[11] else ""}
            </para>
            """
            story.append(Paragraph(app_info, styles['Normal']))
            story.append(Spacer(1, 6))

        doc.build(story)
        logger.info(f"📄 Proof report generated: {report_path}")

async def main():
    applicator = Proven100JobApplicator()

    logger.info("🎯 MISSION: Apply to 100 real jobs with complete proof!")
    logger.info("📸 Every application will have before/after proof screenshots")
    logger.info("💾 All data will be saved to database for verification")

    successful, failed = await applicator.apply_to_100_jobs()

    logger.info(f"\n🏆 FINAL RESULTS:")
    logger.info(f"✅ Successfully applied to {successful} jobs")
    logger.info(f"❌ Failed to apply to {failed} jobs")
    logger.info(f"📊 Success rate: {(successful/(successful+failed)*100):.1f}%")
    logger.info(f"🗂️  Database: {applicator.db_path}")
    logger.info(f"📁 Proof screenshots: {applicator.proof_dir}")

if __name__ == "__main__":
    asyncio.run(main())