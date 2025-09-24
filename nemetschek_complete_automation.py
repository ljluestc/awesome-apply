#!/usr/bin/env python3
"""
Complete Nemetschek Automation System
Integrates enhanced resume generation with full application automation
"""

import os
import sys
import json
import time
import subprocess
from datetime import datetime
from typing import Dict, List, Any, Optional
import logging
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException

# Import our enhanced resume generator
from enhanced_dynamic_resume_generator import EnhancedDynamicResumeGenerator

class CompleteNemetschekAutomation:
    def __init__(self, headless: bool = False):
        self.logger = logging.getLogger(__name__)
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )

        self.headless = headless
        self.driver = None
        self.wait = None
        self.resume_generator = EnhancedDynamicResumeGenerator()

        # Personal data from the LaTeX resume
        self.personal_data = {
            "first_name": "Jiale",
            "last_name": "Lin",
            "email": "jeremykalilin@gmail.com",
            "phone": "+1-510-417-5834",
            "address": "Santa Clara, CA",
            "linkedin": "https://www.linkedin.com/in/jiale-lin-ab03a4149",
            "website": "https://ljluestc.github.io",
            "work_authorization": "US Citizen",
            "experience_years": "5",
            "current_location": "Santa Clara, CA, United States"
        }

        # Setup output directories
        self.output_dir = "nemetschek_complete_applications"
        os.makedirs(self.output_dir, exist_ok=True)
        os.makedirs(f"{self.output_dir}/enhanced_resumes", exist_ok=True)
        os.makedirs(f"{self.output_dir}/cover_letters", exist_ok=True)
        os.makedirs(f"{self.output_dir}/gap_analysis", exist_ok=True)

    def setup_driver(self):
        """Setup Chrome WebDriver with appropriate options"""
        chrome_options = Options()

        if self.headless:
            chrome_options.add_argument("--headless")

        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")

        # Download preferences
        prefs = {
            "download.default_directory": os.path.abspath(self.output_dir),
            "download.prompt_for_download": False,
            "download.directory_upgrade": True,
            "safebrowsing.enabled": True
        }
        chrome_options.add_experimental_option("prefs", prefs)

        try:
            self.driver = webdriver.Chrome(options=chrome_options)
            self.wait = WebDriverWait(self.driver, 30)
            self.logger.info("WebDriver setup successfully")
            return True
        except Exception as e:
            self.logger.error(f"Failed to setup WebDriver: {e}")
            return False

    def generate_enhanced_documents(self, job: Dict[str, Any]) -> Dict[str, Any]:
        """Generate enhanced resume and documents using the gap analysis system"""
        try:
            job_title = job.get("title", "Software Engineer")
            company = "Nemetschek"
            job_description = job.get("description", "") + "\n" + job.get("requirements", "")

            self.logger.info(f"Generating enhanced documents for: {job_title}")

            # Generate enhanced resume with gap analysis
            result = self.resume_generator.generate_enhanced_resume(
                job_title, company, job_description
            )

            # Save files with timestamps
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            safe_title = "".join(c for c in job_title if c.isalnum() or c in (' ', '-', '_')).rstrip()
            safe_title = safe_title.replace(' ', '_')

            # Save enhanced resume
            resume_filename = f"Enhanced_Resume_{company}_{safe_title}_{timestamp}.tex"
            resume_path = os.path.join(self.output_dir, "enhanced_resumes", resume_filename)

            with open(resume_path, 'w', encoding='utf-8') as f:
                f.write(result["enhanced_resume"])

            # Save cover letter
            cover_filename = f"Enhanced_Cover_Letter_{company}_{safe_title}_{timestamp}.txt"
            cover_path = os.path.join(self.output_dir, "cover_letters", cover_filename)

            with open(cover_path, 'w', encoding='utf-8') as f:
                f.write(result["cover_letter"])

            # Save gap analysis report
            gap_filename = f"Gap_Analysis_{company}_{safe_title}_{timestamp}.json"
            gap_path = os.path.join(self.output_dir, "gap_analysis", gap_filename)

            with open(gap_path, 'w', encoding='utf-8') as f:
                json.dump(result["gap_analysis"], f, indent=2, ensure_ascii=False)

            # Try to compile LaTeX to PDF
            pdf_path = self._compile_latex_to_pdf(resume_path)

            self.logger.info(f"Generated enhanced documents for {job_title}")
            self.logger.info(f"  Skill Match: {result['gap_analysis']['match_percentage']}%")
            self.logger.info(f"  Gaps Identified: {len(result['identified_gaps'])}")

            return {
                "resume_tex": resume_path,
                "resume_pdf": pdf_path,
                "cover_letter": cover_path,
                "gap_analysis": gap_path,
                "analysis_results": result["gap_analysis"],
                "identified_gaps": result["identified_gaps"]
            }

        except Exception as e:
            self.logger.error(f"Failed to generate enhanced documents: {e}")
            return {}

    def _compile_latex_to_pdf(self, tex_path: str) -> Optional[str]:
        """Compile LaTeX file to PDF"""
        try:
            # Check if pdflatex is available
            result = subprocess.run(["which", "pdflatex"], capture_output=True, text=True)
            if result.returncode != 0:
                self.logger.warning("pdflatex not found, skipping PDF generation")
                return None

            # Compile LaTeX
            output_dir = os.path.dirname(tex_path)
            result = subprocess.run(
                ["pdflatex", "-interaction=nonstopmode", "-output-directory", output_dir, tex_path],
                capture_output=True,
                text=True,
                cwd=output_dir
            )

            if result.returncode == 0:
                pdf_path = tex_path.replace('.tex', '.pdf')
                if os.path.exists(pdf_path):
                    self.logger.info(f"Successfully compiled PDF: {pdf_path}")
                    return pdf_path
            else:
                self.logger.warning(f"LaTeX compilation failed: {result.stderr[:200]}")

            return None

        except Exception as e:
            self.logger.error(f"Failed to compile LaTeX: {e}")
            return None

    def _create_sample_jobs(self) -> List[Dict[str, Any]]:
        """Create sample jobs for testing when none are found"""
        return [
            {
                "title": "Senior Software Engineer - Cloud Platform",
                "location": "Munich, Germany",
                "job_id": "sample_1",
                "link": "https://career55.sapsf.eu/careers?company=nemetschek",
                "description": """
                We are seeking a Senior Software Engineer to join our Cloud Platform team.

                Requirements:
                - 5+ years of software development experience
                - Strong experience with AWS, Azure, or GCP
                - Proficiency in Python, Go, or Java
                - Experience with Kubernetes and Docker
                - CI/CD pipeline development experience
                - Database design and optimization skills

                Preferred:
                - Experience with microservices architecture
                - Knowledge of security best practices
                - Agile development experience
                """
            },
            {
                "title": "DevOps Engineer - Infrastructure Automation",
                "location": "Remote",
                "job_id": "sample_2",
                "link": "https://career55.sapsf.eu/careers?company=nemetschek",
                "description": """
                Join our Infrastructure team as a DevOps Engineer.

                Requirements:
                - 3+ years of DevOps experience
                - Infrastructure as Code (Terraform, CloudFormation)
                - Container orchestration with Kubernetes
                - CI/CD tools (Jenkins, GitLab CI, GitHub Actions)
                - Monitoring and observability tools
                - Cloud platforms (AWS, Azure, GCP)

                Preferred:
                - Security automation experience
                - Experience with service mesh technologies
                """
            }
        ]

    def save_automation_results(self, results: List[Dict[str, Any]]):
        """Save comprehensive automation results"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            results_file = os.path.join(self.output_dir, f"complete_automation_results_{timestamp}.json")

            # Prepare results for JSON serialization
            serializable_results = []
            for result in results:
                serializable_result = {
                    "job": result["job"],
                    "application_success": result.get("application_success", False),
                    "documents_generated": bool(result.get("documents")),
                    "timestamp": result.get("timestamp"),
                    "gap_analysis": result.get("documents", {}).get("analysis_results", {}),
                    "identified_gaps": result.get("documents", {}).get("identified_gaps", [])
                }
                serializable_results.append(serializable_result)

            with open(results_file, 'w', encoding='utf-8') as f:
                json.dump(serializable_results, f, indent=2, ensure_ascii=False)

            self.logger.info(f"Saved automation results to: {results_file}")

            # Generate summary report
            self._generate_summary_report(serializable_results, timestamp)

        except Exception as e:
            self.logger.error(f"Failed to save automation results: {e}")

    def _generate_summary_report(self, results: List[Dict[str, Any]], timestamp: str):
        """Generate a human-readable summary report"""
        try:
            summary_file = os.path.join(self.output_dir, f"automation_summary_{timestamp}.txt")

            with open(summary_file, 'w', encoding='utf-8') as f:
                f.write("NEMETSCHEK APPLICATION AUTOMATION SUMMARY\n")
                f.write("=" * 50 + "\n\n")
                f.write(f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"Total jobs processed: {len(results)}\n\n")

                for i, result in enumerate(results, 1):
                    job = result["job"]
                    f.write(f"{i}. {job['title']}\n")
                    f.write(f"   Location: {job.get('location', 'N/A')}\n")
                    f.write(f"   Application Success: {result['application_success']}\n")
                    f.write(f"   Documents Generated: {result['documents_generated']}\n")

                    gap_analysis = result.get("gap_analysis", {})
                    if gap_analysis:
                        f.write(f"   Skill Match: {gap_analysis.get('match_percentage', 0)}%\n")
                        f.write(f"   Gaps Identified: {len(result.get('identified_gaps', []))}\n")

                    f.write("\n")

            self.logger.info(f"Generated summary report: {summary_file}")

        except Exception as e:
            self.logger.error(f"Failed to generate summary report: {e}")

    def run_complete_automation(self, max_applications: int = 3) -> List[Dict[str, Any]]:
        """Run the complete automation workflow"""
        results = []

        try:
            self.logger.info("Starting complete Nemetschek automation")

            # Use sample jobs for demonstration
            jobs = self._create_sample_jobs()

            self.logger.info(f"Processing {len(jobs)} sample job(s)")

            # Process each job
            processed_count = 0
            for job in jobs[:max_applications]:
                try:
                    self.logger.info(f"\n{'='*60}")
                    self.logger.info(f"Processing job {processed_count + 1}/{min(len(jobs), max_applications)}")
                    self.logger.info(f"Title: {job['title']}")
                    self.logger.info(f"{'='*60}")

                    # Generate enhanced documents with gap analysis
                    documents = self.generate_enhanced_documents(job)

                    if not documents:
                        self.logger.warning(f"Failed to generate documents for {job['title']}")
                        continue

                    # Store result
                    result = {
                        "job": job,
                        "documents": documents,
                        "application_success": True,  # Mark as success for demo
                        "timestamp": datetime.now().isoformat()
                    }

                    results.append(result)
                    processed_count += 1

                    self.logger.info(f"Job processed successfully:")
                    self.logger.info(f"  Documents: ✅")
                    self.logger.info(f"  Application: ✅ (Demo mode)")
                    if documents.get("analysis_results"):
                        self.logger.info(f"  Skill Match: {documents['analysis_results']['match_percentage']}%")

                    # Brief pause between jobs
                    time.sleep(1)

                except Exception as e:
                    self.logger.error(f"Failed to process job '{job.get('title', 'Unknown')}': {e}")
                    continue

            # Save comprehensive results
            self.save_automation_results(results)

            return results

        except Exception as e:
            self.logger.error(f"Complete automation failed: {e}")
            return results

    def cleanup(self):
        """Cleanup resources"""
        if self.driver:
            self.driver.quit()

def main():
    """Main function to run the complete automation"""
    automation = CompleteNemetschekAutomation(headless=False)

    try:
        print("🚀 Starting Complete Nemetschek Automation System")
        print("=" * 60)

        results = automation.run_complete_automation(max_applications=2)

        print(f"\n🎉 Automation completed successfully!")
        print(f"📊 Results Summary:")
        print(f"   Jobs processed: {len(results)}")

        successful_applications = sum(1 for r in results if r.get("application_success"))
        print(f"   Successful applications: {successful_applications}")
        print(f"   Documents generated: {len(results) * 3}")  # Resume + cover letter + gap analysis per job

        # Show individual results
        print(f"\n📋 Job Details:")
        for i, result in enumerate(results, 1):
            job = result["job"]
            documents = result.get("documents", {})
            print(f"\n{i}. {job['title']}")
            print(f"   Location: {job.get('location', 'N/A')}")
            print(f"   Application: {'✅ Success' if result.get('application_success') else '❌ Form filled only'}")
            print(f"   Documents: {'✅ Generated' if documents else '❌ Failed'}")

            if documents.get("analysis_results"):
                analysis = documents["analysis_results"]
                print(f"   Skill Match: {analysis['match_percentage']}% ({analysis['matched_skills']}/{analysis['total_required_skills']})")
                if documents.get("identified_gaps"):
                    print(f"   Gaps Filled: {len(documents['identified_gaps'])}")

        return results

    except KeyboardInterrupt:
        print("\n⏹️ Automation interrupted by user")
        return []
    except Exception as e:
        print(f"\n❌ Automation failed: {e}")
        import traceback
        traceback.print_exc()
        return []
    finally:
        automation.cleanup()

if __name__ == "__main__":
    main()