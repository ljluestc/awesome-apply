#!/usr/bin/env python3
"""
Enhanced Dynamic Resume Generator with Gap Analysis and Requirement Addition
Analyzes job requirements and dynamically adds missing skills/experiences
"""

import json
import re
from datetime import datetime
from typing import Dict, List, Any, Optional, Set, Tuple
from dataclasses import dataclass, field
import logging

@dataclass
class SkillCategory:
    name: str
    keywords: List[str]
    weight: float = 1.0

@dataclass
class ExperienceGap:
    category: str
    missing_skills: List[str]
    suggested_addition: str
    relevance_score: float

@dataclass
class EnhancedResumeData:
    personal_info: Dict[str, str]
    education: List[Dict[str, str]]
    experience: List[Dict[str, Any]]
    projects: List[Dict[str, Any]]
    skills: Dict[str, List[str]]
    original_latex: str
    identified_gaps: List[ExperienceGap] = field(default_factory=list)

class EnhancedDynamicResumeGenerator:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        logging.basicConfig(level=logging.INFO)

        # Skill categories for gap analysis
        self.skill_categories = {
            "cloud_platforms": SkillCategory(
                "Cloud Platforms",
                ["AWS", "Azure", "GCP", "Google Cloud", "Microsoft Azure", "Amazon Web Services"],
                2.0
            ),
            "containers": SkillCategory(
                "Containerization",
                ["Docker", "Kubernetes", "K8s", "Podman", "containerd", "OpenShift"],
                1.8
            ),
            "cicd": SkillCategory(
                "CI/CD Tools",
                ["Jenkins", "GitHub Actions", "GitLab CI", "CircleCI", "ArgoCD", "Tekton", "Spinnaker"],
                1.7
            ),
            "iac": SkillCategory(
                "Infrastructure as Code",
                ["Terraform", "CloudFormation", "Ansible", "Chef", "Puppet", "Pulumi"],
                1.6
            ),
            "monitoring": SkillCategory(
                "Monitoring & Observability",
                ["Prometheus", "Grafana", "DataDog", "New Relic", "Splunk", "ELK", "Jaeger"],
                1.5
            ),
            "programming": SkillCategory(
                "Programming Languages",
                ["Python", "Go", "Java", "JavaScript", "TypeScript", "C++", "Rust", "Scala"],
                1.4
            ),
            "databases": SkillCategory(
                "Databases",
                ["PostgreSQL", "MySQL", "MongoDB", "Redis", "Cassandra", "DynamoDB", "BigQuery"],
                1.3
            ),
            "security": SkillCategory(
                "Security Tools",
                ["Vault", "SIEM", "OWASP", "Snyk", "SonarQube", "Checkmarx", "Veracode"],
                1.2
            ),
            "web_frameworks": SkillCategory(
                "Web Frameworks",
                ["React", "Angular", "Vue.js", "Express", "Django", "Flask", "Spring"],
                1.1
            ),
            "testing": SkillCategory(
                "Testing Frameworks",
                ["Jest", "Selenium", "Cypress", "JUnit", "PyTest", "TestNG", "Cucumber"],
                1.0
            )
        }

        # Parse the provided LaTeX resume
        self.base_resume = self._parse_latex_resume()

    def _parse_latex_resume(self) -> EnhancedResumeData:
        """Parse the LaTeX resume into structured data"""

        latex_content = r"""
\documentclass[letterpaper,11pt]{article}

\usepackage{latexsym}
\usepackage[empty]{fullpage}
\usepackage{titlesec}
\usepackage{marvosym}
\usepackage[usenames,dvipsnames]{color}
\usepackage{verbatim}
\usepackage{enumitem}
\usepackage[pdftex]{hyperref}
\usepackage{fancyhdr}

\pagestyle{fancy}
\fancyhf{} % clear header/footer
\fancyfoot{}
\renewcommand{\headrulewidth}{0pt}
\renewcommand{\footrulewidth}{0pt}

% Adjust margins (sb2nov defaults)
\addtolength{\oddsidemargin}{-0.375in}
\addtolength{\evensidemargin}{-0.375in}
\addtolength{\textwidth}{1in}
\addtolength{\topmargin}{-.5in}
\addtolength{\textheight}{1.0in}

\urlstyle{same}
\raggedbottom
\raggedright
\setlength{\tabcolsep}{0in}
\setlength{\parindent}{0pt}

% Section formatting (sb2nov defaults, slightly tighter rule space)
\titleformat{\section}{
  \vspace{-4pt}\scshape\raggedright\large
}{}{0em}{}[\color{black}\titlerule \vspace{-6pt}]

% Tight lists
\newcommand{\resumeItem}[2]{\item\small{\textbf{#1}{: }#2}}
\newcommand{\resumeSubheading}[4]{%
  \vspace{-1pt}\item
    \begin{tabular*}{0.97\textwidth}{l@{\extracolsep{\fill}}r}
      \textbf{#1} & #2 \\
      \textit{\small #3} & \textit{\small #4} \\
    \end{tabular*}\vspace{-4pt}
}
\newcommand{\resumeSubItem}[2]{\resumeItem{#1}{#2}\vspace{-2pt}}
\renewcommand{\labelitemii}{$\circ$}

\newcommand{\resumeSubHeadingListStart}{\begin{itemize}[leftmargin=*, itemsep=1pt, topsep=2pt]}
\newcommand{\resumeSubHeadingListEnd}{\end{itemize}}
\newcommand{\resumeItemListStart}{\begin{itemize}[leftmargin=*, itemsep=1pt, topsep=1pt]}
\newcommand{\resumeItemListEnd}{\end{itemize}\vspace{-4pt}}

%-------------------------------------------
%%%%%%  CV STARTS HERE  %%%%%%%%%%%%%%%%%%%%

\begin{document}

%----------HEADING-----------------
\begin{tabular*}{\textwidth}{l@{\extracolsep{\fill}}r}
  \textbf{\Large Jiale Lin} & \href{mailto:jeremykalilin@gmail.com}{jeremykalilin@gmail.com}\\
  \href{https://ljluestc.github.io}{ljluestc.github.io} & +1-510-417-5834 \\
  \href{https://www.linkedin.com/in/jiale-lin-ab03a4149}{linkedin.com/in/jiale-lin} & U.S. Citizen \\
\end{tabular*}

%-----------EDUCATION-----------------
\section{Education}
  \resumeSubHeadingListStart
    \resumeSubheading
      {University of Colorado Boulder}{} % location omitted
      {Master of Science in Computer Science}{May 2025}
    \resumeSubheading
      {University of Arizona}{} % location omitted
      {Bachelor in Mathematics (CS Emphasis)}{May 2019}
  \resumeSubHeadingListEnd

%-----------EXPERIENCE-----------------
\section{Experience}
  \resumeSubHeadingListStart

    \resumeSubheading
      {Aviatrix}{Santa Clara, CA}
      {Senior Software Engineer (2024–Present) \,|\, Senior MTS (2023–2024) \,|\, MTS (2022–2023)}{May 2022 -- Present}
      \resumeItemListStart
        \resumeItem{Software Development}
          {Developed REST/gRPC services using Go, Python, Bash, Kafka; optimized service boundaries, caching, and concurrency for scalability and reliability.}
        \resumeItem{Infrastructure \& DevOps Automation}
          {Automated infrastructure with Terraform; operated Kubernetes across AWS, Azure, and GCP; built CI/CD with GitHub Actions, Jenkins, ArgoCD, and GitOps, reducing deployment time by \textbf{30\%}.}
        \resumeItem{Observability}
          {Enhanced monitoring with Prometheus, Grafana, and DataDog; added CI/CD health signals and SLOs; reduced MTTR by \textbf{15\%}.}
        \resumeItem{Security \& Networking}
          {Built secure multi-cloud automation with TLS and Zero-Trust; implemented eBPF/iptables validation for firewall upgrades and DDoS mitigation; hardened supply chain with SBOM and policy gates.}
      \resumeItemListEnd

    \resumeSubheading
      {Veeva Systems}{Pleasanton, CA}
      {Software Development Engineer in Test}{Aug 2021 -- May 2022}
      \resumeItemListStart
        \resumeItem{BDD Framework Development}
          {Implemented a cross-platform BDD framework using Kotlin, Cucumber, and Gradle; integrated with Jenkins CI to automate execution and expand coverage.}
        \resumeItem{UI Test Automation}
          {Automated web UI with Selenium and native iOS/Android with Appium; integrated suites into CI/CD with dashboards and flaky-test quarantine.}
        \resumeItem{Process Optimization}
          {Streamlined QA by refactoring suites and optimizing test cases, improving defect detection and reducing regression escapes.}
      \resumeItemListEnd

    \resumeSubheading
      {Google Fiber (via Adecco)}{Mountain View, CA}
      {Test Engineer}{Jun 2019 -- Jun 2021}
      \resumeItemListStart
        \resumeItem{Test Automation}
          {Developed a Page Object Model framework with Selenium/WebDriver (Java) for Angular apps, reducing test failures by \textbf{25\%}.}
        \resumeItem{Database Optimization}
          {Built BigQuery SQL objects (tables, views, macros, procedures), boosting query performance by \textbf{30\%}.}
        \resumeItem{Automation}
          {Automated tasks using Google Apps Script, Python, and Bash, saving \textbf{15 hrs/week}.}
        \resumeItem{Network Testing}
          {Performed CPE testing with Ixia Veriwave, improving network throughput by \textbf{20\%}.}
        \resumeItem{Infrastructure \& Monitoring}
          {Streamlined deployments with Docker and Kubernetes; implemented Prometheus/Grafana for real-time monitoring.}
      \resumeItemListEnd

  \resumeSubHeadingListEnd

%-----------PROJECTS (EXPANDED)-----------------
\section{Projects}
  \resumeSubHeadingListStart
    \resumeSubItem{AI-Powered Network Traffic Classifier \textnormal{(C++, Python, TF/ONNX, eBPF, gRPC, K8s)}}
      {Realtime packet/flow features via \textbf{eBPF}; ONNX model served over async gRPC on Kubernetes with rollout guards (\textit{shadow A/B}, drift detection, canary). Qt6/Electron dashboard with rate/latency charts; CI for model eval (AUC/PR), \texttt{onnxruntime} CPU/GPU.}
    \resumeSubItem{Graph-based Social Recommender \textnormal{(Python, Node2Vec, FAISS, MF, Airflow)}}
      {Graph ETL \(\rightarrow\) \textbf{Node2Vec} embeddings + matrix factorization; \textbf{FAISS} ANN for sub-ms top-$k$ retrieval; offline metrics (AUC, NDCG) and online CTR lift (double-digit). Deployed as \texttt{FastAPI} service with Redis cache; Airflow DAGs for retraining/backfills.}
    \resumeSubItem{Algorithm Visualization Tool \textnormal{(JavaFX, k-NN, Telemetry)}}
      {Interactive 2D collision/physics visualizer with toggleable \textbf{k-NN} "ML mode" vs. analytic solver; perf counters, frame timing, exportable traces — \href{https://ljluestc.github.io/visualgo/demo.html}{\textit{live demo}}.}
    \resumeSubItem{Multi-Protocol Router Sim \textnormal{(C++, FRR, BGP/OSPF/ISIS, Netem, CMake)}}
      {FRR control-plane integration; token-bucket/WFQ shaping; \texttt{tc}/netem impairments; gtest coverage and pcap diffing; CLI \& YAML scenarios for regression suites.}
  \resumeSubHeadingListEnd

\end{document}
"""

        # Extract personal info
        personal_info = {
            "name": "Jiale Lin",
            "email": "jeremykalilin@gmail.com",
            "phone": "+1-510-417-5834",
            "website": "ljluestc.github.io",
            "linkedin": "linkedin.com/in/jiale-lin-ab03a4149",
            "citizenship": "U.S. Citizen"
        }

        # Extract education
        education = [
            {
                "institution": "University of Colorado Boulder",
                "degree": "Master of Science in Computer Science",
                "graduation": "May 2025"
            },
            {
                "institution": "University of Arizona",
                "degree": "Bachelor in Mathematics (CS Emphasis)",
                "graduation": "May 2019"
            }
        ]

        # Extract experience
        experience = [
            {
                "company": "Aviatrix",
                "location": "Santa Clara, CA",
                "title": "Senior Software Engineer (2024–Present) | Senior MTS (2023–2024) | MTS (2022–2023)",
                "duration": "May 2022 -- Present",
                "achievements": [
                    "Developed REST/gRPC services using Go, Python, Bash, Kafka; optimized service boundaries, caching, and concurrency for scalability and reliability.",
                    "Automated infrastructure with Terraform; operated Kubernetes across AWS, Azure, and GCP; built CI/CD with GitHub Actions, Jenkins, ArgoCD, and GitOps, reducing deployment time by 30%.",
                    "Enhanced monitoring with Prometheus, Grafana, and DataDog; added CI/CD health signals and SLOs; reduced MTTR by 15%.",
                    "Built secure multi-cloud automation with TLS and Zero-Trust; implemented eBPF/iptables validation for firewall upgrades and DDoS mitigation; hardened supply chain with SBOM and policy gates."
                ],
                "current": True
            },
            {
                "company": "Veeva Systems",
                "location": "Pleasanton, CA",
                "title": "Software Development Engineer in Test",
                "duration": "Aug 2021 -- May 2022",
                "achievements": [
                    "Implemented a cross-platform BDD framework using Kotlin, Cucumber, and Gradle; integrated with Jenkins CI to automate execution and expand coverage.",
                    "Automated web UI with Selenium and native iOS/Android with Appium; integrated suites into CI/CD with dashboards and flaky-test quarantine.",
                    "Streamlined QA by refactoring suites and optimizing test cases, improving defect detection and reducing regression escapes."
                ],
                "current": False
            },
            {
                "company": "Google Fiber (via Adecco)",
                "location": "Mountain View, CA",
                "title": "Test Engineer",
                "duration": "Jun 2019 -- Jun 2021",
                "achievements": [
                    "Developed a Page Object Model framework with Selenium/WebDriver (Java) for Angular apps, reducing test failures by 25%.",
                    "Built BigQuery SQL objects (tables, views, macros, procedures), boosting query performance by 30%.",
                    "Automated tasks using Google Apps Script, Python, and Bash, saving 15 hrs/week.",
                    "Performed CPE testing with Ixia Veriwave, improving network throughput by 20%.",
                    "Streamlined deployments with Docker and Kubernetes; implemented Prometheus/Grafana for real-time monitoring."
                ],
                "current": False
            }
        ]

        # Extract projects
        projects = [
            {
                "name": "AI-Powered Network Traffic Classifier",
                "technologies": ["C++", "Python", "TF/ONNX", "eBPF", "gRPC", "K8s"],
                "description": "Realtime packet/flow features via eBPF; ONNX model served over async gRPC on Kubernetes with rollout guards (shadow A/B, drift detection, canary). Qt6/Electron dashboard with rate/latency charts; CI for model eval (AUC/PR), onnxruntime CPU/GPU."
            },
            {
                "name": "Graph-based Social Recommender",
                "technologies": ["Python", "Node2Vec", "FAISS", "MF", "Airflow"],
                "description": "Graph ETL → Node2Vec embeddings + matrix factorization; FAISS ANN for sub-ms top-k retrieval; offline metrics (AUC, NDCG) and online CTR lift (double-digit). Deployed as FastAPI service with Redis cache; Airflow DAGs for retraining/backfills."
            },
            {
                "name": "Algorithm Visualization Tool",
                "technologies": ["JavaFX", "k-NN", "Telemetry"],
                "description": "Interactive 2D collision/physics visualizer with toggleable k-NN 'ML mode' vs. analytic solver; perf counters, frame timing, exportable traces."
            },
            {
                "name": "Multi-Protocol Router Sim",
                "technologies": ["C++", "FRR", "BGP/OSPF/ISIS", "Netem", "CMake"],
                "description": "FRR control-plane integration; token-bucket/WFQ shaping; tc/netem impairments; gtest coverage and pcap diffing; CLI & YAML scenarios for regression suites."
            }
        ]

        # Extract skills from content
        skills = self._extract_skills_from_content(latex_content)

        return EnhancedResumeData(
            personal_info=personal_info,
            education=education,
            experience=experience,
            projects=projects,
            skills=skills,
            original_latex=latex_content
        )

    def _extract_skills_from_content(self, content: str) -> Dict[str, List[str]]:
        """Extract skills from the resume content"""

        # Extract all technologies mentioned
        all_tech = set()

        # Common patterns for technologies
        tech_patterns = [
            r'\b(Go|Python|Java|JavaScript|TypeScript|C\+\+|Rust|Scala|Kotlin)\b',
            r'\b(AWS|Azure|GCP|Google Cloud)\b',
            r'\b(Kubernetes|Docker|K8s)\b',
            r'\b(Jenkins|GitHub Actions|GitLab CI|ArgoCD)\b',
            r'\b(Terraform|Ansible|Chef|Puppet)\b',
            r'\b(Prometheus|Grafana|DataDog|New Relic)\b',
            r'\b(PostgreSQL|MySQL|MongoDB|Redis|BigQuery)\b',
            r'\b(React|Angular|Vue\.js|Express|Django|Flask)\b',
            r'\b(Selenium|Cypress|Jest|JUnit|PyTest)\b'
        ]

        for pattern in tech_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            all_tech.update(matches)

        # Categorize skills
        skills = {
            "Programming Languages": ["Go", "Python", "Java", "JavaScript", "C++", "Bash"],
            "Cloud Platforms": ["AWS", "Azure", "GCP"],
            "Infrastructure": ["Kubernetes", "Docker", "Terraform"],
            "CI/CD": ["GitHub Actions", "Jenkins", "ArgoCD", "GitOps"],
            "Monitoring": ["Prometheus", "Grafana", "DataDog"],
            "Databases": ["BigQuery", "Redis"],
            "Testing": ["Selenium", "Appium", "Cucumber"],
            "Networking": ["eBPF", "iptables", "gRPC", "REST"],
            "Security": ["TLS", "Zero-Trust", "SBOM", "DDoS mitigation"],
            "Machine Learning": ["TensorFlow", "ONNX", "Node2Vec", "FAISS"]
        }

        return skills

    def analyze_job_requirements(self, job_description: str) -> Dict[str, Any]:
        """Enhanced job analysis with more detailed requirement extraction"""

        requirements = {
            "required_skills": [],
            "preferred_skills": [],
            "technologies": [],
            "experience_level": "",
            "domain_focus": [],
            "certifications": [],
            "missing_skills": [],
            "skill_gaps": {}
        }

        # Extract technologies with context
        for category_name, category in self.skill_categories.items():
            found_skills = []
            for keyword in category.keywords:
                if re.search(rf'\b{re.escape(keyword)}\b', job_description, re.IGNORECASE):
                    found_skills.append(keyword)
                    requirements["technologies"].append(keyword)

            if found_skills:
                requirements["domain_focus"].append(category_name)
                requirements["skill_gaps"][category_name] = {
                    "found": found_skills,
                    "weight": category.weight
                }

        # Extract experience level with more precision
        exp_patterns = [
            (r'(\d+)\+?\s*years?\s*(?:of\s*)?experience', lambda m: f"{m.group(1)}+ years"),
            (r'senior|lead|principal', lambda m: "senior"),
            (r'junior|entry.level|graduate', lambda m: "junior"),
            (r'mid.level|intermediate', lambda m: "mid-level")
        ]

        for pattern, extractor in exp_patterns:
            match = re.search(pattern, job_description, re.IGNORECASE)
            if match:
                requirements["experience_level"] = extractor(match)
                break

        # Extract certifications
        cert_patterns = [
            r'\b(AWS\s+Certified|Azure\s+Certified|GCP\s+Certified)\b',
            r'\b(CISSP|CISM|CEH|Security\+)\b',
            r'\b(CKA|CKAD|CKS)\b'  # Kubernetes certifications
        ]

        for pattern in cert_patterns:
            matches = re.findall(pattern, job_description, re.IGNORECASE)
            requirements["certifications"].extend(matches)

        return requirements

    def identify_skill_gaps(self, job_requirements: Dict[str, Any]) -> List[ExperienceGap]:
        """Identify gaps between current skills and job requirements"""

        gaps = []
        current_skills = set()

        # Flatten current skills
        for skill_list in self.base_resume.skills.values():
            current_skills.update([skill.lower() for skill in skill_list])

        # Check each skill category
        for category_name, gap_info in job_requirements.get("skill_gaps", {}).items():
            category = self.skill_categories[category_name]
            found_skills = gap_info["found"]

            # Find missing skills in this category
            missing_skills = []
            for keyword in category.keywords:
                if keyword.lower() not in current_skills and keyword not in found_skills:
                    missing_skills.append(keyword)

            if missing_skills:
                # Generate suggested addition
                suggested_addition = self._generate_skill_addition(category_name, missing_skills)

                gap = ExperienceGap(
                    category=category_name,
                    missing_skills=missing_skills[:3],  # Top 3 missing
                    suggested_addition=suggested_addition,
                    relevance_score=gap_info["weight"]
                )
                gaps.append(gap)

        # Sort by relevance score
        gaps.sort(key=lambda x: x.relevance_score, reverse=True)
        return gaps

    def _generate_skill_addition(self, category: str, missing_skills: List[str]) -> str:
        """Generate a realistic experience addition for missing skills"""

        skill_additions = {
            "cloud_platforms": {
                "AWS": "Architected and deployed scalable solutions on AWS using EC2, S3, RDS, and Lambda; implemented cost optimization strategies reducing infrastructure spend by 25%.",
                "Azure": "Designed multi-region Azure infrastructure with AKS, Storage Accounts, and Azure SQL; integrated with Azure DevOps for automated deployments.",
                "GCP": "Built data processing pipelines on Google Cloud using Compute Engine, Cloud Storage, and BigQuery; optimized for high availability and cost efficiency."
            },
            "containers": {
                "Docker": "Containerized applications using Docker with multi-stage builds; created optimized images reducing size by 40% and improving deployment speed.",
                "OpenShift": "Deployed and managed applications on OpenShift platform; implemented GitOps workflows and automated scaling policies."
            },
            "cicd": {
                "GitLab CI": "Designed and implemented GitLab CI/CD pipelines with automated testing, security scanning, and deployment to multiple environments.",
                "CircleCI": "Built efficient CircleCI workflows with parallel testing and deployment strategies; reduced build times by 35%."
            },
            "iac": {
                "CloudFormation": "Developed AWS CloudFormation templates for infrastructure provisioning; implemented nested stacks and cross-stack references for modular architecture.",
                "Ansible": "Automated server configuration and application deployment using Ansible playbooks; managed infrastructure across 100+ servers.",
                "Pulumi": "Implemented infrastructure as code using Pulumi with Python; enabled rapid environment provisioning and consistent deployments."
            },
            "monitoring": {
                "New Relic": "Implemented comprehensive application monitoring with New Relic APM; created custom dashboards and alerting reducing MTTR by 20%.",
                "Splunk": "Designed log aggregation and analysis pipelines using Splunk; built custom searches and dashboards for operational insights.",
                "ELK": "Deployed Elasticsearch, Logstash, and Kibana stack for centralized logging; processed 10TB+ of log data daily with real-time alerting."
            },
            "databases": {
                "MongoDB": "Designed and optimized MongoDB databases for high-volume applications; implemented sharding and replica sets for scalability.",
                "Cassandra": "Built distributed NoSQL solutions using Apache Cassandra; optimized for high availability and eventual consistency requirements.",
                "DynamoDB": "Architected serverless applications with DynamoDB; implemented efficient data modeling and query patterns for sub-millisecond response times."
            },
            "security": {
                "Vault": "Implemented HashiCorp Vault for secrets management; automated certificate rotation and secure credential distribution across microservices.",
                "SIEM": "Deployed SIEM solutions for security event monitoring; created correlation rules and automated incident response workflows.",
                "OWASP": "Conducted security assessments following OWASP guidelines; implemented secure coding practices and vulnerability remediation."
            },
            "web_frameworks": {
                "React": "Built responsive web applications using React with hooks and context API; implemented efficient state management and component optimization.",
                "Angular": "Developed enterprise-scale applications with Angular; created reusable components and implemented lazy loading for performance.",
                "Django": "Built robust backend APIs using Django REST framework; implemented authentication, caching, and database optimization."
            },
            "testing": {
                "Jest": "Implemented comprehensive unit and integration testing with Jest; achieved 90%+ code coverage and automated test execution.",
                "Cypress": "Developed end-to-end testing suites using Cypress; automated browser testing across multiple environments and browsers.",
                "PyTest": "Created extensive Python test suites using PyTest; implemented fixtures, mocking, and parallel test execution."
            }
        }

        # Get the first missing skill and return its addition
        if missing_skills and category in skill_additions:
            first_skill = missing_skills[0]
            if first_skill in skill_additions[category]:
                return skill_additions[category][first_skill]

        # Fallback generic addition
        return f"Gained experience with {', '.join(missing_skills[:2])} through personal projects and continuous learning initiatives."

    def enhance_resume_with_gaps(self, job_requirements: Dict[str, Any], max_additions: int = 2) -> str:
        """Generate enhanced resume with strategically added missing skills"""

        # Identify skill gaps
        gaps = self.identify_skill_gaps(job_requirements)

        # Select top gaps to address
        selected_gaps = gaps[:max_additions]

        # Start with base resume structure
        enhanced_latex = self.base_resume.original_latex

        # Add gap-filling content to the most recent experience
        if selected_gaps:
            gap_additions = []
            for gap in selected_gaps:
                gap_additions.append(f"\\resumeItem{{{gap.category.replace('_', ' ').title()}}}\n          {{{gap.suggested_addition}}}")

            # Find the first resumeItemListEnd and insert before it
            pattern = r'(\\resumeItemListStart.*?)(\\resumeItemListEnd)'

            def replace_first_experience(match):
                existing_items = match.group(1)
                end_tag = match.group(2)

                # Add new items
                new_items = '\n        '.join(gap_additions)
                return f"{existing_items}\n        {new_items}\n      {end_tag}"

            enhanced_latex = re.sub(pattern, replace_first_experience, enhanced_latex, count=1, flags=re.DOTALL)

        # Store the gaps for reference
        self.base_resume.identified_gaps = selected_gaps

        return enhanced_latex

    def generate_enhanced_resume(self, job_title: str, company: str, job_description: str) -> Dict[str, Any]:
        """Generate a comprehensive enhanced resume with gap analysis"""

        # Analyze job requirements
        job_requirements = self.analyze_job_requirements(job_description)

        # Generate enhanced resume with missing skills
        enhanced_latex = self.enhance_resume_with_gaps(job_requirements, max_additions=2)

        # Generate cover letter highlighting additions
        cover_letter = self.generate_enhanced_cover_letter(job_title, company, job_requirements)

        # Create gap analysis report
        gap_report = self.create_gap_analysis_report(job_requirements)

        return {
            "enhanced_resume": enhanced_latex,
            "cover_letter": cover_letter,
            "gap_analysis": gap_report,
            "job_requirements": job_requirements,
            "identified_gaps": [
                {
                    "category": gap.category,
                    "missing_skills": gap.missing_skills,
                    "addition": gap.suggested_addition,
                    "relevance": gap.relevance_score
                } for gap in self.base_resume.identified_gaps
            ]
        }

    def generate_enhanced_cover_letter(self, job_title: str, company: str, job_requirements: Dict[str, Any]) -> str:
        """Generate cover letter that subtly mentions the enhanced skills"""

        cover_letter = f"""Dear {company} Hiring Team,

I am writing to express my strong interest in the {job_title} position at {company}. With my comprehensive background as a Senior Software Engineer at Aviatrix and my continuous pursuit of cutting-edge technologies, I am excited about the opportunity to contribute to {company}'s innovative solutions.

My experience spans the full spectrum of modern software development and infrastructure management. At Aviatrix, I have consistently delivered scalable solutions while staying current with emerging technologies and industry best practices.

Key highlights that align with your requirements:

"""

        # Add relevant experience highlights
        relevant_skills = job_requirements.get("technologies", [])[:3]
        if relevant_skills:
            cover_letter += f"• Extensive experience with {', '.join(relevant_skills)} in production environments\n"

        cover_letter += """• Proven track record of reducing deployment times by 30% and system downtime by 15%
• Strong foundation in cloud infrastructure, DevOps automation, and security best practices
• Continuous learning mindset with hands-on experience in emerging technologies

"""

        # Mention any gap-filling additions subtly
        if self.base_resume.identified_gaps:
            cover_letter += f"I have also been expanding my expertise in areas such as {self.base_resume.identified_gaps[0].category.replace('_', ' ')} "
            cover_letter += "through personal projects and professional development initiatives.\n\n"

        cover_letter += f"""I am particularly drawn to {company}'s commitment to innovation and technical excellence. I would welcome the opportunity to discuss how my skills and passion for technology can contribute to your team's continued success.

Thank you for your consideration. I look forward to hearing from you.

Best regards,
Jiale Lin
jeremykalilin@gmail.com
+1-510-417-5834"""

        return cover_letter

    def create_gap_analysis_report(self, job_requirements: Dict[str, Any]) -> Dict[str, Any]:
        """Create a detailed gap analysis report"""

        current_skills = set()
        for skill_list in self.base_resume.skills.values():
            current_skills.update([skill.lower() for skill in skill_list])

        required_skills = set([skill.lower() for skill in job_requirements.get("technologies", [])])

        matched_skills = current_skills.intersection(required_skills)
        missing_skills = required_skills - current_skills

        return {
            "total_required_skills": len(required_skills),
            "matched_skills": len(matched_skills),
            "missing_skills": len(missing_skills),
            "match_percentage": round((len(matched_skills) / len(required_skills)) * 100, 1) if required_skills else 0,
            "matched_skill_list": list(matched_skills),
            "missing_skill_list": list(missing_skills),
            "recommendations": [gap.suggested_addition for gap in self.base_resume.identified_gaps[:3]]
        }

def main():
    """Test the enhanced system"""
    generator = EnhancedDynamicResumeGenerator()

    # Test with a comprehensive job description
    test_job_description = """
    Senior DevOps Engineer - Cloud Infrastructure

    We are seeking a Senior DevOps Engineer with 5+ years of experience to join our Cloud Infrastructure team.

    Required Skills:
    - Strong experience with AWS, Azure, and GCP cloud platforms
    - Expertise in Kubernetes, Docker, and container orchestration
    - Infrastructure as Code with Terraform and CloudFormation
    - CI/CD pipeline development (Jenkins, GitLab CI, CircleCI)
    - Monitoring and observability (Prometheus, Grafana, New Relic, Splunk)
    - Programming skills in Python, Go, and shell scripting
    - Database management (PostgreSQL, MongoDB, DynamoDB)
    - Security tools and practices (Vault, SIEM, OWASP)

    Preferred:
    - Experience with service mesh technologies (Istio, Linkerd)
    - Knowledge of serverless architectures
    - Agile/Scrum methodology experience
    - AWS/Azure/GCP certifications

    We offer competitive salary, comprehensive benefits, and opportunities for professional growth.
    """

    print("🚀 Enhanced Dynamic Resume Generator - Testing")
    print("=" * 60)

    result = generator.generate_enhanced_resume(
        "Senior DevOps Engineer - Cloud Infrastructure",
        "Nemetschek",
        test_job_description
    )

    print("📊 Gap Analysis Results:")
    gap_analysis = result["gap_analysis"]
    print(f"  Skill Match: {gap_analysis['match_percentage']}% ({gap_analysis['matched_skills']}/{gap_analysis['total_required_skills']})")
    print(f"  Matched Skills: {', '.join(gap_analysis['matched_skill_list'][:5])}")
    print(f"  Missing Skills: {', '.join(gap_analysis['missing_skill_list'][:5])}")

    print(f"\n🔧 Identified Gaps:")
    for i, gap in enumerate(result["identified_gaps"][:2], 1):
        print(f"  {i}. {gap['category'].replace('_', ' ').title()}")
        print(f"     Missing: {', '.join(gap['missing_skills'])}")
        print(f"     Relevance: {gap['relevance']}")

    # Save enhanced resume
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    resume_file = f"Enhanced_Resume_Nemetschek_DevOps_{timestamp}.tex"
    cover_file = f"Enhanced_Cover_Letter_Nemetschek_DevOps_{timestamp}.txt"

    with open(resume_file, 'w', encoding='utf-8') as f:
        f.write(result["enhanced_resume"])

    with open(cover_file, 'w', encoding='utf-8') as f:
        f.write(result["cover_letter"])

    print(f"\n✅ Generated Files:")
    print(f"  Enhanced Resume: {resume_file}")
    print(f"  Cover Letter: {cover_file}")

    return result

if __name__ == "__main__":
    main()