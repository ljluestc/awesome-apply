#!/usr/bin/env python3
"""
Dynamic Resume Generator for Nemetschek Applications
Analyzes job requirements and dynamically generates tailored resumes
"""

import json
import re
from datetime import datetime
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
import logging

@dataclass
class PersonalInfo:
    name: str
    email: str
    phone: str
    website: str
    linkedin: str
    citizenship: str

@dataclass
class Education:
    institution: str
    degree: str
    field: str
    graduation_date: str
    location: str = ""

@dataclass
class Experience:
    company: str
    title: str
    location: str
    start_date: str
    end_date: str
    achievements: List[str]

@dataclass
class Project:
    name: str
    technologies: List[str]
    description: str

@dataclass
class ResumeData:
    personal_info: PersonalInfo
    education: List[Education]
    experience: List[Experience]
    projects: List[Project]
    skills: Dict[str, List[str]]

class DynamicResumeGenerator:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        logging.basicConfig(level=logging.INFO)

        # Base resume data extracted from the PDF
        self.base_resume = ResumeData(
            personal_info=PersonalInfo(
                name="Jiale Lin",
                email="jeremykalilin@gmail.com",
                phone="+1-510-417-5834",
                website="ljluestc.github.io",
                linkedin="linkedin.com/in/jiale-lin",
                citizenship="U.S. Citizen"
            ),
            education=[
                Education(
                    institution="University of Colorado Boulder",
                    degree="Master of Science",
                    field="Computer Science",
                    graduation_date="May 2025"
                ),
                Education(
                    institution="University of Arizona",
                    degree="Bachelor",
                    field="Mathematics (CS Emphasis)",
                    graduation_date="May 2019"
                )
            ],
            experience=[
                Experience(
                    company="Aviatrix",
                    title="Senior Software Engineer (2024–Present) | Senior MTS (2023–2024) | MTS (2022–2023)",
                    location="Santa Clara, CA",
                    start_date="May 2022",
                    end_date="Present",
                    achievements=[
                        "Software Development: Developed REST/gRPC services using Go, Python, Bash, Kafka; optimized service boundaries, caching, and concurrency for scalability and reliability.",
                        "Infrastructure & DevOps Automation: Automated infrastructure with Terraform; operated Kubernetes across AWS, Azure, and GCP; built CI/CD with GitHub Actions, Jenkins, ArgoCD, and GitOps, reducing deployment time by 30%.",
                        "Observability: Enhanced monitoring with Prometheus, Grafana, and DataDog; added CI/CD health signals and SLOs; reduced MTTR by 15%.",
                        "Security & Networking: Built secure multi-cloud automation with TLS and Zero-Trust; implemented eBPF/iptables validation for firewall upgrades and DDoS mitigation; hardened supply chain with SBOM and policy gates."
                    ]
                ),
                Experience(
                    company="Veeva Systems",
                    title="Software Development Engineer in Test",
                    location="Pleasanton, CA",
                    start_date="Aug 2021",
                    end_date="May 2022",
                    achievements=[
                        "BDD Framework Development: Implemented a cross-platform BDD framework using Kotlin, Cucumber, and Gradle; integrated with Jenkins CI to automate execution and expand coverage.",
                        "UI Test Automation: Automated web UI with Selenium and native iOS/Android with Appium; integrated suites into CI/CD with dashboards and flaky-test quarantine.",
                        "Process Optimization: Streamlined QA by refactoring suites and optimizing test cases, improving defect detection and reducing regression escapes."
                    ]
                ),
                Experience(
                    company="Google Fiber (via Adecco)",
                    title="Test Engineer",
                    location="Mountain View, CA",
                    start_date="Jun 2019",
                    end_date="Jun 2021",
                    achievements=[
                        "Test Automation: Developed a Page Object Model framework with Selenium/WebDriver (Java) for Angular apps, reducing test failures by 25%.",
                        "Database Optimization: Built BigQuery SQL objects (tables, views, macros, procedures), boosting query performance by 30%.",
                        "Automation: Automated tasks using Google Apps Script, Python, and Bash, saving 15 hrs/week.",
                        "Network Testing: Performed CPE testing with Ixia Veriwave, improving network throughput by 20%.",
                        "Infrastructure & Monitoring: Streamlined deployments with Docker and Kubernetes; implemented Prometheus/Grafana for real-time monitoring."
                    ]
                )
            ],
            projects=[
                Project(
                    name="AI-Powered Network Traffic Classifier",
                    technologies=["C++", "Python", "TF/ONNX", "eBPF", "gRPC", "K8s"],
                    description="Realtime packet/flow features via eBPF; ONNX model served over async gRPC on Kubernetes with rollout guards (shadow A/B, drift detection, canary). Qt6/Electron dashboard with rate/latency charts; CI for model eval (AUC/PR), onnxruntime CPU/GPU."
                ),
                Project(
                    name="Graph-based Social Recommender",
                    technologies=["Python", "Node2Vec", "FAISS", "MF", "Airflow"],
                    description="Graph ETL → Node2Vec embeddings + matrix factorization; FAISS ANN for sub-ms top-k retrieval; offline metrics (AUC, NDCG) and online CTR lift (double-digit). Deployed as FastAPI service with Redis cache; Airflow DAGs for retraining/backfills."
                ),
                Project(
                    name="Algorithm Visualization Tool",
                    technologies=["JavaFX", "k-NN", "Telemetry"],
                    description="Interactive 2D collision/physics visualizer with toggleable k-NN 'ML mode' vs. analytic solver; perf counters, frame timing, exportable traces — live demo."
                ),
                Project(
                    name="Multi-Protocol Router Sim",
                    technologies=["C++", "FRR", "BGP/OSPF/ISIS", "Netem", "CMake"],
                    description="FRR control-plane integration; token-bucket/WFQ shaping; tc/netem impairments; gtest coverage and pcap diffing; CLI & YAML scenarios for regression suites."
                )
            ],
            skills={
                "Programming Languages": ["Go", "Python", "C++", "Java", "Kotlin", "JavaScript", "Bash"],
                "Cloud Platforms": ["AWS", "Azure", "GCP"],
                "Infrastructure": ["Kubernetes", "Docker", "Terraform"],
                "CI/CD": ["GitHub Actions", "Jenkins", "ArgoCD", "GitOps"],
                "Monitoring": ["Prometheus", "Grafana", "DataDog"],
                "Databases": ["BigQuery", "Redis"],
                "Testing": ["Selenium", "Appium", "Cucumber", "gtest"],
                "Networking": ["eBPF", "iptables", "BGP", "OSPF", "ISIS"],
                "Security": ["TLS", "Zero-Trust", "SBOM", "DDoS mitigation"],
                "Frameworks": ["gRPC", "REST", "FastAPI", "JavaFX", "Qt6", "Electron"]
            }
        )

    def analyze_job_requirements(self, job_description: str) -> Dict[str, Any]:
        """Analyze job description to extract key requirements"""
        requirements = {
            "required_skills": [],
            "preferred_skills": [],
            "technologies": [],
            "experience_level": "",
            "domain_focus": [],
            "certifications": []
        }

        # Common technology patterns
        tech_patterns = {
            "cloud": r"\b(AWS|Azure|GCP|Google Cloud|Amazon Web Services|Microsoft Azure)\b",
            "containers": r"\b(Kubernetes|Docker|K8s|containerization|Helm)\b",
            "cicd": r"\b(CI/CD|Jenkins|GitHub Actions|GitLab CI|ArgoCD|DevOps)\b",
            "programming": r"\b(Python|Java|Go|C\+\+|JavaScript|TypeScript|Kotlin|Scala)\b",
            "databases": r"\b(SQL|PostgreSQL|MySQL|MongoDB|Redis|BigQuery|NoSQL)\b",
            "monitoring": r"\b(Prometheus|Grafana|DataDog|ELK|monitoring|observability)\b",
            "automation": r"\b(Terraform|Ansible|Chef|Puppet|Infrastructure as Code|IaC)\b",
            "testing": r"\b(testing|automation|Selenium|unit tests|integration tests)\b",
            "security": r"\b(security|encryption|TLS|authentication|authorization|RBAC)\b",
            "networking": r"\b(networking|TCP/IP|HTTP|REST|gRPC|API)\b"
        }

        # Extract technologies
        for category, pattern in tech_patterns.items():
            matches = re.findall(pattern, job_description, re.IGNORECASE)
            if matches:
                requirements["technologies"].extend(matches)
                requirements["domain_focus"].append(category)

        # Extract experience level
        exp_patterns = [
            (r"(\d+)\+?\s*years?\s*(?:of\s*)?experience", "years"),
            (r"senior|lead|principal", "senior"),
            (r"junior|entry.level|graduate", "junior"),
            (r"mid.level|intermediate", "mid")
        ]

        for pattern, level in exp_patterns:
            if re.search(pattern, job_description, re.IGNORECASE):
                requirements["experience_level"] = level
                break

        return requirements

    def calculate_relevance_score(self, achievement: str, job_requirements: Dict[str, Any]) -> float:
        """Calculate how relevant an achievement is to the job requirements"""
        score = 0.0
        achievement_lower = achievement.lower()

        # Check for technology matches
        for tech in job_requirements.get("technologies", []):
            if tech.lower() in achievement_lower:
                score += 1.0

        # Check for domain focus matches
        domain_keywords = {
            "cloud": ["aws", "azure", "gcp", "cloud", "multi-cloud"],
            "containers": ["kubernetes", "docker", "k8s", "container"],
            "cicd": ["ci/cd", "jenkins", "github actions", "deployment", "devops"],
            "monitoring": ["prometheus", "grafana", "monitoring", "observability", "datadog"],
            "security": ["security", "tls", "zero-trust", "ddos", "firewall"],
            "automation": ["terraform", "automation", "infrastructure"],
            "testing": ["testing", "test", "automation", "selenium"],
            "networking": ["network", "grpc", "rest", "api", "ebpf"]
        }

        for domain in job_requirements.get("domain_focus", []):
            if domain in domain_keywords:
                for keyword in domain_keywords[domain]:
                    if keyword in achievement_lower:
                        score += 0.5

        return score

    def prioritize_experience(self, job_requirements: Dict[str, Any]) -> List[Experience]:
        """Prioritize and potentially reorder experience based on job requirements"""
        scored_experiences = []

        for exp in self.base_resume.experience:
            total_score = 0.0
            for achievement in exp.achievements:
                total_score += self.calculate_relevance_score(achievement, job_requirements)

            # Boost score for recent experience
            if "present" in exp.end_date.lower():
                total_score += 2.0
            elif "2024" in exp.end_date or "2023" in exp.end_date:
                total_score += 1.0

            scored_experiences.append((exp, total_score))

        # Sort by score (descending)
        scored_experiences.sort(key=lambda x: x[1], reverse=True)
        return [exp for exp, score in scored_experiences]

    def prioritize_achievements(self, achievements: List[str], job_requirements: Dict[str, Any]) -> List[str]:
        """Prioritize achievements within an experience based on job requirements"""
        scored_achievements = []

        for achievement in achievements:
            score = self.calculate_relevance_score(achievement, job_requirements)
            scored_achievements.append((achievement, score))

        # Sort by score (descending)
        scored_achievements.sort(key=lambda x: x[1], reverse=True)
        return [ach for ach, score in scored_achievements]

    def enhance_achievements_for_job(self, achievements: List[str], job_requirements: Dict[str, Any]) -> List[str]:
        """Enhance achievements by emphasizing relevant keywords"""
        enhanced_achievements = []

        for achievement in achievements:
            enhanced = achievement

            # Add emphasis to relevant technologies
            for tech in job_requirements.get("technologies", []):
                if tech.lower() in achievement.lower():
                    # Bold important technologies
                    enhanced = re.sub(
                        f"\\b{re.escape(tech)}\\b",
                        f"\\textbf{{{tech}}}",
                        enhanced,
                        flags=re.IGNORECASE
                    )

            enhanced_achievements.append(enhanced)

        return enhanced_achievements

    def generate_latex_resume(self, job_title: str, company: str, job_requirements: Dict[str, Any]) -> str:
        """Generate a tailored LaTeX resume"""
        prioritized_experience = self.prioritize_experience(job_requirements)

        # Enhance each experience's achievements
        for exp in prioritized_experience:
            exp.achievements = self.enhance_achievements_for_job(
                self.prioritize_achievements(exp.achievements, job_requirements),
                job_requirements
            )

        latex_content = f"""%---------------------------------------------------------
% Resume in LaTeX (sb2nov template) — Jiale Lin
% Dynamically generated for {company} - {job_title}
% Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
%---------------------------------------------------------

\\documentclass[letterpaper,11pt]{{article}}

\\usepackage{{latexsym}}
\\usepackage[empty]{{fullpage}}
\\usepackage{{titlesec}}
\\usepackage{{marvosym}}
\\usepackage[usenames,dvipsnames]{{color}}
\\usepackage{{verbatim}}
\\usepackage{{enumitem}}
\\usepackage[pdftex]{{hyperref}}
\\usepackage{{fancyhdr}}

\\pagestyle{{fancy}}
\\fancyhf{{}}
\\fancyfoot{{}}
\\renewcommand{{\\headrulewidth}}{{0pt}}
\\renewcommand{{\\footrulewidth}}{{0pt}}

% Adjust margins
\\addtolength{{\\oddsidemargin}}{{-0.375in}}
\\addtolength{{\\evensidemargin}}{{-0.375in}}
\\addtolength{{\\textwidth}}{{1in}}
\\addtolength{{\\topmargin}}{{-.5in}}
\\addtolength{{\\textheight}}{{1.0in}}

\\urlstyle{{same}}
\\raggedbottom
\\raggedright
\\setlength{{\\tabcolsep}}{{0in}}
\\setlength{{\\parindent}}{{0pt}}

% Section formatting
\\titleformat{{\\section}}{{
  \\vspace{{-4pt}}\\scshape\\raggedright\\large
}}{{}}{{0em}}{{}}[\\color{{black}}\\titlerule \\vspace{{-6pt}}]

% List formatting
\\newcommand{{\\resumeItem}}[2]{{\\item\\small{{\\textbf{{#1}}{{: }}#2}}}}
\\newcommand{{\\resumeSubheading}}[4]{{%
  \\vspace{{-1pt}}\\item
    \\begin{{tabular*}}{{0.97\\textwidth}}{{l@{{\\extracolsep{{\\fill}}}}r}}
      \\textbf{{#1}} & #2 \\\\
      \\textit{{\\small #3}} & \\textit{{\\small #4}} \\\\
    \\end{{tabular*}}\\vspace{{-4pt}}
}}
\\newcommand{{\\resumeSubItem}}[2]{{\\resumeItem{{#1}}{{#2}}\\vspace{{-2pt}}}}
\\renewcommand{{\\labelitemii}}{{$\\circ$}}

\\newcommand{{\\resumeSubHeadingListStart}}{{\\begin{{itemize}}[leftmargin=*, itemsep=1pt, topsep=2pt]}}
\\newcommand{{\\resumeSubHeadingListEnd}}{{\\end{{itemize}}}}
\\newcommand{{\\resumeItemListStart}}{{\\begin{{itemize}}[leftmargin=*, itemsep=1pt, topsep=1pt]}}
\\newcommand{{\\resumeItemListEnd}}{{\\end{{itemize}}\\vspace{{-4pt}}}}

%-------------------------------------------
%%%%%%  CV STARTS HERE  %%%%%%%%%%%%%%%%%%%%

\\begin{{document}}

%----------HEADING-----------------
\\begin{{tabular*}}{{\\textwidth}}{{l@{{\\extracolsep{{\\fill}}}}r}}
  \\textbf{{\\Large {self.base_resume.personal_info.name}}} & \\href{{mailto:{self.base_resume.personal_info.email}}}{{{self.base_resume.personal_info.email}}}\\\\
  \\href{{https://{self.base_resume.personal_info.website}}}{{{self.base_resume.personal_info.website}}} & {self.base_resume.personal_info.phone} \\\\
  \\href{{https://{self.base_resume.personal_info.linkedin}}}{{{self.base_resume.personal_info.linkedin}}} & {self.base_resume.personal_info.citizenship} \\\\
\\end{{tabular*}}

%-----------EDUCATION-----------------
\\section{{Education}}
  \\resumeSubHeadingListStart"""

        # Add education
        for edu in self.base_resume.education:
            latex_content += f"""
    \\resumeSubheading
      {{{edu.institution}}}{{}}
      {{{edu.degree} in {edu.field}}}{{{edu.graduation_date}}}"""

        latex_content += """
  \\resumeSubHeadingListEnd

%-----------EXPERIENCE-----------------
\\section{Experience}
  \\resumeSubHeadingListStart"""

        # Add prioritized experience
        for exp in prioritized_experience:
            latex_content += f"""

    \\resumeSubheading
      {{{exp.company}}}{{{exp.location}}}
      {{{exp.title}}}{{{exp.start_date} -- {exp.end_date}}}
      \\resumeItemListStart"""

            # Add prioritized achievements
            for achievement in exp.achievements[:4]:  # Limit to top 4 achievements
                # Clean up achievement text for LaTeX
                clean_achievement = achievement.replace('&', '\\&')
                latex_content += f"""
        \\resumeItem{{}}
          {{{clean_achievement}}}"""

            latex_content += """
      \\resumeItemListEnd"""

        latex_content += """

  \\resumeSubHeadingListEnd

%-----------PROJECTS-----------------
\\section{Projects}
  \\resumeSubHeadingListStart"""

        # Add projects (could be prioritized based on relevance)
        for project in self.base_resume.projects:
            tech_string = ", ".join(project.technologies)
            clean_description = project.description.replace('&', '\\&')
            latex_content += f"""
    \\resumeSubItem{{{project.name} \\textnormal{{({tech_string})}}}}
      {{{clean_description}}}"""

        latex_content += """
  \\resumeSubHeadingListEnd

\\end{document}"""

        return latex_content

    def generate_cover_letter(self, job_title: str, company: str, job_requirements: Dict[str, Any]) -> str:
        """Generate a tailored cover letter"""

        # Extract relevant experience highlights
        relevant_highlights = []
        for exp in self.base_resume.experience:
            for achievement in exp.achievements:
                score = self.calculate_relevance_score(achievement, job_requirements)
                if score > 0.5:
                    relevant_highlights.append((achievement, score))

        # Sort by relevance and take top 3
        relevant_highlights.sort(key=lambda x: x[1], reverse=True)
        top_highlights = [h[0] for h in relevant_highlights[:3]]

        cover_letter = f"""Dear {company} Hiring Team,

I am writing to express my strong interest in the {job_title} position at {company}. With my background as a Senior Software Engineer at Aviatrix and extensive experience in cloud infrastructure, DevOps automation, and software development, I am excited about the opportunity to contribute to {company}'s innovative technology solutions.

In my current role at Aviatrix, I have developed expertise that directly aligns with your requirements:

"""

        # Add relevant highlights
        for i, highlight in enumerate(top_highlights, 1):
            # Clean up the highlight for the cover letter
            clean_highlight = re.sub(r'^[^:]+:\s*', '', highlight)
            cover_letter += f"• {clean_highlight}\n"

        cover_letter += f"""
My experience spans the full software development lifecycle, from designing scalable architectures to implementing robust CI/CD pipelines. I have consistently delivered measurable results, including reducing deployment times by 30% and improving system reliability.

I am particularly drawn to {company}'s commitment to innovation and would welcome the opportunity to discuss how my technical expertise and problem-solving abilities can contribute to your team's success.

Thank you for your consideration. I look forward to hearing from you.

Best regards,
{self.base_resume.personal_info.name}
{self.base_resume.personal_info.email}
{self.base_resume.personal_info.phone}"""

        return cover_letter

def main():
    generator = DynamicResumeGenerator()

    # Example usage
    sample_job_description = """
    We are looking for a Senior DevOps Engineer with 5+ years of experience.
    Requirements:
    - Strong experience with AWS, Azure, or GCP
    - Kubernetes and Docker expertise
    - CI/CD pipeline development (Jenkins, GitHub Actions)
    - Infrastructure as Code (Terraform, Ansible)
    - Monitoring and observability (Prometheus, Grafana)
    - Python and Go programming skills
    - Security best practices
    """

    job_requirements = generator.analyze_job_requirements(sample_job_description)
    print("Analyzed job requirements:", json.dumps(job_requirements, indent=2))

    # Generate tailored resume
    latex_resume = generator.generate_latex_resume(
        "Senior DevOps Engineer",
        "Nemetschek",
        job_requirements
    )

    # Generate cover letter
    cover_letter = generator.generate_cover_letter(
        "Senior DevOps Engineer",
        "Nemetschek",
        job_requirements
    )

    print("\nGenerated LaTeX resume and cover letter successfully!")

    return latex_resume, cover_letter

if __name__ == "__main__":
    main()