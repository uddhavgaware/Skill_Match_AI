"""
SkillMatch AI - Skill Taxonomy & Ontology
Comprehensive dictionary of skills, canonical normalizations, domain categorization,
and competency pillar calculations for student-job alignment.
"""

from typing import Dict, List, Set

# Canonical skills grouped by core domains
TAXONOMY: Dict[str, List[str]] = {
    "Languages": [
        "Python", "JavaScript", "TypeScript", "Java", "C++", "C", "C#", "Go", "Rust",
        "Kotlin", "Swift", "PHP", "Ruby", "Scala", "R", "Dart", "SQL", "Bash", "Shell",
        "HTML", "CSS", "Solidity", "MATLAB", "Julia", "Perl", "Haskell"
    ],
    "AI & Machine Learning": [
        "Machine Learning", "Deep Learning", "Natural Language Processing", "Computer Vision",
        "Large Language Models", "Generative AI", "PyTorch", "TensorFlow", "Keras",
        "Scikit-Learn", "Hugging Face", "Transformers", "LangChain", "LlamaIndex",
        "Reinforcement Learning", "OpenCV", "MediaPipe", "NLTK", "SpaCy", "YOLO",
        "Vector Databases", "ChromaDB", "Pinecone", "Milvus", "Prompt Engineering",
        "Model Fine-Tuning", "LoRA", "RAG", "MLflow", "Weights & Biases", "ONNX", "vLLM"
    ],
    "Data & Analytics": [
        "Data Analysis", "Data Science", "Pandas", "NumPy", "SciPy", "Polars",
        "Data Engineering", "Apache Spark", "PySpark", "Apache Kafka", "Airflow",
        "Hadoop", "ETL Pipelines", "Data Warehousing", "Snowflake", "BigQuery",
        "Databricks", "Tableau", "Power BI", "Data Visualization", "Matplotlib",
        "Seaborn", "Plotly", "Statistical Modeling", "A/B Testing", "Time Series Analysis"
    ],
    "Web & Fullstack": [
        "React", "Next.js", "Vue.js", "Nuxt.js", "Angular", "Svelte", "Node.js",
        "Express.js", "NestJS", "FastAPI", "Django", "Flask", "Spring Boot", "ASP.NET",
        "GraphQL", "REST APIs", "Tailwind CSS", "Bootstrap", "Redux", "Zustand",
        "WebSockets", "Microservices", "Serverless", "Prisma", "Drizzle ORM",
        "WebAssembly", "OAuth", "JWT", "PWA", "Responsive Web Design"
    ],
    "Cloud & DevOps": [
        "AWS", "Amazon Web Services", "Google Cloud Platform", "GCP", "Microsoft Azure",
        "Docker", "Kubernetes", "CI/CD", "GitHub Actions", "GitLab CI", "Terraform",
        "Ansible", "Linux", "System Administration", "Nginx", "Monitoring", "Prometheus",
        "Grafana", "Cloudflare", "Serverless Architecture", "Helm", "Infrastructure as Code"
    ],
    "Databases": [
        "PostgreSQL", "MySQL", "MongoDB", "Redis", "SQLite", "DynamoDB", "Cassandra",
        "Neo4j", "Elasticsearch", "Supabase", "Firebase", "Firestore", "SQLAlchemy",
        "Database Design", "Query Optimization", "NoSQL", "Relational Databases"
    ],
    "Systems & Core CS": [
        "Data Structures", "Algorithms", "Object-Oriented Programming", "System Design",
        "Operating Systems", "Computer Networks", "Distributed Systems", "Concurrency",
        "Multithreading", "Memory Management", "Git", "GitHub", "Version Control",
        "Design Patterns", "Unit Testing", "Debugging", "Low-Level Programming"
    ],
    "Cybersecurity": [
        "Cybersecurity", "Network Security", "Penetration Testing", "Ethical Hacking",
        "Cryptography", "Vulnerability Assessment", "Wireshark", "OWASP", "SIEM",
        "Identity Management", "Firewalls", "Incident Response", "Burp Suite"
    ],
    "Mobile Development": [
        "Flutter", "React Native", "Android Development", "iOS Development", "SwiftUI",
        "Jetpack Compose", "Mobile UI", "Cross-Platform Development"
    ],
    "UI/UX & Product": [
        "UI/UX Design", "Figma", "User Research", "Wireframing", "Prototyping",
        "Design Systems", "Usability Testing", "Product Management", "Agile", "Scrum",
        "Information Architecture", "Interaction Design"
    ],
    "Soft Skills & Methodologies": [
        "Agile Methodology", "Scrum", "Team Collaboration", "Problem Solving",
        "Technical Writing", "Code Review", "Critical Thinking", "Communication",
        "Project Management", "Time Management", "Leadership"
    ]
}

# Alias / Synonym lookup mapping raw string -> canonical skill name
ALIASES: Dict[str, str] = {
    # Languages
    "py": "Python", "python3": "Python",
    "js": "JavaScript", "javascript": "JavaScript", "es6": "JavaScript", "ecmascript": "JavaScript",
    "ts": "TypeScript", "typescript": "TypeScript",
    "golang": "Go", "go lang": "Go",
    "cpp": "C++", "c plus plus": "C++",
    "csharp": "C#", "c-sharp": "C#",
    "sh": "Shell", "bash scripting": "Bash",
    "postgres": "PostgreSQL", "psql": "PostgreSQL", "postgresql": "PostgreSQL",
    "mongo": "MongoDB", "mongodb": "MongoDB",

    # AI & ML
    "ml": "Machine Learning", "machine learning": "Machine Learning",
    "dl": "Deep Learning", "deep learning": "Deep Learning",
    "nlp": "Natural Language Processing", "natural language processing": "Natural Language Processing",
    "cv": "Computer Vision", "computer vision": "Computer Vision",
    "llm": "Large Language Models", "llms": "Large Language Models", "large language model": "Large Language Models",
    "genai": "Generative AI", "gen ai": "Generative AI", "generative ai": "Generative AI",
    "pytorch": "PyTorch", "torch": "PyTorch",
    "tf": "TensorFlow", "tensorflow": "TensorFlow",
    "sklearn": "Scikit-Learn", "scikit": "Scikit-Learn", "scikit-learn": "Scikit-Learn",
    "hf": "Hugging Face", "huggingface": "Hugging Face",
    "rag": "RAG", "retrieval augmented generation": "RAG", "retrieval-augmented generation": "RAG",
    "prompt engineering": "Prompt Engineering",
    "fine-tuning": "Model Fine-Tuning", "finetuning": "Model Fine-Tuning",

    # Web & Fullstack
    "reactjs": "React", "react.js": "React", "react": "React",
    "nextjs": "Next.js", "next.js": "Next.js", "next": "Next.js",
    "vue": "Vue.js", "vuejs": "Vue.js", "vue.js": "Vue.js",
    "nodejs": "Node.js", "node.js": "Node.js", "node": "Node.js",
    "express": "Express.js", "expressjs": "Express.js",
    "fastapi": "FastAPI", "fast api": "FastAPI",
    "django": "Django", "flask": "Flask",
    "tailwind": "Tailwind CSS", "tailwindcss": "Tailwind CSS",
    "rest": "REST APIs", "rest api": "REST APIs", "restful api": "REST APIs", "restful": "REST APIs",
    "graphql": "GraphQL",
    "fullstack": "Web & Fullstack", "full-stack": "Web & Fullstack",

    # Cloud & DevOps
    "aws": "AWS", "amazon web services": "AWS",
    "gcp": "Google Cloud Platform", "google cloud": "Google Cloud Platform",
    "azure": "Microsoft Azure", "ms azure": "Microsoft Azure",
    "k8s": "Kubernetes", "kubernetes": "Kubernetes",
    "docker": "Docker", "containerization": "Docker",
    "cicd": "CI/CD", "ci/cd": "CI/CD", "continuous integration": "CI/CD",
    "terraform": "Terraform", "iac": "Terraform",
    "github actions": "GitHub Actions", "git actions": "GitHub Actions",

    # Data
    "eda": "Data Analysis", "data analytics": "Data Analysis",
    "spark": "Apache Spark", "pyspark": "PySpark",
    "kafka": "Apache Kafka", "airflow": "Airflow",
    "tableau": "Tableau", "power bi": "Power BI", "powerbi": "Power BI",

    # Core CS & Tools
    "dsa": "Data Structures", "data structures and algorithms": "Data Structures",
    "algo": "Algorithms", "algorithms": "Algorithms",
    "oop": "Object-Oriented Programming", "oops": "Object-Oriented Programming",
    "system design": "System Design", "sys design": "System Design",
    "git": "Git", "github": "GitHub",

    # Design
    "ux": "UI/UX Design", "ui/ux": "UI/UX Design", "ui design": "UI/UX Design", "ux design": "UI/UX Design",
    "figma": "Figma"
}

# Invert / build lowercase lookup for canonical names
CANONICAL_LOOKUP: Dict[str, str] = {}
for category, skills in TAXONOMY.items():
    for s in skills:
        CANONICAL_LOOKUP[s.lower()] = s

for alias, canon in ALIASES.items():
    CANONICAL_LOOKUP[alias.lower()] = canon

# Mapping from Skill Category to 6 Main Radar Pillars
PILLAR_MAPPING: Dict[str, List[str]] = {
    "AI & ML": ["AI & Machine Learning"],
    "Fullstack": ["Web & Fullstack", "Mobile Development"],
    "Data & Analytics": ["Data & Analytics", "Databases"],
    "Cloud & DevOps": ["Cloud & DevOps"],
    "Systems & CS": ["Systems & Core CS", "Cybersecurity"],
    "Product & Design": ["UI/UX & Product", "Soft Skills & Methodologies"]
}


def normalize_skill(skill_text: str) -> str:
    """Returns canonical formatted skill name or title-cased string."""
    cleaned = skill_text.strip().lower()
    if cleaned in CANONICAL_LOOKUP:
        return CANONICAL_LOOKUP[cleaned]
    # Check without punctuation
    no_punc = cleaned.replace("-", " ").replace(".", "")
    if no_punc in CANONICAL_LOOKUP:
        return CANONICAL_LOOKUP[no_punc]
    return skill_text.strip().title()


def get_skill_category(skill: str) -> str:
    """Returns the primary taxonomy category for a skill."""
    canon = normalize_skill(skill)
    for cat, skills in TAXONOMY.items():
        if canon in skills:
            return cat
    return "Other Technical"


def compute_skill_pillars(skills: List[str]) -> Dict[str, float]:
    """
    Computes competency radar percentages (0-100%) across 6 main pillars
    based on the student's cataloged skills.
    """
    normalized_skills = {normalize_skill(s) for s in skills}
    
    # Counts per category
    cat_counts: Dict[str, int] = {cat: 0 for cat in TAXONOMY}
    for s in normalized_skills:
        for cat, cat_skills in TAXONOMY.items():
            if s in cat_skills:
                cat_counts[cat] += 1
                break

    # Calculate 6 pillar scores with calibrated curve
    # 1 skill = 35%, 2 skills = 55%, 3 skills = 70%, 4 skills = 85%, 5+ skills = 95-100%
    pillar_scores: Dict[str, float] = {}
    for pillar, mapped_cats in PILLAR_MAPPING.items():
        total_skills_in_pillar = sum(cat_counts.get(c, 0) for c in mapped_cats)
        if total_skills_in_pillar == 0:
            score = 15.0  # Baseline baseline interest
        elif total_skills_in_pillar == 1:
            score = 42.0
        elif total_skills_in_pillar == 2:
            score = 64.0
        elif total_skills_in_pillar == 3:
            score = 78.0
        elif total_skills_in_pillar == 4:
            score = 88.0
        else:
            score = min(98.0, 88.0 + (total_skills_in_pillar - 4) * 3.0)
        pillar_scores[pillar] = round(score, 1)

    return pillar_scores


def get_all_skills_flat() -> List[str]:
    """Returns all unique canonical skills across all domains."""
    all_skills: Set[str] = set()
    for skills in TAXONOMY.values():
        all_skills.update(skills)
    return sorted(list(all_skills))
