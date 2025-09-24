#!/usr/bin/env python3
"""
Test SAP SuccessFactors automation system
"""

import sys
import os
import json
from datetime import datetime
from sap_nemetschek_complete_automation import SAPNemetschekAutomation

def test_resume_generation():
    """Test the dynamic resume generation functionality"""
    print("🧪 Testing Dynamic Resume Generation System")
    print("=" * 50)

    try:
        # Initialize automation system
        automation = SAPNemetschekAutomation()

        # Sample job descriptions for Nemetschek
        test_jobs = [
            {
                "title": "Senior DevOps Engineer - Cloud Infrastructure",
                "company": "Nemetschek",
                "description": """
                We are seeking a Senior DevOps Engineer to join our innovative cloud infrastructure team.

                Required Skills:
                - 5+ years of experience in DevOps and cloud infrastructure
                - Expert knowledge of AWS, Azure, or GCP cloud platforms
                - Strong experience with Kubernetes and Docker containerization
                - Proficiency in Infrastructure as Code using Terraform
                - Experience with CI/CD pipelines (Jenkins, GitHub Actions, GitLab CI)
                - Programming skills in Python, Go, or similar languages
                - Experience with monitoring tools like Prometheus and Grafana
                - Understanding of security best practices and Zero Trust architecture
                """
            },
            {
                "title": "Senior Software Engineer - CAD Platform",
                "company": "Nemetschek",
                "description": """
                We are looking for a Senior Software Engineer to join our CAD Platform team.

                Requirements:
                - 5+ years of C++ development experience
                - Experience with 3D graphics and rendering
                - Knowledge of CAD software architecture
                - Proficiency in Python and scripting
                - Experience with cloud platforms (AWS, Azure)
                - Familiarity with CI/CD and DevOps practices
                """
            },
            {
                "title": "Full Stack Developer - Web Platform",
                "company": "Nemetschek",
                "description": """
                We're seeking a Full Stack Developer for our web platform.

                Requirements:
                - Strong experience with React and modern JavaScript
                - Backend development with Node.js or Python
                - Database experience with PostgreSQL or MongoDB
                - REST API design and development
                - Experience with microservices architecture
                """
            }
        ]

        results = []

        for job in test_jobs:
            print(f"\n📋 Processing: {job['title']}")

            try:
                # Use the resume generator from automation system
                from intelligent_resume_generator import DynamicResumeGenerator

                generator = DynamicResumeGenerator()

                # Generate tailored resume
                latex_resume = generator.generate_latex_resume(
                    job["title"],
                    job["description"],
                    job["company"]
                )

                # Save resume
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                resume_filename = f"Test_{job['company']}_{job['title'].replace(' ', '_').replace('-', '_')}_{timestamp}.tex"

                with open(resume_filename, 'w', encoding='utf-8') as f:
                    f.write(latex_resume)

                print(f"✅ Resume saved: {resume_filename}")

                # Verify file was created and has content
                if os.path.exists(resume_filename):
                    file_size = os.path.getsize(resume_filename)
                    print(f"📄 File size: {file_size} bytes")

                    # Basic content validation
                    with open(resume_filename, 'r') as f:
                        content = f.read()
                        if "Jiale Lin" in content and "\\documentclass" in content:
                            print("✅ Content validation passed")
                            success = True
                        else:
                            print("❌ Content validation failed")
                            success = False
                else:
                    print("❌ File was not created")
                    success = False

                results.append({
                    "job": job["title"],
                    "file": resume_filename,
                    "size": file_size if 'file_size' in locals() else 0,
                    "success": success
                })

            except Exception as e:
                print(f"❌ Error processing {job['title']}: {e}")
                results.append({
                    "job": job["title"],
                    "success": False,
                    "error": str(e)
                })

        # Generate summary report
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report = {
            "timestamp": datetime.now().isoformat(),
            "total_jobs": len(test_jobs),
            "successful": len([r for r in results if r.get("success", False)]),
            "failed": len([r for r in results if not r.get("success", False)]),
            "results": results
        }

        report_filename = f"Test_Resume_Generation_Report_{timestamp}.json"
        with open(report_filename, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)

        print(f"\n📊 SUMMARY REPORT")
        print("=" * 30)
        print(f"🎯 Total Jobs: {report['total_jobs']}")
        print(f"✅ Successful: {report['successful']}")
        print(f"❌ Failed: {report['failed']}")
        print(f"📁 Report saved: {report_filename}")

        return report['successful'] == report['total_jobs']

    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Main test function"""
    print("🚀 SAP SuccessFactors Nemetschek Automation Test")
    print("=" * 60)

    success = test_resume_generation()

    if success:
        print("\n✅ All tests passed!")
    else:
        print("\n❌ Tests failed!")

    return success

if __name__ == "__main__":
    main()