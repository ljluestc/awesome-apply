#!/usr/bin/env python3
"""
Test Suite for Complete Nemetschek Automation System
Tests both the resume generator and automation components
"""

import os
import tempfile
import unittest
from pathlib import Path
import json
from datetime import datetime

# Import our modules
from intelligent_resume_generator import DynamicResumeGenerator, JobRequirementAnalyzer, ResumeData

class TestIntelligentResumeGenerator(unittest.TestCase):
    def setUp(self):
        self.generator = DynamicResumeGenerator()
        self.analyzer = JobRequirementAnalyzer()

    def test_job_requirement_analysis(self):
        """Test job requirement analysis"""
        job_title = "Senior DevOps Engineer"
        job_description = """
        We are looking for a Senior DevOps Engineer with experience in:
        - Kubernetes and Docker containerization
        - AWS, Azure, and GCP cloud platforms
        - Python and Go programming
        - Terraform infrastructure as code
        - CI/CD with Jenkins and GitHub Actions
        - Monitoring with Prometheus and Grafana
        """

        scores = self.analyzer.analyze_job_description(job_title, job_description)

        # Check that relevant keywords are detected
        self.assertIn("kubernetes", scores)
        self.assertIn("python", scores)
        self.assertIn("aws", scores)
        self.assertIn("terraform", scores)
        self.assertIn("jenkins", scores)
        self.assertIn("senior", scores)

        # Check scoring weights
        self.assertGreater(scores.get("senior", 0), 1.0)  # Senior should have weight > 1
        self.assertEqual(scores.get("python", 0), 1.0)    # Python should have base weight

    def test_technology_matching(self):
        """Test relevant technology extraction"""
        job_scores = {
            "python": 2.0,
            "kubernetes": 1.5,
            "terraform": 1.0,
            "go": 1.0,
            "prometheus": 1.0
        }

        relevant_techs = self.analyzer.get_relevant_technologies(job_scores, self.generator.resume_data)

        # Should include technologies mentioned in both job and resume
        expected_techs = ["python", "kubernetes", "terraform", "go", "prometheus"]
        for tech in expected_techs:
            self.assertIn(tech, relevant_techs)

    def test_latex_resume_generation(self):
        """Test LaTeX resume generation"""
        job_title = "Senior Software Engineer"
        job_description = "Python, Go, Kubernetes, AWS, microservices development"
        company_name = "TestCorp"

        latex_content = self.generator.generate_latex_resume(job_title, job_description, company_name)

        # Check LaTeX structure
        self.assertIn("\\documentclass", latex_content)
        self.assertIn("\\begin{document}", latex_content)
        self.assertIn("\\end{document}", latex_content)

        # Check content sections
        self.assertIn("\\section{Education}", latex_content)
        self.assertIn("\\section{Experience}", latex_content)
        self.assertIn("\\section{Projects}", latex_content)

        # Check personal information
        self.assertIn("Jiale Lin", latex_content)
        self.assertIn("jeremykalilin@gmail.com", latex_content)

    def test_experience_prioritization(self):
        """Test experience prioritization based on job requirements"""
        job_scores = {
            "kubernetes": 2.0,
            "python": 2.0,
            "terraform": 1.5,
            "devops": 1.0
        }

        prioritized_exp = self.generator._prioritize_experiences(job_scores)

        # Aviatrix experience should be first (most relevant for DevOps roles)
        self.assertEqual(prioritized_exp[0].company, "Aviatrix")

        # Check that experiences are properly ordered
        self.assertEqual(len(prioritized_exp), 3)
        for exp in prioritized_exp:
            self.assertIsInstance(exp.company, str)
            self.assertIsInstance(exp.achievements, list)

    def test_project_selection(self):
        """Test project selection based on relevance"""
        job_scores = {
            "machine learning": 2.0,
            "python": 1.5,
            "kubernetes": 1.0
        }
        relevant_techs = ["python", "tensorflow", "kubernetes"]

        selected_projects = self.generator._select_relevant_projects(job_scores, relevant_techs)

        # Should return top relevant projects
        self.assertLessEqual(len(selected_projects), 4)

        # AI-Powered Network Traffic Classifier should be highly ranked for ML jobs
        project_names = [p.name for p in selected_projects]
        self.assertIn("AI-Powered Network Traffic Classifier", project_names)

    def test_achievement_enhancement(self):
        """Test achievement text enhancement"""
        achievements = [
            "Developed REST/gRPC services using Go and Python",
            "Automated infrastructure with Terraform and Kubernetes"
        ]

        job_scores = {
            "go": 1.0,
            "terraform": 1.0,
            "kubernetes": 1.0
        }

        enhanced = self.generator._enhance_achievements(achievements, job_scores)

        # Should have same number of achievements
        self.assertEqual(len(enhanced), len(achievements))

        # Should contain enhanced text (this is basic - could be more sophisticated)
        for achievement in enhanced:
            self.assertIsInstance(achievement, str)

    def test_file_saving(self):
        """Test resume file saving"""
        latex_content = "\\documentclass{article}\\begin{document}Test\\end{document}"

        with tempfile.TemporaryDirectory() as temp_dir:
            os.chdir(temp_dir)

            filepath = self.generator.save_resume(latex_content, "TestCompany", "Test Engineer")

            # Check file was created
            self.assertTrue(Path(filepath).exists())

            # Check filename format
            self.assertIn("Jiale_Lin_Resume", filepath)
            self.assertIn("TestCompany", filepath)
            self.assertIn("Test_Engineer", filepath)
            self.assertTrue(filepath.endswith(".tex"))

            # Check content
            with open(filepath, 'r') as f:
                content = f.read()
                self.assertEqual(content, latex_content)

class TestResumeDataStructure(unittest.TestCase):
    def setUp(self):
        self.resume_data = ResumeData()

    def test_contact_information(self):
        """Test contact information structure"""
        contact = self.resume_data.contact

        self.assertEqual(contact.name, "Jiale Lin")
        self.assertEqual(contact.email, "jeremykalilin@gmail.com")
        self.assertIn("510", contact.phone)
        self.assertIn("linkedin", contact.linkedin)
        self.assertIn("ljluestc", contact.website)

    def test_education_data(self):
        """Test education data structure"""
        education = self.resume_data.education

        self.assertEqual(len(education), 2)

        # Check graduate education
        grad_edu = education[0]
        self.assertEqual(grad_edu.institution, "University of Colorado Boulder")
        self.assertEqual(grad_edu.degree, "Master of Science")
        self.assertEqual(grad_edu.field, "Computer Science")
        self.assertEqual(grad_edu.graduation_date, "May 2025")

    def test_experience_data(self):
        """Test work experience data"""
        experiences = self.resume_data.experiences

        self.assertGreater(len(experiences), 0)

        # Check Aviatrix experience
        aviatrix_exp = experiences[0]
        self.assertEqual(aviatrix_exp.company, "Aviatrix")
        self.assertEqual(aviatrix_exp.position, "Senior Software Engineer")
        self.assertIn("Go", aviatrix_exp.technologies)
        self.assertIn("Python", aviatrix_exp.technologies)
        self.assertIn("Kubernetes", aviatrix_exp.technologies)

    def test_projects_data(self):
        """Test projects data structure"""
        projects = self.resume_data.projects

        self.assertGreater(len(projects), 0)

        # Check AI project exists
        ai_project = next((p for p in projects if "AI-Powered" in p.name), None)
        self.assertIsNotNone(ai_project)
        self.assertIn("Python", ai_project.technologies)
        self.assertIn("eBPF", ai_project.technologies)

    def test_skills_data(self):
        """Test skills data structure"""
        skills = self.resume_data.skills

        self.assertIn("Programming Languages", skills)
        self.assertIn("Cloud & Infrastructure", skills)

        # Check programming languages
        prog_langs = skills["Programming Languages"]
        self.assertIn("Python", prog_langs)
        self.assertIn("Go", prog_langs)
        self.assertIn("Java", prog_langs)

class TestJobRequirementAnalyzer(unittest.TestCase):
    def setUp(self):
        self.analyzer = JobRequirementAnalyzer()

    def test_keyword_weights(self):
        """Test keyword weight configuration"""
        weights = self.analyzer.keyword_weights

        # Check that important keywords have appropriate weights
        self.assertEqual(weights.get("python", 0), 1.0)
        self.assertEqual(weights.get("kubernetes", 0), 1.0)
        self.assertGreater(weights.get("senior", 0), 1.0)

    def test_keyword_detection(self):
        """Test keyword detection in job descriptions"""
        job_text = "We need a Senior Python developer with Kubernetes experience"

        scores = {}
        for keyword, weight in self.analyzer.keyword_weights.items():
            import re
            count = len(re.findall(r'\b' + re.escape(keyword) + r'\b', job_text.lower()))
            if count > 0:
                scores[keyword] = count * weight

        self.assertIn("senior", scores)
        self.assertIn("python", scores)
        self.assertIn("kubernetes", scores)

def run_system_integration_test():
    """Run a complete system integration test"""
    print("\n" + "="*60)
    print("RUNNING SYSTEM INTEGRATION TEST")
    print("="*60)

    generator = DynamicResumeGenerator()

    # Test job scenarios
    test_jobs = [
        {
            "title": "Senior DevOps Engineer",
            "description": "Kubernetes, Docker, AWS, Python, Terraform, CI/CD, monitoring",
            "company": "TechCorp"
        },
        {
            "title": "Full Stack Developer",
            "description": "React, Node.js, Python, PostgreSQL, REST APIs, microservices",
            "company": "WebCompany"
        },
        {
            "title": "ML Engineer",
            "description": "Python, TensorFlow, PyTorch, Kubernetes, MLOps, data pipelines",
            "company": "AIStartup"
        }
    ]

    results = []

    for job in test_jobs:
        print(f"\nTesting job: {job['title']} at {job['company']}")

        try:
            # Generate tailored resume
            latex_content = generator.generate_latex_resume(
                job["title"],
                job["description"],
                job["company"]
            )

            # Save to file
            filepath = generator.save_resume(
                latex_content,
                job["company"],
                job["title"]
            )

            # Verify file exists and has content
            if Path(filepath).exists():
                file_size = Path(filepath).stat().st_size
                print(f"✓ Generated resume: {filepath} ({file_size} bytes)")

                results.append({
                    "job": job,
                    "file": filepath,
                    "size": file_size,
                    "success": True
                })
            else:
                print(f"✗ Failed to create file: {filepath}")
                results.append({
                    "job": job,
                    "success": False,
                    "error": "File not created"
                })

        except Exception as e:
            print(f"✗ Error generating resume for {job['title']}: {e}")
            results.append({
                "job": job,
                "success": False,
                "error": str(e)
            })

    # Save integration test results
    test_results = {
        "timestamp": datetime.now().isoformat(),
        "total_tests": len(test_jobs),
        "successful": len([r for r in results if r["success"]]),
        "failed": len([r for r in results if not r["success"]]),
        "results": results
    }

    results_file = f"system_integration_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(results_file, 'w') as f:
        json.dump(test_results, f, indent=2)

    print(f"\n" + "="*60)
    print("INTEGRATION TEST SUMMARY")
    print("="*60)
    print(f"Total tests: {test_results['total_tests']}")
    print(f"Successful: {test_results['successful']}")
    print(f"Failed: {test_results['failed']}")
    print(f"Results saved to: {results_file}")

    return test_results

def main():
    """Run all tests"""
    print("Testing Intelligent Resume Generator System")
    print("="*50)

    # Run unit tests
    unittest.main(argv=[''], exit=False, verbosity=2)

    # Run integration test
    integration_results = run_system_integration_test()

    return integration_results

if __name__ == "__main__":
    main()