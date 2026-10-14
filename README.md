# ⚡ SkillMatch AI

> **ML-Based Student Skill Mapping & Precision Internship Recommendation System**

[![Python Version](https://img.shields.io/badge/python-3.11%20%7C%203.12%20%7C%203.13-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-009688.svg?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![Docker](https://img.shields.io/badge/Docker-Ready-2496ED.svg?logo=docker&logoColor=white)](https://www.docker.com/)
[![Tests](https://img.shields.io/badge/tests-32%20passed-brightgreen.svg)](https://pytest.org/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](#)

SkillMatch AI bridges the gap between student competencies and industry hiring standards. Using a hybrid machine-learning matching architecture (TF-IDF vectorization, Okapi BM25 lexical ranking, and an ontology of 400+ normalized technical skills), SkillMatch AI parses candidate resumes, maps multidimensional competency radars, computes personalized internship fit scores, and generates actionable upskilling pathways.

---

## 🚀 Key Features

- **Semantic Resume Ingestion**: Native extraction from PDF (PyMuPDF & PyPDF), DOCX, and raw text with instant entity recognition for skills, contact data, and coursework.
- **Hybrid ML Match Engine**: Combines **TF-IDF cosine similarity** (30%), **Okapi BM25 ranking** (25%), **exact required skill overlap** (35%), and **preferred skill bonus** (10%) for sub-50ms precision recommendations.
- **6-Pillar Competency Radar Index**: Real-time canvas visualization indexing candidate strength across *AI & Machine Learning*, *Fullstack Development*, *Data & Analytics*, *Cloud & DevOps*, *Systems & CS*, and *UI/UX & Product*.
- **"What-If" Career Simulation Engine**: Interactive career sandbox allowing students to test hypothetical skill acquisitions and preview real-time score improvements and rank shifts.
- **Granular Skill Gap Analysis & Roadmap**: Automated calculation of missing required and preferred competencies with tailored milestones, study hours, and project recommendations.
- **Recruiter & Talent Portal Support**: Endpoints for employer role publishing, talent search, and candidate match ranking.
- **Production DevOps Ready**: Dockerized container, Gunicorn multi-worker configuration, CI/CD pipeline, and comprehensive test suite.

---

## 🏗️ System Architecture

```
                  ┌────────────────────────────────────────┐
                  │          Candidate Resume / CV         │
                  └───────────────────┬────────────────────┘
                                      │
                         [PyMuPDF / docx Parser]
                                      │
                                      ▼
                        ┌───────────────────────────┐
                        │  Skill Extraction Engine  │
                        │ (400+ Canonical Ontology) │
                        └─────────────┬─────────────┘
                                      │
                 ┌────────────────────┴────────────────────┐
                 │                                         │
                 ▼                                         ▼
   ┌───────────────────────────┐             ┌───────────────────────────┐
   │ Competency Radar Analysis │             │ Hybrid Recommendation Core│
   │   (6 Domain Pillars)      │             │  • TF-IDF Cosine (30%)    │
   └───────────────────────────┘             │  • Okapi BM25 (25%)       │
                                             │  • Skill Overlap (35%)    │
                                             │  • Preferred Bonus (10%)  │
                                             └─────────────┬─────────────┘
                                                           │
                                                           ▼
                                             ┌───────────────────────────┐
                                             │ Ranked Internship Matches │
                                             └─────────────┬─────────────┘
                                                           │
                                                           ▼
                                             ┌───────────────────────────┐
                                             │    Target Role Gap &      │
                                             │   What-If Simulation      │
                                             └───────────────────────────┘
```

---

## 📁 Repository Structure

```
.
├── backend/
│   ├── data/
│   │   ├── internships.json       # 24+ rich internship records across 6 domains
│   │   └── sample_resumes.json     # Pre-built student personas for 1-click demos
│   ├── ml/
│   │   ├── parser.py              # Resume parsing & regex entity extraction
│   │   ├── recommender.py         # Hybrid TF-IDF + BM25 recommendation engine
│   │   ├── gap_analyzer.py        # Gap calculation & personalized roadmaps
│   │   └── taxonomy.py            # Skill taxonomy, normalization & pillar mapping
│   └── main.py                    # FastAPI server & production REST endpoints
├── frontend/
│   ├── css/
│   │   └── styles.css             # Glassmorphism dark-mode UI & responsive styling
│   ├── js/
│   │   ├── app.js                 # Frontend application state & API integration
│   │   └── charts.js              # Custom HTML5 Canvas Radar chart engine
│   └── index.html                 # Main dashboard UI
├── tests/
│   ├── conftest.py                # Pytest fixtures & TestClient configuration
│   ├── test_health.py             # Health check & telemetry tests
│   ├── test_ml_parser.py          # Resume parser & taxonomy tests
│   ├── test_ml_recommender.py     # Recommender algorithm tests
│   ├── test_ml_gap_analyzer.py    # Gap analysis & simulation tests
│   ├── test_api_endpoints.py      # Core REST API endpoint tests
│   └── test_applications_and_recruiter.py # Applications & recruiter flow tests
├── .github/workflows/
│   └── ci.yml                     # GitHub Actions CI workflow
├── Dockerfile                     # Lean, multi-stage production container image
├── docker-compose.yml             # Local & server container orchestration
├── gunicorn_conf.py               # Enterprise Gunicorn configuration
├── run.py                         # Dual dev/prod launcher script
├── requirements.txt               # Pinned production & test dependencies
├── .env.example                   # Environment variable template
├── DEPLOYMENT.md                  # Comprehensive cloud deployment & DevOps manual
└── README.md
```

---

## ⚡ Quickstart

### 1. Prerequisites
- Python 3.11+ (or Docker)
- Git

### 2. Clone and Setup Environment

```bash
# Clone the repository
git clone <your-repo-url>
cd "ML project"

# Create a virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
.\venv\Scripts\activate
# Linux/macOS:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Launch Development Server

```bash
# Starts development server with auto-reload at http://localhost:8000
python run.py
```

Open your browser at **`http://localhost:8000`** to interact with the application.  
API documentation is available at **`http://localhost:8000/docs`**.

---

## 🏭 Production Execution

### Using the Production Multi-Worker Launcher
```bash
# Multi-worker server binding on 0.0.0.0:8000
python run.py --prod --workers 4
```

### Using Docker Compose
```bash
docker-compose up -d --build
```

### Using Docker CLI
```bash
docker build -t skillmatch-ai:latest .
docker run -d -p 8000:8000 --name skillmatch-app skillmatch-ai:latest
```

For comprehensive instructions on deploying to **Render**, **Railway**, **AWS ECS**, **DigitalOcean**, or configuring **Nginx Reverse Proxy + SSL**, see [**`DEPLOYMENT.md`**](file:///d:/my%20projects/ML%20project/DEPLOYMENT.md).

---

## 🧪 Testing Suite

SkillMatch AI includes 32 automated unit and integration tests covering the ML engines, parsers, and API workflows:

```bash
# Run full test suite with verbose output
python -m pytest -v

# Run with test coverage
python -m pytest --cov=backend tests/
```

---

## 🩺 System Telemetry & Health

Check real-time system metrics, memory consumption, and ML model status at:
```bash
curl http://localhost:8000/api/health
```

---

## 📄 License

This project is licensed under the MIT License.
