"""
SkillMatch AI - FastAPI Application Server
Provides RESTful endpoints for resume parsing, hybrid internship recommendations,
skill gap analysis, What-If simulation, and market intelligence.
"""

import json
import os
import sys
import time
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from backend.ml.gap_analyzer import SkillGapAnalyzer
from backend.ml.parser import ResumeParser
from backend.ml.recommender import InternshipRecommender
from backend.ml.taxonomy import (
    TAXONOMY,
    compute_skill_pillars,
    get_all_skills_flat,
    get_skill_category,
    normalize_skill,
)

SERVER_START_TIME = time.time()
ENVIRONMENT = os.getenv("ENVIRONMENT", "development")

app = FastAPI(
    title="SkillMatch AI",
    description="ML-Based Student Skill Mapping and Internship Recommendation System",
    version="2.0.0"
)

# CORS middleware for frontend communication (configurable via ALLOWED_ORIGINS env)
allowed_origins_env = os.getenv("ALLOWED_ORIGINS", "*")
if allowed_origins_env == "*":
    allowed_origins = ["*"]
else:
    allowed_origins = [o.strip() for o in allowed_origins_env.split(",") if o.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize ML engines
parser = ResumeParser()
recommender = InternshipRecommender()

# Load sample resumes
samples_path = Path(__file__).parent / "data" / "sample_resumes.json"
sample_students: List[Dict[str, Any]] = []
if samples_path.exists():
    with open(samples_path, "r", encoding="utf-8") as f:
        sample_students = json.load(f)

# Candidate talent pool database (seeded with sample students + dynamically registered candidates)
candidates_db: List[Dict[str, Any]] = [dict(s) for s in sample_students]

# Applications database
applications_db: List[Dict[str, Any]] = [
    {
        "id": "app-101",
        "internship_id": "int-01",
        "internship_title": "Machine Learning Research Intern",
        "company": "Anthropic AI",
        "student_id": "alex-chen",
        "student_name": "Alex Chen",
        "student_email": "alex.chen@berkeley.edu",
        "student_education": "B.S. in Electrical Engineering & Computer Science, UC Berkeley (GPA: 3.92)",
        "student_skills": ["Python", "PyTorch", "Transformers", "Machine Learning", "Deep Learning", "Computer Vision", "Docker"],
        "match_score": 96.5,
        "status": "Interviewing",
        "applied_at": "Oct 12, 2026"
    },
    {
        "id": "app-102",
        "internship_id": "int-02",
        "internship_title": "Fullstack Software Engineering Intern",
        "company": "Stripe",
        "student_id": "maya-patel",
        "student_name": "Maya Patel",
        "student_email": "maya.patel@stanford.edu",
        "student_education": "B.S. in Computer Science, Stanford University (GPA: 3.85)",
        "student_skills": ["TypeScript", "JavaScript", "React", "Next.js", "Node.js", "PostgreSQL", "REST APIs", "Docker"],
        "match_score": 94.0,
        "status": "Shortlisted",
        "applied_at": "Oct 13, 2026"
    },
    {
        "id": "app-103",
        "internship_id": "int-03",
        "internship_title": "Data Science & Analytics Intern",
        "company": "Spotify",
        "student_id": "jordan-lee",
        "student_name": "Jordan Lee",
        "student_email": "jordan.lee@umich.edu",
        "student_education": "B.S. in Data Science & Statistics, University of Michigan (GPA: 3.78)",
        "student_skills": ["Python", "SQL", "Pandas", "NumPy", "Tableau", "Statistical Modeling", "A/B Testing"],
        "match_score": 91.2,
        "status": "Under Review",
        "applied_at": "Oct 14, 2026"
    }
]


# Request Models
class TextParseRequest(BaseModel):
    text: str = Field(..., description="Raw text of resume or CV")


class RecommendationRequest(BaseModel):
    skills: List[str] = Field(default_factory=list)
    experience_summary: str = Field(default="")
    education: str = Field(default="")
    domain: Optional[str] = Field(default=None)
    work_type: Optional[str] = Field(default=None)
    min_match: Optional[float] = Field(default=0.0)
    top_k: Optional[int] = Field(default=15)
    simulated_skills: Optional[List[str]] = Field(default_factory=list)
    mode: Optional[str] = Field(default="real")


class SkillGapRequest(BaseModel):
    skills: List[str] = Field(default_factory=list, description="Candidate skills")
    internship_id: str = Field(..., description="Target internship ID")


class SimulationRequest(BaseModel):
    current_skills: List[str] = Field(default_factory=list, description="Current candidate skills")
    skills_to_add: List[str] = Field(default_factory=list, description="Hypothetical skills to add")
    internship_id: str = Field(..., description="Target internship ID")


class PostInternshipRequest(BaseModel):
    title: str = Field(..., min_length=3)
    company: str = Field(..., min_length=2)
    domain: str = Field(default="Software Engineering")
    location: str = Field(default="Remote")
    work_type: str = Field(default="Remote")
    duration: str = Field(default="12 Weeks (Summer 2026)")
    stipend: str = Field(default="$48/hr ($7,680/mo)")
    level: str = Field(default="Undergrad / Masters")
    description: str = Field(..., min_length=10)
    required_skills: List[str] = Field(default_factory=list)
    preferred_skills: List[str] = Field(default_factory=list)
    responsibilities: List[str] = Field(default_factory=list)
    learning_outcomes: List[str] = Field(default_factory=list)


class ApplyRequest(BaseModel):
    internship_id: str = Field(...)
    student_id: Optional[str] = Field(default="student-live")
    student_name: str = Field(..., min_length=2)
    student_email: Optional[str] = Field(default="student@university.edu")
    student_education: Optional[str] = Field(default="Undergraduate Student")
    student_skills: List[str] = Field(default_factory=list)
    match_score: Optional[float] = Field(default=85.0)


class ApplicationStatusUpdate(BaseModel):
    status: str = Field(...)


class SaveCandidateProfileRequest(BaseModel):
    id: Optional[str] = None
    name: str
    email: Optional[str] = ""
    phone: Optional[str] = ""
    education: Optional[str] = ""
    extracted_skills: List[str] = Field(default_factory=list)
    experience_summary: Optional[str] = ""
    links: Optional[Dict[str, str]] = Field(default_factory=dict)


SIMULATION_SCENARIOS = [
    {
        "id": "ai-engineer",
        "title": "AI & Deep Learning Engineer",
        "badge": "AI & ML",
        "color": "#6366F1",
        "description": "Master transformer models, neural network architectures, and production MLOps.",
        "skills": ["PyTorch", "Transformers", "LangChain", "Deep Learning", "MLOps", "Computer Vision"]
    },
    {
        "id": "fullstack-pro",
        "title": "Modern Fullstack Engineer",
        "badge": "Fullstack",
        "color": "#10B981",
        "description": "Build production React/Next.js systems with relational databases, REST APIs, and Docker.",
        "skills": ["Next.js", "Node.js", "PostgreSQL", "GraphQL", "Docker", "REST APIs"]
    },
    {
        "id": "cloud-devops",
        "title": "Cloud Architect & DevOps",
        "badge": "Cloud & Ops",
        "color": "#06B6D4",
        "description": "Orchestrate high-availability cloud workloads with containers, IaC, and automated CI/CD.",
        "skills": ["AWS", "Kubernetes", "Docker", "Terraform", "CI/CD", "Linux"]
    },
    {
        "id": "data-platform",
        "title": "Big Data & ML Engineering",
        "badge": "Data & Analytics",
        "color": "#F59E0B",
        "description": "High-throughput data streaming, feature stores, and distributed pipeline processing.",
        "skills": ["PySpark", "Pandas", "SQL", "Airflow", "Data Modeling", "ETL"]
    },
    {
        "id": "cybersecurity",
        "title": "Cybersecurity & Defense Specialist",
        "badge": "Security",
        "color": "#EC4899",
        "description": "Penetration testing, application vulnerability remediation, and zero-trust security.",
        "skills": ["Ethical Hacking", "OWASP", "Network Security", "Cryptography", "Linux"]
    }
]


# Endpoints

@app.get("/health")
@app.get("/api/health")
async def health_check():
    """
    Production health check and telemetry endpoint.
    Used by container orchestrators (Docker, Kubernetes), load balancers, and monitoring tools.
    """
    uptime_sec = round(time.time() - SERVER_START_TIME, 2)
    memory_info = {}
    try:
        import psutil
        process = psutil.Process()
        mem = process.memory_info()
        memory_info = {
            "rss_mb": round(mem.rss / (1024 * 1024), 2),
            "vms_mb": round(mem.vms / (1024 * 1024), 2),
            "cpu_percent": process.cpu_percent(interval=None)
        }
    except Exception:
        memory_info = {"status": "telemetry_unavailable"}

    return {
        "status": "healthy",
        "service": "SkillMatch AI",
        "version": "2.0.0",
        "environment": ENVIRONMENT,
        "uptime_seconds": uptime_sec,
        "timestamp": datetime.now().astimezone().isoformat(),
        "ml_engines": {
            "parser": "active",
            "recommender": "active",
            "taxonomy_skills_count": len(get_all_skills_flat()),
            "indexed_internships_count": len(recommender.internships),
            "candidate_pool_count": len(candidates_db),
            "applications_count": len(applications_db)
        },
        "system": {
            "python_version": sys.version.split()[0],
            "memory": memory_info
        }
    }


@app.get("/api/simulation-scenarios")
async def get_simulation_scenarios():
    """Returns curated career pivot scenarios for the What-If simulation engine."""
    return {"scenarios": SIMULATION_SCENARIOS}


@app.post("/api/upload-resume")
async def upload_resume(file: UploadFile = File(...)):
    """Upload PDF, DOCX, or TXT resume to extract skills and compute instant recommendations."""
    content = await file.read()
    if not content:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")

    filename = file.filename or "resume.txt"
    parsed_profile = parser.parse_document(content, filename)

    # Initial recommendation
    recs = recommender.recommend(
        student_skills=parsed_profile["extracted_skills"],
        experience_summary=parsed_profile.get("experience_summary", ""),
        education=parsed_profile.get("education", ""),
        top_k=12
    )

    return {
        "status": "success",
        "filename": filename,
        "profile": parsed_profile,
        "recommendations": recs
    }


@app.post("/api/parse-text")
async def parse_text_endpoint(req: TextParseRequest):
    """Parses raw pasted text and computes candidate profile and recommendations."""
    if not req.text.strip():
        raise HTTPException(status_code=400, detail="Text cannot be empty.")

    parsed_profile = parser.parse_text(req.text)
    recs = recommender.recommend(
        student_skills=parsed_profile["extracted_skills"],
        experience_summary=parsed_profile.get("experience_summary", ""),
        education=parsed_profile.get("education", ""),
        top_k=12
    )

    return {
        "status": "success",
        "profile": parsed_profile,
        "recommendations": recs
    }


@app.post("/api/recommend")
async def get_recommendations(req: RecommendationRequest):
    """Computes filtered hybrid internship recommendations in Real or Simulation mode."""
    mode = req.mode or "real"
    sim_skills = req.simulated_skills or []
    is_simulation = mode == "simulation" or len(sim_skills) > 0

    # 1. Base real recommendations
    base_recs = recommender.recommend(
        student_skills=req.skills,
        experience_summary=req.experience_summary,
        education=req.education,
        target_domain=req.domain,
        work_type_filter=req.work_type,
        min_match_score=0.0,
        top_k=50
    )
    base_scores_map = {r["internship"]["id"]: (r["match_score"], rank_idx) for rank_idx, r in enumerate(base_recs)}
    real_radar = compute_skill_pillars(req.skills)

    if not is_simulation:
        filtered_recs = [r for r in base_recs if r["match_score"] >= (req.min_match or 0.0)][:req.top_k or 15]
        return {
            "mode": "real",
            "recommendations": filtered_recs,
            "radar_pillars": real_radar,
            "simulated_radar_pillars": None,
            "total_matches": len(filtered_recs)
        }

    # 2. Simulation Mode: combine real + simulated skills
    combined_skills = list(dict.fromkeys(req.skills + sim_skills))
    sim_recs = recommender.recommend(
        student_skills=combined_skills,
        experience_summary=req.experience_summary,
        education=req.education,
        target_domain=req.domain,
        work_type_filter=req.work_type,
        min_match_score=0.0,
        top_k=50
    )
    simulated_radar = compute_skill_pillars(combined_skills)

    # Enrich each simulated recommendation with comparative delta data
    enriched_sim_recs = []
    norm_sim_skills = {normalize_skill(s) for s in sim_skills}

    for sim_rank, r in enumerate(sim_recs):
        job = r["internship"]
        job_id = job["id"]
        
        real_info = base_scores_map.get(job_id)
        if real_info:
            real_score, real_rank = real_info
            rank_shift = real_rank - sim_rank
        else:
            real_score = round(min(r["match_score"], 22.0), 1)
            rank_shift = 0

        score_delta = round(r["match_score"] - real_score, 1)

        # Identify which simulated skills satisfied job requirements or preferences
        req_norm = [normalize_skill(s) for s in job.get("required_skills", [])]
        pref_norm = [normalize_skill(s) for s in job.get("preferred_skills", [])]
        satisfied_skills = [
            s for s in sim_skills
            if normalize_skill(s) in req_norm or normalize_skill(s) in pref_norm
        ]

        r_copy = dict(r)
        r_copy["real_match_score"] = real_score
        r_copy["simulated_match_score"] = r["match_score"]
        r_copy["score_delta"] = score_delta
        r_copy["rank_shift"] = rank_shift
        r_copy["simulated_satisfied_skills"] = satisfied_skills

        if r_copy["simulated_match_score"] >= (req.min_match or 0.0):
            enriched_sim_recs.append(r_copy)

    final_recs = enriched_sim_recs[:req.top_k or 15]

    return {
        "mode": "simulation",
        "recommendations": final_recs,
        "radar_pillars": real_radar,
        "simulated_radar_pillars": simulated_radar,
        "total_matches": len(final_recs),
        "simulated_skills": sim_skills
    }


@app.post("/api/skill-gap")
async def get_skill_gap(req: SkillGapRequest):
    """Calculates granular gap analysis and personalized learning roadmap for a specific job."""
    target_job = next((j for j in recommender.internships if j["id"] == req.internship_id), None)
    if not target_job:
        raise HTTPException(status_code=404, detail=f"Internship with ID '{req.internship_id}' not found.")

    gap_analysis = SkillGapAnalyzer.analyze_gap(req.skills, target_job)
    return gap_analysis


@app.post("/api/simulate")
async def simulate_score(req: SimulationRequest):
    """What-If simulator: calculates match score improvement if student learns proposed skills."""
    target_job = next((j for j in recommender.internships if j["id"] == req.internship_id), None)
    if not target_job:
        raise HTTPException(status_code=404, detail=f"Internship with ID '{req.internship_id}' not found.")

    sim_result = SkillGapAnalyzer.simulate_what_if(
        current_skills=req.current_skills,
        skills_to_add=req.skills_to_add,
        internship=target_job,
        recommender_engine=recommender
    )
    return sim_result


@app.get("/api/internships")
async def list_internships(
    domain: Optional[str] = None,
    work_type: Optional[str] = None,
    search: Optional[str] = None
):
    """Returns directory of all internship postings with optional search & filters."""
    results = recommender.internships
    if domain and domain.lower() != "all":
        results = [j for j in results if j["domain"].lower() == domain.lower()]
    if work_type and work_type.lower() != "all":
        results = [j for j in results if j["work_type"].lower() == work_type.lower()]
    if search:
        s = search.lower()
        results = [
            j for j in results
            if s in j["title"].lower()
            or s in j["company"].lower()
            or any(s in skill.lower() for skill in j.get("required_skills", []))
            or s in j["description"].lower()
        ]
    return {"internships": results, "count": len(results)}


@app.get("/api/internships/{internship_id}")
async def get_internship_detail(internship_id: str):
    """Returns single internship by ID."""
    job = next((j for j in recommender.internships if j["id"] == internship_id), None)
    if not job:
        raise HTTPException(status_code=404, detail="Internship not found")
    return job


@app.get("/api/samples")
async def get_samples():
    """Returns sample pre-built student personas for 1-click test drive."""
    return {"samples": sample_students}


@app.get("/api/market-trends")
async def get_market_trends():
    """Computes industry-wide skill demand frequency across all indexed internships."""
    skill_counts: Dict[str, int] = {}
    domain_counts: Dict[str, int] = {}

    for job in recommender.internships:
        d = job["domain"]
        domain_counts[d] = domain_counts.get(d, 0) + 1
        for s in job.get("required_skills", []):
            canon = normalize_skill(s)
            skill_counts[canon] = skill_counts.get(canon, 0) + 2  # Required has double weight
        for s in job.get("preferred_skills", []):
            canon = normalize_skill(s)
            skill_counts[canon] = skill_counts.get(canon, 0) + 1

    sorted_skills = sorted(skill_counts.items(), key=lambda x: x[1], reverse=True)[:15]

    return {
        "top_demanded_skills": [{"skill": s, "demand_score": score, "category": get_skill_category(s)} for s, score in sorted_skills],
        "domain_distribution": domain_counts,
        "total_internships": len(recommender.internships)
    }


@app.get("/api/taxonomy")
async def get_taxonomy_data():
    """Returns skill taxonomy and all available canonical skills."""
    return {
        "taxonomy": TAXONOMY,
        "all_skills": get_all_skills_flat()
    }


# Recruiter & Dual-Portal Endpoints

@app.post("/api/internships")
async def create_internship(req: PostInternshipRequest):
    """Creates a new internship listing posted by an employer/recruiter."""
    job_id = f"int-rec-{uuid.uuid4().hex[:6]}"
    initials = "".join([w[0].upper() for w in req.company.split()[:2]]) or "CO"
    colors = ["#6366F1", "#10B981", "#06B6D4", "#F59E0B", "#EC4899", "#8B5CF6"]
    company_color = colors[len(recommender.internships) % len(colors)]

    new_job = {
        "id": job_id,
        "title": req.title,
        "company": req.company,
        "domain": req.domain,
        "location": req.location,
        "work_type": req.work_type,
        "duration": req.duration,
        "stipend": req.stipend,
        "level": req.level,
        "company_initials": initials,
        "company_color": company_color,
        "description": req.description,
        "required_skills": req.required_skills,
        "preferred_skills": req.preferred_skills,
        "responsibilities": req.responsibilities or [
            f"Contribute to real-world {req.domain} engineering initiatives",
            "Collaborate cross-functionally with senior mentors and peers"
        ],
        "learning_outcomes": req.learning_outcomes or [
            "Production experience with industry best practices",
            "Mentorship from leading industry practitioners"
        ]
    }

    recommender.add_internship(new_job)

    return {
        "status": "success",
        "message": f"Internship '{req.title}' successfully published and indexed!",
        "internship": new_job
    }


@app.post("/api/apply")
async def apply_to_internship(req: ApplyRequest):
    """Allows a student candidate to apply to an internship with their live profile."""
    target_job = next((j for j in recommender.internships if j["id"] == req.internship_id), None)
    if not target_job:
        raise HTTPException(status_code=404, detail="Target internship not found.")

    # Check if already applied
    existing = next((a for a in applications_db if a["internship_id"] == req.internship_id and a["student_name"].lower() == req.student_name.lower()), None)
    if existing:
        return {
            "status": "already_applied",
            "message": "You have already submitted an application for this role.",
            "application": existing
        }

    app_id = f"app-{uuid.uuid4().hex[:6]}"
    now_str = datetime.now().strftime("%b %d, %Y")

    new_app = {
        "id": app_id,
        "internship_id": req.internship_id,
        "internship_title": target_job["title"],
        "company": target_job["company"],
        "student_id": req.student_id or f"cand-{uuid.uuid4().hex[:6]}",
        "student_name": req.student_name,
        "student_email": req.student_email,
        "student_education": req.student_education,
        "student_skills": req.student_skills,
        "match_score": req.match_score,
        "status": "Under Review",
        "applied_at": now_str
    }

    applications_db.insert(0, new_app)

    # Also register/update in candidate pool
    cand_match = next((c for c in candidates_db if c.get("name", "").lower() == req.student_name.lower()), None)
    if not cand_match:
        candidates_db.append({
            "id": new_app["student_id"],
            "name": req.student_name,
            "email": req.student_email,
            "education": req.student_education,
            "extracted_skills": req.student_skills,
            "experience_summary": f"Applicant for {target_job['title']}",
            "links": {}
        })

    return {
        "status": "success",
        "message": f"Application to {target_job['company']} successfully submitted!",
        "application": new_app
    }


@app.get("/api/applications")
async def get_applications(
    internship_id: Optional[str] = None,
    student_id: Optional[str] = None
):
    """Retrieves all submitted applications with optional filters."""
    results = applications_db
    if internship_id:
        results = [a for a in results if a["internship_id"] == internship_id]
    if student_id:
        results = [a for a in results if a["student_id"] == student_id or a["student_name"].lower() == student_id.lower()]
    return {"applications": results, "count": len(results)}


@app.patch("/api/applications/{application_id}/status")
async def update_application_status(application_id: str, body: ApplicationStatusUpdate):
    """Updates applicant status (e.g. Shortlisted, Interviewing, Offered, Rejected)."""
    app_record = next((a for a in applications_db if a["id"] == application_id), None)
    if not app_record:
        raise HTTPException(status_code=404, detail="Application record not found.")

    app_record["status"] = body.status
    return {
        "status": "success",
        "message": f"Application status updated to '{body.status}'",
        "application": app_record
    }


@app.get("/api/candidates")
async def list_candidates():
    """Returns candidate pool for recruiter talent search and scouting."""
    return {"candidates": candidates_db, "count": len(candidates_db)}


@app.post("/api/candidate-profile")
async def save_candidate_profile(req: SaveCandidateProfileRequest):
    """Saves or updates a candidate's profile into the candidate talent pool."""
    cand_id = req.id or f"cand-{uuid.uuid4().hex[:6]}"
    existing = next((c for c in candidates_db if c.get("id") == cand_id or c.get("name", "").lower() == req.name.lower()), None)
    
    profile_data = {
        "id": cand_id,
        "name": req.name,
        "email": req.email,
        "phone": req.phone,
        "education": req.education,
        "extracted_skills": req.extracted_skills,
        "experience_summary": req.experience_summary,
        "links": req.links or {}
    }

    if existing:
        existing.update(profile_data)
    else:
        candidates_db.insert(0, profile_data)

    return {"status": "success", "candidate": profile_data}


@app.get("/api/recruiter/internships/{internship_id}/applicants")
async def get_role_applicants(internship_id: str):
    """
    Returns all applicants for a given internship, ranked by hybrid AI match score.
    If no direct applicants exist, evaluates candidates in pool to give recruiter actionable scout matches.
    """
    job = next((j for j in recommender.internships if j["id"] == internship_id), None)
    if not job:
        raise HTTPException(status_code=404, detail="Internship not found.")

    direct_apps = [a for a in applications_db if a["internship_id"] == internship_id]

    cand_list = []
    if direct_apps:
        for a in direct_apps:
            cand_list.append({
                "id": a["student_id"],
                "name": a["student_name"],
                "email": a["student_email"],
                "education": a["student_education"],
                "extracted_skills": a["student_skills"],
                "application_id": a["id"],
                "application_status": a["status"],
                "applied_at": a["applied_at"]
            })
    else:
        # Scout candidate talent pool
        for c in candidates_db:
            cand_copy = dict(c)
            cand_copy["application_id"] = None
            cand_copy["application_status"] = "Pool Scout"
            cand_copy["applied_at"] = "Candidate Pool"
            cand_list.append(cand_copy)

    ranked = recommender.rank_candidates(cand_list, job)

    return {
        "internship": job,
        "direct_applications_count": len(direct_apps),
        "applicants": ranked
    }


# Mount Frontend static files
frontend_dir = Path(__file__).parent.parent / "frontend"
if frontend_dir.exists():
    app.mount("/", StaticFiles(directory=str(frontend_dir), html=True), name="frontend")
