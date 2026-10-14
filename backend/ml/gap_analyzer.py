"""
SkillMatch AI - Skill Gap Analyzer & Personalized Learning Pathway Engine
Analyzes missing competencies between student profile and target role,
provides curated learning recommendations, and runs What-If score simulations.
"""

from typing import Any, Dict, List, Optional
from backend.ml.taxonomy import normalize_skill

# Curated repository of learning pathways for key industry skills
SKILL_LEARNING_RESOURCES: Dict[str, Dict[str, Any]] = {
    "Docker": {
        "resource": "Docker for Developers & Containerization Masterclass",
        "platform": "freeCodeCamp & Docker Official Docs",
        "type": "Interactive / Hands-on",
        "estimated_hours": "12-16 hours",
        "difficulty": "Intermediate",
        "key_concepts": ["Dockerfiles", "Multi-stage builds", "Docker Compose", "Volume mounts", "Network bridges"],
        "recommended_project": "Containerize a fullstack app with frontend, backend, and PostgreSQL database with healthchecks."
    },
    "Kubernetes": {
        "resource": "Kubernetes the Hard Way & CKA Essentials",
        "platform": "Kelsey Hightower / Linux Foundation",
        "type": "Hands-on Workshop",
        "estimated_hours": "25-30 hours",
        "difficulty": "Advanced",
        "key_concepts": ["Pods & Deployments", "Services & Ingress", "ConfigMaps & Secrets", "Horizontal Pod Autoscaling", "Helm charts"],
        "recommended_project": "Deploy a microservice cluster on local Minikube with Ingress routing and automatic replica scaling."
    },
    "Transformers": {
        "resource": "Hugging Face NLP Course (Free Interactive)",
        "platform": "Hugging Face",
        "type": "Interactive Code Labs",
        "estimated_hours": "20-25 hours",
        "difficulty": "Advanced",
        "key_concepts": ["Self-Attention mechanism", "BERT vs GPT architectures", "Fine-tuning with Trainer API", "Tokenizers", "LoRA / PEFT"],
        "recommended_project": "Fine-tune a lightweight Llama or RoBERTa model on domain-specific question answering with Hugging Face Trainer."
    },
    "PyTorch": {
        "resource": "PyTorch for Deep Learning Bootcamp",
        "platform": "PyTorch.org Tutorials & Daniel Bourke",
        "type": "Video & Code Notebooks",
        "estimated_hours": "30-40 hours",
        "difficulty": "Intermediate",
        "key_concepts": ["Tensors & Autograd", "Custom nn.Module layers", "Dataset & DataLoader", "Training loops & Backpropagation", "GPU acceleration"],
        "recommended_project": "Train a convolutional neural network on custom image dataset achieving >85% validation accuracy."
    },
    "PostgreSQL": {
        "resource": "PostgreSQL High Performance & Schema Design",
        "platform": "Postgres Guide & SQLBolt",
        "type": "Interactive SQL Practice",
        "estimated_hours": "10-14 hours",
        "difficulty": "Intermediate",
        "key_concepts": ["Relational normalization", "B-tree vs GIN indexes", "Transactions & ACID", "Window functions & CTEs", "Explain Analyze profiling"],
        "recommended_project": "Build an e-commerce database with complex analytical aggregation queries and optimized indexing."
    },
    "FastAPI": {
        "resource": "FastAPI Modern Python Web APIs Tutorial",
        "platform": "tiangolo FastAPI Docs & Real Python",
        "type": "Documentation & Labs",
        "estimated_hours": "10-15 hours",
        "difficulty": "Beginner to Intermediate",
        "key_concepts": ["Type hints & Pydantic validation", "Async def endpoints", "Dependency Injection", "JWT Authentication", "OpenAPI docs"],
        "recommended_project": "Build an asynchronous CRUD REST API with JWT authentication and automated OpenAPI documentation."
    },
    "TypeScript": {
        "resource": "TypeScript for JavaScript Developers",
        "platform": "TypeScript Official Handbook & ExecuteProgram",
        "type": "Interactive Coding",
        "estimated_hours": "15-20 hours",
        "difficulty": "Intermediate",
        "key_concepts": ["Generics", "Union & Intersection types", "Utility types", "Strict null checks", "Type narrowing"],
        "recommended_project": "Refactor an existing JavaScript React app into 100% strict-mode TypeScript with custom generic hooks."
    },
    "Next.js": {
        "resource": "Next.js App Router Masterclass",
        "platform": "Next.js Learn (Vercel)",
        "type": "Interactive Documentation",
        "estimated_hours": "15-18 hours",
        "difficulty": "Intermediate",
        "key_concepts": ["App Router", "Server vs Client Components", "Server Actions", "Streaming & Suspense", "Static & Dynamic Rendering"],
        "recommended_project": "Create a high-performance content platform with Server Actions, optimistic UI updates, and SEO metadata."
    },
    "AWS": {
        "resource": "AWS Cloud Practitioner & Solutions Architect Essentials",
        "platform": "AWS Skill Builder & Stéphane Maarek",
        "type": "Hands-on Cloud Labs",
        "estimated_hours": "25-35 hours",
        "difficulty": "Intermediate",
        "key_concepts": ["EC2 & S3 storage", "IAM roles & security groups", "VPC networking", "Lambda serverless", "RDS managed databases"],
        "recommended_project": "Deploy a serverless microservice using AWS Lambda, API Gateway, DynamoDB, and CloudFront distribution."
    },
    "CI/CD": {
        "resource": "GitHub Actions for Automated Testing & Deployment",
        "platform": "GitHub Skills & Documentation",
        "type": "Interactive Workflow Labs",
        "estimated_hours": "8-10 hours",
        "difficulty": "Beginner to Intermediate",
        "key_concepts": ["Workflow triggers", "Job matrixes", "Secrets management", "Automated linting & testing", "Artifact deployment"],
        "recommended_project": "Build a multi-stage GitHub Actions workflow that runs pytest, builds Docker image, and publishes to GitHub Container Registry."
    },
    "RAG": {
        "resource": "Building Production RAG Systems",
        "platform": "DeepLearning.AI Short Courses",
        "type": "Video & Jupyter Labs",
        "estimated_hours": "12-16 hours",
        "difficulty": "Advanced",
        "key_concepts": ["Chunking strategies", "Dense vector embeddings", "Hybrid search (BM25 + Dense)", "Re-ranking models", "Context evaluation"],
        "recommended_project": "Create a document chat assistant that ingests company PDF policies with ChromaDB vector search and re-ranking."
    },
    "Figma": {
        "resource": "Figma for UI Designers & Design Systems",
        "platform": "Figma Community & DesignCode",
        "type": "Visual Tutorials & UI Kits",
        "estimated_hours": "12-15 hours",
        "difficulty": "Beginner to Intermediate",
        "key_concepts": ["Auto Layout 5.0", "Component variants", "Interactive prototyping", "Design tokens", "Grid layouts"],
        "recommended_project": "Design a complete responsive mobile app design system with light and dark mode variable tokens in Figma."
    },
    "Cybersecurity": {
        "resource": "Practical Ethical Hacking & Defensive Security",
        "platform": "TryHackMe & PortSwigger Web Security Academy",
        "type": "Interactive Sandboxed Labs",
        "estimated_hours": "30-40 hours",
        "difficulty": "Intermediate to Advanced",
        "key_concepts": ["OWASP Top 10 vulnerabilities", "SQL injection & XSS", "Network packet sniffing", "Privilege escalation", "Log analysis"],
        "recommended_project": "Complete TryHackMe Junior Penetration Tester learning path and solve 5 vulnerable machine capture-the-flags."
    },
    "Distributed Systems": {
        "resource": "Distributed Systems Principles & Fallacies",
        "platform": "MIT 6.824 (Robert Morris lectures)",
        "type": "Lecture Series & Labs",
        "estimated_hours": "35-45 hours",
        "difficulty": "Advanced",
        "key_concepts": ["CAP Theorem", "Raft consensus algorithm", "Replication & Sharding", "Fault tolerance & Heartbeats", "RPC frameworks"],
        "recommended_project": "Implement a simplified Raft consensus algorithm in Go or Python with leader election and log replication."
    }
}

# Generic fallback pathway generator for skills without a dedicated manual entry
def _get_generic_pathway(skill_name: str) -> Dict[str, Any]:
    return {
        "resource": f"Complete {skill_name} Developer Guide & Official Documentation",
        "platform": "Official Docs, GitHub Tutorials & freeCodeCamp",
        "type": "Documentation & Hands-on Coding",
        "estimated_hours": "12-20 hours",
        "difficulty": "Intermediate",
        "key_concepts": [
            f"Core fundamentals and syntax of {skill_name}",
            f"Best practices and design patterns in {skill_name}",
            "Integrating with existing project pipelines",
            "Debugging and performance profiling"
        ],
        "recommended_project": f"Build an end-to-end portfolio project featuring {skill_name} with automated testing and comprehensive README."
    }


class SkillGapAnalyzer:
    """Provides granular gap breakdowns and actionable learning pathways."""

    @staticmethod
    def analyze_gap(student_skills: List[str], internship: Dict[str, Any]) -> Dict[str, Any]:
        normalized_student = {normalize_skill(s) for s in student_skills}

        req_skills = [normalize_skill(s) for s in internship.get("required_skills", [])]
        pref_skills = [normalize_skill(s) for s in internship.get("preferred_skills", [])]

        missing_req = [s for s in req_skills if s not in normalized_student]
        matched_req = [s for s in req_skills if s in normalized_student]
        missing_pref = [s for s in pref_skills if s not in normalized_student]
        matched_pref = [s for s in pref_skills if s in normalized_student]

        # Generate learning pathways for all missing skills (prioritizing required)
        learning_pathways = []
        for skill in missing_req:
            resource = SKILL_LEARNING_RESOURCES.get(skill, _get_generic_pathway(skill))
            learning_pathways.append({
                "skill": skill,
                "priority": "HIGH (Core Requirement)",
                "priority_badge": "Critical Requirement",
                "priority_color": "#EF4444",
                **resource
            })

        for skill in missing_pref:
            resource = SKILL_LEARNING_RESOURCES.get(skill, _get_generic_pathway(skill))
            learning_pathways.append({
                "skill": skill,
                "priority": "MEDIUM (Preferred Qualification)",
                "priority_badge": "Competitive Edge",
                "priority_color": "#F59E0B",
                **resource
            })

        # Calculate high leverage skill (the one whose addition creates the biggest point boost)
        high_leverage_skill = missing_req[0] if missing_req else (missing_pref[0] if missing_pref else None)

        total_req = len(req_skills) if req_skills else 1
        readiness_pct = round((len(matched_req) / total_req) * 100, 1)

        return {
            "internship_id": internship.get("id"),
            "internship_title": internship.get("title"),
            "company": internship.get("company"),
            "readiness_percentage": readiness_pct,
            "matched_required_count": len(matched_req),
            "total_required_count": len(req_skills),
            "missing_required": missing_req,
            "matched_required": matched_req,
            "missing_preferred": missing_pref,
            "matched_preferred": matched_pref,
            "high_leverage_skill": high_leverage_skill,
            "learning_pathways": learning_pathways,
            "estimated_upskill_time": f"{len(missing_req) * 15 + len(missing_pref) * 8} estimated study hours"
        }

    @staticmethod
    def simulate_what_if(
        current_skills: List[str],
        skills_to_add: List[str],
        internship: Dict[str, Any],
        recommender_engine: Any
    ) -> Dict[str, Any]:
        """
        Calculates match score before and after adding hypothetical skills,
        showing the exact point increase.
        """
        # Baseline recommendation
        base_recs = recommender_engine.recommend(
            student_skills=current_skills,
            top_k=50
        )
        base_score = 30.0
        for r in base_recs:
            if r["internship"]["id"] == internship["id"]:
                base_score = r["match_score"]
                break

        # Simulated recommendation
        simulated_skills = list(set(current_skills + skills_to_add))
        sim_recs = recommender_engine.recommend(
            student_skills=simulated_skills,
            top_k=50
        )
        sim_score = base_score
        for r in sim_recs:
            if r["internship"]["id"] == internship["id"]:
                sim_score = r["match_score"]
                break

        delta = round(sim_score - base_score, 1)

        return {
            "current_score": base_score,
            "projected_score": sim_score,
            "score_delta": delta,
            "added_skills": skills_to_add,
            "impact_message": f"Acquiring {', '.join(skills_to_add)} increases your match score by +{delta}%!" if delta > 0 else "Skills already accounted for or outside primary qualification criteria."
        }
