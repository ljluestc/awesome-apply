#!/usr/bin/env python3
"""
Simple test for the Nemetschek automation system
"""

import os
from intelligent_resume_generator import DynamicResumeGenerator

def test_basic_functionality():
    """Test basic functionality of the resume generator"""
    print("Testing Dynamic Resume Generator...")

    generator = DynamicResumeGenerator()

    # Test job
    job_title = "Senior Software Engineer - CAD Platform"
    job_description = """
    We are looking for a Senior Software Engineer to join our CAD Platform team at Nemetschek.

    Requirements:
    - 5+ years of software engineering experience
    - Strong experience with C++, Python, or Java
    - Experience with 3D graphics and CAD software
    - Knowledge of software architecture and design patterns
    - Experience with cloud platforms (AWS, Azure)
    - Familiarity with CI/CD and DevOps practices

    Responsibilities:
    - Develop and maintain CAD platform components
    - Collaborate with cross-functional teams
    - Implement new features and optimize performance
    - Write clean, maintainable code
    """

    company_name = "Nemetschek"

    print(f"Generating resume for: {job_title} at {company_name}")

    try:
        # Generate tailored resume
        latex_content = generator.generate_latex_resume(job_title, job_description, company_name)

        # Save resume
        filepath = generator.save_resume(latex_content, company_name, job_title)

        print(f"✓ Successfully generated resume: {filepath}")

        # Check if file exists and has content
        if os.path.exists(filepath):
            file_size = os.path.getsize(filepath)
            print(f"✓ File size: {file_size} bytes")

            # Read first few lines to verify content
            with open(filepath, 'r') as f:
                first_lines = f.read(500)
                if "Jiale Lin" in first_lines and "\\documentclass" in first_lines:
                    print("✓ Content verification passed")
                    return True
                else:
                    print("✗ Content verification failed")
                    return False
        else:
            print("✗ File was not created")
            return False

    except Exception as e:
        print(f"✗ Error: {e}")
        return False

def test_job_analysis():
    """Test job requirement analysis"""
    print("\nTesting Job Requirement Analysis...")

    from intelligent_resume_generator import JobRequirementAnalyzer

    analyzer = JobRequirementAnalyzer()

    job_title = "DevOps Engineer"
    job_description = "Kubernetes Docker AWS Python Terraform Jenkins CI/CD monitoring"

    scores = analyzer.analyze_job_description(job_title, job_description)

    print(f"Detected keywords and scores: {scores}")

    expected_keywords = ["kubernetes", "python", "aws", "terraform", "jenkins", "devops"]
    detected_keywords = list(scores.keys())

    matches = [kw for kw in expected_keywords if kw in detected_keywords]
    print(f"Expected: {expected_keywords}")
    print(f"Detected: {detected_keywords}")
    print(f"Matches: {matches}")

    if len(matches) >= 4:  # At least 4 matches
        print("✓ Job analysis test passed")
        return True
    else:
        print("✗ Job analysis test failed")
        return False

def main():
    """Run simple tests"""
    print("="*60)
    print("NEMETSCHEK AUTOMATION SYSTEM - SIMPLE TESTS")
    print("="*60)

    tests = [
        test_basic_functionality,
        test_job_analysis
    ]

    results = []

    for test_func in tests:
        try:
            result = test_func()
            results.append(result)
        except Exception as e:
            print(f"✗ Test {test_func.__name__} failed with error: {e}")
            results.append(False)

    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    print(f"Total tests: {len(tests)}")
    print(f"Passed: {sum(results)}")
    print(f"Failed: {len(results) - sum(results)}")

    if all(results):
        print("✓ All tests passed!")
    else:
        print("✗ Some tests failed")

    return all(results)

if __name__ == "__main__":
    main()