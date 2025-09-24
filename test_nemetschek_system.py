#!/usr/bin/env python3
"""
Test script to demonstrate the dynamic resume generation system
"""

import json
from datetime import datetime
from nemetschek_dynamic_resume_generator import DynamicResumeGenerator

def test_dynamic_resume_generation():
    """Test the dynamic resume generation with sample job descriptions"""

    generator = DynamicResumeGenerator()

    # Sample job descriptions from Nemetschek-type companies
    test_jobs = [
        {
            "title": "Senior DevOps Engineer - Infrastructure",
            "company": "Nemetschek",
            "description": """
            We are seeking a Senior DevOps Engineer to join our Infrastructure team.
            You will be responsible for:

            Requirements:
            - 5+ years of experience with AWS, Azure, or GCP
            - Strong experience with Kubernetes and Docker
            - Expertise in CI/CD pipelines (Jenkins, GitHub Actions, GitLab CI)
            - Infrastructure as Code (Terraform, CloudFormation)
            - Monitoring and observability (Prometheus, Grafana, DataDog)
            - Python, Go, or Java programming skills
            - Experience with microservices architecture
            - Security best practices and compliance
            - Bachelor's degree in Computer Science or related field

            Preferred:
            - Experience with service mesh (Istio, Linkerd)
            - Knowledge of databases (PostgreSQL, Redis, MongoDB)
            - Experience with logging systems (ELK, Splunk)
            - Agile/Scrum methodology experience
            """
        },
        {
            "title": "Full Stack Developer - Web Platform",
            "company": "Nemetschek",
            "description": """
            Join our Web Platform team as a Full Stack Developer working on cutting-edge applications.

            Requirements:
            - 3+ years of full-stack development experience
            - Strong proficiency in JavaScript/TypeScript
            - Experience with React, Angular, or Vue.js
            - Backend development with Node.js, Python, or Java
            - Database design and optimization (SQL and NoSQL)
            - RESTful API development
            - Version control with Git
            - Experience with testing frameworks
            - Understanding of web security principles

            Preferred:
            - Experience with cloud platforms (AWS, Azure, GCP)
            - Knowledge of containerization (Docker, Kubernetes)
            - GraphQL experience
            - Mobile app development experience
            - Experience with CAD software integration
            """
        },
        {
            "title": "Senior Software Engineer - CAD Platform",
            "company": "Nemetschek",
            "description": """
            We're looking for a Senior Software Engineer to work on our CAD Platform.

            Requirements:
            - 5+ years of software development experience
            - Strong proficiency in C++, C#, or Java
            - Experience with desktop application development
            - 3D graphics programming experience (OpenGL, DirectX)
            - Algorithm optimization and performance tuning
            - Experience with large-scale software architecture
            - Knowledge of design patterns and software engineering principles
            - Experience with version control systems (Git, SVN)

            Preferred:
            - Experience with CAD/CAM software development
            - Knowledge of computational geometry
            - Experience with Qt or similar GUI frameworks
            - Understanding of building information modeling (BIM)
            - Experience with software development lifecycle
            """
        },
        {
            "title": "Network Security Engineer",
            "company": "Nemetschek",
            "description": """
            Join our Security team as a Network Security Engineer.

            Requirements:
            - 4+ years of network security experience
            - Strong understanding of network protocols (TCP/IP, HTTP/HTTPS, DNS)
            - Experience with firewalls, VPNs, and intrusion detection systems
            - Knowledge of security frameworks and compliance standards
            - Experience with network monitoring and analysis tools
            - Scripting skills (Python, Bash, PowerShell)
            - Understanding of cloud security (AWS, Azure)
            - Security certifications (CISSP, CISM, CEH) preferred

            Preferred:
            - Experience with SIEM tools
            - Knowledge of threat intelligence and incident response
            - Experience with penetration testing
            - Understanding of DevSecOps practices
            """
        }
    ]

    print("🚀 Testing Dynamic Resume Generation System")
    print("=" * 60)

    results = []

    for job in test_jobs:
        print(f"\n📋 Processing: {job['title']}")
        print(f"Company: {job['company']}")
        print("-" * 40)

        # Analyze job requirements
        job_requirements = generator.analyze_job_requirements(job['description'])

        print("🔍 Analyzed Job Requirements:")
        print(f"  Technologies: {', '.join(job_requirements.get('technologies', [])[:5])}")
        print(f"  Domain Focus: {', '.join(job_requirements.get('domain_focus', []))}")
        print(f"  Experience Level: {job_requirements.get('experience_level', 'Not specified')}")

        # Generate tailored resume
        latex_resume = generator.generate_latex_resume(
            job['title'], job['company'], job_requirements
        )

        # Generate cover letter
        cover_letter = generator.generate_cover_letter(
            job['title'], job['company'], job_requirements
        )

        # Save files
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_title = "".join(c for c in job['title'] if c.isalnum() or c in (' ', '-', '_')).rstrip()
        safe_title = safe_title.replace(' ', '_')

        # Save LaTeX resume
        resume_filename = f"Jiale_Lin_Resume_{job['company']}_{safe_title}_{timestamp}.tex"
        with open(resume_filename, 'w', encoding='utf-8') as f:
            f.write(latex_resume)

        # Save cover letter
        cover_filename = f"Jiale_Lin_Cover_Letter_{job['company']}_{safe_title}_{timestamp}.txt"
        with open(cover_filename, 'w', encoding='utf-8') as f:
            f.write(cover_letter)

        print(f"✅ Generated: {resume_filename}")
        print(f"✅ Generated: {cover_filename}")

        # Store result
        result = {
            "job": job,
            "job_requirements": job_requirements,
            "resume_file": resume_filename,
            "cover_letter_file": cover_filename,
            "timestamp": datetime.now().isoformat()
        }
        results.append(result)

    # Save test results
    test_results_file = f"nemetschek_test_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(test_results_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    print(f"\n📊 Test Results Summary:")
    print(f"  Total jobs processed: {len(results)}")
    print(f"  Documents generated: {len(results) * 2}")
    print(f"  Test results saved to: {test_results_file}")

    # Display sample cover letter
    print(f"\n📝 Sample Cover Letter (for {results[0]['job']['title']}):")
    print("=" * 60)
    with open(results[0]['cover_letter_file'], 'r', encoding='utf-8') as f:
        cover_content = f.read()
        print(cover_content[:500] + "..." if len(cover_content) > 500 else cover_content)

    return results

def test_job_analysis():
    """Test the job requirement analysis functionality"""

    generator = DynamicResumeGenerator()

    sample_description = """
    We are looking for a Senior Software Engineer with 5+ years of experience.

    Required Skills:
    - Strong experience with Python, Go, and JavaScript
    - Experience with AWS, Kubernetes, and Docker
    - CI/CD pipeline development (Jenkins, GitHub Actions)
    - Microservices architecture
    - Database design (PostgreSQL, Redis)
    - Monitoring and observability (Prometheus, Grafana)
    - Security best practices

    Preferred:
    - Experience with machine learning frameworks
    - Knowledge of DevOps practices
    - Agile methodology experience
    """

    print("\n🔬 Testing Job Analysis Functionality")
    print("=" * 60)

    requirements = generator.analyze_job_requirements(sample_description)

    print("📊 Analysis Results:")
    print(json.dumps(requirements, indent=2))

    return requirements

def main():
    """Main test function"""
    print("🧪 Nemetschek Dynamic Resume System - Test Suite")
    print("=" * 60)

    try:
        # Test job analysis
        analysis_results = test_job_analysis()

        # Test dynamic resume generation
        generation_results = test_dynamic_resume_generation()

        print("\n🎉 All tests completed successfully!")
        print(f"✅ Job analysis: {len(analysis_results)} requirements extracted")
        print(f"✅ Resume generation: {len(generation_results)} jobs processed")

        return {
            "analysis_results": analysis_results,
            "generation_results": generation_results
        }

    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    main()