#!/usr/bin/env python3
"""
Intelligent Resume Generator
Dynamically adapts resume content based on job requirements
"""

import json
import re
from datetime import datetime
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class Contact:
    name: str
    email: str
    phone: str
    linkedin: str
    website: str
    location: str

@dataclass
class Education:
    institution: str
    degree: str
    field: str
    graduation_date: str
    location: Optional[str] = ""

@dataclass
class Experience:
    company: str
    position: str
    location: str
    start_date: str
    end_date: str
    achievements: List[str]
    technologies: List[str]
    metrics: List[str]

@dataclass
class Project:
    name: str
    description: str
    technologies: List[str]
    achievements: List[str]
    url: Optional[str] = ""

@dataclass
class Skill:
    category: str
    items: List[str]
    proficiency: str

class ResumeData:
    def __init__(self):
        self.contact = Contact(
            name="Jiale Lin",
            email="jeremykalilin@gmail.com",
            phone="+1-510-417-5834",
            linkedin="linkedin.com/in/jiale-lin",
            website="ljluestc.github.io",
            location="U.S. Citizen"
        )

        self.education = [
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
        ]

        self.experiences = [
            Experience(
                company="Aviatrix",
                position="Senior Software Engineer",
                location="Santa Clara, CA",
                start_date="May 2022",
                end_date="Present",
                achievements=[
                    "Developed REST/gRPC services using Go, Python, Bash, Kafka; optimized service boundaries, caching, and concurrency for scalability and reliability",
                    "Automated infrastructure with Terraform; operated Kubernetes across AWS, Azure, and GCP; built CI/CD with GitHub Actions, Jenkins, ArgoCD, and GitOps, reducing deployment time by 30%",
                    "Enhanced monitoring with Prometheus, Grafana, and DataDog; added CI/CD health signals and SLOs; reduced MTTR by 15%",
                    "Built secure multi-cloud automation with TLS and Zero-Trust; implemented eBPF/iptables validation for firewall upgrades and DDoS mitigation; hardened supply chain with SBOM and policy gates"
                ],
                technologies=["Go", "Python", "Bash", "Kafka", "Terraform", "Kubernetes", "AWS", "Azure", "GCP", "GitHub Actions", "Jenkins", "ArgoCD", "Prometheus", "Grafana", "DataDog", "eBPF", "iptables"],
                metrics=["30% deployment time reduction", "15% MTTR reduction"]
            ),
            Experience(
                company="Veeva Systems",
                position="Software Development Engineer in Test",
                location="Pleasanton, CA",
                start_date="Aug 2021",
                end_date="May 2022",
                achievements=[
                    "Implemented a cross-platform BDD framework using Kotlin, Cucumber, and Gradle; integrated with Jenkins CI to automate execution and expand coverage",
                    "Automated web UI with Selenium and native iOS/Android with Appium; integrated suites into CI/CD with dashboards and flaky-test quarantine",
                    "Streamlined QA by refactoring suites and optimizing test cases, improving defect detection and reducing regression escapes"
                ],
                technologies=["Kotlin", "Cucumber", "Gradle", "Jenkins", "Selenium", "Appium", "iOS", "Android"],
                metrics=[]
            ),
            Experience(
                company="Google Fiber (via Adecco)",
                position="Test Engineer",
                location="Mountain View, CA",
                start_date="Jun 2019",
                end_date="Jun 2021",
                achievements=[
                    "Developed a Page Object Model framework with Selenium/WebDriver (Java) for Angular apps, reducing test failures by 25%",
                    "Built BigQuery SQL objects (tables, views, macros, procedures), boosting query performance by 30%",
                    "Automated tasks using Google Apps Script, Python, and Bash, saving 15 hrs/week",
                    "Performed CPE testing with Ixia Veriwave, improving network throughput by 20%",
                    "Streamlined deployments with Docker and Kubernetes; implemented Prometheus/Grafana for real-time monitoring"
                ],
                technologies=["Java", "Selenium", "WebDriver", "Angular", "BigQuery", "SQL", "Google Apps Script", "Python", "Bash", "Docker", "Kubernetes", "Prometheus", "Grafana"],
                metrics=["25% test failure reduction", "30% query performance boost", "15 hrs/week saved", "20% network throughput improvement"]
            )
        ]

        self.projects = [
            Project(
                name="AI-Powered Network Traffic Classifier",
                description="Realtime packet/flow features via eBPF; ONNX model served over async gRPC on Kubernetes with rollout guards (shadow A/B, drift detection, canary). Qt6/Electron dashboard with rate/latency charts; CI for model eval (AUC/PR), onnxruntime CPU/GPU",
                technologies=["C++", "Python", "TensorFlow", "ONNX", "eBPF", "gRPC", "Kubernetes", "Qt6", "Electron"],
                achievements=["Real-time packet classification", "Shadow A/B testing", "Drift detection", "Canary deployments"]
            ),
            Project(
                name="Graph-based Social Recommender",
                description="Graph ETL → Node2Vec embeddings + matrix factorization; FAISS ANN for sub-ms top-k retrieval; offline metrics (AUC, NDCG) and online CTR lift (double-digit). Deployed as FastAPI service with Redis cache; Airflow DAGs for retraining/backfills",
                technologies=["Python", "Node2Vec", "FAISS", "Matrix Factorization", "Airflow", "FastAPI", "Redis"],
                achievements=["Sub-ms retrieval", "Double-digit CTR lift", "Automated retraining"]
            ),
            Project(
                name="Algorithm Visualization Tool",
                description="Interactive 2D collision/physics visualizer with toggleable k-NN 'ML mode' vs. analytic solver; perf counters, frame timing, exportable traces",
                technologies=["JavaFX", "k-NN", "Machine Learning"],
                achievements=["Interactive visualization", "Performance monitoring", "Exportable traces"],
                url="ljluestc.github.io/visualgo/demo.html"
            ),
            Project(
                name="Multi-Protocol Router Sim",
                description="FRR control-plane integration; token-bucket/WFQ shaping; tc/netem impairments; gtest coverage and pcap diffing; CLI & YAML scenarios for regression suites",
                technologies=["C++", "FRR", "BGP", "OSPF", "ISIS", "Netem", "CMake"],
                achievements=["Protocol simulation", "Automated testing", "Regression coverage"]
            )
        ]

        self.skills = {
            "Programming Languages": ["Python", "Go", "C++", "Java", "Kotlin", "JavaScript", "Bash"],
            "Cloud & Infrastructure": ["AWS", "Azure", "GCP", "Kubernetes", "Docker", "Terraform"],
            "DevOps & CI/CD": ["GitHub Actions", "Jenkins", "ArgoCD", "GitOps"],
            "Monitoring & Observability": ["Prometheus", "Grafana", "DataDog"],
            "Databases": ["BigQuery", "SQL", "Redis"],
            "Testing & QA": ["Selenium", "Appium", "Cucumber", "Gradle", "JUnit"],
            "Networking & Security": ["eBPF", "iptables", "TLS", "Zero-Trust", "BGP", "OSPF"],
            "Machine Learning": ["TensorFlow", "ONNX", "Node2Vec", "FAISS", "Scikit-learn"],
            "Web Technologies": ["REST", "gRPC", "FastAPI", "Angular", "React"]
        }

class JobRequirementAnalyzer:
    def __init__(self):
        self.keyword_weights = {
            # Technical Skills
            "python": 1.0, "go": 1.0, "java": 1.0, "c++": 1.0, "javascript": 1.0,
            "kubernetes": 1.0, "docker": 1.0, "aws": 1.0, "azure": 1.0, "gcp": 1.0,
            "terraform": 1.0, "jenkins": 1.0, "ci/cd": 1.0, "devops": 1.0,
            "microservices": 1.0, "rest": 1.0, "grpc": 1.0, "api": 1.0,
            "machine learning": 1.0, "ai": 1.0, "tensorflow": 1.0, "pytorch": 1.0,
            "sql": 1.0, "nosql": 1.0, "redis": 1.0, "postgresql": 1.0, "mongodb": 1.0,

            # Job Types
            "senior": 1.2, "lead": 1.2, "principal": 1.2, "staff": 1.2,
            "fullstack": 1.0, "backend": 1.0, "frontend": 1.0, "devops": 1.0,
            "security": 1.0, "infrastructure": 1.0, "platform": 1.0,

            # Company Focus Areas
            "cad": 1.0, "architecture": 1.0, "construction": 1.0, "design": 1.0,
            "engineering": 1.0, "3d": 1.0, "modeling": 1.0, "simulation": 1.0,

            # Soft Skills
            "leadership": 0.8, "mentoring": 0.8, "collaboration": 0.8, "agile": 0.8,
            "scrum": 0.8, "communication": 0.8, "problem-solving": 0.8
        }

    def analyze_job_description(self, job_title: str, job_description: str) -> Dict[str, float]:
        """Analyze job requirements and return keyword scores"""
        text = (job_title + " " + job_description).lower()

        scores = {}
        for keyword, weight in self.keyword_weights.items():
            count = len(re.findall(r'\b' + re.escape(keyword) + r'\b', text))
            if count > 0:
                scores[keyword] = count * weight

        return scores

    def get_relevant_technologies(self, job_scores: Dict[str, float], resume_data: ResumeData) -> List[str]:
        """Extract relevant technologies based on job requirements"""
        all_techs = set()

        # Collect all technologies from resume
        for exp in resume_data.experiences:
            all_techs.update([tech.lower() for tech in exp.technologies])

        for project in resume_data.projects:
            all_techs.update([tech.lower() for tech in project.technologies])

        for category, skills in resume_data.skills.items():
            all_techs.update([skill.lower() for skill in skills])

        # Match with job requirements
        relevant_techs = []
        for tech in all_techs:
            if any(keyword in tech or tech in keyword for keyword in job_scores.keys()):
                relevant_techs.append(tech)

        return list(set(relevant_techs))

class DynamicResumeGenerator:
    def __init__(self):
        self.resume_data = ResumeData()
        self.analyzer = JobRequirementAnalyzer()

    def generate_latex_resume(self, job_title: str, job_description: str, company_name: str = "") -> str:
        """Generate a LaTeX resume tailored to specific job requirements"""

        # Analyze job requirements
        job_scores = self.analyzer.analyze_job_description(job_title, job_description)
        relevant_techs = self.analyzer.get_relevant_technologies(job_scores, self.resume_data)

        # Filter and prioritize experiences
        prioritized_experiences = self._prioritize_experiences(job_scores)
        relevant_projects = self._select_relevant_projects(job_scores, relevant_techs)

        # Generate LaTeX content
        latex_content = self._generate_latex_header()
        latex_content += self._generate_contact_section()
        latex_content += self._generate_education_section()
        latex_content += self._generate_experience_section(prioritized_experiences, job_scores)
        latex_content += self._generate_projects_section(relevant_projects, job_scores)
        latex_content += self._generate_footer()

        return latex_content

    def _prioritize_experiences(self, job_scores: Dict[str, float]) -> List[Experience]:
        """Prioritize experiences based on job requirements"""
        scored_experiences = []

        for exp in self.resume_data.experiences:
            score = 0
            exp_text = " ".join(exp.achievements + exp.technologies).lower()

            for keyword, weight in job_scores.items():
                if keyword in exp_text:
                    score += weight

            scored_experiences.append((score, exp))

        # Sort by score (descending) and return experiences
        scored_experiences.sort(key=lambda x: x[0], reverse=True)
        return [exp for _, exp in scored_experiences]

    def _select_relevant_projects(self, job_scores: Dict[str, float], relevant_techs: List[str]) -> List[Project]:
        """Select most relevant projects based on job requirements"""
        scored_projects = []

        for project in self.resume_data.projects:
            score = 0
            project_text = (project.name + " " + project.description + " " +
                          " ".join(project.technologies + project.achievements)).lower()

            # Score based on job keywords
            for keyword, weight in job_scores.items():
                if keyword in project_text:
                    score += weight

            # Bonus for relevant technologies
            for tech in relevant_techs:
                if tech in project_text:
                    score += 0.5

            scored_projects.append((score, project))

        # Sort by score and return top projects
        scored_projects.sort(key=lambda x: x[0], reverse=True)
        return [project for _, project in scored_projects[:4]]  # Top 4 projects

    def _enhance_achievements(self, achievements: List[str], job_scores: Dict[str, float]) -> List[str]:
        """Enhance achievement descriptions based on job requirements"""
        enhanced = []

        for achievement in achievements:
            # Add emphasis to relevant keywords
            enhanced_text = achievement
            for keyword in job_scores.keys():
                if keyword in achievement.lower():
                    # Add LaTeX bold formatting for relevant keywords
                    pattern = re.compile(re.escape(keyword), re.IGNORECASE)
                    enhanced_text = pattern.sub(f"\\textbf{{{keyword}}}", enhanced_text, count=1)

            enhanced.append(enhanced_text)

        return enhanced

    def _generate_latex_header(self) -> str:
        return """% Resume in LaTeX (sb2nov template) — Jiale Lin
% https://github.com/sb2nov/resume  |  License: MIT
%------------------------

\\documentclass[letterpaper,11pt]{article}

\\usepackage{latexsym}
\\usepackage[empty]{fullpage}
\\usepackage{titlesec}
\\usepackage{marvosym}
\\usepackage[usenames,dvipsnames]{color}
\\usepackage{verbatim}
\\usepackage{enumitem}
\\usepackage[pdftex]{hyperref}
\\usepackage{fancyhdr}

\\pagestyle{fancy}
\\fancyhf{} % clear header/footer
\\fancyfoot{}
\\renewcommand{\\headrulewidth}{0pt}
\\renewcommand{\\footrulewidth}{0pt}

% Adjust margins (sb2nov defaults)
\\addtolength{\\oddsidemargin}{-0.375in}
\\addtolength{\\evensidemargin}{-0.375in}
\\addtolength{\\textwidth}{1in}
\\addtolength{\\topmargin}{-.5in}
\\addtolength{\\textheight}{1.0in}

\\urlstyle{same}
\\raggedbottom
\\raggedright
\\setlength{\\tabcolsep}{0in}
\\setlength{\\parindent}{0pt}

% Section formatting (sb2nov defaults, slightly tighter rule space)
\\titleformat{\\section}{
  \\vspace{-4pt}\\scshape\\raggedright\\large
}{}{0em}{}[\\color{black}\\titlerule \\vspace{-6pt}]

% Tight lists
\\newcommand{\\resumeItem}[2]{\\item\\small{\\textbf{#1}{: }#2}}
\\newcommand{\\resumeSubheading}[4]{%
  \\vspace{-1pt}\\item
    \\begin{tabular*}{0.97\\textwidth}{l@{\\extracolsep{\\fill}}r}
      \\textbf{#1} & #2 \\\\
      \\textit{\\small #3} & \\textit{\\small #4} \\\\
    \\end{tabular*}\\vspace{-4pt}
}
\\newcommand{\\resumeSubItem}[2]{\\resumeItem{#1}{#2}\\vspace{-2pt}}
\\renewcommand{\\labelitemii}{$\\circ$}

\\newcommand{\\resumeSubHeadingListStart}{\\begin{itemize}[leftmargin=*, itemsep=1pt, topsep=2pt]}
\\newcommand{\\resumeSubHeadingListEnd}{\\end{itemize}}
\\newcommand{\\resumeItemListStart}{\\begin{itemize}[leftmargin=*, itemsep=1pt, topsep=1pt]}
\\newcommand{\\resumeItemListEnd}{\\end{itemize}\\vspace{-4pt}}

%-------------------------------------------
%%%%%%  CV STARTS HERE  %%%%%%%%%%%%%%%%%%%%

\\begin{document}

"""

    def _generate_contact_section(self) -> str:
        contact = self.resume_data.contact
        return f"""
%----------HEADING-----------------
\\begin{{tabular*}}{{\\textwidth}}{{l@{{\\extracolsep{{\\fill}}}}r}}
  \\textbf{{\\Large {contact.name}}} & \\href{{mailto:{contact.email}}}{{{contact.email}}}\\\\
  \\href{{{contact.website}}}{{{contact.website}}} & {contact.phone} \\\\
  \\href{{{contact.linkedin}}}{{{contact.linkedin}}} & {contact.location} \\\\
\\end{{tabular*}}

"""

    def _generate_education_section(self) -> str:
        content = "%-----------EDUCATION-----------------\n\\section{Education}\n  \\resumeSubHeadingListStart\n"

        for edu in self.resume_data.education:
            content += f"""    \\resumeSubheading
      {{{edu.institution}}}{{{edu.location}}}
      {{{edu.degree} in {edu.field}}}{{{edu.graduation_date}}}
"""

        content += "  \\resumeSubHeadingListEnd\n\n"
        return content

    def _generate_experience_section(self, experiences: List[Experience], job_scores: Dict[str, float]) -> str:
        content = "%-----------EXPERIENCE-----------------\n\\section{Experience}\n  \\resumeSubHeadingListStart\n\n"

        for exp in experiences:
            content += f"""    \\resumeSubheading
      {{{exp.company}}}{{{exp.location}}}
      {{{exp.position}}}{{{exp.start_date} -- {exp.end_date}}}
      \\resumeItemListStart
"""

            # Enhance achievements based on job requirements
            enhanced_achievements = self._enhance_achievements(exp.achievements, job_scores)

            for i, achievement in enumerate(enhanced_achievements):
                category = self._categorize_achievement(achievement)
                content += f"        \\resumeItem{{{category}}}\n          {{{achievement}}}\n"

            content += "      \\resumeItemListEnd\n\n"

        content += "  \\resumeSubHeadingListEnd\n\n"
        return content

    def _generate_projects_section(self, projects: List[Project], job_scores: Dict[str, float]) -> str:
        content = "%-----------PROJECTS (EXPANDED)-----------------\n\\section{Projects}\n  \\resumeSubHeadingListStart\n"

        for project in projects:
            tech_string = ", ".join(project.technologies)
            enhanced_description = self._enhance_achievements([project.description], job_scores)[0]

            content += f"""    \\resumeSubItem{{{project.name} \\textnormal{{({tech_string})}}}}
      {{{enhanced_description}}}
"""

        content += "  \\resumeSubHeadingListEnd\n\n"
        return content

    def _generate_footer(self) -> str:
        return "\n%-------------------------------------------\n\\end{document}\n"

    def _categorize_achievement(self, achievement: str) -> str:
        """Categorize achievements for better organization"""
        achievement_lower = achievement.lower()

        if any(word in achievement_lower for word in ["developed", "built", "implemented", "created"]):
            return "Software Development"
        elif any(word in achievement_lower for word in ["automated", "ci/cd", "deployment", "infrastructure"]):
            return "Infrastructure & DevOps Automation"
        elif any(word in achievement_lower for word in ["monitoring", "observability", "metrics", "prometheus"]):
            return "Observability"
        elif any(word in achievement_lower for word in ["security", "tls", "zero-trust", "ebpf"]):
            return "Security & Networking"
        elif any(word in achievement_lower for word in ["test", "qa", "automation", "framework"]):
            return "Test Automation"
        elif any(word in achievement_lower for word in ["database", "sql", "query", "performance"]):
            return "Database Optimization"
        elif any(word in achievement_lower for word in ["process", "optimization", "streamlined"]):
            return "Process Optimization"
        else:
            return "Technical Achievement"

    def save_resume(self, latex_content: str, company_name: str, job_title: str) -> str:
        """Save the generated resume to a file"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_company = re.sub(r'[^a-zA-Z0-9]', '_', company_name)
        safe_title = re.sub(r'[^a-zA-Z0-9]', '_', job_title)

        filename = f"Jiale_Lin_Resume_{safe_company}_{safe_title}_{timestamp}.tex"
        filepath = Path(filename)

        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(latex_content)

        logger.info(f"Resume saved to: {filepath}")
        return str(filepath)

def main():
    """Example usage of the dynamic resume generator"""
    generator = DynamicResumeGenerator()

    # Example job requirements
    job_title = "Senior DevOps Engineer - Infrastructure"
    job_description = """
    We are looking for a Senior DevOps Engineer to join our Infrastructure team.
    You will be responsible for:
    - Building and maintaining cloud infrastructure on AWS, Azure, and GCP
    - Implementing CI/CD pipelines using Jenkins, GitHub Actions, and ArgoCD
    - Managing Kubernetes clusters and container orchestration
    - Developing infrastructure as code using Terraform
    - Implementing monitoring and observability with Prometheus and Grafana
    - Ensuring security best practices and compliance
    - Automating deployment processes and reducing manual operations

    Requirements:
    - 5+ years of experience in DevOps/Infrastructure
    - Strong experience with Go, Python, or similar languages
    - Expertise in Kubernetes, Docker, and container technologies
    - Experience with cloud platforms (AWS, Azure, GCP)
    - Knowledge of Infrastructure as Code (Terraform, CloudFormation)
    - Experience with monitoring tools (Prometheus, Grafana, DataDog)
    - Strong understanding of security practices
    """

    company_name = "Nemetschek"

    # Generate tailored resume
    latex_content = generator.generate_latex_resume(job_title, job_description, company_name)
    filepath = generator.save_resume(latex_content, company_name, job_title)

    print(f"Generated tailored resume: {filepath}")

if __name__ == "__main__":
    main()