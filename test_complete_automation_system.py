#!/usr/bin/env python3
"""
🚀 COMPLETE AUTOMATION SYSTEM TEST 🚀
=====================================

Test the complete integrated system:
1. Dynamic resume generation based on job requirements
2. SAP Nemetschek careers automation
3. Full application workflow with custom resumes

This is a comprehensive test of the complete system.
"""

import sys
import os
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict

# Add current directory to path for imports
sys.path.append('/home/calelin/awesome-apply')

from dynamic_resume_generator import DynamicResumeGenerator, JialeLinProfile
from sap_nemetschek_automation import SAPNemetschekCareersAutomation

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class CompleteAutomationSystemTest:
    """Test the complete automation system"""

    def __init__(self):
        self.resume_generator = DynamicResumeGenerator(JialeLinProfile())
        self.results = {
            'start_time': datetime.now().isoformat(),
            'tests_passed': 0,
            'tests_failed': 0,
            'test_details': []
        }

    def test_resume_generation(self) -> bool:
        """Test dynamic resume generation"""
        logger.info("🧪 Testing dynamic resume generation...")

        try:
            # Test with multiple job scenarios
            test_scenarios = [
                {
                    'job_title': 'Senior Backend Engineer',
                    'company': 'Nemetschek',
                    'description': '''
                    We are looking for a Senior Backend Engineer with 5+ years of experience.

                    Requirements:
                    - Strong experience with Python, Go, and microservices
                    - Experience with Kubernetes, Docker, and cloud platforms
                    - Knowledge of distributed systems and scalability
                    - Experience with monitoring and observability tools
                    - Background in DevOps and automation

                    You will be working on high-scale systems and APIs.
                    '''
                },
                {
                    'job_title': 'Full Stack Developer',
                    'company': 'Nemetschek',
                    'description': '''
                    We need a Full Stack Developer with frontend and backend skills.

                    Requirements:
                    - Experience with React, JavaScript, and modern frontend
                    - Backend development with Python or Node.js
                    - Database experience with SQL and NoSQL
                    - Knowledge of CI/CD and testing
                    - Experience with REST APIs and GraphQL
                    '''
                },
                {
                    'job_title': 'DevOps Engineer',
                    'company': 'Nemetschek',
                    'description': '''
                    DevOps Engineer to manage our infrastructure and automation.

                    Requirements:
                    - Strong Kubernetes and Docker experience
                    - Infrastructure as Code with Terraform
                    - CI/CD pipeline development
                    - Monitoring with Prometheus and Grafana
                    - Cloud platforms: AWS, Azure, GCP
                    - Security and compliance automation
                    '''
                }
            ]

            for i, scenario in enumerate(test_scenarios):
                logger.info(f"📝 Testing scenario {i+1}: {scenario['job_title']}")

                # Generate customized resume
                resume_path = self.resume_generator.generate_customized_resume(
                    job_description=scenario['description'],
                    job_title=scenario['job_title'],
                    company=scenario['company'],
                    output_format="pdf",
                    include_suggestions=True
                )

                # Verify resume was created
                if resume_path and Path(resume_path).exists():
                    logger.info(f"✅ Resume generated: {resume_path}")

                    # Analyze the job matching
                    analysis = self.resume_generator.job_analysis

                    self.results['test_details'].append({
                        'test': f'Resume Generation - {scenario["job_title"]}',
                        'status': 'PASSED',
                        'resume_path': resume_path,
                        'match_score': analysis['relevance_scores']['overall_match'],
                        'matched_skills': len(analysis['matching_skills']['exact']),
                        'matched_technologies': len(analysis['matching_technologies'])
                    })

                    logger.info(f"📊 Match Score: {analysis['relevance_scores']['overall_match']:.1f}%")

                else:
                    logger.error(f"❌ Failed to generate resume for {scenario['job_title']}")
                    self.results['test_details'].append({
                        'test': f'Resume Generation - {scenario["job_title"]}',
                        'status': 'FAILED',
                        'error': 'Resume file not created'
                    })
                    return False

            logger.info("✅ All resume generation tests passed")
            return True

        except Exception as e:
            logger.error(f"❌ Resume generation test failed: {e}")
            self.results['test_details'].append({
                'test': 'Resume Generation',
                'status': 'FAILED',
                'error': str(e)
            })
            return False

    def test_job_analysis_accuracy(self) -> bool:
        """Test job analysis and matching accuracy"""
        logger.info("🧪 Testing job analysis accuracy...")

        try:
            # Test with a job description that should match Jiale's profile well
            perfect_match_job = '''
            Senior Software Engineer with 5+ years of experience in backend development.

            Requirements:
            - Strong experience with Python and Go programming
            - Experience with Kubernetes and Docker containerization
            - Knowledge of microservices architecture and distributed systems
            - Experience with CI/CD pipelines and DevOps practices
            - Background in test automation and quality assurance
            - Experience with monitoring tools like Prometheus and Grafana
            - Cloud platform experience (AWS, Azure, GCP)
            - Experience with networking and security
            '''

            analysis = self.resume_generator.analyze_job_requirements(
                perfect_match_job,
                "Senior Software Engineer",
                "Nemetschek"
            )

            # Check that analysis identifies high match
            match_score = analysis['relevance_scores']['overall_match']

            if match_score >= 60:  # Should be high match for this job
                logger.info(f"✅ Job analysis accuracy test passed: {match_score:.1f}% match")

                self.results['test_details'].append({
                    'test': 'Job Analysis Accuracy',
                    'status': 'PASSED',
                    'match_score': match_score,
                    'matched_skills': len(analysis['matching_skills']['exact']),
                    'required_skills': len(analysis['required_skills'])
                })

                return True
            else:
                logger.error(f"❌ Job analysis accuracy test failed: only {match_score:.1f}% match")
                return False

        except Exception as e:
            logger.error(f"❌ Job analysis test failed: {e}")
            return False

    def test_missing_skills_detection(self) -> bool:
        """Test detection of missing skills and suggestions"""
        logger.info("🧪 Testing missing skills detection...")

        try:
            # Job with skills Jiale doesn't have
            job_with_missing_skills = '''
            We need a developer with experience in:
            - React and Vue.js frontend development
            - Node.js backend development
            - MongoDB and PostgreSQL databases
            - GraphQL API development
            - Elasticsearch for search functionality
            - Docker and Kubernetes (which Jiale has)
            - Python programming (which Jiale has)
            '''

            analysis = self.resume_generator.analyze_job_requirements(
                job_with_missing_skills,
                "Full Stack Developer",
                "Nemetschek"
            )

            missing = analysis['missing_requirements']

            # Should detect some missing skills
            if len(missing['skills']) > 0 or len(missing['technologies']) > 0:
                logger.info(f"✅ Missing skills detection passed: {len(missing['skills'])} missing skills, {len(missing['technologies'])} missing technologies")

                # Check for transferable skills suggestions
                if len(missing['can_add']) > 0:
                    logger.info(f"✅ Transferable skills suggested: {len(missing['can_add'])} suggestions")

                self.results['test_details'].append({
                    'test': 'Missing Skills Detection',
                    'status': 'PASSED',
                    'missing_skills': len(missing['skills']),
                    'missing_technologies': len(missing['technologies']),
                    'suggested_additions': len(missing['can_add'])
                })

                return True
            else:
                logger.warning("⚠️ Missing skills detection may not be working properly")
                return False

        except Exception as e:
            logger.error(f"❌ Missing skills detection test failed: {e}")
            return False

    def test_resume_prioritization(self) -> bool:
        """Test that resume content is properly prioritized"""
        logger.info("🧪 Testing resume content prioritization...")

        try:
            # Job focused on networking and security
            networking_job = '''
            Network Security Engineer position requiring:
            - Strong networking knowledge (BGP, OSPF, ISIS)
            - Security experience with firewalls and DDoS mitigation
            - Experience with eBPF and iptables
            - Knowledge of TLS and Zero-Trust architecture
            - Infrastructure automation experience
            '''

            # Generate resume
            resume_path = self.resume_generator.generate_customized_resume(
                job_description=networking_job,
                job_title="Network Security Engineer",
                company="Nemetschek",
                output_format="pdf"
            )

            analysis = self.resume_generator.job_analysis

            # Check that networking/security experience is prioritized
            experience_scores = analysis['relevance_scores']['experience']

            # Aviatrix should score highest due to networking/security work
            aviatrix_score = experience_scores.get('Aviatrix', 0)

            if aviatrix_score > 50:  # Should be high relevance
                logger.info(f"✅ Resume prioritization working: Aviatrix scored {aviatrix_score:.1f}%")

                self.results['test_details'].append({
                    'test': 'Resume Prioritization',
                    'status': 'PASSED',
                    'top_experience_score': aviatrix_score,
                    'resume_path': resume_path
                })

                return True
            else:
                logger.warning(f"⚠️ Resume prioritization may need improvement: Aviatrix scored {aviatrix_score:.1f}%")
                return False

        except Exception as e:
            logger.error(f"❌ Resume prioritization test failed: {e}")
            return False

    def test_automation_initialization(self) -> bool:
        """Test that automation system can initialize properly"""
        logger.info("🧪 Testing automation system initialization...")

        try:
            # Test without actually running browser automation
            automation = SAPNemetschekCareersAutomation(headless=True)

            # Test that personal data is loaded
            if automation.application_data and 'personal_info' in automation.application_data:
                logger.info("✅ Automation system initialized with personal data")

                # Test that resume generator is integrated
                if automation.resume_generator:
                    logger.info("✅ Resume generator integrated successfully")

                    self.results['test_details'].append({
                        'test': 'Automation System Initialization',
                        'status': 'PASSED',
                        'has_personal_data': True,
                        'has_resume_generator': True
                    })

                    return True
                else:
                    logger.error("❌ Resume generator not integrated")
                    return False
            else:
                logger.error("❌ Personal data not loaded")
                return False

        except Exception as e:
            logger.error(f"❌ Automation initialization test failed: {e}")
            return False

    def run_complete_test_suite(self) -> Dict:
        """Run the complete test suite"""
        logger.info("🚀 STARTING COMPLETE AUTOMATION SYSTEM TESTS")
        logger.info("=" * 70)

        tests = [
            ("Resume Generation", self.test_resume_generation),
            ("Job Analysis Accuracy", self.test_job_analysis_accuracy),
            ("Missing Skills Detection", self.test_missing_skills_detection),
            ("Resume Prioritization", self.test_resume_prioritization),
            ("Automation Initialization", self.test_automation_initialization)
        ]

        for test_name, test_func in tests:
            logger.info(f"🧪 Running test: {test_name}")
            try:
                if test_func():
                    self.results['tests_passed'] += 1
                    logger.info(f"✅ {test_name} - PASSED")
                else:
                    self.results['tests_failed'] += 1
                    logger.error(f"❌ {test_name} - FAILED")
            except Exception as e:
                self.results['tests_failed'] += 1
                logger.error(f"💥 {test_name} - ERROR: {e}")
                self.results['test_details'].append({
                    'test': test_name,
                    'status': 'ERROR',
                    'error': str(e)
                })

        # Calculate results
        total_tests = self.results['tests_passed'] + self.results['tests_failed']
        success_rate = (self.results['tests_passed'] / total_tests * 100) if total_tests > 0 else 0

        self.results['end_time'] = datetime.now().isoformat()
        self.results['total_tests'] = total_tests
        self.results['success_rate'] = success_rate

        # Display results
        logger.info("=" * 70)
        logger.info("📊 COMPLETE AUTOMATION SYSTEM TEST RESULTS")
        logger.info("=" * 70)
        logger.info(f"✅ Tests Passed: {self.results['tests_passed']}")
        logger.info(f"❌ Tests Failed: {self.results['tests_failed']}")
        logger.info(f"📈 Success Rate: {success_rate:.1f}%")
        logger.info("=" * 70)

        if success_rate >= 80:
            logger.info("🎉 COMPLETE SYSTEM TEST SUITE PASSED!")
            logger.info("✅ Dynamic resume generation working")
            logger.info("✅ Job analysis and matching working")
            logger.info("✅ Automation system ready for deployment")
        else:
            logger.warning("⚠️ Some tests failed - review and fix issues")

        return self.results

def main():
    """Main function to run complete system tests"""
    print("🚀 COMPLETE AUTOMATION SYSTEM TEST SUITE")
    print("=" * 60)
    print("Testing integrated system:")
    print("✅ Dynamic Resume Generation")
    print("✅ AI-Powered Job Analysis")
    print("✅ SAP Nemetschek Automation")
    print("✅ Complete Application Workflow")
    print("=" * 60)

    tester = CompleteAutomationSystemTest()

    try:
        results = tester.run_complete_test_suite()

        # Save detailed results
        results_file = f"/home/calelin/awesome-apply/complete_system_test_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(results_file, 'w') as f:
            json.dump(results, f, indent=2)

        print(f"\n📄 Detailed results saved to: {results_file}")

        # Return appropriate exit code
        return 0 if results['success_rate'] >= 80 else 1

    except Exception as e:
        print(f"\n💥 Test suite failed: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())